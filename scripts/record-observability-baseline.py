#!/usr/bin/env python3
"""Локальный HTTP-прогон карты. Печатает JSON с UTC-окнами и задержками."""

import argparse
import concurrent.futures
import datetime
import json
import time
import urllib.error
import urllib.request


def request(base_url, path):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(base_url + path, timeout=15) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except Exception as error:
        status = type(error).__name__
    return status, (time.perf_counter() - started) * 1000


def run(name, base_url, paths, seconds, workers):
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    deadline = time.monotonic() + seconds
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        while time.monotonic() < deadline:
            futures = [pool.submit(request, base_url, paths[i % len(paths)]) for i in range(workers)]
            results.extend(future.result() for future in futures)
            time.sleep(0.2)
    latencies = sorted(value for status, value in results if status == 200)
    statuses = {str(status): sum(item[0] == status for item in results) for status, _ in results}
    return {
        "scenario": name,
        "start_utc": started_utc,
        "end_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(results),
        "statuses": statuses,
        "p50_ms": round(latencies[len(latencies) // 2], 2) if latencies else None,
        "p95_ms": round(latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))], 2) if latencies else None,
        "max_ms": round(max(latencies), 2) if latencies else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()
    if args.seconds < 1:
        parser.error("--seconds must be positive")
    base_url = args.base_url.rstrip("/")
    scenarios = [
        ("normal_viewport", ["/api/v1/world/viewport?x=0&y=0&radius=16"], 1),
        ("mixed_viewport", [
            "/api/v1/world/viewport?x=0&y=0&radius=48",
            "/api/v1/world/viewport?x=80&y=40&radius=48",
            "/api/v1/world/chunks?x=0&y=0&radius=1",
            "/api/v1/world/chunks?x=2&y=1&radius=1",
        ], 4),
    ]
    for name, paths, workers in scenarios:
        print(json.dumps(run(name, base_url, paths, args.seconds, workers), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
