"""
vibration_isolator: модель заявки (таблица vibration_isolator_requests) — аналог Request в NestJS.

Заявка пользователя на подбор / поставку виброизолятора.
  title                  — заголовок заявки
  description            — текст (необязательно)
  status                 — 'pending' (на рассмотрении) / 'approved' (одобрена) / 'rejected' (отклонена)
  author_id              — автор, ставится АВТОМАТИЧЕСКИ из сессии (клиент его не передаёт)
  vibration_isolator_id  — какой виброизолятор нужен (необязательно)
created_at не добавляется.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base

VIBRATION_ISOLATOR_REQUEST_STATUSES = ("pending", "approved", "rejected")


class VibrationIsolatorRequest(Base):
    __tablename__ = "vibration_isolator_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vibration_isolator_id = Column(Integer, ForeignKey("vibration_isolators.id"), nullable=True)

    author = relationship("User", back_populates="vibration_isolator_requests")
