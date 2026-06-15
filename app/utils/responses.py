from datetime import UTC, datetime
from typing import Any

from fastapi import Request


def timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def success_response(request: Request, data: Any = None, msg: str = "success") -> dict[str, Any]:
    return {
        "code": 200,
        "msg": msg,
        "data": data if data is not None else {},
        "request_id": getattr(request.state, "request_id", ""),
        "timestamp": timestamp_ms(),
    }


def error_response(request: Request, code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return {
        "code": code,
        "msg": msg,
        "data": data if data is not None else {},
        "request_id": getattr(request.state, "request_id", ""),
        "timestamp": timestamp_ms(),
    }
