"""family-candidate-v1.0 — 계열 후보 탐지(ADR-011). 후보는 판정이 아니다."""
import json
import sqlite3
from pathlib import Path

import pytest

from datanav.pipeline.families import detect_families, load_reviews, _family_id
from datanav.store import db as store


def _release_db(records):
    conn = sqlite3.connect(":memory:")
    conn.executescript(store.SCHEMA)
    for r in records:
        conn.execute(
            "INSERT INTO datasets (record_id, list_key, list_type, title, org_name,"
            " regions, source_json) VALUES (?, ?, ?, ?, ?, ?, '{}')",
            (r["record_id"], r.get("list_key", r["record_id"]), r.get("list_type", "FILE"),
             r["title"], r.get("org_name", "기관A"), json.dumps(r.get("regions", []))),
        )
    return conn


def _obs_db(tmp_path, key_hash_cols):
    """(list_key, structure_hash, column_count) 목록으로 최소 관측 스토어 구성."""
    p = tmp_path / "observations.db"
    conn = sqlite3.connect(p)
    conn.executescript(
        "CREATE TABLE source_assets (asset_id TEXT PRIMARY KEY, list_key TEXT);"
        "CREATE TABLE observations (observation_id TEXT PRIMARY KEY, asset_id TEXT, structure_hash TEXT);"
        "CREATE TABLE data_tables (table_id TEXT PRIMARY KEY, observation_id TEXT, column_count INTEGER);"
    )
    for i, (lk, h, cols) in enumerate(key_hash_cols):
        conn.execute("INSERT INTO source_assets VALUES (?, ?)", (f"a{i}", lk))
        conn.execute("INSERT INTO observations VALUES (?, ?, ?)", (f"o{i}", f"a{i}", h))
        conn.execute("INSERT INTO data_tables VALUES (?, ?, ?)", (f"t{i}", f"o{i}", cols))
    conn.commit()
    conn.close()
    return p


def _families(conn):
    return {r["family_id"]: dict(r) for r in conn.execute("SELECT * FROM families")}


def test_title_cluster_and_singleton_excluded():
    conn = _release_db([
        {"record_id": "1", "title": "관광지 현황 2023"},
        {"record_id": "2", "title": "관광지 현황 2024"},
        {"record_id": "3", "title": "전혀 다른 데이터"},
    ])
    summary = detect_families(conn, detected_at="2026-08-05T00:00:00Z")
    fams = _families(conn)
    assert summary["families"] == 1
    fam = next(iter(fams.values()))
    assert fam["member_count"] == 2
    assert fam["evidence_level"] == "CATALOG_ONLY"  # 관측 없음 → 강등
    assert fam["review_status"] == "UNREVIEWED"
    assert fam["relation_type"] == "TIME_LIKE"
    members = {r[0] for r in conn.execute("SELECT record_id FROM family_members")}
    assert members == {"1", "2"}


def test_pattern_cluster_jeju_type():
    conn = _release_db([
        {"record_id": str(i), "title": f"제주_{name}_무장애여행코스", "org_name": "제주"}
        for i, name in enumerate(["가문동", "검은여로", "곤을동", "공천포구"])
    ])
    summary = detect_families(conn, detected_at="t")
    assert summary["families"] == 1
    fam = next(iter(_families(conn).values()))
    assert fam["member_count"] == 4
    assert "PATTERN" in json.loads(fam["signals"])


def test_different_org_never_merges():
    conn = _release_db([
        {"record_id": "1", "title": "충전소 현황 2023", "org_name": "A시"},
        {"record_id": "2", "title": "충전소 현황 2024", "org_name": "B시"},
    ])
    assert detect_families(conn, detected_at="t")["families"] == 0


def test_api_records_excluded():
    conn = _release_db([
        {"record_id": "1", "title": "버스 위치 2023", "list_type": "API"},
        {"record_id": "2", "title": "버스 위치 2024", "list_type": "API"},
    ])
    assert detect_families(conn, detected_at="t")["families"] == 0


def test_structure_signal_and_evidence(tmp_path):
    conn = _release_db([
        {"record_id": "1", "list_key": "k1", "title": "시설 현황 2023"},
        {"record_id": "2", "list_key": "k2", "title": "시설 현황 2024"},
    ])
    obs = _obs_db(tmp_path, [("k1", "H1", 8), ("k2", "H1", 8)])
    fam = next(iter(_families_after(conn, obs).values()))
    assert fam["evidence_level"] == "PLUS_STRUCTURE"
    assert set(json.loads(fam["signals"])) == {"TITLE", "STRUCTURE"}


def test_generic_schema_below_column_floor_ignored(tmp_path):
    # 컬럼 4개 미만 지문은 범용 스키마 과대병합 방지를 위해 구조 신호에서 제외
    conn = _release_db([
        {"record_id": "1", "list_key": "k1", "title": "연혁"},
        {"record_id": "2", "list_key": "k2", "title": "조직도"},
    ])
    obs = _obs_db(tmp_path, [("k1", "H2", 2), ("k2", "H2", 2)])
    assert detect_families(conn, obs_path=obs, detected_at="t")["families"] == 0


