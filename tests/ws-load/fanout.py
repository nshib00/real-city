#!/usr/bin/env python3
"""Измеряет доставку глобального чата подписчикам изолированного API."""

import argparse
import asyncio
import json
import secrets
import time
import urllib.parse
import urllib.request

from websockets.asyncio.client import connect


def http_json(base, path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.load(response)


def metrics(base):
    with urllib.request.urlopen(base + "/metrics", timeout=10) as response:
        lines = response.read().decode().splitlines()
    names = ("real_city_ws_fanout_total", "real_city_ws_messages_dropped_total", "real_city_ws_eventbus_drops_total")
    return {name: float(next((line.split()[-1] for line in lines if line.startswith(name + " ")), "0")) for name in names}


async def receive_chat(socket, expected_id, results):
    async for raw in socket:
        event = json.loads(raw)
        if event.get("type") == "chat.message.created":
            message = event.get("payload", {})
            if message.get("author_id") == expected_id:
                results.add(message.get("id"))


async def main(args):
    if urllib.parse.urlparse(args.base_url).hostname not in ("127.0.0.1", "localhost"):
        raise SystemExit("Нагрузочный сценарий разрешён только для локального тестового стенда")
    base = args.base_url.rstrip("/")
    nonce = secrets.token_hex(6)
    status, account = await asyncio.to_thread(http_json, base, "/api/v1/auth/register", "POST", {
        "email": f"fanout-{nonce}@example.invalid", "name": f"Fanout{nonce}", "password": f"Load{nonce}12345",
    })
    if status != 201:
        raise RuntimeError(f"registration: {status}")
    token = account["access_token"]
    player_id = account["player"]["id"]
    before = await asyncio.to_thread(metrics, base)
    url = base.replace("http://", "ws://", 1) + "/api/v1/realtime?token=" + urllib.parse.quote(token)
    sockets = []
    readers = []
    received = []
    started = time.monotonic()
    try:
        for _ in range(args.connections):
            socket = await connect(url, open_timeout=10)
            sockets.append(socket)
            await socket.send(json.dumps({"type": "subscribe", "chunk_ids": [], "private": True}))
            # Initial connection ack and subscription ack must arrive before publishing.
            for _ in range(2):
                await asyncio.wait_for(socket.recv(), timeout=10)
            messages = set()
            received.append(messages)
            readers.append(asyncio.create_task(receive_chat(socket, player_id, messages)))
        for index in range(args.messages):
            status, _ = await asyncio.to_thread(http_json, base, "/api/v1/chat/messages", "POST", {
                "channel": "global", "body": f"fanout-{nonce}-{index}",
            }, token)
            if status != 201:
                raise RuntimeError(f"chat status: {status}")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and any(len(messages) < args.messages for messages in received):
            await asyncio.sleep(0.1)
    finally:
        await asyncio.gather(*(socket.close() for socket in sockets), return_exceptions=True)
        for reader in readers:
            reader.cancel()
        await asyncio.gather(*readers, return_exceptions=True)
    after = await asyncio.to_thread(metrics, base)
    total = sum(len(messages) for messages in received)
    expected = args.connections * args.messages
    result = {
        "connections": args.connections, "messages": args.messages, "expected_deliveries": expected,
        "received_deliveries": total, "elapsed_seconds": round(time.monotonic() - started, 3),
        "fanout_delta": after["real_city_ws_fanout_total"] - before["real_city_ws_fanout_total"],
        "drops_delta": after["real_city_ws_messages_dropped_total"] - before["real_city_ws_messages_dropped_total"],
        "eventbus_drops_delta": after["real_city_ws_eventbus_drops_total"] - before["real_city_ws_eventbus_drops_total"],
    }
    print(json.dumps(result, ensure_ascii=False))
    if total != expected or result["drops_delta"] or result["eventbus_drops_delta"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--connections", type=int, default=50)
    parser.add_argument("--messages", type=int, default=10)
    options = parser.parse_args()
    if not 1 <= options.connections <= 1000 or not 1 <= options.messages <= 100:
        parser.error("connections: 1..1000; messages: 1..100")
    asyncio.run(main(options))
