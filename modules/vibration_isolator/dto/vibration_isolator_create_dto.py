"""
vibration_isolator: DTO для создания (POST) — аналог CreateProductDto.

Валидация как у class-validator в NestJS:
  - title       — строка, не короче 3 символов (обязательно)
  - type        — только «Пружинный» или «Резинометаллический» (обязательно)
  - stiffness   — целое число > 0, Н/мм (обязательно)
  - freq        — число > 0, Гц (обязательно)
  - description — строка до 500 символов (необязательно)
  - video_url   — ссылка на видео (необязательно)
extra="forbid" — лишние поля запрещены (как forbidNonWhitelisted: true).
"""
from pydantic import BaseModel, ConfigDict, field_validator

# Допустимые типы виброизоляторов (бизнес-правило)
VIBRATION_ISOLATOR_TYPES = ("Пружинный", "Резинометаллический")


class VibrationIsolatorCreateDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str
    type: str
    stiffness: int
    freq: float
    description: str | None = None
    video_url: str | None = None

    @field_validator("title")
    @classmethod
    def vibration_isolator_check_title(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Название должно быть не менее 3 символов")
        if len(v) > 100:
            raise ValueError("Название должно быть не длиннее 100 символов")
        return v

    @field_validator("type")
    @classmethod
    def vibration_isolator_check_type(cls, v: str) -> str:
        if v not in VIBRATION_ISOLATOR_TYPES:
            raise ValueError("Тип должен быть «Пружинный» или «Резинометаллический»")
        return v

    @field_validator("stiffness")
    @classmethod
    def vibration_isolator_check_stiffness(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Жёсткость должна быть больше 0")
        return v

    @field_validator("freq")
    @classmethod
    def vibration_isolator_check_freq(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Собственная частота должна быть больше 0")
        return v

    @field_validator("description")
    @classmethod
    def vibration_isolator_check_description(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("Описание должно быть не длиннее 500 символов")
        return v
