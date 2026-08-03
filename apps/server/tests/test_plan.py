"""build_data_plan(계약 v1.4) — 결정론적 계획 조립기의 경계 검증.

핵심 계약: 항상 DRAFT, 품질 NOT_ASSESSED, 결합 키 CANDIDATE_ONLY,
검색 0건은 오류가 아니라 요구 미충족(missingNeeds)으로 보고.
"""
from __future__ import annotations

import pytest

from datanav.api.errors import InvalidArgument
from datanav.api.plan import build_plan, _extract_terms
from tests.conftest import requires_catalog


def test_extract_terms_strips_particles_stopwords_and_region():
    terms, region = _extract_terms("서울 무더위 쉼터를 분석하고 싶다")
    assert region == "KR-11"
    assert "무더위" in terms and "쉼터" in terms
    assert all(t not in terms for t in ("서울", "싶다", "분석하고"))


@requires_catalog
def test_plan_is_always_draft_and_never_asserts_fit(service):
    body = build_plan(service, "어린이 보호구역 안전을 분석하고 싶다", max_candidates=5)
    d = body["data"]
    assert d["planStatus"] == "DRAFT"
    assert d["qualityAssessment"] == "NOT_ASSESSED"
    assert 1 <= len(d["recommendedDatasets"]) <= 5
    for c in d["recommendedDatasets"]:
        assert c["candidateStatus"] == "CANDIDATE_DATASET"
        assert c["roles"] and c["whySelected"] and c["limitations"]
        assert c["fitSignals"]["searchRelevance"] in ("HIGH", "MEDIUM", "LOW")
    for k in d["possibleJoinKeys"]:
        assert k["status"] == "CANDIDATE_ONLY"
        assert len(k["observedIn"]) >= 2
    # 초안 고지 + 규칙 버전
    assert any("초안(DRAFT)" in w for w in body["warnings"])
    assert "plan-assembly-v1.0" in body["meta"]["ruleVersions"]


@requires_catalog
def test_region_parameter_accepts_name_and_code(service):
    by_name = build_plan(service, "무더위 쉼터 현황", region="서울특별시", max_candidates=3)
    assert by_name["data"]["interpretedPurpose"]["regionApplied"] == "KR-11"
    assert by_name["data"]["interpretedPurpose"]["regionSource"] == "PARAMETER"
    by_code = build_plan(service, "무더위 쉼터 현황", region="KR-26", max_candidates=3)
    assert by_code["data"]["interpretedPurpose"]["regionApplied"] == "KR-26"


@requires_catalog
def test_region_from_purpose_text(service):
    body = build_plan(service, "부산 버스 정류장 위치 현황", max_candidates=3)
    ip = body["data"]["interpretedPurpose"]
    assert ip["regionApplied"] == "KR-26"
    assert ip["regionSource"] == "PURPOSE_TEXT"


@requires_catalog
def test_no_results_reports_unsatisfied_not_error(service):
    body = build_plan(service, "존재하지않는주제어구십구", max_candidates=3)
    d = body["data"]
    assert d["planStatus"] == "DRAFT"  # 실패가 아니다
    assert d["recommendedDatasets"] == []
    assert any(n["status"] == "UNSATISFIED" for n in d["dataNeeds"])
    assert d["missingNeeds"] and d["missingNeeds"][0]["reason"]


@requires_catalog
def test_analysis_hint_adds_demand_supply_needs(service):
    body = build_plan(service, "고령자 의료 접근성을 분석하고 싶다", max_candidates=5)
    roles = {n["role"] for n in body["data"]["dataNeeds"]}
    assert {"PRIMARY", "SPATIAL", "TEMPORAL", "DEMAND", "SUPPLY"} <= roles


def test_invalid_inputs(service_or_none=None):
    class _Svc:  # purpose 검증은 검색 전에 일어난다 — 서비스 불필요
        snapshot = "test"
    with pytest.raises(InvalidArgument):
        build_plan(_Svc(), "짧")
    with pytest.raises(InvalidArgument):
        build_plan(_Svc(), "x" * 300)
    with pytest.raises(InvalidArgument):
        build_plan(_Svc(), "무더위 쉼터 현황", region="아틀란티스")
