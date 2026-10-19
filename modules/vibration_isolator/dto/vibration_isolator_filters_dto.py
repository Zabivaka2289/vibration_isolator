"""
vibration_isolator: DTO фильтров для GET-списка — аналог ProductFiltersDto.

Все параметры передаются в query-строке и необязательны, их можно комбинировать:
  /api/vibration_isolators?search=пруж&type=Пружинный&min_stiffness=30&max_stiffness=80
"""
from pydantic import BaseModel, ConfigDict, Field


class VibrationIsolatorFiltersDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: str | None = None                  # поиск по названию и описанию (ILIKE)
    type: str | None = None                    # точное совпадение типа
    min_stiffness: int | None = Field(None, ge=0)
    max_stiffness: int | None = Field(None, ge=0)
    min_freq: float | None = Field(None, ge=0)
    max_freq: float | None = Field(None, ge=0)
    include_deleted: bool = False              # показать и мягко удалённые
