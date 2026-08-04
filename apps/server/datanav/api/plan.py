"""활용 계획 초안 조립기 — build_data_plan Tool(계약 v1.4)의 구현.

§2 책임 분리를 유지하는 **결정론적 계획 조립기**: 서버는 LLM 없이 규칙으로만
검색어 추출 → 후보 검색 → 역할 배정 → 근거·한계·예상 결합 키를 조립한다.

서버가 하는 판단: 어떤 검색어·필터를 썼는지, 어떤 후보가 어떤 근거(fitSignals)로
어떤 역할을 할 수 있는지, 무엇이 부족한지(missingNeeds), 무엇을 확인해야 하는지.
서버가 하지 않는 판단: 품질 확정(NOT_ASSESSED), 결합 가능성 확정(CANDIDATE_ONLY),
분석 충분성 확정 — 모든 산출은 초안(planStatus=DRAFT)이다. 검증·반복 설계는
별도 컨시어지의 몫이다.
"""
from __future__ import annotations

import re

from .envelope import envelope
from .errors import InvalidArgument

RULE_PLAN = "plan-assembly-v1.0"
RULE_QUERY_INTERPRET = "query-interpret-v1.0"

# 시·도 이름 → ISO 3166-2:KR (search_datasets의 region 코드 체계와 동일)
REGION_CODES: dict[str, str] = {
    "서울": "KR-11", "서울시": "KR-11", "서울특별시": "KR-11",
    "부산": "KR-26", "부산시": "KR-26", "부산광역시": "KR-26",
    "대구": "KR-27", "대구시": "KR-27", "대구광역시": "KR-27",
    "인천": "KR-28", "인천시": "KR-28", "인천광역시": "KR-28",
    "광주": "KR-29", "광주시": "KR-29", "광주광역시": "KR-29",
    "대전": "KR-30", "대전시": "KR-30", "대전광역시": "KR-30",
    "울산": "KR-31", "울산시": "KR-31", "울산광역시": "KR-31",
    "세종": "KR-50", "세종시": "KR-50", "세종특별자치시": "KR-50",
    "경기": "KR-41", "경기도": "KR-41",
    "강원": "KR-42", "강원도": "KR-42", "강원특별자치도": "KR-42",
    "충북": "KR-43", "충청북도": "KR-43", "충남": "KR-44", "충청남도": "KR-44",
    "전북": "KR-45", "전라북도": "KR-45", "전북특별자치도": "KR-45",
    "전남": "KR-46", "전라남도": "KR-46",
    "경북": "KR-47", "경상북도": "KR-47", "경남": "KR-48", "경상남도": "KR-48",
    "제주": "KR-49", "제주도": "KR-49", "제주특별자치도": "KR-49",
}
_REGION_CODE_SET = set(REGION_CODES.values())

# 질의 해석 별칭(query-interpret-v1.0) — 검색어 토큰을 결정론적으로 필터로 옮긴다.
# 제한 어휘: 확장은 additive(규칙 버전 증가 없이 사전 추가 금지 — registry definition 참조).
_FORMAT_ALIAS = {"CSV": "CSV", "JSON": "JSON", "XML": "XML", "XLSX": "XLSX",
                 "엑셀": "XLSX", "EXCEL": "XLSX", "PDF": "PDF", "SHP": "SHP"}
_CYCLE_ALIAS = {"일간": "DAILY", "매일": "DAILY", "주간": "WEEKLY", "매주": "WEEKLY",
                "월간": "MONTHLY", "매월": "MONTHLY", "분기": "QUARTERLY",
                "반기": "SEMIANNUAL", "연간": "ANNUAL", "매년": "ANNUAL", "수시": "IRREGULAR"}
_TYPE_ALIAS = {"API": "API", "파일": "FILE", "FILE": "FILE", "표준": "STD", "STD": "STD"}
_INTERPRET_FIELDS = ("region", "format", "updateCycle", "listType")


def interpret_query(raw: str, skip_fields: set[str] | None = None) -> tuple[str, list[dict]]:
    """검색어에서 지역·포맷·주기·유형 토큰을 필터로 분리한다(query-interpret-v1.0).

    반환: (남은 질의, interpretedFilters[]{field,value,sourceToken,ruleId}).
    skip_fields의 축은 해석하지 않는다(명시 필터 우선 — 토큰은 질의에 남긴다).
    """
    skip = skip_fields or set()
    interpreted: list[dict] = []
    seen: set[str] = set()
    rest: list[str] = []

    def hit(field: str, value: str, token: str) -> bool:
        if field in skip or field in seen:
            return False
        seen.add(field)
        interpreted.append({"field": field, "value": value,
                            "sourceToken": token, "ruleId": RULE_QUERY_INTERPRET})
        return True

    for token in raw.split():
        t = token.strip()
        up = t.upper()
        if t in REGION_CODES and hit("region", REGION_CODES[t], token):
            continue
        if up in _FORMAT_ALIAS and hit("format", _FORMAT_ALIAS[up], token):
            continue
        if t in _CYCLE_ALIAS and hit("updateCycle", _CYCLE_ALIAS[t], token):
            continue
        if up in _TYPE_ALIAS and hit("listType", _TYPE_ALIAS[up], token):
            continue
        rest.append(token)
    return " ".join(rest), interpreted

