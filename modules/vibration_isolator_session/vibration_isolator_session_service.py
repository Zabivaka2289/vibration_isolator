"""
vibration_isolator: сервис сессий в Redis — аналог SessionService в NestJS.

Как устроена сессия:
  1. При входе генерируется случайный sessionId.
  2. В Redis пишется запись   vibration_isolator_session:<sessionId> → <userId>
     со сроком жизни (TTL) 1 час — по истечении Redis сам удалит её.
  3. sessionId отдаётся браузеру в куке vibration_isolator_session_id (HttpOnly).
  4. На каждый запрос сервер берёт sessionId из куки и ищет userId в Redis.
  5. При выходе запись удаляется → кука сразу перестаёт работать.

Почему Redis, а не память процесса: сессии переживают перезапуск сервера
и доступны нескольким экземплярам приложения.
"""
from functools import lru_cache

from redis.asyncio import Redis

from core.config import settings

VIBRATION_ISOLATOR_SESSION_PREFIX = "vibration_isolator_session:"


class VibrationIsolatorSessionService:
    def __init__(self):
        self.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"{VIBRATION_ISOLATOR_SESSION_PREFIX}{session_id}"

    async def create(self, session_id: str, user_id: int,
                     ttl_sec: int = settings.VIBRATION_ISOLATOR_SESSION_TTL) -> None:
        """Создаёт сессию: SETEX ключ TTL значение."""
        await self.redis.setex(self._key(session_id), ttl_sec, str(user_id))

    async def get_user_id(self, session_id: str) -> int | None:
        """userId по sessionId или None, если сессии нет / истекла."""
        value = await self.redis.get(self._key(session_id))
        return int(value) if value else None

    async def destroy(self, session_id: str) -> None:
        """Удаляет сессию (logout)."""
        await self.redis.delete(self._key(session_id))

    async def exists(self, session_id: str) -> bool:
        return await self.redis.exists(self._key(session_id)) == 1


@lru_cache
def get_vibration_isolator_session_service() -> VibrationIsolatorSessionService:
    # Один клиент Redis на всё приложение (как @Global() модуль в NestJS)
    return VibrationIsolatorSessionService()
