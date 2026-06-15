from datetime import datetime
from ipaddress import ip_address

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TunnelEnableIn(BaseModel):
    local_ip: str = Field(default="127.0.0.1", max_length=64)
    local_port: int = Field(ge=1, le=65535)
    remote_port: int | None = Field(default=None, ge=1, le=65535)
    sync_device_base_url: bool = True
    use_encryption: bool = True
    use_compression: bool = True

    @field_validator("local_ip")
    @classmethod
    def validate_local_ip(cls, value: str) -> str:
        return _validate_local_ip(value)


class TunnelUpdateIn(BaseModel):
    local_ip: str | None = Field(default=None, max_length=64)
    local_port: int | None = Field(default=None, ge=1, le=65535)
    use_encryption: bool | None = None
    use_compression: bool | None = None

    @field_validator("local_ip")
    @classmethod
    def validate_local_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_local_ip(value)


class TunnelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    proxy_type: str
    proxy_name: str
    local_ip: str
    local_port: int
    remote_port: int
    internal_base_url: str
    public_base_url: str | None
    use_encryption: bool
    use_compression: bool
    status: str
    last_config_generated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TunnelTokenOut(BaseModel):
    token: str


class TunnelFrpcConfigOut(BaseModel):
    filename: str
    format: str = "toml"
    content: str


def _validate_local_ip(value: str) -> str:
    normalized = value.strip()
    if normalized == "localhost":
        return normalized
    try:
        parsed = ip_address(normalized)
    except ValueError as exc:
        raise ValueError("local_ip must be localhost, loopback, or private address") from exc
    if parsed.is_loopback or parsed.is_private:
        return normalized
    raise ValueError("local_ip must be localhost, loopback, or private address")
