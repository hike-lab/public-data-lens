"""원본 CSV 파싱 — 원본값 보존이 최우선(수용 기준: 원본값 추적 가능, 파싱 실패 0)."""
from __future__ import annotations

import codecs
import csv
from pathlib import Path
from typing import Iterator

csv.field_size_limit(50_000_000)

# 목록개방현황 CSV 컬럼 → 내부 필드명 (매핑표의 1단계)
COLUMN_MAP = {
    "목록키": "list_key",
    "목록유형": "list_type",
    "목록명": "title",
    "파일데이터명": "file_data_name",
    "분류체계": "theme_raw",
    "제공기관코드": "org_code",
    "제공기관": "org_name",
    "관리 부서명": "dept_name",
    "관리부서 전화번호": "dept_phone_raw",
    "보유근거": "retention_basis",
    "수집방법": "collection_method",
    "업데이트 주기": "update_cycle_raw",
    "차기 등록 예정일": "next_registration_date",
    "매체유형": "media_type",
    "전체행": "row_count_raw",
    "확장자(데이터포맷)": "format_raw",
    "키워드": "keywords_raw",
    "다운로드_활용신청건수": "download_count_raw",
    "등록일": "created_date",
    "수정일": "modified_date",
    "데이터 한계": "data_limits",
    "제공형태": "provision_type",
    "설명": "description",
    "기타 유의사항": "notes",
    "공간범위": "spatial_raw",
    "시간범위": "temporal_raw",
    "비용부과유무": "fee_raw",
    "비용부과기준 및 단위": "fee_basis",
    "이용허락범위": "license_raw",
    "API 유형": "api_type_raw",
    "신청가능 트래픽": "traffic",
    "심의 유형": "review_type",
    "조회수": "view_count_raw",
    "목록 URL": "list_url",
    "국가중점여부": "national_core_raw",
    "표준데이터여부": "standard_raw",
}


class ParseError(Exception):
    pass


def detect_encoding(path: Path) -> str:
    """스냅샷 CSV 인코딩 감지 — UTF-8(BOM 허용) 우선, 실패 시 CP949(§8).
    포털 원본이 회차에 따라 어느 쪽으로도 내려올 수 있어 전량 스트림 검증으로 판별하고,
    호출자는 감지 결과를 meta.json·build_report.json에 기록한다."""
    for enc in ("utf-8-sig", "cp949"):
        decoder = codecs.getincrementaldecoder(enc)()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    decoder.decode(chunk)
                decoder.decode(b"", final=True)
            return enc
        except UnicodeDecodeError:
            continue
    raise ParseError(f"지원하지 않는 인코딩(utf-8/cp949 모두 아님): {path}")


def parse_snapshot_csv(path: Path, encoding: str | None = None) -> Iterator[dict]:
    """행 단위로 (source: 원본 dict, row_no) 반환. 컬럼 구조가 다르면 즉시 실패(§8)."""
    with open(path, encoding=encoding or detect_encoding(path), newline="") as f:
        reader = csv.DictReader(f)
        missing = set(COLUMN_MAP) - set(reader.fieldnames or [])
        if missing:
            raise ParseError(f"컬럼 구조 변경 감지 — 누락 컬럼: {sorted(missing)}")
        for row_no, row in enumerate(reader, start=2):  # 헤더가 1행
            if row.get("목록키") is None or row["목록키"].strip() == "":
                raise ParseError(f"{row_no}행: 목록키 없음")
            yield {"row_no": row_no, "source": row}
