"""계열 검증시트(CSV) → family_reviews.json 변환(ADR-011 G0 루프).

사용: python scripts/family_reviews_from_sheet.py <검증시트.csv> [출력.json]
  - verdict 컬럼이 비어 있는 행은 건너뛴다(미판정 = UNREVIEWED 유지).
  - 허용 판정: CONFIRMED_FAMILY | LEGITIMATE_SPLIT | NOT_A_FAMILY.
  - 기존 출력 파일이 있으면 병합한다(같은 family_id는 시트 값이 이긴다).
  - 판정 요약(정밀도 산출용 집계)을 stdout으로 출력한다.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

VALID = {"CONFIRMED_FAMILY", "LEGITIMATE_SPLIT", "NOT_A_FAMILY"}


def convert(sheet: Path, out: Path) -> dict:
    existing = {}
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8")).get("families", {})

    counts: Counter = Counter()
    by_evidence: dict[str, Counter] = {}
    with open(sheet, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        verdict_col = next((c for c in reader.fieldnames if c.startswith("verdict")), None)
        if not verdict_col:
            raise SystemExit("verdict 컬럼을 찾을 수 없습니다.")
        for row in reader:
            verdict = (row[verdict_col] or "").strip().upper()
            if not verdict:
                counts["(미판정)"] += 1
                continue
            if verdict not in VALID:
                raise SystemExit(
                    f"허용되지 않은 판정 '{verdict}' (family_id={row['family_id']}). 허용: {sorted(VALID)}"
                )
            entry = {"reviewStatus": verdict}
            note = (row.get("note") or "").strip()
            rel = (row.get("relation_type_human") or "").strip()
            if note:
                entry["note"] = note
            if rel:
                entry["relationTypeHuman"] = rel
            existing[row["family_id"]] = entry
            counts[verdict] += 1
            ev = row.get("evidence", "?")
            by_evidence.setdefault(ev, Counter())[verdict] += 1

    out.write_text(
        json.dumps({"families": existing}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # 정밀도(참 계열 비율) — NOT_A_FAMILY만 오탐으로 계산. LEGITIMATE_SPLIT은
    # '계열이되 정당한 분리'이므로 탐지 정밀도에서는 참으로 센다(ADR-011).
    judged = sum(v for k, v in counts.items() if k != "(미판정)")
    summary = {"counts": dict(counts), "judged": judged}
    if judged:
        tp = counts["CONFIRMED_FAMILY"] + counts["LEGITIMATE_SPLIT"]
        summary["precision"] = round(tp / judged, 3)
        summary["byEvidence"] = {
            ev: {"judged": sum(c.values()),
                 "precision": round((c["CONFIRMED_FAMILY"] + c["LEGITIMATE_SPLIT"]) / sum(c.values()), 3)}
            for ev, c in by_evidence.items()
        }
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sheet = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/catalog/family_reviews.json")
    print(json.dumps(convert(sheet, out), ensure_ascii=False, indent=1))
