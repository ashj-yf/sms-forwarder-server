from datetime import UTC, datetime
from typing import Any

VALID_EVENT_TYPES = {"sms", "call", "notification", "battery", "heartbeat"}


def parse_webhook_payload(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = str(payload.get("event_type") or payload.get("type") or "").lower()
    if event_type not in VALID_EVENT_TYPES:
        event_type = "notification"
    return {
        "event_id": payload.get("event_id") or payload.get("id"),
        "event_type": event_type,
        "event_time": datetime.now(UTC),
        "normalized_payload": payload,
    }
