"""
vibration_isolator: контроллер аутентификации — аналог AuthController в NestJS.

  POST /api/vibration_isolator_auth/register  — регистрация (JSON), 201
  POST /api/vibration_isolator_auth/login     — вход: ставит куку vibration_isolator_session_id
  POST /api/vibration_isolator_auth/logout    — выход: удаляет сессию из Redis и куку
  GET  /api/vibration_isolator_auth/me        — кто я (нужна кука)
"""
from fastapi import APIRouter, Depends, Request, Response, status

from core.config import settings
from modules.vibration_isolator_auth.vibration_isolator_auth_dto import (
    VibrationIsolatorLoginDto,
    VibrationIsolatorRegisterDto,
    VibrationIsolatorUserResponseDto,
)
from modules.vibration_isolator_auth.vibration_isolator_auth_service import (
    VibrationIsolatorAuthService,
    get_vibration_isolator_auth_service,
)
from modules.vibration_isolator_auth.vibration_isolator_session_guard import (
    VIBRATION_ISOLATOR_SESSION_COOKIE,
    VibrationIsolatorCurrentUser,
)

vibration_isolator_auth_router = APIRouter(prefix="/vibration_isolator_auth", tags=["vibration_isolator_auth"])


def vibration_isolator_set_session_cookie(response: Response, session_id: str) -> None:
    """Кука сессии:
    httponly=True  — недоступна из JavaScript (защита от XSS);
    samesite=lax   — не отправляется с чужих сайтов при POST (защита от CSRF);
    secure=False   — работаем по http на localhost (в продакшене True);
    max_age        — живёт столько же, сколько сессия в Redis."""
    response.set_cookie(
        key=VIBRATION_ISOLATOR_SESSION_COOKIE,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.VIBRATION_ISOLATOR_SESSION_TTL,
        path="/",
    )


@vibration_isolator_auth_router.post("/register", response_model=VibrationIsolatorUserResponseDto,
                                     status_code=status.HTTP_201_CREATED)
async def vibration_isolator_register(
    dto: VibrationIsolatorRegisterDto,
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    return await auth.register(dto.email, dto.password, dto.name)


@vibration_isolator_auth_router.post("/login")
async def vibration_isolator_login(
    dto: VibrationIsolatorLoginDto,
    response: Response,
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    session_id, user = await auth.login(dto.email, dto.password)
    vibration_isolator_set_session_cookie(response, session_id)  # → заголовок Set-Cookie
    return {"user": VibrationIsolatorUserResponseDto.model_validate(user)}


@vibration_isolator_auth_router.post("/logout")
async def vibration_isolator_logout(
    request: Request,
    response: Response,
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    session_id = request.cookies.get(VIBRATION_ISOLATOR_SESSION_COOKIE)
    if session_id:
        await auth.logout(session_id)
    response.delete_cookie(VIBRATION_ISOLATOR_SESSION_COOKIE, path="/")
    return {"ok": True, "message": "Вы вышли из аккаунта"}


@vibration_isolator_auth_router.get("/me", response_model=VibrationIsolatorUserResponseDto)
async def vibration_isolator_me(user: VibrationIsolatorCurrentUser):
    return user
