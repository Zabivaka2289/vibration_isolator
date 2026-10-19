"""vibration_isolator: auth fields for users + vibration_isolator_requests (ЛР-4)

1) users: добавлены email, password_hash, name, role; username расширен до 255.
   Уже существующий test_user (id = 1, из seed.sql) становится МОДЕРАТОРОМ:
       email: moderator@vibration.ru   пароль: 123
2) Новая таблица vibration_isolator_requests (заявки пользователей).
created_at не добавляется.

Revision ID: 0002
Revises: 0001
"""
import hashlib
import secrets
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _hash(password: str) -> str:
    # тот же формат, что в core/vibration_isolator_security.py
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"pbkdf2_sha256$200000${salt}${digest}"


def upgrade() -> None:
    # ---- 1. users ----
    op.alter_column("users", "username", type_=sa.String(length=255))
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))

    # Тестовый пользователь из ЛР-2 → модератор
    op.execute(sa.text(
        "UPDATE users SET email = 'moderator@vibration.ru', password_hash = :h, "
        "name = 'Модератор', role = 'moderator' WHERE username = 'test_user'"
    ).bindparams(h=_hash("123")))
    # Остальным старым записям (если вдруг есть) — email из username и пароль 123
    op.execute(sa.text(
        "UPDATE users SET email = username || '@vibration.local', password_hash = :h "
        "WHERE email IS NULL"
    ).bindparams(h=_hash("123")))

    op.alter_column("users", "email", nullable=False)
    op.alter_column("users", "password_hash", nullable=False)
    op.create_unique_constraint("uq_users_email", "users", ["email"])

    # ---- 2. vibration_isolator_requests ----
    op.create_table(
        "vibration_isolator_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vibration_isolator_id", sa.Integer(),
                  sa.ForeignKey("vibration_isolators.id"), nullable=True),
    )
    op.create_index("ix_vibration_isolator_requests_id", "vibration_isolator_requests", ["id"])


def downgrade() -> None:
    op.drop_index("ix_vibration_isolator_requests_id", table_name="vibration_isolator_requests")
    op.drop_table("vibration_isolator_requests")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "role")
    op.drop_column("users", "name")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
    op.alter_column("users", "username", type_=sa.String(length=50))
