"""add device tunnels

Revision ID: 0002_device_tunnels
Revises: 0001_init
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_device_tunnels"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "device_tunnels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(128), sa.ForeignKey("devices.device_id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("proxy_type", sa.String(16), nullable=False, server_default="tcp"),
        sa.Column("proxy_name", sa.String(128), nullable=False),
        sa.Column("local_ip", sa.String(64), nullable=False, server_default="127.0.0.1"),
        sa.Column("local_port", sa.Integer(), nullable=False),
        sa.Column("remote_port", sa.Integer(), nullable=False, unique=True),
        sa.Column("auth_token_encrypted", sa.Text(), nullable=False),
        sa.Column("internal_base_url", sa.Text(), nullable=False),
        sa.Column("public_base_url", sa.Text()),
        sa.Column("previous_base_url", sa.Text()),
        sa.Column("use_encryption", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("use_compression", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("last_config_generated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_device_tunnels_device_id", "device_tunnels", ["device_id"])
    op.create_index("ix_device_tunnels_remote_port", "device_tunnels", ["remote_port"])


def downgrade() -> None:
    op.drop_index("ix_device_tunnels_remote_port", table_name="device_tunnels")
    op.drop_index("ix_device_tunnels_device_id", table_name="device_tunnels")
    op.drop_table("device_tunnels")
