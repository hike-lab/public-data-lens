"""evals/cases 자산 가드(ADR-010·ADR-013) — 케이스가 스키마에 맞고 id=파일명인지 보증한다.

케이스는 '이 입력이면 이 판정이 맞다'의 정형 기록이다. 스키마 위반 케이스가 쌓이면
자산이 아니라 잡동사니가 된다.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "evals" / "schema" / "case.schema.json"
CASES = sorted((ROOT / "evals" / "cases").glob("*.json"))


def test_cases_exist():
    assert CASES, "evals/cases가 비어 있다 — 최소 1건의 판정 케이스가 있어야 한다"


def test_cases_match_schema_and_filename():
    validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    for p in CASES:
        case = json.loads(p.read_text(encoding="utf-8"))
        errors = [e.message for e in validator.iter_errors(case)]
        assert not errors, f"{p.name}: {errors}"
        assert case["id"] == p.stem, f"{p.name}: id({case['id']})와 파일명이 다르다"
