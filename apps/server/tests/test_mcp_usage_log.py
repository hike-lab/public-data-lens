"""MCP 사용 로그(고지 v1.1) — 익명 규칙·옵트아웃·항목 캡 검증."""
from __future__ import annotations

import json

import pytest

from datanav.api import mcp_server
from datanav.api.usage import normalize_client, opted_out


def _lines(caplog):
    return [json.loads(r.message) for r in caplog.records if r.name == "datanav.mcp.usage"]


@pytest.fixture()
def usage_caplog(caplog):
    # 전용 핸들러(propagate=False)라 caplog가 못 보므로 테스트 동안만 전파를 켠다
    mcp_server._usage_logger.propagate = True
    with caplog.at_level("INFO", logger="datanav.mcp.usage"):
        yield caplog
    mcp_server._usage_logger.propagate = False


def test_guard_logs_tool_ms_and_query_cap(usage_caplog):
    long_q = "가" * 500
    result = mcp_server._guard(lambda: {"data": {"totalEstimate": 3}},
                               tool="search_datasets", q=long_q[:200])
    # 반환은 컴팩트 JSON 문자열(들여쓰기 없음 — 호스트 LLM 토큰 절감)
    assert "\n" not in result
    assert json.loads(result)["data"]["totalEstimate"] == 3
    (entry,) = _lines(usage_caplog)
    assert entry["kind"] == "mcp"
    assert entry["tool"] == "search_datasets"
    assert isinstance(entry["ms"], int)
    assert len(entry["q"]) == 200          # 질의 200자 캡
    assert entry["zero"] is False
    assert entry["client"] == "unknown"    # 인메모리 — HTTP 헤더 없음
    assert "anon" not in entry             # IP 없음 → 해시도 없음(날조 금지)


def test_guard_logs_error_code_without_traceback(usage_caplog):
    from datanav.api.errors import InvalidArgument

    def boom():
        raise InvalidArgument("bad", {})

    body = json.loads(mcp_server._guard(boom, tool="get_dataset"))
    assert body["error"]["code"] == "INVALID_ARGUMENT"
    (entry,) = _lines(usage_caplog)
    assert entry["error"] == "INVALID_ARGUMENT"
    assert "Traceback" not in json.dumps(entry)


def test_optout_header_skips_logging_entirely(usage_caplog, monkeypatch):
    monkeypatch.setattr(mcp_server, "_request_meta",
                        lambda: ({"x-datanav-no-log": "1"}, "1.2.3.4"))
    mcp_server._guard(lambda: {"data": {}}, tool="get_context")
    assert _lines(usage_caplog) == []      # 고지 §2 — 전부 미기록


def test_ip_is_hashed_never_raw(usage_caplog, monkeypatch):
    monkeypatch.setattr(mcp_server, "_request_meta",
                        lambda: ({"user-agent": "Claude-User/1.0"}, "203.0.113.7"))
    mcp_server._guard(lambda: {"data": {}}, tool="get_context")
    (entry,) = _lines(usage_caplog)
    assert "203.0.113.7" not in json.dumps(entry)   # 원 IP 미저장
    assert len(entry["anon"]) == 12
    assert entry["client"] == "claude"


def test_client_normalization_no_raw_ua():
    assert normalize_client("Claude-User/1.0 (+claude.ai)") == "claude"
    assert normalize_client("openai-mcp/1.0") == "openai"
    assert normalize_client("claude-code/2.1") == "claude-code"
    assert normalize_client("Mozilla/5.0 ...") == "other"
    assert normalize_client(None) == "unknown"


def test_opted_out_signals():
    assert opted_out({"dnt": "1"})
    assert opted_out({"sec-gpc": "1"})
    assert opted_out({"x-datanav-no-log": "1"})
    assert not opted_out({})
