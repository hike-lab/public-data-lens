"""관측 스토어 스키마·연결 — 카탈로그 릴리스 DB와 분리(v2.2 §3).

StructureObservation은 완전 불변: 적재 후 UPDATE하지 않는다.
가변 상태는 asset_coverage에만 존재하고, 레코드 수준 상태는 뷰로 집계한다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .. import config

OBSERVATIONS_DIR = config.DATA_DIR / "observations"
OBSERVATIONS_DB = OBSERVATIONS_DIR / "observations.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS source_assets (
  asset_id        TEXT PRIMARY KEY,
  list_key        TEXT NOT NULL,
  list_type       TEXT NOT NULL,
  file_name       TEXT NOT NULL,   -- 원본 파일데이터명(ZIP 내부 경로 포함 가능)
  container_name  TEXT,            -- ZIP 컨테이너(상위파일데이터명)
  format          TEXT,            -- csv|xlsx|xls|...
  shape           TEXT,            -- CSV|XLSX|ZIP>CSV|ZIP>XLSX
  zip_file_count  INTEGER,
  portal_url      TEXT
);
CREATE INDEX IF NOT EXISTS idx_assets_list ON source_assets(list_key, list_type);

CREATE TABLE IF NOT EXISTS observations (
  observation_id     TEXT PRIMARY KEY,
  asset_id           TEXT NOT NULL REFERENCES source_assets(asset_id),
  source_sha256      TEXT,                       -- NULL이면 provenance로 표기
  provenance         TEXT NOT NULL,              -- VERIFIED | UNVERIFIED_SOURCE
  observed_at        TEXT NOT NULL,              -- 불변(최초 관측 시점)
  tool_version       TEXT NOT NULL,
  rule_versions      TEXT NOT NULL,              -- JSON 배열
  scan_scope         TEXT NOT NULL,              -- FULL | PARTIAL (테이블 집계)
  scan_scope_assumed INTEGER NOT NULL DEFAULT 0, -- 제공자 확인 전 추정 여부
  structure_hash     TEXT NOT NULL,              -- 스키마 변경 이력 비교 키
  license_gate       TEXT NOT NULL               -- FULL | COLUMNS_ONLY
);
CREATE INDEX IF NOT EXISTS idx_obs_asset ON observations(asset_id);

CREATE TABLE IF NOT EXISTS data_tables (
  table_id        TEXT PRIMARY KEY,
  observation_id  TEXT NOT NULL REFERENCES observations(observation_id),
  source_path     TEXT,            -- ZIP 내부 경로(해당 시)
  sheet_name      TEXT,            -- XLSX 시트명(해당 시)
  table_index     INTEGER NOT NULL,
  scan_scope      TEXT NOT NULL,   -- FULL | PARTIAL
  rows_scanned    INTEGER,
  row_count_total INTEGER,
  column_count    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tables_obs ON data_tables(observation_id);

CREATE TABLE IF NOT EXISTS file_columns (
  table_id        TEXT NOT NULL REFERENCES data_tables(table_id),
  ordinal         INTEGER NOT NULL,   -- 1-base, 테이블 내
  source_name     TEXT NOT NULL,      -- 원본 그대로 — 변경 금지
  observed_type   TEXT,               -- NULL = 미관측
  distinct_count  INTEGER,
  distinct_approx INTEGER NOT NULL DEFAULT 0,
  example_status  TEXT NOT NULL,      -- AVAILABLE|NO_NON_NULL_VALUES|WITHHELD_BY_LICENSE|WITHHELD_BY_SAFETY|NOT_COLLECTED|COLLECTION_FAILED
  safety_status   TEXT NOT NULL,      -- CLEAR|WITHHELD|REVIEW_REQUIRED|NOT_ASSESSED
  safety_reason   TEXT,
  examples        TEXT,               -- JSON 배열 — AVAILABLE일 때만
  example_method  TEXT,
  note            TEXT,
  PRIMARY KEY (table_id, ordinal)
);

-- 컬럼 검색용 색인(S2): 레코드×원본 컬럼명 중복 제거 — 원본명 그대로(정규화 없음)
CREATE TABLE IF NOT EXISTS record_column_index (
  list_key    TEXT NOT NULL,
  source_name TEXT NOT NULL,
  PRIMARY KEY (list_key, source_name)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS asset_coverage (
  asset_id               TEXT PRIMARY KEY REFERENCES source_assets(asset_id),
  status                 TEXT NOT NULL,
  failure_reason         TEXT,
  last_attempt_at        TEXT,
  current_observation_id TEXT,
  last_verified_at       TEXT
);

-- 레코드 수준 커버리지: 자산 상태의 집계(파생) — v2.2 §3
CREATE VIEW IF NOT EXISTS record_coverage AS
SELECT
  a.list_key,
  a.list_type,
  COUNT(*) AS total_asset_count,
  SUM(CASE WHEN c.status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_asset_count,
  CASE
    WHEN SUM(CASE WHEN c.status = 'AVAILABLE' THEN 1 ELSE 0 END) = COUNT(*) THEN 'AVAILABLE'
    WHEN SUM(CASE WHEN c.status = 'AVAILABLE' THEN 1 ELSE 0 END) > 0 THEN 'PARTIAL'
    ELSE MAX(c.status)
  END AS coverage_status
FROM source_assets a
JOIN asset_coverage c USING (asset_id)
GROUP BY a.list_key, a.list_type;
"""


def create_store(path: Path | None = None) -> sqlite3.Connection:
    """스토어를 생성(멱등)하고 쓰기 연결을 반환한다."""
    p = path or OBSERVATIONS_DB
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def open_ro(path: Path | None = None) -> sqlite3.Connection:
    """읽기 전용 연결. 스레드 간 공유 금지(호출자가 스레드별로 연다)."""
    p = path or OBSERVATIONS_DB
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
