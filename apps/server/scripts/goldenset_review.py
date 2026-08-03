#!/usr/bin/env python3
"""골든셋 인간 검수 도구.

1) export: 질의별 상위 후보 + 자동 관련성 제안을 검수 파일로 출력
   python scripts/goldenset_review.py export           → golden/review-{snapshot}.json

   검수 방법: 각 후보의 "verdict"를 채운다.
     "R"  = 관련(relevant) / "N" = 무관 / null(미기재) = 자동 제안(auto) 채택
   목록에 없는 관련 데이터셋은 "additionalRelevantIds"에 recordId를 추가한다.

2) promote: 검수 파일 → 확정 골든셋 v1(목록키 고정, 스냅샷 귀속)
   python scripts/goldenset_review.py promote          → golden/goldenset_v1.json
   이후 평가: python scripts/eval_goldenset.py golden/goldenset_v1.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.api.service import Service  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden"
V0_PATH = GOLDEN_DIR / "goldenset_v0.json"
TOP_K = 20


def export() -> int:
    svc = Service()
    v0 = json.loads(V0_PATH.read_text(encoding="utf-8"))
    out_queries = []
    for q in v0["queries"]:
        pat = re.compile(q["titleRegex"], re.IGNORECASE)
        res = svc.search_datasets(query=q["searchQuery"], region=q["region"], page_size=TOP_K)
        candidates = [
            {
                "recordId": it["recordId"],
                "title": it["title"],
                "orgName": it["orgName"],
                "listType": it["listType"],
                "autoRelevant": bool(pat.search(it["title"])),
                "verdict": None,
            }
            for it in res["data"]["items"]
        ]
        out_queries.append({
            "id": q["id"], "purpose": q["purpose"], "searchQuery": q["searchQuery"],
            "region": q["region"], "titleRegex": q["titleRegex"],
            "candidates": candidates,
            "additionalRelevantIds": [],
            "reviewerNote": None,
        })
    out = {
        "snapshot": svc.snapshot,
        "instructions": "각 후보 verdict: 'R'(관련)/'N'(무관)/null(자동 제안 채택). 누락 관련 데이터셋은 additionalRelevantIds에 recordId 추가.",
        "queries": out_queries,
    }
    path = GOLDEN_DIR / f"review-{svc.snapshot}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(q["candidates"]) for q in out_queries)
    print(f"검수 파일 생성: {path}")
    print(f"질의 {len(out_queries)}개 · 후보 {n}건 — verdict를 채운 뒤 promote를 실행하세요.")
    return 0


def promote() -> int:
    svc = Service()
    review_path = GOLDEN_DIR / f"review-{svc.snapshot}.json"
    if not review_path.exists():
        print(f"검수 파일 없음: {review_path} — 먼저 export를 실행하세요.")
        return 2
    review = json.loads(review_path.read_text(encoding="utf-8"))

    reviewed = 0
    queries = []
    for q in review["queries"]:
        relevant, excluded = [], []
        for c in q["candidates"]:
            verdict = c["verdict"]
            if verdict is not None:
                reviewed += 1
            is_rel = (verdict == "R") if verdict else c["autoRelevant"]
            (relevant if is_rel else excluded).append(c["recordId"])
        for rid in q.get("additionalRelevantIds", []):
            if rid not in relevant:
                relevant.append(rid)
                reviewed += 1
        queries.append({
            "id": q["id"], "purpose": q["purpose"], "searchQuery": q["searchQuery"],
            "region": q["region"],
            "relevantRecordIds": relevant,
            "excludedRecordIds": excluded,
        })

    # 유효성: 확정 관련 ID가 현재 스냅샷에 존재하는지 (스냅샷 교체 시 골든셋 드리프트 감지)
    missing = []
    for q in queries:
        for rid in q["relevantRecordIds"]:
            row = svc.conn.execute(
                "SELECT 1 FROM datasets WHERE record_id = ?", (rid,)
            ).fetchone()
            if row is None:
                missing.append((q["id"], rid))
    if missing:
        print(f"경고: 현재 스냅샷에 없는 관련 ID {len(missing)}건 — {missing[:5]}")

    out = {
        "version": "v1",
        "snapshot": review["snapshot"],
        "humanReviewed": reviewed > 0,
        "reviewedVerdicts": reviewed,
        "note": "recordId 고정 골든셋. 스냅샷 갱신 시 promote를 재실행해 드리프트를 검사한다(§11).",
        "queries": queries,
    }
    path = GOLDEN_DIR / "goldenset_v1.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    total_rel = sum(len(q["relevantRecordIds"]) for q in queries)
    print(f"골든셋 v1 생성: {path}")
    print(f"질의 {len(queries)}개 · 관련 {total_rel}건 · 인간 verdict {reviewed}건"
          + (" (0건 — 전부 자동 제안 채택 상태, humanReviewed=false)" if reviewed == 0 else ""))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "export":
        raise SystemExit(export())
    if cmd == "promote":
        raise SystemExit(promote())
    print(__doc__)
    raise SystemExit(2)
