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


# --- 보강(ADR-017): 계약 오류 코드 병기·실패 위치·거짓 양성 방지·청크 재조립 ---

def test_error_carries_contract_code_and_failure_position():
    """제보자의 실제 어려움은 원인 규명이었다 — 실패 바이트 위치·사유를 담는다."""
    async def downstream(scope, receive, send):
        raise AssertionError("비UTF-8 본문이 하류로 전달되었다")

    sent = []
    payload = json.dumps({"params": {"query": "주차장"}}, ensure_ascii=False).encode("cp949")

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    async def send(msg):
        sent.append(msg)

    _run(Utf8GuardMiddleware(downstream)(_http_scope(), receive, send))
    err = json.loads(next(m for m in sent if m["type"] == "http.response.body")["body"])["error"]
    assert err["code"] == -32700
    assert err["data"]["code"] == "INVALID_ARGUMENT"  # 계약 오류 모델(§4.3)과 정합
    assert err["data"]["details"]["expectedEncoding"] == "utf-8"
    assert isinstance(err["data"]["details"]["failedAtByte"], int)
    assert err["data"]["details"]["reason"]


def test_ascii_only_cp949_body_is_not_rejected():
    """CP949로 보냈지만 ASCII만 있으면 UTF-8로도 유효하다 — 막지 않는다."""
    captured = {}

    async def downstream(scope, receive, send):
        captured["body"] = (await receive())["body"]

    payload = b'{"jsonrpc":"2.0","method":"get_context","id":1}'

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    _run(Utf8GuardMiddleware(downstream)(_http_scope(), receive, lambda m: None))
    assert captured["body"] == payload


def test_chunked_body_is_reassembled_and_replayed():
    """청크 경계가 멀티바이트 문자를 가르더라도 전체를 모아 판정한다."""
    payload = "한글 질의".encode("utf-8")
    queue = [
        {"type": "http.request", "body": payload[:4], "more_body": True},
        {"type": "http.request", "body": payload[4:], "more_body": False},
    ]
    captured = []

    async def downstream(scope, receive, send):
        while True:
            msg = await receive()
            captured.append(msg.get("body", b""))
            if not msg.get("more_body"):
                break

    async def receive():
        return queue.pop(0)

    _run(Utf8GuardMiddleware(downstream)(_http_scope(), receive, lambda m: None))
    assert b"".join(captured) == payload  # 청크 구조까지 보존해 재생
