from fastapi.testclient import TestClient


def _login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_device(client: TestClient, headers: dict[str, str], base_url: str | None = None) -> str:
    payload = {"device_name": "phone", "channel_type": "hybrid"}
    if base_url:
        payload["base_url"] = base_url
    response = client.post("/api/v1/devices", json=payload, headers=headers)
    assert response.status_code == 200
    return response.json()["data"]["device_id"]


def test_enable_tunnel_syncs_base_url_and_hides_token(client: TestClient) -> None:
    headers = _login(client)
    device_id = _create_device(client, headers)

    response = client.post(
        f"/api/v1/devices/{device_id}/tunnel",
        json={"local_port": 8080},
        headers=headers,
    )

    assert response.status_code == 200
    tunnel = response.json()["data"]
    assert tunnel["enabled"] is True
    assert tunnel["remote_port"] == 17000
    assert tunnel["internal_base_url"] == "http://127.0.0.1:17000"
    assert "token" not in tunnel

    device = client.get(f"/api/v1/devices/{device_id}", headers=headers).json()["data"]
    assert device["base_url"] == "http://127.0.0.1:17000"


def test_frpc_config_contains_token_and_proxy(client: TestClient) -> None:
    headers = _login(client)
    device_id = _create_device(client, headers)
    client.post(f"/api/v1/devices/{device_id}/tunnel", json={"local_port": 8080}, headers=headers)

    response = client.get(f"/api/v1/devices/{device_id}/tunnel/frpc-config", headers=headers)

    assert response.status_code == 200
    config = response.json()["data"]
    assert config["filename"].endswith("-frpc.toml")
    assert 'serverAddr = "localhost"' in config["content"]
    assert 'auth.token = "change-me-frps-token"' in config["content"]
    assert "[[proxies]]" in config["content"]
    assert "remotePort = 17000" in config["content"]


def test_disable_tunnel_restores_previous_base_url(client: TestClient) -> None:
    headers = _login(client)
    device_id = _create_device(client, headers, "http://192.168.1.10:8080")
    client.post(f"/api/v1/devices/{device_id}/tunnel", json={"local_port": 8080}, headers=headers)

    response = client.delete(f"/api/v1/devices/{device_id}/tunnel", headers=headers)

    assert response.status_code == 200
    device = client.get(f"/api/v1/devices/{device_id}", headers=headers).json()["data"]
    assert device["base_url"] == "http://192.168.1.10:8080/"


def test_active_tunnel_blocks_manual_base_url_update(client: TestClient) -> None:
    headers = _login(client)
    device_id = _create_device(client, headers)
    client.post(f"/api/v1/devices/{device_id}/tunnel", json={"local_port": 8080}, headers=headers)

    response = client.put(
        f"/api/v1/devices/{device_id}",
        json={"base_url": "http://192.168.1.20:8080"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["msg"] == "base_url is managed by tunnel"


def test_tunnel_remote_ports_are_unique(client: TestClient) -> None:
    headers = _login(client)
    first_id = _create_device(client, headers)
    second_id = _create_device(client, headers)

    first = client.post(
        f"/api/v1/devices/{first_id}/tunnel", json={"local_port": 8080}, headers=headers
    ).json()["data"]
    second = client.post(
        f"/api/v1/devices/{second_id}/tunnel", json={"local_port": 8080}, headers=headers
    ).json()["data"]

    assert first["remote_port"] == 17000
    assert second["remote_port"] == 17001
