from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import DeviceChannelError
from app.models.device import Device
from app.models.device_tunnel import DeviceTunnel
from app.schemas.frps import FrpsDeviceListOut, FrpsDeviceOut


@dataclass(frozen=True)
class FrpsProxy:
    name: str
    status: str
    remote_port: int | None
    client_version: str | None
    today_traffic_in: str | None
    today_traffic_out: str | None
    last_start_time: datetime | None


class FrpsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_devices(self, connected_only: bool = False) -> FrpsDeviceListOut:
        proxies = {proxy.name: proxy for proxy in self._fetch_tcp_proxies()}
        rows = (
            self.db.query(Device, DeviceTunnel)
            .join(DeviceTunnel, DeviceTunnel.device_id == Device.device_id)
            .order_by(DeviceTunnel.remote_port.asc())
            .all()
        )
        items = [
            self._build_item(device, tunnel, proxies.get(tunnel.proxy_name))
            for device, tunnel in rows
        ]
        if connected_only:
            items = [item for item in items if item.connected]
        return FrpsDeviceListOut(
            items=items,
            total=len(items),
            connected=sum(1 for item in items if item.connected),
        )

    def _fetch_tcp_proxies(self) -> list[FrpsProxy]:
        settings = get_settings()
        url = f"http://127.0.0.1:{settings.frps_dashboard_port}/api/proxy/tcp"
        try:
            response = httpx.get(
                url,
                auth=(settings.frps_dashboard_user, settings.frps_dashboard_password),
                timeout=settings.http_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DeviceChannelError("frps dashboard unavailable") from exc
        if not isinstance(payload, dict):
            raise DeviceChannelError("invalid frps dashboard response")
        raw_proxies = payload.get("proxies", [])
        if not isinstance(raw_proxies, list):
            raise DeviceChannelError("invalid frps dashboard response")
        return [self._parse_proxy(proxy) for proxy in raw_proxies if isinstance(proxy, dict)]

    def _build_item(
        self, device: Device, tunnel: DeviceTunnel, proxy: FrpsProxy | None
    ) -> FrpsDeviceOut:
        connected = proxy is not None and proxy.status.lower() == "online"
        return FrpsDeviceOut(
            device_id=device.device_id,
            device_name=device.device_name,
            channel_type=device.channel_type,
            base_url=device.base_url,
            tunnel_enabled=tunnel.enabled,
            proxy_name=tunnel.proxy_name,
            remote_port=tunnel.remote_port,
            local_ip=tunnel.local_ip,
            local_port=tunnel.local_port,
            connected=connected,
            frps_status=proxy.status if proxy else "missing",
            client_version=proxy.client_version if proxy else None,
            today_traffic_in=proxy.today_traffic_in if proxy else None,
            today_traffic_out=proxy.today_traffic_out if proxy else None,
            last_start_time=proxy.last_start_time if proxy else None,
        )

    def _parse_proxy(self, proxy: dict[str, Any]) -> FrpsProxy:
        raw_conf = proxy.get("conf")
        conf = raw_conf if isinstance(raw_conf, dict) else {}
        name = str(proxy.get("name") or conf.get("name") or "")
        status = str(proxy.get("status") or "unknown")
        return FrpsProxy(
            name=name,
            status=status,
            remote_port=self._optional_int(conf.get("remote_port") or proxy.get("remote_port")),
            client_version=self._optional_str(proxy.get("client_version")),
            today_traffic_in=self._optional_str(proxy.get("today_traffic_in")),
            today_traffic_out=self._optional_str(proxy.get("today_traffic_out")),
            last_start_time=self._optional_datetime(proxy.get("last_start_time")),
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _optional_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _optional_datetime(self, value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
