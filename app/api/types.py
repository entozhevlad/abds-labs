import re
from datetime import date
from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, BeforeValidator, Field

UInt64 = Annotated[int, Field(strict=True, ge=0, lt=2**64)]
UInt32 = Annotated[int, Field(strict=True, ge=0, lt=2**32)]
Identifier = Annotated[int, Path(ge=0, lt=2**64)]


def valid_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if not date(1970, 1, 1) <= parsed <= date(2106, 2, 6):
        raise ValueError("Date out of range")
    return value


def nonempty(value: str) -> str:
    if not value.strip():
        raise ValueError("Empty string")
    return value


def query_uint(value: object) -> object:
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+", value):
            raise ValueError("Expected nonnegative integer")
        return int(value)
    return value


DateString = Annotated[str, Field(strict=True), AfterValidator(valid_date)]
NonemptyString = Annotated[str, Field(strict=True), AfterValidator(nonempty)]
QueryUInt = Annotated[UInt64, BeforeValidator(query_uint)]
