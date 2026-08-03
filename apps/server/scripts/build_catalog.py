#!/usr/bin/env python3
"""월간 카탈로그 빌드 실행: python scripts/build_catalog.py <csv> <YYYY-MM>"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datanav.pipeline.build import BuildError, build_release  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    csv_path, snapshot = Path(sys.argv[1]), sys.argv[2]
    if not csv_path.exists():
        print(f"CSV 없음: {csv_path}")
        return 2
    t0 = time.time()
    try:
        release_dir = build_release(csv_path, snapshot)
    except BuildError as e:
        print(f"[중단] {e} — 이전 정상 버전 유지")
        return 1
    print(f"[완료] {release_dir.name} ({time.time() - t0:.1f}s)")
    print((release_dir / "build_report.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
