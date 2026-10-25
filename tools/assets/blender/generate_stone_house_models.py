"""Production stone house models: levels 1-6 in all documented states."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy

from tools.assets.blender.real_city import AssetOutput, RenderProfile
from tools.assets.blender.real_city import export, geometry, ground, materials, scene
from tools.assets.blender.real_city.components import COMPONENT_LIBRARY_VERSION
from tools.assets.blender.real_city.components import housing, stone_house_architecture, stone_house_decor, stone_house_pilot, stone_house_variants
from tools.assets.blender.real_city.state import state_name

ASSET_ID = "stone_house"
DISPLAY_NAME = "Каменный дом"
CATEGORY = "housing"
LEVELS = tuple(range(1, 7))
STATES = ("active", "construction", "damaged")
FOOTPRINT_AREA_MULTIPLIER = 1.10
FOOTPRINT_SCALE = math.sqrt(FOOTPRINT_AREA_MULTIPLIER)


def build_model(collection, mats: dict, *, level: int = 1, state: str = "active") -> None:
    if level not in LEVELS or state not in STATES:
        raise ValueError(f"Unsupported stone house pilot variant: {level=} {state=}")
    ground.add_ground_tile(collection, mats, prefix=ASSET_ID, include_path=True)
    name = f"pilot_stone_house_l{level:02d}"
    if level == 6:
        stone_house_pilot.add_level_six_wood_yard(f"{name}_yard", collection, mats, level=level)
        stone_house_architecture.add_level_six_house(name, collection, mats, state=state)
    elif state == "construction":
        stone_house_variants.add_construction(name, collection, mats, level=level)
    else:
        damaged = state == "damaged"
        _width, _depth, shell_height = stone_house_variants.dimensions(level)
        housing.add_stone_house_shell(name, collection, mats, level=level, damaged=damaged,
                                      detailed_pilot=True,
                                      footprint_scale=FOOTPRINT_SCALE * (1.08 if level >= 5 else 1.0),
                                      height_override=shell_height if level >= 4 else None,
                                      window_scale=1.30 if level >= 4 else 1.0)
        stone_house_pilot.add_level_six_wood_yard(f"{name}_yard", collection, mats, level=level)
        _add_pilot_decor(name, collection, mats, level=level, damaged=damaged)
        stone_house_variants.add_progression(name, collection, mats, level=level, damaged=damaged)
        if damaged:
            stone_house_variants.add_damage(name, collection, mats, level=level)

    for obj in collection.all_objects:
        obj["real_city_asset"] = ASSET_ID
        obj["real_city_level"] = level
        obj["real_city_state"] = state
        obj["component_library_version"] = COMPONENT_LIBRARY_VERSION
        obj["asset_source"] = "tools/assets/blender/generate_stone_house_models.py"


def _add_pilot_decor(name, collection, mats, *, level: int, damaged: bool) -> None:
    width, depth, height = stone_house_variants.dimensions(level)
    front_y = -depth / 2 - 0.095
    roof_z = 0.22 + height
    ridge_z = roof_z + 0.39 + 0.075
    decor = stone_house_decor
    decor.add_keystone_sun(f"{name}_decor_keystone", collection, mats, (0, front_y, 1.04))
    for side in (-1, 1):
        decor.add_window_drain_lip(f"{name}_decor_sill_{side}", collection, mats,
                                   (side * width * 0.28, front_y, 0.68), width=0.39)
    decor.add_ridge_copper_clasp(f"{name}_decor_ridge_clasp", collection, mats,
                                 (0, 0.22, ridge_z))
    decor.add_roof_leaf_finial(f"{name}_decor_finial", collection, mats,
                               (0, depth / 2 + 0.07, ridge_z))
    if not damaged:
        decor.add_chimney_copper_crown(f"{name}_decor_chimney_crown", collection, mats,
                                   (-width * 0.34, depth * 0.20, roof_z + 0.14 + 0.42 * 0.54))
    decor.add_dormer_side_fins(f"{name}_decor_dormer_fins", collection, mats,
                               (-0.28, -(depth + 0.24 + (0.08 if level >= 2 else 0)) * 0.36, roof_z + 0.21))
    decor.add_paved_stone_sun(f"{name}_decor_paved_sun", collection, mats, (0, -1.31, 0.035))
    decor.add_courtyard_moss_slab(f"{name}_decor_moss_slab", collection, mats, (0.46, -1.08, 0.035))
    decor.add_stone_seed_planter(f"{name}_decor_seed_planter", collection, mats, (1.15, -0.20, 0.035))


def _setup_scene():
    scene.clear_scene()
    asset_scene = bpy.context.scene
    asset_scene.name = f"{ASSET_ID}_scene"
    profile = RenderProfile(samples=32)
    scene.configure_asset_scene(asset_scene, profile, light_prefix=ASSET_ID)
    mats = materials.create_palette(f"MAT_{ASSET_ID}")
    return asset_scene, profile, mats


def preview(level: int, state: str) -> str:
    asset_scene, _profile, mats = _setup_scene()
    name = state_name("stone_house", level, state)
    collection = geometry.create_collection(name)
    build_model(collection, mats, level=level, state=state)
    geometry.clean_meshes(collection)
    target = AssetOutput(ASSET_ID, CATEGORY, ROOT).runtime_dir / "preview" / f"{name}.png"
    export.render_png(target, scene=asset_scene)
    print("STONE_HOUSE_PREVIEW_COMPLETE", name, len(collection.all_objects), str(target))
    return str(target)


def generate_level(level: int) -> list[dict]:
    if level not in LEVELS:
        raise ValueError(f"Unsupported level: {level}")
    output = AssetOutput(ASSET_ID, CATEGORY, ROOT, use_public_glb=True)
    output.runtime_dir.mkdir(parents=True, exist_ok=True)
    output_rel_dir = PurePosixPath("frontend") / "public" / "assets" / "buildings" / CATEGORY / ASSET_ID
    asset_scene, _profile, mats = _setup_scene()
    collections = {}
    for state in STATES:
        name = state_name("stone_house", level, state)
        collection = geometry.create_collection(name)
        build_model(collection, mats, level=level, state=state)
        geometry.clean_meshes(collection)
        collections[name] = collection
    items = []
    for state in STATES:
        name = state_name("stone_house", level, state)
        item = export.export_state_assets(name, collections[name], output.runtime_dir,
                                          render=True, scene=asset_scene)
        item["level"] = level
        item["state"] = state
        item["glb"] = str(output_rel_dir / f"{name}.glb")
        item["png"] = str(output_rel_dir / f"{name}.png")
        items.append(item)
    blend_name = "stone_house_levels.blend" if level == 1 else f"stone_house_l{level:02d}_states.blend"
    bpy.context.preferences.filepaths.save_version = 0
    export.save_blend(output.runtime_dir / blend_name)
    report = output.runtime_dir / f"stone_house_l{level:02d}_report.json"
    report.write_text(json.dumps({"level": level, "states": list(STATES), "items": items,
                                  "source_blend": str(output_rel_dir / blend_name)},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("STONE_HOUSE_LEVEL_COMPLETE", level, len(items), str(report))
    return items


def finalize() -> dict:
    output = AssetOutput(ASSET_ID, CATEGORY, ROOT, use_public_glb=True)
    output_rel_dir = PurePosixPath("frontend") / "public" / "assets" / "buildings" / CATEGORY / ASSET_ID
    items = []
    source_blends = []
    for level in LEVELS:
        report = json.loads((output.runtime_dir / f"stone_house_l{level:02d}_report.json").read_text(encoding="utf-8"))
        if len(report["items"]) != len(STATES):
            raise ValueError(f"Incomplete level {level} report")
        items.extend(report["items"])
        source_blends.append(report["source_blend"])
    export.write_manifest(
        output.runtime_dir / "manifest.json",
        asset_id=ASSET_ID,
        display_name=DISPLAY_NAME,
        category=CATEGORY,
        levels=LEVELS,
        states=STATES,
        items=items,
        source_blend=str(output_rel_dir / f"{ASSET_ID}_levels.blend"),
        combined_glb=None,
        material_map={
            "stone": "основной корпус и кладка",
            "stone_block": "фундамент и читаемые блоки",
            "green_tile": "зеленая черепичная кровля",
            "glass": "теплые окна",
            "wood": "дверь и дворовые props",
        },
        extra={
            "component_library_version": COMPONENT_LIBRARY_VERSION,
            "generator": "tools/assets/blender/generate_stone_house_models.py",
            "source_blends": source_blends,
        },
    )
    report = {
        "asset_id": ASSET_ID,
        "display_name": DISPLAY_NAME,
        "category": CATEGORY,
        "levels": list(LEVELS),
        "states": list(STATES),
        "component_library_version": COMPONENT_LIBRARY_VERSION,
        "footprint_area_multiplier": FOOTPRINT_AREA_MULTIPLIER,
        "footprint_scale": FOOTPRINT_SCALE,
        "generator": "tools/assets/blender/generate_stone_house_models.py",
        "outputs": {"source_blends": source_blends, "manifest": str(output_rel_dir / "manifest.json")},
        "item_count": len(items),
        "triangles": {item["id"]: item["triangles"] for item in items},
        "sprite": {"size": [512, 384], "anchor": [256, 292]},
        "components": [
            "ground.add_ground_tile",
            "housing.add_stone_house_shell",
            "stone_house_pilot.add_full_stone_cladding",
            "stone_house_pilot.add_green_tiled_roof",
            "stone_house_pilot.add_level_six_wood_yard",
            "stone_house_decor.add_keystone_sun",
            "stone_house_decor.add_window_drain_lip",
            "stone_house_decor.add_ridge_copper_clasp",
            "stone_house_decor.add_roof_leaf_finial",
            "stone_house_decor.add_chimney_copper_crown",
            "stone_house_decor.add_dormer_side_fins",
            "stone_house_decor.add_paved_stone_sun",
            "stone_house_decor.add_courtyard_moss_slab",
            "stone_house_decor.add_stone_seed_planter",
            "stone_house_variants.add_progression",
            "stone_house_variants.add_construction",
            "stone_house_variants.add_damage",
            "stone_house_architecture.add_triangular_side_dormer",
            "stone_house_architecture.add_round_attic_window",
            "stone_house_architecture.add_right_stone_annex",
            "stone_house_architecture.add_second_storey_details",
            "stone_house_architecture.add_stone_entrance_porch",
            "stone_house_architecture.add_upper_annex_storey",
            "stone_house_architecture.add_annex_entry_door",
            "stone_house_architecture.add_planted_flower_beds",
            "stone_house_architecture.add_level_six_house",
        ],
    }
    report_path = output.runtime_dir / "generation-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("STONE_HOUSE_COMPLETE", len(items), str(output.runtime_dir))
    return report


if __name__ == "__main__":
    for level in LEVELS:
        generate_level(level)
    finalize()
