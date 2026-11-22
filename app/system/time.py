from datetime import UTC, datetime, timedelta


def timestamp(previous: str | None = None) -> str:
    """Создаёт монотонную временную метку версии."""
    now = datetime.now(UTC).replace(tzinfo=None, microsecond=0)
    if previous:
        now = max(now, datetime.fromisoformat(previous) + timedelta(seconds=1))
    return now.strftime("%Y-%m-%d %H:%M:%S")
