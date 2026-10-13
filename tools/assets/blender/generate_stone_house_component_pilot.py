"""Pilot generation: stone house level 1 active from reusable components."""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy

from tools.assets.blender.real_city import AssetOutput, RenderProfile
from tools.assets.blender.real_city import export, geometry, ground, materials, scene
from tools.assets.blender.real_city.components import COMPONENT_LIBRARY_VERSION
from tools.assets.blender.real_city.components import housing, landscaping, props
from tools.assets.blender.real_city.state import state_name

ASSET_ID = "stone_house_component_pilot"
DISPLAY_NAME = "Каменный дом - component pilot"
CATEGORY = "housing"
LEVEL = 1
STATE = "active"


def build_model(collection, mats: dict) -> None:
    ground.add_ground_tile(collection, mats, prefix=ASSET_ID, include_path=True)
    housing.add_stone_house_shell("pilot_stone_house_l01", collection, mats, level=1, damaged=False)
    housing.add_housing_yard("pilot_stone_house_l01", collection, mats, level=1, damaged=False)
    landscaping.add_flower_bed("pilot_stone_house_bed_round", collection, mats, (-1.10, -0.52, 0.08), style="stone_ring")
    landscaping.add_flower_bed("pilot_stone_house_bed_strip", collection, mats, (0.88, 0.82, 0.08), style="strip")
    props.add_decor_cluster("pilot_stone_house_supplies", collection, mats, (1.05, -0.74, 0.02))

    for obj in collection.all_objects:
        obj["real_city_asset"] = ASSET_ID
        obj["component_library_version"] = COMPONENT_LIBRARY_VERSION
        obj["pilot_source"] = "tools/assets/blender/generate_stone_house_component_pilot.py"


def generate() -> dict:
    output = AssetOutput(ASSET_ID, CATEGORY, ROOT, use_public_glb=True)
    output.runtime_dir.mkdir(parents=True, exist_ok=True)
    output_rel_dir = PurePosixPath("frontend") / "public" / "assets" / "buildings" / CATEGORY / ASSET_ID

    scene.clear_scene()
    asset_scene = bpy.context.scene
    asset_scene.name = f"{ASSET_ID}_scene"
    profile = RenderProfile(samples=32)
    scene.configure_asset_scene(asset_scene, profile, light_prefix=ASSET_ID)
    mats = materials.create_palette(f"MAT_{ASSET_ID}")

    name = state_name("stone_house", LEVEL, STATE)
    collection = geometry.create_collection(name)
    build_model(collection, mats)
    geometry.clean_meshes(collection)

    item = export.export_state_assets(name, collection, output.runtime_dir, render=True, scene=asset_scene)
    manifest_item = dict(item)
    manifest_item["glb"] = str(output_rel_dir / f"{name}.glb")
    manifest_item["png"] = str(output_rel_dir / f"{name}.png")
    export.save_blend(output.runtime_dir / f"{ASSET_ID}_levels.blend")
    export.write_manifest(
        output.runtime_dir / "manifest.json",
        asset_id=ASSET_ID,
        display_name=DISPLAY_NAME,
        category=CATEGORY,
        levels=[LEVEL],
        states=[STATE],
        items=[manifest_item],
        source_blend=str(output_rel_dir / f"{ASSET_ID}_levels.blend"),
        combined_glb=None,
        material_map={
            "stone": "основной корпус и кладка",
            "stone_block": "фундамент и читаемые блоки",
            "brick": "теплая черепичная крыша",
            "glass": "теплые окна",
            "wood": "дверь и дворовые props",
        },
        extra={
            "pilot": True,
            "component_library_version": COMPONENT_LIBRARY_VERSION,
            "generator": "tools/assets/blender/generate_stone_house_component_pilot.py",
        },
    )

    report = {
        "asset_id": ASSET_ID,
        "display_name": DISPLAY_NAME,
        "category": CATEGORY,
        "level": LEVEL,
        "state": STATE,
        "component_library_version": COMPONENT_LIBRARY_VERSION,
        "generator": "tools/assets/blender/generate_stone_house_component_pilot.py",
        "outputs": {
            "blend": str(output_rel_dir / f"{ASSET_ID}_levels.blend"),
            "glb": str(output_rel_dir / f"{name}.glb"),
            "png": str(output_rel_dir / f"{name}.png"),
            "manifest": str(output_rel_dir / "manifest.json"),
        },
        "triangles": item["triangles"],
        "bounds": item["bounds"],
        "sprite": {"size": list(profile.sprite_size), "anchor": list(profile.anchor)},
        "components": [
            "ground.add_ground_tile",
            "housing.add_stone_house_shell",
            "housing.add_housing_yard",
            "landscaping.add_flower_bed",
            "props.add_decor_cluster",
        ],
    }
    report_path = output.runtime_dir / "component-pilot-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("STONE_HOUSE_COMPONENT_PILOT_COMPLETE", json.dumps(report["outputs"], ensure_ascii=False))
    return report


if __name__ == "__main__":
    generate()
