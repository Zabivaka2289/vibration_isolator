"""
Подключение к базе данных.

engine              - асинхронный «движок», держит пул соединений с PostgreSQL
async_session_maker - фабрика сессий (одна сессия = одна единица работы с БД)
get_db()            - зависимость FastAPI: на каждый запрос открывает сессию,
                      отдаёт её в обработчик и закрывает после ответа
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты остаются доступными после commit()
)


async def get_db():
    async with async_session_maker() as session:
        yield session