# 목적 문장에서 걷어낼 일반어(검색 변별력 없음) — 제한 어휘, 확장은 additive
_STOPWORDS = {
    "데이터", "공공데이터", "자료", "정보", "관련", "및", "대한", "위한", "위해",
    "분석하고", "분석하려고", "검토", "검토하고", "활용", "활용하려고", "참고", "참고할",
    "싶다", "싶어", "싶습니다", "한다", "하려고", "합니다", "찾아줘", "찾아", "알려줘",
    "필요한", "필요하다", "중인데", "있는", "하는",
}
_PARTICLES = ("에서", "으로", "까지", "부터", "이나", "라도",
              "을", "를", "이", "가", "은", "는", "도", "의", "와", "과", "로", "에")

# 역할 배정 규칙(제목·주제 기반) — 제한 템플릿(v1): PRIMARY/DEMAND/SUPPLY/SPATIAL/TEMPORAL/REFERENCE
_DEMAND_PAT = re.compile(r"인구|수요|이용객|이용량|이용현황|등록\s?대수|가구|세대|방문객|승하차")
_SUPPLY_PAT = re.compile(r"시설|위치|충전소|정류장|기관|센터|병원|의원|약국|학교|주차장|쉼터|도서관")
_REFERENCE_PAT = re.compile(r"코드|분류체계|표준")
_SPATIAL_COL = re.compile(r"위도|경도|좌표|주소|소재지|행정동|법정동|시군구")
_TEMPORAL_COL = re.compile(r"연도|년도|일자|날짜|기준일|년월|시점")
# 목적 문장이 수요·공급 결합형 분석을 시사하는지(DEMAND/SUPPLY 요구를 계획에 포함할지)
_ANALYSIS_HINT = re.compile(r"접근성|수요|사각지대|입지|배치|격차|불균형|공급")

# 예상 결합 키 후보 패턴 — 항상 CANDIDATE_ONLY(값 체계 일치는 검증하지 않음)
_JOIN_PATTERNS: list[tuple[str, re.Pattern | None]] = [
    ("행정구역·법정동 코드", re.compile(r"행정.{0,3}코드|법정동.{0,2}코드|시군구.{0,2}코드|지역.?코드")),
    ("주소·소재지", re.compile(r"주소|소재지")),
    ("좌표(위도·경도)", None),  # 특수: 위도·경도 쌍이 모두 관측되어야 함
    ("기준 연도·일자", re.compile(r"연도|년도|기준일")),
    ("사업자등록번호", re.compile(r"사업자.{0,2}등록.{0,2}번호")),
]

_MAX_CANDIDATES = 8


def _strip_particle(token: str) -> str:
    for p in _PARTICLES:
        if len(token) > len(p) + 1 and token.endswith(p):
            return token[: -len(p)]
    return token


def _extract_terms(purpose: str) -> tuple[list[str], str | None]:
    """목적 문장 → (검색어 목록, 문장 내 지역 코드). 결정론적 토큰 규칙만 사용한다."""
    region_code = None
    terms: list[str] = []
    for raw in re.split(r"[\s,·]+", purpose.strip()):
        t = _strip_particle(re.sub(r"[^\w가-힣]", "", raw))
        if not t or len(t) < 2:
            continue
        if t in REGION_CODES:
            region_code = region_code or REGION_CODES[t]
            continue
        if t in _STOPWORDS:
            continue
        terms.append(t)
    return terms[:6], region_code  # 검색어 상한 — 과도한 질의 방지


def _resolve_region(region: str | None) -> str | None:
    if not region:
        return None
    r = region.strip()
    if r in _REGION_CODE_SET:
        return r
    if r in REGION_CODES:
        return REGION_CODES[r]
    raise InvalidArgument(
        "region은 시·도 코드(KR-11) 또는 시·도명(서울특별시)이어야 합니다",
        {"region": region, "accepted": sorted(_REGION_CODE_SET)},
    )


def _observed_columns(svc, item: dict) -> list[str]:
    """후보의 관측 컬럼명(실파일 근거). 미관측이면 빈 목록 — 컬럼 부재가 아니라 미수집."""
    if not item.get("structureAvailable"):
        return []
    body = svc.get_dataset_structure(item["recordId"], view_examples=False)
    cols: list[str] = []
    for asset in body["data"].get("assets", []):
        for table in asset.get("tables", []) or []:
            cols.extend(c["sourceName"] for c in table.get("columns", []) if c.get("sourceName"))
    return cols[:300]


