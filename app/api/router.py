from fastapi import APIRouter
from pydantic import BaseModel

from app.api.create_reading.handlers import router as create_reading_router
from app.api.get_invoices.handlers import router as get_invoices_router
from app.api.get_readings.handlers import router as get_readings_router
from app.api.get_realty.handlers import router as get_realty_router
from app.api.get_tariff.handlers import router as get_tariff_router
from app.api.get_user.handlers import router as get_user_router
from app.api.install_gauge.handlers import router as install_gauge_router
from app.api.ping.handlers import router as ping_router
from app.api.update_user.handlers import router as update_user_router


class ErrorResponse(BaseModel):
    message: str


router = APIRouter(
    responses={code: {"model": ErrorResponse} for code in (400, 404, 405, 500)}
)
router.include_router(ping_router)
router.include_router(get_user_router)
router.include_router(update_user_router)
router.include_router(get_realty_router)
router.include_router(create_reading_router)
router.include_router(get_readings_router)
router.include_router(get_invoices_router)
router.include_router(get_tariff_router)
router.include_router(install_gauge_router)
