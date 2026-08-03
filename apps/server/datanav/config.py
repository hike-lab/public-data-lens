"""경로·상수 설정. 설계서 §7 네임스페이스, §4.3 스키마 버전."""
from __future__ import annotations

import json
import os
from pathlib import Path

# 프로젝트 루트: apps/server/datanav/config.py → 3단계 위
PROJECT_ROOT = Path(
    os.environ.get("DATANAV_ROOT", Path(__file__).resolve().parents[3])
)
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CATALOG_DIR = DATA_DIR / "catalog"
RELEASES_DIR = CATALOG_DIR / "releases"
CURRENT_POINTER = CATALOG_DIR / "current.json"

# §7 확정 네임스페이스 (영구 불변)
BASE_URI = "https://service.datahub.kr/projects/public-data-lens"

SCHEMA_VERSION = "1.3.0"

DISCLAIMER = (
    "본 결과는 공공데이터포털 목록 메타데이터 기반이며 "
    "실제 데이터의 내용·품질·결합 가능성을 보증하지 않습니다."
)

# §4.3 입력 제한
MAX_QUERY_LENGTH = 500
MAX_COMPARE = 5
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def read_current_pointer() -> dict:
    """원자적 배포의 current 포인터를 읽는다(§8)."""
    if not CURRENT_POINTER.exists():
        raise FileNotFoundError(
            f"current 포인터가 없습니다: {CURRENT_POINTER} — 먼저 빌드를 실행하세요."
        )
    return json.loads(CURRENT_POINTER.read_text(encoding="utf-8"))


def current_db_path() -> Path:
    ptr = read_current_pointer()
    return RELEASES_DIR / ptr["release"] / "catalog.db"
