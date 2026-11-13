from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import Service
from app.api.types import CalendarDateString

from .schemas import TariffResponse

router = APIRouter(tags=["Tariffs"])


@router.get("/tariffs", response_model=TariffResponse)
def get_tariff(
    service: Service, date: Annotated[CalendarDateString, Query()]
) -> TariffResponse:
    return TariffResponse.model_validate(service.get_tariff(date))
