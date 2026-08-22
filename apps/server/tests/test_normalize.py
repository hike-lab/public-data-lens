from datanav.pipeline.normalize import (
    detect_issues,
    excel_serial_to_iso,
    normalize_date,
    normalize_formats,
    normalize_keywords,
    normalize_row,
)

SAMPLE = {
    "목록키": "15000001",
    "목록유형": "FILE",
    "목록명": "테스트_데이터",
    "파일데이터명": "테스트_20260101",
    "분류체계": "공공행정 - 법제",
    "제공기관코드": "1000000",
    "제공기관": "테스트기관",
    "관리 부서명": "테스트팀",
    "관리부서 전화번호": "`0212345678",
    "보유근거": "-",
    "수집방법": "-",
    "업데이트 주기": "연간",
    "차기 등록 예정일": "2027-01-01",
    "매체유형": "텍스트",
    "전체행": "1,234",
    "확장자(데이터포맷)": "JSON+XML",
    "키워드": "a,b, a ,c",
    "다운로드_활용신청건수": "10",
    "등록일": "2020-01-01",
    "수정일": "2026-01-01",
    "데이터 한계": "-",
    "제공형태": "-",
    "설명": "설명문",
    "기타 유의사항": "-",
    "공간범위": "서울특별시",
    "시간범위": "2025년",
    "비용부과유무": "무료",
    "비용부과기준 및 단위": "-",
    "이용허락범위": "공공저작물_출처표시",
    "API 유형": "-",
    "신청가능 트래픽": "-",
    "심의 유형": "-",
    "조회수": "100",
    "목록 URL": "https://www.data.go.kr/data/15000001/fileData.do",
    "국가중점여부": "N",
    "표준데이터여부": "N",
}


def test_format_normalization():
    assert normalize_formats("JSON+XML") == ["JSON", "XML"]
    assert normalize_formats("csv") == ["CSV"]
    assert normalize_formats("CSV") == ["CSV"]
    assert normalize_formats("-") == []
    assert normalize_formats(None) == []


def test_keyword_dedup_and_trim():
    assert normalize_keywords("a,b, a ,c") == ["a", "b", "c"]


def test_normalize_row_core_fields():
    rec = normalize_row(SAMPLE, row_no=2)
    assert rec["list_key"] == "15000001"
    assert rec["update_cycle"] == "ANNUAL"
    assert rec["license_code"] == "KOGL_BY"
    assert rec["theme_top"] == "공공행정" and rec["theme_sub"] == "법제"
    assert rec["row_count"] == 1234
    assert rec["dept_phone"] == "0212345678"  # 백틱 제거(원본은 source_json에 보존)
    assert rec["data_limits"] is None  # '-' → None
    assert rec["fee"] == "FREE"
    # 원본값 추적 가능(수용 기준)
    import json
    assert json.loads(rec["source_json"])["관리부서 전화번호"] == "`0212345678"


def test_region_explicit_from_spatial():
    rec = normalize_row(SAMPLE, row_no=2)
    seoul = [r for r in rec["regions"] if r["code"] == "KR-11"]
    assert seoul and seoul[0]["evidence"] == "EXPLICIT_SPATIAL"


def test_issue_detection_backtick_and_url():
    rec = normalize_row(SAMPLE, row_no=2)
    issues = detect_issues(rec, SAMPLE)
    types = {i["issue_type"] for i in issues}
    assert "LEADING_QUOTE_ARTIFACT" in types

    bad = dict(SAMPLE, **{"목록 URL": "www.data.go.kr/no-scheme"})
    rec2 = normalize_row(bad, row_no=3)
    types2 = {i["issue_type"] for i in detect_issues(rec2, bad)}
    assert "INVALID_URL_FORMAT" in types2


def test_issue_nonnumeric_count():
    bad = dict(SAMPLE, **{"전체행": "abc"})
    rec = normalize_row(bad, row_no=4)
    assert rec["row_count"] is None
    types = {i["issue_type"] for i in detect_issues(rec, bad)}
    assert "NEGATIVE_OR_NONNUMERIC_COUNT" in types


# ------------------------------------------------- normalize-date-v1.0

def test_iso_date_passes_through():
    assert normalize_date("2012-12-06") == "2012-12-06"


def test_excel_serial_is_converted():
    """2026-07 스냅샷 실측: 41249 → 2012-12-06 (2026-06 스냅샷 대조 전건 일치)."""
    assert excel_serial_to_iso("41249") == "2012-12-06"
    assert excel_serial_to_iso("44834") == "2022-09-30"
    assert excel_serial_to_iso("45912") == "2025-09-12"
    assert normalize_date("41249") == "2012-12-06"


def test_year_like_value_is_not_treated_as_serial():
    """연도 4자리를 일련번호로 오인하지 않는다."""
    assert excel_serial_to_iso("2026") is None
    assert normalize_date("2026") == "2026"


def test_out_of_range_serial_is_left_alone():
    assert excel_serial_to_iso("12345") is None
    assert excel_serial_to_iso("99999") is None


def test_unrecognized_date_keeps_source_value():
    """해석 불가 값을 버리지 않는다 — 원본값 추적(§8)."""
    assert normalize_date("2026.07.31") == "2026.07.31"
    assert normalize_date("-") is None


def test_serial_date_is_observed_not_silently_fixed():
    src = dict(SAMPLE, 등록일="41249", 수정일="44834")
    rec = normalize_row(src, 2)
    assert rec["created_date"] == "2012-12-06"
    assert rec["modified_date"] == "2022-09-30"
    types = {(i["field"], i["issue_type"]) for i in detect_issues(rec, src)}
    assert ("등록일", "EXCEL_SERIAL_DATE_ARTIFACT") in types
    assert ("수정일", "EXCEL_SERIAL_DATE_ARTIFACT") in types


def test_clean_iso_dates_produce_no_date_issue():
    rec = normalize_row(SAMPLE, 2)
    date_issues = [
        i for i in detect_issues(rec, SAMPLE)
        if i["issue_type"] in ("EXCEL_SERIAL_DATE_ARTIFACT", "UNPARSEABLE_DATE_FORMAT")
    ]
    assert date_issues == []


def test_unparseable_date_is_observed():
    src = dict(SAMPLE, 수정일="2026.07.31")
    rec = normalize_row(src, 2)
    types = {(i["field"], i["issue_type"]) for i in detect_issues(rec, src)}
    assert ("수정일", "UNPARSEABLE_DATE_FORMAT") in types
