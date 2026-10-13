#!/usr/bin/env python3
"""Validate building manifest completeness and file references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from asset_validation_common import existing_items_by_key, item_id, load_manifests, resolve_asset_path
from blender.real_city.validation import glb_header


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or asset directories. Defaults to all building manifests.")
    parser.add_argument("--report", help="Write JSON report to this path.")
    parser.add_argument("--skip-glb-header", action="store_true", help="Only check GLB existence, not GLB header validity.")
    parser.add_argument("--require-triangles", action="store_true", help="Fail when items do not store triangle metadata.")
    parser.add_argument("--require-bounds-metadata", action="store_true", help="Fail when items do not store bounds/alpha_bounds metadata.")
    args = parser.parse_args()

    report = []
    failures = 0
    for manifest in load_manifests(args.paths):
        errors = validate_manifest(
            manifest,
            check_glb_header=not args.skip_glb_header,
            require_triangles=args.require_triangles,
            require_bounds_metadata=args.require_bounds_metadata,
        )
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


def validate_manifest(manifest, *, check_glb_header: bool, require_triangles: bool, require_bounds_metadata: bool) -> list[str]:
    errors: list[str] = []
    data = manifest.data
    if not manifest.asset_id:
        errors.append("missing required field: asset_id")
    if not manifest.category:
        errors.append("missing required field: category")
    if not manifest.levels:
        errors.append("missing required field: levels")
    if not manifest.states:
        errors.append("missing required field: states")
    if data.get("sprite"):
        sprite = data["sprite"]
        if tuple(sprite.get("size", ())) != (512, 384):
            errors.append("sprite.size must be [512, 384]")
        if tuple(sprite.get("anchor", ())) != (256, 292):
            errors.append("sprite.anchor must be [256, 292]")

    items = existing_items_by_key(manifest)
    expected = {(level, state) for level in manifest.levels for state in manifest.states}
    missing = sorted(expected - set(items))
    for level, state in missing:
        errors.append(f"missing manifest item for {item_id(manifest.asset_id, level, state)}")

    for key, item in sorted(items.items()):
        level, state = key
        label = str(item.get("id") or item_id(manifest.asset_id, level, state))
        parsed_level_state = (level, state)
        if item.get("level") is None and not parsed_level_state:
            errors.append(f"{label}: missing metadata level")
        if item.get("state") is None and not parsed_level_state:
            errors.append(f"{label}: missing metadata state")
        if require_triangles and item.get("triangles") is None:
            errors.append(f"{label}: missing metadata triangles")
        if require_bounds_metadata and item.get("bounds") is None and item.get("alpha_bounds") is None:
            errors.append(f"{label}: missing bounds or alpha_bounds metadata")
        for field in ("png", "glb"):
            path = resolve_asset_path(manifest.directory, item.get(field))
            if path is None:
                errors.append(f"{label}: missing {field} reference")
            elif not path.exists() or path.stat().st_size <= 0:
                errors.append(f"{label}: missing or empty {field}: {path}")
            elif field == "glb" and check_glb_header:
                try:
                    glb_header(path)
                except Exception as exc:
                    errors.append(f"{label}: invalid GLB {path}: {exc}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
