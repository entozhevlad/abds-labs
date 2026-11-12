from pydantic import BaseModel

from app.api.types import DateString, UInt32, UInt64


class CreateReadingRequest(BaseModel):
    user_id: UInt64
    gauge_id: UInt64
    tariff_id: UInt64
    reading_date: DateString
    day_kw: UInt32
    night_kw: UInt32
