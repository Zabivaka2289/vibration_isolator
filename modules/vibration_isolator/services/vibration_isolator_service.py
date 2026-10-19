"""
vibration_isolator: сервис с бизнес-логикой — аналог ProductsService в NestJS.

Бизнес-правила:
  1. Удаление — только мягкое (is_deleted = true).
  2. Удалённые записи не показываются в списках и по id (404).
  3. Удалённую запись нельзя обновить (400) и нельзя загрузить ей картинку.
  4. Жёсткость и частота > 0, название ≥ 3 символов, тип — из списка (проверяется в DTO).
  5. При загрузке новой картинки старая удаляется из MinIO.
  6. Клиенту отдаются подписанные ссылки на картинки, поле is_deleted не отдаётся.
"""
from fastapi import HTTPException, UploadFile, status

from models.vibration_isolator import VibrationIsolator
from modules.vibration_isolator.dto import (
    VibrationIsolatorCreateDto,
    VibrationIsolatorUpdateDto,
    VibrationIsolatorResponseDto,
    VibrationIsolatorFiltersDto,
)
from modules.vibration_isolator.repositories.vibration_isolator_repository import VibrationIsolatorRepository
from modules.vibration_isolator.services.vibration_isolator_minio_service import (
    VibrationIsolatorMinioService,
    VIBRATION_ISOLATOR_IMAGE_EXT,
)

VIBRATION_ISOLATOR_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 МБ


class VibrationIsolatorService:
    def __init__(self, repository: VibrationIsolatorRepository, minio: VibrationIsolatorMinioService):
        self.repository = repository
        self.minio = minio

    # ---- вспомогательное: модель БД → DTO ответа (без is_deleted, с подписанной ссылкой)
    async def _to_response(self, item: VibrationIsolator) -> VibrationIsolatorResponseDto:
        dto = VibrationIsolatorResponseDto.model_validate(item)
        dto.image_url = await self.minio.get_signed_url(item.image_url)
        return dto

    async def _get_active_or_404(self, vibration_isolator_id: int) -> VibrationIsolator:
        item = await self.repository.find_by_id(vibration_isolator_id)
        if item is None or item.is_deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                f"Виброизолятор с ID {vibration_isolator_id} не найден")
        return item

    # ---- GET список
    async def find_all(self, filters: VibrationIsolatorFiltersDto) -> list[VibrationIsolatorResponseDto]:
        items = await self.repository.find_all(filters)
        return [await self._to_response(item) for item in items]

    # ---- GET один
    async def find_by_id(self, vibration_isolator_id: int) -> VibrationIsolatorResponseDto:
        item = await self._get_active_or_404(vibration_isolator_id)
        return await self._to_response(item)

    # ---- POST
    async def create(self, dto: VibrationIsolatorCreateDto) -> VibrationIsolatorResponseDto:
        item = await self.repository.create(dto.model_dump())
        return await self._to_response(item)

    # ---- PUT
    async def update(self, vibration_isolator_id: int, dto: VibrationIsolatorUpdateDto) -> VibrationIsolatorResponseDto:
        item = await self.repository.find_by_id(vibration_isolator_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                f"Виброизолятор с ID {vibration_isolator_id} не найден")
        if item.is_deleted:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Нельзя обновлять удалённый виброизолятор")
        # exclude_unset — берём только поля, которые реально пришли в запросе
        data = dto.model_dump(exclude_unset=True)
        updated = await self.repository.update(vibration_isolator_id, data)
        return await self._to_response(updated)

    # ---- DELETE (мягкое)
    async def remove(self, vibration_isolator_id: int) -> None:
        await self._get_active_or_404(vibration_isolator_id)
        await self.repository.soft_delete(vibration_isolator_id)

    # ---- POST картинки в MinIO
    async def upload_image(self, vibration_isolator_id: int, image: UploadFile | None) -> VibrationIsolatorResponseDto:
        item = await self._get_active_or_404(vibration_isolator_id)

        if image is None or not image.filename:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Файл не предоставлен")
        if image.content_type not in VIBRATION_ISOLATOR_IMAGE_EXT:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Поддерживаются только изображения (jpg, jpeg, png, gif, webp)")
        data = await image.read()
        if len(data) > VIBRATION_ISOLATOR_MAX_IMAGE_SIZE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Размер файла больше 5 МБ")

        try:
            old_url = item.image_url
            new_url = await self.minio.upload_vibration_isolator_image(
                data, vibration_isolator_id, image.content_type
            )
            updated = await self.repository.update(vibration_isolator_id, {"image_url": new_url})
            if old_url:
                await self.minio.delete_file(old_url)  # старая картинка заменяется
        except HTTPException:
            raise
        except Exception as error:
            print("vibration_isolator: ошибка при загрузке изображения:", error)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "Не удалось загрузить изображение (проверьте, что MinIO запущен)")
        return await self._to_response(updated)
