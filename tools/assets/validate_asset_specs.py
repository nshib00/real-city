#!/usr/bin/env python3
"""Validate Real City Blender asset specs against local catalog/docs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.assets.blender.real_city.spec import AssetSpec, AssetSpecError, load_asset_spec


@dataclass(frozen=True)
class CatalogEntry:
    type_id: str
    category: str
    footprint: tuple[int, int]
    levels: tuple[int, ...]
    cost_resources: tuple[str, ...]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", nargs="*", help="Spec files or directories. Defaults to docs/assets/specs/**/*.yaml")
    parser.add_argument("--reports-root", default=str(ROOT / "frontend" / "public" / "assets" / "buildings"), help="Root that contains generation-report.json files.")
    parser.add_argument("--require-generation-report", action="store_true", help="Fail when a spec has no generation-report.json yet.")
    parser.add_argument("--skip-generation-report", action="store_true", help="Validate authoring specs before asset generation, without comparing old reports.")
    args = parser.parse_args()

    specs = collect_specs(args.specs)
    if not specs:
        print("No asset specs found.", file=sys.stderr)
        return 2

    catalog = parse_catalog(ROOT / "data" / "buildings" / "catalog-v2.json")
    failures = 0
    for path in specs:
        try:
            spec = load_asset_spec(path)
            errors = validate_against_project(spec, catalog)
            if not args.skip_generation_report:
                errors.extend(validate_generation_report(spec, Path(args.reports_root), require=args.require_generation_report))
        except AssetSpecError as exc:
            errors = [str(exc)]
        if errors:
            failures += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    return 1 if failures else 0


def collect_specs(inputs: list[str]) -> list[Path]:
    if not inputs:
        return [path for path in sorted((ROOT / "docs" / "assets" / "specs").glob("**/*.yaml")) if path.name != "template.yaml"]
    result: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            result.extend(sorted(file for file in path.glob("**/*.yaml") if file.name != "template.yaml"))
            result.extend(sorted(path.glob("**/*.yml")))
            result.extend(sorted(file for file in path.glob("**/*.json") if file.name != "schema.json"))
        else:
            result.append(path)
    return result


def validate_against_project(spec: AssetSpec, catalog: dict[str, CatalogEntry]) -> list[str]:
    errors: list[str] = []
    if spec.kind == "building":
        entry = catalog.get(spec.asset_id)
        if entry is None:
            if spec.raw.get("catalog_status") != "planned":
                errors.append(f"asset_id '{spec.asset_id}' is missing from shared/catalog/buildings.ts")
        else:
            if spec.category != entry.category:
                errors.append(f"category mismatch: spec={spec.category}, catalog={entry.category}")
            if spec.footprint != entry.footprint:
                errors.append(f"footprint mismatch: spec={spec.footprint}, catalog={entry.footprint}")
            documented_future_levels = spec.raw.get("catalog_level_policy") == "documented_future_levels" and set(entry.levels).issubset(spec.level_numbers)
            visual_prototype = (spec.raw.get("catalog_level_policy") == "visual_prototype"
                                and spec.raw.get("output", {}).get("runtime_dir", "").endswith("_test"))
            if spec.level_numbers != entry.levels and not documented_future_levels and not visual_prototype:
                errors.append(f"levels mismatch: spec={spec.level_numbers}, catalog={entry.levels}")
            missing_resources = sorted(set(entry.cost_resources) - set(spec.material_map))
            optional_missing = {"coins"}
            missing_resources = [item for item in missing_resources if item not in optional_missing]
            if missing_resources:
                errors.append("material_map misses catalog cost resources: " + ", ".join(missing_resources))

    references = spec.references
    for key in ("docs", "art_guide", "existing_generators", "existing_assets"):
        values = references.get(key, [])
        if isinstance(values, str):
            values = [values]
        for value in values:
            path = ROOT / value
            if not path.exists():
                errors.append(f"reference does not exist: {value}")
    if spec.style_profile != "aeolian_fantasy_midpoly":
        errors.append("style_profile must be aeolian_fantasy_midpoly for the current factory profile")
    checklist = ROOT / "docs" / "assets" / "blender-generation-checklist.md"
    if not checklist.exists():
        errors.append("style validation checklist is missing: docs/assets/blender-generation-checklist.md")
    profile = spec.png_policy
    expected_camera = (
        "level_emblem_orthographic_three_quarter" if spec.asset_id == "player_level_emblems"
        else "real_city_modular_wall" if spec.asset_id in ("wooden_wall", "stone_wall", "concrete_wall", "modern_wall")
        else "real_city_isometric"
    )
    if profile.get("camera_profile") != expected_camera:
        errors.append(f"png_policy.camera_profile must be {expected_camera}")
    return errors


def validate_generation_report(spec: AssetSpec, reports_root: Path, *, require: bool = False) -> list[str]:
    output_dir = spec.output.get("runtime_dir") or spec.output.get("directory") or spec.output.get("dir")
    candidates = []
    if output_dir:
        candidates.append(ROOT / str(output_dir) / "generation-report.json")
    candidates.append(reports_root / spec.category / spec.asset_id / "generation-report.json")
    report_path = next((path for path in candidates if path.exists()), None)
    if report_path is None:
        return [f"generation-report.json is missing for {spec.asset_id}"] if require else []

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid generation report {report_path}: {exc}"]

    text = json.dumps(report, ensure_ascii=False).lower()
    errors = []
    for resource in sorted(spec.material_map):
        if resource == "coins":
            continue
        aliases = {resource.lower(), resource.replace("_", " ").lower(), resource.replace("_", "-").lower()}
        if not any(alias in text for alias in aliases):
            errors.append(f"generation report does not reflect material resource: {resource}")
    for level in spec.levels:
        key = f"_l{level.level:02d}_"
        if key not in text:
            errors.append(f"generation report has no entries for level {level.level}")
    return errors


def parse_catalog(path: Path) -> dict[str, CatalogEntry]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = {}
        for item in data["buildings"]:
            levels = item.get("upgradeLevels") or [item]
            entries[item["type"]] = CatalogEntry(
                item["type"], item["category"],
                (item["footprint"]["width"], item["footprint"]["height"]),
                tuple(level["level"] for level in levels),
                tuple(sorted({cost["resource"] for level in levels for cost in level["cost"]})),
            )
        return entries
    text = path.read_text(encoding="utf-8")
    entries: dict[str, CatalogEntry] = {}
    for match in re.finditer(r"type:\s*'([^']+)'", text):
        type_id = match.group(1)
        start = text.rfind("{", 0, match.start())
        if start == -1:
            continue
        block = read_brace_block(text, start)
        category = read_string(block, "category")
        width = read_int(block, "width")
        height = read_int(block, "height")
        levels = tuple(sorted({int(value) for value in re.findall(r"\blevel:\s*(\d+)", block)}))
        if not levels:
            root_level = read_int(block, "level")
            levels = (root_level,) if root_level else ()
        cost_resources = tuple(sorted(set(re.findall(r"resource:\s*'([^']+)'", block))))
        if category and width and height and levels:
            entries[type_id] = CatalogEntry(type_id, category, (width, height), levels, cost_resources)
    return entries


def read_brace_block(text: str, start: int) -> str:
    depth = 0
    in_quote = False
    quote = ""
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_quote = False
            continue
        if char in {"'", '"', "`"}:
            in_quote = True
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return text[start:]


def read_string(block: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}:\s*'([^']+)'", block)
    return match.group(1) if match else ""


def read_int(block: str, key: str) -> int:
    match = re.search(rf"\b{re.escape(key)}:\s*(\d+)", block)
    return int(match.group(1)) if match else 0


if __name__ == "__main__":
    raise SystemExit(main())
