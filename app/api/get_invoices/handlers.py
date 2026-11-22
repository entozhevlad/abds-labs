from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import Service
from app.api.types import Identifier, QueryUInt

from .schemas import InvoicesResponse

router = APIRouter(tags=["Invoices"])


@router.get("/realty/{id}/invoices", response_model=InvoicesResponse)
def get_invoices(
    id: Identifier,
    service: Service,
    limit: Annotated[QueryUInt, Query()] = 10,
    offset: Annotated[QueryUInt, Query()] = 0,
) -> InvoicesResponse:
    return InvoicesResponse.model_validate(service.get_invoices(id, limit, offset))
