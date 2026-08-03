"""부속 명세 — Tool별 출력 JSON Schema 정의(공개 계약 v1.0.0 — 동결).

입력 스키마는 MCP 서버(FastMCP)가 생성하는 것을 단일 출처로 추출하고(스크립트),
출력 스키마는 본 모듈이 단일 출처다. 계약-코드 정합은 tests/test_contract_spec.py가 보증한다.

호환성 원칙(동결): 필드 추가는 하위 호환(minor), required 필드 제거·의미 변경은 breaking(major).
schemaVersion은 응답 봉투 meta.schemaVersion으로 전달된다.
"""
from __future__ import annotations

SPEC_VERSION = "1.3.0"

# ---------------------------------------------------------------- $defs
DEFS = {
    "meta": {
        "type": "object",
        "required": ["sourceSnapshot", "processedAt", "schemaVersion", "ruleVersions"],
        "properties": {
            "sourceSnapshot": {"type": "string", "description": "판정 근거 스냅샷(YYYY-MM)"},
            "processedAt": {"type": "string", "format": "date-time"},
            "schemaVersion": {"type": "string"},
            "ruleVersions": {"type": "array", "items": {"type": "string"}},
        },
    },
    "warnings": {
        "type": "array",
        "items": {"type": "string"},
        "description": "면책 고지 1건 이상 항상 포함(§10)",
        "minItems": 1,
    },
    "error": {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["code", "message", "details", "sourceSnapshot"],
                "properties": {
                    "code": {
                        "enum": [
                            "INVALID_ARGUMENT", "DATASET_NOT_FOUND", "SNAPSHOT_NOT_FOUND",
                            "FILTER_NOT_AVAILABLE", "TOO_MANY_DATASETS", "INDEX_NOT_READY",
                            "SOURCE_VERSION_UNAVAILABLE", "RATE_LIMITED", "INTERNAL_ERROR",
                        ]
                    },
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                    "sourceSnapshot": {"type": ["string", "null"]},
                },
            }
        },
    },
    "completeness": {
        "type": "object",
        "required": ["score", "profile", "rule"],
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "profile": {"enum": ["FILE", "API", "STD"]},
            "rule": {"type": "string"},
            "filledFields": {"type": "integer", "minimum": 0},
            "totalFields": {"type": "integer", "minimum": 1},
            "keyFields": {
                "type": "object",
                "description": "판단 직결 3필드(공간·시간범위, 이용제한)의 기재 여부 — v1.1.0 추가",
                "required": ["spatial", "temporal", "dataLimits"],
                "properties": {
                    "spatial": {"type": "boolean"},
                    "temporal": {"type": "boolean"},
                    "dataLimits": {"type": "boolean"},
                },
            },
            "topPercent": {"type": "number", "description": "유형 내 이 점수보다 높은 비율(%) — 낮을수록 상위. v1.1.0 추가"},
            "typical": {"type": "boolean", "description": "유형 내 최빈 점수와 동일(대다수와 같은 수준). v1.1.0 추가"},
            "typicalShare": {"type": "number", "description": "유형 내 최빈 점수 비중(%). v1.1.0 추가"},
            "fields": {
                "type": "object",
                "description": "card 뷰 전용 — 프로파일 점검 필드별 기재 여부(점수의 분해 근거). v1.1.0 추가",
                "additionalProperties": {"type": "boolean"},
            },
        },
    },
    "region": {
        "type": "object",
        "required": ["code", "name", "evidence", "confidence"],
        "properties": {
            "code": {"type": "string", "pattern": "^KR-\\d{2}$"},
            "name": {"type": "string"},
            "evidence": {
                "enum": ["EXPLICIT_SPATIAL", "INFERRED_FROM_TITLE",
                         "INFERRED_FROM_PUBLISHER", "INFERRED_FROM_DESCRIPTION", "UNKNOWN"]
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    },
    "summaryItem": {
        "type": "object",
        "required": ["recordId", "listKey", "listType", "title", "orgName",
                     "theme", "formats", "updateCycle", "completeness", "regions"],
        "properties": {
            "recordId": {"type": "string"},
            "listKey": {"type": "string"},
            "listType": {"enum": ["FILE", "API", "STD"]},
            "title": {"type": "string"},
            "orgName": {"type": ["string", "null"]},
            "theme": {
                "type": "object",
                "properties": {"top": {"type": ["string", "null"]}, "sub": {"type": ["string", "null"]}},
            },
            "formats": {"type": "array", "items": {"type": "string"}},
            "updateCycle": {"type": "string"},
            "modifiedDate": {"type": ["string", "null"]},
            "completeness": {"$ref": "#/$defs/completeness"},
            "regions": {"type": "array", "items": {"$ref": "#/$defs/region"}},
            "portalUrl": {"type": ["string", "null"]},
            "rowCountListed": {"type": "integer",
                               "description": "목록 메타데이터에 기재된 전체 행수"},
            "structureAvailable": {"type": "boolean", "description": "데이터 구조 관측 존재 여부(get_dataset_structure로 조회). v1.2.0 추가"},
            "score": {"type": "number", "description": "query 있을 때만 — BM25 점수(낮을수록 상위)"},
        },
    },
    "ranking": {
        "type": "object",
        "required": ["method", "version", "indexVersion", "embeddingModel", "tieBreak"],
        "properties": {
            "method": {"type": "string"},
            "version": {"type": "string"},
            "indexVersion": {"type": "string"},
            "embeddingModel": {"type": ["string", "null"]},
            "tieBreak": {"type": "string"},
        },
    },
    "changeItem": {
        "type": "object",
        "required": ["recordId", "listKey", "status", "changedFields", "title", "orgName"],
        "properties": {
            "recordId": {"type": "string"},
            "listKey": {"type": "string"},
            "status": {
                "enum": ["ADDED", "MODIFIED", "MISSING_FROM_SNAPSHOT", "REAPPEARED",
                         "POSSIBLE_IDENTITY_CHANGE", "OFFICIALLY_WITHDRAWN"]
            },
            "changedFields": {"type": ["array", "null"], "items": {"type": "string"}},
            "title": {"type": ["string", "null"]},
            "orgName": {"type": ["string", "null"]},
        },
    },
}


def _envelope(data_schema: dict) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["data", "meta", "warnings"],
        "properties": {
            "data": data_schema,
            "meta": {"$ref": "#/$defs/meta"},
            "warnings": {"$ref": "#/$defs/warnings"},
        },
        "$defs": DEFS,
    }


