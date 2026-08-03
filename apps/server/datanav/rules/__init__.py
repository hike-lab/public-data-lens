"""판정 규칙 레지스트리(§5) — rule-id·버전·정의를 코드에 암묵화하지 않고 공개한다."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent / "registry.json"


@lru_cache(maxsize=1)
def load_registry() -> dict:
    return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def rule(rule_id: str) -> dict:
    for r in load_registry()["rules"]:
        if r["ruleId"] == rule_id:
            return r
    raise KeyError(f"미등록 규칙: {rule_id}")


RULE_COMPLETENESS = {
    "FILE": "catalog-completeness-file-v1.0",
    "API": "catalog-completeness-api-v1.0",
    "STD": "catalog-completeness-std-v1.0",
}
RULE_FORMAT = "normalize-format-v1.0"
RULE_CYCLE = "normalize-cycle-v1.0"
RULE_LICENSE = "normalize-license-v1.0"
RULE_IDENTITY = "record-identity-v1.0"
RULE_REGION = "region-match-v1.0"
RULE_RANKING = "ranking-bm25-v1.0"
RULE_CARD = "card-projection-v1.0"
RULE_DIFF = "diff-v1.0"
RULE_ISSUE = "issue-detect-v1.0"
RULE_FRESHNESS = "freshness-v1.0"
RULE_AIRD = "aird-mmi-v1.1"
RULE_DISCOVERABILITY = "catalog-discoverability-v1.0"
