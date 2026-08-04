"""JSON-LD 매핑 — dcat:Catalog / dcat:Dataset(Discovery 계층 1) / dcat:CatalogRecord (§3.1, §7)."""
from __future__ import annotations

import json

from ..config import BASE_URI

CONTEXT_URI = f"{BASE_URI}/context/catalog/1.0"

# JSON-LD Context (정본은 HTTP Resource로도 공개)
JSONLD_CONTEXT = {
    "@version": 1.1,
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dqv": "http://www.w3.org/ns/dqv#",
    "oa": "http://www.w3.org/ns/oa#",
    "prov": "http://www.w3.org/ns/prov#",
    "aird": f"{BASE_URI}/ns/aird#",
    "kdp": f"{BASE_URI}/ns/kdp#",
    # DCAT-AP-KR(HIKE Lab) — 한국 포털 기술 메타데이터 확장(어휘 매핑 확장 제안 v1.1)
    "dcatkr": "http://vocab.datahub.kr/def/dcat-ap-kr/",
    "koor": "http://vocab.datahub.kr/def/organization/",
    "schema": "http://schema.org/",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "title": "dct:title",
    "description": "dct:description",
    "identifier": "dct:identifier",
    "issued": {"@id": "dct:issued", "@type": "xsd:date"},
    "modified": {"@id": "dct:modified", "@type": "xsd:date"},
    "keyword": "dcat:keyword",
    "theme": "dcat:theme",
    "landingPage": {"@id": "dcat:landingPage", "@type": "@id"},
    "publisher": "dct:publisher",
    "accrualPeriodicity": "dct:accrualPeriodicity",
    "license": "dct:license",
    "spatial": "dct:spatial",
    "temporal": "dct:temporal",
    "dataset": "dcat:dataset",
    "record": "dcat:record",
}


def dataset_uri(list_key: str) -> str:
    """정본 Dataset URI — 항상 목록키 기반 불변(§7, rule: record-identity-v1.0)."""
    return f"{BASE_URI}/dataset/{list_key}"


def catalog_uri(snapshot: str) -> str:
    return f"{BASE_URI}/catalog/{snapshot}"


def record_uri(snapshot: str, record_id: str) -> str:
    return f"{BASE_URI}/catalog/{snapshot}/record/{record_id}"


# update_cycle 코드 → EU 발행처 Frequency 권위 URI (원문 대체가 아닌 병기 — 제안 v1.1 §2)
_FREQUENCY_URI = {
    "DAILY": "http://publications.europa.eu/resource/authority/frequency/DAILY",
    "WEEKLY": "http://publications.europa.eu/resource/authority/frequency/WEEKLY",
    "MONTHLY": "http://publications.europa.eu/resource/authority/frequency/MONTHLY",
    "QUARTERLY": "http://publications.europa.eu/resource/authority/frequency/QUARTERLY",
    "SEMIANNUAL": "http://publications.europa.eu/resource/authority/frequency/ANNUAL_2",
    "ANNUAL": "http://publications.europa.eu/resource/authority/frequency/ANNUAL",
    "IRREGULAR": "http://publications.europa.eu/resource/authority/frequency/IRREG",
}


