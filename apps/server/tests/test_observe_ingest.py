"""S1a 관측 적재 — 수용 기준(v2.2 §9): 결정론, 안전 선행 저장, 라이선스 게이트,
테이블 분리(시트·ZIP), 상태 산출, 원본 보존."""
from __future__ import annotations

import json
import sqlite3

import pytest

from datanav.observe.ingest import ingest_profile_csv, observe_type
from datanav.observe.safety import screen_column

HEADER = ("dataID,목록명,상위파일데이터명,파일데이터명_확장자(데이터포맷),기관명,데이터유형,"
          "zip_file_count,파일데이터명,확장자(데이터포맷),데이터형태,비고,전체행,전체열,"
          "컬럼명,한글컬럼명,컬럼명_샘플,시트명,컬럼명_비고,고유값수,고유값_근사,열순번")


def _row(list_key="15000001", file="a.csv", shape="CSV", sheet="", rows="100",
         name="시설명", samples="['중앙경로당', '행복경로당']", ordinal="1",
         distinct="50", container=""):
    return (f'{list_key},목록,{container},x,기관,FILE,,{file},csv,{shape},,{rows},2,'
            f'{name},,"{samples}",{sheet},,{distinct},,{ordinal}')


def _write(tmp_path, lines):
    p = tmp_path / "profile.csv"
    p.write_text("﻿" + HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return p


def _ingest(tmp_path, lines, licenses=None, observed_at="2026-07-29T00:00:00Z"):
    csv_path = _write(tmp_path, lines)
    db = tmp_path / "obs.db"
    report = ingest_profile_csv(
        csv_path, db, licenses or {"15000001": "NO_RESTRICTION"},
        observed_at=observed_at,
    )
    return sqlite3.connect(db), report


def test_deterministic_rebuild(tmp_path):
    lines = [_row(), _row(name="위도", samples="['37.5', '36.2']", ordinal="2")]
    conn1, _ = _ingest(tmp_path, lines)
    d1 = list(conn1.execute("SELECT * FROM file_columns ORDER BY ordinal"))
    (tmp_path / "obs.db").unlink()
    conn2, _ = _ingest(tmp_path, lines)
    d2 = list(conn2.execute("SELECT * FROM file_columns ORDER BY ordinal"))
    assert d1 == d2  # 같은 입력 → 같은 내용(결정론)


def test_source_name_preserved_verbatim(tmp_path):
    # 공백·특수문자 포함 원본명이 그대로 — trim·정규화 금지
    conn, _ = _ingest(tmp_path, [_row(name=" 소재지 도로명주소 (지번) ")])
    got = conn.execute("SELECT source_name FROM file_columns").fetchone()[0]
    assert got == " 소재지 도로명주소 (지번) "


def test_safety_withholds_and_discards_values(tmp_path):
    lines = [
        _row(name="담당자 전화번호", samples="['010-1234-5678']", ordinal="1"),
        _row(name="시설명", samples="['중앙경로당']", ordinal="2"),
    ]
    conn, report = _ingest(tmp_path, lines)
    rows = {r[0]: r for r in conn.execute(
        "SELECT source_name, example_status, safety_status, examples FROM file_columns")}
    blocked = rows["담당자 전화번호"]
    assert blocked[1] == "WITHHELD_BY_SAFETY" and blocked[2] == "WITHHELD"
    assert blocked[3] is None  # 값이 어디에도 저장되지 않음
    assert "010-1234-5678" not in open(tmp_path / "obs.db", "rb").read().decode("utf-8", "ignore")
    assert rows["시설명"][1] == "AVAILABLE"  # 시설명은 일률 차단 금지
    assert report.withheld_by_safety == 1


def test_license_gate_columns_only(tmp_path):
    conn, report = _ingest(tmp_path, [_row()], licenses={"15000001": "OTHER"})
    r = conn.execute("SELECT example_status, examples, observed_type FROM file_columns").fetchone()
    assert r[0] == "WITHHELD_BY_LICENSE" and r[1] is None
    assert r[2] == "STRING"  # 컬럼명·유형 관측은 제공(게이트는 예시값만 차단)
    gate = conn.execute("SELECT license_gate FROM observations").fetchone()[0]
    assert gate == "COLUMNS_ONLY"


def test_unknown_listkey_defaults_conservative(tmp_path):
    conn, _ = _ingest(tmp_path, [_row(list_key="99999999")], licenses={})
    assert conn.execute("SELECT license_gate FROM observations").fetchone()[0] == "COLUMNS_ONLY"


def test_sheets_and_zip_members_become_tables(tmp_path):
    lines = [
        _row(file="통계.xlsx", shape="XLSX", sheet="요약", rows="200", ordinal="1"),
        _row(file="통계.xlsx", shape="XLSX", sheet="원자료", rows="5000",
             name="코드", samples="['A1', 'B2']", ordinal="1"),
        _row(file="in/z.csv", shape="ZIP>CSV", container="묶음.zip", ordinal="1"),
    ]
    conn, report = _ingest(tmp_path, lines)
    tables = list(conn.execute(
        "SELECT sheet_name, source_path, rows_scanned FROM data_tables ORDER BY table_index"))
    assert report.assets == 2 and report.tables == 3
    sheets = {t[0] for t in tables}
    assert sheets == {"요약", "원자료", None}
    zip_member = conn.execute(
        "SELECT source_path FROM data_tables WHERE sheet_name IS NULL").fetchone()[0]
    assert zip_member == "in/z.csv"  # ZIP 멤버 경로 보존
    assert conn.execute(
        "SELECT container_name FROM source_assets WHERE file_name='in/z.csv'"
    ).fetchone()[0] == "묶음.zip"


def test_example_status_variants(tmp_path):
    lines = [
        _row(ordinal="1"),                                     # AVAILABLE
        _row(name="빈컬럼", samples="[]", ordinal="2"),          # NO_NON_NULL_VALUES
        _row(name="누락", samples="", ordinal="3"),              # NOT_COLLECTED
        _row(name="깨짐", samples="['미완성", ordinal="4"),       # COLLECTION_FAILED (파싱 실패)
    ]
    conn, report = _ingest(tmp_path, lines)
    got = {r[0]: r[1] for r in conn.execute("SELECT source_name, example_status FROM file_columns")}
    assert got == {"시설명": "AVAILABLE", "빈컬럼": "NO_NON_NULL_VALUES",
                   "누락": "NOT_COLLECTED", "깨짐": "COLLECTION_FAILED"}
    # 파싱 실패 원문도 저장하지 않는다(플래그만)
    raw = open(tmp_path / "obs.db", "rb").read().decode("utf-8", "ignore")
    assert "미완성" not in raw
    assert report.parse_failed == 1


def test_all_tables_fail_marks_collection_failed(tmp_path):
    """전 테이블 검증 실패: 관측 미생성, 상태 COLLECTION_FAILED, 실패 코드 기록."""
    lines = [_row(ordinal="1"), _row(name="b", ordinal="3")]  # 1,3 — 불연속
    conn, report = _ingest(tmp_path, lines)
    cov = conn.execute(
        "SELECT status, failure_reason, current_observation_id FROM asset_coverage").fetchone()
    assert cov[0] == "COLLECTION_FAILED"
    assert cov[1] == "ordinal-not-contiguous"  # 기계 판독 실패 코드
    assert cov[2] is None                      # 관측 참조 없음
    assert conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM data_tables").fetchone()[0] == 0
    assert report.tables == 0


def test_partial_when_some_tables_fail(tmp_path):
    """복수 테이블 중 일부만 실패: PARTIAL + 유효 테이블만 관측에 포함."""
    lines = [
        _row(file="t.xlsx", shape="XLSX", sheet="정상", ordinal="1"),
        _row(file="t.xlsx", shape="XLSX", sheet="불량", ordinal="2"),  # 단독 ordinal 2 — 불연속
    ]
    conn, report = _ingest(tmp_path, lines)
    cov = conn.execute(
        "SELECT status, failure_reason, current_observation_id FROM asset_coverage").fetchone()
    assert cov[0] == "PARTIAL" and cov[1] == "ordinal-not-contiguous"
    assert cov[2] is not None                  # 유효분 관측은 존재
    sheets = [r[0] for r in conn.execute("SELECT sheet_name FROM data_tables")]
    assert sheets == ["정상"]
    assert report.tables == 1


def _first_obs_id(conn):
    return conn.execute("SELECT observation_id FROM observations").fetchone()[0]


def test_observation_id_distinguishes_structure_and_time(tmp_path):
    """해시 부재 관측: 구조 변경·재관측 시점이 다르면 다른 ID, 동일 입력·시점이면 같은 ID."""
    base = [_row()]
    conn, _ = _ingest(tmp_path, base)
    id_base = _first_obs_id(conn)

    (tmp_path / "obs.db").unlink()
    conn, _ = _ingest(tmp_path, [_row(name="다른컬럼명")])   # 구조 변경
    assert _first_obs_id(conn) != id_base

    (tmp_path / "obs.db").unlink()
    conn, _ = _ingest(tmp_path, base, observed_at="2026-08-15T00:00:00Z")  # 재관측 시점
    assert _first_obs_id(conn) != id_base

    (tmp_path / "obs.db").unlink()
    conn, _ = _ingest(tmp_path, base)                        # 동일 입력·동일 시점
    assert _first_obs_id(conn) == id_base


def test_record_coverage_view(tmp_path):
    conn, _ = _ingest(tmp_path, [_row(), _row(file="b.csv", ordinal="1")])
    row = conn.execute("SELECT coverage_status, available_asset_count, total_asset_count "
                       "FROM record_coverage").fetchone()
    assert row == ("AVAILABLE", 2, 2)


def test_observe_type():
    assert observe_type(["1", "2"]) == "INTEGER"
    assert observe_type(["1.5", "2"]) == "NUMBER"
    assert observe_type(["2026-06-30", "2026/07/01"]) == "DATE_LIKE"
    assert observe_type(["Y", "N"]) == "BOOL_LIKE"
    assert observe_type(["서울", "부산"]) == "STRING"
    assert observe_type([]) is None


@pytest.mark.parametrize("name,examples,expected", [
    ("담당자 전화번호", ["02-123-4567"], "WITHHELD"),
    ("시설명", ["중앙경로당"], "CLEAR"),                 # 과차단 금지
    ("소재지도로명주소", ["서울특별시 중구 세종대로 110"], "CLEAR"),
    ("이메일", ["a@b.kr"], "WITHHELD"),
    ("코드", ["a@b.kr"], "WITHHELD"),                   # 값 패턴 단독으로도 차단
    ("대표자명", ["홍길동"], "WITHHELD"),
    ("민원내용", ["도로가 파손되어..."], "REVIEW_REQUIRED"),
    ("행정동코드", ["1111051500"], "CLEAR"),
    ("위도", ["37.5665123456789"], "CLEAR"),            # 고정밀 좌표 — 긴 숫자열 오탐 금지
    ("등록번호", ["900101-1234567"], "WITHHELD"),        # 실제 주민번호형은 차단
    ("측정값", ["9915311234567"], "CLEAR"),              # 13자리지만 월 15 — 생년월일 불가
])
def test_screen_column(name, examples, expected):
    status, _ = screen_column(name, examples)
    assert status == expected
