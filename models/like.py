"""
Модель лайка (таблица likes) — связь «многие-ко-многим»
между пользователями (users) и виброизоляторами (vibration_isolators).
Одна строка = «пользователь user_id лайкнул виброизолятор vibration_isolator_id».
"""
from sqlalchemy import Column, Integer, ForeignKey

from db.base import Base


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vibration_isolator_id = Column(Integer, ForeignKey("vibration_isolators.id"), nullable=False)
