"""
vibration_isolator: DTO заявок — аналог CreateRequestDto в NestJS.
author_id в DTO создания НЕТ — автор всегда берётся из сессии.
"""
from pydantic import BaseModel, ConfigDict, field_validator

from models.vibration_isolator_request import VIBRATION_ISOLATOR_REQUEST_STATUSES


class VibrationIsolatorRequestCreateDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, json_schema_extra={
        "example": {"title": "Заявка на виброизолятор для насоса",
                    "description": "Нужно 4 шт. под насос 120 кг", "vibration_isolator_id": 1}
    })

    title: str
    description: str | None = None
    vibration_isolator_id: int | None = None

    @field_validator("title")
    @classmethod
    def vibration_isolator_check_title(cls, v: str) -> str:
        if not 3 <= len(v) <= 200:
            raise ValueError("Заголовок должен быть от 3 до 200 символов")
        return v


class VibrationIsolatorRequestStatusDto(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"status": "approved"}})

    status: str

    @field_validator("status")
    @classmethod
    def vibration_isolator_check_status(cls, v: str) -> str:
        if v not in VIBRATION_ISOLATOR_REQUEST_STATUSES:
            raise ValueError("Статус должен быть pending, approved или rejected")
        return v


class VibrationIsolatorRequestResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: str
    author_id: int
    vibration_isolator_id: int | None = None
