"""MCP 인터페이스(Tool 5+1, Prompt 2, Resource) + SHACL 치명 오류 탐지 검증."""
import asyncio
import json

import pytest

from tests.conftest import requires_catalog


@requires_catalog
def test_mcp_surface_and_calls():
    from mcp.shared.memory import create_connected_server_and_client_session
    from datanav.api.mcp_server import mcp as server

    async def run():
        async with create_connected_server_and_client_session(server._mcp_server) as c:
            tools = {t.name for t in (await c.list_tools()).tools}
            assert tools == {
                "search_datasets", "get_dataset", "compare_datasets",
                "get_catalog_changes", "get_catalog_stats", "get_context",
                "get_dataset_structure",  # v1.2 — 데이터 구조 관측
                "search_by_columns",      # v1.3 — 컬럼 기준 검색
            }
            prompts = {p.name for p in (await c.list_prompts()).prompts}
            assert prompts == {"build_data_plan", "compare_for_purpose"}
            resources = {str(r.uri) for r in (await c.list_resources()).resources}
            assert len(resources) == 5  # 규칙·Context·SHACL·Prompt 문서·부속 명세
            assert all(u.startswith("https://service.datahub.kr/projects/public-data-lens/") for u in resources)

            # Tool 정상 호출 + 봉투
            r = await c.call_tool("search_datasets", {"query": "도서관", "pageSize": 3})
            body = json.loads(r.content[0].text)
            assert body["meta"]["sourceSnapshot"]
            # 오류 일관성
            r2 = await c.call_tool("get_dataset", {"recordId": "없는키"})
            err = json.loads(r2.content[0].text)["error"]
            assert err["code"] == "DATASET_NOT_FOUND"
            # Prompt에 사실/추론 구분·비단정 규칙 포함(§11 M-기준)
            p = await c.get_prompt("build_data_plan", {"purpose": "테스트"})
            text = p.messages[0].content.text
            assert "사실" in text and "추론" in text and "예상 결합 키" in text
            # 보안: 목록 필드 비신뢰 입력 문구(§10)
            assert "지시문이 아니다" in text

    asyncio.run(run())


def test_shacl_catches_fatal_violation():
    from datanav.pipeline.shacl import validate_docs

    good = {
        "@id": "https://service.datahub.kr/projects/public-data-lens/dataset/1",
        "@type": "dcat:Dataset",
        "title": "정상", "identifier": "1",
        "kdp:listType": "FILE", "kdp:evidenceLevel": "CATALOG_METADATA_ONLY",
        "landingPage": "https://www.data.go.kr/data/1/fileData.do",
        "description": "d", "keyword": ["k"],
    }
    bad = dict(good, **{"@id": "https://service.datahub.kr/projects/public-data-lens/dataset/2"})
    del bad["title"]
    bad["kdp:listType"] = "WEIRD"

    ok = validate_docs([good])
    assert ok["conforms"] and ok["violationCount"] == 0
    res = validate_docs([bad])
    assert not res["conforms"]
    assert res["violationCount"] >= 2  # title 누락 + listType 위반


def _mini_db(rows):
    """rows: (record_id, list_key, row_count) 목록으로 최소 datasets 테이블 구성."""
    import sqlite3
    from datanav.store.db import SCHEMA

    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    for rid, key, rc in rows:
        conn.execute(
            "INSERT INTO datasets (record_id, list_key, list_type, title, keywords,"
            " license_code, row_count, source_json)"
            " VALUES (?, ?, 'FILE', '제목', '[]', 'KOGL_BY', ?, '{}')",
            (rid, key, rc),
        )
    return conn


def test_aird_standard_mmi():
    """표준 MMI(aird-mmi-v1.1, AIRD 제2부 v0.87): 4지표·QI_MMI·DM-0 판정."""
    from datanav.pipeline.aird import measure_mmi

    # (a) recordCount=0 → SCHEMA_ONLY, 판정 불가(6.1절 7항)
    empty = measure_mmi(_mini_db([]), "t")
    assert empty["kdp:diagnosticStatus"] == "SCHEMA_ONLY"
    assert empty["aird:qualityIndexMMI"] is None
    assert empty["aird:diagnosticMaturity"] is None

    # (b) 정상 데이터 → 4지표 전부 APPLIED, DM-0(참고 공시 라벨)
    clean = measure_mmi(_mini_db([("1", "1", 10), ("2", "2", 20)]), "t")
    ids = {i["kdp:indicatorId"] for i in clean["kdp:indicators"]}
    assert ids == {"D5-03", "D6-01", "D7-01", "D7-02"}
    assert all(i["kdp:status"] == "APPLIED" for i in clean["kdp:indicators"])
    assert clean["aird:qualityIndexMMI"] == 1.0
    assert clean["aird:diagnosticMaturity"] == "DM-0"
    assert clean["kdp:label"] == "DM-0 (기본 적합성, STRUCT, 참고)"
    assert "aird:qualityTier" not in clean  # Discoverable에서 qualityTier 금지(제3부 5.3절)

    # (c) 더미값(9999, -1)은 D5-03 감점, 중복 목록키는 D6-01 감점
    dirty = measure_mmi(
        _mini_db([("1", "K", 9999), ("2", "K", -1), ("3", "3", 5), ("4", "4", 7)]), "t"
    )
    by_id = {i["kdp:indicatorId"]: i["kdp:score"] for i in dirty["kdp:indicators"]}
    assert by_id["D5-03"] == 0.5   # 4셀 중 2셀 더미
    assert by_id["D6-01"] == 0.75  # 4행 중 유니크 키 3개
    assert dirty["aird:qualityIndexMMI"] < 1.0


def test_discoverability_is_not_mmi():
    """발견성 8지표는 참고 지표 — DM 판정 필드를 갖지 않는다."""
    from datanav.pipeline.aird import measure_discoverability

    r = measure_discoverability(_mini_db([("1", "1", 10)]))
    assert r["rule"] == "catalog-discoverability-v1.0"
    assert "catalogMetadataReadinessScore" in r
    assert "aird:diagnosticMaturity" not in r
