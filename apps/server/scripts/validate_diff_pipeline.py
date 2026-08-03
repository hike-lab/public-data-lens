#!/usr/bin/env python3
"""diff 파이프라인 실전 검증 — 2026-02에서 파생한 합성 스냅샷으로 전 경로를 확인하고 원상 복구한다.

시나리오: 30건 제거(MISSING_FROM_SNAPSHOT), 50건 수정일 변경(MODIFIED),
5건 제목+기관 동시 변경(POSSIBLE_IDENTITY_CHANGE), 10건 신규(ADDED).
실제 월간 CSV를 확보하면 build_catalog.py로 동일 경로가 실행된다.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.config import CATALOG_DIR, CURRENT_POINTER, RAW_DIR, RELEASES_DIR  # noqa: E402
from datanav.pipeline.build import build_release  # noqa: E402

csv.field_size_limit(50_000_000)

N_MISSING, N_MODIFIED, N_IDENTITY, N_ADDED = 30, 50, 5, 10
SYNTH_SNAPSHOT = "2026-03-synthetic"

EXPECTED = {
    "MISSING_FROM_SNAPSHOT": N_MISSING,
    "MODIFIED": N_MODIFIED,
    "POSSIBLE_IDENTITY_CHANGE": N_IDENTITY,
    "ADDED": N_ADDED,
}


def make_synthetic(src: Path, dst: Path) -> None:
    with open(src, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    i_key, i_title, i_org, i_mod = (
        header.index("목록키"), header.index("목록명"),
        header.index("제공기관"), header.index("수정일"),
    )
    key_counts = Counter(r[i_key] for r in rows)
    # 중복키 행은 건드리지 않아 상태 수를 정확히 예측한다
    unique_idx = [i for i, r in enumerate(rows) if key_counts[r[i_key]] == 1]

    drop = set(unique_idx[:N_MISSING])
    modify = unique_idx[N_MISSING:N_MISSING + N_MODIFIED]
    identity = unique_idx[N_MISSING + N_MODIFIED:N_MISSING + N_MODIFIED + N_IDENTITY]
    for i in modify:
        rows[i][i_mod] = "2026-03-01"
    for i in identity:
        rows[i][i_title] = "완전히다른데이터_" + rows[i][i_key]
        rows[i][i_org] = "다른기관_" + rows[i][i_key]

    template = rows[unique_idx[-1]]
    added = []
    for n in range(N_ADDED):
        r = list(template)
        r[i_key] = f"99{n:06d}"
        r[i_title] = f"합성_신규_데이터셋_{n}"
        added.append(r)

    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for i, r in enumerate(rows):
            if i not in drop:
                w.writerow(r)
        w.writerows(added)


def main() -> int:
    src = RAW_DIR / "2026-02" / "public_data_2026-02.csv"
    if not src.exists() or not CURRENT_POINTER.exists():
        print("2026-02 릴리스가 먼저 필요합니다")
        return 2

    pointer_backup = CURRENT_POINTER.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        synth_csv = Path(td) / "synthetic.csv"
        print("합성 스냅샷 생성 중…")
        make_synthetic(src, synth_csv)

        print("합성 스냅샷 빌드(diff 포함) 중…")
        release_dir = build_release(synth_csv, SYNTH_SNAPSHOT)
        report = json.loads((release_dir / "build_report.json").read_text(encoding="utf-8"))
        counts = report["diff"]["counts"]
        print(f"기준 스냅샷: {report['diff']['baseSnapshot']}")
        print(f"판정 결과:   {counts}")
        print(f"기대 결과:   {EXPECTED}")
        ok = counts == EXPECTED

        # 변경 API 경로 확인
        from datanav.api.service import Service
        svc = Service()
        ch = svc.get_catalog_changes(status="POSSIBLE_IDENTITY_CHANGE", page_size=10)
        api_ok = ch["data"]["totalEstimate"] == N_IDENTITY and all(
            set(i["changedFields"]) >= {"title", "org_name"} for i in ch["data"]["items"]
        )
        print(f"changes API(POSSIBLE_IDENTITY_CHANGE): {ch['data']['totalEstimate']}건, 필드 표기 {'OK' if api_ok else 'FAIL'}")
        svc.conn.close()

    # 원상 복구: 포인터 되돌리고 합성 산출물 제거
    CURRENT_POINTER.write_text(pointer_backup, encoding="utf-8")
    for d in RELEASES_DIR.glob(f"{SYNTH_SNAPSHOT}_*"):
        shutil.rmtree(d)
    synth_raw = RAW_DIR / SYNTH_SNAPSHOT
    if synth_raw.exists():
        shutil.rmtree(synth_raw)

    from datanav.api.service import Service
    svc = Service()
    restored = svc.snapshot == "2026-02" and svc.get_catalog_changes()["data"]["totalEstimate"] == 0
    print(f"원상 복구: 현재 스냅샷 {svc.snapshot}, changes {'비어 있음' if restored else 'FAIL'}")

    verdict = ok and api_ok and restored
    print(f"\n검증 {'통과' if verdict else '실패'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
