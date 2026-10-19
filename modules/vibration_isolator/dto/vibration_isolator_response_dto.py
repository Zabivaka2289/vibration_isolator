"""
vibration_isolator: DTO ответа (аналог ProductResponseDto в NestJS).

«Коробка», в которую кладём только то, что можно показать клиенту.
Поля is_deleted здесь НЕТ — клиент не должен видеть флаг удаления
(в NestJS для этого используется @Exclude()).
"""
from pydantic import BaseModel, ConfigDict


class VibrationIsolatorResponseDto(BaseModel):
    # from_attributes=True — можно собрать DTO прямо из объекта модели SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: str
    stiffness: int
    freq: float
    description: str | None = None
    image_url: str | None = None   # подписанная (временная) ссылка на картинку в MinIO
    video_url: str | None = None
