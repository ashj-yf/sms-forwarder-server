from typing import Any

import pytest

from app.adapters.smsforwarder_http_adapter import SmsForwarderHttpAdapter


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


@pytest.mark.asyncio
async def test_adapter_posts_signed_body(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({"code": 200, "data": {"ok": True}})

    monkeypatch.setattr("app.adapters.smsforwarder_http_adapter.httpx.AsyncClient", FakeClient)

    result = await SmsForwarderHttpAdapter().request(
        "http://device.local/", "/sms/query", {"page_num": 1}, "secret"
    )

    assert result["data"]["ok"] is True
    assert captured["url"] == "http://device.local/sms/query"
    assert captured["json"]["data"] == {"page_num": 1}
    assert "timestamp" in captured["json"]
    assert "sign" in captured["json"]
