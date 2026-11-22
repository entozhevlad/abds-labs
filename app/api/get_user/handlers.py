from fastapi import APIRouter

from app.api.dependencies import Service
from app.api.types import Identifier

from .schemas import UserResponse

router = APIRouter(tags=["Users"])


@router.get("/users/{id}", response_model=UserResponse)
def get_user(id: Identifier, service: Service) -> UserResponse:
    return UserResponse.model_validate(service.get_user(id))
