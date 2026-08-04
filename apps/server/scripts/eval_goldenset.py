#!/usr/bin/env python3
"""골든셋 평가 하네스(§11 검색 수용 기준): Precision@10, Recall@10, NDCG@10, 0건 비율, 목적 질의 성공률.

사용: python scripts/eval_goldenset.py [golden/goldenset_v0.json]
관련성 판정은 골든셋 파일의 titleRegex(+region)로 재현 가능하게 산출한다.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.api.service import Service  # noqa: E402

K = 10


def relevant_set(service: Service, q: dict) -> set[str]:
    """관련 집합 산출 — v1(recordId 고정) 우선, 없으면 v0(titleRegex) 방식."""
    if "relevantRecordIds" in q:
        return set(q["relevantRecordIds"])
    pat = re.compile(q["titleRegex"], re.IGNORECASE)
    region = q["region"]
    out = set()
    for rid, title, regions in service.conn.execute(
        "SELECT record_id, title, regions FROM datasets"
    ):
        if not pat.search(title):
            continue
        if region and f'"{region}"' not in regions:
            continue
        out.add(rid)
    return out


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(
        1 / math.log2(i + 2) for i, rid in enumerate(retrieved[:k]) if rid in relevant
    )
    ideal_hits = min(len(relevant), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg


def main() -> int:
    golden_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "golden" / "goldenset_v0.json"
    )
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    service = Service()

    rows = []
    for q in golden["queries"]:
        rel = relevant_set(service, q)
        res = service.search_datasets(
            query=q["searchQuery"], region=q["region"], page_size=K
        )
        retrieved = [i["recordId"] for i in res["data"]["items"]]
        hits = [r for r in retrieved if r in rel]
        rows.append({
            "id": q["id"],
            "searchQuery": q["searchQuery"],
            "region": q["region"],
            "relevantTotal": len(rel),
            "retrieved": len(retrieved),
            "hits": len(hits),
            "precisionAt10": round(len(hits) / K, 4),
            "recallAt10": round(len(hits) / min(len(rel), K), 4) if rel else None,
            "ndcgAt10": round(ndcg_at_k(retrieved, rel, K), 4),
            "zeroResult": len(retrieved) == 0,
            "success": len(hits) > 0,
        })

    n = len(rows)
    scored = [r for r in rows if r["relevantTotal"] > 0]
    summary = {
        "goldenVersion": golden["version"],
        "snapshot": service.snapshot,
        "indexVersion": service.release,
        "ranking": "ranking-bm25-v1.0",
        "queries": n,
        "queriesWithRelevant": len(scored),
        "meanPrecisionAt10": round(sum(r["precisionAt10"] for r in scored) / len(scored), 4),
        "meanRecallAt10": round(sum(r["recallAt10"] for r in scored) / len(scored), 4),
        "meanNdcgAt10": round(sum(r["ndcgAt10"] for r in scored) / len(scored), 4),
        "zeroResultRate": round(sum(r["zeroResult"] for r in rows) / n, 4),
        "successRate": round(sum(r["success"] for r in scored) / len(scored), 4),
        "humanReviewed": golden.get("humanReviewed", False),
    }
    report = {"summary": summary, "perQuery": rows}
    out = golden_path.parent / "eval_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    worst = sorted(scored, key=lambda r: r["ndcgAt10"])[:5]
    print("\n최저 NDCG 5개:")
    for r in worst:
        print(f"  {r['id']} {r['searchQuery']!r:24} rel={r['relevantTotal']:5} hits={r['hits']:2} ndcg={r['ndcgAt10']}")
    print(f"\n상세: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
