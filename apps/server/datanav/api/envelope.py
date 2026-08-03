"""응답 봉투(§4.3): { data, meta: { sourceSnapshot, processedAt, schemaVersion, ruleVersions[] }, warnings[] }"""
from __future__ import annotations

import base64
import datetime as dt
import json

from ..config import DISCLAIMER, SCHEMA_VERSION
from .errors import InvalidArgument


def envelope(
    data,
    source_snapshot: str,
    rule_versions: list[str],
    warnings: list[str] | None = None,
) -> dict:
    w = list(warnings or [])
    w.append(DISCLAIMER)  # 면책 고지: 모든 응답에 포함(§10)
    return {
        "data": data,
        "meta": {
            "sourceSnapshot": source_snapshot,
            "processedAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schemaVersion": SCHEMA_VERSION,
            "ruleVersions": sorted(set(rule_versions)),
        },
        "warnings": w,
    }


def encode_cursor(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")


def decode_cursor(cursor: str, expected_snapshot: str) -> dict:
    try:
        pad = "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(cursor + pad))
    except Exception as e:
        raise InvalidArgument("cursor 형식이 올바르지 않습니다", {"cursor": cursor}) from e
    if payload.get("s") != expected_snapshot:
        raise InvalidArgument(
            "cursor가 현재 스냅샷과 일치하지 않습니다 — 처음부터 다시 조회하세요",
            {"cursorSnapshot": payload.get("s"), "currentSnapshot": expected_snapshot},
        )
    offset = payload.get("o", 0)
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise InvalidArgument("cursor 형식이 올바르지 않습니다", {"cursor": cursor})
    return payload
