"""
vibration_isolator: HTML-страницы входа, регистрации и профиля (ЛР-4)
— аналог login.hbs / profile.hbs + AppController в NestJS (вместо Handlebars — Jinja2).

  GET  /login                             — форма входа
  POST /login                             — вход: кука vibration_isolator_session_id → редирект на /profile
  GET  /register, POST /register          — регистрация
  GET  /profile                           — профиль + заявки (без куки → редирект на /login)
  POST /profile/requests                  — создать заявку из формы
  POST /profile/requests/{id}/status      — модератор меняет статус
  POST /logout                            — выход: сессия удаляется из Redis, кука стирается
"""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.vibration_isolator import VibrationIsolator
from modules.vibration_isolator_auth.vibration_isolator_auth_controller import (
    vibration_isolator_set_session_cookie,
)
from modules.vibration_isolator_auth.vibration_isolator_auth_dto import VibrationIsolatorRegisterDto
from modules.vibration_isolator_auth.vibration_isolator_auth_service import (
    VibrationIsolatorAuthService,
    get_vibration_isolator_auth_service,
)
from modules.vibration_isolator_auth.vibration_isolator_session_guard import VIBRATION_ISOLATOR_SESSION_COOKIE
from modules.vibration_isolator_request.vibration_isolator_request_dto import VibrationIsolatorRequestCreateDto
from modules.vibration_isolator_request.vibration_isolator_request_service import (
    VibrationIsolatorRequestService,
    get_vibration_isolator_request_service,
)
from models.vibration_isolator_request import VIBRATION_ISOLATOR_REQUEST_STATUSES

vibration_isolator_auth_pages_router = APIRouter()
vibration_isolator_auth_templates = Jinja2Templates(directory="templates")

VIBRATION_ISOLATOR_STATUS_LABELS = {"pending": "На рассмотрении", "approved": "Одобрена", "rejected": "Отклонена"}


async def vibration_isolator_page_user(request: Request, auth: VibrationIsolatorAuthService):
    """Пользователь по куке или None (для страниц: вместо 401 — редирект на /login)."""
    try:
        return await auth.validate_session(request.cookies.get(VIBRATION_ISOLATOR_SESSION_COOKIE))
    except HTTPException:
        return None


# ---------------------------------------------------------------------------
# vibration_isolator: Вход
# ---------------------------------------------------------------------------
@vibration_isolator_auth_pages_router.get("/login", include_in_schema=False)
async def vibration_isolator_login_page(request: Request, registered: int = 0):
    return vibration_isolator_auth_templates.TemplateResponse(
        request=request, name="vibration_isolator_login.html",
        context={"error": None, "email": "", "registered": registered},
    )


@vibration_isolator_auth_pages_router.post("/login", include_in_schema=False)
async def vibration_isolator_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    try:
        session_id, _ = await auth.login(email.strip().lower(), password)
    except HTTPException as error:
        return vibration_isolator_auth_templates.TemplateResponse(
            request=request, name="vibration_isolator_login.html",
            context={"error": error.detail, "email": email, "registered": 0}, status_code=401,
        )
    response = RedirectResponse("/profile", status_code=303)
    vibration_isolator_set_session_cookie(response, session_id)
    return response


# ---------------------------------------------------------------------------
# vibration_isolator: Регистрация
# ---------------------------------------------------------------------------
@vibration_isolator_auth_pages_router.get("/register", include_in_schema=False)
async def vibration_isolator_register_page(request: Request):
    return vibration_isolator_auth_templates.TemplateResponse(
        request=request, name="vibration_isolator_register.html",
        context={"error": None, "email": "", "name": ""},
    )


@vibration_isolator_auth_pages_router.post("/register", include_in_schema=False)
async def vibration_isolator_register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(""),
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    try:
        dto = VibrationIsolatorRegisterDto(email=email, password=password, name=name or None)
        await auth.register(dto.email, dto.password, dto.name)
    except (ValidationError, HTTPException) as error:
        message = (error.detail if isinstance(error, HTTPException)
                   else error.errors()[0]["msg"].removeprefix("Value error, "))
        return vibration_isolator_auth_templates.TemplateResponse(
            request=request, name="vibration_isolator_register.html",
            context={"error": message, "email": email, "name": name}, status_code=400,
        )
    return RedirectResponse("/login?registered=1", status_code=303)


# ---------------------------------------------------------------------------
# vibration_isolator: Профиль и заявки
# ---------------------------------------------------------------------------
@vibration_isolator_auth_pages_router.get("/profile", include_in_schema=False)
async def vibration_isolator_profile_page(
    request: Request,
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
    requests_service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
    db: AsyncSession = Depends(get_db),
    error: str = "",
):
    user = await vibration_isolator_page_user(request, auth)
    if user is None:
        return RedirectResponse("/login", status_code=303)  # нет сессии → на вход

    user_requests = await requests_service.find_for_user(user)
    isolators = (await db.execute(
        select(VibrationIsolator).where(VibrationIsolator.is_deleted == False)  # noqa: E712
        .order_by(VibrationIsolator.id)
    )).scalars().all()

    return vibration_isolator_auth_templates.TemplateResponse(
        request=request, name="vibration_isolator_profile.html",
        context={
            "user": user,
            "vibration_isolator_requests": user_requests,
            "vibration_isolators": isolators,
            "isolator_titles": {i.id: i.title for i in isolators},
            "status_labels": VIBRATION_ISOLATOR_STATUS_LABELS,
            "statuses": VIBRATION_ISOLATOR_REQUEST_STATUSES,
            "error": error,
        },
    )


@vibration_isolator_auth_pages_router.post("/profile/requests", include_in_schema=False)
async def vibration_isolator_profile_create_request(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    vibration_isolator_id: str = Form(""),
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
    requests_service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    user = await vibration_isolator_page_user(request, auth)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    try:
        dto = VibrationIsolatorRequestCreateDto(
            title=title, description=description or None,
            vibration_isolator_id=int(vibration_isolator_id) if vibration_isolator_id else None,
        )
        await requests_service.create(dto, author_id=user.id)
    except (ValidationError, HTTPException) as error:
        message = (error.detail if isinstance(error, HTTPException)
                   else error.errors()[0]["msg"].removeprefix("Value error, "))
        return RedirectResponse(f"/profile?error={message}", status_code=303)
    return RedirectResponse("/profile", status_code=303)


@vibration_isolator_auth_pages_router.post("/profile/requests/{request_id}/status", include_in_schema=False)
async def vibration_isolator_profile_set_status(
    request: Request,
    request_id: int,
    status: str = Form(...),
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
    requests_service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    user = await vibration_isolator_page_user(request, auth)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "moderator" or status not in VIBRATION_ISOLATOR_REQUEST_STATUSES:
        return RedirectResponse("/profile?error=Менять статус может только модератор", status_code=303)
    await requests_service.set_status(request_id, status)
    return RedirectResponse("/profile", status_code=303)


# ---------------------------------------------------------------------------
# vibration_isolator: Выход
# ---------------------------------------------------------------------------
@vibration_isolator_auth_pages_router.post("/logout", include_in_schema=False)
async def vibration_isolator_logout_submit(
    request: Request,
    auth: VibrationIsolatorAuthService = Depends(get_vibration_isolator_auth_service),
):
    session_id = request.cookies.get(VIBRATION_ISOLATOR_SESSION_COOKIE)
    if session_id:
        await auth.logout(session_id)  # удаляем сессию из Redis
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(VIBRATION_ISOLATOR_SESSION_COOKIE, path="/")
    return response
