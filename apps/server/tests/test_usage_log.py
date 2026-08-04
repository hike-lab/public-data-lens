"""§10 익명 사용 로그 — 기록 형식, 옵트아웃(전면 미기록), 검색 지표 주석(§12)."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from datanav.api.rest import app
from tests.conftest import requires_catalog

client = TestClient(app)


def _read_lines(tmp_path):
    files = list(tmp_path.glob("usage-*.jsonl"))
    if not files:
        return []
    return [json.loads(l) for l in files[0].read_text(encoding="utf-8").splitlines()]


def test_usage_log_written_anonymously(tmp_path, monkeypatch):
    monkeypatch.setenv("DATANAV_LOG_DIR", str(tmp_path))
    # 카탈로그 비의존 엔드포인트 사용 — 신선한 클론(카탈로그 미빌드)에서도 검증 가능해야 한다
    client.get("/api/resources/rules", headers={"X-Datanav-Anon-Id": "test-anon-1"})
    lines = _read_lines(tmp_path)
    assert len(lines) == 1
    entry = lines[0]
    assert entry["path"] == "/api/resources/rules" and entry["status"] == 200
    assert entry["anon"] == "test-anon-1"
    # 원 IP가 어떤 필드에도 저장되지 않는다
    assert "127.0.0.1" not in json.dumps(entry) and "testclient" not in json.dumps(entry)


def test_optout_headers_skip_logging_entirely(tmp_path, monkeypatch):
    monkeypatch.setenv("DATANAV_LOG_DIR", str(tmp_path))
    for headers in ({"DNT": "1"}, {"Sec-GPC": "1"}, {"X-Datanav-No-Log": "1"}):
        client.get("/api/status", headers=headers)
    assert _read_lines(tmp_path) == []  # 익명 항목 포함 전부 미기록


def test_non_api_paths_not_logged(tmp_path, monkeypatch):
    monkeypatch.setenv("DATANAV_LOG_DIR", str(tmp_path))
    client.get("/docs")  # FastAPI 자체 경로 — 기록 대상 아님
    assert _read_lines(tmp_path) == []


@requires_catalog
def test_search_entry_annotated_for_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("DATANAV_LOG_DIR", str(tmp_path))
    client.get("/api/search", params={"query": "도서관", "theme": "교육"})
    client.get("/api/search", params={"query": "zzz없는검색어qqq"})
    lines = [e for e in _read_lines(tmp_path) if e["path"] == "/api/search"]
    assert lines[0]["q"] == "도서관" and lines[0]["filters"] == ["theme"]
    assert lines[0]["zero"] is False
    assert lines[1]["zero"] is True  # 0건 비율(§12) 측정 가능


def test_anon_hmac_key_persists_across_process_restart(tmp_path, monkeypatch):
    """키 미지정 시 데이터 볼륨에 영속 — 재시작에도 캡·지표 연속(v0.5 회귀)."""
    from datanav import config
    from datanav.api import rest

    monkeypatch.delenv("DATANAV_ANON_HMAC_KEY", raising=False)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    k1 = rest._anon_hmac_key()
    k2 = rest._anon_hmac_key()  # 프로세스 재시작 상당(모듈 상수 재계산)
    assert k1 == k2 and len(k1) == 32
    assert (tmp_path / "anon_hmac.key").exists()

    monkeypatch.setenv("DATANAV_ANON_HMAC_KEY", "explicit-secret")
    assert rest._anon_hmac_key() == b"explicit-secret"  # 환경변수가 우선
