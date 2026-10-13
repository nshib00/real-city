#!/usr/bin/env python3
"""Validate building PNG sprite size, alpha bounds and anchor alignment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from asset_validation_common import load_manifests, resolve_asset_path

DEFAULT_SIZE = (512, 384)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or asset directories. Defaults to all building manifests.")
    parser.add_argument("--report", help="Write JSON report to this path.")
    parser.add_argument("--min-opaque", type=int, default=1200)
    parser.add_argument("--max-edge-margin", type=int, default=10)
    parser.add_argument("--anchor-tolerance", type=int, default=18)
    args = parser.parse_args()

    report = []
    failures = 0
    for manifest in load_manifests(args.paths):
        errors = []
        expected_size = manifest.data.get("sprite", {}).get("size") if isinstance(manifest.data.get("sprite"), dict) else None
        expected_size = expected_size or manifest.data.get("spriteSize") or manifest.data.get("size") or DEFAULT_SIZE
        expected_size = tuple(int(value) for value in expected_size)
        for item in manifest.items:
            path = resolve_asset_path(manifest.directory, item.get("png"))
            label = item.get("id") or path
            if not path or not path.exists():
                errors.append(f"{label}: missing PNG")
                continue
            result = validate_png(path, expected_size=expected_size, min_opaque=args.min_opaque, max_edge_margin=args.max_edge_margin, anchor_tolerance=args.anchor_tolerance)
            if result["errors"]:
                errors.extend(f"{label}: {error}" for error in result["errors"])
            report.append({"manifest": str(manifest.path), "id": str(label), **result})
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


def validate_png(path: Path, *, expected_size: tuple[int, int], min_opaque: int, max_edge_margin: int, anchor_tolerance: int) -> dict:
    errors: list[str] = []
    with Image.open(path) as image:
        image = image.convert("RGBA")
        if image.size != expected_size:
            errors.append(f"size must be {expected_size}, got {image.size}")
        alpha = image.getchannel("A")
        bbox = alpha.point(lambda value: 255 if value >= 8 else 0).getbbox()
        if not bbox:
            return {"path": str(path), "size": list(image.size), "alpha_bounds": None, "opaque_pixels": 0, "errors": ["empty transparent render"]}
        opaque_pixels = sum(1 for value in alpha.getdata() if value >= 8)
        if opaque_pixels < min_opaque:
            errors.append(f"too few opaque pixels: {opaque_pixels} < {min_opaque}")
        left, top, right, bottom = bbox
        width, height = image.size
        if left < max_edge_margin or top < max_edge_margin or right > width - max_edge_margin or bottom > height - 1:
            errors.append(f"alpha bounds too close to frame edge: {bbox}")
        if expected_size == DEFAULT_SIZE:
            expected_baseline_y = expected_size[1] - 16
            if abs(bottom - expected_baseline_y) > anchor_tolerance:
                errors.append(f"bottom alpha bound {bottom} is not aligned with sprite baseline y={expected_baseline_y}")
        small = image.resize((128, 96), Image.Resampling.LANCZOS)
        small_alpha = small.getchannel("A").point(lambda value: 255 if value >= 8 else 0)
        if not small_alpha.getbbox():
            errors.append("small-scale readability check failed: sprite disappears at 128x96")
        return {"path": str(path), "size": list(image.size), "alpha_bounds": list(bbox), "opaque_pixels": opaque_pixels, "errors": errors}


if __name__ == "__main__":
    raise SystemExit(main())
