#!/usr/bin/env python3
"""Update the short asset-generation status document after orchestrator runs."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = ROOT / "docs" / "assets" / "asset-generation-status.md"
SECTION = "## Orchestrator batches"


def update_status(report_path: str | Path, status_path: str | Path = STATUS_PATH) -> Path:
    report_file = Path(report_path)
    report = json.loads(report_file.read_text(encoding="utf-8"))
    target = Path(status_path)
    text = target.read_text(encoding="utf-8") if target.exists() else "# Статус генерации ассетов\n"
    line = _format_line(report, report_file)
    if SECTION not in text:
        text = text.rstrip() + f"\n\n{SECTION}\n\n{line}\n"
    else:
        before, after = text.split(SECTION, 1)
        body = after.strip()
        lines = [item for item in body.splitlines() if item.strip()]
        key = f"`{report.get('asset_id')}` `{report.get('mode')}`"
        lines = [item for item in lines if key not in item]
        lines.insert(0, line)
        text = before.rstrip() + f"\n\n{SECTION}\n\n" + "\n".join(lines) + "\n"
    target.write_text(text, encoding="utf-8")
    return target


def _format_line(report: dict[str, Any], report_file: Path) -> str:
    outputs = report.get("outputs") or {}
    levels = ",".join(str(item) for item in report.get("levels") or [])
    states = ",".join(str(item) for item in report.get("states") or [])
    rel_report = _rel(report_file)
    manifest = outputs.get("manifest") or "n/a"
    contact = outputs.get("contact_sheet") or "n/a"
    return (
        f"- {date.today().isoformat()}: `{report.get('asset_id')}` `{report.get('mode')}` "
        f"levels `{levels}` states `{states}`; manifest `{manifest}`; "
        f"contact sheet `{contact}`; report `{rel_report}`."
    )


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Path to orchestrator-report.json")
    parser.add_argument("--status", default=str(STATUS_PATH), help="Status markdown path")
    args = parser.parse_args()
    path = update_status(args.report, args.status)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

