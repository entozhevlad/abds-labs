from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.api.types import NonemptyString


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fio: NonemptyString | None = None
    phone: NonemptyString | None = None

    @field_validator("fio", "phone", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Explicit null is not allowed")
        return value

    @model_validator(mode="after")
    def require_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self
