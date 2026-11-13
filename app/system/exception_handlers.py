import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.system.exceptions import ApiError


def install_exception_handlers(app: FastAPI) -> None:
    """Регистрирует преобразование исключений в HTTP-ответы."""

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse({"message": exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error = exc.errors()[0]
        location = error["loc"]
        if error["type"] in ("json_invalid", "model_attributes_type"):
            message = "invalid JSON body"
        else:
            name = location[1] if len(location) > 1 else "fio"
            kind = "parameter" if location[0] == "query" else "field"
            message = f'invalid "{name}" {kind}'
        return JSONResponse({"message": message}, status_code=400)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        message = "Not found" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse({"message": message}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).error("Request failed", exc_info=exc)
        return JSONResponse({"message": "Internal server error"}, status_code=500)
