"""
vibration_isolator: сервис пользователей — аналог UserService в NestJS.
Только работа с таблицей users: создать, найти по email, найти по id.
"""
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User


class VibrationIsolatorUserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, password_hash: str, name: str | None, role: str = "user") -> User:
        user = User(username=email, email=email, password_hash=password_hash, name=name, role=role)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def find_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)


def get_vibration_isolator_user_service(db: AsyncSession = Depends(get_db)) -> VibrationIsolatorUserService:
    return VibrationIsolatorUserService(db)