def _dcatkr_extension(rec: dict) -> dict:
    """DCAT-AP-KR 확장(어휘 매핑 확장 제안 v1.1) — 미매핑 항목의 무손실 기술.

    현행 dcatkr 정의 항목 + 신설 확정 용어(notes·provisionType·mediaType·reviewType·
    isNationalCore·isStandardData·apiType·requestLimitNote — 발행 주체 승인, 어휘 문서
    차기 업데이트 예정)를 모두 dcatkr로 기술한다. kdp는 판정·정규화 코드 계층에만 남는다.
    dept_phone(D1)·DCMI 병기(D3)는 결정 보류로 이번 범위 제외.
    """
    ext: dict = {
        "dcatkr:numberOfRow": rec["row_count"],
        "dcatkr:numberOfView": rec["view_count"],
        "dcatkr:legalBasis": rec["retention_basis"],
        "dcatkr:nextRegistrationDate": rec["next_registration_date"],
        "dcatkr:derivedSystem": rec["collection_method"],
        "dcatkr:mediaType": rec["media_type"],
        "dcatkr:provisionType": rec["provision_type"],
        "dcatkr:notes": rec["notes"],
        "dcatkr:reviewType": rec["review_type"],
        "dcatkr:isNationalCore": bool(rec["is_national_core"]),
        "dcatkr:isStandardData": bool(rec["is_standard"]),
    }
    if rec["dept_name"]:
        ext["dcatkr:maintainer"] = {"@type": "foaf:Agent", "foaf:name": rec["dept_name"]}
    # 비용: dcatkr:fee(boolean, true=부과) — UNSPECIFIED는 생략해 3치 손실 방지(kdp 코드 병기)
    if rec["fee"] in ("FREE", "PAID"):
        ext["dcatkr:fee"] = rec["fee"] == "PAID"
    ext["kdp:feeCode"] = rec["fee"]
    if rec["fee_basis"]:
        ext["schema:offer"] = {"@type": "schema:Offer", "schema:description": rec["fee_basis"]}
    # 데이터 한계(기관 자기기재) — DQV 품질 주석(이슈 관찰과 동일 어휘 체계)
    if rec["data_limits"]:
        ext["dqv:hasQualityAnnotation"] = {
            "@type": "dqv:QualityAnnotation",
            "oa:bodyValue": rec["data_limits"],
            "kdp:assertedBy": "provider",
        }

    if rec["list_type"] == "FILE" and (rec["file_data_name"] or rec["formats"]):
        dist = {
            "@type": "dcat:Distribution",
            "dct:title": rec["file_data_name"],
            "dct:format": rec["formats"] or None,
            "dcatkr:numberOfDownload": rec["download_count"],
        }
        if rec["list_url"]:
            dist["dcat:accessURL"] = {"@id": rec["list_url"]}
        ext["dcat:distribution"] = {k: v for k, v in dist.items() if v is not None}
    elif rec["list_type"] == "API":
        # 다운로드수 열은 API에서 활용신청 수를 담는다(포털 관행) — dcatkr가 도메인을 구분
        ext["dcatkr:numberOfRequest"] = rec["download_count"]
        ext["dcatkr:apiType"] = rec["api_type"]  # 통제어휘 URI 병기는 어휘 문서 갱신 후
        if rec["traffic"]:
            try:
                ext["dcatkr:numberOfRequestLimit"] = int(str(rec["traffic"]).strip())
            except ValueError:
                ext["dcatkr:requestLimitNote"] = rec["traffic"]  # 서술형 원문 보존
    return {k: v for k, v in ext.items() if v is not None}


def dataset_jsonld(rec: dict, snapshot: str) -> dict:
    """개별 공공데이터의 Discovery Profile. Q-Tier·DM 부여 금지(§3.1) — null 고정."""
    doc = {
        "@context": CONTEXT_URI,
        "@id": dataset_uri(rec["list_key"]),
        "@type": "dcat:Dataset",
        "identifier": rec["list_key"],
        "dct:language": "ko",
        "title": rec["title"],
        "description": rec["description"],
        "keyword": rec["keywords"] or None,
        "theme": rec["theme_raw"],
        "issued": rec["created_date"],
        "modified": rec["modified_date"],
        "landingPage": rec["list_url"],
        "publisher": {
            "@type": "foaf:Agent",
            "foaf:name": rec["org_name"],
            "kdp:orgCode": rec["org_code"],
        },
        # 원문 리터럴 + Frequency 권위 URI 병기(코드 매핑 시)
        "accrualPeriodicity": (
            [rec["update_cycle_raw"], {"@id": _FREQUENCY_URI[rec["update_cycle"]]}]
            if rec["update_cycle"] in _FREQUENCY_URI and rec["update_cycle_raw"]
            else rec["update_cycle_raw"]
        ),
        "license": rec["license_raw"],
        "spatial": rec["spatial_raw"],
        "temporal": rec["temporal_raw"],
        "kdp:listType": rec["list_type"],
        "kdp:listKey": rec["list_key"],
        "kdp:recordId": rec["record_id"],
        "kdp:evidenceLevel": "CATALOG_METADATA_ONLY",
        "kdp:qualityTier": None,
        "kdp:diagnosticMaturity": None,
        "kdp:catalogMetadataCompleteness": {
            "kdp:score": rec["completeness_score"],
            "kdp:profile": rec["completeness_profile"],
            "kdp:rule": rec["completeness_rule"],
        },
        "kdp:sourceSnapshot": snapshot,
        "kdp:catalogRecord": record_uri(snapshot, rec["record_id"]),
    }
    doc.update(_dcatkr_extension(rec))
    if rec["list_type"] == "API":
        doc["@type"] = ["dcat:Dataset", "dcat:DataService"]  # DCAT-AP-KR: API는 DataService 병기
    # Q-Tier·DM 부여 금지는 명시적 null로 표현한다(§3.1) — 그 외 미기재 필드만 제거
    keep_null = {"kdp:qualityTier", "kdp:diagnosticMaturity"}
    return {k: v for k, v in doc.items() if v is not None or k in keep_null}


