"""
Модель пользователя (таблица users).
Пока используется один тестовый пользователь с id = 1 — от его имени ставятся лайки.
"""
from sqlalchemy import Column, Integer, String

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
