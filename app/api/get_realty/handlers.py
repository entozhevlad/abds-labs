from fastapi import APIRouter

from app.api.dependencies import Service
from app.api.types import Identifier

from .schemas import RealtyResponse

router = APIRouter(tags=["Realty"])


@router.get("/realty/{id}", response_model=RealtyResponse)
def get_realty(id: Identifier, service: Service) -> RealtyResponse:
    return RealtyResponse.model_validate(service.get_realty(id))
