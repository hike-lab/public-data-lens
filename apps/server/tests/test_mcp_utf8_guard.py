"""비UTF-8 요청 본문 가드(Issue #1 문제②) — generic -32603 대신 명시적 -32700."""
import asyncio
import json

from datanav.api.mcp_server import Utf8GuardMiddleware


def _run(coro):
    return asyncio.run(coro)


def _http_scope(method="POST"):
    return {"type": "http", "method": method, "path": "/mcp", "headers": []}


def test_non_utf8_body_returns_explicit_parse_error():
    async def downstream(scope, receive, send):  # 도달하면 실패
        raise AssertionError("비UTF-8 본문이 하류로 전달되었다")

    sent = []

    async def receive():
        return {"type": "http.request", "body": b"\xff\xfe\x00invalid", "more_body": False}

    async def send(msg):
        sent.append(msg)

    _run(Utf8GuardMiddleware(downstream)(_http_scope(), receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    assert start["status"] == 400
    body = json.loads(next(m for m in sent if m["type"] == "http.response.body")["body"])
    assert body["error"]["code"] == -32700
    assert "UTF-8" in body["error"]["message"]  # 원인 명시 — generic 문구 금지


def test_valid_utf8_body_is_replayed_downstream():
    captured = {}

    async def downstream(scope, receive, send):
        msg = await receive()
        captured["body"] = msg["body"]

    payload = json.dumps({"jsonrpc": "2.0", "method": "x", "id": 1},
                         ensure_ascii=False).encode("utf-8")

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    async def send(msg):
        pass

    _run(Utf8GuardMiddleware(downstream)(_http_scope(), receive, send))
    assert captured["body"] == payload  # 무손실 재전달


def test_non_post_passthrough():
    called = {}

    async def downstream(scope, receive, send):
        called["ok"] = True

    _run(Utf8GuardMiddleware(downstream)(_http_scope("GET"), None, None))
    assert called.get("ok")
