"""Build active town hall visual studies from the existing Real City generator.

Run with Blender: blender -b --factory-startup --python this_file -- --levels 1,6,15
The output is staging-only; the runtime town_hall family is never written.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/assets/blender"))

from real_city import export, geometry  # noqa: E402
from real_city.geometry import collection_bounds, collection_triangle_count  # noqa: E402

source_spec = importlib.util.spec_from_file_location("legacy_town_halls", Path(__file__).with_name("regenerate_town_halls.py"))
legacy = importlib.util.module_from_spec(source_spec)
source_spec.loader.exec_module(legacy)
H = legacy.H

OUTPUT = ROOT / "tools/assets/staging/town_hall_vertical_test"
SOURCE_BLEND = ROOT / "frontend/src/assets/buildings/center/town_hall/town_hall_levels.blend"
ROOF_COLORS = {
    "light_green": (0.10, 0.55, 0.01),
    "yellow": (0.75, 0.38, 0.0005),
    "orange": (0.73, 0.24, 0.0003),
    "sky_blue": (0.015, 0.26, 0.75),
    "dark_purple": (0.02, 0.003, 0.07),
}
STAGE = {**{n: "light_green" for n in (4, 5)}, **{n: "yellow" for n in (6, 7)},
         **{n: "orange" for n in (8, 9, 10)}, **{n: "sky_blue" for n in (11, 12, 13)},
         **{n: "dark_purple" for n in (14, 15)}}


def original_scene():
    """Recreate the camera/light setup of the original town hall generator."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    for collection in list(scene.collection.children):
        bpy.data.collections.remove(collection, do_unlink=True)
    H.setup_camera(scene)
    return scene


def configure_roof(level):
    legacy.hip_roof = ORIGINAL_HIP_ROOF
    H.roof = ORIGINAL_GABLE_ROOF
    if level < 4:
        H.MATS["roof"] = ORIGINAL_ROOF_MATERIAL
        return
    stage = STAGE[level]
    H.MATS["roof"] = H.MATS[f"vertical_roof_{stage}"]

    def pointed_hip(cx, cy, width, depth, z, rise, leaves=False):
        return ORIGINAL_HIP_ROOF(cx, cy, width, depth, z, rise * 1.35, False)

    def pointed_gable(width, depth, eaves, rise, damaged=False, cx=0, cy=0, rows=4, cols=7):
        return ORIGINAL_GABLE_ROOF(width, depth, eaves, rise * 1.7, damaged, cx, cy, rows, cols)

    legacy.hip_roof = pointed_hip
    H.roof = pointed_gable


def recolor_all_roofs(level):
    if level < 4:
        return
    material = H.MATS["roof"]
    for obj in H.COL.all_objects:
        if obj.type != "MESH" or "roof_shingle" not in obj.name:
            continue
        obj.data.materials.clear()
        obj.data.materials.append(material)


def remove_old_flag():
    for obj in list(H.COL.all_objects):
        if obj.name.startswith(H.PREFIX + "_flag_pole") or obj.name.startswith(H.PREFIX + "_main_flag"):
            bpy.data.objects.remove(obj, do_unlink=True)


def roof_spire(name, x, y, z, width, rise):
    """An enclosed steep civic roof, with readable trim and a metal tip."""
    mat = H.MATS["roof"]
    r = width / 2
    vertices = [(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0), (0, 0, rise)]
    roof = geometry.mesh(f"{H.PREFIX}_{name}_roof_shingle", H.COL, vertices,
                         [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], mat)
    roof.location = (x, y, z)
    for cx, cy in ((-r, -r), (r, -r), (r, r), (-r, r)):
        geometry.beam(f"{H.PREFIX}_{name}_roof_rib", H.COL, (x + cx, y + cy, z),
                      (x, y, z + rise), 0.022, H.MATS["beam"])
    geometry.box(f"{H.PREFIX}_{name}_cornice", H.COL, (x, y, z + 0.025),
                 (width * 1.08, width * 1.08, 0.055), H.MATS["beam"], bevel=0.012)
    geometry.beam(f"{H.PREFIX}_{name}_tip", H.COL, (x, y, z + rise - 0.01),
                  (x, y, z + rise + 0.12), 0.020, H.MATS["accent"])


