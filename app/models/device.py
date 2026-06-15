from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    device_name: Mapped[str | None] = mapped_column(String(255))
    channel_type: Mapped[str] = mapped_column(String(64), default="hybrid", nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    sign_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    sm4_key_encrypted: Mapped[str | None] = mapped_column(Text)
    rsa_public_key: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(64))
    app_version: Mapped[str | None] = mapped_column(String(64))
    protocol_version: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="inactive", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_webhook_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    webhook_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
