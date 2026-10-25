"""Blender-side orchestration for spec-driven Real City asset batches."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .constants import AssetOutput, RenderProfile
from .spec import AssetSpec, load_asset_spec


ROOT = Path(__file__).resolve().parents[4]
GENERATOR_ID = "tools/assets/blender/real_city/orchestrator.py"


@dataclass(frozen=True)
class BatchConfig:
    spec_path: Path
    mode: str
    levels: tuple[int, ...] | None = None
    states: tuple[str, ...] | None = None
    repair_targets: tuple[str, ...] = ()
    read_files: tuple[str, ...] = ()
    skill_files: tuple[str, ...] = ()


def run_from_json(config_path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    config = BatchConfig(
        spec_path=Path(data["spec_path"]),
        mode=str(data["mode"]),
        levels=tuple(data.get("levels") or ()) or None,
        states=tuple(data.get("states") or ()) or None,
        repair_targets=tuple(data.get("repair_targets") or ()),
        read_files=tuple(data.get("read_files") or ()),
        skill_files=tuple(data.get("skill_files") or ()),
    )
    return generate_batch(config)


def generate_batch(config: BatchConfig) -> dict[str, Any]:
    import bpy

    from . import export, geometry, ground, materials, scene
    from .components import COMPONENT_LIBRARY_VERSION, civic, housing, props
    from .state import state_name, unhide_scene_collections

    spec = load_asset_spec(config.spec_path)
    output = _asset_output(spec)
    output.runtime_dir.mkdir(parents=True, exist_ok=True)

    selected_levels = _select_levels(spec, config)
    selected_states = _select_states(spec, config)
    render_png = _should_repair(config, "png") or config.mode in {"preview", "full"}
    export_lods = _should_repair(config, "lod") or config.mode in {"preview", "full"}

    scene.clear_scene()
    asset_scene = bpy.context.scene
    asset_scene.name = f"{spec.asset_id}_{config.mode}_scene"
    profile = _render_profile(spec)
    scene.configure_asset_scene(asset_scene, profile, light_prefix=spec.asset_id)
    palette_overrides = (
        {
            "dark_metal": (0.13, 0.23, 0.25),
            "metal_worn": (0.34, 0.44, 0.43),
            "armor": (0.29, 0.43, 0.43),
            "wood_pale": (0.79, 0.46, 0.19),
            "copper": (0.78, 0.36, 0.12),
        }
        if spec.asset_id == "defense_cannon"
        else {
            "wood_beam": (0.36, 0.20, 0.10),
            "wood_pale": (0.66, 0.42, 0.21),
            "rope": (0.85, 0.80, 0.65),
            "metal_worn": (0.35, 0.40, 0.39),
            "dark_metal": (0.20, 0.27, 0.28),
            "copper": (0.70, 0.46, 0.22),
        } if spec.asset_id == "defense_bolt_thrower"
        else {
            "wood_beam": (0.55, 0.29, 0.13),
            "wood_pale": (0.77, 0.47, 0.23),
            "roof_teal": (0.13, 0.54, 0.57),
        } if spec.asset_id == "tower"
        else {
            "dark_metal": (0.13, 0.20, 0.23),
            "steel_light": (0.48, 0.58, 0.59),
            "copper": (0.76, 0.39, 0.16),
            "armor": (0.27, 0.40, 0.43),
            "glass_cyan": (0.32, 0.73, 0.84),
        } if spec.asset_id == "defense_storm_coil"
        else {
            "resin_amber": (0.24, 0.095, 0.025),
            "resin_highlight": (0.58, 0.30, 0.075),
            "wood_pale": (0.76, 0.48, 0.24),
            "wood_dark": (0.34, 0.20, 0.09),
            "metal_worn": (0.43, 0.44, 0.40),
        } if spec.asset_id == "defense_resin_snare"
        else {
            "dark_metal": (0.14, 0.20, 0.23),
            "steel_light": (0.52, 0.62, 0.64),
            "armor": (0.29, 0.42, 0.46),
            "copper": (0.80, 0.43, 0.18),
            "glass_cyan": (0.38, 0.76, 0.83),
            "reinforced_concrete": (0.61, 0.64, 0.62),
        } if spec.asset_id == "defense_automaton_bay"
        else {
            "concrete": (0.49, 0.62, 0.58),
            "reinforced_concrete": (0.36, 0.52, 0.52),
            "steel_light": (0.37, 0.57, 0.61),
            "dark_metal": (0.12, 0.24, 0.28),
            "armor": (0.22, 0.42, 0.46),
            "brick_warm": (0.68, 0.34, 0.21),
        } if spec.asset_id == "military_factory"
        else {
            "reinforced_concrete": (0.64, 0.70, 0.70),
            "steel_light": (0.40, 0.55, 0.60),
            "dark_metal": (0.08, 0.20, 0.24),
            "armor": (0.17, 0.36, 0.42),
            "roof_teal": (0.06, 0.43, 0.50),
            "glass_cyan": (0.21, 0.78, 0.91),
            "copper": (0.86, 0.45, 0.17),
        } if spec.asset_id == "electronics_workshop"
        else {
            "brick_warm": (0.67, 0.32, 0.18),
            "wood_beam": (0.52, 0.29, 0.13),
            "wood_pale": (0.77, 0.52, 0.25),
            "copper": (0.84, 0.43, 0.17),
            "steel_light": (0.56, 0.61, 0.60),
            "dark_metal": (0.19, 0.25, 0.27),
            "roof_teal": (0.15, 0.44, 0.48),
            "armor": (0.34, 0.42, 0.42),
        } if spec.asset_id == "mechanical_workshop"
        else None
    )
    mats = materials.create_palette(f"MAT_{spec.asset_id}", overrides=palette_overrides)

    collections = {}
    items: list[dict[str, Any]] = []
    for level in selected_levels:
        for state in selected_states:
            name = state_name(spec.asset_id, level, state)
            collection = geometry.create_collection(name)
            _build_state_model(spec, collection, mats, level=level, state=state)
            for obj in collection.all_objects:
                obj["real_city_asset"] = spec.asset_id
                obj["real_city_level"] = level
                obj["real_city_state"] = state
                obj["component_library_version"] = COMPONENT_LIBRARY_VERSION
                obj["generator"] = GENERATOR_ID
            geometry.clean_meshes(collection)
            collections[name] = collection

            item: dict[str, Any] = {
                "id": name,
                "level": level,
                "state": state,
                "triangles": geometry.collection_triangle_count(collection),
                "bounds": geometry.collection_bounds(collection),
            }
            if export_lods:
                lods = export.export_lod_glbs(name, collection, output.runtime_dir, list(spec.lod_policy.get("chain") or []), scene=asset_scene)
                item["lods"] = [_rel_lod(record, output.runtime_dir, spec) for record in lods]
                lod0 = next((record for record in item["lods"] if record["name"] == "LOD0"), item["lods"][0] if item["lods"] else None)
                item["glb"] = lod0["glb"] if lod0 else None
            if render_png:
                from .state import show_only

                show_only(name, scene=asset_scene)
                png = export.render_png(output.runtime_dir / f"{name}.png", scene=asset_scene)
                item["png"] = _rel_output(png, spec)
            items.append(item)

    source_blend = None
    combined_glb = None
    if not _repair_only(config, {"png", "contact-sheet"}):
        source_blend = export.save_blend(output.blend_path)
        unhide_scene_collections(asset_scene)
        combined_glb = export.export_combined_glb(output.combined_glb_path, scene=asset_scene)

    manifest_path = output.manifest_path
    if _should_repair(config, "manifest") or config.mode in {"preview", "full"}:
        export.write_manifest(
            manifest_path,
            asset_id=spec.asset_id,
            display_name=spec.display_name,
            category=spec.category,
            levels=selected_levels,
            states=selected_states,
            items=items,
            source_blend=_rel_output(source_blend, spec) if source_blend else None,
            combined_glb=_rel_output(combined_glb, spec) if combined_glb else None,
            material_map=spec.material_map,
            extra={
                "spec_path": str(config.spec_path.relative_to(ROOT) if config.spec_path.is_absolute() else config.spec_path),
                "generation_mode": config.mode,
                "component_library_version": COMPONENT_LIBRARY_VERSION,
                "lod_policy": spec.lod_policy,
                "png_policy": spec.png_policy,
            },
        )

    report = _build_report(
        spec,
        config,
        selected_levels,
        selected_states,
        items,
        component_library_version=COMPONENT_LIBRARY_VERSION,
        source_blend=source_blend,
        combined_glb=combined_glb,
    )
    report_path = output.runtime_dir / "orchestrator-report.json"
    export.write_generation_report(report_path, report)
    print("REAL_CITY_ASSET_ORCHESTRATOR_COMPLETE", json.dumps({"asset_id": spec.asset_id, "mode": config.mode, "report": str(report_path)}, ensure_ascii=False))
    return report


def make_execution_brief(spec: AssetSpec, *, read_files: tuple[str, ...] = (), skill_files: tuple[str, ...] = ()) -> str:
    level_span = f"{spec.level_numbers[0]}-{spec.level_numbers[-1]}" if len(spec.level_numbers) > 1 else str(spec.level_numbers[0])
    materials = ", ".join(spec.material_map.keys()) or "none"
    skills = [item for group in spec.skill_profile.values() for item in group]
    return "\n".join(
        [
            f"asset_id: {spec.asset_id}",
            f"display_name: {spec.display_name}",
            f"category/kind: {spec.category}/{spec.kind}",
            f"levels: {level_span}",
            f"states: {', '.join(spec.states)}",
            f"style: {spec.style_profile}",
            f"materials: {materials}",
            f"skills: {', '.join(skills)}",
            "lod: " + ", ".join(str(item.get("name")) for item in spec.lod_policy.get("chain", [])),
            f"png: {spec.png_policy.get('sprite_size')} anchor={spec.png_policy.get('anchor')}",
            "read_files: " + (", ".join(read_files) if read_files else "none"),
            "skill_files: " + (", ".join(skill_files) if skill_files else "none"),
        ]
    )


def _build_state_model(spec: AssetSpec, collection, mats: dict, *, level: int, state: str) -> None:
    from . import ground
    from .components import civic, housing, props

    damaged = state == "damaged"
    construction = state == "construction"
    ground.add_ground_tile(collection, mats, prefix=f"{spec.asset_id}_l{level:02d}", include_path=True)

    if spec.asset_id == "dugout":
        housing.add_dugout_shell(spec.asset_id, collection, mats, level=level, damaged=damaged)
        housing.add_housing_yard(spec.asset_id, collection, mats, level=level, damaged=damaged)
    elif spec.asset_id == "wood_house":
        housing.add_wood_house_shell(spec.asset_id, collection, mats, level=level, damaged=damaged)
        housing.add_housing_yard(spec.asset_id, collection, mats, level=level, damaged=damaged)
    elif spec.asset_id == "stone_house":
        housing.add_stone_house_shell(spec.asset_id, collection, mats, level=level, damaged=damaged, rune_roof=level >= 4)
        housing.add_housing_yard(spec.asset_id, collection, mats, level=level, damaged=damaged)
    elif spec.asset_id == "town_hall":
        civic.add_plaza(f"{spec.asset_id}_plaza", collection, mats)
        civic.add_town_hall_core(spec.asset_id, collection, mats, level=level, damaged=damaged)
        civic.add_notice_board(f"{spec.asset_id}_notice", collection, mats)
    elif spec.asset_id == "defense_cannon":
        from .components import cannon

        cannon.add_cannon(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_stakes":
        from .components import stakes

        stakes.add_stakes(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_bolt_thrower":
        from .components import bolt_thrower

        bolt_thrower.add_bolt_thrower(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "tower":
        from .components import watchtower

        watchtower.add_watchtower(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_storm_coil":
        from .components import storm_coil

        storm_coil.add_storm_coil(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_resin_snare":
        from .components import resin_snare

        resin_snare.add_resin_snare(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_automaton_bay":
        from .components import automaton_bay

        automaton_bay.add_automaton_bay(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "defense_guardian_enclosure":
        from .components import guardian_enclosure

        guardian_enclosure.add_guardian_enclosure(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "crystal_greenhouse":
        from .components import crystal_greenhouse

        crystal_greenhouse.add_crystal_greenhouse(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "dye_garden":
        from .components import dye_garden

        dye_garden.add_dye_garden(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "brick_yard":
        from .components import brick_yard

        brick_yard.add_brick_yard(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "cement_workshop":
        from .components import cement_workshop

        cement_workshop.add_cement_workshop(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "concrete_plant":
        from .components import concrete_plant

        concrete_plant.add_concrete_plant(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "foundry":
        from .components import foundry

        foundry.add_foundry(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "military_factory":
        from .components import military_factory

        military_factory.add_military_factory(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "paper_workshop":
        from .components import paper_workshop

        paper_workshop.add_paper_workshop(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "tile_factory":
        from .components import tile_factory

        tile_factory.add_tile_factory(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "weaving_yard":
        from .components import weaving_yard

        weaving_yard.add_weaving_yard(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "paint_workshop":
        from .components import paint_workshop

        paint_workshop.add_paint_workshop(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "electronics_workshop":
        from .components import electronics_workshop

        electronics_workshop.add_electronics_workshop(collection, mats, level=level, state=state)
        return
    elif spec.asset_id == "mechanical_workshop":
        from .components import mechanical_workshop

        mechanical_workshop.add_mechanical_workshop(collection, mats, level=level, state=state)
        return
    elif spec.asset_id in {"oil_press", "oil_refinery", "resin_kiln", "steelworks", "sulfur_spring"}:
        from .components import process_industry

        getattr(process_industry, f"add_{spec.asset_id}")(collection, mats, level=level, state=state)
        return
    else:
        raise ValueError(f"Unsupported asset_id for phase-4 component orchestrator: {spec.asset_id}")

    if construction:
        props.add_construction_scaffold(f"{spec.asset_id}_construction_scaffold", collection, mats, width=1.45, height=1.08)
        props.add_plank_stack(f"{spec.asset_id}_construction_planks", collection, mats, (-0.94, -0.74, 0.12), rows=3, count=5)
    elif damaged:
        props.add_scattered_debris(f"{spec.asset_id}_damage_debris", collection, mats, count=10)


def _select_levels(spec: AssetSpec, config: BatchConfig) -> tuple[int, ...]:
    if config.levels:
        requested = set(config.levels)
        return tuple(level for level in spec.level_numbers if level in requested)
    if config.mode == "preview":
        numbers = spec.level_numbers
        return tuple(dict.fromkeys((numbers[0], numbers[len(numbers) // 2], numbers[-1])))
    return spec.level_numbers


def _select_states(spec: AssetSpec, config: BatchConfig) -> tuple[str, ...]:
    if config.states:
        requested = set(config.states)
        return tuple(state for state in spec.states if state in requested)
    if config.mode == "preview":
        include = set((spec.png_policy.get("contact_sheet") or {}).get("include_states") or spec.states)
        return tuple(state for state in spec.states if state in include)
    return spec.states


def _asset_output(spec: AssetSpec) -> AssetOutput:
    use_public = bool(spec.output.get("use_public_glb", True))
    return AssetOutput(spec.asset_id, spec.category, ROOT, use_public_glb=use_public)


def _render_profile(spec: AssetSpec) -> RenderProfile:
    png = spec.png_policy
    return RenderProfile(sprite_size=tuple(png.get("sprite_size", (512, 384))), anchor=tuple(png.get("anchor", (256, 292))))


def _rel_output(path: str | Path | None, spec: AssetSpec) -> str | None:
    if path is None:
        return None
    value = Path(path)
    try:
        return str(PurePosixPath(value.relative_to(ROOT)))
    except ValueError:
        return str(value)


def _rel_lod(record: dict[str, Any], output_dir: Path, spec: AssetSpec) -> dict[str, Any]:
    item = dict(record)
    item["glb"] = _rel_output(item["glb"], spec)
    return item


def _should_repair(config: BatchConfig, target: str) -> bool:
    return config.mode == "repair" and target in set(config.repair_targets)


def _repair_only(config: BatchConfig, targets: set[str]) -> bool:
    return config.mode == "repair" and set(config.repair_targets).issubset(targets)


def _build_report(
    spec: AssetSpec,
    config: BatchConfig,
    levels: tuple[int, ...],
    states: tuple[str, ...],
    items: list[dict[str, Any]],
    *,
    component_library_version: str,
    source_blend: Path | None,
    combined_glb: Path | None,
) -> dict[str, Any]:
    brief = make_execution_brief(spec, read_files=config.read_files, skill_files=config.skill_files)
    return {
        "asset_id": spec.asset_id,
        "display_name": spec.display_name,
        "category": spec.category,
        "mode": config.mode,
        "preview_status": "passed" if config.mode == "preview" else None,
        "levels": list(levels),
        "states": list(states),
        "items": items,
        "outputs": {
            "blend": _rel_output(source_blend, spec),
            "combined_glb": _rel_output(combined_glb, spec),
            "manifest": f"frontend/public/assets/buildings/{spec.category}/{spec.asset_id}/manifest.json",
            "contact_sheet": f"frontend/public/assets/buildings/{spec.category}/{spec.asset_id}/{spec.asset_id}_{config.mode}_contact_sheet.png",
        },
        "component_library_version": component_library_version,
        "generator": GENERATOR_ID,
        "spec_path": str(config.spec_path),
        "token_budget_policy": {
            "read_files": list(config.read_files),
            "skill_files": list(config.skill_files),
            "long_logs": "write to output report files, not chat",
        },
        "production_brief": brief,
    }