def _assign_roles(item: dict, columns: list[str], rank: int) -> list[str]:
    roles: list[str] = []
    text = f"{item.get('title', '')} {item.get('theme', {}).get('top', '') or ''}"
    if rank < 2:
        roles.append("PRIMARY")
    if _DEMAND_PAT.search(text):
        roles.append("DEMAND")
    if _SUPPLY_PAT.search(text):
        roles.append("SUPPLY")
    if item.get("listType") == "STD" or _REFERENCE_PAT.search(text):
        roles.append("REFERENCE")
    col_text = " ".join(columns)
    if columns and _SPATIAL_COL.search(col_text):
        roles.append("SPATIAL")
    if columns and _TEMPORAL_COL.search(col_text):
        roles.append("TEMPORAL")
    if not roles:
        roles.append("RELATED")  # 역할 규칙에 걸리지 않은 관련 후보 — 역할 판단은 호스트·사용자 몫
    return roles


def _fit_signals(item: dict, columns: list[str], rank: int) -> dict:
    c = item.get("completeness") or {}
    return {
        "searchRelevance": "HIGH" if rank < 3 else "MEDIUM" if rank < 6 else "LOW",
        "structureEvidence": "FILE_OBSERVATION" if columns else (
            "STRUCTURE_NOT_COLLECTED" if item.get("listType") == "FILE" else "NOT_APPLICABLE"),
        "freshness": "LISTED" if item.get("modifiedDate") else "UNKNOWN",
        "metadataCompleteness": "TYPICAL" if c.get("typical") else (
            f"TOP_{c.get('topPercent')}" if c.get("topPercent") is not None else "UNKNOWN"),
    }


def _why_selected(item: dict, columns: list[str], terms: list[str], rank: int) -> list[str]:
    why = [f"검색 관련도 {rank + 1}위 (bm25)"]
    title = item.get("title", "")
    hit = [t for t in terms if t in title]
    if hit:
        why.append(f"제목에 '{'·'.join(hit[:3])}' 일치")
    if columns:
        why.append(f"실파일 구조 관측됨 (컬럼 {len(columns)}개)")
        spatial = sorted({c for c in columns if _SPATIAL_COL.search(c)})[:4]
        if spatial:
            why.append(f"위치 관련 컬럼 관측: {', '.join(spatial)}")
    kf = (item.get("completeness") or {}).get("keyFields") or {}
    if kf.get("spatial"):
        why.append("목록에 공간범위 기재")
    return why


def _limitations(columns: list[str], item: dict) -> list[str]:
    lims = ["품질은 평가되지 않음(NOT_ASSESSED) — 값 수준 검증은 원문에서 수행"]
    if columns:
        lims.append("구조 관측은 수집 표본 기준 — 최신 원문과 다를 수 있음")
    elif item.get("listType") == "FILE":
        lims.append("실파일 구조 미관측(STRUCTURE_NOT_COLLECTED) — 컬럼 부재가 아니라 미수집")
    else:
        lims.append("API 유형 구조는 차기 지원 — 오퍼레이션·필드는 원문에서 확인")
    return lims


def _join_keys(cand_columns: dict[str, list[str]]) -> list[dict]:
    """후보들의 관측 컬럼에서 결합 키 후보를 찾는다 — 항상 CANDIDATE_ONLY."""
    keys = []
    for label, pat in _JOIN_PATTERNS:
        observed_in = []
        for rid, cols in cand_columns.items():
            if pat is None:  # 좌표 쌍
                if any("위도" in c for c in cols) and any("경도" in c for c in cols):
                    observed_in.append(rid)
            elif any(pat.search(c) for c in cols):
                observed_in.append(rid)
        if len(observed_in) >= 2:
            keys.append({
                "key": label,
                "status": "CANDIDATE_ONLY",
                "observedIn": observed_in,
                "warning": "값 체계·기준 시점의 일치 여부는 검증되지 않았습니다",
            })
    return keys


