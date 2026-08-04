"""query-interpret-v1.0 골든 케이스 가드 — evals/query_interpret_cases.json과 구현의 일치."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from datanav.api.plan import RULE_QUERY_INTERPRET, interpret_query

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "evals" / "query_interpret_cases.json")
    .read_text(encoding="utf-8")
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["query"] for c in CASES])
def test_golden_case(case):
    rest, interpreted = interpret_query(case["query"])
    got = {f["field"]: f["value"] for f in interpreted}
    assert got == case["expect"], f"해석 불일치: {case['query']}"
    assert rest == case["rest"]
    for f in interpreted:
        assert f["ruleId"] == RULE_QUERY_INTERPRET
        assert f["sourceToken"] in case["query"].split()


def test_explicit_filter_wins():
    """명시 필터가 있는 축은 해석하지 않는다 — 토큰은 질의에 남는다."""
    rest, interpreted = interpret_query("서울 무더위 쉼터", skip_fields={"region"})
    assert interpreted == []
    assert rest == "서울 무더위 쉼터"
