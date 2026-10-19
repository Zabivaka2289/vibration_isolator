"""
vibration_isolator: контроллер заявок — аналог RequestController в NestJS.
Все маршруты защищены «guard'ом» сессии (нужна кука vibration_isolator_session_id).

  POST /api/vibration_isolator_requests              — создать заявку (автор из сессии)
  GET  /api/vibration_isolator_requests              — мои заявки (модератор — все)
  GET  /api/vibration_isolator_requests/{id}         — одна заявка (своя или модератор, иначе 403)
  PUT  /api/vibration_isolator_requests/{id}/status  — сменить статус (только модератор, иначе 403)
"""
from fastapi import APIRouter, Depends, status

from modules.vibration_isolator_auth.vibration_isolator_session_guard import (
    VibrationIsolatorCurrentUser,
    VibrationIsolatorModerator,
)
from modules.vibration_isolator_request.vibration_isolator_request_dto import (
    VibrationIsolatorRequestCreateDto,
    VibrationIsolatorRequestResponseDto,
    VibrationIsolatorRequestStatusDto,
)
from modules.vibration_isolator_request.vibration_isolator_request_service import (
    VibrationIsolatorRequestService,
    get_vibration_isolator_request_service,
)

vibration_isolator_request_router = APIRouter(prefix="/vibration_isolator_requests",
                                              tags=["vibration_isolator_requests"])


@vibration_isolator_request_router.post("", response_model=VibrationIsolatorRequestResponseDto,
                                        status_code=status.HTTP_201_CREATED)
async def vibration_isolator_create_request(
    dto: VibrationIsolatorRequestCreateDto,
    user: VibrationIsolatorCurrentUser,
    service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    # Автор берётся из сессии, а не из тела запроса
    return await service.create(dto, author_id=user.id)


@vibration_isolator_request_router.get("", response_model=list[VibrationIsolatorRequestResponseDto])
async def vibration_isolator_get_requests(
    user: VibrationIsolatorCurrentUser,
    service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    return await service.find_for_user(user)


@vibration_isolator_request_router.get("/{request_id}", response_model=VibrationIsolatorRequestResponseDto)
async def vibration_isolator_get_request(
    request_id: int,
    user: VibrationIsolatorCurrentUser,
    service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    return await service.find_one_for_user(request_id, user)


@vibration_isolator_request_router.put("/{request_id}/status", response_model=VibrationIsolatorRequestResponseDto)
async def vibration_isolator_set_request_status(
    request_id: int,
    dto: VibrationIsolatorRequestStatusDto,
    moderator: VibrationIsolatorModerator,
    service: VibrationIsolatorRequestService = Depends(get_vibration_isolator_request_service),
):
    return await service.set_status(request_id, dto.status)
