"""§11 수용 기준: 커서 페이징 무중복·무누락, 4뷰 정합, 오류 일관성, 전 응답 스냅샷·rule 버전."""
import pytest

from datanav.api.errors import (
    DatasetNotFound,
    InvalidArgument,
    TooManyDatasets,
)

def _envelope_ok(body):
    assert set(body) == {"data", "meta", "warnings", "notices"}  # notices: v1.5 additive
    assert body["meta"]["sourceSnapshot"]
    from datanav.config import SCHEMA_VERSION
    assert body["meta"]["schemaVersion"] == SCHEMA_VERSION
    assert isinstance(body["meta"]["ruleVersions"], list)
    assert any("보증하지 않습니다" in w for w in body["warnings"])  # 면책 고지
    # notices는 warnings의 구조화 미러 — 개수 일치, 면책 고지는 severity=info
    assert [n["text"] for n in body["notices"]] == body["warnings"]
    assert any(n["code"] == "DISCLAIMER" and n["severity"] == "info" for n in body["notices"])


def test_search_envelope_and_ranking_meta(catalog_service):
    r = catalog_service.search_datasets(query="도서관", page_size=10)
    _envelope_ok(r)
    rk = r["data"]["ranking"]
    assert rk["version"] == "ranking-bm25-v1.0"
    assert rk["indexVersion"] and rk["tieBreak"]


def test_cursor_pagination_no_dup_no_gap(catalog_service):
    seen = []
    cursor = None
    for _ in range(3):
        r = catalog_service.search_datasets(page_size=2, cursor=cursor)
        ids = [i["recordId"] for i in r["data"]["items"]]
        seen.extend(ids)
        cursor = r["data"]["nextCursor"]
        if not cursor:
            break
    assert len(seen) == len(set(seen))  # 무중복
    total = catalog_service.search_datasets(page_size=50)["data"]["totalEstimate"]
    assert len(seen) == total  # 무누락


def test_four_views_consistency(catalog_service):
    rid = catalog_service.search_datasets(page_size=1)["data"]["items"][0]["recordId"]
    card = catalog_service.get_dataset(rid, "card")["data"]["dataset"]
    norm = catalog_service.get_dataset(rid, "normalized")["data"]["dataset"]
    src = catalog_service.get_dataset(rid, "source")["data"]["dataset"]
    jld = catalog_service.get_dataset(rid, "jsonld")["data"]["dataset"]
    assert card["title"] == norm["title"] == src["sourceFields"]["목록명"] == jld["title"]
    assert card["listKey"] == norm["list_key"] == src["sourceFields"]["목록키"]
    # 정본 URI는 목록키 기반 불변(§7), record_id는 내부 식별자(kdp:recordId)
    assert jld["@id"].endswith(f"/dataset/{card['listKey']}")
    assert jld["kdp:recordId"] == rid
    assert jld["kdp:evidenceLevel"] == "CATALOG_METADATA_ONLY"
    assert jld["kdp:qualityTier"] is None
    assert jld["kdp:diagnosticMaturity"] is None
    # card 재구성 규칙 버전 표기
    assert card["cardRule"] == "card-projection-v1.0"


def test_jsonld_preserves_row_count_mapping(catalog_service):
    with_rows = catalog_service.get_dataset("rec-001", "jsonld")["data"]["dataset"]
    assert with_rows["dcatkr:numberOfRow"] == 100
    assert isinstance(with_rows["dcatkr:numberOfRow"], int)

    zero_rows = catalog_service.get_dataset("rec-002", "jsonld")["data"]["dataset"]
    assert zero_rows["dcatkr:numberOfRow"] == 0

    missing_rows = catalog_service.get_dataset("rec-003", "jsonld")["data"]["dataset"]
    assert "dcatkr:numberOfRow" not in missing_rows


def test_error_consistency(catalog_service):
    with pytest.raises(DatasetNotFound):
        catalog_service.get_dataset("no-such-id", "card")
    with pytest.raises(InvalidArgument):
        catalog_service.get_dataset("rec-001", "bogus-view")
    with pytest.raises(TooManyDatasets):
        catalog_service.compare_datasets(["a", "b", "c", "d", "e", "f"])
    with pytest.raises(InvalidArgument):
        catalog_service.search_datasets(query="x" * 501)
    with pytest.raises(InvalidArgument):
        catalog_service.search_datasets(cursor="박살난커서")
    err = DatasetNotFound("x").to_dict("2026-02")
    assert set(err["error"]) == {"code", "message", "details", "sourceSnapshot"}


def test_compare_is_fact_only(catalog_service):
    ids = [i["recordId"] for i in catalog_service.search_datasets(page_size=2)["data"]["items"]]
    r = catalog_service.compare_datasets(ids)
    _envelope_ok(r)
    assert "해석" in r["data"]["note"]  # 무해석 명시
    for d in r["data"]["differences"]:
        assert set(d) == {"field", "values"}  # 사실 구조만


def test_changes_no_baseline_warning(catalog_service):
    r = catalog_service.get_catalog_changes()
    _envelope_ok(r)
    if r["data"]["baseSnapshot"] is None:
        assert any("이전 스냅샷" in w for w in r["warnings"])


def test_stats_completeness_by_profile(catalog_service):
    r = catalog_service.get_catalog_stats("completeness")
    _envelope_ok(r)
    profiles = {p["profile"]: p for p in r["data"]["profiles"]}
    assert set(profiles) == {"FILE", "API", "STD"}
    for p in profiles.values():
        assert p["rule"].startswith("catalog-completeness-")


def test_region_evidence_in_results(catalog_service):
    r = catalog_service.search_datasets(region="KR-11", include_inferred=False, page_size=5)
    for item in r["data"]["items"]:
        seoul = [x for x in item["regions"] if x["code"] == "KR-11"]
        assert seoul and seoul[0]["evidence"] == "EXPLICIT_SPATIAL"
