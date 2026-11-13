import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from typing import Any, ClassVar
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.db import ClickHouse
from app.manage import load

TEST_ID = 9000000001


def request(method: str, path: str, body: object = None) -> tuple[int, Any]:
    payload = None if body is None else json.dumps(body).encode()
    req = Request(
        f"http://localhost:{os.environ['APP_PORT']}{path}",
        data=payload,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urlopen(req, timeout=float(os.environ["HTTP_TIMEOUT"]))
    except HTTPError as exc:
        response = exc
    with response:
        data = response.read()
        return response.status, json.loads(data) if data else None


class IntegrationTests(unittest.TestCase):
    db: ClassVar[ClickHouse]

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = ClickHouse()
        tables = cls.db.rows(
            "SELECT name FROM system.tables WHERE database = {database:String}",
            {"database": cls.db.database},
        )
        if len(tables) < 7:
            raise RuntimeError("Schema is missing. Run make setup before make check.")
        cls.clean()
        now = "2023-11-01 00:00:00"
        cls.db.insert(
            "dim_realty",
            [
                {
                    "id": TEST_ID,
                    "address": "Test",
                    "square": 50,
                    "type": "flat",
                    "number": "1",
                    "rooms": 2,
                    "floor": 1,
                    "porch": 1,
                    "created_at": now,
                }
            ],
        )
        cls.db.insert(
            "dim_users",
            [
                {
                    "id": TEST_ID,
                    "fio": "Old Name",
                    "phone": "+70000000000",
                    "phone_prev": "",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )
        cls.db.insert(
            "dim_gauges",
            [{"id": TEST_ID, "name": "Test", "country": "Россия", "created_at": now}],
        )

    @classmethod
    def clean(cls) -> None:
        for table, field in (
            ("fact_meter_readings", "realty_id"),
            ("fact_gauge_bindings", "realty_id"),
            ("fact_invoice", "realty_id"),
            ("dim_tariffs", "id"),
            ("dim_users", "id"),
            ("dim_gauges", "id"),
            ("dim_realty", "id"),
        ):
            cls.db.execute(
                f"ALTER TABLE {table} DELETE WHERE {field} = {{id:UInt64}} "
                "SETTINGS mutations_sync = 1",
                {"id": TEST_ID},
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clean()

    def test_counts_and_engines(self) -> None:
        expected = {
            "dim_realty": 1000,
            "dim_users": 1000,
            "dim_gauges": 1100,
            "dim_tariffs": 2,
            "fact_meter_readings": 1096000,
            "fact_invoice": 36000,
            "fact_gauge_bindings": 1000,
        }
        for table, count in expected.items():
            field = "id" if table.startswith("dim_") else "realty_id"
            final = (
                ""
                if table in ("dim_realty", "dim_gauges", "fact_invoice")
                else " FINAL"
            )
            value = self.db.rows(
                f"SELECT count() AS n FROM {table}{final} WHERE {field} < {TEST_ID}"
            )[0]["n"]
            self.assertEqual(value, count, table)
        self.assertTrue(
            self.db.rows(
                "SELECT id FROM dim_tariffs FINAL GROUP BY id HAVING count() >= 2"
            )
        )
        self.assertTrue(
            self.db.rows(
                "SELECT version FROM fact_gauge_bindings FINAL "
                "WHERE version >= 2 LIMIT 1"
            )
        )
        engines = {
            row["name"]: row["engine"]
            for row in self.db.rows(
                "SELECT name, engine FROM system.tables "
                "WHERE database = {database:String}",
                {"database": self.db.database},
            )
        }
        self.assertEqual(
            engines,
            {
                "dim_realty": "MergeTree",
                "dim_gauges": "MergeTree",
                "dim_users": "ReplacingMergeTree",
                "dim_tariffs": "ReplacingMergeTree",
                "fact_meter_readings": "ReplacingMergeTree",
                "fact_invoice": "MergeTree",
                "fact_gauge_bindings": "VersionedCollapsingMergeTree",
            },
        )

    def test_delete_and_tariff_versioning(self) -> None:
        tariff = {
            "id": TEST_ID,
            "name": "Test",
            "price_day_kwph": 100,
            "price_night_kwph": 50,
            "valid_from": "2023-11-01 00:00:00",
            "valid_to": "2099-01-01 00:00:00",
            "created_at": "2023-11-01 00:00:00",
            "updated_at": "2023-11-01 00:00:00",
        }
        self.db.insert("dim_tariffs", [tariff])
        self.db.insert(
            "dim_tariffs",
            [
                dict(
                    tariff,
                    valid_to="2025-11-01 00:00:00",
                    updated_at="2025-11-01 00:00:00",
                ),
                dict(
                    tariff,
                    valid_from="2025-11-01 00:00:00",
                    price_day_kwph=200,
                    updated_at="2025-11-01 00:00:00",
                ),
            ],
        )
        versions = self.db.rows(
            "SELECT valid_from, valid_to, price_day_kwph FROM dim_tariffs FINAL "
            "WHERE id = {id:UInt64} ORDER BY valid_from",
            {"id": TEST_ID},
        )
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["valid_to"], versions[1]["valid_from"])
        self.assertEqual([row["price_day_kwph"] for row in versions], [100, 200])
        self.db.insert(
            "fact_invoice",
            [
                {
                    "realty_id": TEST_ID,
                    "user_id": TEST_ID,
                    "tariff_id": TEST_ID,
                    "gauge_id": TEST_ID,
                    "day_kw": 100,
                    "night_kw": 10,
                    "price": 105000,
                    "deadline": "2026-11-10",
                    "created_at": "2026-10-31 23:00:00",
                }
            ],
        )
        self.db.execute(
            "ALTER TABLE fact_invoice DELETE WHERE realty_id = {id:UInt64} "
            "SETTINGS mutations_sync=1",
            {"id": TEST_ID},
        )
        self.assertEqual(
            self.db.rows(
                "SELECT count() AS n FROM fact_invoice WHERE realty_id = {id:UInt64}",
                {"id": TEST_ID},
            )[0]["n"],
            0,
        )

    def test_ping_and_errors(self) -> None:
        self.assertEqual(request("GET", "/ping"), (200, None))
        self.assertEqual(
            request("GET", "/users/8999999999"), (404, {"message": "Not found"})
        )
        for path in (
            "/tariffs",
            "/tariffs?date=2026-02-29",
            "/realty/1/readings",
            "/realty/1/invoices?limit=-1",
            "/realty/1/invoices?offset=x",
        ):
            self.assertEqual(request("GET", path)[0], 400, path)
        self.assertEqual(request("GET", "/tariffs?date=2022-01-01")[0], 404)
        self.assertEqual(request("GET", "/tariffs?date=1900-01-01")[0], 404)
        self.assertEqual(request("PATCH", f"/users/{TEST_ID}", {})[0], 400)

    def test_scd_users(self) -> None:
        path = f"/users/{TEST_ID}"
        self.assertEqual(
            request("PATCH", path, {"fio": "O'Нил \\ Иван", "phone": "+71111111111"})[
                0
            ],
            204,
        )
        self.assertEqual(request("PATCH", path, {"phone": "+72222222222"})[0], 204)
        self.assertEqual(request("PATCH", path, {"phone": "+72222222222"})[0], 204)
        self.assertEqual(
            request("GET", path)[1],
            {
                "id": TEST_ID,
                "fio": "O'Нил \\ Иван",
                "phone": "+72222222222",
                "phone_prev": "+71111111111",
            },
        )
        self.assertEqual(
            self.db.rows(
                "SELECT count() AS n FROM dim_users "
                "WHERE id = {id:UInt64} AND fio = 'Old Name'",
                {"id": TEST_ID},
            )[0]["n"],
            0,
        )

    def test_reading_corrections(self) -> None:
        path = f"/realty/{TEST_ID}/readings"
        row = {
            "user_id": TEST_ID,
            "gauge_id": TEST_ID,
            "tariff_id": 1,
            "reading_date": "2026-10-01",
            "day_kw": 100,
            "night_kw": 20,
        }
        for value in (-1, True, 1.5, 2**32):
            self.assertEqual(
                request("POST", path, dict(row, day_kw=value)),
                (400, {"message": 'invalid "day_kw" field'}),
            )
        self.assertEqual(request("POST", path, dict(row, user_id=8999999999))[0], 404)
        self.assertEqual(request("POST", path, row)[0], 201)
        self.assertEqual(
            request("POST", path, dict(row, day_kw=110, gauge_id=1))[0], 201
        )
        response = request("GET", path + "?date_from=2026-10-01&date_to=2026-10-01")[1]
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["readings"][0]["day_kw"], 110)
        self.assertEqual(response["readings"][0]["gauge_id"], 1)
        self.assertEqual(
            request("GET", path + "?date_from=2022-01-01&date_to=2022-01-01")[1],
            {"readings": [], "count": 0},
        )

    def test_gauge_replacement_concurrent(self) -> None:
        path = f"/realty/{TEST_ID}/gauges"
        self.assertEqual(request("POST", path, {"gauge_id": TEST_ID})[0], 201)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(
                pool.map(
                    lambda _: request("POST", path, {"gauge_id": TEST_ID}), range(4)
                )
            )
        self.assertTrue(all(status == 201 for status, _ in results))
        rows = self.db.rows(
            "SELECT gauge_id, version, sign FROM fact_gauge_bindings FINAL "
            "WHERE realty_id = {id:UInt64}",
            {"id": TEST_ID},
        )
        self.assertEqual(rows, [{"gauge_id": TEST_ID, "version": 5, "sign": 1}])

    def test_tariffs_and_invoice_calculation(self) -> None:
        old = request("GET", "/tariffs?date=2025-10-31")[1]
        new = request("GET", "/tariffs?date=2025-11-01")[1]
        self.assertEqual(old["valid_to"], new["valid_from"])
        self.assertNotEqual(old["price_day_kwph"], new["price_day_kwph"])
        self.assertEqual(new["valid_to"], "2099-01-01 00:00:00")
        invoices = request("GET", "/realty/1/invoices?limit=100")[1]
        self.assertEqual(invoices["count"], 36)
        self.assertEqual(len(invoices["invoices"]), 36)
        dates = [row["created_at"] for row in invoices["invoices"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for row in invoices["invoices"]:
            tariff = old if row["created_at"] < new["valid_from"] else new
            self.assertEqual(
                row["price"],
                row["day_kw"] * tariff["price_day_kwph"]
                + row["night_kw"] * tariff["price_night_kwph"],
            )
            self.assertTrue(row["deadline"].endswith("-10"))
        self.assertEqual(
            request("GET", "/realty/1/invoices?limit=0")[1],
            {"invoices": [], "count": 36},
        )
        self.assertEqual(
            request("GET", "/realty/1/invoices?offset=36")[1],
            {"invoices": [], "count": 36},
        )

    def test_repeated_load_refused(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "not empty"):
            load(self.db)


if __name__ == "__main__":
    unittest.main(verbosity=2)
