from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    tariff_id: int
    gauge_id: int
    day_kw: int
    night_kw: int
    price: int
    deadline: str
    created_at: str


class InvoicesResponse(BaseModel):
    invoices: list[InvoiceResponse]
    count: int
