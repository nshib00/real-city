#!/usr/bin/env python3
"""Create deterministic contact sheets for Real City building PNG batches."""

from __future__ import annotations

import argparse
from pathlib import Path

from asset_validation_common import load_manifests, parse_level_state, resolve_asset_path
from blender.real_city.export import make_contact_sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or asset directories. Defaults to all building manifests.")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--preview", action="store_true", help="Include only active/construction/damaged states.")
    parser.add_argument("--output-name", default="contact-sheet.png")
    args = parser.parse_args()

    states = {"active", "construction", "damaged"} if args.preview else None
    failures = 0
    for manifest in load_manifests(args.paths):
        image_paths = []
        for item in sorted(manifest.items, key=lambda i: (int(i.get("level", 0)), str(i.get("state", "")), str(i.get("id", "")))):
            state = item.get("state")
            if not state:
                parsed = parse_level_state(str(item.get("id") or ""))
                state = parsed[1] if parsed else None
            if states and state not in states:
                continue
            path = resolve_asset_path(manifest.directory, item.get("png"))
            if path and path.exists():
                image_paths.append(path)
        if not image_paths:
            failures += 1
            print(f"FAIL {manifest.path}: no PNG files for contact sheet")
            continue
        output = manifest.directory / args.output_name
        make_contact_sheet(image_paths, output, columns=args.columns)
        print(f"PASS {output}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
