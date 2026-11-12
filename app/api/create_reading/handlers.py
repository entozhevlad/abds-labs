from fastapi import APIRouter, Response

from app.api.dependencies import Service
from app.api.types import Identifier

from .schemas import CreateReadingRequest

router = APIRouter(tags=["Readings"])


@router.post("/realty/{id}/readings", status_code=201, response_class=Response)
def create_reading(
    id: Identifier, body: CreateReadingRequest, service: Service
) -> Response:
    service.create_reading(id, body.model_dump())
    return Response(status_code=201)
