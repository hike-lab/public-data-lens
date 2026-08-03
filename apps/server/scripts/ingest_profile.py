#!/usr/bin/env python3
"""프로파일 CSV → 관측 스토어 적재 (S1a).

사용법: python scripts/ingest_profile.py <프로파일_컬럼별.csv> <관측시점 ISO8601>
예:     python scripts/ingest_profile.py ~/Downloads/프로파일_컬럼별.csv 2026-07-29T00:00:00Z

- 라이선스 게이트는 현재 카탈로그 릴리스에서 주입한다(NO_RESTRICTION만 예시값 공개).
- 원자적 배포: 임시 파일로 빌드 후 rename. 리포트는 data/observations/reports/에 남긴다.
- 리포트에는 예시값 원문을 포함하지 않는다(안전 원칙) — 검수는 컬럼명·사유 기준.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.observe.ingest import ingest_profile_csv  # noqa: E402
from datanav.observe.store import OBSERVATIONS_DB, OBSERVATIONS_DIR  # noqa: E402
from datanav.store.db import open_ro  # noqa: E402
from datanav.config import current_db_path  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    csv_path = Path(sys.argv[1]).expanduser()
    observed_at = sys.argv[2]

    conn = open_ro(current_db_path())
    license_lookup = {
        r["list_key"]: r["license_code"]
        for r in conn.execute("SELECT list_key, license_code FROM datasets WHERE list_type='FILE'")
    }
    print(f"라이선스 게이트 주입: {len(license_lookup):,}건 (현재 카탈로그)")

    tmp = OBSERVATIONS_DB.with_suffix(".building")
    report = ingest_profile_csv(
        csv_path, tmp, license_lookup,
        observed_at=observed_at,
        example_method="FIRST_DISTINCT_UP_TO_10",
        scan_scope_assumed=True,
        source_note="프로파일 260729 — 외부 정리분(A.6). 해시 미제공 → UNVERIFIED_SOURCE",
    )
    tmp.replace(OBSERVATIONS_DB)  # 원자적 교체

    reports_dir = OBSERVATIONS_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"ingest-{observed_at[:10]}.json"
    out.write_text(json.dumps(report.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    # 안전 판정 표본 검수 파일(수용 기준) — 값은 포함하지 않는다(컬럼명·사유만)
    import sqlite3
    oconn = sqlite3.connect(OBSERVATIONS_DB)
    sample = oconn.execute(
        "SELECT a.list_key, a.file_name, c.source_name, c.safety_status, c.safety_reason "
        "FROM file_columns c JOIN data_tables t ON c.table_id=t.table_id "
        "JOIN observations o ON t.observation_id=o.observation_id "
        "JOIN source_assets a ON o.asset_id=a.asset_id "
        "WHERE c.safety_status != 'CLEAR' AND c.safety_status != 'NOT_ASSESSED' "
        "ORDER BY c.table_id LIMIT 100"
    ).fetchall()
    review = reports_dir / f"safety-review-sample-{observed_at[:10]}.csv"
    with open(review, "w", encoding="utf-8-sig") as f:
        f.write("list_key,file_name,source_name,safety_status,safety_reason\n")
        for r in sample:
            f.write(",".join(f'"{x}"' for x in r) + "\n")

    print(json.dumps(report.__dict__, ensure_ascii=False, indent=2))
    print(f"\n적재 완료: {OBSERVATIONS_DB}")
    print(f"리포트: {out}")
    print(f"안전 검수 표본(값 미포함): {review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
