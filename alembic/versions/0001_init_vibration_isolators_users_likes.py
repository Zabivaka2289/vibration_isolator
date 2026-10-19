"""init vibration_isolators, users and likes tables

Создаёт 3 таблицы:
  vibration_isolators — услуги (виброизоляторы), с флагом мягкого удаления is_deleted
  users               — пользователи
  likes               — лайки (связь многие-ко-многим users <-> vibration_isolators)
Поля created_at нет — оно не требуется.

Revision ID: 0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vibration_isolators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("stiffness", sa.Integer(), nullable=False),
        sa.Column("freq", sa.Float(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("video_url", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_vibration_isolators_id", "vibration_isolators", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
    )
    op.create_index("ix_users_id", "users", ["id"])

    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vibration_isolator_id", sa.Integer(),
                  sa.ForeignKey("vibration_isolators.id"), nullable=False),
    )
    op.create_index("ix_likes_id", "likes", ["id"])


def downgrade() -> None:
    op.drop_index("ix_likes_id", table_name="likes")
    op.drop_table("likes")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_vibration_isolators_id", table_name="vibration_isolators")
    op.drop_table("vibration_isolators")
