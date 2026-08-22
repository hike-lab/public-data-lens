"""정규화(매핑표 2단계) — 포맷·주기·라이선스·수치·키워드. 원본은 source에 보존."""
from __future__ import annotations

import datetime as dt
import json
import re

from .parse import COLUMN_MAP
from .regions import match_regions

EMPTY = ("", "-", "null", "없음")

CYCLE_MAP = {
    "수시": "IRREGULAR",
    "일간": "DAILY",
    "주간": "WEEKLY",
    "월간": "MONTHLY",
    "분기": "QUARTERLY",
    "반기": "SEMIANNUAL",
    "연간": "ANNUAL",
    "-": "UNSPECIFIED",
    "": "UNSPECIFIED",
}

LICENSE_MAP = {
    "이용허락범위 제한 없음": "NO_RESTRICTION",
    "공공저작물_출처표시": "KOGL_BY",
    "공공저작물_출처표시 + 상업적 이용금지": "KOGL_BY_NC",
    "공공저작물_출처표시 + 변경금지": "KOGL_BY_ND",
    "공공저작물_출처표시 + 상업적 이용금지 + 변경금지": "KOGL_BY_NC_ND",
    "저작자표시-비영리-동일조건변경허락": "CC_BY_NC_SA",
    "-": "UNSPECIFIED",
    "": "UNSPECIFIED",
}

FEE_MAP = {"무료": "FREE", "유료": "PAID", "-": "UNSPECIFIED", "": "UNSPECIFIED"}

_URL_RE = re.compile(r"^https?://", re.I)

def is_empty(v: str | None) -> bool:
    return v is None or v.strip() in EMPTY


# rule: normalize-date-v1.0 — 엑셀 일련번호 날짜 환산
# 발행자 내보내기 경로에 따라 날짜 컬럼이 엑셀 내부 일련번호로 내려오는 회차가 있다
# (2026-07 스냅샷의 API 블록 11,960행). 기준 원점은 엑셀 1900 날짜 체계의 1899-12-30.
# 범위 하한을 두어 연도 4자리("2026" 등)를 일련번호로 오인하지 않는다.
_EXCEL_EPOCH = dt.date(1899, 12, 30)
_SERIAL_RE = re.compile(r"^\d{5}$")
_SERIAL_MIN, _SERIAL_MAX = 30000, 60000  # 1982-03-12 ~ 2064-04-05
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_DATE_COLUMNS = ("등록일", "수정일", "차기 등록 예정일")


def excel_serial_to_iso(raw: str) -> str | None:
    """엑셀 일련번호 문자열 → ISO 날짜. 일련번호로 판정되지 않으면 None."""
    v = raw.strip()
    if not _SERIAL_RE.match(v):
        return None
    n = int(v)
    if not _SERIAL_MIN <= n <= _SERIAL_MAX:
        return None
    return (_EXCEL_EPOCH + dt.timedelta(days=n)).isoformat()


def normalize_date(raw: str | None) -> str | None:
    """ISO 날짜는 그대로, 엑셀 일련번호는 환산, 그 외 원본값 유지(§8 원본값 추적).
    변환 사실은 detect_issues가 EXCEL_SERIAL_DATE_ARTIFACT로 별도 관찰한다."""
    if is_empty(raw):
        return None
    v = raw.strip()
    if _ISO_DATE_RE.match(v):
        return v
    return excel_serial_to_iso(v) or v


def _to_int(v: str | None) -> int | None:
    if is_empty(v):
        return None
    try:
        return int(v.strip().replace(",", ""))
    except ValueError:
        return None


def normalize_formats(raw: str | None) -> list[str]:
    if is_empty(raw):
        return []
    tokens = re.split(r"[+,/]", raw.strip())
    out = []
    for t in tokens:
        t = t.strip().upper()
        if t and t not in out:
            out.append(t)
    return out


def normalize_keywords(raw: str | None) -> list[str]:
    if is_empty(raw):
        return []
    out = []
    for k in raw.split(","):
        k = k.strip()
        if k and k not in out:
            out.append(k)
    return out


