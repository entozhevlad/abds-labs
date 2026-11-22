from pydantic import BaseModel


class TariffResponse(BaseModel):
    id: int
    name: str
    price_day_kwph: int
    price_night_kwph: int
    valid_from: str
    valid_to: str
