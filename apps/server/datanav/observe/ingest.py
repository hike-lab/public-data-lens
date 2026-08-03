"""프로파일 CSV 적재 어댑터 — Structure Ingest v1의 제1 지원 형식(A.6).

입력: 컬럼 단위 프로파일 CSV(프로파일_컬럼별.csv 형식)
처리: 검증 → 유형 관측 → 안전 스크리닝 → 라이선스 게이트 → 불변 관측 적재
원칙(v2.2): 안전·라이선스 판정을 통과한 예시값만 영구 저장한다.
  후보 값은 메모리에만 존재하며 거부분은 폐기하고 사유(example_status)만 남긴다.
  파싱 실패 표본도 원문을 저장하지 않는다(플래그만) — 검사 전 저장 금지 원칙 우선.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .safety import RULE_SAFETY, screen_column
from .store import create_store

TOOL_VERSION = "datanav-observe/0.1.0"
RULE_TYPE = "column-type-observation-v1.0"
RULE_EXAMPLE = "example-extraction-v1.0"
RULE_STATUS = "structure-status-v1.0"
RULE_BUNDLE = [RULE_TYPE, RULE_EXAMPLE, RULE_SAFETY, RULE_STATUS]

MAX_EXAMPLES = 10

_RE_INT = re.compile(r"^-?\d+$")
_RE_NUM = re.compile(r"^-?\d+([.,]\d+)?$")
_RE_DATE = re.compile(r"^\d{4}([-./]\d{1,2}){2}$|^\d{8}$")
_BOOLS = {"y", "n", "true", "false", "예", "아니오", "유", "무"}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def observe_type(examples: list[str]) -> str | None:
    """예시값 표본 기반 유형 관측(RULE_TYPE) — 표본 한정 관찰."""
    vals = [str(v).strip() for v in examples if str(v).strip()]
    if not vals:
        return "EMPTY" if examples else None
    if all(_RE_INT.match(v) for v in vals):
        return "INTEGER"
    if all(_RE_NUM.match(v) for v in vals):
        return "NUMBER"
    if all(_RE_DATE.match(v) for v in vals):
        return "DATE_LIKE"
    if all(v.lower() in _BOOLS for v in vals):
        return "BOOL_LIKE"
    return "STRING"


@dataclass
class IngestReport:
    rows_read: int = 0
    rows_rejected: int = 0
    reject_reasons: dict = field(default_factory=dict)
    assets: int = 0
    tables: int = 0
    columns: int = 0
    examples_available: int = 0
    withheld_by_safety: int = 0
    withheld_by_license: int = 0
    review_required: int = 0
    not_collected: int = 0
    parse_failed: int = 0
    safety_reasons: dict = field(default_factory=dict)
    non_contiguous_groups: int = 0

    def reject(self, reason: str) -> None:
        self.rows_rejected += 1
        self.reject_reasons[reason] = self.reject_reasons.get(reason, 0) + 1


# 프로파일 CSV의 열 이름(A.6 매핑의 좌변)
_COL = {
    "list_key": "dataID",
    "file_name": "파일데이터명",
    "container": "상위파일데이터명",
    "shape": "데이터형태",
    "ext": "확장자(데이터포맷)",
    "zip_count": "zip_file_count",
    "rows": "전체행",
    "cols": "전체열",
    "name": "컬럼명",
    "samples": "컬럼명_샘플",
    "sheet": "시트명",
    "note": "컬럼명_비고",
    "distinct": "고유값수",
    "distinct_approx": "고유값_근사",
    "ordinal": "열순번",
}


def ingest_profile_csv(
    csv_path: Path,
    db_path: Path,
    license_lookup: dict[str, str],
    *,
    observed_at: str,
    example_method: str = "FIRST_DISTINCT_UP_TO_10",
    scan_scope_assumed: bool = True,
    source_note: str | None = None,
) -> IngestReport:
    """프로파일 CSV를 관측 스토어로 적재한다. 결정론적 — 같은 입력이면 같은 내용.

    license_lookup: list_key → license_code (카탈로그에서 주입). 미등재 키는 보수적으로
    COLUMNS_ONLY 처리한다(예시값 비공개).
    """
    report = IngestReport()
    if db_path.exists():
        db_path.unlink()  # 결정론 보장: 항상 새로 빌드(원자적 배포는 호출 스크립트가 담당)
    conn = create_store(db_path)

    # 배치 provenance: 입력 파일 자체의 해시를 meta에 남긴다
    h = hashlib.sha256()
    with open(csv_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    input_sha = h.hexdigest()

    conn.executemany(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        [
            ("input_file", csv_path.name),
            ("input_sha256", input_sha),
            ("observed_at", observed_at),
            ("tool_version", TOOL_VERSION),
            ("rule_versions", json.dumps(RULE_BUNDLE)),
            ("example_method", example_method),
            ("scan_scope_assumed", "1" if scan_scope_assumed else "0"),
            ("source_note", source_note or ""),
        ],
    )

    seen_assets: set[tuple] = set()
    current_key: tuple | None = None
    current_rows: list[dict] = []

    def flush() -> None:
        if current_key and current_rows:
            _load_asset(conn, current_key, current_rows, license_lookup, report,
                        observed_at=observed_at, example_method=example_method,
                        scan_scope_assumed=scan_scope_assumed)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            report.rows_read += 1
            list_key = (row.get(_COL["list_key"]) or "").strip()
            file_name = (row.get(_COL["file_name"]) or "").strip()
            if not list_key or not file_name:
                report.reject("missing-key-or-filename")
                continue
            key = (list_key, file_name)
            if key != current_key:
                flush()
                if key in seen_assets:
                    # 비연속 그룹: 결정론·순서 보장을 깨므로 거부(입력 정렬 전제 — A.6 실측 정합)
                    report.non_contiguous_groups += 1
                    report.reject("non-contiguous-asset-group")
                    current_key = None
                    current_rows = []
                    continue
                seen_assets.add(key)
                current_key = key
                current_rows = []
            current_rows.append(row)
    flush()
    conn.commit()

    # 요약 통계를 meta에 고정
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('report', ?)",
                 (json.dumps(report.__dict__, ensure_ascii=False),))
    conn.commit()
    conn.close()
    return report


def _load_asset(conn: sqlite3.Connection, key: tuple, rows: list[dict],
                license_lookup: dict[str, str], report: IngestReport, *,
                observed_at: str, example_method: str, scan_scope_assumed: bool) -> None:
    list_key, file_name = key
    first = rows[0]
    container = (first.get(_COL["container"]) or "").strip() or None
    shape = (first.get(_COL["shape"]) or "").strip() or None
    ext = (first.get(_COL["ext"]) or "").strip().upper() or None
    zip_count = _to_int(first.get(_COL["zip_count"]))

    license_code = license_lookup.get(list_key)
    license_gate = "FULL" if license_code == "NO_RESTRICTION" else "COLUMNS_ONLY"

    asset_id = _sha(f"{list_key}|FILE|{container or ''}|{file_name}")[:16]

    # 테이블 분할: 시트명 기준(등장 순서 유지)
    tables: dict[str | None, list[dict]] = {}
    order: list[str | None] = []
    for r in rows:
        sheet = (r.get(_COL["sheet"]) or "").strip() or None
        if sheet not in tables:
            tables[sheet] = []
            order.append(sheet)
        tables[sheet].append(r)

    # 테이블 사전 검증 — 자산 상태는 검증 결과의 집계다(리뷰 지적 1)
    valid_sheets: list[str | None] = []
    failure_code: str | None = None
    for sheet in order:
        ordinals = sorted(_to_int(r[_COL["ordinal"]]) or 0 for r in tables[sheet])
        if ordinals == list(range(1, len(ordinals) + 1)):
            valid_sheets.append(sheet)
        else:
            failure_code = "ordinal-not-contiguous"
            report.reject(f"ordinal-not-contiguous:{list_key}")

    conn.execute(
        "INSERT OR REPLACE INTO source_assets VALUES (?,?,?,?,?,?,?,?,?)",
        (asset_id, list_key, "FILE", file_name, container, ext, shape, zip_count,
         f"https://www.data.go.kr/data/{list_key}/fileData.do"),
    )
    report.assets += 1

    if not valid_sheets:
        # 전부 실패: 관측을 생성하지 않는다 — 해시·컬럼 없는 '관측'은 존재하지 않는다(v2.2 §3)
        conn.execute(
            "INSERT OR REPLACE INTO asset_coverage VALUES (?,?,?,?,?,?)",
            (asset_id, "COLLECTION_FAILED", failure_code, observed_at, None, None),
        )
        return

    # 구조 해시(스키마 변경 이력 비교 키) — 유효 테이블의 원본명·순서만 사용
    structure = [
        [sheet or "", [(_to_int(r[_COL["ordinal"]]) or 0, r[_COL["name"]] or "")
                       for r in tables[sheet]]]
        for sheet in valid_sheets
    ]
    structure_hash = _sha(json.dumps(structure, ensure_ascii=False, sort_keys=False))
    # 해시 부재 시 구조·관측 시점을 앵커로 사용(리뷰 지적 2) — 자산 구조가 바뀌거나
    # 재관측하면 새 observation_id가 된다. 예시값(원문·해시)은 ID에 포함하지 않는다.
    source_anchor = f"nohash:{structure_hash}:{observed_at}"
    observation_id = _sha(f"{asset_id}|{source_anchor}|{TOOL_VERSION}|{','.join(RULE_BUNDLE)}")[:16]

    status = "AVAILABLE" if len(valid_sheets) == len(order) else "PARTIAL"
    conn.execute(
        "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (observation_id, asset_id, None, "UNVERIFIED_SOURCE", observed_at,
         TOOL_VERSION, json.dumps(RULE_BUNDLE), "FULL",
         1 if scan_scope_assumed else 0, structure_hash, license_gate),
    )
    conn.execute(
        "INSERT OR REPLACE INTO asset_coverage VALUES (?,?,?,?,?,?)",
        (asset_id, status, failure_code, observed_at, observation_id, None),
    )

    for t_index, sheet in enumerate(valid_sheets):
        trows = tables[sheet]
        rows_scanned = _to_int(trows[0].get(_COL["rows"]))
        table_id = _sha(f"{observation_id}|{file_name}|{sheet or ''}|{t_index}")[:16]
        # ZIP 멤버 경로: 파일데이터명이 컨테이너 내부 경로를 담는 실측 관행(A.6)
        source_path = file_name if (shape or "").startswith("ZIP") else None

        conn.execute(
            "INSERT OR REPLACE INTO data_tables VALUES (?,?,?,?,?,?,?,?,?)",
            (table_id, observation_id, source_path, sheet, t_index,
             "FULL", rows_scanned, rows_scanned, len(trows)),
        )
        report.tables += 1

        col_rows = []
        for r in sorted(trows, key=lambda x: _to_int(x[_COL["ordinal"]]) or 0):
            col_rows.append(_column_row(r, table_id, license_gate, example_method, report))
        conn.executemany(
            "INSERT OR REPLACE INTO file_columns VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            col_rows,
        )
        conn.executemany(  # 컬럼 검색 색인(S2) — 원본명 그대로
            "INSERT OR IGNORE INTO record_column_index VALUES (?,?)",
            [(list_key, c[2]) for c in col_rows],
        )
        report.columns += len(col_rows)


def _column_row(r: dict, table_id: str, license_gate: str,
                example_method: str, report: IngestReport) -> tuple:
    ordinal = _to_int(r[_COL["ordinal"]]) or 0
    source_name = r[_COL["name"]] or ""
    note = (r.get(_COL["note"]) or "").strip() or None
    distinct = _to_int(r.get(_COL["distinct"]))
    distinct_approx = 1 if (r.get(_COL["distinct_approx"]) or "").strip() == "Y" else 0

    raw = r.get(_COL["samples"])
    examples: list[str] | None = None
    observed = None
    safety_status, safety_reason = "NOT_ASSESSED", None
    if raw is None or not str(raw).strip():
        example_status = "NOT_COLLECTED"
        report.not_collected += 1
    else:
        try:
            parsed = ast.literal_eval(raw)
            if not isinstance(parsed, list):
                raise ValueError("not a list")
            candidates = [str(v) for v in parsed][:MAX_EXAMPLES]
        except (ValueError, SyntaxError):
            # 원문 미보존(안전검사 전 저장 금지 원칙) — 플래그만 남긴다
            report.parse_failed += 1
            return (table_id, ordinal, source_name, None, distinct, distinct_approx,
                    "COLLECTION_FAILED", "NOT_ASSESSED", "sample-parse-failed",
                    None, example_method, note)

        observed = observe_type(candidates)
        if not candidates:
            example_status = "NO_NON_NULL_VALUES"
        else:
            safety_status, safety_reason = screen_column(source_name, candidates)
            if safety_status != "CLEAR":
                example_status = "WITHHELD_BY_SAFETY"
                if safety_status == "REVIEW_REQUIRED":
                    report.review_required += 1
                else:
                    report.withheld_by_safety += 1
                if safety_reason:
                    report.safety_reasons[safety_reason] = \
                        report.safety_reasons.get(safety_reason, 0) + 1
            elif license_gate != "FULL":
                example_status = "WITHHELD_BY_LICENSE"
                report.withheld_by_license += 1
            else:
                example_status = "AVAILABLE"
                examples = candidates
                report.examples_available += 1

    return (table_id, ordinal, source_name, observed, distinct, distinct_approx,
            example_status, safety_status, safety_reason,
            json.dumps(examples, ensure_ascii=False) if examples else None,
            example_method, note)


def _to_int(v) -> int | None:
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None
