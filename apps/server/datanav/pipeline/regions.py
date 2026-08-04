"""지역 매칭(rule: region-match-v1.0) — 근거 수준·신뢰도 동반(§4.4)."""
from __future__ import annotations

# 시·도 17개 (ISO 3166-2:KR). aliases: (별칭, 동음이의 여부)
SIDO = [
    ("KR-11", "서울특별시", ["서울특별시", "서울시", "서울"], []),
    ("KR-26", "부산광역시", ["부산광역시", "부산시", "부산"], []),
    ("KR-27", "대구광역시", ["대구광역시", "대구시", "대구"], []),
    ("KR-28", "인천광역시", ["인천광역시", "인천시", "인천"], []),
    ("KR-29", "광주광역시", ["광주광역시"], ["광주시", "광주"]),  # 경기 광주시와 동음이의
    ("KR-30", "대전광역시", ["대전광역시", "대전시", "대전"], []),
    ("KR-31", "울산광역시", ["울산광역시", "울산시", "울산"], []),
    ("KR-50", "세종특별자치시", ["세종특별자치시", "세종시", "세종"], []),
    ("KR-41", "경기도", ["경기도", "경기"], []),
    ("KR-42", "강원특별자치도", ["강원특별자치도", "강원도", "강원"], []),
    ("KR-43", "충청북도", ["충청북도", "충북"], []),
    ("KR-44", "충청남도", ["충청남도", "충남"], []),
    ("KR-45", "전북특별자치도", ["전북특별자치도", "전라북도", "전북"], []),
    ("KR-46", "전라남도", ["전라남도", "전남"], []),
    ("KR-47", "경상북도", ["경상북도", "경북"], []),
    ("KR-48", "경상남도", ["경상남도", "경남"], []),
    ("KR-49", "제주특별자치도", ["제주특별자치도", "제주도", "제주"], []),
]

EVIDENCE_CONFIDENCE = {
    "EXPLICIT_SPATIAL": 0.95,
    "INFERRED_FROM_TITLE": 0.8,
    "INFERRED_FROM_PUBLISHER": 0.6,
    "INFERRED_FROM_DESCRIPTION": 0.5,
}
AMBIGUOUS_PENALTY = 0.3


def _match_text(text: str) -> list[tuple[str, str, bool]]:
    """텍스트에서 (code, name, ambiguous) 매칭 목록."""
    out = []
    if not text:
        return out
    for code, name, aliases, ambiguous_aliases in SIDO:
        hit = amb = False
        for a in aliases:
            if a in text:
                hit = True
                break
        if not hit:
            for a in ambiguous_aliases:
                if a in text:
                    hit = amb = True
                    break
        if hit:
            out.append((code, name, amb))
    return out


def match_regions(spatial: str, title: str, org_name: str, description: str) -> list[dict]:
    """근거 수준이 높은 순으로 지역 매칭. 같은 지역은 최고 근거만 유지."""
    found: dict[str, dict] = {}
    sources = [
        ("EXPLICIT_SPATIAL", spatial),
        ("INFERRED_FROM_TITLE", title),
        ("INFERRED_FROM_PUBLISHER", org_name),
        ("INFERRED_FROM_DESCRIPTION", description),
    ]
    for evidence, text in sources:
        if text and text.strip() in ("", "-"):
            continue
        for code, name, amb in _match_text(text or ""):
            if code in found:
                continue
            conf = EVIDENCE_CONFIDENCE[evidence]
            if amb:
                conf = round(conf - AMBIGUOUS_PENALTY, 2)
            found[code] = {
                "code": code,
                "name": name,
                "evidence": evidence,
                "confidence": conf,
            }
    return list(found.values())
