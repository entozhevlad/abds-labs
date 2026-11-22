import argparse
import time
from pathlib import Path

from app.config import settings
from app.db import ClickHouse
from app.generate import TABLES, generate


def schema(db: ClickHouse) -> None:
    db.execute(f"CREATE DATABASE IF NOT EXISTS {db.database}", database=False)
    sql = (Path(__file__).resolve().parent.parent / "sql/schema.sql").read_text()
    for statement in sql.split(";"):
        if statement.strip():
            db.execute(statement)


def load(db: ClickHouse) -> None:
    # Refuse before writing any rows: replaying collapsing events is not idempotent.
    schema(db)
    for table in TABLES:
        if db.rows(f"SELECT count() AS count FROM {table}")[0]["count"]:
            raise RuntimeError(
                "Database is not empty. Run make teardown before make setup/load."
            )
    paths = [(table, settings.data_dir / f"{table}.csv") for table in TABLES]
    for _, path in paths:
        if not path.is_file():
            raise RuntimeError(f"Missing {path}; run make gen")
    for table, path in paths:
        with path.open("rb") as source:
            while True:
                chunk = source.readlines(settings.load_chunk_bytes)
                if not chunk:
                    break
                db.execute(f"INSERT INTO {table} FORMAT CSV", data=b"".join(chunk))
        print(f"Loaded {table}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("gen", "schema", "load", "setup", "teardown")
    )
    command = parser.parse_args().command
    started = time.monotonic()
    if command == "gen":
        generate()
    else:
        db = ClickHouse()
        if command == "schema":
            schema(db)
        if command == "setup":
            generate()
        if command in ("load", "setup"):
            load(db)
        if command == "teardown":
            for table in reversed(TABLES):
                db.execute(
                    f"DROP TABLE IF EXISTS {db.database}.{table} SYNC", database=False
                )
    print(f"{command}: {time.monotonic() - started:.2f}s", flush=True)


if __name__ == "__main__":
    main()
