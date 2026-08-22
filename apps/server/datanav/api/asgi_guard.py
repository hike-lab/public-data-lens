"""전송 계층 요청 판정 — MCP SDK가 내부 오류로 뭉개는 원인을 먼저 알려준다.

배경(Issue #1 항목 2): 요청 본문이 UTF-8이 아닐 때 MCP SDK의 POST 핸들러
(`mcp/server/streamable_http.py`)가 catch-all로 받아 `-32603 "Error handling POST
request"`만 반환한다. 제보자는 한글 질의만 실패하는 것처럼 보여 서버 버그로 오인했다.
클라이언트 잘못이지만 원인을 알 수 없는 오류는 디버깅 비용을 전가한다.

JSON-RPC 규격상 해석 불가한 입력은 Parse error(-32700)이며 내부 오류(-32603)가 아니다.
계약 오류 모델(§4.3)의 INVALID_ARGUMENT를 data에 병기해 REST 표면과 코드를 맞춘다.
"""
from __future__ import annotations

import json

# MCP 요청 본문은 작다. 판정을 위해 버퍼링하므로 상한을 둔다.
MAX_BODY_PEEK = 1 << 20  # 1 MiB

_PARSE_ERROR = -32700


def _error_payload(exc: UnicodeDecodeError) -> bytes:
    return json.dumps({
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": _PARSE_ERROR,
            "message": (
                "요청 본문이 UTF-8이 아닙니다 — MCP 요청은 UTF-8로 인코딩해야 합니다. "
                f"{exc.start}바이트 위치에서 디코딩 실패({exc.encoding}: {exc.reason}). "
                "클라이언트가 CP949 등 다른 인코딩으로 본문을 보냈는지 확인하십시오."
            ),
            "data": {
                "code": "INVALID_ARGUMENT",
                "details": {
                    "expectedEncoding": "utf-8",
                    "failedAtByte": exc.start,
                    "reason": exc.reason,
                },
            },
        },
    }, ensure_ascii=False).encode("utf-8")


class Utf8BodyGuard:
    """POST 본문의 UTF-8 디코딩 가능성만 판정하는 순수 ASGI 미들웨어.

    BaseHTTPMiddleware를 쓰지 않는다 — SSE·스트리밍 응답을 깨뜨리기 때문이다.
    판정 후에는 소비한 ASGI 메시지를 그대로 재생해 하위 앱이 본문을 다시 읽게 한다.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return

        buffered: list[dict] = []
        size = 0
        while True:
            message = await receive()
            buffered.append(message)
            if message["type"] != "http.request":
                break  # http.disconnect 등 — 판정하지 않고 그대로 넘긴다
            size += len(message.get("body", b""))
            if not message.get("more_body", False) or size > MAX_BODY_PEEK:
                break

        body = b"".join(
            m.get("body", b"") for m in buffered if m["type"] == "http.request"
        )
        try:
            body.decode("utf-8")
        except UnicodeDecodeError as exc:
            payload = _error_payload(exc)
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(payload)).encode()),
                ],
            })
            await send({"type": "http.response.body", "body": payload})
            return

        pending = iter(buffered)

        async def replay():
            """버퍼링한 메시지를 먼저 돌려주고, 소진되면 원래 receive로 넘어간다."""
            try:
                return next(pending)
            except StopIteration:
                return await receive()

        await self.app(scope, replay, send)
