"""
Модель услуги — виброизолятор (таблица vibration_isolators).

Обязательные поля (NOT NULL): title, type, stiffness, freq, is_deleted.
Необязательные поля (NULL допускается): description, image_url, video_url —
их можно не заполнять на странице «Добавить».
Поле created_at НЕ добавляется (не требуется по заданию).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean

from db.base import Base


class VibrationIsolator(Base):
    __tablename__ = "vibration_isolators"

    id = Column(Integer, primary_key=True, index=True)          # первичный ключ
    title = Column(String(100), nullable=False)                  # название, напр. «Пружинный АР-120»
    type = Column(String(50), nullable=False)                    # тип: Пружинный / Резинометаллический
    stiffness = Column(Integer, nullable=False)                  # жёсткость, Н/мм
    freq = Column(Float, nullable=False)                         # собственная частота, Гц
    description = Column(String(500), nullable=True)             # описание (необязательно)
    image_url = Column(String(255), nullable=True)               # ссылка на фото (необязательно)
    video_url = Column(String(255), nullable=True)               # ссылка на видео (необязательно)
    is_deleted = Column(Boolean, nullable=False, default=False,  # флаг мягкого удаления
                        server_default="false")
