#!/usr/bin/env python3
"""Короткий HTTP-прогон размещения и чата на локальной тестовой базе."""

import concurrent.futures
import json
import secrets
import statistics
import time
import urllib.error
import urllib.request


BASE = "http://127.0.0.1:18080"


def call(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if method == "POST" and path == "/api/v1/buildings":
        headers["Idempotency-Key"] = secrets.token_hex(16)
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.load(response), (time.perf_counter() - started) * 1000
    except urllib.error.HTTPError as error:
        return error.code, json.load(error), (time.perf_counter() - started) * 1000


def summary(samples):
    durations = sorted(duration for _, _, duration in samples)
    codes = {}
    for status, _, _ in samples:
        codes[str(status)] = codes.get(str(status), 0) + 1
    return {"requests": len(samples), "statuses": codes, "p50_ms": round(statistics.median(durations), 2),
            "p95_ms": round(durations[min(len(durations) - 1, int(len(durations) * .95))], 2)}


def main():
    nonce = secrets.token_hex(6)
    status, account, _ = call("/api/v1/auth/register", "POST", {
        "email": f"commands-{nonce}@example.invalid", "name": f"Commands{nonce}", "password": f"Load{nonce}12345",
    })
    if status != 201:
        raise SystemExit(f"registration failed: {status} {account}")
    token = account["access_token"]
    _, snapshot, _ = call("/api/v1/world/viewport?x=80&y=80&radius=48")
    grass = [tile for chunk in snapshot["chunks"] for tile in chunk["tiles"] if tile["terrain"] == "grass"]
    center = None
    placement_samples = []
    for tile in grass[:100]:
        response = call("/api/v1/buildings", "POST", {"type": "town_hall", "tile_x": tile["x"], "tile_y": tile["y"]}, token)
        placement_samples.append(response)
        if response[0] == 201:
            center = tile
            break
    if center is None:
        raise SystemExit(f"no valid starting tile: {summary(placement_samples)}")
    nearby = [tile for tile in grass if abs(tile["x"] - center["x"]) <= 5 and abs(tile["y"] - center["y"]) <= 5 and tile != center][:20]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        placement_samples.extend(pool.map(lambda tile: call("/api/v1/buildings", "POST", {
            "type": "road", "tile_x": tile["x"], "tile_y": tile["y"]}, token), nearby))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        chat_samples = list(pool.map(lambda index: call("/api/v1/chat/messages", "POST", {
            "channel": "global", "body": f"commands-{nonce}-{index}"}, token), range(20)))
    result = {"placement": summary(placement_samples), "chat": summary(chat_samples),
              "server_errors": [{"status": status, "body": body} for status, body, _ in placement_samples + chat_samples if status >= 500]}
    print(json.dumps(result, ensure_ascii=False))
    if any(status >= 500 for status, _, _ in placement_samples + chat_samples):
        raise SystemExit(1)
    if not any(status == 201 for status, _, _ in placement_samples):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
