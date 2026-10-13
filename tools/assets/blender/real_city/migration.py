"""Compatibility layer for migrating legacy Blender generators.

This module intentionally does not rebuild geometry. Legacy generators can keep
their proven mesh construction while writing the same manifest/report/fixture
contract as the spec-driven orchestrator.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .constants import ANCHOR, SPRITE_SIZE
from .export import make_contact_sheet, write_generation_report, write_manifest
from .geometry import collection_bounds, collection_triangle_count
from .paths import project_root


_STATE_RE = re.compile(r"^(?P<asset>.+)_l(?P<level>\d{2})_(?P<state>.+)$")


@dataclass(frozen=True)
class LegacyAssetMigration:
    asset_id: str
    display_name: str
    category: str
    output_dir: Path
    levels: Iterable[int]
    states: Iterable[str]
    source_blend: str | Path | None = None
    combined_glb: str | Path | None = None
    generator: str | None = None
    style_reference: str = "Real City bright fantasy stylized mid-poly"
    lod_chain: tuple[dict, ...] = (
        {"name": "LOD0", "ratio": 1.0},
        {"name": "LOD1", "ratio": 0.55},
        {"name": "LOD2", "ratio": 0.28},
    )


def finalize_legacy_asset_generation(config: LegacyAssetMigration) -> dict:
    """Write shared migration artifacts for a legacy generator.

    The function reads collections and already rendered/exported files from the
    current Blender scene. It does not mutate source geometry and is safe to add
    at the end of existing generators.
    """

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    levels = tuple(config.levels)
    states = tuple(config.states)
    collections = _collect_state_collections(config.asset_id, levels, states)
    items = [_state_item(config, collection) for collection in collections]
    report = _migration_report(config, items, levels, states)

    write_manifest(
        output_dir / "manifest.json",
        asset_id=config.asset_id,
        display_name=config.display_name,
        category=config.category,
        levels=levels,
        states=states,
        items=items,
        source_blend=_project_relative(config.source_blend or output_dir / f"{config.asset_id}_levels.blend"),
        combined_glb=_project_relative(config.combined_glb or output_dir / f"{config.asset_id}_levels.glb"),
        material_map=_existing_material_map(output_dir / "manifest.json"),
        extra={
            "generated_at": date.today().isoformat(),
            "generator": config.generator,
            "style_reference": config.style_reference,
            "lod_policy": {
                "chain": list(config.lod_chain),
                "status": "planned_for_phase_4_orchestrator_exports; legacy files keep historical filenames",
            },
            "migration": {
                "phase": 5,
                "visual_geometry_source": "legacy_generator",
                "contract": "shared scene/export/report/fixture metadata",
            },
        },
    )
    write_generation_report(output_dir / "generation-report.json", report)
    _write_fixture(config, items, report, levels, states)
    _try_contact_sheet(config, items, states)
    return report


def _collect_state_collections(asset_id: str, levels: Iterable[int], states: Iterable[str]) -> list:
    import bpy

    collections = []
    for level in levels:
        for state in states:
            name = f"{asset_id}_l{int(level):02d}_{state}"
            collection = bpy.data.collections.get(name)
            if collection is not None:
                collections.append(collection)
    return collections


def _state_item(config: LegacyAssetMigration, collection) -> dict:
    match = _STATE_RE.match(collection.name)
    if not match:
        raise ValueError(f"Unsupported legacy collection name: {collection.name}")
    level = int(match.group("level"))
    state = match.group("state")
    glb_path = config.output_dir / f"{collection.name}.glb"
    png_path = config.output_dir / f"{collection.name}.png"
    triangles = collection_triangle_count(collection)
    return {
        "id": collection.name,
        "level": level,
        "state": state,
        "glb": _project_relative(glb_path),
        "png": _project_relative(png_path),
        "triangles": triangles,
        "bounds": collection_bounds(collection),
        "sprite": {"size": list(SPRITE_SIZE), "anchor": list(ANCHOR)},
        "compatibility": {
            "glb_exists": glb_path.exists(),
            "png_exists": png_path.exists(),
            "legacy_filename": True,
        },
    }


def _migration_report(config: LegacyAssetMigration, items: list[dict], levels: tuple[int, ...], states: tuple[str, ...]) -> dict:
    triangle_values = [item["triangles"] for item in items]
    by_state = {}
    for item in items:
        by_state.setdefault(item["state"], []).append(item["triangles"])
    return {
        "asset_id": config.asset_id,
        "display_name": config.display_name,
        "category": config.category,
        "generated_at": date.today().isoformat(),
        "generator": config.generator,
        "migration_phase": 5,
        "style_reference": config.style_reference,
        "sprite": {"size": list(SPRITE_SIZE), "anchor": list(ANCHOR)},
        "levels": list(levels),
        "states": list(states),
        "models": len(items),
        "triangle_range": _range(triangle_values),
        "triangle_ranges_by_state": {state: _range(values) for state, values in by_state.items()},
        "lod_policy": list(config.lod_chain),
        "items": {item["id"]: item for item in items},
    }


def _write_fixture(config: LegacyAssetMigration, items: list[dict], report: dict, levels: tuple[int, ...], states: tuple[str, ...]) -> Path:
    root = project_root()
    fixture_dir = root / "tools" / "assets" / "tests" / "fixtures" / "blender-assets"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture = {
        "asset_id": config.asset_id,
        "category": config.category,
        "levels": list(levels),
        "states": list(states),
        "sprite": report["sprite"],
        "triangle_range": report["triangle_range"],
        "triangle_ranges_by_state": report["triangle_ranges_by_state"],
        "bounds": {item["id"]: item["bounds"] for item in items},
        "expected_files": {
            item["id"]: {"glb": item["glb"], "png": item["png"]}
            for item in items
        },
    }
    path = fixture_dir / f"{config.asset_id}.json"
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _try_contact_sheet(config: LegacyAssetMigration, items: list[dict], states: tuple[str, ...]) -> None:
    image_paths = [config.output_dir / f"{item['id']}.png" for item in items]
    if not all(path.exists() for path in image_paths):
        return
    try:
        make_contact_sheet(image_paths, config.output_dir / f"{config.asset_id}_contact_sheet.png", columns=len(states))
    except Exception:
        return


def _range(values: list[int]) -> dict:
    if not values:
        return {"min": 0, "max": 0}
    return {"min": min(values), "max": max(values)}


def _existing_material_map(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    material_map = manifest.get("material_map") or manifest.get("material_mapping")
    return material_map if isinstance(material_map, dict) else {}


def _project_relative(path: str | Path | None) -> str | None:
    if path is None:
        return None
    target = Path(path)
    if not target.is_absolute():
        return target.as_posix()
    root = project_root(target)
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return target.as_posix()