# ------------------------------------------------------- Tool별 출력 스키마
OUTPUT_SCHEMAS: dict[str, dict] = {
    "search_datasets": _envelope({
        "type": "object",
        "required": ["items", "nextCursor", "hasMore", "totalEstimate", "ranking"],
        "properties": {
            "items": {"type": "array", "items": {"$ref": "#/$defs/summaryItem"}},
            "nextCursor": {"type": ["string", "null"]},
            "hasMore": {"type": "boolean"},
            "totalEstimate": {"type": "integer", "minimum": 0},
            "ranking": {"$ref": "#/$defs/ranking"},
        },
    }),
    "get_dataset": _envelope({
        "type": "object",
        "required": ["view", "dataset"],
        "properties": {
            "view": {"enum": ["card", "normalized", "source", "jsonld"]},
            "dataset": {"type": "object"},
        },
        "allOf": [
            {
                "if": {"properties": {"view": {"const": "card"}}},
                "then": {"properties": {"dataset": {
                    "type": "object",
                    "required": ["recordId", "listKey", "listType", "title", "completeness",
                                 "freshness", "evidenceLevel", "cardRule", "portal"],
                    "properties": {
                        "evidenceLevel": {"const": "CATALOG_METADATA_ONLY"},
                        "cardRule": {"type": "string"},
                        "freshness": {
                            "type": "object",
                            "required": ["status", "rule"],
                            "properties": {"status": {"enum": ["FRESH", "POSSIBLY_STALE", "UNKNOWN"]}},
                        },
                        "portal": {
                            "type": "object",
                            "required": ["listKey", "orgName", "listUrl", "listBaseDate", "analyzedAt"],
                        },
                    },
                }}},
            },
            {
                "if": {"properties": {"view": {"const": "source"}}},
                "then": {"properties": {"dataset": {
                    "type": "object", "required": ["sourceFields", "sourceRowNo"],
                }}},
            },
            {
                "if": {"properties": {"view": {"const": "jsonld"}}},
                "then": {"properties": {"dataset": {
                    "type": "object",
                    "required": ["@context", "@id", "@type", "identifier",
                                 "kdp:recordId", "kdp:evidenceLevel",
                                 "kdp:qualityTier", "kdp:diagnosticMaturity"],
                    "properties": {
                        "@type": {"const": "dcat:Dataset"},
                        "kdp:evidenceLevel": {"const": "CATALOG_METADATA_ONLY"},
                        "kdp:qualityTier": {"type": "null"},
                        "kdp:diagnosticMaturity": {"type": "null"},
                    },
                }}},
            },
        ],
    }),
    "compare_datasets": _envelope({
        "type": "object",
        "required": ["datasets", "differences", "sharedFields", "note"],
        "properties": {
            "datasets": {"type": "array", "minItems": 2, "maxItems": 5,
                         "items": {"$ref": "#/$defs/summaryItem"}},
            "differences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field", "values"],
                    "properties": {"field": {"type": "string"}, "values": {"type": "object"}},
                    "additionalProperties": False,
                },
                "description": "사실 차이만 — 해석 필드는 계약상 존재하지 않는다(§4.1)",
            },
            "sharedFields": {
                "type": "array",
                "items": {"type": "object", "required": ["field", "value"]},
            },
            "note": {"type": "string"},
            "structureComparison": {
                "type": "object",
                "description": "전 대상의 구조가 관측된 경우에만 — 원본 컬럼명 정확 일치 기준 사실 비교(v1.3.0 추가)",
                "required": ["commonColumns", "onlyIn", "columnCounts", "note"],
                "properties": {
                    "commonColumns": {"type": "array", "maxItems": 50, "items": {"type": "string"}},
                    "onlyIn": {"type": "object",
                               "additionalProperties": {"type": "array", "items": {"type": "string"}}},
                    "columnCounts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "note": {"type": "string"},
                },
            },
            "structureComparisonRule": {"type": "string"},
        },
    }),
    "get_catalog_changes": _envelope({
        "type": "object",
        "required": ["baseSnapshot", "currentSnapshot", "items", "nextCursor",
                     "hasMore", "totalEstimate"],
        "properties": {
            "baseSnapshot": {"type": ["string", "null"],
                             "description": "v1.0 범위: 직전 배포 스냅샷과의 diff만 제공. 기간·기준월 조회는 v1.1 백로그"},
            "currentSnapshot": {"type": "string"},
            "items": {"type": "array", "items": {"$ref": "#/$defs/changeItem"}},
            "nextCursor": {"type": ["string", "null"]},
            "hasMore": {"type": "boolean"},
            "totalEstimate": {"type": "integer", "minimum": 0},
        },
    }),
    "get_catalog_stats": _envelope({
        "type": "object",
        "required": ["axis"],
        "properties": {"axis": {"enum": ["theme", "org", "format", "completeness", "listType"]}},
        "oneOf": [
            {
                "required": ["buckets"],
                "properties": {"buckets": {"type": "array", "items": {
                    "type": "object", "required": ["key", "count"],
                    "properties": {"key": {"type": ["string", "null"]},
                                   "count": {"type": "integer"}},
                }}},
            },
            {
                "required": ["profiles"],
                "properties": {"profiles": {"type": "array", "items": {
                    "type": "object",
                    "required": ["profile", "rule", "average", "histogram"],
                    "properties": {
                        "profile": {"enum": ["FILE", "API", "STD"]},
                        "average": {"type": ["number", "null"]},
                        "histogram": {"type": "array", "items": {
                            "type": "object", "required": ["range", "count"],
                        }},
                    },
                }}},
            },
        ],
    }),
    "search_by_columns": _envelope({
        "type": "object",
        "required": ["columnKeywords", "items", "totalEstimate", "hasMore", "coverage"],
        "properties": {
            "columnKeywords": {"type": "array", "items": {"type": "string"}},
            "items": {"type": "array", "items": {
                "allOf": [{"$ref": "#/$defs/summaryItem"}],
                "type": "object",
                "required": ["matchedColumns"],
                "properties": {
                    "matchedColumns": {
                        "type": "array",
                        "description": "검색 근거 — 키워드별로 일치한 원본 컬럼명(최대 5개씩)",
                        "items": {
                            "type": "object",
                            "required": ["keyword", "columns"],
                            "properties": {
                                "keyword": {"type": "string"},
                                "columns": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                },
            }},
            "totalEstimate": {"type": "integer", "minimum": 0},
            "hasMore": {"type": "boolean"},
            "coverage": {
                "type": "object",
                "description": "검색 모집단 명시 — 미수집과 '컬럼 없음'을 구분(v2.2 §12)",
                "required": ["searchedRecords", "fileRecordsTotal"],
                "properties": {
                    "searchedRecords": {"type": "integer"},
                    "fileRecordsTotal": {"type": "integer"},
                },
            },
        },
    }),
    "get_dataset_structure": _envelope({
        "type": "object",
        "required": ["recordId", "listKey", "distributionType", "coverageStatus", "examplesPublic"],
        "properties": {
            "recordId": {"type": "string"},
            "listKey": {"type": "string"},
            "distributionType": {"enum": ["FILE", "API", "STD"]},
            "coverageStatus": {
                "enum": ["AVAILABLE", "PARTIAL", "NOT_COLLECTED", "QUEUED", "COLLECTING",
                         "SOURCE_UNAVAILABLE", "UNSUPPORTED_FORMAT", "ACCESS_RESTRICTED",
                         "COLLECTION_FAILED", "API_STRUCTURE_NOT_SUPPORTED_YET"],
                "description": "미수집·보류·차단은 오류가 아닌 정상 상태(v2.2 구조 관측 설계)",
            },
            "reason": {"type": "string"},
            "evidenceLevel": {"const": "FILE_OBSERVATION"},
            "examplesPublic": {"type": "boolean",
                               "description": "false면 응답 정책상 예시값 비노출(S0-2 확인 전 보수 모드)"},
            "portalUrl": {"type": ["string", "null"]},
            "coverage": {
                "type": "object",
                "required": ["availableAssets", "totalAssets"],
            },
            "assets": {"type": "array", "items": {
                "type": "object",
                "required": ["fileName", "status"],
                "properties": {
                    "fileName": {"type": "string"},
                    "containerName": {"type": ["string", "null"], "description": "ZIP 컨테이너"},
                    "format": {"type": ["string", "null"]},
                    "shape": {"type": ["string", "null"]},
                    "status": {"type": "string"},
                    "failureReason": {"type": ["string", "null"]},
                    "observation": {
                        "type": "object",
                        "required": ["observationId", "observedAt", "provenance",
                                     "scanScope", "licenseGate"],
                    },
                    "tables": {"type": "array", "items": {
                        "type": "object",
                        "required": ["tableIndex", "columnCount", "columns"],
                        "properties": {
                            "sheetName": {"type": ["string", "null"]},
                            "sourcePath": {"type": ["string", "null"]},
                            "tableIndex": {"type": "integer"},
                            "scanScope": {"type": "string"},
                            "rowsScanned": {"type": ["integer", "null"]},
                            "rowCountObserved": {"type": ["integer", "null"],
                                                 "description": "관측 결과 알 수 있는 전체 행수. 알 수 없으면 null"},
                            "columnCount": {"type": "integer"},
                            "columns": {"type": "array", "items": {
                                "type": "object",
                                "required": ["ordinal", "sourceName", "exampleStatus"],
                                "properties": {
                                    "ordinal": {"type": "integer"},
                                    "sourceName": {"type": "string",
                                                   "description": "원본 컬럼명 그대로 — 정규화·번역 없음"},
                                    "observedType": {"type": ["string", "null"]},
                                    "distinctCount": {"type": ["integer", "null"]},
                                    "distinctApprox": {"type": "boolean"},
                                    "exampleStatus": {
                                        "enum": ["AVAILABLE", "NO_NON_NULL_VALUES",
                                                 "WITHHELD_BY_LICENSE", "WITHHELD_BY_SAFETY",
                                                 "NOT_COLLECTED", "COLLECTION_FAILED"]},
                                    "safetyStatus": {"type": "string"},
                                    "examples": {"type": "array", "maxItems": 10,
                                                 "items": {"type": "string"}},
                                    "exampleMethod": {"type": ["string", "null"]},
                                    "note": {"type": ["string", "null"]},
                                },
                            }},
                        },
                    }},
                },
            }},
        },
    }),
    "get_context": _envelope({
        "type": "object",
        "required": ["currentSnapshot", "release", "deployedAt", "processedAt",
                     "counts", "service"],
        "properties": {
            "counts": {
                "type": "object",
                "required": ["datasets", "issues", "changes"],
            },
            "service": {
                "type": "object",
                "required": ["definition", "baseUri", "rules", "responsibilityNote"],
                "properties": {"rules": {"type": "array", "items": {
                    "type": "object", "required": ["ruleId", "title"],
                }}},
            },
        },
    }),
}
