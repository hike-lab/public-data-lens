"""AIRD 자가 진단 — 월별 카탈로그(1건의 STRUCT 데이터셋)에 대한 표준 MMI 측정과 DM-0 판정.

근거: AIRD 제2부 v0.87 — §3.13(MMI 4지표), 표 5.3(DM-0 조건), 6.1절 7항(적재 사전 검사),
§7.5(QI_MMI 산출), 표 8.4(참고 공시 표기), 표 9.1(유형별 적용표), 제3부 §5.3(aird: 필드).

- MMI = D5-03(통계적 타당성) · D6-01(유일성) · D7-01(인코딩 일관성) · D7-02(기술적 유효성)
- STRUCT 적용 가능 집합 = 4개 전부(D7-02는 선택(○)이나 적용 가능 — 표 9.1, 해석은 규칙 정의에 기록)
- QI_MMI = 적용 가능 지표 점수 합 / 적용 가능 지표 수, ≥ 0.7이면 DM-0(기본 적합성)
- DM-0은 참고 공시("DM-0 (기본 적합성, STRUCT, 참고)") — 공식 Q-Tier 공시는 DM-2 이상
- 별도 참고: 카탈로그 발견성 8지표(catalog-discoverability-v1.0)는 MMI가 아니며 DM 판정에 쓰지 않는다.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3

from ..config import BASE_URI
from ..rules import RULE_AIRD, RULE_DISCOVERABILITY
from .jsonld import CONTEXT_URI

QI_MMI_THRESHOLD = 0.7  # 면제 불가 게이트(제2부 §8.1, AIRD-OPG-001 §15.3)

# D5-03 더미값 패턴(제2부 6.6절). '0000' 등 문자열 패턴은 정수 정규화 과정에서
# 판별 불가하므로 제외하고 details에 기록한다.
DUMMY_VALUES = {999999, 99999999, 9999, -1, -9}

# 카탈로그 데이터셋의 수치 컬럼(원본: 전체행 / 다운로드_활용신청건수 / 조회수)
NUMERIC_COLUMNS = ["row_count", "download_count", "view_count"]

_URL_RE = re.compile(r"^https?://\S+$")

AIRD_STANDARD_REF = "AIRD-Part-2-Quality-v0.87"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def measure_mmi(
    conn: sqlite3.Connection,
    snapshot: str,
    source_sha256: str | None = None,
    parse_failures: int = 0,
    encoding_ok: bool = True,
) -> dict:
    """표준 MMI 4지표를 측정하고 DM-0을 판정한 진단 레코드(JSON-LD 호환 dict)를 반환한다."""
    record_count = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]

    # 6.1절 7항 — 데이터 적재 사전 검사
    if record_count == 0:
        return {
            "@context": CONTEXT_URI,
            "@id": f"{BASE_URI}/catalog/{snapshot}/aird-assessment",
            "@type": "kdp:AirdAssessment",
            "aird:dataType": "STRUCT",
            "kdp:diagnosticStatus": "SCHEMA_ONLY",
            "kdp:recordCount": 0,
            "aird:qualityIndexMMI": None,
            "aird:diagnosticMaturity": None,
            "kdp:rule": RULE_AIRD,
            "kdp:standardRef": AIRD_STANDARD_REF,
        }

    indicators = []

    # ---- D5-03 통계적 타당성: 수치 셀 중 더미값 비율 --------------------
    dummy_cells = 0
    measured_cells = 0
    per_column: dict[str, dict] = {}
    for col in NUMERIC_COLUMNS:
        total = conn.execute(
            f"SELECT COUNT(*) FROM datasets WHERE {col} IS NOT NULL"
        ).fetchone()[0]
        placeholders = ",".join("?" * len(DUMMY_VALUES))
        dummies = conn.execute(
            f"SELECT COUNT(*) FROM datasets WHERE {col} IN ({placeholders})",
            list(DUMMY_VALUES),
        ).fetchone()[0]
        measured_cells += total
        dummy_cells += dummies
        per_column[col] = {
            "cells": total,
            "dummyCells": dummies,
            "dummyValueRate": round(dummies / total, 6) if total else None,
        }
    d5_03 = round(1 - (dummy_cells / measured_cells), 4) if measured_cells else 1.0
    indicators.append({
        "kdp:indicatorId": "D5-03",
        "kdp:indicatorName": "통계적 타당성",
        "kdp:score": d5_03,
        "kdp:status": "APPLIED",
        "kdp:detailsJson": json.dumps({
            "dummyValuePatterns": sorted(DUMMY_VALUES),
            "dummyValueRate": per_column,
            "note": "문자열형 더미 패턴('0000' 등)은 정수 정규화로 판별 불가하여 제외",
        }, ensure_ascii=False),
    })

    # ---- D6-01 유일성: 식별 컬럼(목록키) 기준 ---------------------------
    unique_keys = conn.execute("SELECT COUNT(DISTINCT list_key) FROM datasets").fetchone()[0]
    d6_01 = round(unique_keys / record_count, 4)
    indicators.append({
        "kdp:indicatorId": "D6-01",
        "kdp:indicatorName": "유일성",
        "kdp:score": d6_01,
        "kdp:status": "APPLIED",
        "kdp:detailsJson": json.dumps({
            "identifierColumn": "목록키",
            "identifierUniqueness": {"uniqueKeys": unique_keys, "records": record_count},
        }, ensure_ascii=False),
    })

    # ---- D7-01 인코딩 일관성: 단일 파일, 기준 UTF-8 ---------------------
    d7_01 = 1.0 if encoding_ok else 0.0
    indicators.append({
        "kdp:indicatorId": "D7-01",
        "kdp:indicatorName": "인코딩 일관성",
        "kdp:score": d7_01,
        "kdp:status": "APPLIED",
        "kdp:detailsJson": json.dumps(
            {"files": 1, "baselineEncoding": "UTF-8", "note": "BOM 유무는 측정 대상 아님"},
            ensure_ascii=False),
    })

    # ---- D7-02 기술적 유효성: STRUCT = 파일 파싱 가능 여부 ---------------
    d7_02 = 1.0 if parse_failures == 0 else round(1 - parse_failures / record_count, 4)
    indicators.append({
        "kdp:indicatorId": "D7-02",
        "kdp:indicatorName": "기술적 유효성",
        "kdp:score": d7_02,
        "kdp:status": "APPLIED",
        "kdp:detailsJson": json.dumps(
            {"files": 1, "parseFailures": parse_failures,
             "applicability": "STRUCT에서 선택(○)이나 적용 가능 집합에 포함(표 9.1)"},
            ensure_ascii=False),
    })

    qi_mmi = round(sum(i["kdp:score"] for i in indicators) / len(indicators), 4)
    passed = qi_mmi >= QI_MMI_THRESHOLD
    return {
        "@context": CONTEXT_URI,
        "@id": f"{BASE_URI}/catalog/{snapshot}/aird-assessment",
        "@type": "kdp:AirdAssessment",
        "aird:dataType": "STRUCT",
        "kdp:diagnosticStatus": "POPULATED",
        "kdp:recordCount": record_count,
        "kdp:indicators": indicators,
        "kdp:applicableMmiCount": len(indicators),
        "aird:qualityIndexMMI": qi_mmi,
        "kdp:threshold": QI_MMI_THRESHOLD,
        "aird:diagnosticMaturity": "DM-0" if passed else None,
        "kdp:label": "DM-0 (기본 적합성, STRUCT, 참고)" if passed else None,
        "kdp:disclosure": "참고 공시 — DM-0·DM-1은 내부 진단 참고용이며 공식 적합성 선언에 사용하지 않는다(제2부 5.4절)",
        "prov:wasGeneratedBy": {
            "@type": "prov:Activity",
            "prov:endedAtTime": _now(),
            "kdp:sourceSnapshot": snapshot,
            "kdp:sourceSha256": source_sha256,
            "kdp:tool": "datanav/0.1.0",
            "kdp:rule": RULE_AIRD,
            "kdp:standardRef": AIRD_STANDARD_REF,
        },
        "kdp:note": (
            "월별 카탈로그 전체를 1건의 STRUCT 데이터셋으로 보고 측정. "
            "개별 목록 행에는 Q-Tier·DM을 부여하지 않는다(evidenceLevel=CATALOG_METADATA_ONLY). "
            "aird:qualityTier는 Discoverable 상태에서 금지되므로 기록하지 않는다(제3부 5.3절)."
        ),
    }


def measure_discoverability(conn: sqlite3.Connection) -> dict:
    """카탈로그 발견성 8지표(참고) — MMI가 아니며 DM 판정에 사용하지 않는다."""
    total = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    if total == 0:
        raise ValueError("빈 카탈로그에는 발견성 지표를 측정하지 않는다")

    def ratio(where: str) -> float:
        n = conn.execute(f"SELECT COUNT(*) FROM datasets WHERE {where}").fetchone()[0]
        return round(n / total, 4)

    urls = conn.execute("SELECT list_url FROM datasets WHERE list_url IS NOT NULL").fetchall()
    url_valid_n = sum(1 for (u,) in urls if _URL_RE.match(u))

    indicators = {
        "identifierPresence": ratio("list_key IS NOT NULL AND list_key != ''"),
        "titlePresence": ratio("title IS NOT NULL AND title != ''"),
        "descriptionPresence": ratio("description IS NOT NULL"),
        "publisherPresence": ratio("org_name IS NOT NULL"),
        "licensePresence": ratio("license_code NOT IN ('UNSPECIFIED')"),
        "keywordPresence": ratio("keywords != '[]'"),
        "datePresence": ratio("modified_date IS NOT NULL AND created_date IS NOT NULL"),
        "urlFormatValidity": round(url_valid_n / total, 4),
    }
    score = round(sum(indicators.values()) / len(indicators), 4)
    return {
        "rule": RULE_DISCOVERABILITY,
        "indicators": indicators,
        "catalogMetadataReadinessScore": score,
        "note": "목록 메타데이터 충실도 참고 지표 — AIRD MMI가 아니며 DM 판정에 사용하지 않는다.",
    }