def _families_after(conn, obs_path):
    detect_families(conn, obs_path=obs_path, detected_at="t")
    return _families(conn)


def test_family_id_deterministic_and_membership_bound():
    ids = _family_id(["b", "a"]), _family_id(["a", "b"])
    assert ids[0] == ids[1]  # 순서 무관 결정론
    assert _family_id(["a", "b"]) != _family_id(["a", "b", "c"])  # 구성 변경 → id 변경


def test_review_merge(tmp_path):
    conn = _release_db([
        {"record_id": "1", "title": "공원 현황 2023"},
        {"record_id": "2", "title": "공원 현황 2024"},
    ])
    fam_id = _family_id(["1", "2"])
    reviews_path = tmp_path / "family_reviews.json"
    reviews_path.write_text(json.dumps({
        "families": {fam_id: {"reviewStatus": "LEGITIMATE_SPLIT", "note": "연도별 관리 주체 상이"}}
    }), encoding="utf-8")
    summary = detect_families(
        conn, reviews=load_reviews(reviews_path), detected_at="t"
    )
    fam = _families(conn)[fam_id]
    assert fam["review_status"] == "LEGITIMATE_SPLIT"
    assert summary["reviewStatus"] == {"LEGITIMATE_SPLIT": 1}


# ---------------------------------------------------------------- v1.8 노출(P1)

def _service_with_family(catalog_db):
    """conftest 픽스처 DB에 rec-001·rec-002 계열 후보를 등재한 Service."""
    fam_id = _family_id(["rec-001", "rec-002"])
    conn = sqlite3.connect(catalog_db)
    conn.execute(
        "INSERT INTO families VALUES (?, 2, '테스트기관', 'TIME_LIKE', 'CATALOG_ONLY',"
        " '[\"TITLE\"]', 'UNREVIEWED', NULL, 'family-candidate-v1.0', 't')",
        (fam_id,),
    )
    conn.executemany(
        "INSERT INTO family_members VALUES (?, ?, ?)",
        [(fam_id, "rec-001", "list-001"), (fam_id, "rec-002", "list-002")],
    )
    conn.commit()
    conn.close()
    from datanav.api.service import Service
    return Service(catalog_db), fam_id


def test_get_dataset_exposes_family_candidate(catalog_db):
    from jsonschema import Draft202012Validator
    from datanav.spec import OUTPUT_SCHEMAS

    svc, fam_id = _service_with_family(catalog_db)
    body = svc.get_dataset("rec-001", "card")
    fc = body["data"]["familyCandidate"]
    assert fc["familyId"] == fam_id
    assert fc["reviewStatus"] == "UNREVIEWED"          # 후보는 판정이 아니다
    assert {m["recordId"] for m in fc["members"]} == {"rec-001", "rec-002"}
    assert "family-candidate-v1.0" in body["meta"]["ruleVersions"]
    Draft202012Validator(OUTPUT_SCHEMAS["get_dataset"]).validate(body)

    # 계열에 속하지 않은 레코드는 null — 부재가 아니라 '후보 없음'
    body3 = svc.get_dataset("rec-003", "card")
    assert body3["data"]["familyCandidate"] is None
    Draft202012Validator(OUTPUT_SCHEMAS["get_dataset"]).validate(body3)


def test_stats_family_axis(catalog_db):
    from jsonschema import Draft202012Validator
    from datanav.spec import OUTPUT_SCHEMAS

    svc, _ = _service_with_family(catalog_db)
    body = svc.get_catalog_stats("family")
    data = body["data"]
    assert data["available"] is True
    assert data["familyCandidates"]["families"] == 1
    assert data["familyCandidates"]["memberRecords"] == 2
    assert data["familyCandidates"]["byReviewStatus"] == {"UNREVIEWED": 1}
    Draft202012Validator(OUTPUT_SCHEMAS["get_catalog_stats"]).validate(body)


def test_stats_family_axis_pre_adoption_release(catalog_db):
    # 도입 전 릴리스(families 테이블 부재): 0건이 아니라 미산출로 보고
    conn = sqlite3.connect(catalog_db)
    conn.executescript("DROP TABLE families; DROP TABLE family_members;")
    conn.commit()
    conn.close()
    from datanav.api.service import Service
    svc = Service(catalog_db)
    body = svc.get_catalog_stats("family")
    assert body["data"]["available"] is False
    assert svc.get_dataset("rec-001", "card")["data"]["familyCandidate"] is None


def test_union_of_signals_merges_transitively():
    # 1↔2는 제목, 2↔3은 패턴으로만 이어져도 하나의 계열로 합집합
    conn = _release_db([
        {"record_id": "1", "title": "하천_A구간_수질측정", "org_name": "X"},
        {"record_id": "2", "title": "하천_B구간_수질측정", "org_name": "X"},
        {"record_id": "3", "title": "하천_C구간_수질측정", "org_name": "X"},
    ])
    summary = detect_families(conn, detected_at="t")
    assert summary["families"] == 1
    assert next(iter(_families(conn).values()))["member_count"] == 3
