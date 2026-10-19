"""
vibration_isolator: DTO аутентификации — аналог LoginDto / RegisterDto в NestJS.
Пример значений (json_schema_extra) показывается в Swagger, как @ApiProperty({ example }).
"""
import re

from pydantic import BaseModel, ConfigDict, field_validator

VIBRATION_ISOLATOR_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class VibrationIsolatorRegisterDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, json_schema_extra={
        "example": {"email": "user@test.com", "password": "123", "name": "Test User"}
    })

    email: str
    password: str
    name: str | None = None

    @field_validator("email")
    @classmethod
    def vibration_isolator_check_email(cls, v: str) -> str:
        if not VIBRATION_ISOLATOR_EMAIL_RE.match(v):
            raise ValueError("Некорректный email")
        return v.lower()

    @field_validator("password")
    @classmethod
    def vibration_isolator_check_password(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Пароль должен быть не короче 3 символов")
        return v


class VibrationIsolatorLoginDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, json_schema_extra={
        "example": {"email": "user@test.com", "password": "123"}
    })

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def vibration_isolator_lower_email(cls, v: str) -> str:
        return v.lower()


class VibrationIsolatorUserResponseDto(BaseModel):
    """Что отдаём о пользователе. Хеша пароля здесь НЕТ."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    role: str
