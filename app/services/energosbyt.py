from _thread import LockType
from typing import Any

from app.db import ClickHouse
from app.system.exceptions import ApiError
from app.system.time import timestamp


class EnergosbytService:
    def __init__(self, db: ClickHouse, write_lock: LockType) -> None:
        self.db = db
        self.write_lock = write_lock

    def exists(self, table: str, identifier: int) -> None:
        final = " FINAL" if table in ("dim_users", "dim_tariffs") else ""
        rows = self.db.rows(
            f"SELECT id FROM {table}{final} WHERE id = {{id:UInt64}} LIMIT 1",
            {"id": identifier},
        )
        if not rows:
            raise ApiError(404, "Not found")

    def get_user(self, identifier: int) -> dict[str, Any]:
        rows = self.db.rows(
            "SELECT * FROM dim_users FINAL WHERE id = {id:UInt64}", {"id": identifier}
        )
        if not rows:
            raise ApiError(404, "Not found")
        return rows[0]

    def update_user(self, identifier: int, changes: dict[str, str]) -> None:
        with self.write_lock:
            user = self.get_user(identifier)
            if "phone" in changes and changes["phone"] != user["phone"]:
                user["phone_prev"] = user["phone"]
                user["phone"] = changes["phone"]
            if "fio" in changes:
                self.db.execute(
                    "ALTER TABLE dim_users UPDATE fio = {fio:String} "
                    "WHERE id = {id:UInt64} SETTINGS mutations_sync = 1",
                    {"id": identifier, "fio": changes["fio"]},
                )
                user["fio"] = changes["fio"]
            user["updated_at"] = timestamp(user["updated_at"])
            self.db.insert("dim_users", [user])

    def get_realty(self, identifier: int) -> dict[str, Any]:
        rows = self.db.rows(
            "SELECT id, address, square, type, number, rooms, floor, porch "
            "FROM dim_realty WHERE id = {id:UInt64}",
            {"id": identifier},
        )
        if not rows:
            raise ApiError(404, "Not found")
        return rows[0]

    def get_tariff(self, day: str) -> dict[str, Any]:
        rows = self.db.rows(
            "SELECT id, name, price_day_kwph, price_night_kwph, valid_from, valid_to "
            "FROM dim_tariffs FINAL "
            "WHERE toDate32(valid_from) <= toDate32({day:String}) "
            "AND toDate32({day:String}) < toDate32(valid_to) "
            "ORDER BY id LIMIT 1",
            {"day": day},
        )
        if not rows:
            raise ApiError(404, "Not found")
        return rows[0]

    def get_readings(self, identifier: int, start: str, end: str) -> dict[str, Any]:
        self.exists("dim_realty", identifier)
        rows = self.db.rows(
            "SELECT reading_date, user_id, tariff_id, gauge_id, day_kw, night_kw "
            "FROM fact_meter_readings FINAL WHERE realty_id = {id:UInt64} "
            "AND reading_date BETWEEN {start:Date} AND {end:Date} "
            "ORDER BY reading_date",
            {"id": identifier, "start": start, "end": end},
        )
        return {"readings": rows, "count": len(rows)}

    def create_reading(self, identifier: int, reading: dict[str, Any]) -> None:
        with self.write_lock:
            self.exists("dim_realty", identifier)
            for key, table in (
                ("user_id", "dim_users"),
                ("gauge_id", "dim_gauges"),
                ("tariff_id", "dim_tariffs"),
            ):
                self.exists(table, reading[key])
            old = self.db.rows(
                "SELECT created_at FROM fact_meter_readings FINAL "
                "WHERE realty_id = {id:UInt64} AND reading_date = {day:Date}",
                {"id": identifier, "day": reading["reading_date"]},
            )
            row = dict(
                reading,
                realty_id=identifier,
                created_at=timestamp(old[0]["created_at"] if old else None),
            )
            self.db.insert("fact_meter_readings", [row])

    def get_invoices(self, identifier: int, limit: int, offset: int) -> dict[str, Any]:
        self.exists("dim_realty", identifier)
        params = {"id": identifier, "limit": limit, "offset": offset}
        count = self.db.rows(
            "SELECT count() AS count FROM fact_invoice WHERE realty_id = {id:UInt64}",
            params,
        )[0]["count"]
        rows = self.db.rows(
            "SELECT tariff_id, gauge_id, day_kw, night_kw, price, deadline, created_at "
            "FROM fact_invoice WHERE realty_id = {id:UInt64} ORDER BY created_at DESC "
            "LIMIT {limit:UInt64} OFFSET {offset:UInt64}",
            params,
        )
        return {"invoices": rows, "count": count}

    def install_gauge(self, identifier: int, gauge_id: int) -> None:
        with self.write_lock:
            self.exists("dim_realty", identifier)
            self.exists("dim_gauges", gauge_id)
            active = self.db.rows(
                "SELECT * FROM fact_gauge_bindings FINAL "
                "WHERE realty_id = {id:UInt64} AND sign = 1 ORDER BY version DESC",
                {"id": identifier},
            )
            rows = [dict(row, sign=-1) for row in active]
            version = max((row["version"] for row in active), default=0) + 1
            rows.append(
                {
                    "gauge_id": gauge_id,
                    "realty_id": identifier,
                    "created_at": timestamp(),
                    "sign": 1,
                    "version": version,
                }
            )
            self.db.insert("fact_gauge_bindings", rows)
