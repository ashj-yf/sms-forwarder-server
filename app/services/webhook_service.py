import hashlib
import secrets
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.webhook_parser import parse_webhook_payload
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.models.device import Device
from app.models.device_event import DeviceEvent
from app.models.device_webhook import DeviceWebhook
from app.utils.deduplication import stable_event_id


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class WebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, device_id: str) -> dict[str, str]:
        device = self.db.query(Device).filter(Device.device_id == device_id).one_or_none()
        if device is None:
            raise NotFoundError("device not found")
        token = f"wh_{secrets.token_urlsafe(32)}"
        webhook = DeviceWebhook(
            device_id=device_id,
            webhook_token_hash=hash_token(token),
            webhook_token_prefix=token[:8],
        )
        self.db.add(webhook)
        self.db.commit()
        base_url = get_settings().public_base_url.rstrip("/")
        return {
            "webhook_url": f"{base_url}/api/v1/webhooks/smsforwarder/{token}",
            "webhook_token": token,
        }

    def rotate(self, device_id: str) -> dict[str, str]:
        old_items = self.db.query(DeviceWebhook).filter(DeviceWebhook.device_id == device_id).all()
        for item in old_items:
            item.enabled = False
        return self.create(device_id)

    def lookup(self, token: str) -> DeviceWebhook:
        webhook = (
            self.db.query(DeviceWebhook)
            .filter(
                DeviceWebhook.webhook_token_hash == hash_token(token),
                DeviceWebhook.enabled.is_(True),
            )
            .one_or_none()
        )
        if webhook is None:
            raise UnauthorizedError("invalid webhook token")
        return webhook

    def ingest(
        self, webhook: DeviceWebhook, payload: dict[str, Any], source_ip: str | None
    ) -> dict[str, Any]:
        parsed = parse_webhook_payload(payload)
        event_type = parsed["event_type"]
        event_id = parsed["event_id"] or stable_event_id(webhook.device_id, event_type, payload)
        now = datetime.now(UTC)
        event = DeviceEvent(
            event_id=event_id,
            device_id=webhook.device_id,
            event_type=event_type,
            event_time=parsed["event_time"],
            normalized_payload=parsed["normalized_payload"],
            raw_payload=payload,
            source_ip=source_ip,
            created_at=now,
        )
        duplicate = False
        try:
            self.db.add(event)
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            duplicate = True
        device = self.db.query(Device).filter(Device.device_id == webhook.device_id).one()
        device.last_seen_at = now
        device.last_webhook_at = now
        device.is_active = True
        device.status = "active"
        webhook.last_called_at = now
        webhook.called_count += 1
        if not duplicate:
            device.webhook_count += 1
        self.db.commit()
        return {"duplicate": duplicate, "event_id": event_id, "event_type": event_type}
