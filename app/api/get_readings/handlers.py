from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import Service
from app.api.types import DateString, Identifier
from app.system.exceptions import invalid

from .schemas import ReadingsResponse

router = APIRouter(tags=["Readings"])


@router.get("/realty/{id}/readings", response_model=ReadingsResponse)
def get_readings(
    id: Identifier,
    service: Service,
    date_from: Annotated[DateString, Query()],
    date_to: Annotated[DateString, Query()],
) -> ReadingsResponse:
    if date_from > date_to:
        invalid("date_to", "parameter")
    return ReadingsResponse.model_validate(service.get_readings(id, date_from, date_to))
