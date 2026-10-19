"""
vibration_isolator: модель пользователя (таблица users) — аналог User в NestJS (Sequelize).

ЛР-2: использовалась для лайков (тестовый пользователь id = 1).
ЛР-4: добавлены поля для регистрации / входа и ролевой модели.
  email          — логин, уникальный
  password_hash  — хеш пароля (PBKDF2 + соль). Сам пароль в БД НЕ хранится
  name           — отображаемое имя (необязательно)
  role           — 'user' или 'moderator', по умолчанию 'user'
  username       — оставлен из ЛР-2, при регистрации заполняется email
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from db.base import Base

VIBRATION_ISOLATOR_ROLES = ("user", "moderator")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="user", server_default="user")

    # Заявки пользователя (аналог @HasMany(() => Request))
    vibration_isolator_requests = relationship("VibrationIsolatorRequest", back_populates="author")
