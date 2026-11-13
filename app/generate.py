import csv
import random
from contextlib import ExitStack
from datetime import timedelta

from app.config import settings

TABLES = (
    "dim_realty",
    "dim_gauges",
    "dim_tariffs",
    "dim_users",
    "fact_gauge_bindings",
    "fact_meter_readings",
    "fact_invoice",
)
START = settings.generator_start_date
END = settings.generator_end_date
CHANGE = settings.generator_tariff_change_date
REPLACEMENT = settings.generator_gauge_replacement_date
CREATED = f"{START} 00:00:00"


def generate() -> None:
    directory = settings.data_dir
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(settings.generator_seed)
    with ExitStack() as stack:
        writers = {
            name: csv.writer(
                stack.enter_context(
                    (directory / f"{name}.csv").open("w", newline="", encoding="utf-8")
                )
            )
            for name in TABLES
        }
        for start, end, day_price, night_price in (
            (
                START,
                CHANGE,
                settings.generator_old_day_price,
                settings.generator_old_night_price,
            ),
            (
                CHANGE,
                settings.generator_open_version_date,
                settings.generator_new_day_price,
                settings.generator_new_night_price,
            ),
        ):
            writers["dim_tariffs"].writerow(
                (
                    1,
                    settings.generator_tariff_name,
                    day_price,
                    night_price,
                    f"{start} 00:00:00",
                    f"{end} 00:00:00",
                    CREATED,
                    CREATED,
                )
            )
        days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
        corrections = 0
        for identifier in range(1, settings.generator_objects + 1):
            commercial = identifier % settings.generator_commercial_step == 0
            writers["dim_realty"].writerow(
                (
                    identifier,
                    "г. Москва, ул. Энергетиков, д. "
                    f"{(identifier - 1) // settings.generator_objects_per_house + 1}",
                    rng.randint(
                        settings.generator_square_min,
                        settings.generator_square_max,
                    ),
                    "nrcp" if commercial else "flat",
                    ""
                    if commercial
                    else str(
                        (identifier - 1) % settings.generator_objects_per_house + 1
                    ),
                    0
                    if commercial
                    else rng.randint(
                        settings.generator_rooms_min,
                        settings.generator_rooms_max,
                    ),
                    (identifier - 1) % settings.generator_floors + 1,
                    1,
                    CREATED,
                )
            )
            writers["dim_users"].writerow(
                (
                    identifier,
                    f"Иванов Иван {identifier}",
                    f"+7900{identifier:07d}",
                    "",
                    CREATED,
                    CREATED,
                )
            )
            writers["dim_gauges"].writerow(
                (
                    identifier,
                    settings.generator_gauge_name,
                    settings.generator_gauge_country,
                    CREATED,
                )
            )
            writers["fact_gauge_bindings"].writerow(
                (identifier, identifier, CREATED, 1, 1)
            )
            replaced = identifier % settings.generator_replacement_step == 0
            if replaced:
                writers["dim_gauges"].writerow(
                    (
                        settings.generator_gauge_offset + identifier,
                        settings.generator_replacement_gauge_name,
                        settings.generator_gauge_country,
                        f"{REPLACEMENT} 00:00:00",
                    )
                )
                writers["fact_gauge_bindings"].writerow(
                    (identifier, identifier, CREATED, -1, 1)
                )
                writers["fact_gauge_bindings"].writerow(
                    (
                        settings.generator_gauge_offset + identifier,
                        identifier,
                        f"{REPLACEMENT} 00:00:00",
                        1,
                        2,
                    )
                )
            day_total = night_total = month_day = month_night = 0
            for day in days:
                gauge = (
                    settings.generator_gauge_offset + identifier
                    if replaced and day >= REPLACEMENT
                    else identifier
                )
                if replaced and day == REPLACEMENT:
                    day_total = night_total = 0
                day_usage = rng.randint(
                    settings.generator_day_usage_min,
                    settings.generator_day_usage_max,
                )
                night_usage = rng.randint(
                    settings.generator_night_usage_min,
                    settings.generator_night_usage_max,
                )
                day_total += day_usage
                night_total += night_usage
                month_day += day_usage
                month_night += night_usage
                prefix = (identifier, identifier, 1, gauge, day.isoformat())
                # Ошибочную передачу заменяет фактическое показание.
                if rng.random() < settings.generator_correction_rate:
                    writers["fact_meter_readings"].writerow(
                        (
                            *prefix,
                            day_total + settings.generator_correction_delta,
                            night_total,
                            f"{day} 20:00:00",
                        )
                    )
                    corrections += 1
                writers["fact_meter_readings"].writerow(
                    (*prefix, day_total, night_total, f"{day} 21:00:00")
                )
                tomorrow = day + timedelta(days=1)
                if tomorrow.month != day.month:
                    day_price, night_price = (
                        (
                            settings.generator_old_day_price,
                            settings.generator_old_night_price,
                        )
                        if day < CHANGE
                        else (
                            settings.generator_new_day_price,
                            settings.generator_new_night_price,
                        )
                    )
                    writers["fact_invoice"].writerow(
                        (
                            identifier,
                            identifier,
                            1,
                            gauge,
                            month_day,
                            month_night,
                            month_day * day_price + month_night * night_price,
                            tomorrow.replace(
                                day=settings.generator_invoice_deadline_day
                            ),
                            f"{day} 23:00:00",
                        )
                    )
                    month_day = month_night = 0
        print(
            f"Generated {len(days) * settings.generator_objects:,} daily readings "
            f"+ {corrections:,} corrections",
            flush=True,
        )
