from pydantic import BaseModel


class RealtyResponse(BaseModel):
    id: int
    address: str
    square: int
    type: str
    number: str
    rooms: int
    floor: int
    porch: int
