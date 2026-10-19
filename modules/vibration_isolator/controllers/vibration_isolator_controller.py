"""
vibration_isolator: контроллер REST API — аналог ProductsController в NestJS.

Контроллер — «входная дверь» API: принимает HTTP-запрос, проверяет данные
через DTO, вызывает сервис и возвращает JSON.

Маршруты (с общим префиксом /api, как app.setGlobalPrefix('api')):
  GET    /api/vibration_isolators              — список + фильтры (query)
  GET    /api/vibration_isolators/{id}         — один виброизолятор
  POST   /api/vibration_isolators              — создать (JSON)
  PUT    /api/vibration_isolators/{id}         — обновить (JSON)
  DELETE /api/vibration_isolators/{id}         — мягко удалить
  POST   /api/vibration_isolators/{id}/image   — загрузить картинку в MinIO (form-data, ключ image)
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from modules.vibration_isolator.dto import (
    VibrationIsolatorCreateDto,
    VibrationIsolatorUpdateDto,
    VibrationIsolatorResponseDto,
    VibrationIsolatorFiltersDto,
)
from modules.vibration_isolator.services.vibration_isolator_service import VibrationIsolatorService
from modules.vibration_isolator.vibration_isolator_module import get_vibration_isolator_service

vibration_isolator_api_router = APIRouter(prefix="/vibration_isolators", tags=["vibration_isolator"])

# Тип-сокращение: сервис, который FastAPI сам создаст и подставит (как DI в NestJS)
VibrationIsolatorServiceDep = Annotated[VibrationIsolatorService, Depends(get_vibration_isolator_service)]


@vibration_isolator_api_router.get("", response_model=list[VibrationIsolatorResponseDto])
async def get_all_vibration_isolators(
    filters: Annotated[VibrationIsolatorFiltersDto, Query()],
    service: VibrationIsolatorServiceDep,
):
    return await service.find_all(filters)


@vibration_isolator_api_router.get("/{vibration_isolator_id}", response_model=VibrationIsolatorResponseDto)
async def get_vibration_isolator_by_id(vibration_isolator_id: int, service: VibrationIsolatorServiceDep):
    # vibration_isolator_id: int — FastAPI сам проверит, что это число (аналог ParseIntPipe)
    return await service.find_by_id(vibration_isolator_id)


@vibration_isolator_api_router.post("", response_model=VibrationIsolatorResponseDto,
                                    status_code=status.HTTP_201_CREATED)
async def create_vibration_isolator(dto: VibrationIsolatorCreateDto, service: VibrationIsolatorServiceDep):
    return await service.create(dto)


@vibration_isolator_api_router.put("/{vibration_isolator_id}", response_model=VibrationIsolatorResponseDto)
async def update_vibration_isolator(
    vibration_isolator_id: int, dto: VibrationIsolatorUpdateDto, service: VibrationIsolatorServiceDep
):
    return await service.update(vibration_isolator_id, dto)


@vibration_isolator_api_router.delete("/{vibration_isolator_id}")
async def delete_vibration_isolator(vibration_isolator_id: int, service: VibrationIsolatorServiceDep):
    await service.remove(vibration_isolator_id)
    return {
        "message": f"Виброизолятор с ID {vibration_isolator_id} успешно удалён",
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@vibration_isolator_api_router.post("/{vibration_isolator_id}/image", response_model=VibrationIsolatorResponseDto)
async def upload_vibration_isolator_image(
    vibration_isolator_id: int,
    service: VibrationIsolatorServiceDep,
    image: UploadFile | None = File(None),
):
    return await service.upload_image(vibration_isolator_id, image)