def central_tower(level):
    eaves = (1.23, 1.43, 1.57, 1.96, 2.13, 2.28, 2.43, 2.58, 2.72, 2.88)[min(level, 10) - 1]
    top = eaves + 0.90 + 0.015 * (min(level, 10) - 4) + 0.09 * max(0, level - 10)
    bottom = eaves + 0.38
    role = "wood" if level <= 5 else "stone" if level <= 8 else "brick"
    legacy.walls(0, 0, 0.56, 0.56, bottom, top - bottom, role, name="vertical_central_tower", courses=4)
    # Explicit floor bands make the additional height read as a built storey.
    floors = 1 if level < 10 else 2 if level < 15 else 3
    for index in range(floors):
        z = bottom + (index + 1) * (top - bottom) / (floors + 1)
        H.box("vertical_central_floor_band", (0, -0.294, z), (0.64, 0.055, 0.075),
              "wood" if level <= 5 else "stone", 0.01)
        H.window(0, -0.33, min(top - 0.15, z + 0.13), 0.20, 0.18)
    roof_spire("central_spire", 0, 0, top, 0.72, 0.35)
    H.beam("vertical_flag_pole", (0, 0, top + 0.45), (0, 0, top + 0.65), 0.025, "wood")
    H.box("vertical_main_flag", (0.14, 0, top + 0.56), (0.27, 0.025, 0.14), "accent", 0.007)
    return top + 0.35


def upgrade_side_towers(level):
    # Lift the legacy left/right towers above the wings so both read in isometric view.
    for side, first in ((-1, 7), (1, 9)):
        if level < first:
            continue
        x, y = side * 1.31, -0.04
        extra_storey = (side < 0 and level >= 11) or (side > 0 and level >= 13)
        top = 2.55 + 0.05 * (level - first) + (0.18 if extra_storey else 0)
        role = "stone" if level < 9 else "brick"
        legacy.walls(x, y, 0.40, 0.46, 0.21, top - 0.21, role, name="vertical_side_tower", courses=7)
        H.window(x, y - 0.28, top - 0.34, 0.16, 0.22)
        if level >= first + 1:
            H.box("vertical_side_floor_band", (x, y - 0.26, top - 0.68),
                  (0.48, 0.06, 0.07), "stone" if level < 9 else "brick", 0.01)
        if extra_storey:
            H.window(x, y - 0.28, top - 0.78, 0.14, 0.17)
            H.box("vertical_added_storey_band", (x, y - 0.26, top - 0.52),
                  (0.48, 0.06, 0.07), "brick", 0.01)
        roof_spire("left_spire" if side < 0 else "right_spire", x, y, top, 0.56, 0.32)


def new_corner_tower(side, level):
    x, y = side * 1.42, 1.02 if side > 0 else -1.02
    top = 2.20 + 0.055 * (level - (12 if side > 0 else 14))
    H.box("vertical_corner_connector", (side * 1.23, 0.73 if side > 0 else -0.73, 0.76),
          (0.54, 0.65, 1.10), "brick", 0.025)
    legacy.walls(x, y, 0.42, 0.42, 0.21, top - 0.21, "brick", name="vertical_corner_tower", courses=6)
    H.window(x, y - 0.25, top - 0.31, 0.16, 0.22)
    roof_spire("front_left_spire" if side < 0 else "rear_right_spire", x, y, top, 0.55, 0.30)


def export_test_lods(name, collection, scene):
    """Decimate one joined building mesh per LOD; keep the ground untouched."""
    records = []
    path = OUTPUT / f"{name}_LOD0.glb"
    export.export_glb(path, collection=collection)
    records.append({"name": "LOD0", "ratio": 1.0, "glb": str(path),
                    "triangles": collection_triangle_count(collection)})
    for lod_name, ratio in (("LOD1", 0.55), ("LOD2", 0.28)):
        temp = bpy.data.collections.new(f"{name}_{lod_name}_temp")
        scene.collection.children.link(temp)
        building_parts = []
        for obj in collection.all_objects:
            if obj.type != "MESH":
                continue
            clone = obj.copy()
            clone.data = obj.data.copy()
            temp.objects.link(clone)
            if not any(part in obj.name for part in ("earth_tile", "grass_tile", "path_stone")):
                building_parts.append(clone)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in building_parts:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = building_parts[0]
        bpy.ops.object.join()
        joined = building_parts[0]
        modifier = joined.modifiers.new("test_lod_decimate", "DECIMATE")
        modifier.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.ops.object.select_all(action="DESELECT")
        glb = OUTPUT / f"{name}_{lod_name}.glb"
        export.export_glb(glb, collection=temp)
        records.append({"name": lod_name, "ratio": ratio, "glb": str(glb),
                        "triangles": collection_triangle_count(temp)})
        for obj in list(temp.objects):
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(temp)
    return records


