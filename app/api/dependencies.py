from typing import Annotated, cast

from fastapi import Depends, Request

from app.containers import Container
from app.services.energosbyt import EnergosbytService


def get_service(request: Request) -> EnergosbytService:
    container = cast(Container, request.app.state.container)
    return container.service()


Service = Annotated[EnergosbytService, Depends(get_service)]
