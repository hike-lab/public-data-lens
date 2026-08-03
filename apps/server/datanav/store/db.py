"""SQLite 스토어 — 릴리스 단위 불변 DB(원자적 배포 대상, §8)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE datasets (
    record_id TEXT PRIMARY KEY,
    list_key TEXT NOT NULL,
    list_type TEXT NOT NULL,
    title TEXT NOT NULL,
    file_data_name TEXT,
    theme_raw TEXT, theme_top TEXT, theme_sub TEXT,
    org_code TEXT, org_name TEXT, dept_name TEXT, dept_phone TEXT,
    retention_basis TEXT, collection_method TEXT,
    update_cycle_raw TEXT, update_cycle TEXT,
    next_registration_date TEXT,
    media_type TEXT, row_count INTEGER,
    format_raw TEXT, formats TEXT,
    keywords TEXT,
    download_count INTEGER,
    created_date TEXT, modified_date TEXT,
    data_limits TEXT, provision_type TEXT, description TEXT, notes TEXT,
    spatial_raw TEXT, temporal_raw TEXT,
    fee TEXT, fee_basis TEXT,
    license_raw TEXT, license_code TEXT,
    api_type TEXT, traffic TEXT, review_type TEXT,
    view_count INTEGER, list_url TEXT,
    is_national_core INTEGER, is_standard INTEGER,
    completeness_score REAL, completeness_profile TEXT, completeness_rule TEXT,
    regions TEXT,
    source_row_no INTEGER,
    source_json TEXT NOT NULL
);
CREATE INDEX idx_datasets_list_key ON datasets(list_key);
CREATE INDEX idx_datasets_theme ON datasets(theme_top);
CREATE INDEX idx_datasets_org ON datasets(org_name);
CREATE INDEX idx_datasets_type ON datasets(list_type);
CREATE INDEX idx_datasets_modified ON datasets(modified_date);

CREATE VIRTUAL TABLE datasets_fts USING fts5(
    title, keywords, description, org_name,
    content='datasets', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE issues (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    field TEXT NOT NULL,
    source_value TEXT,
    issue_type TEXT NOT NULL,
    confidence REAL,
    detection_rule TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'SUGGESTED',
    resolution_status TEXT NOT NULL DEFAULT 'OPEN'
);

CREATE TABLE changes (
    record_id TEXT NOT NULL,
    list_key TEXT NOT NULL,
    status TEXT NOT NULL,
    changed_fields TEXT,
    base_snapshot TEXT,
    title TEXT, org_name TEXT
);
CREATE INDEX idx_changes_status ON changes(status);

CREATE TABLE build_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

DATASET_COLUMNS = [
    "record_id", "list_key", "list_type", "title", "file_data_name",
    "theme_raw", "theme_top", "theme_sub",
    "org_code", "org_name", "dept_name", "dept_phone",
    "retention_basis", "collection_method",
    "update_cycle_raw", "update_cycle", "next_registration_date",
    "media_type", "row_count", "format_raw", "formats", "keywords",
    "download_count", "created_date", "modified_date",
    "data_limits", "provision_type", "description", "notes",
    "spatial_raw", "temporal_raw", "fee", "fee_basis",
    "license_raw", "license_code", "api_type", "traffic", "review_type",
    "view_count", "list_url", "is_national_core", "is_standard",
    "completeness_score", "completeness_profile", "completeness_rule",
    "regions", "source_row_no", "source_json",
]

_JSON_FIELDS = ("formats", "keywords", "regions")


def create_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def insert_dataset(conn: sqlite3.Connection, rec: dict, completeness: dict) -> None:
    row = dict(rec)
    row["completeness_score"] = completeness["score"]
    row["completeness_profile"] = completeness["profile"]
    row["completeness_rule"] = completeness["rule"]
    for f in _JSON_FIELDS:
        row[f] = json.dumps(row[f], ensure_ascii=False)
    conn.execute(
        f"INSERT INTO datasets ({','.join(DATASET_COLUMNS)}) VALUES ({','.join('?' * len(DATASET_COLUMNS))})",
        [row.get(c) for c in DATASET_COLUMNS],
    )


def build_fts(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO datasets_fts(datasets_fts) VALUES('rebuild')")


def open_ro(path: Path) -> sqlite3.Connection:
    # 읽기 전용 릴리스 DB. 연결은 스레드 간 공유 금지 — Service가 스레드별로 연다.
    # (동시 공유 시 커서 상태 오염으로 CPU 폭주 — 실측 버그)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_meta(conn: sqlite3.Connection) -> dict:
    return {k: v for k, v in conn.execute("SELECT key, value FROM build_meta")}


def row_to_record(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in _JSON_FIELDS:
        if f in d and isinstance(d[f], str):
            d[f] = json.loads(d[f])
    return d
