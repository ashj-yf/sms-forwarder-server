from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DeviceTunnel(Base, TimestampMixin):
    __tablename__ = "device_tunnels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("devices.device_id"), unique=True, nullable=False, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proxy_type: Mapped[str] = mapped_column(String(16), default="tcp", nullable=False)
    proxy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    local_ip: Mapped[str] = mapped_column(String(64), default="127.0.0.1", nullable=False)
    local_port: Mapped[int] = mapped_column(Integer, nullable=False)
    remote_port: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    auth_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    internal_base_url: Mapped[str] = mapped_column(Text, nullable=False)
    public_base_url: Mapped[str | None] = mapped_column(Text)
    previous_base_url: Mapped[str | None] = mapped_column(Text)
    use_encryption: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_compression: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    last_config_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
