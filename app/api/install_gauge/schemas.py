from pydantic import BaseModel

from app.api.types import UInt64


class InstallGaugeRequest(BaseModel):
    gauge_id: UInt64
