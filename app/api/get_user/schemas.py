from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    fio: str
    phone: str
    phone_prev: str
