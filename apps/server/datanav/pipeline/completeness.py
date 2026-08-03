"""catalogMetadataCompleteness — 유형별 프로파일 산출(§3.2)."""
from __future__ import annotations

from ..rules import RULE_COMPLETENESS, rule

# 정규화 레코드에서 각 평가 필드의 '기재됨' 판정
_CHECKS = {
    "title": lambda r: bool(r["title"]),
    "theme": lambda r: bool(r["theme_raw"]),
    "org_name": lambda r: bool(r["org_name"]),
    "update_cycle": lambda r: r["update_cycle"] not in ("UNSPECIFIED",),
    "keywords": lambda r: len(r["keywords"]) > 0,
    "description": lambda r: bool(r["description"]),
    "license": lambda r: r["license_code"] not in ("UNSPECIFIED",),
    "created_date": lambda r: bool(r["created_date"]),
    "modified_date": lambda r: bool(r["modified_date"]),
    "list_url": lambda r: bool(r["list_url"]),
    "spatial": lambda r: bool(r["spatial_raw"]),
    "temporal": lambda r: bool(r["temporal_raw"]),
    "data_limits": lambda r: bool(r["data_limits"]),
    "format": lambda r: len(r["formats"]) > 0,
    "row_count": lambda r: r["row_count"] is not None,
    "file_data_name": lambda r: bool(r["file_data_name"]),
    "api_type": lambda r: bool(r["api_type"]),
    "traffic": lambda r: bool(r["traffic"]),
}


def field_status(rec: dict) -> dict:
    """프로파일 점검 필드별 기재 여부 — 카드 뷰 체크리스트용(점수의 분해 근거)."""
    profile = rec["list_type"] if rec["list_type"] in RULE_COMPLETENESS else "FILE"
    fields = rule(RULE_COMPLETENESS[profile])["fields"]
    return {f: bool(_CHECKS[f](rec)) for f in fields}


def compute_completeness(rec: dict) -> dict:
    """응답 예(§3.2): {score, profile, rule}."""
    profile = rec["list_type"] if rec["list_type"] in RULE_COMPLETENESS else "FILE"
    rule_id = RULE_COMPLETENESS[profile]
    fields = rule(rule_id)["fields"]
    filled = sum(1 for f in fields if _CHECKS[f](rec))
    return {
        "score": round(filled / len(fields), 4),
        "profile": profile,
        "rule": rule_id,
        "filledFields": filled,
        "totalFields": len(fields),
    }
