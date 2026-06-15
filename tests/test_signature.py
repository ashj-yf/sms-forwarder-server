import base64
import hashlib
import hmac
from urllib.parse import quote

from app.adapters.smsforwarder_http_adapter import build_sign


def test_build_sign() -> None:
    timestamp = "1781488800000"
    secret = "test-secret"
    message = f"{timestamp}\n{secret}".encode()
    expected = quote(
        base64.b64encode(hmac.new(secret.encode(), message, hashlib.sha256).digest()).decode(),
        safe="",
    )

    assert build_sign(timestamp, secret) == expected
