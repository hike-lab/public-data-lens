"""스냅샷 수용 게이트 — 2026-07 회차에서 실제로 뚫린 검사들의 회귀 방지(ADR-016·018)."""
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "verify_snapshot", Path(__file__).resolve().parents[1] / "scripts" / "verify_snapshot.py"
)
vs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(vs)


def _row(**kw):
    base = {c: "" for c in vs.TEXT_COLUMNS}
    base.update({"목록키": "1", "목록유형": "FILE"})
    base.update(kw)
    return base


def _levels(rep, check_prefix):
    return [r["level"] for r in rep.rows if r["check"].startswith(check_prefix)]


# ------------------------------------------------------- 수식 오류 잔재

def test_formula_error_is_reported():
    """2026-07 수정판 실측 형태 — 셀이 비지 않아 채움률·값 회귀로는 잡히지 않는다."""
    rep = vs.Report()
    vs.check_formula_errors([_row(설명="ME?"), _row(**{"기타 유의사항": "#NAME?"})], rep)
    assert _levels(rep, "수식 오류") == ["WARN"]
    detail = next(r["detail"] for r in rep.rows if r["check"].startswith("수식 오류"))
    assert "2건" in detail and "복원" in detail


def test_clean_rows_pass_formula_check():
    rep = vs.Report()
    vs.check_formula_errors([_row(설명="정상 설명문"), _row(설명="")], rep)
    assert _levels(rep, "수식 오류") == ["PASS"]


def test_formula_lookalike_in_prose_is_not_flagged():
    """전체 셀 정확 일치만 본다 — 본문에 등장하는 오류 코드는 정상 내용이다."""
    rep = vs.Report()
    vs.check_formula_errors([_row(설명="#NAME? 오류의 원인과 해결 방법을 정리한 자료")], rep)
    assert _levels(rep, "수식 오류") == ["PASS"]


# ------------------------------------------------------- 원문 급감

def _pair(new_desc, old_desc):
    return {"a": _row(설명=new_desc)}, {"a": _row(설명=old_desc)}


def test_text_collapse_is_reported():
    cur, prv = _pair("짧게", "가" * 200)
    rep = vs.Report()
    vs.check_text_collapse(cur, prv, rep)
    assert _levels(rep, "원문 급감") == ["WARN"]


def test_emptied_cell_is_left_to_value_regression():
    """빈값은 값 회귀 검사 담당 — 두 검사가 같은 셀을 이중 보고하지 않는다."""
    cur, prv = _pair("", "가" * 200)
    rep = vs.Report()
    vs.check_text_collapse(cur, prv, rep)
    assert _levels(rep, "원문 급감") == ["PASS"]


def test_formula_error_is_left_to_its_own_check():
    cur, prv = _pair("ME?", "가" * 200)
    rep = vs.Report()
    vs.check_text_collapse(cur, prv, rep)
    assert _levels(rep, "원문 급감") == ["PASS"]


def test_small_edit_is_not_a_collapse():
    cur, prv = _pair("가" * 190, "가" * 200)
    rep = vs.Report()
    vs.check_text_collapse(cur, prv, rep)
    assert _levels(rep, "원문 급감") == ["PASS"]


# ------------------------------------------------------- 채움률 함정

def test_dash_is_not_counted_as_filled():
    """2026-07 초판 함정 — 파일데이터명 ''↔'-' 요동이 채움률 '개선'으로 보였다."""
    assert not vs.filled({"x": "-"}, "x")
    assert not vs.filled({"x": ""}, "x")
    assert not vs.filled({"x": "없음"}, "x")
    assert vs.filled({"x": "실제값"}, "x")


def test_formula_error_is_not_counted_as_filled():
    assert not vs.filled({"x": "ME?"}, "x")
    assert not vs.filled({"x": "#NAME?"}, "x")


# ------------------------------------------------------- 날짜·중복키

def test_serial_dates_block():
    rep = vs.Report()
    vs.check_dates([_row(등록일="41249", 수정일="44834", **{"차기 등록 예정일": ""})], rep)
    blocks = [r for r in rep.rows if r["level"] == "BLOCK"]
    assert len(blocks) == 2
    assert "엑셀 일련번호" in blocks[0]["detail"]


def test_iso_dates_pass():
    rep = vs.Report()
    vs.check_dates([_row(등록일="2012-12-06", 수정일="2022-09-30",
                         **{"차기 등록 예정일": "2027-01-01"})], rep)
    assert all(r["level"] == "PASS" for r in rep.rows)


def test_counter_decrease_blocks():
    cur = {"a": _row(조회수="100", 다운로드_활용신청건수="5")}
    prv = {"a": _row(조회수="120", 다운로드_활용신청건수="5")}
    rep = vs.Report()
    vs.check_counters(cur, prv, rep)
    assert "BLOCK" in _levels(rep, "카운터 단조성 · 조회수")
    assert _levels(rep, "카운터 단조성 · 다운로드") == ["PASS"]
