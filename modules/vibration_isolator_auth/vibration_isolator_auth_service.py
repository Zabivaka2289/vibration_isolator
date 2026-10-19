"""
vibration_isolator: сервис аутентификации — аналог AuthService в NestJS.

  register         — регистрация (роль всегда 'user', модератора через API не создать)
  login            — проверка email/пароля → новая сессия в Redis → sessionId
  logout           — удаление сессии из Redis
  validate_session — sessionId → пользователь (иначе 401)
"""
import secrets

from fastapi import Depends, HTTPException, status

from core.vibration_isolator_security import (
    vibration_isolator_hash_password,
    vibration_isolator_verify_password,
)
from models.user import User
from modules.vibration_isolator_session.vibration_isolator_session_service import (
    VibrationIsolatorSessionService,
    get_vibration_isolator_session_service,
)
from modules.vibration_isolator_user.vibration_isolator_user_service import (
    VibrationIsolatorUserService,
    get_vibration_isolator_user_service,
)


class VibrationIsolatorAuthService:
    def __init__(self, users: VibrationIsolatorUserService, sessions: VibrationIsolatorSessionService):
        self.users = users
        self.sessions = sessions

    async def register(self, email: str, password: str, name: str | None) -> User:
        if await self.users.find_by_email(email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким email уже существует")
        return await self.users.create(email, vibration_isolator_hash_password(password), name, role="user")

    async def login(self, email: str, password: str) -> tuple[str, User]:
        user = await self.users.find_by_email(email)
        if user is None or not vibration_isolator_verify_password(password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
        # Случайный, непредсказуемый идентификатор сессии
        session_id = secrets.token_urlsafe(32)
        await self.sessions.create(session_id, user.id)
        return session_id, user

    async def logout(self, session_id: str) -> None:
        await self.sessions.destroy(session_id)

    async def validate_session(self, session_id: str | None) -> User:
        if not session_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Нет куки сессии — выполните вход")
        user_id = await self.sessions.get_user_id(session_id)
        if user_id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Сессия недействительна или истекла")
        user = await self.users.find_by_id(user_id)
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден")
        return user


def get_vibration_isolator_auth_service(
    users: VibrationIsolatorUserService = Depends(get_vibration_isolator_user_service),
    sessions: VibrationIsolatorSessionService = Depends(get_vibration_isolator_session_service),
) -> VibrationIsolatorAuthService:
    return VibrationIsolatorAuthService(users, sessions)
