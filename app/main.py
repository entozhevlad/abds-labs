import uvicorn
from fastapi import FastAPI

from app.api.router import router
from app.config import settings
from app.containers import Container
from app.system.exception_handlers import install_exception_handlers
from app.system.middleware import RequestLimitsMiddleware


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.container = container if container is not None else Container()
    app.include_router(router)
    install_exception_handlers(app)
    app.add_middleware(RequestLimitsMiddleware, max_bytes=settings.max_request_bytes)

    # The contract uses 400 rather than FastAPI's automatically documented 422.
    schema = app.openapi()
    for path in schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.get("responses", {}).pop("422", None)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host=settings.app_host, port=settings.app_port)
