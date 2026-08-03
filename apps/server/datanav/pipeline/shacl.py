"""SHACL 검증 — 카탈로그 노드 + 데이터셋 표본(기본 500건, 전수는 옵션).

전수 pyshacl 검증은 9.5만 건 규모에서 실행 시간이 과도하므로,
구조 검증은 파이프라인의 프로그램적 검사(전수)와 SHACL 표본 검증을 병행한다.
표본 크기는 DATANAV_SHACL_SAMPLE 환경변수로 조정(0 = 전수).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from pyshacl import validate as pyshacl_validate
from rdflib import Graph

from .jsonld import JSONLD_CONTEXT

SHAPES_PATH = Path(__file__).parent / "shapes" / "catalog-1.0.ttl"
DEFAULT_SAMPLE = 500


def _to_graph(docs: list[dict]) -> Graph:
    g = Graph()
    for doc in docs:
        inline = dict(doc)
        inline["@context"] = JSONLD_CONTEXT  # 로컬 검증은 컨텍스트 인라인
        g.parse(data=json.dumps(inline, ensure_ascii=False), format="json-ld")
    return g


def validate_docs(docs: list[dict]) -> dict:
    """JSON-LD 문서 목록을 SHACL 셰이프로 검증. 반환: {conforms, violations, warnings, results[]}."""
    data_graph = _to_graph(docs)
    shapes = Graph().parse(SHAPES_PATH, format="turtle")
    conforms, results_graph, _ = pyshacl_validate(
        data_graph, shacl_graph=shapes, allow_warnings=True
    )
    from rdflib.namespace import SH

    results = []
    for r in results_graph.subjects(predicate=None, object=SH.ValidationResult):
        sev = results_graph.value(r, SH.resultSeverity)
        results.append({
            "severity": str(sev).rsplit("#", 1)[-1] if sev else "Unknown",
            "focusNode": str(results_graph.value(r, SH.focusNode) or ""),
            "message": str(results_graph.value(r, SH.resultMessage) or ""),
            "path": str(results_graph.value(r, SH.resultPath) or ""),
        })
    violations = [x for x in results if x["severity"] == "Violation"]
    warnings = [x for x in results if x["severity"] == "Warning"]
    return {
        "conforms": len(violations) == 0,
        "violationCount": len(violations),
        "warningCount": len(warnings),
        "results": (violations + warnings)[:200],
    }


def sample_size() -> int:
    return int(os.environ.get("DATANAV_SHACL_SAMPLE", DEFAULT_SAMPLE))
