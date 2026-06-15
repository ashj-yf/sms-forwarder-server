from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.device import Device
from app.models.device_tunnel import DeviceTunnel
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.utils.crypto import encrypt
from app.utils.id_generator import generate_device_id


class DeviceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: DeviceCreate) -> Device:
        device = Device(
            device_id=generate_device_id(),
            device_name=payload.device_name,
            channel_type=payload.channel_type,
            base_url=str(payload.base_url) if payload.base_url else None,
            sign_secret_encrypted=encrypt(payload.sign_secret) if payload.sign_secret else None,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def list(self) -> list[Device]:
        return list(self.db.query(Device).order_by(Device.id.desc()).all())

    def get(self, device_id: str) -> Device:
        device = self.db.query(Device).filter(Device.device_id == device_id).one_or_none()
        if device is None:
            raise NotFoundError("device not found")
        return device

    def update(self, device_id: str, payload: DeviceUpdate) -> Device:
        device = self.get(device_id)
        changes = payload.model_dump(exclude_unset=True)
        if "base_url" in changes:
            active_tunnel = (
                self.db.query(DeviceTunnel)
                .filter(DeviceTunnel.device_id == device_id, DeviceTunnel.enabled.is_(True))
                .one_or_none()
            )
            if active_tunnel is not None:
                raise ConflictError("base_url is managed by tunnel")
        if "base_url" in changes and changes["base_url"] is not None:
            changes["base_url"] = str(changes["base_url"])
        sign_secret = changes.pop("sign_secret", None)
        for key, value in changes.items():
            setattr(device, key, value)
        if sign_secret:
            device.sign_secret_encrypted = encrypt(sign_secret)
        self.db.commit()
        self.db.refresh(device)
        return device