def build(level, scene, *, full):
    name = f"town_hall_l{level:02d}_active"
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    H.COL = collection
    H.PREFIX = name
    configure_roof(level)
    legacy.building(min(level, 10))
    if level >= 4:
        remove_old_flag()
        central_tower(level)
        upgrade_side_towers(level)
        if level >= 12:
            new_corner_tower(1, level)
        if level >= 14:
            new_corner_tower(-1, level)
        recolor_all_roofs(level)
    H.clean_meshes(collection)
    bpy.context.view_layer.update()

    for other in scene.collection.children:
        other.hide_render = other != collection
    scene.render.filepath = str(OUTPUT / f"{name}.png")
    scene.cycles.samples = 12 if not full else 24
    export.render_png(OUTPUT / f"{name}.png", scene=scene)
    if full:
        lods = export_test_lods(name, collection, scene)
    else:
        lods = [{"name": "LOD0", "ratio": 1.0, "glb": str(export.export_glb(OUTPUT / f"{name}_LOD0.glb", collection=collection)),
                 "triangles": collection_triangle_count(collection)}]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.preferences.filepaths.save_version = 0
    export.save_blend(OUTPUT / f"{name}.blend")
    bounds = collection_bounds(collection)
    result = {"id": name, "level": level, "state": "active", "png": str(OUTPUT / f"{name}.png"),
              "glb": str(OUTPUT / f"{name}_LOD0.glb"), "source_blend": str(OUTPUT / f"{name}.blend"),
              "triangles": collection_triangle_count(collection), "bounds": bounds, "lods": lods,
              "roof_stage": STAGE.get(level, "legacy")}
    print("BUILT", level, result["triangles"], result["bounds"], flush=True)
    for obj in list(collection.all_objects):
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    scene.collection.children.unlink(collection)
    bpy.data.collections.remove(collection)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default=",".join(map(str, range(1, 16))))
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    levels = [int(value) for value in args.levels.split(",")]
    assert levels and all(1 <= n <= 15 for n in levels)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scene = original_scene()
    H.palette()
    H.box = legacy.efficient_box
    for role, color in {"brick": (0.56, 0.19, 0.10), "mycelium": (0.73, 0.67, 0.43),
                        "premium": (0.35, 0.17, 0.065), "super_mycelium": (0.70, 0.35, 0.10)}.items():
        H.material(role, color)
    for stage, color in ROOF_COLORS.items():
        H.material(f"vertical_roof_{stage}", color)
    global ORIGINAL_HIP_ROOF, ORIGINAL_GABLE_ROOF, ORIGINAL_ROOF_MATERIAL
    ORIGINAL_HIP_ROOF = legacy.hip_roof
    ORIGINAL_GABLE_ROOF = H.roof
    ORIGINAL_ROOF_MATERIAL = H.MATS["roof"]
    items = [build(level, scene, full=args.full) for level in levels]
    report_path = OUTPUT / ("generation-report.json" if args.full else "preview-report.json")
    if args.full and report_path.exists() and len(levels) < 15:
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        by_level = {item["level"]: item for item in previous["items"]}
        by_level.update({item["level"]: item for item in items})
        items = [by_level[level] for level in sorted(by_level)]
    report = {"generator": "tools/assets/blender/build_town_hall_vertical_test.py",
              "source": str(SOURCE_BLEND.relative_to(ROOT)), "staging_only": True, "items": items}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("REPORT", report_path, flush=True)


if __name__ == "__main__":
    main()
