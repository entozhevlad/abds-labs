from fastapi import APIRouter, Response

from app.api.dependencies import Service
from app.api.types import Identifier

from .schemas import UpdateUserRequest

router = APIRouter(tags=["Users"])


@router.patch("/users/{id}", status_code=204, response_class=Response)
def update_user(id: Identifier, body: UpdateUserRequest, service: Service) -> Response:
    service.update_user(id, body.model_dump(exclude_unset=True))
    return Response(status_code=204)
