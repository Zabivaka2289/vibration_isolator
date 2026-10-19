"""
vibration_isolator: DTO для обновления (PUT) — аналог UpdateProductDto.

Все поля необязательные: меняются только те, что пришли в теле запроса.
Правила проверки те же, что при создании. Обязательные в БД поля
(title, type, stiffness, freq) нельзя «обнулить» значением null.
"""
from pydantic import ConfigDict, field_validator

from modules.vibration_isolator.dto.vibration_isolator_create_dto import VibrationIsolatorCreateDto


class VibrationIsolatorUpdateDto(VibrationIsolatorCreateDto):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = None
    type: str | None = None
    stiffness: int | None = None
    freq: float | None = None
    description: str | None = None
    video_url: str | None = None

    @field_validator("title", "type", "stiffness", "freq", mode="before")
    @classmethod
    def vibration_isolator_not_null(cls, v):
        # Валидатор вызывается только для полей, которые реально пришли в запросе
        if v is None:
            raise ValueError("Поле обязательное, null передавать нельзя")
        return v
