"""소형 fixture로 빌드 전 과정을 재현 검증 — 실카탈로그 없이도 파이프라인이 검증되도록 한다."""
from __future__ import annotations

import csv
import gzip
import json

import pytest

from datanav.pipeline.parse import COLUMN_MAP

BASE_ROW = {
    "목록키": "", "목록유형": "FILE", "목록명": "", "파일데이터명": "테스트_20260101",
    "분류체계": "공공행정 - 일반행정", "제공기관코드": "1000000", "제공기관": "테스트기관",
    "관리 부서명": "팀", "관리부서 전화번호": "021234567", "보유근거": "-", "수집방법": "-",
    "업데이트 주기": "연간", "차기 등록 예정일": "2027-01-01", "매체유형": "텍스트",
    "전체행": "100", "확장자(데이터포맷)": "csv", "키워드": "테스트,데이터",
    "다운로드_활용신청건수": "5", "등록일": "2024-01-01", "수정일": "2026-01-15",
    "데이터 한계": "-", "제공형태": "다운로드", "설명": "테스트 설명입니다",
    "기타 유의사항": "-", "공간범위": "서울특별시", "시간범위": "2025년",
    "비용부과유무": "무료", "비용부과기준 및 단위": "-", "이용허락범위": "공공저작물_출처표시",
    "API 유형": "-", "신청가능 트래픽": "-", "심의 유형": "-", "조회수": "10",
    "목록 URL": "", "국가중점여부": "N", "표준데이터여부": "N",
}


def make_fixture_csv(path, n_unique=20, encoding="utf-8-sig"):
    rows = []
    for i in range(n_unique):
        r = dict(BASE_ROW)
        r["목록키"] = f"1500{i:04d}"
        r["목록명"] = f"테스트_데이터셋_{i}"
        r["목록 URL"] = f"https://www.data.go.kr/data/1500{i:04d}/fileData.do"
        rows.append(r)
    # 중복 목록키(FILE/API 이중 등재) 1쌍
    dup = dict(BASE_ROW, **{
        "목록키": "1509999", "목록명": "이중등재_데이터", "목록유형": "API",
        "API 유형": "REST", "확장자(데이터포맷)": "JSON", "전체행": "-",
        "목록 URL": "https://www.data.go.kr/data/1509999/openapi.do",
    })
    dup_file = dict(BASE_ROW, **{
        "목록키": "1509999", "목록명": "이중등재_데이터",
        "목록 URL": "https://www.data.go.kr/data/1509999/fileData.do",
    })
    rows += [dup_file, dup]
    # 더미값 행(D5-03 감점 대상) + 백틱 전화번호(이슈 관찰 대상)
    bad = dict(BASE_ROW, **{
        "목록키": "1508888", "목록명": "더미값_데이터", "전체행": "9999",
        "관리부서 전화번호": "`021234567",
        "목록 URL": "https://www.data.go.kr/data/1508888/fileData.do",
    })
    rows.append(bad)

    with open(path, "w", encoding=encoding, newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMN_MAP))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


@pytest.fixture()
def isolated_config(tmp_path, monkeypatch):
    from datanav import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(config, "CATALOG_DIR", tmp_path / "data" / "catalog")
    monkeypatch.setattr(config, "RELEASES_DIR", tmp_path / "data" / "catalog" / "releases")
    monkeypatch.setattr(config, "CURRENT_POINTER", tmp_path / "data" / "catalog" / "current.json")
    (tmp_path / "data" / "catalog" / "releases").mkdir(parents=True)
    return config


