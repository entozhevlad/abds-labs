import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


def load_env() -> None:
    """Загружает переменные из файла локального окружения."""
    path = Path(__file__).resolve().parent.parent / ".env.local"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)


def env(name: str) -> str:
    """Возвращает обязательную переменную окружения."""
    try:
        return os.environ[name]
    except KeyError as exc:
        raise RuntimeError(f"Missing environment variable: {name}") from exc


@dataclass(frozen=True)
class Settings:
    """Хранит конфигурацию приложения и генератора."""

    app_name: str
    app_version: str
    app_host: str
    app_port: int
    clickhouse_host: str
    clickhouse_http_port: int
    clickhouse_user: str
    clickhouse_password: str
    clickhouse_database: str
    http_timeout: float
    max_request_bytes: int
    data_dir: Path
    load_chunk_bytes: int
    generator_seed: int
    generator_objects: int
    generator_commercial_step: int
    generator_objects_per_house: int
    generator_square_min: int
    generator_square_max: int
    generator_rooms_min: int
    generator_rooms_max: int
    generator_floors: int
    generator_day_usage_min: int
    generator_day_usage_max: int
    generator_night_usage_min: int
    generator_night_usage_max: int
    generator_invoice_deadline_day: int
    generator_tariff_name: str
    generator_gauge_name: str
    generator_replacement_gauge_name: str
    generator_gauge_country: str
    generator_start_date: date
    generator_end_date: date
    generator_tariff_change_date: date
    generator_gauge_replacement_date: date
    generator_open_version_date: date
    generator_replacement_step: int
    generator_gauge_offset: int
    generator_correction_rate: float
    generator_correction_delta: int
    generator_old_day_price: int
    generator_old_night_price: int
    generator_new_day_price: int
    generator_new_night_price: int

    @classmethod
    def from_env(cls) -> "Settings":
        """Создаёт конфигурацию из переменных окружения."""
        return cls(
            app_name=env("APP_NAME"),
            app_version=env("APP_VERSION"),
            app_host=env("APP_HOST"),
            app_port=int(env("APP_PORT")),
            clickhouse_host=env("CLICKHOUSE_HOST"),
            clickhouse_http_port=int(env("CLICKHOUSE_HTTP_PORT")),
            clickhouse_user=env("CLICKHOUSE_USER"),
            clickhouse_password=env("CLICKHOUSE_PASSWORD"),
            clickhouse_database=env("CLICKHOUSE_DATABASE"),
            http_timeout=float(env("HTTP_TIMEOUT")),
            max_request_bytes=int(env("MAX_REQUEST_BYTES")),
            data_dir=Path(env("DATA_DIR")),
            load_chunk_bytes=int(env("LOAD_CHUNK_BYTES")),
            generator_seed=int(env("GENERATOR_SEED")),
            generator_objects=int(env("GENERATOR_OBJECTS")),
            generator_commercial_step=int(env("GENERATOR_COMMERCIAL_STEP")),
            generator_objects_per_house=int(env("GENERATOR_OBJECTS_PER_HOUSE")),
            generator_square_min=int(env("GENERATOR_SQUARE_MIN")),
            generator_square_max=int(env("GENERATOR_SQUARE_MAX")),
            generator_rooms_min=int(env("GENERATOR_ROOMS_MIN")),
            generator_rooms_max=int(env("GENERATOR_ROOMS_MAX")),
            generator_floors=int(env("GENERATOR_FLOORS")),
            generator_day_usage_min=int(env("GENERATOR_DAY_USAGE_MIN")),
            generator_day_usage_max=int(env("GENERATOR_DAY_USAGE_MAX")),
            generator_night_usage_min=int(env("GENERATOR_NIGHT_USAGE_MIN")),
            generator_night_usage_max=int(env("GENERATOR_NIGHT_USAGE_MAX")),
            generator_invoice_deadline_day=int(env("GENERATOR_INVOICE_DEADLINE_DAY")),
            generator_tariff_name=env("GENERATOR_TARIFF_NAME"),
            generator_gauge_name=env("GENERATOR_GAUGE_NAME"),
            generator_replacement_gauge_name=env("GENERATOR_REPLACEMENT_GAUGE_NAME"),
            generator_gauge_country=env("GENERATOR_GAUGE_COUNTRY"),
            generator_start_date=date.fromisoformat(env("GENERATOR_START_DATE")),
            generator_end_date=date.fromisoformat(env("GENERATOR_END_DATE")),
            generator_tariff_change_date=date.fromisoformat(
                env("GENERATOR_TARIFF_CHANGE_DATE")
            ),
            generator_gauge_replacement_date=date.fromisoformat(
                env("GENERATOR_GAUGE_REPLACEMENT_DATE")
            ),
            generator_open_version_date=date.fromisoformat(
                env("GENERATOR_OPEN_VERSION_DATE")
            ),
            generator_replacement_step=int(env("GENERATOR_REPLACEMENT_STEP")),
            generator_gauge_offset=int(env("GENERATOR_GAUGE_OFFSET")),
            generator_correction_rate=float(env("GENERATOR_CORRECTION_RATE")),
            generator_correction_delta=int(env("GENERATOR_CORRECTION_DELTA")),
            generator_old_day_price=int(env("GENERATOR_OLD_DAY_PRICE")),
            generator_old_night_price=int(env("GENERATOR_OLD_NIGHT_PRICE")),
            generator_new_day_price=int(env("GENERATOR_NEW_DAY_PRICE")),
            generator_new_night_price=int(env("GENERATOR_NEW_NIGHT_PRICE")),
        )


load_env()
settings = Settings.from_env()
