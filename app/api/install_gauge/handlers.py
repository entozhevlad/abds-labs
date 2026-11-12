from fastapi import APIRouter, Response

from app.api.dependencies import Service
from app.api.types import Identifier

from .schemas import InstallGaugeRequest

router = APIRouter(tags=["Gauges"])


@router.post("/realty/{id}/gauges", status_code=201, response_class=Response)
def install_gauge(
    id: Identifier, body: InstallGaugeRequest, service: Service
) -> Response:
    service.install_gauge(id, body.gauge_id)
    return Response(status_code=201)
