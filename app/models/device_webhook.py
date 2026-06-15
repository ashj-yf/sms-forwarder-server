from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DeviceWebhook(Base, TimestampMixin):
    __tablename__ = "device_webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    webhook_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    webhook_token_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    webhook_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    called_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
