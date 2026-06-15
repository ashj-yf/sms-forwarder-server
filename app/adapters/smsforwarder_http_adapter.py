import base64
import hashlib
import hmac
from time import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.core.exceptions import DeviceChannelError, DeviceTimeoutError


def build_sign(timestamp: str, secret: str) -> str:
    message = f"{timestamp}\n{secret}".encode()
    digest = hmac.new(secret.encode(), message, hashlib.sha256).digest()
    return quote(base64.b64encode(digest).decode(), safe="")


class SmsForwarderHttpAdapter:
    async def request(
        self, base_url: str, path: str, payload: dict[str, Any], secret: str | None = None
    ) -> dict[str, Any]:
        if not base_url:
            raise DeviceChannelError("device base_url is required")
        timestamp = str(int(time() * 1000))
        body: dict[str, Any] = {"data": payload, "timestamp": timestamp}
        if secret:
            body["sign"] = build_sign(timestamp, secret)
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=get_settings().http_timeout_seconds) as client:
                response = await client.post(url, json=body)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise DeviceTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise DeviceChannelError(str(exc)) from exc
        if not isinstance(data, dict):
            raise DeviceChannelError("invalid device response")
        return data