def test_full_build_on_fixture(tmp_path, isolated_config):
    from datanav.pipeline.build import build_release

    csv_path = tmp_path / "fixture.csv"
    total = make_fixture_csv(csv_path)

    release_dir = build_release(csv_path, "9999-01", min_rows=5)
    report = json.loads((release_dir / "build_report.json").read_text(encoding="utf-8"))

    # 수용 검사(§11)
    assert all(v["pass"] for v in report["acceptance"].values())
    assert report["insertedRows"] == total
    assert report["duplicateListKeys"] == 1
    assert report["sourceEncoding"] == "utf-8-sig"

    # 표준 MMI 진단(aird-mmi-v1.1): 더미 1셀·중복 키에도 소형 셋은 DM-0 통과
    assert report["aird"]["rule"] == "aird-mmi-v1.1"
    assert report["aird"]["qualityIndexMMI"] >= 0.7
    assert report["aird"]["label"] == "DM-0 (기본 적합성, STRUCT, 참고)"

    assessment = json.loads(
        (release_dir / "aird-assessment-9999-01.jsonld").read_text(encoding="utf-8")
    )
    scores = {i["kdp:indicatorId"]: i["kdp:score"] for i in assessment["kdp:indicators"]}
    assert scores["D6-01"] < 1.0  # 중복 목록키 반영
    assert scores["D5-03"] < 1.0  # 더미값 9999 반영
    assert assessment["prov:wasGeneratedBy"]["kdp:sourceSha256"]
    assert assessment["@context"]  # 단독 해석 가능한 JSON-LD

    # 벌크 정본: 라인 수 = 레코드 수, Dataset URI는 목록키 기반
    bulk = report["bulk"]
    assert bulk["datasets"]["lines"] == total == bulk["catalogRecords"]["lines"]
    with gzip.open(release_dir / bulk["datasets"]["file"], "rt", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]
    dup_docs = [d for d in docs if d["kdp:listKey"] == "1509999"]
    assert len(dup_docs) == 2
    assert all(d["@id"].endswith("/dataset/1509999") for d in dup_docs)  # 불변 URI 공유
    assert {d["kdp:recordId"] for d in dup_docs} == {"1509999-FILE", "1509999-API"}

    # 이슈 관찰 DQV 벌크: 백틱 1 + 중복키 2
    assert bulk["qualityAnnotations"]["lines"] >= 3
    with gzip.open(release_dir / bulk["qualityAnnotations"]["file"], "rt", encoding="utf-8") as f:
        anns = [json.loads(line) for line in f]
    assert all(a["@type"] == "dqv:QualityAnnotation" for a in anns)
    assert all("prov:wasGeneratedBy" in a for a in anns)

    # 원자적 배포: 포인터가 새 릴리스를 가리킴
    ptr = json.loads(isolated_config.CURRENT_POINTER.read_text(encoding="utf-8"))
    assert ptr["snapshot"] == "9999-01"


def test_same_snapshot_rebuild_carries_changes(tmp_path, isolated_config):
    """같은 스냅샷 재빌드 시 이전 릴리스의 diff를 승계해야 한다(변경 피드 소실 방지)."""
    from datanav.pipeline.build import build_release

    csv1 = tmp_path / "a.csv"
    make_fixture_csv(csv1, n_unique=20)
    build_release(csv1, "9999-01", min_rows=5)

    csv2 = tmp_path / "b.csv"
    make_fixture_csv(csv2, n_unique=19)  # 1행 제거 → MISSING 1 발생
    rel2 = build_release(csv2, "9999-02", min_rows=5)
    r2 = json.loads((rel2 / "build_report.json").read_text(encoding="utf-8"))
    assert r2["diff"]["counts"].get("MISSING_FROM_SNAPSHOT") == 1

    rel3 = build_release(csv2, "9999-02", min_rows=5)  # 같은 스냅샷 재빌드
    r3 = json.loads((rel3 / "build_report.json").read_text(encoding="utf-8"))
    assert r3["diff"]["counts"] == r2["diff"]["counts"]  # diff 승계
    assert r3["diff"]["baseSnapshot"] == "9999-01"
    assert "carriedFrom" in r3["diff"]


def test_full_build_on_cp949_fixture(tmp_path, isolated_config):
    """CP949 원본도 전 과정 빌드되고 감지 인코딩이 메타·리포트에 기록된다(P1 회귀)."""
    from datanav.pipeline.build import build_release

    csv_path = tmp_path / "fixture_cp949.csv"
    total = make_fixture_csv(csv_path, encoding="cp949")

    release_dir = build_release(csv_path, "9999-02", min_rows=5)
    report = json.loads((release_dir / "build_report.json").read_text(encoding="utf-8"))
    assert report["sourceEncoding"] == "cp949"
    assert report["insertedRows"] == total
    assert all(v["pass"] for v in report["acceptance"].values())

    meta = json.loads(
        (isolated_config.RAW_DIR / "9999-02" / "meta.json").read_text(encoding="utf-8")
    )
    assert meta["encoding"] == "cp949"


def test_detect_encoding_prefers_utf8_and_rejects_unknown(tmp_path):
    from datanav.pipeline.parse import ParseError, detect_encoding

    utf8 = tmp_path / "u.csv"
    utf8.write_text("목록키,목록명\n1,가나다\n", encoding="utf-8-sig")
    assert detect_encoding(utf8) == "utf-8-sig"

    cp949 = tmp_path / "c.csv"
    cp949.write_text("목록키,목록명\n1,가나다\n", encoding="cp949")
    assert detect_encoding(cp949) == "cp949"

    bogus = tmp_path / "b.csv"
    bogus.write_bytes(b"\xff\xfe\x00\xd8ok")  # utf-8도 cp949도 아닌 바이트열
    with pytest.raises(ParseError):
        detect_encoding(bogus)
