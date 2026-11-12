import json
import unittest
from typing import Any
from unittest.mock import Mock

from dependency_injector import providers
from starlette.types import ASGIApp, Message, Scope

from app.containers import Container
from app.main import create_app


async def call(
    app: ASGIApp, method: str, path: str, body: bytes = b"", query: bytes = b""
) -> tuple[int, Any]:
    messages: list[Message] = []

    async def receive() -> Message:
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: Message) -> None:
        messages.append(message)

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query,
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
    }
    await app(scope, receive, send)
    status = next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    payload = b"".join(message.get("body", b"") for message in messages)
    return status, json.loads(payload) if payload else None


class ApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.container = Container()
        self.service = Mock()
        self.container.service.override(providers.Object(self.service))
        self.app = create_app(self.container)

    async def test_dependency_override_and_response_filter(self) -> None:
        self.service.get_user.return_value = {
            "id": 1,
            "fio": "Name",
            "phone": "123",
            "phone_prev": "",
            "created_at": "private",
        }
        status, body = await call(self.app, "GET", "/users/1")
        self.assertEqual(status, 200)
        self.assertNotIn("created_at", body)
        self.service.get_user.assert_called_once_with(1)

    async def test_validation_contract(self) -> None:
        for method, path, body, query, message in (
            (
                "POST",
                "/realty/1/gauges",
                b'{"gauge_id":true}',
                b"",
                'invalid "gauge_id" field',
            ),
            ("PATCH", "/users/1", b'{"phone":null}', b"", 'invalid "phone" field'),
            ("PATCH", "/users/1", b"{}", b"", 'invalid "fio" field'),
            ("PATCH", "/users/1", b"{", b"", "invalid JSON body"),
            ("PATCH", "/users/1", b"[]", b"", "invalid JSON body"),
            ("GET", "/tariffs", b"", b"", 'invalid "date" parameter'),
            (
                "GET",
                "/tariffs",
                b"",
                b"date=2025-01-01&date=2026-01-01",
                'invalid "date" parameter',
            ),
            (
                "GET",
                "/realty/1/invoices",
                b"",
                b"limit=1.5",
                'invalid "limit" parameter',
            ),
            (
                "GET",
                "/realty/1/readings",
                b"",
                b"date_from=2026-01-02&date_to=2026-01-01",
                'invalid "date_to" parameter',
            ),
        ):
            with self.subTest(path=path, body=body, query=query):
                self.assertEqual(
                    await call(self.app, method, path, body, query),
                    (400, {"message": message}),
                )
        self.assertEqual(self.service.mock_calls, [])

    async def test_body_limit(self) -> None:
        self.assertEqual(
            await call(self.app, "PATCH", "/users/1", b"x" * 65537),
            (400, {"message": "invalid JSON body"}),
        )

    async def test_empty_responses(self) -> None:
        self.assertEqual(await call(self.app, "GET", "/ping"), (200, None))
        self.assertEqual(
            await call(self.app, "PATCH", "/users/1", b'{"fio":"New"}'), (204, None)
        )
        self.assertEqual(
            await call(self.app, "POST", "/realty/1/gauges", b'{"gauge_id":2}'),
            (201, None),
        )

    async def test_openapi_and_not_found(self) -> None:
        self.assertEqual(
            await call(self.app, "GET", "/missing"), (404, {"message": "Not found"})
        )
        status, schema = await call(self.app, "GET", "/openapi.json")
        self.assertEqual(status, 200)
        operations = [
            operation
            for path in schema["paths"].values()
            for operation in path.values()
        ]
        self.assertEqual(len(operations), 9)
        self.assertTrue(
            all("422" not in operation["responses"] for operation in operations)
        )
        self.assertIn("CreateReadingRequest", schema["components"]["schemas"])


class ContainerTests(unittest.TestCase):
    def test_shared_lock_and_database_override(self) -> None:
        container = Container()
        fake_db = Mock()
        with container.database.override(providers.Object(fake_db)):
            first, second = container.service(), container.service()
            self.assertIs(first.db, fake_db)
            self.assertIs(first.write_lock, second.write_lock)
        self.assertIsNot(first, second)
        self.assertIsNot(container.write_lock(), Container().write_lock())
