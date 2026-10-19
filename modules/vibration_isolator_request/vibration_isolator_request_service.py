"""
vibration_isolator: сервис заявок — аналог RequestService в NestJS.

Правила доступа (ролевая модель):
  user       — создаёт заявки, видит и открывает ТОЛЬКО свои;
  moderator  — видит все заявки и меняет их статус.
Автор заявки всегда = пользователь из сессии.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User
from models.vibration_isolator import VibrationIsolator
from models.vibration_isolator_request import VibrationIsolatorRequest
from modules.vibration_isolator_request.vibration_isolator_request_dto import VibrationIsolatorRequestCreateDto


class VibrationIsolatorRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, dto: VibrationIsolatorRequestCreateDto, author_id: int) -> VibrationIsolatorRequest:
        if dto.vibration_isolator_id is not None:
            item = await self.db.get(VibrationIsolator, dto.vibration_isolator_id)
            if item is None or item.is_deleted:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"Виброизолятор с ID {dto.vibration_isolator_id} не найден")
        request = VibrationIsolatorRequest(**dto.model_dump(), author_id=author_id, status="pending")
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def find_all_by_author(self, author_id: int) -> list[VibrationIsolatorRequest]:
        result = await self.db.execute(
            select(VibrationIsolatorRequest)
            .where(VibrationIsolatorRequest.author_id == author_id)
            .order_by(VibrationIsolatorRequest.id)
        )
        return list(result.scalars().all())

    async def find_all(self) -> list[VibrationIsolatorRequest]:
        result = await self.db.execute(select(VibrationIsolatorRequest).order_by(VibrationIsolatorRequest.id))
        return list(result.scalars().all())

    async def find_for_user(self, user: User) -> list[VibrationIsolatorRequest]:
        """Модератор — все заявки, обычный пользователь — только свои."""
        if user.role == "moderator":
            return await self.find_all()
        return await self.find_all_by_author(user.id)

    async def find_one_for_user(self, request_id: int, user: User) -> VibrationIsolatorRequest:
        request = await self.db.get(VibrationIsolatorRequest, request_id)
        if request is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Заявка с ID {request_id} не найдена")
        if request.author_id != user.id and user.role != "moderator":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа к чужой заявке")
        return request

    async def set_status(self, request_id: int, new_status: str) -> VibrationIsolatorRequest:
        request = await self.db.get(VibrationIsolatorRequest, request_id)
        if request is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Заявка с ID {request_id} не найдена")
        request.status = new_status
        await self.db.commit()
        await self.db.refresh(request)
        return request


def get_vibration_isolator_request_service(db: AsyncSession = Depends(get_db)) -> VibrationIsolatorRequestService:
    return VibrationIsolatorRequestService(db)
