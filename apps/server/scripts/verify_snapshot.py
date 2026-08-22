#!/usr/bin/env python3
"""스냅샷 수용 검증 — 빌드 전에 회차 CSV가 받아들일 만한 것인지 판정한다.

사용법:
    python scripts/verify_snapshot.py <새_CSV> [이전_CSV]

이전 CSV를 주면 회차 간 대조 검사(카운터 단조성·채움률 델타·어휘 델타·값 회귀·diff 예측)까지
수행한다. 차단(BLOCK) 항목이 하나라도 걸리면 종료코드 1 — 빌드를 진행하지 않는다.

배경: 2026-07 회차에서 발행자 내보내기 경로 변경으로 API 유형 11,960행의 날짜가 엑셀
일련번호로, 설명 필드의 줄바꿈 처리가 반대로 내려왔다. 채움률만 보는 점검은 이를 놓친다
(파일데이터명은 '' → '-'로 바뀌어 채움률이 오히려 12.2pp '개선'된 것으로 보였다).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.pipeline.completeness import compute_completeness  # noqa: E402
from datanav.pipeline.diff import _TRACKED, _compare_value  # noqa: E402
from datanav.pipeline.normalize import detect_issues, is_empty, normalize_row  # noqa: E402
from datanav.pipeline.parse import (  # noqa: E402
    COLUMN_MAP,
    ParseError,
    detect_encoding,
    parse_snapshot_csv,
)

csv.field_size_limit(50_000_000)

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_COLUMNS = ("등록일", "수정일", "차기 등록 예정일")
COUNTER_COLUMNS = ("조회수", "다운로드_활용신청건수")
# 어휘가 통제되어야 하는 컬럼 — 값이 새로 생기거나 사라지면 재코딩 신호다
ENUM_COLUMNS = (
    "목록유형", "업데이트 주기", "매체유형", "제공형태", "비용부과유무",
    "이용허락범위", "API 유형", "심의 유형", "국가중점여부", "표준데이터여부",
)
FILL_DROP_BLOCK_PP = 5.0   # 채움률 변동 차단 임계(퍼센트포인트)
FILL_DROP_WARN_PP = 1.0

_ANSI = {"BLOCK": "\033[31m", "WARN": "\033[33m", "PASS": "\033[32m", None: "\033[0m"}


class Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, level: str, check: str, detail) -> None:
        self.rows.append({"level": level, "check": check, "detail": str(detail)})

    @property
    def blocked(self) -> bool:
        return any(r["level"] == "BLOCK" for r in self.rows)

    def render(self) -> None:
        w = max(len(r["check"]) for r in self.rows)
        for r in self.rows:
            c, z = _ANSI[r["level"]], _ANSI[None]
            print(f"  {c}[{r['level']:<5}]{z} {r['check']:<{w}}  {r['detail']}")


def load_rows(path: Path) -> tuple[list[dict], str]:
    enc = detect_encoding(path)
    return [item["source"] for item in parse_snapshot_csv(path, enc)], enc


def g(row: dict, col: str) -> str:
    return (row.get(col) or "").strip()


def filled(row: dict, col: str) -> bool:
    """is_empty()와 같은 기준 — '-'·'없음'을 채움으로 세지 않는다(파일데이터명 함정)."""
    return not is_empty(row.get(col))


def to_int(v: str) -> int | None:
    try:
        return int(float(v.replace(",", "").strip()))
    except (ValueError, AttributeError):
        return None


# --------------------------------------------------------------- 단일 파일 검사

def check_structure(rows: list[dict], enc: str, rep: Report) -> dict[str, dict]:
    rep.add("PASS", "인코딩", enc)
    header = [c for c in (rows[0].keys() if rows else []) if c is not None]
    missing = set(COLUMN_MAP) - set(header)
    extra = [c for c in header if c not in COLUMN_MAP]
    if missing:
        rep.add("BLOCK", "헤더 구조", f"누락 컬럼 {sorted(missing)}")
    else:
        rep.add("PASS", "헤더 구조",
                f"{len(COLUMN_MAP)}컬럼 일치" + (f" (계약 외 추가 {extra})" if extra else ""))

    by_key: dict[str, dict] = {}
    dups = Counter()
    for r in rows:
        k = g(r, "목록키")
        if k in by_key:
            dups[k] += 1
        by_key[k] = r
    if dups:
        rep.add("BLOCK", "목록키 중복",
                f"{len(dups)}종 — record_id가 '{{키}}-{{유형}}' 형태로 바뀌어 diff가 같은 "
                f"데이터를 MISSING+ADDED로 쪼갠다: {list(dups)[:5]}")
    else:
        rep.add("PASS", "목록키 중복", f"0종 (고유키 {len(by_key):,})")
    rep.add("PASS", "행수", f"{len(rows):,}행")
    return by_key


def check_dates(rows: list[dict], rep: Report) -> None:
    """2026-07 수정 요청의 핵심 — 날짜 컬럼이 100% ISO여야 한다."""
    for col in DATE_COLUMNS:
        present = [v for v in (g(r, col) for r in rows) if v and v != "-"]
        bad = [v for v in present if not ISO_DATE.match(v)]
        if not bad:
            rep.add("PASS", f"날짜 형식 · {col}", f"{len(present):,}건 전부 ISO")
            continue
        badset = set(bad)
        serial = [v for v in bad if re.fullmatch(r"\d{5}", v)]
        by_type = Counter(g(r, "목록유형") for r in rows if g(r, col) in badset)
        kind = "엑셀 일련번호" if len(serial) > len(bad) // 2 else "형식 불명"
        rep.add("BLOCK", f"날짜 형식 · {col}",
                f"{len(bad):,}건 위반 ({kind}) — 유형별 {dict(by_type)}, 예: {bad[:3]}")


def check_contract(rows: list[dict], rep: Report) -> dict:
    """파이프라인을 실제로 통과시켜 계약 노출 지표를 뽑는다."""
    scores: dict[str, list[float]] = defaultdict(list)
    evidence, licenses, issues = Counter(), Counter(), Counter()
    for n, src in enumerate(rows, start=2):
        rec = normalize_row(src, n)
        scores[rec["list_type"]].append(compute_completeness(rec)["score"])
        licenses[rec["license_code"]] += 1
        for reg in rec["regions"]:
            evidence[reg["evidence"]] += 1
        for i in detect_issues(rec, src):
            issues[i["issue_type"]] += 1
    allv = [s for v in scores.values() for s in v]
    overall = sum(allv) / len(allv)
    per = "  ".join(f"{k} {sum(v) / len(v):.4f}" for k, v in sorted(scores.items()))
    rep.add("PASS", "완전성 평균", f"전체 {overall:.4f}   {per}")
    rep.add("PASS", "지역 근거 분포", dict(evidence.most_common()))
    rep.add("PASS", "license_code", dict(licenses.most_common()))
    if issues:
        # 날짜 아티팩트는 정규화가 복원하므로 관찰(WARN), 그 외는 확인 필요
        rep.add("WARN", "이슈 관찰", dict(issues.most_common()))
    else:
        rep.add("PASS", "이슈 관찰", "0건")
    return {"completeness": round(overall, 4),
            "completenessByType": {k: round(sum(v) / len(v), 4) for k, v in scores.items()},
            "regionEvidence": dict(evidence), "issues": dict(issues)}


# --------------------------------------------------------------- 회차 간 검사

def check_counters(cur: dict, prv: dict, rep: Report) -> None:
    """조회수·다운로드는 누적값이다. 감소는 회차 역행이나 다른 지표 혼입을 뜻한다."""
    shared = cur.keys() & prv.keys()
    for col in COUNTER_COLUMNS:
        dec = tot = 0
        for k in shared:
            a, b = to_int(g(cur[k], col)), to_int(g(prv[k], col))
            if a is None or b is None:
                continue
            if a < b:
                dec += 1
                tot += b - a
        if dec == 0:
            rep.add("PASS", f"카운터 단조성 · {col}", "감소 0건")
        else:
            rep.add("BLOCK", f"카운터 단조성 · {col}",
                    f"{dec:,}건 감소 ({dec / max(len(shared), 1) * 100:.1f}%), 총 {tot:,} — "
                    f"이전 회차보다 오래된 자료이거나 다른 지표가 들어왔다")


def check_fill_rates(cur: dict, prv: dict, rep: Report) -> None:
    moved = []
    for col in COLUMN_MAP:
        a = sum(1 for r in cur.values() if filled(r, col)) / len(cur) * 100
        b = sum(1 for r in prv.values() if filled(r, col)) / len(prv) * 100
        d = a - b
        if abs(d) >= FILL_DROP_WARN_PP:
            lvl = "BLOCK" if d <= -FILL_DROP_BLOCK_PP else "WARN"
            moved.append((lvl, col, b, a, d))
    for lvl, col, b, a, d in sorted(moved, key=lambda x: x[4]):
        note = " — 컬럼 소실 의심" if lvl == "BLOCK" else ""
        rep.add(lvl, f"채움률 · {col}", f"{b:.1f}% → {a:.1f}% ({d:+.1f}pp){note}")
    if not moved:
        rep.add("PASS", "채움률 델타", f"전 {len(COLUMN_MAP)}컬럼 ±{FILL_DROP_WARN_PP}pp 이내")


def check_vocabularies(cur: dict, prv: dict, rep: Report) -> None:
    for col in ENUM_COLUMNS:
        a = {g(r, col) for r in cur.values() if g(r, col)}
        b = {g(r, col) for r in prv.values() if g(r, col)}
        added, gone = sorted(a - b), sorted(b - a)
        if not added and not gone:
            rep.add("PASS", f"어휘 · {col}", f"{len(a)}종 불변")
            continue
        # 어휘가 절반 이상 사라지면 재코딩이다(2026-08 API 합성본의 이용허락범위 사례)
        lvl = "BLOCK" if b and len(gone) > len(b) / 2 else "WARN"
        rep.add(lvl, f"어휘 · {col}",
                f"{len(b)}종 → {len(a)}종  신규 {added[:3]}  소멸 {gone[:3]}")


def check_value_regression(cur: dict, prv: dict, rep: Report) -> None:
    """이전 회차에는 값이 있었는데 이번에 비어버린 셀 — 수정하다 다른 걸 깬 경우를 잡는다."""
    shared = cur.keys() & prv.keys()
    lost = Counter()
    for k in shared:
        for col in COLUMN_MAP:
            if filled(prv[k], col) and not filled(cur[k], col):
                lost[col] += 1
    heavy = {c: n for c, n in lost.items() if n > len(shared) * 0.01}
    if heavy:
        rep.add("BLOCK", "값 회귀",
                f"유지키 {len(shared):,}건 중 값이 사라진 컬럼: "
                + ", ".join(f"{c} {n:,}" for c, n in sorted(heavy.items(), key=lambda x: -x[1])))
    elif lost:
        rep.add("WARN", "값 회귀", f"소규모: {dict(lost.most_common(5))}")
    else:
        rep.add("PASS", "값 회귀", "없음")


def predict_diff(cur: dict, prv: dict, rep: Report) -> dict:
    """diff-v1.1 비교 규칙으로 상태 분포를 미리 계산한다 — 빌드 결과와 대조할 기대치."""
    def norm(rows: dict) -> dict:
        out = {}
        for n, (k, src) in enumerate(rows.items(), start=2):
            rec = normalize_row(src, n)
            rec["formats"] = json.dumps(rec["formats"], ensure_ascii=False)
            out[k] = tuple(_compare_value(f, rec[f]) for f in _TRACKED)
        return out

    a, b = norm(cur), norm(prv)
    st, fields = Counter(), Counter()
    for k, row in a.items():
        if k not in b:
            st["ADDED"] += 1
            continue
        ch = [_TRACKED[i] for i in range(len(_TRACKED)) if row[i] != b[k][i]]
        if not ch:
            continue
        st["POSSIBLE_IDENTITY_CHANGE" if {"title", "org_name"} <= set(ch) else "MODIFIED"] += 1
        for f in ch:
            fields[f] += 1
    st["MISSING_FROM_SNAPSHOT"] = sum(1 for k in b if k not in a)
    rep.add("PASS", "diff 예측 (diff-v1.1)", dict(st.most_common()))
    rep.add("PASS", "diff 변경 필드", dict(fields.most_common()))
    return {"statuses": dict(st), "fields": dict(fields)}


# --------------------------------------------------------------------- 실행

def main() -> int:
    if not 2 <= len(sys.argv) <= 3:
        print(__doc__)
        return 2
    new_path = Path(sys.argv[1])
    old_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    for p in (new_path, old_path):
        if p and not p.exists():
            print(f"CSV 없음: {p}")
            return 2

    rep = Report()
    print(f"\n■ 대상: {new_path.name}")
    try:
        rows, enc = load_rows(new_path)
    except ParseError as e:
        print(f"  \033[31m[BLOCK]\033[0m 파싱 실패 — {e}")
        return 1
    cur = check_structure(rows, enc, rep)
    check_dates(rows, rep)
    summary = {"file": new_path.name, "rows": len(rows), "encoding": enc}
    summary.update(check_contract(rows, rep))

    if old_path:
        print(f"■ 대조: {old_path.name}")
        prv_rows, _ = load_rows(old_path)
        prv = {g(r, "목록키"): r for r in prv_rows}
        rep.add("PASS", "키 증감",
                f"신규 {len(cur.keys() - prv.keys()):,}  소멸 {len(prv.keys() - cur.keys()):,}  "
                f"유지 {len(cur.keys() & prv.keys()):,}")
        check_counters(cur, prv, rep)
        check_fill_rates(cur, prv, rep)
        check_vocabularies(cur, prv, rep)
        check_value_regression(cur, prv, rep)
        summary["diff"] = predict_diff(cur, prv, rep)

    print()
    rep.render()
    n_block = sum(1 for r in rep.rows if r["level"] == "BLOCK")
    n_warn = sum(1 for r in rep.rows if r["level"] == "WARN")
    print()
    if rep.blocked:
        print(f"\033[31m판정: 수용 불가\033[0m — 차단 {n_block}건, 경고 {n_warn}건. 빌드하지 않는다.")
    else:
        print(f"\033[32m판정: 수용 가능\033[0m — 차단 0건, 경고 {n_warn}건.")
    out = new_path.parent / f"verify_{new_path.stem}.json"
    out.write_text(json.dumps({"summary": summary, "checks": rep.rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"상세: {out}")
    return 1 if rep.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
