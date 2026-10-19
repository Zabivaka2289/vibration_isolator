"""
Базовый класс для всех моделей SQLAlchemy.
Все модели (VibrationIsolator, User, Like) наследуются от Base,
поэтому их таблицы попадают в общий Base.metadata, который читает Alembic.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
