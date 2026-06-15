from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class DeviceCreate(BaseModel):
    device_name: str | None = Field(default=None, max_length=255)
    channel_type: str = "hybrid"
    base_url: HttpUrl | None = None
    sign_secret: str | None = Field(default=None, max_length=512)


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(default=None, max_length=255)
    channel_type: str | None = None
    base_url: HttpUrl | None = None
    sign_secret: str | None = Field(default=None, max_length=512)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    device_name: str | None
    channel_type: str
    base_url: str | None
    status: str
    is_active: bool
    last_seen_at: datetime | None
    last_webhook_at: datetime | None
    webhook_count: int


class DeviceListOut(BaseModel):
    items: list[DeviceOut]
    total: int
