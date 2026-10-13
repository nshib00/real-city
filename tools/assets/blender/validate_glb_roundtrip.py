#!/usr/bin/env python3
"""Blender entrypoint for GLB roundtrip validation.

Run with:
  blender --background --python tools/assets/blender/validate_glb_roundtrip.py -- --limit 48
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS_ASSETS = ROOT / "tools" / "assets"
if str(TOOLS_ASSETS) not in sys.path:
    sys.path.insert(0, str(TOOLS_ASSETS))

from asset_validation_common import load_manifests, resolve_asset_path
from blender.real_city.validation import validate_glb_roundtrip


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or directories. Defaults to all building manifests.")
    parser.add_argument("--limit", type=int, default=48, help="Limit imported GLBs for local smoke checks. 0 means all.")
    parser.add_argument("--report", default="/tmp/real-city-glb-roundtrip.json")
    args = parser.parse_args(argv)

    glbs = []
    for manifest in load_manifests(args.paths):
        for item in manifest.items:
            path = resolve_asset_path(manifest.directory, item.get("glb"))
            if path and path.exists():
                glbs.append(path)
    glbs = sorted(dict.fromkeys(glbs))
    if args.limit > 0:
        glbs = glbs[: args.limit]
    if not glbs:
        print("No GLB files found for roundtrip validation.", file=sys.stderr)
        return 2

    results = validate_glb_roundtrip(glbs)
    failures = [item for item in results if not item.get("ok")]
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked": len(results), "failures": len(failures), "report": str(target)}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    raise SystemExit(main(args))
