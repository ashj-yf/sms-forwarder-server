from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.device import Device
from app.models.device_tunnel import DeviceTunnel
from app.schemas.tunnel import TunnelEnableIn, TunnelFrpcConfigOut, TunnelUpdateIn
from app.services.audit_service import AuditService
from app.utils.crypto import decrypt, encrypt


class TunnelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, device_id: str) -> DeviceTunnel | None:
        self._get_device(device_id)
        return self._get_tunnel(device_id)

    def enable(self, device_id: str, payload: TunnelEnableIn) -> DeviceTunnel:
        device = self._get_device(device_id)
        tunnel = self._get_tunnel(device_id)
        if tunnel and tunnel.enabled:
            raise ConflictError("device tunnel already enabled")
        remote_port = payload.remote_port or self._next_remote_port()
        self._ensure_remote_port_allowed(remote_port)
        token = self._token()
        if tunnel is None:
            tunnel = DeviceTunnel(
                device_id=device_id,
                proxy_name=self._proxy_name(device_id),
                local_port=payload.local_port,
                remote_port=remote_port,
                auth_token_encrypted=encrypt(token),
                internal_base_url=self._internal_base_url(remote_port),
            )
            self.db.add(tunnel)
        else:
            tunnel.remote_port = remote_port
            tunnel.auth_token_encrypted = encrypt(token)
            tunnel.internal_base_url = self._internal_base_url(remote_port)
        tunnel.enabled = True
        tunnel.proxy_type = "tcp"
        tunnel.local_ip = payload.local_ip
        tunnel.local_port = payload.local_port
        tunnel.public_base_url = self._public_base_url(remote_port)
        tunnel.previous_base_url = device.base_url
        tunnel.use_encryption = payload.use_encryption
        tunnel.use_compression = payload.use_compression
        tunnel.status = "active"
        if payload.sync_device_base_url:
            device.base_url = tunnel.internal_base_url
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("remote port already allocated") from exc
        self.db.refresh(tunnel)
        return tunnel

    def update(self, device_id: str, payload: TunnelUpdateIn) -> DeviceTunnel:
        tunnel = self._require_tunnel(device_id)
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            if value is not None:
                setattr(tunnel, key, value)
        self.db.commit()
        self.db.refresh(tunnel)
        return tunnel

    def disable(self, device_id: str) -> DeviceTunnel:
        device = self._get_device(device_id)
        tunnel = self._require_tunnel(device_id)
        tunnel.enabled = False
        tunnel.status = "disabled"
        device.base_url = tunnel.previous_base_url
        self.db.commit()
        self.db.refresh(tunnel)
        return tunnel

    def rotate_token(self, device_id: str) -> dict[str, str]:
        tunnel = self._require_tunnel(device_id)
        token = self._token()
        tunnel.auth_token_encrypted = encrypt(token)
        self.db.commit()
        return {"token": token}

    def render_frpc_config(self, device_id: str, user_id: int | None = None) -> TunnelFrpcConfigOut:
        tunnel = self._require_tunnel(device_id)
        token = decrypt(tunnel.auth_token_encrypted)
        tunnel.last_config_generated_at = datetime.now(UTC)
        AuditService(self.db).record(
            "tunnel.frpc_config.read",
            "success",
            {"proxy_name": tunnel.proxy_name, "remote_port": tunnel.remote_port},
            user_id=user_id,
            device_id=device_id,
        )
        self.db.commit()
        content = self._frpc_toml(tunnel, token)
        return TunnelFrpcConfigOut(filename=f"{tunnel.proxy_name}-frpc.toml", content=content)

    def _get_device(self, device_id: str) -> Device:
        device = self.db.query(Device).filter(Device.device_id == device_id).one_or_none()
        if device is None:
            raise NotFoundError("device not found")
        return device

    def _get_tunnel(self, device_id: str) -> DeviceTunnel | None:
        return self.db.query(DeviceTunnel).filter(DeviceTunnel.device_id == device_id).one_or_none()

    def _require_tunnel(self, device_id: str) -> DeviceTunnel:
        self._get_device(device_id)
        tunnel = self._get_tunnel(device_id)
        if tunnel is None:
            raise NotFoundError("device tunnel not found")
        return tunnel

    def _next_remote_port(self) -> int:
        settings = get_settings()
        used = {
            row[0]
            for row in self.db.query(DeviceTunnel.remote_port)
            .filter(
                DeviceTunnel.remote_port >= settings.frps_allow_port_min,
                DeviceTunnel.remote_port <= settings.frps_allow_port_max,
            )
            .all()
        }
        for port in range(settings.frps_allow_port_min, settings.frps_allow_port_max + 1):
            if port not in used:
                return port
        raise ConflictError("no frps remote ports available")

    def _ensure_remote_port_allowed(self, remote_port: int) -> None:
        settings = get_settings()
        if remote_port < settings.frps_allow_port_min or remote_port > settings.frps_allow_port_max:
            raise ConflictError("remote port is outside frps allow range")

    def _internal_base_url(self, remote_port: int) -> str:
        settings = get_settings()
        return f"http://{settings.frps_internal_host}:{remote_port}"

    def _public_base_url(self, remote_port: int) -> str:
        settings = get_settings()
        return f"tcp://{settings.frps_public_host}:{remote_port}"

    def _proxy_name(self, device_id: str) -> str:
        return f"smsf-{device_id}"[:128]

    def _token(self) -> str:
        return get_settings().frps_auth_token

    def _frpc_toml(self, tunnel: DeviceTunnel, token: str) -> str:
        settings = get_settings()
        use_encryption = str(tunnel.use_encryption).lower()
        use_compression = str(tunnel.use_compression).lower()
        return "\n".join(
            [
                f'serverAddr = "{settings.frps_public_host}"',
                f"serverPort = {settings.frps_bind_port}",
                "",
                'auth.method = "token"',
                f'auth.token = "{token}"',
                "",
                "[[proxies]]",
                f'name = "{tunnel.proxy_name}"',
                'type = "tcp"',
                f'localIP = "{tunnel.local_ip}"',
                f"localPort = {tunnel.local_port}",
                f"remotePort = {tunnel.remote_port}",
                f"transport.useEncryption = {use_encryption}",
                f"transport.useCompression = {use_compression}",
                "",
            ]
        )