def build_plan(svc, purpose: str, region: str | None = None,
               max_candidates: int = 5) -> dict:
    purpose = (purpose or "").strip()
    if not 2 <= len(purpose) <= 200:
        raise InvalidArgument("purpose는 2~200자의 목적 문장이어야 합니다", {"length": len(purpose)})
    max_candidates = max(1, min(int(max_candidates), _MAX_CANDIDATES))

    terms, region_from_text = _extract_terms(purpose)
    region_code = _resolve_region(region) or region_from_text
    query = " ".join(terms) if terms else purpose

    # 검색(내부 반복 최대 2회): ① 검색어+지역 → ② 0건이면 지역 해제
    iterations = 1
    search = svc.search_datasets(query=query, region=region_code, page_size=max_candidates * 2)
    if not search["data"]["items"] and region_code:
        iterations = 2
        search = svc.search_datasets(query=query, page_size=max_candidates * 2)
    items = search["data"]["items"][:max_candidates]
    search_warnings = [w for w in search.get("warnings", []) if not w.startswith("본 결과는")]

    cand_columns: dict[str, list[str]] = {}
    recommended = []
    for rank, item in enumerate(items):
        cols = _observed_columns(svc, item)
        cand_columns[item["recordId"]] = cols
        roles = _assign_roles(item, cols, rank)
        recommended.append({
            "recordId": item["recordId"],
            "title": item.get("title"),
            "orgName": item.get("orgName"),
            "listType": item.get("listType"),
            "portalUrl": item.get("portalUrl"),
            "candidateStatus": "CANDIDATE_DATASET",
            "roles": roles,
            "fitSignals": _fit_signals(item, cols, rank),
            "whySelected": _why_selected(item, cols, terms, rank),
            "limitations": _limitations(cols, item),
        })

    # 데이터 요구(제한 템플릿) — 실패가 아니라 요구 미충족으로 보고한다
    def need(role: str, text: str, satisfied_by: list[str], partial: bool = False) -> dict:
        if satisfied_by:
            return {"role": role, "need": text,
                    "status": "PARTIAL" if partial else "SATISFIED", "matchedRecordIds": satisfied_by}
        return {"role": role, "need": text, "status": "UNSATISFIED",
                "reason": "현재 카탈로그 검색에서 확인되지 않음"}

    by_role: dict[str, list[str]] = {}
    for r in recommended:
        for role in r["roles"]:
            by_role.setdefault(role, []).append(r["recordId"])
    spatial_listed = [r["recordId"] for i, r in enumerate(recommended)
                      if ((items[i].get("completeness") or {}).get("keyFields") or {}).get("spatial")]
    temporal_listed = [r["recordId"] for i, r in enumerate(recommended) if items[i].get("modifiedDate")]

    data_needs = [
        need("PRIMARY", f"목적 대상 데이터({' '.join(terms[:3]) or purpose[:30]})", by_role.get("PRIMARY", [])),
        need("SPATIAL", "위치(좌표·주소) 또는 행정구역 연결 정보",
             by_role.get("SPATIAL") or spatial_listed, partial="SPATIAL" not in by_role),
        need("TEMPORAL", "기준 시점·갱신 주기 정보",
             by_role.get("TEMPORAL") or temporal_listed, partial="TEMPORAL" not in by_role),
    ]
    if _ANALYSIS_HINT.search(purpose):
        data_needs.append(need("DEMAND", "수요·인구·이용량 데이터", by_role.get("DEMAND", [])))
        data_needs.append(need("SUPPLY", "시설·서비스 공급 현황 데이터", by_role.get("SUPPLY", [])))
    if by_role.get("REFERENCE"):
        data_needs.append(need("REFERENCE", "코드·분류 기준정보", by_role["REFERENCE"]))

    missing = [n for n in data_needs if n["status"] == "UNSATISFIED"]
    join_keys = _join_keys(cand_columns)

    next_checks = [
        "포털 원문에서 각 후보의 기준 시점·갱신 상태 확인",
        "예상 결합 키의 코드 체계·값 형식 비교(서버는 검증하지 않음)",
        "결측률·좌표 유효성 등 값 수준 품질 확인(NOT_ASSESSED)",
    ]
    if not join_keys and len(recommended) >= 2:
        next_checks.insert(1, "후보 간 공통 결합 항목을 원문 컬럼 정의에서 직접 확인(관측 근거 부족)")
    if missing:
        next_checks.append("미충족 요구는 검색어를 바꿔 재검색하거나 원천 기관에 확인")

    data = {
        "purpose": purpose,
        "planStatus": "DRAFT",
        "interpretedPurpose": {
            "searchTerms": terms,
            "regionApplied": region_code,
            "regionSource": ("PARAMETER" if region else "PURPOSE_TEXT") if region_code else None,
            "iterationsUsed": iterations,
        },
        "dataNeeds": data_needs,
        "recommendedDatasets": recommended,
        "possibleJoinKeys": join_keys,
        "missingNeeds": missing,
        "qualityAssessment": "NOT_ASSESSED",
        "nextChecks": next_checks,
    }
    warnings = [
        "이 계획은 목록 메타데이터와 관측 구조에 기반한 초안(DRAFT)입니다 — "
        "품질·결합 가능성·분석 충분성을 확정하지 않습니다. 검증·반복 설계는 별도 컨시어지에서 제공됩니다.",
        *search_warnings,
    ]
    rules = [RULE_PLAN, *search["meta"]["ruleVersions"]]
    return envelope(data, svc.snapshot, rules, warnings)
