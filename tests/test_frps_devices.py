import pytest
from fastapi.testclient import TestClient

from app.services.frps_service import FrpsProxy, FrpsService


def _login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_device(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/v1/devices",
        json={"device_name": name, "channel_type": "hybrid"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]["device_id"]


def test_list_frps_devices_filters_connected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _login(client)
    first_id = _create_device(client, headers, "online phone")
    second_id = _create_device(client, headers, "offline phone")
    client.post(f"/api/v1/devices/{first_id}/tunnel", json={"local_port": 8080}, headers=headers)
    client.post(f"/api/v1/devices/{second_id}/tunnel", json={"local_port": 8080}, headers=headers)

    def fetch_proxies(self: FrpsService) -> list[FrpsProxy]:
        return [
            FrpsProxy(
                name=f"smsf-{first_id}",
                status="online",
                remote_port=17000,
                client_version="0.61.2",
                today_traffic_in="1 KiB",
                today_traffic_out="2 KiB",
                last_start_time=None,
            )
        ]

    monkeypatch.setattr(FrpsService, "_fetch_tcp_proxies", fetch_proxies)

    response = client.get("/api/v1/frps/devices?connected_only=true", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["connected"] == 1
    assert data["items"][0]["device_id"] == first_id
    assert data["items"][0]["connected"] is True
