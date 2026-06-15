import re
from collections.abc import Mapping, Sequence
from typing import Any

PHONE_RE = re.compile(r"(?<!\d)(\d{3})\d{4}(\d{4})(?!\d)")
SENSITIVE_KEYS = {"token", "webhook_token", "sign", "secret", "password", "authorization"}
CONTENT_KEYS = {"content", "sms_content", "message", "body"}


def mask_phone(value: str) -> str:
    return PHONE_RE.sub(r"\1****\2", value)


def scrub(value: Any) -> Any:
    if isinstance(value, str):
        return mask_phone(value)
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered in SENSITIVE_KEYS or lowered.endswith("_secret"):
                cleaned[key_text] = "***"
            elif lowered in CONTENT_KEYS and isinstance(item, str):
                cleaned[key_text] = {"content_length": len(item)}
            else:
                cleaned[key_text] = scrub(item)
        return cleaned
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [scrub(item) for item in value]
    return value
