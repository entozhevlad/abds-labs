from fastapi import APIRouter, Response

router = APIRouter(tags=["Health"])


@router.get("/ping", response_class=Response)
def ping() -> Response:
    return Response(status_code=200)
