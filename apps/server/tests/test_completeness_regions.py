from datanav.pipeline.completeness import compute_completeness
from datanav.pipeline.regions import match_regions
from tests.test_normalize import SAMPLE
from datanav.pipeline.normalize import normalize_row


def test_file_profile_selected():
    rec = normalize_row(SAMPLE, 2)
    c = compute_completeness(rec)
    assert c["profile"] == "FILE"
    assert c["rule"] == "catalog-completeness-file-v1.0"
    assert 0 <= c["score"] <= 1


def test_api_profile_does_not_penalize_file_fields():
    """API 목록에 파일 전용 필드(전체행·파일데이터명) 부재를 감점하지 않는다(§3.2)."""
    api_row = dict(SAMPLE, **{
        "목록유형": "API", "전체행": "-", "파일데이터명": "-",
        "API 유형": "REST", "신청가능 트래픽": "1000/일",
        "확장자(데이터포맷)": "JSON",
    })
    rec = normalize_row(api_row, 2)
    c = compute_completeness(rec)
    assert c["profile"] == "API"
    file_row = normalize_row(SAMPLE, 2)
    cf = compute_completeness(file_row)
    # 같은 공통 필드 충족 상태에서 API 프로파일이 파일 필드 부재로 손해 보지 않음
    assert c["score"] >= cf["score"] - 0.15


def test_region_evidence_ordering():
    # 공간범위 명시가 제목 추론보다 우선
    r = match_regions("부산광역시", "부산 버스정류장", "", "")
    busan = [x for x in r if x["code"] == "KR-26"][0]
    assert busan["evidence"] == "EXPLICIT_SPATIAL"
    assert busan["confidence"] == 0.95

    r2 = match_regions("", "부산 버스정류장", "", "")
    assert r2[0]["evidence"] == "INFERRED_FROM_TITLE"


def test_ambiguous_gwangju_low_confidence():
    """'광주'는 광주광역시/경기 광주시 동음이의 — 감점된 신뢰도."""
    r = match_regions("", "광주시 공영주차장", "", "")
    gj = [x for x in r if x["code"] == "KR-29"]
    assert gj and gj[0]["confidence"] < 0.8

    r2 = match_regions("광주광역시", "", "", "")
    gj2 = [x for x in r2 if x["code"] == "KR-29"]
    assert gj2 and gj2[0]["confidence"] == 0.95
