"""
vibration_isolator: репозиторий — аналог TypeORMProductsRepository в NestJS.

Репозиторий — «посредник» между сервисом и БД:
  - выполняет запросы через SQLAlchemy;
  - возвращает объекты модели VibrationIsolator;
  - прячет SQL от бизнес-логики.
Никаких проверок и правил тут нет — они в сервисе.
"""
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.vibration_isolator import VibrationIsolator
from modules.vibration_isolator.dto.vibration_isolator_filters_dto import VibrationIsolatorFiltersDto


class VibrationIsolatorRepository:
    def __init__(self, db: AsyncSession):
        # Сессия БД приходит через внедрение зависимостей (Depends), как @InjectRepository
        self.db = db

    async def find_all(self, filters: VibrationIsolatorFiltersDto) -> list[VibrationIsolator]:
        """Список с фильтрами (аналог createQueryBuilder в TypeORM)."""
        query = select(VibrationIsolator)

        if not filters.include_deleted:
            query = query.where(VibrationIsolator.is_deleted == False)  # noqa: E712

        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.where(or_(
                VibrationIsolator.title.ilike(pattern),
                VibrationIsolator.description.ilike(pattern),
            ))
        if filters.type:
            query = query.where(VibrationIsolator.type == filters.type)
        if filters.min_stiffness is not None:
            query = query.where(VibrationIsolator.stiffness >= filters.min_stiffness)
        if filters.max_stiffness is not None:
            query = query.where(VibrationIsolator.stiffness <= filters.max_stiffness)
        if filters.min_freq is not None:
            query = query.where(VibrationIsolator.freq >= filters.min_freq)
        if filters.max_freq is not None:
            query = query.where(VibrationIsolator.freq <= filters.max_freq)

        result = await self.db.execute(query.order_by(VibrationIsolator.id))
        return list(result.scalars().all())

    async def find_by_id(self, vibration_isolator_id: int) -> VibrationIsolator | None:
        """Одна запись по id (в том числе удалённая — решает сервис)."""
        return await self.db.get(VibrationIsolator, vibration_isolator_id)

    async def create(self, data: dict) -> VibrationIsolator:
        item = VibrationIsolator(**data, is_deleted=False)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(self, vibration_isolator_id: int, data: dict) -> VibrationIsolator:
        if data:
            await self.db.execute(
                update(VibrationIsolator)
                .where(VibrationIsolator.id == vibration_isolator_id)
                .values(**data)
            )
            await self.db.commit()
        item = await self.find_by_id(vibration_isolator_id)
        await self.db.refresh(item)  # перечитываем свежие значения из БД
        return item

    async def soft_delete(self, vibration_isolator_id: int) -> None:
        """Мягкое удаление: запись остаётся в таблице, меняется только флаг."""
        await self.db.execute(
            update(VibrationIsolator)
            .where(VibrationIsolator.id == vibration_isolator_id)
            .values(is_deleted=True)
        )
        await self.db.commit()
