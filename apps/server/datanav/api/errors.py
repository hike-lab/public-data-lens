"""오류 모델(§4.3) — 일관 구조 + sourceSnapshot 포함."""
from __future__ import annotations


class DatanavError(Exception):
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self, source_snapshot: str | None = None) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "sourceSnapshot": source_snapshot,
            }
        }


class InvalidArgument(DatanavError):
    code = "INVALID_ARGUMENT"


class DatasetNotFound(DatanavError):
    code = "DATASET_NOT_FOUND"


class SnapshotNotFound(DatanavError):
    code = "SNAPSHOT_NOT_FOUND"


class FilterNotAvailable(DatanavError):
    code = "FILTER_NOT_AVAILABLE"


class TooManyDatasets(DatanavError):
    code = "TOO_MANY_DATASETS"


class IndexNotReady(DatanavError):
    code = "INDEX_NOT_READY"


class SourceVersionUnavailable(DatanavError):
    code = "SOURCE_VERSION_UNAVAILABLE"


class RateLimited(DatanavError):
    """설계서 검토에서 식별된 보완 코드 — 부속 명세 확정 대상."""
    code = "RATE_LIMITED"


HTTP_STATUS = {
    "CONCIERGE_UNAVAILABLE": 503,  # M3 전용 — 부속 명세 v1.1 대상(비생성형 계약과 분리)
    "INVALID_ARGUMENT": 400,
    "DATASET_NOT_FOUND": 404,
    "SNAPSHOT_NOT_FOUND": 404,
    "FILTER_NOT_AVAILABLE": 400,
    "TOO_MANY_DATASETS": 400,
    "INDEX_NOT_READY": 503,
    "SOURCE_VERSION_UNAVAILABLE": 404,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}
