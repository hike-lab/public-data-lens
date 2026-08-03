import pytest
import json

from datanav.config import CURRENT_POINTER


def built_catalog_available() -> bool:
    return CURRENT_POINTER.exists()


requires_catalog = pytest.mark.skipif(
    not built_catalog_available(),
    reason="빌드된 카탈로그 없음 — scripts/build_catalog.py 먼저 실행",
)


@pytest.fixture(scope="session")
def service():
    from datanav.api.service import Service
    return Service()


def _catalog_rec(record_id: str, list_key: str, *, title: str, list_type: str = "FILE",
                 row_count: int | None = 100, keywords: list[str] | None = None) -> dict:
    source = {
        "목록키": list_key,
        "목록명": title,
        "기관명": "테스트기관",
        "전체행": "" if row_count is None else str(row_count),
    }
    return {
        "record_id": record_id,
        "list_key": list_key,
        "list_type": list_type,
        "title": title,
        "file_data_name": f"{title}.csv" if list_type == "FILE" else None,
        "theme_raw": "교육 - 테스트",
        "theme_top": "교육",
        "theme_sub": "테스트",
        "org_code": "TEST",
        "org_name": "테스트기관",
        "dept_name": "테스트부서",
        "dept_phone": None,
        "retention_basis": None,
        "collection_method": None,
        "update_cycle_raw": "월간",
        "update_cycle": "MONTHLY",
        "next_registration_date": None,
        "media_type": None,
        "row_count": row_count,
        "format_raw": "CSV" if list_type == "FILE" else None,
        "formats": ["CSV"] if list_type == "FILE" else [],
        "keywords": keywords or ["fixture"],
        "download_count": 0,
        "created_date": "2026-01-01",
        "modified_date": "2026-07-01",
        "data_limits": None,
        "provision_type": None,
        "description": f"{title} 설명",
        "notes": None,
        "spatial_raw": "서울특별시",
        "temporal_raw": "2026",
        "fee": "FREE",
        "fee_basis": None,
        "license_raw": "공공누리 제1유형",
        "license_code": "KOGL_BY",
        "api_type": "REST" if list_type == "API" else None,
        "traffic": None,
        "review_type": None,
        "view_count": 0,
        "list_url": f"https://www.data.go.kr/data/{list_key}/fileData.do",
        "is_national_core": 0,
        "is_standard": 0,
        "regions": [{
            "code": "KR-11",
            "name": "서울특별시",
            "evidence": "EXPLICIT_SPATIAL",
            "confidence": 1.0,
        }],
        "source_row_no": int(record_id[-3:]),
        "source_json": json.dumps(source, ensure_ascii=False),
    }


@pytest.fixture()
def catalog_db(tmp_path):
    from datanav.pipeline.completeness import compute_completeness
    from datanav.store.db import build_fts, create_db, insert_dataset

    db = tmp_path / "catalog.db"
    conn = create_db(db)
    rows = [
        _catalog_rec("rec-001", "list-001", title="도서관 현황", row_count=100,
                     keywords=["도서관", "현황"]),
        _catalog_rec("rec-002", "list-002", title="공원 시설", row_count=0,
                     keywords=["공원", "시설"]),
        _catalog_rec("rec-003", "list-003", title="주소 좌표", row_count=None,
                     keywords=["주소", "좌표"]),
        _catalog_rec("rec-004", "list-004", title="API 목록", list_type="API",
                     row_count=20, keywords=["API"]),
    ]
    for rec in rows:
        insert_dataset(conn, rec, compute_completeness(rec))
    conn.executemany(
        "INSERT INTO build_meta(key, value) VALUES (?, ?)",
        [
            ("snapshot", "2099-01"),
            ("processedAt", "2099-01-31T00:00:00Z"),
            ("release", "2099-01_fixture"),
        ],
    )
    build_fts(conn)
    conn.commit()
    conn.close()
    return db


@pytest.fixture()
def catalog_service(catalog_db):
    from datanav.api.service import Service
    return Service(catalog_db)
