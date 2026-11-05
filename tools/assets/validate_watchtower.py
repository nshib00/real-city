#!/usr/bin/env python3
"""Validate the complete six-level, four-state watchtower asset batch."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "frontend/public/assets/buildings/defense/tower"
SPEC = ROOT / "docs/assets/specs/defense/tower.json"
LEVELS = tuple(range(1, 7))
STATES = ("construction", "active", "damaged", "ruined")
LODS = ("LOD0", "LOD1", "LOD2")


def main() -> int:
    errors: list[str] = []
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((ASSETS / "orchestrator-report.json").read_text(encoding="utf-8"))

    expected = {f"tower_l{level:02d}_{state}" for level in LEVELS for state in STATES}
    check(spec.get("states") == list(STATES), "spec states must cover all four variants", errors)
    check([entry["level"] for entry in spec.get("levels", [])] == list(LEVELS),
          "spec levels must cover 1–6 without concept-only levels", errors)
    check("concept_levels" not in spec, "concept_levels must be removed", errors)
    check(manifest.get("levels") == list(LEVELS), "manifest levels must be 1–6", errors)
    check(manifest.get("states") == list(STATES), "manifest states must cover all four variants", errors)
    items = {entry["id"]: entry for entry in manifest.get("items", [])}
    check(set(items) == expected, f"manifest variants: expected {len(expected)}, got {len(items)}", errors)
    check(report.get("mode") == "full", "generation report must be full", errors)
    check({entry["id"] for entry in report.get("items", [])} == expected,
          "report variants must match manifest", errors)

    for stem in sorted(expected):
        item = items.get(stem)
        if item is None:
            continue
        png = asset_path(item.get("png"), errors)
        if png and png.exists():
            with Image.open(png) as image:
                check(image.size == (512, 384), f"{stem}: PNG size {image.size}", errors)
                check(image.mode == "RGBA", f"{stem}: PNG must be RGBA", errors)
                bounds = image.getchannel("A").getbbox()
                check(bounds is not None, f"{stem}: empty PNG", errors)
                if bounds:
                    check(bounds[0] > 8 and bounds[1] > 8 and bounds[2] < 504 and bounds[3] < 376,
                          f"{stem}: cropped sprite {bounds}", errors)
        lods = {entry.get("name"): entry for entry in item.get("lods", [])}
        check(set(lods) == set(LODS), f"{stem}: LOD0/1/2 required", errors)
        for lod in LODS:
            record = lods.get(lod)
            if not record:
                continue
            glb = asset_path(record.get("glb"), errors)
            if glb and glb.exists():
                with glb.open("rb") as stream:
                    check(stream.read(4) == b"glTF", f"{stem}/{lod}: invalid GLB", errors)
            check(120 <= record.get("triangles", 0) <= (5000 if lod == "LOD0" else 3200 if lod == "LOD1" else 1900),
                  f"{stem}/{lod}: triangle budget", errors)
        if "LOD0" in lods:
            check(item.get("triangles") == lods["LOD0"].get("triangles"),
                  f"{stem}: LOD0 triangle count mismatch", errors)

    for level in LEVELS:
        variants = [items.get(f"tower_l{level:02d}_{state}") for state in STATES]
        if not all(variants):
            continue
        tops = {state: variants[index]["bounds"][2][1] for index, state in enumerate(STATES)}
        check(tops["ruined"] + 0.5 < tops["damaged"] < tops["active"],
              f"L{level}: ruined/damaged/active silhouette heights {tops}", errors)
        check(tops["construction"] + 0.5 < tops["active"],
              f"L{level}: construction must be visibly incomplete {tops}", errors)
        footprints = [tuple(tuple(axis) for axis in variant["bounds"][:2]) for variant in variants]
        check(len(set(footprints)) == 1, f"L{level}: variant footprint mismatch", errors)

    for key in ("source_blends", "combined_glbs"):
        values = manifest.get(key, [])
        check(len(values) == 24, f"{key}: one source per variant required", errors)
        for value in values:
            path = asset_path(value, errors)
            if path and path.exists():
                check(path.stat().st_size > 1024, f"{key}: file too small", errors)
                with path.open("rb") as stream:
                    header = stream.read(7)
                    valid = header.startswith((b"BLENDER", b"\x28\xb5\x2f\xfd")) if key == "source_blends" else header.startswith(b"glTF")
                    check(valid, f"{key}: invalid file {value}", errors)
    sheet = ASSETS / "tower_full_contact_sheet.png"
    check(sheet.is_file() and sheet.stat().st_size > 1024, "full contact sheet missing", errors)
    if errors:
        for error in errors:
            print("FAIL", error)
        return 1
    print("PASS watchtower: 6 levels × 4 states, 24 PNG, 72 LOD GLB, 24 source blends, 24 combined GLB, contact sheet")
    return 0


def asset_path(value: str | None, errors: list[str]) -> Path | None:
    if not value:
        errors.append("missing asset path")
        return None
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ASSETS.resolve()):
        errors.append(f"path outside tower assets: {value}")
        return None
    if not path.is_file():
        errors.append(f"missing file: {value}")
    return path


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


if __name__ == "__main__":
    raise SystemExit(main())
