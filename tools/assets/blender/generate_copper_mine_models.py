"""Generate all documented copper-mine levels from the shared mine component kit."""

from __future__ import annotations

import importlib.util
import json
import logging
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "copper_mine"
SPEC_PATH = ROOT / "docs" / "assets" / "specs" / "industry" / "copper_mine.json"
LEVELS = range(1, 11)
STATES = ("active", "construction", "damaged")

module_spec = importlib.util.spec_from_file_location("real_city_base_mine", Path(__file__).with_name("generate_mine_models.py"))
M = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(M)
H = M.H


def copper_piles(level: int, state: str) -> None:
    damaged = state == "damaged"
    for index, (x, y) in enumerate(((-1.04, -0.18), (1.08, -0.20), (0.88, -0.98))):
        role = "ore_verdigris" if index == 1 and not damaged else "ore_copper" if not damaged else "rock_warm"
        M.frustum(f"copper_ore_pile_{index+1}", x, y, 0.13, 0.25 + level * 0.021, 0.16 + level * 0.014, 0.18 + level * 0.022, 0.12, role, rings=3, segments=16, wobble=0.065)
    if level >= 2:
        for index in range(min(1 + level // 3, 3)):
            x = -1.25 + index * 0.19
            H.box("copper_ore_basket", (x, 0.23, 0.22), (0.28, 0.24, 0.20), "wood", 0.024)
            M.frustum("basket_ore_load", x, 0.23, 0.31, 0.12, 0.10, 0.10, 0.28, "ore_copper", rings=3, segments=10)
    if level >= 3:
        M.cylinder("fuel_barrel_body", (1.25, 0.38, 0.34), 0.16, 0.42, "fuel_red" if not damaged else "char", segments=16)
        for z in (0.20, 0.48):
            M.cylinder("fuel_barrel_hoop", (1.25, 0.38, z), 0.168, 0.035, "rail_iron", segments=16)


def add_copper_identity(collection, level: int, state: str) -> None:
    H.COL = collection
    H.PREFIX = f"copper_mine_l{level:02d}_{state}"
    # Embedded mineral ridges make the exposed deposit visible even at map scale.
    for index, (x, y, z, size) in enumerate(((-1.12, -0.10, 0.42, 0.19), (1.04, -0.12, 0.55, 0.23), (-0.76, 0.09, 1.02, 0.17), (0.68, 0.15, 1.10, 0.16))):
        role = "ore_verdigris" if index % 2 else "ore_copper"
        if state == "damaged" and index == 3:
            continue
        M.jagged_rock(f"exposed_copper_vein_{index+1}", x, y, z, size, size * 0.64, 0.29 + 0.025 * min(level, 8), role, segments=7, top_scale=0.18, twist=0.23)
        H.beam(f"copper_vein_branch_{index+1}", (x, y - 0.055, z + 0.05), (x + (0.13 if x < 0 else -0.13), y - 0.055, z + 0.23), 0.034, "ore_copper")
    if state == "active":
        # Tier accents sit on the existing portal/hoist, and do not imply a new recipe.
        if level >= 4:
            for side in (-1, 1):
                H.box("copper_depth_gauge", (side * 0.78, -0.96, 0.78), (0.12, 0.055, 0.28), "ore_copper", 0.01)
        if level >= 7:
            H.box("sorting_sieve_frame", (0.90, 0.74, 0.34), (0.47, 0.29, 0.13), "rail_iron", 0.017)
            for index in range(4):
                H.box("sorted_copper_piece", (0.73 + index * 0.10, 0.72, 0.44), (0.08, 0.07, 0.07), "ore_copper" if index % 2 else "ore_verdigris", 0.012)
        if level >= 9:
            H.box("protected_copper_output", (-1.08, 0.46, 0.35), (0.31, 0.30, 0.26), "protective_plate", 0.025)
            H.box("copper_output_mark", (-1.08, 0.29, 0.39), (0.18, 0.03, 0.08), "ore_copper", 0.008)


def setup() -> bpy.types.Scene:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Blender names are global: stale previews otherwise force .001 suffixes
    # into runtime filenames and leave the unreviewed first preview in place.
    for collection in list(bpy.data.collections):
        if collection.name.startswith("copper_mine_l"):
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
    fallback_scene = next((item for item in bpy.data.scenes if not item.name.startswith("Real_City_Copper_Mine_Models")), None)
    if fallback_scene is not None:
        bpy.context.window.scene = fallback_scene
    for old_scene in list(bpy.data.scenes):
        if old_scene.name.startswith("Real_City_Copper_Mine_Models"):
            bpy.data.scenes.remove(old_scene)
    scene = bpy.data.scenes.new("Real_City_Copper_Mine_Models")
    bpy.context.window.scene = scene
    M.palette()
    M.add_material("ore_copper", (0.72, 0.35, 0.13), 0.55, 0.28)
    M.add_material("ore_verdigris", (0.20, 0.58, 0.48), 0.69, 0.09)
    H.MATS["coal"] = H.MATS["ore_copper"]
    M.coal_and_stone_piles = copper_piles
    H.setup_camera(scene)
    # Match the existing mine's 512-square runtime ground width and anchor.
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 5.43058
    scene.camera.data.shift_y = 0.125
    scene["asset_id"] = "copper_mine"
    scene["catalog_discrepancy"] = "docs levels 1-10; game catalog currently level 1"
    return scene


def glb_triangles(path: Path) -> int:
    raw = path.read_bytes()
    assert raw[:4] == b"glTF"
    size = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    return sum(document["accessors"][part["indices"]]["count"] // 3 for mesh in document.get("meshes", ()) for part in mesh["primitives"] if "indices" in part)


def export_lod(collection, name: str, lod: str, omit: tuple[str, ...]) -> dict:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        obj.select_set(obj.type == "MESH" and not any(token in obj.name for token in omit))
    path = OUT_DIR / f"{name}_{lod}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, use_active_scene=True)
    return {"name": lod, "glb": path.name, "triangles": glb_triangles(path)}


def generate(levels=None, states=None, preview=False):
    logging.getLogger("glTF").setLevel(logging.ERROR)
    scene = setup()
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    selected_levels = list(levels or LEVELS)
    selected_states = tuple(states or STATES)
    report = {}
    collections = []
    for level in selected_levels:
        active = None
        for state in selected_states:
            if state != "active" and active is None:
                raise ValueError("Preview/full must build active before other states to copy ground")
            collection = M.mine(level, state, active)
            collection.name = f"copper_mine_l{level:02d}_{state}"
            collection["ground_source"] = f"copper_mine_l{level:02d}_active"
            add_copper_identity(collection, level, state)
            if state == "active":
                active = collection
            M.hide_all(collections)
            collection.hide_render = False
            collection.hide_viewport = False
            bpy.context.view_layer.update()
            name = collection.name
            if preview:
                scene.render.filepath = str(OUT_DIR / f"{name}.png")
                bpy.ops.render.render(write_still=True)
                report[name] = {"level": level, "state": state, "png": f"{name}.png"}
            else:
                lod0 = export_lod(collection, name, "LOD0", ())
                lod1 = export_lod(collection, name, "LOD1", ("grass_tuft", "copper_vein_branch", "round_arch_rivet", "sorted_copper_piece", "front_anchor_bolt", "explosive_crate_strap"))
                lod2 = export_lod(collection, name, "LOD2", ("grass_tuft", "copper_vein_branch", "round_arch_rivet", "sorted_copper_piece", "pick_handle", "pick_head", "lamp_hook", "copper_depth_gauge", "front_rail_sleeper", "cart_track_sleeper", "small_lightcrystal_marker", "angular_face_chip", "front_masonry_detail_block", "yard_rock", "laid_stone_block_course", "explosive_crate_strap", "armor_bolt_column", "front_anchor_bolt", "upper_sharp_crown", "front_block_face", "concrete_face_capstone"))
                scene.render.filepath = str(OUT_DIR / f"{name}.png")
                bpy.ops.render.render(write_still=True)
                report[name] = {"level": level, "state": state, "triangles": lod0["triangles"], "png": f"{name}.png", "glb": lod0["glb"], "lods": [lod0, lod1, lod2]}
                print("COPPER_MINE_DONE", name, flush=True)
            collections.append(collection)
    if not preview:
        bpy.data.libraries.write(str(OUT_DIR / "copper_mine.blend"), {scene}, fake_user=True)
        manifest = {"id": "copper_mine", "display_name": "Медный рудник", "building_type": "industry", "size": [512, 512], "anchor": [256, 320], "levels": selected_levels, "states": list(selected_states), "material_map": spec["material_map"], "lod_policy": spec["lod_policy"], "assets": report}
        (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        generation = {"asset_id": "copper_mine", "generated": len(report), "levels": selected_levels, "states": list(selected_states), "triangle_range": [min(item["triangles"] for item in report.values()), max(item["triangles"] for item in report.values())], "material_map": spec["material_map"], "assets": list(report), "roundtrip_validated": 0}
        (OUT_DIR / "generation-report.json").write_text(json.dumps(generation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("COPPER_MINE_GENERATED", len(report), "preview" if preview else "full", flush=True)


if __name__ == "__main__":
    generate()
