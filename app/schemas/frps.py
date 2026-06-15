from datetime import datetime

from pydantic import BaseModel


class FrpsDeviceOut(BaseModel):
    device_id: str
    device_name: str | None
    channel_type: str
    base_url: str | None
    tunnel_enabled: bool
    proxy_name: str
    remote_port: int
    local_ip: str
    local_port: int
    connected: bool
    frps_status: str
    client_version: str | None = None
    today_traffic_in: str | None = None
    today_traffic_out: str | None = None
    last_start_time: datetime | None = None


class FrpsDeviceListOut(BaseModel):
    items: list[FrpsDeviceOut]
    total: int
    connected: int
