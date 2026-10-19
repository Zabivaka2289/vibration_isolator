"""
vibration_isolator: «guard» — аналог SessionGuard в NestJS.

В NestJS guard вешается декоратором @UseGuards(SessionGuard).
В FastAPI то же самое делает зависимость: если в параметрах обработчика есть
  user: VibrationIsolatorCurrentUser
то до вызова обработчика FastAPI:
  1) достанет куку vibration_isolator_session_id из запроса;
  2) найдёт сессию в Redis и пользователя в БД;
  3) если что-то не так — сразу ответит 401, обработчик не вызовется.

VibrationIsolatorModerator дополнительно проверяет роль (авторизация) → иначе 403.

APIKeyCookie нужен ещё и для Swagger: появляется кнопка Authorize с полем для куки
(аналог .addCookieAuth('sessionId')).
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie

from models.user import User
from modules.vibration_isolator_auth.vibration_isolator_auth_service import (
    VibrationIsolatorAuthService,
    get_vibration_isolator_auth_service,
)

# Имя куки с идентификатором сессии
VIBRATION_ISOLATOR_SESSION_COOKIE = "vibration_isolator_session_id"

vibration_isolator_cookie_scheme = APIKeyCookie(name=VIBRATION_ISOLATOR_SESSION_COOKIE, auto_error=False)


async def vibration_isolator_session_guard(
    session_id: str | None = Depends(vibration_isolator_cookie_scheme),
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
) -> User:
    """Аутентификация: кто ты? (401, если не вошёл)"""
    return await auth.validate_session(session_id)


async def vibration_isolator_moderator_guard(
    user: User = Depends(vibration_isolator_session_guard),
) -> User:
    """Авторизация: что тебе можно? (403, если не модератор)"""
    if user.role != "moderator":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Доступно только модератору")
    return user


# Короткие типы для обработчиков
VibrationIsolatorCurrentUser = Annotated[User, Depends(vibration_isolator_session_guard)]
VibrationIsolatorModerator = Annotated[User, Depends(vibration_isolator_moderator_guard)]
