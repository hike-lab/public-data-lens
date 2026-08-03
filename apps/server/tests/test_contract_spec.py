"""계약-코드 정합 가드 — 부속 명세(v1.0.0 동결)와 실제 서버 동작의 일치를 보증한다.

이 테스트가 깨지면 코드가 공개 계약에서 이탈했다는 뜻이다.
계약을 바꾸려면 datanav/spec을 수정하고 scripts/gen_tool_spec.py로 재생성해야 한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from datanav.spec import OUTPUT_SCHEMAS

SPEC_PATH = (
    Path(__file__).resolve().parents[1] / "datanav" / "spec" / "tool-schemas-v1.3.0.json"
)


def test_spec_file_exists_and_matches_module():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert set(spec["tools"]) == set(OUTPUT_SCHEMAS)
    for name, tool in spec["tools"].items():
        assert tool["outputSchema"] == OUTPUT_SCHEMAS[name], f"{name} 출력 스키마 불일치 — gen_tool_spec.py 재실행 필요"


def test_input_schemas_match_live_server():
    """MCP 서버의 입력 스키마가 명세 파일과 동일한지(계약 이탈 감지)."""
    import asyncio
    from mcp.shared.memory import create_connected_server_and_client_session
    from datanav.api.mcp_server import mcp

    async def live():
        async with create_connected_server_and_client_session(mcp._mcp_server) as c:
            return {t.name: t.inputSchema for t in (await c.list_tools()).tools}

    live_schemas = asyncio.run(live())
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    for name, tool in spec["tools"].items():
        assert live_schemas[name] == tool["inputSchema"], f"{name} 입력 스키마 변경됨 — 명세 재생성·재승인 필요"


@pytest.mark.parametrize("tool,call", [
    ("search_datasets", lambda s: s.search_datasets(query="도서관", page_size=5)),
    ("search_datasets", lambda s: s.search_datasets(page_size=1)),
    ("get_catalog_changes", lambda s: s.get_catalog_changes(page_size=5)),
    ("get_catalog_stats", lambda s: s.get_catalog_stats("completeness")),
    ("get_catalog_stats", lambda s: s.get_catalog_stats("theme")),
])
def test_live_output_conforms(catalog_service, tool, call):
    Draft202012Validator(OUTPUT_SCHEMAS[tool]).validate(call(catalog_service))


def test_live_dataset_views_conform(catalog_service):
    rid = catalog_service.search_datasets(page_size=1)["data"]["items"][0]["recordId"]
    v = Draft202012Validator(OUTPUT_SCHEMAS["get_dataset"])
    for view in ("card", "normalized", "source", "jsonld"):
        v.validate(catalog_service.get_dataset(rid, view))


def test_live_compare_conforms(catalog_service):
    items = catalog_service.search_datasets(page_size=2)["data"]["items"]
    Draft202012Validator(OUTPUT_SCHEMAS["compare_datasets"]).validate(
        catalog_service.compare_datasets([i["recordId"] for i in items])
    )
