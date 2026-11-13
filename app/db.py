import base64
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any, cast
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import Settings, settings


class DatabaseError(Exception):
    pass


class ClickHouse:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.database = config.clickhouse_database
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", self.database):
            raise ValueError("Invalid CLICKHOUSE_DATABASE")
        self.url = f"http://{config.clickhouse_host}:{config.clickhouse_http_port}/"

    def execute(
        self,
        sql: str,
        params: Mapping[str, object] | None = None,
        data: bytes | None = None,
        database: bool = True,
    ) -> str:
        query = {
            "query": sql,
            "wait_end_of_query": "1",
            "output_format_json_quote_64bit_integers": "0",
        }
        if database:
            query["database"] = self.database
        query.update({f"param_{k}": str(v) for k, v in (params or {}).items()})
        credentials = f"{self.config.clickhouse_user}:{self.config.clickhouse_password}"
        headers = {
            "Authorization": "Basic " + base64.b64encode(credentials.encode()).decode()
        }
        request = Request(
            self.url + "?" + urlencode(query), data=data or b"", headers=headers
        )
        try:
            with urlopen(request, timeout=self.config.http_timeout) as response:
                return str(response.read().decode())
        except HTTPError as exc:
            raise DatabaseError(exc.read().decode()) from exc

    def rows(
        self, sql: str, params: Mapping[str, object] | None = None
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            json.loads(self.execute(sql + " FORMAT JSON", params))["data"],
        )

    def insert(self, table: str, rows: Iterable[Mapping[str, object]]) -> None:
        payload = "\n".join(
            json.dumps(row, ensure_ascii=False) for row in rows
        ).encode()
        self.execute(f"INSERT INTO {table} FORMAT JSONEachRow", data=payload)
