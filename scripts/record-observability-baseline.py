#!/usr/bin/env python3
"""Локальный HTTP-прогон карты. Печатает JSON с UTC-окнами и задержками."""

import argparse
import concurrent.futures
import datetime
import json
import os
import time
from collections import Counter
import urllib.error
import urllib.request


def request(base_url, path):
    started = time.perf_counter()
    try:
        headers = {}
        if token := os.environ.get('REAL_CITY_ACCESS_TOKEN'):
            headers['Authorization'] = 'Bearer ' + token
        query = urllib.request.Request(base_url + path, headers=headers)
        with urllib.request.urlopen(query, timeout=15) as response:
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
    started = time.monotonic()
    def worker(index):
        samples = []
        while time.monotonic() < deadline:
            samples.append(request(base_url, paths[index % len(paths)]))
            index += 1
        return samples
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, index) for index in range(workers)]
        results = [sample for future in futures for sample in future.result()]
    elapsed = time.monotonic() - started
    latencies = sorted(value for status, value in results if status == 200)
    statuses = dict(Counter(str(status) for status, _ in results))
    return {
        "scenario": name,
        "start_utc": started_utc,
        "end_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(results),
        "workers": workers,
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / elapsed, 2),
        "error_rate": round(sum(status != 200 for status, _ in results) / len(results), 6) if results else 1,
        "statuses": statuses,
        "p50_ms": round(latencies[len(latencies) // 2], 2) if latencies else None,
        "p95_ms": round(latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))], 2) if latencies else None,
        "max_ms": round(max(latencies), 2) if latencies else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-p95-ms", type=float, default=2000)
    parser.add_argument("--max-error-rate", type=float, default=0)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600 or not 1 <= args.workers <= 128:
        parser.error("seconds: 1..3600; workers: 1..128")
    if args.max_p95_ms <= 0 or not 0 <= args.max_error_rate <= 1:
        parser.error("p95 must be positive; error rate: 0..1")
    base_url = args.base_url.rstrip("/")
    scenarios = [
        ("normal_viewport", ["/api/v1/world/viewport?x=0&y=0&radius=16"], 1),
        ("mixed_viewport", [
            "/api/v1/world/viewport?x=0&y=0&radius=48",
            "/api/v1/world/viewport?x=80&y=40&radius=48",
            "/api/v1/world/chunks?x=0&y=0&radius=1",
            "/api/v1/world/chunks?x=2&y=1&radius=1",
        ], args.workers),
        ("world_seams", [
            "/api/v1/world/chunks?x=-1&y=-1&radius=1",
            "/api/v1/world/chunks?x=0&y=0&radius=1",
        ], args.workers),
    ]
    failed = False
    for name, paths, workers in scenarios:
        result = run(name, base_url, paths, args.seconds, workers)
        result['passed'] = result['error_rate'] <= args.max_error_rate and result['p95_ms'] is not None and result['p95_ms'] <= args.max_p95_ms
        failed |= not result['passed']
        print(json.dumps(result, ensure_ascii=False), flush=True)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
