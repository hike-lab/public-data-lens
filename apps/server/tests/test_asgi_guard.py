"""Utf8BodyGuard — 비UTF-8 요청 본문을 명시적 오류로 알린다(Issue #1 항목 2)."""
import json

import pytest

from datanav.api.asgi_guard import Utf8BodyGuard


async def _downstream(scope, receive, send):
    """본문을 끝까지 읽어 그대로 되돌려주는 최소 앱 — 본문 재생이 되는지 확인용."""
    chunks = []
    while True:
        msg = await receive()
        if msg["type"] != "http.request":
            break
        chunks.append(msg.get("body", b""))
        if not msg.get("more_body", False):
            break
    body = b"".join(chunks)
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": body})


async def _call(app, method="POST", chunks=(b"",)):
    scope = {"type": "http", "method": method, "path": "/mcp", "headers": []}
    queue = [
        {"type": "http.request", "body": c, "more_body": i < len(chunks) - 1}
        for i, c in enumerate(chunks)
    ]
    sent = []

    async def receive():
        return queue.pop(0) if queue else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], body


@pytest.mark.anyio
async def test_utf8_body_passes_through_intact():
    """정상 본문은 하위 앱에 원문 그대로 전달된다(재생 검증)."""
    payload = json.dumps({"method": "search_datasets", "params": {"query": "주차장"}},
                         ensure_ascii=False).encode("utf-8")
    status, echoed = await _call(Utf8BodyGuard(_downstream), chunks=(payload,))
    assert status == 200
    assert echoed == payload


@pytest.mark.anyio
async def test_chunked_utf8_body_is_reassembled():
    payload = "한글 질의".encode("utf-8")
    status, echoed = await _call(
        Utf8BodyGuard(_downstream), chunks=(payload[:4], payload[4:])
    )
    assert status == 200
    assert echoed == payload


@pytest.mark.anyio
async def test_cp949_body_is_rejected_with_explicit_cause():
    """제보 상황 재현 — 한글 질의를 CP949로 보내면 원인을 알 수 있어야 한다."""
    payload = json.dumps({"params": {"query": "주차장"}}, ensure_ascii=False).encode("cp949")
    status, body = await _call(Utf8BodyGuard(_downstream), chunks=(payload,))
    assert status == 400
    err = json.loads(body)["error"]
    assert err["code"] == -32700  # Parse error — 내부 오류(-32603)가 아니다
    assert "UTF-8" in err["message"]
    assert err["data"]["code"] == "INVALID_ARGUMENT"
    assert err["data"]["details"]["expectedEncoding"] == "utf-8"
    assert isinstance(err["data"]["details"]["failedAtByte"], int)


@pytest.mark.anyio
async def test_ascii_only_cp949_body_is_not_false_positive():
    """CP949로 보냈지만 ASCII만 있으면 UTF-8로도 유효하다 — 막지 않는다."""
    payload = b'{"method":"get_context"}'
    status, _ = await _call(Utf8BodyGuard(_downstream), chunks=(payload,))
    assert status == 200


@pytest.mark.anyio
async def test_non_post_is_untouched():
    status, _ = await _call(Utf8BodyGuard(_downstream), method="GET")
    assert status == 200
