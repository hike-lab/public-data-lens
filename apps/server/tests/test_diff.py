import sqlite3

from datanav.pipeline.diff import compute_changes

_COLS = (
    "record_id, list_key, title, org_name, theme_raw, update_cycle, formats, "
    "license_raw, modified_date, description, list_url, row_count"
)


def _db(rows):
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE datasets (record_id TEXT, list_key TEXT, title TEXT, org_name TEXT,"
        " theme_raw TEXT, update_cycle TEXT, formats TEXT, license_raw TEXT,"
        " modified_date TEXT, description TEXT, list_url TEXT, row_count INTEGER)"
    )
    conn.executemany(
        f"INSERT INTO datasets ({_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    return conn


def _row(rid, title="제목", org="기관", modified="2026-01-01", formats='["CSV"]', desc="설명"):
    return (rid, rid, title, org, "테마", "ANNUAL", formats, "제한없음", modified, desc, "http://x", 1)


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


# ---------------------------------------------------------------- diff-v1.1

def test_description_whitespace_only_is_not_modified():
    """발행자 내보내기 규칙 변경(줄바꿈 보존)을 실질 변경으로 오인하지 않는다."""
    prev = _db([_row("a", desc="첫 문장입니다.* 둘째 문장")])
    curr = _db([_row("a", desc="첫 문장입니다.\n* 둘째 문장")])
    assert compute_changes(curr, prev, "2026-01") == []


def test_description_content_change_is_still_modified():
    """공백 둔감이 실질 변경을 삼키지 않는다."""
    prev = _db([_row("a", desc="첫 문장입니다.")])
    curr = _db([_row("a", desc="첫 문장입니다. 셋째 문장 추가.")])
    st = _statuses(compute_changes(curr, prev, "2026-01"))
    assert st["a"] == "MODIFIED"


def test_title_whitespace_only_is_not_modified():
    prev = _db([_row("a", title="서울시  주차장 현황")])
    curr = _db([_row("a", title="서울시 주차장 현황")])
    assert compute_changes(curr, prev, "2026-01") == []


def test_format_case_churn_is_not_modified():
    """normalize_formats가 대문자 토큰으로 환산하므로 csv↔CSV는 diff에 닿지 않는다."""
    from datanav.pipeline.normalize import normalize_formats
    assert normalize_formats("csv") == normalize_formats("CSV") == ["CSV"]
    prev = _db([_row("a", formats='["CSV"]')])
    curr = _db([_row("a", formats='["CSV"]')])
    assert compute_changes(curr, prev, "2026-01") == []


def test_real_format_change_is_modified():
    import json
    prev = _db([_row("a", formats='["CSV"]')])
    curr = _db([_row("a", formats='["CSV", "XML"]')])
    changes = compute_changes(curr, prev, "2026-01")
    assert json.loads(changes[0]["changed_fields"]) == ["formats"]
