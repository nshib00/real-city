#!/usr/bin/env python3
"""Validate LOD0/LOD1/LOD2 naming, triangle budgets and bounds consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from asset_validation_common import load_manifests, resolve_asset_path
from blender.real_city.validation import glb_header

LOD_NAMES = ("LOD0", "LOD1", "LOD2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or asset directories. Defaults to all building manifests.")
    parser.add_argument("--report", help="Write JSON report to this path.")
    parser.add_argument("--allow-planned", action="store_true", help="Accept planned LOD chains without exported LOD files.")
    args = parser.parse_args()

    report = []
    failures = 0
    for manifest in load_manifests(args.paths):
        errors = validate_lods(manifest, allow_planned=args.allow_planned)
        report.append({"manifest": str(manifest.path), "asset_id": manifest.asset_id, "errors": errors})
        if errors:
            failures += 1
            print(f"FAIL {manifest.path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {manifest.path}")
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


def validate_lods(manifest, *, allow_planned: bool) -> list[str]:
    errors: list[str] = []
    policy = manifest.data.get("lod_policy") or {}
    chain = policy.get("chain") or manifest.data.get("lod_chain") or []
    if allow_planned and not chain:
        return errors
    names = [item.get("name") for item in chain if isinstance(item, dict)]
    for name in LOD_NAMES:
        if name not in names:
            errors.append(f"lod policy missing {name}")

    for item in manifest.items:
        label = str(item.get("id") or "")
        lods = item.get("lods") or item.get("lod_chain") or []
        if not lods:
            if allow_planned and chain:
                continue
            errors.append(f"{label}: missing exported LOD records")
            continue
        lod_by_name = {record.get("name"): record for record in lods if isinstance(record, dict)}
        lod0_triangles = None
        for name in LOD_NAMES:
            record = lod_by_name.get(name)
            if not record:
                errors.append(f"{label}: missing {name}")
                continue
            glb = resolve_asset_path(manifest.directory, record.get("glb"))
            if not glb or not glb.exists():
                errors.append(f"{label}: missing {name} GLB")
            elif f"_{name}.glb" not in glb.name:
                errors.append(f"{label}: {name} filename must include _{name}.glb")
            else:
                try:
                    glb_header(glb)
                except Exception as exc:
                    errors.append(f"{label}: invalid {name} GLB: {exc}")
            triangles = record.get("triangles")
            if not isinstance(triangles, int) or triangles <= 0:
                errors.append(f"{label}: {name} triangles must be a positive integer")
            elif name == "LOD0":
                lod0_triangles = triangles
            elif lod0_triangles and triangles > lod0_triangles:
                errors.append(f"{label}: {name} has more triangles than LOD0")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