def catalog_record_jsonld(rec: dict, snapshot: str) -> dict:
    """dcat:CatalogRecord — 데이터셋 정체성과 시점 기술의 분리(§3.1)."""
    return {
        "@context": CONTEXT_URI,
        "@id": record_uri(snapshot, rec["record_id"]),
        "@type": "dcat:CatalogRecord",
        "foaf:primaryTopic": {"@id": dataset_uri(rec["list_key"])},
        "modified": rec["modified_date"],
        "kdp:listType": rec["list_type"],
        "kdp:sourceSnapshot": snapshot,
        "kdp:sourceRowNo": rec["source_row_no"],
    }


def catalog_jsonld(
    snapshot: str, dataset_count: int, assessment: dict, discoverability: dict, processed_at: str
) -> dict:
    """월별 카탈로그 전체(1건의 STRUCT 데이터셋) — Discovery JSON-LD + AIRD 진단 레코드 참조."""
    doc = {
        "@context": CONTEXT_URI,
        "@id": catalog_uri(snapshot),
        "@type": "dcat:Catalog",
        "title": f"공공데이터포털 목록개방현황 카탈로그 {snapshot}",
        "description": "공공데이터포털 목록개방현황(월간)을 정규화한 월별 카탈로그. 각 목록 행은 개별 공공데이터의 Discovery Profile로 제공된다.",
        "dct:language": "ko",
        # dct:issued는 컨텍스트상 xsd:date — 날짜부만 기록하고 전체 시각은 별도 키(J2)
        "issued": processed_at[:10],
        "kdp:processedAt": processed_at,
        "kdp:datasetCount": dataset_count,
        "kdp:evidenceLevel": "CATALOG_METADATA_ONLY",
        "kdp:airdAssessment": {"@id": assessment["@id"]},
        # 중첩 키가 RDF에서 소실되지 않도록 프리픽스 부여, 상세는 JSON 리터럴(J3)
        "kdp:catalogDiscoverability": {
            "kdp:rule": discoverability["rule"],
            "kdp:catalogMetadataReadinessScore": discoverability["catalogMetadataReadinessScore"],
            "kdp:indicatorsJson": json.dumps(discoverability["indicators"], ensure_ascii=False),
        },
    }
    # DM-0은 판정 조건 충족 시에만 기록(§9). Discoverable에서 qualityTier는 금지(제3부 5.3절).
    if assessment.get("aird:diagnosticMaturity"):
        doc["aird:diagnosticMaturity"] = assessment["aird:diagnosticMaturity"]
        doc["aird:qualityIndexMMI"] = assessment["aird:qualityIndexMMI"]
        doc["aird:dataType"] = assessment["aird:dataType"]
        doc["kdp:airdState"] = "Discoverable"
    return doc


def issue_annotation_jsonld(issue: dict, snapshot: str, dataset_list_key: str | None) -> dict:
    """이슈 관찰의 DQV·PROV 표현(§6) — 원본 불변, 별도 관찰 객체."""
    target: dict = {"kdp:field": issue["field"]}
    if dataset_list_key:
        target["@id"] = dataset_uri(dataset_list_key)
    else:
        target["@id"] = catalog_uri(snapshot)  # 카탈로그 수준 관찰(계통적 패턴)
    return {
        "@id": f"{catalog_uri(snapshot)}/annotation/{issue['issue_id']}",
        "@type": "dqv:QualityAnnotation",
        "oa:hasTarget": target,
        "oa:hasBody": {
            "kdp:issueType": issue["issue_type"],
            "kdp:sourceValue": issue["source_value"],
            "kdp:confidence": issue["confidence"],
        },
        "oa:motivatedBy": "dqv:qualityAssessment",
        "prov:wasGeneratedBy": {
            "@type": "prov:Activity",
            "kdp:detectionRule": issue["detection_rule"],
            "prov:endedAtTime": issue["detected_at"],
        },
        "kdp:reviewStatus": issue["review_status"],
        "kdp:resolutionStatus": issue["resolution_status"],
        "kdp:sourceSnapshot": snapshot,
    }
