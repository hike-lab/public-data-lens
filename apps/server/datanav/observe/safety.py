"""예시값 안전 판정 — sample-safety-v1.0 (v2.2 §7).

원칙: 판정을 통과하지 않은 원본 값은 영구 저장·반환하지 않는다(호출자가 보장).
시설명·기관명·기관 주소는 일률 차단하지 않는다 — 과차단은 서비스 가치를 없앤다.
보수 기본값: 애매하면 REVIEW_REQUIRED(공개 표면에서는 WITHHELD와 동일하게 비노출).
"""
from __future__ import annotations

import re

RULE_SAFETY = "sample-safety-v1.0"

# ---- 컬럼명 사전 (v2.2 §7 위험군 표) --------------------------------------
# WITHHELD: 개인 직접 식별·연락 수단. 부분 문자열 오탐을 피하기 위해 경계를 신중히 정의.
_NAME_WITHHELD = [
    "주민등록", "주민번호", "생년월일",
    "전화", "연락처", "휴대폰", "핸드폰", "휴대전화",
    "이메일", "메일주소", "email", "e-mail",
    "계좌", "카드번호", "차량번호", "차량 번호", "여권",
    "면허번호", "자격번호", "상세주소",
]
# '성명'류: 시설명·사업장명 등과의 오탐을 막기 위해 어미 일치로만 판정
_NAME_WITHHELD_SUFFIX = ["성명", "대표자명", "담당자명", "신청인명", "환자명", "학생명"]
_NAME_WITHHELD_EXACT = ["이름", "성함"]

# REVIEW_REQUIRED: 자유서술 가능 컬럼(값 검토 전 비노출)
_NAME_REVIEW = ["민원", "상담내용", "요청사항", "질의내용", "사연"]

# ---- 값 패턴 ---------------------------------------------------------------
# (?<!\d)/(?!\d) 경계: 고정밀 좌표·측정값·장식별자 등 더 긴 숫자열 내부 매칭을 배제
_RE_MOBILE = re.compile(r"(?<!\d)01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
_RE_LANDLINE = re.compile(r"(?<!\d)0\d{1,2}[-.\s]\d{3,4}[-.\s]\d{4}(?!\d)")  # 구분자 필수
_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RE_RRN = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})[-\s]?[1-4]\d{6}(?!\d)")


def _looks_like_rrn(v: str) -> bool:
    """주민등록번호형 — 숫자 경계 + 생년월일 타당성(월 01-12, 일 01-31)까지 확인."""
    for m in _RE_RRN.finditer(v):
        mm, dd = int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return True
    return False

_FREE_TEXT_AVG_LEN = 80  # 자유서술 휴리스틱


def screen_column(source_name: str, examples: list[str]) -> tuple[str, str | None]:
    """(safety_status, reason) 반환. CLEAR가 아니면 호출자는 예시값을 폐기해야 한다."""
    name = (source_name or "").strip().lower()

    for pat in _NAME_WITHHELD:
        if pat in name:
            return "WITHHELD", f"column-name:{pat}"
    for suf in _NAME_WITHHELD_SUFFIX:
        if name.endswith(suf):
            return "WITHHELD", f"column-name-suffix:{suf}"
    if name in _NAME_WITHHELD_EXACT:
        return "WITHHELD", f"column-name-exact:{name}"

    # 값 단위로 검사한다 — 이어붙여 검사하면 인접한 코드값 두 개가 결합되어
    # 주민번호형 등으로 오탐된다(예: 10자리 행정코드 + 공백 + 10자리 행정코드).
    for v in examples:
        v = str(v)
        if _looks_like_rrn(v):
            return "WITHHELD", "value-pattern:rrn"
        if _RE_MOBILE.search(v):
            return "WITHHELD", "value-pattern:mobile"
        if _RE_EMAIL.search(v):
            return "WITHHELD", "value-pattern:email"
        if _RE_LANDLINE.search(v):
            return "WITHHELD", "value-pattern:landline"

    for pat in _NAME_REVIEW:
        if pat in name:
            return "REVIEW_REQUIRED", f"column-name:{pat}"
    if examples:
        avg = sum(len(str(v)) for v in examples) / len(examples)
        if avg > _FREE_TEXT_AVG_LEN:
            return "REVIEW_REQUIRED", "free-text-heuristic"

    return "CLEAR", None
