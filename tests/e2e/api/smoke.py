"""Сквозная проверка живого API: два игрока, постройки и запуск рейда."""

import base64
import json
import os
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


BASE = os.environ.get("REAL_CITY_API_URL", "http://127.0.0.1:18080").rstrip("/")


def request(method, path, payload=None, token=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, body, headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.load(response), response.headers
    except urllib.error.HTTPError as exc:
        raise AssertionError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()}") from exc


def websocket_handshake(token):
    url = urllib.parse.urlsplit(BASE)
    port = url.port or (443 if url.scheme == "https" else 80)
    key = base64.b64encode(secrets.token_bytes(16)).decode()
    with socket.create_connection((url.hostname, port), timeout=10) as sock:
        sock.settimeout(10)
        message = (
            f"GET /api/v1/realtime HTTP/1.1\r\nHost: {url.hostname}:{port}\r\n"
            f"Authorization: Bearer {token}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(message.encode())
        status = sock.recv(1024).split(b"\r\n", 1)[0]
        assert b" 101 " in status, f"WS upgrade: {status!r}"


def main():
    nonce = secrets.token_hex(5)
    status, auth, _ = request("POST", "/api/v1/auth/register", {
        "email": f"smoke-{nonce}@example.invalid", "name": f"Smoke{nonce}", "password": "StrongPass123!"
    })
    assert status == 201 and auth["access_token"]
    token = auth["access_token"]
    _, world, _ = request("GET", "/api/v1/world")
    assert world["chunk_size"] > 0
    _, catalog, _ = request("GET", "/api/v1/buildings/catalog")
    assert any(item["type"] == "town_hall" for item in catalog["buildings"])
    _, full_catalog, _ = request("GET", "/api/v1/buildings/catalog?scope=all")
    assert len(full_catalog["buildings"]) == 73
    workshop = next(item for item in full_catalog["buildings"] if item["type"] == "workshop")
    assert workshop["health"] == 100 and workshop["first_level"]
    assert workshop["upgrade_levels"][0]["health"] == 100
    _, viewport, _ = request("GET", "/api/v1/world/viewport?x=0&y=0&radius=8")
    tiles = [tile for chunk in viewport["chunks"] for tile in chunk["tiles"]
             if tile["terrain"] not in {"water", "mountain", "forest", "ruins", "oil_well"}]
    assert tiles, "нет свободных по ландшафту клеток"
    built = None
    for tile in tiles:
        payload = {"type": "town_hall", "tile_x": tile["x"], "tile_y": tile["y"]}
        key = "smoke-build-" + nonce + f"-{tile['x']}-{tile['y']}"
        try:
            status, built, _ = request("POST", "/api/v1/buildings", payload, token, key)
            assert status == 201
            replay_status, replay, replay_headers = request("POST", "/api/v1/buildings", payload, token, key)
            assert replay_status == 201 and replay["building"]["id"] == built["building"]["id"]
            assert replay_headers.get("Idempotency-Replayed") == "true"
            _, refreshed, _ = request("POST", "/api/v1/auth/refresh", {"refresh_token": auth["refresh_token"]})
            token = refreshed["access_token"]
            replay_status, replay, replay_headers = request("POST", "/api/v1/buildings", payload, token, key)
            assert replay_status == 201 and replay["building"]["id"] == built["building"]["id"]
            assert replay_headers.get("Idempotency-Replayed") == "true"
            break
        except AssertionError as exc:
            if "HTTP 409" not in str(exc) and "HTTP 422" not in str(exc) and "HTTP 400" not in str(exc):
                raise
    assert built, "ни одна клетка не приняла ратушу"
    _, inventory, _ = request("GET", "/api/v1/economy/inventory", token=token)
    assert "inventory" in inventory
    _, monsters, _ = request("GET", "/api/v1/monsters", token=token)
    assert "monsters" in monsters
    _, rival_auth, _ = request("POST", "/api/v1/auth/register", {
        "email": f"smoke-rival-{nonce}@example.invalid", "name": f"Rival{nonce}", "password": "StrongPass123!"
    })
    rival_token = rival_auth["access_token"]
    rival_building = None
    origin = built["building"]
    for tile in tiles:
        if abs(tile["x"] - origin["tile_x"]) > 8 or abs(tile["y"] - origin["tile_y"]) > 8:
            continue
        payload = {"type": "town_hall", "tile_x": tile["x"], "tile_y": tile["y"]}
        try:
            _, rival_building, _ = request("POST", "/api/v1/buildings", payload, rival_token,
                                           "smoke-rival-build-" + nonce + f"-{tile['x']}-{tile['y']}")
            break
        except AssertionError as exc:
            if "HTTP 409" not in str(exc) and "HTTP 422" not in str(exc) and "HTTP 400" not in str(exc):
                raise
    assert rival_building, "нет свободной клетки для второго игрока рядом с первым"
    raid_payload = {"target_building_id": rival_building["building"]["id"]}
    raid_key = "smoke-raid-" + nonce
    raid_status, started, _ = request("POST", "/api/v1/raids", raid_payload, token, raid_key)
    assert raid_status == 201 and started["raid"]["status"] == "pending"
    replay_status, replay, headers = request("POST", "/api/v1/raids", raid_payload, token, raid_key)
    assert replay_status == 201 and replay["raid"]["id"] == started["raid"]["id"]
    assert headers.get("Idempotency-Replayed") == "true"
    _, raids, _ = request("GET", "/api/v1/raids", token=token)
    assert any(item["id"] == started["raid"]["id"] for item in raids["raids"])
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        _, raids, _ = request("GET", "/api/v1/raids", token=token)
        current = next(item for item in raids["raids"] if item["id"] == started["raid"]["id"])
        if current["status"] == "done":
            break
        time.sleep(1)
    else:
        raise AssertionError("рейд не завершился за 60 секунд")
    _, target, _ = request("GET", "/api/v1/buildings/" + raid_payload["target_building_id"], token=token)
    assert target["building"]["health"] <= 100 - started["raid"]["damage"]
    websocket_handshake(token)
    print(f"PASS auth → world → build/replay → economy → monsters → raid/replay → realtime; building={built['building']['id']}")


if __name__ == "__main__":
    main()
