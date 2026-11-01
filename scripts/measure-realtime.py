#!/usr/bin/env python3
"""Замер настоящего WS fanout и восстановления подписок на тестовом стенде."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests/e2e/api'))
from gameplay_restart import Realtime
import smoke


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:18080')
    parser.add_argument('--connections', type=int, default=8)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--reconnect-rounds', type=int, default=1)
    parser.add_argument('--max-p95-ms', type=float, default=2000)
    args = parser.parse_args()
    token = os.environ.get('REAL_CITY_ACCESS_TOKEN')
    if not token:
        parser.error('Задайте REAL_CITY_ACCESS_TOKEN тестового игрока')
    if not 1 <= args.connections <= 128 or not 1 <= args.seconds <= 3600 or not 0 <= args.reconnect_rounds <= 10 or args.max_p95_ms <= 0:
        parser.error('connections 1..128, seconds 1..3600, reconnect-rounds 0..10; p95 > 0')
    smoke.BASE = args.base_url.rstrip('/')
    clients, samples, failures = [], [], 0
    started = time.monotonic()
    try:
        for _ in range(args.connections):
            clients.append(Realtime(token))
        for _ in range(args.reconnect_rounds):
            for client in clients:
                client.close()
            clients = []
            with ThreadPoolExecutor(max_workers=args.connections) as pool:
                # Preserve every opened socket, including when another upgrade fails.
                futures = [pool.submit(Realtime, token) for _ in range(args.connections)]
                errors = []
                for future in futures:
                    try:
                        clients.append(future.result())
                    except Exception as error:
                        errors.append(type(error).__name__)
                if errors:
                    raise AssertionError('reconnect failed')
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            sent = time.monotonic()
            _, response, _ = smoke.request('POST', '/api/v1/chat/messages', {'channel': 'global', 'body': 'Замер WS ' + secrets.token_hex(5)}, token)
            message_id = response['message']['id']
            def receive(client):
                client.wait_message(message_id)
                return (time.monotonic() - sent) * 1000
            with ThreadPoolExecutor(max_workers=args.connections) as pool:
                for future in [pool.submit(receive, client) for client in clients]:
                    try:
                        samples.append(future.result())
                    except Exception:
                        failures += 1
            # At most 30 messages/minute: respect the normal chat rate limit.
            time.sleep(max(0, min(deadline - time.monotonic(), 2 - (time.monotonic() - sent))))
    except Exception as error:
        failures += 1
        print(json.dumps({'scenario': 'ws_fanout', 'failure_type': type(error).__name__}), file=sys.stderr)
    finally:
        for client in clients:
            client.close()
    samples.sort()
    p95 = samples[min(len(samples)-1, int(len(samples)*.95))] if samples else None
    result = dict(scenario='ws_fanout', connections=args.connections, reconnect_rounds=args.reconnect_rounds,
                  deliveries=len(samples), failures=failures, elapsed_seconds=round(time.monotonic()-started, 3),
                  p50_end_to_end_ms=round(samples[len(samples)//2], 2) if samples else None,
                  p95_end_to_end_ms=round(p95, 2) if p95 is not None else None)
    result['passed'] = failures == 0 and p95 is not None and p95 <= args.max_p95_ms
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
