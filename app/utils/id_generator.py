import uuid


def generate_device_id() -> str:
    return f"dev_{uuid.uuid4().hex[:24]}"


def generate_request_id(prefix: str = "cmd") -> str:
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}-{uid}"
