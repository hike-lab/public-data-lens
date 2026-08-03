import sqlite3

from datanav.pipeline.diff import compute_changes

_COLS = (
    "record_id, list_key, title, org_name, theme_raw, update_cycle, format_raw, "
    "license_raw, modified_date, description, list_url, row_count"
)


def _db(rows):
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE datasets (record_id TEXT, list_key TEXT, title TEXT, org_name TEXT,"
        " theme_raw TEXT, update_cycle TEXT, format_raw TEXT, license_raw TEXT,"
        " modified_date TEXT, description TEXT, list_url TEXT, row_count INTEGER)"
    )
    conn.executemany(
        f"INSERT INTO datasets ({_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    return conn


def _row(rid, title="제목", org="기관", modified="2026-01-01"):
    return (rid, rid, title, org, "테마", "ANNUAL", "csv", "제한없음", modified, "설명", "http://x", 1)


def _statuses(changes):
    return {c["record_id"]: c["status"] for c in changes}


def test_added_modified_missing():
    prev = _db([_row("a"), _row("b"), _row("c")])
    curr = _db([_row("a"), _row("b", modified="2026-02-01"), _row("d")])
    st = _statuses(compute_changes(curr, prev, "2026-01"))
    assert st["d"] == "ADDED"
    assert st["b"] == "MODIFIED"
    assert st["c"] == "MISSING_FROM_SNAPSHOT"  # 폐기로 단정하지 않음
    assert "a" not in st


def test_modified_carries_changed_fields():
    import json
    prev = _db([_row("b")])
    curr = _db([_row("b", modified="2026-02-01")])
    changes = compute_changes(curr, prev, "2026-01")
    assert json.loads(changes[0]["changed_fields"]) == ["modified_date"]


def test_possible_identity_change():
    prev = _db([_row("a", title="구제목", org="구기관")])
    curr = _db([_row("a", title="신제목", org="신기관")])
    st = _statuses(compute_changes(curr, prev, "2026-01"))
    assert st["a"] == "POSSIBLE_IDENTITY_CHANGE"


def test_reappeared():
    prev = _db([_row("a")])
    curr = _db([_row("a"), _row("z")])
    st = _statuses(compute_changes(curr, prev, "2026-01", prev_missing_ids={"z"}))
    assert st["z"] == "REAPPEARED"


def test_officially_withdrawn_only_with_confirmation():
    prev = _db([_row("a"), _row("w")])
    curr = _db([_row("a")])
    st = _statuses(compute_changes(curr, prev, "2026-01", withdrawn_confirmed={"w"}))
    assert st["w"] == "OFFICIALLY_WITHDRAWN"
    st2 = _statuses(compute_changes(curr, prev, "2026-01"))
    assert st2["w"] == "MISSING_FROM_SNAPSHOT"
