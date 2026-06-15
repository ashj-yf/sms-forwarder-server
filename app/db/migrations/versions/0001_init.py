"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(128), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(128), nullable=False, unique=True),
        sa.Column("device_name", sa.String(255)),
        sa.Column("channel_type", sa.String(64), nullable=False, server_default="hybrid"),
        sa.Column("base_url", sa.Text()),
        sa.Column("sign_secret_encrypted", sa.Text()),
        sa.Column("sm4_key_encrypted", sa.Text()),
        sa.Column("rsa_public_key", sa.Text()),
        sa.Column("platform", sa.String(64)),
        sa.Column("app_version", sa.String(64)),
        sa.Column("protocol_version", sa.String(32)),
        sa.Column("status", sa.String(32), nullable=False, server_default="inactive"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_webhook_at", sa.DateTime(timezone=True)),
        sa.Column("webhook_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"])
    op.create_table(
        "device_webhooks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(128), sa.ForeignKey("devices.device_id"), nullable=False),
        sa.Column("webhook_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("webhook_token_prefix", sa.String(16), nullable=False),
        sa.Column("webhook_secret_encrypted", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_called_at", sa.DateTime(timezone=True)),
        sa.Column("called_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_device_webhooks_prefix", "device_webhooks", ["webhook_token_prefix"])
    op.create_table(
        "device_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True)),
        sa.Column("normalized_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("source_ip", sa.String(64)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("device_id", "event_id", name="uq_device_events_device_event"),
    )
    op.create_index("idx_device_events_device_id", "device_events", ["device_id"])
    op.create_index("idx_device_events_event_type", "device_events", ["event_type"])
    op.create_index("idx_device_events_created_at", "device_events", ["created_at"])
    op.create_table(
        "device_capabilities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("capability", sa.String(128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("device_id", "capability", name="uq_device_cap"),
    )
    op.create_index("ix_device_capabilities_device_id", "device_capabilities", ["device_id"])
    op.create_table(
        "device_command_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(128), nullable=False, unique=True),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("command_type", sa.String(128), nullable=False),
        sa.Column("channel_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("request_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("response_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_msg", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_cmd_device_created", "device_command_logs", ["device_id", "created_at"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("device_id", sa.String(128)),
        sa.Column("client_ip", sa.String(64)),
        sa.Column("user_agent", sa.String()),
        sa.Column("result", sa.String(32)),
        sa.Column("detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_device", "audit_logs", ["device_id"])
    op.create_table(
        "user_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("permission", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("resource_id", sa.String(128)),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "permission", "resource_type", "resource_id", name="uq_user_perm"
        ),
    )
    op.create_table(
        "rate_limits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("resource_key", sa.String(255), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("resource_key", "window_start", name="uq_rate_limit_window"),
    )
    op.create_table(
        "webhook_nonces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("nonce", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("device_id", "nonce", name="uq_webhook_nonce"),
    )


def downgrade() -> None:
    for table in (
        "webhook_nonces",
        "rate_limits",
        "user_permissions",
        "audit_logs",
        "device_command_logs",
        "device_capabilities",
        "device_events",
        "device_webhooks",
        "devices",
        "users",
    ):
        op.drop_table(table)
