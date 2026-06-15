import hashlib
import json
from typing import Any


def stable_event_id(device_id: str, event_type: str, payload: dict[str, Any]) -> str:
    source = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f"{device_id}|{event_type}|{source}".encode()).hexdigest()
