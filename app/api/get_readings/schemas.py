from pydantic import BaseModel


class ReadingResponse(BaseModel):
    reading_date: str
    user_id: int
    tariff_id: int
    gauge_id: int
    day_kw: int
    night_kw: int


class ReadingsResponse(BaseModel):
    readings: list[ReadingResponse]
    count: int
