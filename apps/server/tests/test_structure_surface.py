"""S1b 관측 표면(계약 v1.2) — get_dataset_structure, 검색 structureAvailable,
보수 모드(예시값 응답 게이트), 미수집·API 상태의 정상 응답."""
from __future__ import annotations

import pytest

from datanav.observe.ingest import ingest_profile_csv
from tests.conftest import requires_catalog
from tests.test_observe_ingest import HEADER, _row


@pytest.fixture()
def svc_with_obs(tmp_path, monkeypatch, service):
    """실카탈로그의 FILE 레코드 하나에 합성 관측을 붙인 Service."""
    covered = service.search_datasets(list_type="FILE", page_size=1)["data"]["items"][0]
    lk = covered["listKey"]
    csv_path = tmp_path / "profile.csv"
    csv_path.write_text(
        "﻿" + HEADER + "\n"
        + _row(list_key=lk, ordinal="1") + "\n"
        + _row(list_key=lk, name="위도", samples="['37.5', '36.2']", ordinal="2") + "\n"
        + _row(list_key=lk, name="담당자 전화번호", samples="['010-1234-5678']", ordinal="3") + "\n",
        encoding="utf-8",
    )
    db = tmp_path / "obs.db"
    ingest_profile_csv(csv_path, db, {lk: "NO_RESTRICTION"},
                       observed_at="2026-07-29T00:00:00Z")
    monkeypatch.setenv("DATANAV_OBS_DB", str(db))
    from datanav.api.service import Service
    return Service(), covered["recordId"], lk


@requires_catalog
def test_structure_available_with_conservative_mode(svc_with_obs, monkeypatch):
    svc, rid, lk = svc_with_obs
    monkeypatch.delenv("DATANAV_EXAMPLES_PUBLIC", raising=False)  # 기본 = 보수 모드
    body = svc.get_dataset_structure(rid)
    d = body["data"]
    assert d["coverageStatus"] == "AVAILABLE"
    assert d["evidenceLevel"] == "FILE_OBSERVATION"
    assert d["rowCountListed"] == covered_row_count(svc, rid)
    assert d["examplesPublic"] is False
    assert d["assets"][0]["tables"][0]["rowsScanned"] == 100
    assert d["assets"][0]["tables"][0]["rowCountObserved"] == 100
    cols = d["assets"][0]["tables"][0]["columns"]
    assert [c["sourceName"] for c in cols] == ["시설명", "위도", "담당자 전화번호"]
    assert all("examples" not in c for c in cols)          # 보수 모드: 값 비노출
    assert cols[0]["exampleStatus"] == "AVAILABLE"          # 저장 상태는 그대로 보고
    assert any("비공개" in w for w in body["warnings"])       # 정책 고지
    assert "structure-status-v1.0" in body["meta"]["ruleVersions"]


@requires_catalog
def test_structure_examples_when_public(svc_with_obs, monkeypatch):
    svc, rid, _ = svc_with_obs
    monkeypatch.setenv("DATANAV_EXAMPLES_PUBLIC", "1")
    d = svc.get_dataset_structure(rid)["data"]
    assert d["examplesPublic"] is True
    cols = d["assets"][0]["tables"][0]["columns"]
    assert cols[0]["examples"] == ["중앙경로당", "행복경로당"]
    d2 = svc.get_dataset_structure(rid, max_examples=1)["data"]
    assert d2["assets"][0]["tables"][0]["columns"][0]["examples"] == ["중앙경로당"]


@requires_catalog
def test_safety_withheld_never_leaks_via_public_gate(svc_with_obs, monkeypatch):
    """이중 게이트 불변식(P1 회귀): 응답 게이트를 열어도(EXAMPLES_PUBLIC=1)
    안전 차단 컬럼의 값은 나오지 않는다 — 저장 게이트가 이미 폐기했기 때문."""
    import json as _json
    svc, rid, _ = svc_with_obs
    monkeypatch.setenv("DATANAV_EXAMPLES_PUBLIC", "1")
    body = svc.get_dataset_structure(rid)
    cols = {c["sourceName"]: c for c in body["data"]["assets"][0]["tables"][0]["columns"]}
    blocked = cols["담당자 전화번호"]
    assert blocked["exampleStatus"] == "WITHHELD_BY_SAFETY"
    assert blocked["safetyStatus"] == "WITHHELD"
    assert "examples" not in blocked
    # 응답 전체 직렬화에도 차단 값이 존재하지 않는다(유출 경로 전무)
    assert "010-1234-5678" not in _json.dumps(body, ensure_ascii=False)
    # 동일 응답에서 CLEAR 컬럼은 정상 제공 — 게이트가 과차단으로 동작하는 것도 아님
    assert cols["시설명"]["examples"] == ["중앙경로당", "행복경로당"]


@requires_catalog
def test_not_collected_is_normal_response(svc_with_obs, service):
    svc, _, lk = svc_with_obs
    other = next(i for i in service.search_datasets(list_type="FILE", page_size=20)
                 ["data"]["items"] if i["listKey"] != lk)
    d = svc.get_dataset_structure(other["recordId"])["data"]
    assert d["coverageStatus"] == "NOT_COLLECTED"
    assert "assets" not in d                     # 관측 없는 상태 — 오류 아님


@requires_catalog
def test_api_record_reports_not_supported(svc_with_obs, service):
    svc, _, _ = svc_with_obs
    api_rid = service.search_datasets(list_type="API", page_size=1)["data"]["items"][0]["recordId"]
    d = svc.get_dataset_structure(api_rid)["data"]
    assert d["coverageStatus"] == "API_STRUCTURE_NOT_SUPPORTED_YET"


@requires_catalog
def test_search_summary_structure_flag(svc_with_obs):
    svc, rid, lk = svc_with_obs
    items = svc.search_datasets(list_type="FILE", page_size=5)["data"]["items"]
    flags = {i["listKey"]: i["structureAvailable"] for i in items}
    assert flags[lk] is True
    assert any(v is False for v in flags.values())


@requires_catalog
def test_status_reports_structure_coverage(svc_with_obs):
    svc, _, _ = svc_with_obs
    d = svc.get_status()["data"]
    assert d["structureCoverage"]["recordsAvailable"] == 1
    assert d["structureCoverage"]["fileRecordsTotal"] > 0


@requires_catalog
def test_missing_obs_store_degrades_to_not_collected(monkeypatch, service, tmp_path):
    """관측 스토어 미배포: 전 레코드 NOT_COLLECTED — 기존 기능은 영향 없음."""
    monkeypatch.setenv("DATANAV_OBS_DB", str(tmp_path / "없는파일.db"))
    from datanav.api.service import Service
    svc = Service()
    it = svc.search_datasets(list_type="FILE", page_size=1)["data"]["items"][0]
    assert it["structureAvailable"] is False
    assert svc.get_dataset_structure(it["recordId"])["data"]["coverageStatus"] == "NOT_COLLECTED"
    assert "structureCoverage" not in svc.get_status()["data"]


def covered_row_count(svc, rid):
    return svc.get_dataset(rid, "card")["data"]["dataset"]["rowCount"]