def normalize_row(source: dict, row_no: int) -> dict:
    """원본 행 → 정규화 레코드. record_id는 build 단계에서 중복 해소 후 확정."""
    s = {COLUMN_MAP[k]: (v if v is not None else "") for k, v in source.items() if k in COLUMN_MAP}

    theme_raw = s["theme_raw"].strip()
    theme_top, theme_sub = theme_raw, None
    if " - " in theme_raw:
        theme_top, theme_sub = [p.strip() for p in theme_raw.split(" - ", 1)]

    phone = s["dept_phone_raw"].strip().lstrip("`'").strip()

    rec = {
        "list_key": s["list_key"].strip(),
        "list_type": s["list_type"].strip().upper(),
        "title": s["title"].strip(),
        "file_data_name": None if is_empty(s["file_data_name"]) else s["file_data_name"].strip(),
        "theme_raw": theme_raw or None,
        "theme_top": theme_top or None,
        "theme_sub": theme_sub,
        "org_code": s["org_code"].strip() or None,
        "org_name": s["org_name"].strip() or None,
        "dept_name": None if is_empty(s["dept_name"]) else s["dept_name"].strip(),
        "dept_phone": phone or None,
        "retention_basis": None if is_empty(s["retention_basis"]) else s["retention_basis"].strip(),
        "collection_method": None if is_empty(s["collection_method"]) else s["collection_method"].strip(),
        "update_cycle_raw": s["update_cycle_raw"].strip() or None,
        "update_cycle": CYCLE_MAP.get(s["update_cycle_raw"].strip(), "OTHER"),
        "next_registration_date": normalize_date(s["next_registration_date"]),
        "media_type": None if is_empty(s["media_type"]) else s["media_type"].strip(),
        "row_count": _to_int(s["row_count_raw"]),
        "format_raw": s["format_raw"].strip() or None,
        "formats": normalize_formats(s["format_raw"]),
        "keywords": normalize_keywords(s["keywords_raw"]),
        "download_count": _to_int(s["download_count_raw"]),
        "created_date": normalize_date(s["created_date"]),
        "modified_date": normalize_date(s["modified_date"]),
        "data_limits": None if is_empty(s["data_limits"]) else s["data_limits"].strip(),
        "provision_type": None if is_empty(s["provision_type"]) else s["provision_type"].strip(),
        "description": None if is_empty(s["description"]) else s["description"].strip(),
        "notes": None if is_empty(s["notes"]) else s["notes"].strip(),
        "spatial_raw": None if is_empty(s["spatial_raw"]) else s["spatial_raw"].strip(),
        "temporal_raw": None if is_empty(s["temporal_raw"]) else s["temporal_raw"].strip(),
        "fee": FEE_MAP.get(s["fee_raw"].strip(), "OTHER"),
        "fee_basis": None if is_empty(s["fee_basis"]) else s["fee_basis"].strip(),
        "license_raw": s["license_raw"].strip() or None,
        "license_code": LICENSE_MAP.get(s["license_raw"].strip(), "OTHER"),
        "api_type": None if is_empty(s["api_type_raw"]) else s["api_type_raw"].strip().upper(),
        "traffic": None if is_empty(s["traffic"]) else s["traffic"].strip(),
        "review_type": None if is_empty(s["review_type"]) else s["review_type"].strip(),
        "view_count": _to_int(s["view_count_raw"]),
        "list_url": s["list_url"].strip() or None,
        "is_national_core": 1 if s["national_core_raw"].strip() == "Y" else 0,
        "is_standard": 1 if s["standard_raw"].strip() == "Y" else 0,
        "source_row_no": row_no,
        "source_json": json.dumps(source, ensure_ascii=False),
    }
    rec["regions"] = match_regions(
        rec["spatial_raw"] or "", rec["title"], rec["org_name"] or "", rec["description"] or ""
    )
    return rec


def detect_issues(rec: dict, source: dict) -> list[dict]:
    """rule: issue-detect-v1.0 — 원본 속성을 바꾸지 않는 별도 관찰(§6)."""
    issues = []
    phone_raw = source.get("관리부서 전화번호", "")
    if phone_raw and phone_raw.lstrip() and phone_raw.lstrip()[0] in "`'":
        issues.append({
            "field": "관리부서 전화번호",
            "source_value": phone_raw,
            "issue_type": "LEADING_QUOTE_ARTIFACT",
            "confidence": 0.95,
        })
    url = rec.get("list_url")
    if url and not _URL_RE.match(url):
        issues.append({
            "field": "목록 URL",
            "source_value": url,
            "issue_type": "INVALID_URL_FORMAT",
            "confidence": 0.9,
        })
    for col in _DATE_COLUMNS:
        raw = source.get(col, "")
        if raw and excel_serial_to_iso(raw) is not None:
            issues.append({
                "field": col,
                "source_value": raw,
                "issue_type": "EXCEL_SERIAL_DATE_ARTIFACT",
                "confidence": 1.0,
            })
        elif not is_empty(raw) and not _ISO_DATE_RE.match(raw.strip()):
            issues.append({
                "field": col,
                "source_value": raw,
                "issue_type": "UNPARSEABLE_DATE_FORMAT",
                "confidence": 0.9,
            })
    for col, field in (("전체행", "row_count"), ("다운로드_활용신청건수", "download_count"), ("조회수", "view_count")):
        raw = source.get(col, "")
        if not is_empty(raw) and rec.get(field) is None:
            issues.append({
                "field": col,
                "source_value": raw,
                "issue_type": "NEGATIVE_OR_NONNUMERIC_COUNT",
                "confidence": 0.8,
            })
        elif rec.get(field) is not None and rec[field] < 0:
            issues.append({
                "field": col,
                "source_value": raw,
                "issue_type": "NEGATIVE_OR_NONNUMERIC_COUNT",
                "confidence": 0.9,
            })
    return issues
