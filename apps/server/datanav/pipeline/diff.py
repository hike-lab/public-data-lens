"""월별 diff(rule: diff-v1.0) — 스냅샷 부재를 폐기로 단정하지 않는다(§4.1)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

# 변경 감지 대상 필드(정규화 기준)
_TRACKED = [
    "title", "org_name", "theme_raw", "update_cycle", "format_raw",
    "license_raw", "modified_date", "description", "list_url", "row_count",
]


def compute_changes(
    curr: sqlite3.Connection,
    prev: sqlite3.Connection,
    base_snapshot: str,
    prev_missing_ids: set[str] | None = None,
    withdrawn_confirmed: set[str] | None = None,
) -> list[dict]:
    """이전 릴리스 DB와 비교해 changes 행 목록 생성."""
    prev_missing_ids = prev_missing_ids or set()
    withdrawn_confirmed = withdrawn_confirmed or set()

    def load(conn):
        cols = ", ".join(["record_id", "list_key"] + _TRACKED)
        return {r[0]: r for r in conn.execute(f"SELECT {cols} FROM datasets")}

    cur_rows, prev_rows = load(curr), load(prev)
    changes = []

    for rid, row in cur_rows.items():
        if rid not in prev_rows:
            status = "REAPPEARED" if rid in prev_missing_ids else "ADDED"
            changes.append(_row(rid, row, status, base_snapshot))
            continue
        prow = prev_rows[rid]
        changed = [
            _TRACKED[i] for i in range(len(_TRACKED)) if row[2 + i] != prow[2 + i]
        ]
        if not changed:
            continue
        # 제목·기관 동시 변경 → 정체성 변경 의심
        if "title" in changed and "org_name" in changed:
            changes.append(_row(rid, row, "POSSIBLE_IDENTITY_CHANGE", base_snapshot, changed))
        else:
            changes.append(_row(rid, row, "MODIFIED", base_snapshot, changed))

    for rid, prow in prev_rows.items():
        if rid in cur_rows:
            continue
        status = (
            "OFFICIALLY_WITHDRAWN" if rid in withdrawn_confirmed  # 포털 명시 확인 시에만
            else "MISSING_FROM_SNAPSHOT"
        )
        changes.append(_row(rid, prow, status, base_snapshot))

    return changes


def _row(rid, row, status, base_snapshot, changed_fields=None) -> dict:
    return {
        "record_id": rid,
        "list_key": row[1],
        "status": status,
        "changed_fields": json.dumps(changed_fields, ensure_ascii=False) if changed_fields else None,
        "base_snapshot": base_snapshot,
        "title": row[2],
        "org_name": row[3],
    }


def load_withdrawn_confirmed(path: Path) -> set[str]:
    """포털에서 폐기가 명시 확인된 목록키(수동 관리 파일)."""
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")).get("recordIds", []))
