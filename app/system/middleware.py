from urllib.parse import parse_qs

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestLimitsMiddleware:
    """Проверяет размер тела и повторение параметров запроса."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        query = parse_qs(scope["query_string"].decode(), keep_blank_values=True)
        for name, values in query.items():
            if len(values) > 1:
                response = JSONResponse(
                    {"message": f'invalid "{name}" parameter'}, status_code=400
                )
                return await response(scope, receive, send)
        if scope["method"] in ("POST", "PATCH"):
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > self.max_bytes:
                    response = JSONResponse(
                        {"message": "invalid JSON body"}, status_code=400
                    )
                    return await response(scope, receive, send)
                if not message.get("more_body", False):
                    break

            async def replay() -> Message:
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            return await self.app(scope, replay, send)
        return await self.app(scope, receive, send)
