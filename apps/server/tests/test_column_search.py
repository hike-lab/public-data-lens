"""S2 — 컬럼 기준 검색(search_by_columns)과 비교의 구조 섹션(계약 v1.3).
핵심 수용 기준(v2.2 §12): 검색 결과에 근거(matchedColumns)·커버리지 필수 표기."""
from __future__ import annotations

import pytest

from datanav.api.errors import InvalidArgument
from datanav.observe.ingest import ingest_profile_csv
from tests.conftest import requires_catalog
from tests.test_observe_ingest import HEADER, _row


@pytest.fixture()
def svc_two_obs(tmp_path, monkeypatch, service):
    """실카탈로그 FILE 레코드 2개에 합성 관측 부착 — A(위도·경도·시설명), B(위도·주소)."""
    items = service.search_datasets(list_type="FILE", page_size=3)["data"]["items"]
    a, b, uncovered = items[0], items[1], items[2]
    csv_path = tmp_path / "profile.csv"
    csv_path.write_text(
        "﻿" + HEADER + "\n"
        + _row(list_key=a["listKey"], ordinal="1") + "\n"                              # 시설명
        + _row(list_key=a["listKey"], name="위도", samples="['37.5']", ordinal="2") + "\n"
        + _row(list_key=a["listKey"], name="경도", samples="['127.0']", ordinal="3") + "\n"
        + _row(list_key=b["listKey"], name="위도", samples="['36.2']", ordinal="1") + "\n"
        + _row(list_key=b["listKey"], name="소재지도로명주소", samples="['서울시']", ordinal="2") + "\n",
        encoding="utf-8",
    )
    db = tmp_path / "obs.db"
    ingest_profile_csv(csv_path, db,
                       {a["listKey"]: "NO_RESTRICTION", b["listKey"]: "NO_RESTRICTION"},
                       observed_at="2026-07-29T00:00:00Z")
    monkeypatch.setenv("DATANAV_OBS_DB", str(db))
    from datanav.api.service import Service
    return Service(), a, b, uncovered


@requires_catalog
def test_and_semantics_with_evidence(svc_two_obs):
    svc, a, b, _ = svc_two_obs
    body = svc.search_by_columns(["위도", "경도"])
    d = body["data"]
    assert d["totalEstimate"] == 1                       # 둘 다 가진 것은 A뿐(AND)
    item = d["items"][0]
    assert item["listKey"] == a["listKey"]
    ev = {m["keyword"]: m["columns"] for m in item["matchedColumns"]}
    assert ev == {"위도": ["위도"], "경도": ["경도"]}       # 검색 근거 필수
    assert d["coverage"]["searchedRecords"] == 2         # 커버리지 명시
    assert any("미수집" in w for w in body["warnings"])    # '없음 ≠ 미수집' 고지


@requires_catalog
def test_partial_match_and_substring(svc_two_obs):
    svc, a, b, _ = svc_two_obs
    d = svc.search_by_columns(["위도"])["data"]
    assert d["totalEstimate"] == 2                       # A·B 모두
    d2 = svc.search_by_columns(["주소"])["data"]           # 부분 일치: 소재지도로명주소
    assert d2["totalEstimate"] == 1
    assert d2["items"][0]["listKey"] == b["listKey"]
    assert d2["items"][0]["matchedColumns"][0]["columns"] == ["소재지도로명주소"]


@requires_catalog
def test_input_validation(svc_two_obs):
    svc, *_ = svc_two_obs
    with pytest.raises(InvalidArgument):
        svc.search_by_columns([])
    with pytest.raises(InvalidArgument):
        svc.search_by_columns(["a", "b", "c", "d", "e", "f"])
    with pytest.raises(InvalidArgument):
        svc.search_by_columns(["가" * 51])


@requires_catalog
def test_compare_structure_section(svc_two_obs):
    svc, a, b, uncovered = svc_two_obs
    body = svc.compare_datasets([a["recordId"], b["recordId"]])
    sc = body["data"]["structureComparison"]
    assert sc["commonColumns"] == ["위도"]                # 원본명 정확 일치만
    assert set(sc["onlyIn"][a["recordId"]]) == {"경도", "시설명"}
    assert set(sc["onlyIn"][b["recordId"]]) == {"소재지도로명주소"}
    assert "의미 동일성" in sc["note"]                     # 비단정 문구 필수

    # 일부만 관측: 구조 비교 생략 + 경고(미수집 ≠ 없음)
    body2 = svc.compare_datasets([a["recordId"], uncovered["recordId"]])
    assert "structureComparison" not in body2["data"]
    assert any("일부" in w for w in body2["warnings"])


@pytest.fixture()
def svc_wildcard_obs(tmp_path, monkeypatch, catalog_service):
    csv_path = tmp_path / "profile.csv"
    csv_path.write_text(
        "﻿" + HEADER + "\n"
        + _row(list_key="list-001", name="일반컬럼", ordinal="1") + "\n"
        + _row(list_key="list-002", name="진짜%컬럼", ordinal="1") + "\n"
        + _row(list_key="list-003", name="진짜_컬럼", ordinal="1") + "\n"
        + _row(list_key="list-003", name=r"역슬래시\\컬럼", ordinal="2") + "\n",
        encoding="utf-8",
    )
    db = tmp_path / "obs.db"
    ingest_profile_csv(
        csv_path,
        db,
        {"list-001": "NO_RESTRICTION", "list-002": "NO_RESTRICTION", "list-003": "NO_RESTRICTION"},
        observed_at="2026-07-29T00:00:00Z",
    )
    monkeypatch.setenv("DATANAV_OBS_DB", str(db))
    from datanav.api.service import Service
    return Service(catalog_service._db_path)


def test_column_search_treats_percent_as_literal(svc_wildcard_obs):
    d = svc_wildcard_obs.search_by_columns(["%"])["data"]
    assert d["totalEstimate"] == 1
    assert d["items"][0]["listKey"] == "list-002"
    assert d["items"][0]["matchedColumns"][0]["columns"] == ["진짜%컬럼"]


def test_column_search_treats_underscore_as_literal(svc_wildcard_obs):
    d = svc_wildcard_obs.search_by_columns(["_"])["data"]
    assert d["totalEstimate"] == 1
    assert d["items"][0]["listKey"] == "list-003"
    assert d["items"][0]["matchedColumns"][0]["columns"] == ["진짜_컬럼"]


def test_column_search_treats_escape_character_as_literal(svc_wildcard_obs):
    d = svc_wildcard_obs.search_by_columns([r"\\"])["data"]
    assert d["totalEstimate"] == 1
    assert d["items"][0]["listKey"] == "list-003"
    assert d["items"][0]["matchedColumns"][0]["columns"] == [r"역슬래시\\컬럼"]


def test_column_search_keeps_normal_and_injection_like_inputs(svc_wildcard_obs):
    normal = svc_wildcard_obs.search_by_columns(["컬럼"])["data"]
    assert normal["totalEstimate"] == 3

    injected = svc_wildcard_obs.search_by_columns(["%' OR 1=1 --"])["data"]
    assert injected["totalEstimate"] == 0
