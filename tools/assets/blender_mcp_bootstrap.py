#!/usr/bin/env python3
"""Check the Blender addon socket configured for this project."""

from __future__ import annotations

import argparse
import json
import socket
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".codex" / "config.toml"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


def check_bootstrap(host: str | None = None, port: int | None = None, timeout: float = 2.5) -> dict[str, Any]:
    config = read_config()
    env = (((config.get("mcp_servers") or {}).get("blender") or {}).get("env") or {})
    configured_host = env.get("BLENDER_HOST", DEFAULT_HOST)
    configured_port = int(env.get("BLENDER_PORT", DEFAULT_PORT))
    host = host or configured_host
    port = port or configured_port
    result = {
        "config": str(CONFIG_PATH.relative_to(ROOT)),
        "configured_host": configured_host,
        "configured_port": configured_port,
        "checked_host": host,
        "checked_port": port,
        "tcp_connect": False,
        "warnings": [],
    }
    if configured_host != host:
        result["warnings"].append(f"Config host {configured_host} differs from checked host {host}.")
    if configured_port != port:
        result["warnings"].append(f"Config port {configured_port} differs from checked port {port}.")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            result["tcp_connect"] = True
    except OSError as exc:
        result["error"] = str(exc)
        result["warnings"].append("Blender MCP TCP connection failed. Check Blender addon, Windows Firewall, host and port.")
    return result


def read_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=2.5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check_bootstrap(args.host, args.port, args.timeout)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"config: {result['config']}")
        print(f"host: configured={result['configured_host']} checked={result['checked_host']}")
        print(f"port: configured={result['configured_port']} checked={result['checked_port']}")
        print(f"tcp_connect: {result['tcp_connect']}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
    return 0 if result["tcp_connect"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

