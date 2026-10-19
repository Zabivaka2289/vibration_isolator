"""
vibration_isolator: «модуль» — аналог ProductsModule в NestJS.

В NestJS модуль связывает контроллер, сервис и репозиторий через @Module({providers: [...]}).
В FastAPI ту же роль играют функции-зависимости (Depends):
  get_db()  →  VibrationIsolatorRepository  →  VibrationIsolatorService  ←  VibrationIsolatorMinioService
FastAPI сам вызывает эти функции на каждый запрос и передаёт готовый сервис в контроллер.
"""
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from modules.vibration_isolator.repositories.vibration_isolator_repository import VibrationIsolatorRepository
from modules.vibration_isolator.services.vibration_isolator_minio_service import VibrationIsolatorMinioService
from modules.vibration_isolator.services.vibration_isolator_service import VibrationIsolatorService


def get_vibration_isolator_repository(db: AsyncSession = Depends(get_db)) -> VibrationIsolatorRepository:
    return VibrationIsolatorRepository(db)


@lru_cache
def get_vibration_isolator_minio_service() -> VibrationIsolatorMinioService:
    # Один клиент MinIO на всё приложение (singleton, как провайдер NestJS по умолчанию)
    return VibrationIsolatorMinioService()


def get_vibration_isolator_service(
    repository: VibrationIsolatorRepository = Depends(get_vibration_isolator_repository),
    minio: VibrationIsolatorMinioService = Depends(get_vibration_isolator_minio_service),
) -> VibrationIsolatorService:
    return VibrationIsolatorService(repository, minio)
