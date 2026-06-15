from fastapi.testclient import TestClient


def _login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_webhook_ingest_and_cache_query(client: TestClient) -> None:
    headers = _login(client)
    created = client.post("/api/v1/devices", json={"device_name": "phone"}, headers=headers)
    assert created.status_code == 200
    device_id = created.json()["data"]["device_id"]

    webhook = client.post(f"/api/v1/devices/{device_id}/webhook", headers=headers)
    assert webhook.status_code == 200
    token = webhook.json()["data"]["webhook_token"]

    payload = {
        "event_type": "sms",
        "event_id": "evt-1",
        "phone": "13812345678",
        "content": "hello",
    }
    first = client.post(f"/api/v1/webhooks/smsforwarder/{token}", json=payload)
    assert first.status_code == 200
    assert first.json()["data"]["duplicate"] is False

    second = client.post(f"/api/v1/webhooks/smsforwarder/{token}", json=payload)
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True

    cache = client.post(
        f"/api/v1/devices/{device_id}/sms/query",
        json={"mode": "cache", "page_num": 1, "page_size": 10},
        headers=headers,
    )
    assert cache.status_code == 200
    result = cache.json()["data"]["result"]
    assert result["total"] == 1
    assert result["items"][0]["phone"] == "13812345678"


def test_missing_permission_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/devices")

    assert response.status_code == 401
    assert response.json()["code"] == 401
