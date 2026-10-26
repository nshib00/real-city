"""Complete construction and damaged states for the vertical town hall study.

Run with Blender 5.2.2: blender -b --factory-startup --python this_file -- --levels 1,8,15
The active outputs in staging are deliberately left untouched.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/assets/blender"))

from real_city import export  # noqa: E402
from real_city.geometry import collection_bounds, collection_triangle_count  # noqa: E402

import build_town_hall_vertical_test as V  # noqa: E402

spec = importlib.util.spec_from_file_location("civic_states", Path(__file__).with_name("revise_building_states.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
S.H = V.H

OUTPUT = V.OUTPUT


def make_active(level, scene):
    name = f"town_hall_l{level:02d}_active"
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    V.H.COL = collection
    V.H.PREFIX = name
    V.configure_roof(level)
    V.legacy.building(min(level, 10))
    if level >= 4:
        V.remove_old_flag()
        V.central_tower(level)
        V.upgrade_side_towers(level)
        if level >= 12:
            V.new_corner_tower(1, level)
        if level >= 14:
            V.new_corner_tower(-1, level)
        V.recolor_all_roofs(level)
    V.H.clean_meshes(collection)
    bpy.context.view_layer.update()
    return collection


def remove_collection(collection):
    for obj in list(collection.all_objects):
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for child in list(collection.children):
        bpy.data.collections.remove(child)
    bpy.data.collections.remove(collection)


def build(level, scene, full):
    active = make_active(level, scene)
    result = []
    for state in ("construction", "damaged"):
        name = f"town_hall_l{level:02d}_{state}"
        collection = S.clone_active(active, name, scene)
        for key in ("building_dimensions", "tower_top", "tower_width"):
            if key in active:
                collection[key] = active[key]
        if level >= 4:
            eaves = active["building_dimensions"][2]
            collection["tower_top"] = eaves + 0.90 + 0.015 * (min(level, 10) - 4) + 0.09 * max(0, level - 10)
        edits = S.revise(collection, "town_hall", level, state)
        # The spires added by the vertical study need the same broken/unfinished
        # treatment as the inherited roof shingles.
        for obj in list(collection.all_objects):
            name_lower = obj.name.lower()
            if "vertical_" not in name_lower:
                continue
            if "_tip" in name_lower or "vertical_flag" in name_lower:
                S.remove(obj)
            elif state == "damaged" and "_roof_rib" in name_lower and obj.location.x > 0:
                S.remove(obj)
        V.H.clean_meshes(collection)
        for other in scene.collection.children:
            other.hide_render = other != collection
        scene.cycles.samples = 12 if not full else 24
        export.render_png(OUTPUT / f"{name}.png", scene=scene)
        lods = V.export_test_lods(name, collection, scene) if full else [
            {"name": "LOD0", "ratio": 1.0,
             "glb": str(export.export_glb(OUTPUT / f"{name}_LOD0.glb", collection=collection)),
             "triangles": collection_triangle_count(collection)}]
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.preferences.filepaths.save_version = 0
        export.save_blend(OUTPUT / f"{name}.blend")
        result.append({"id": name, "level": level, "state": state,
                       "png": str(OUTPUT / f"{name}.png"),
                       "source_blend": str(OUTPUT / f"{name}.blend"),
                       "bounds": collection_bounds(collection),
                       "triangles": collection_triangle_count(collection),
                       "lods": lods, **edits})
        print("BUILT", name, result[-1]["triangles"], flush=True)
        remove_collection(collection)
    remove_collection(active)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default=",".join(map(str, range(1, 16))))
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    levels = [int(value) for value in args.levels.split(",")]
    assert levels and all(1 <= level <= 15 for level in levels)
    scene = V.original_scene()
    V.H.palette()
    V.H.box = V.legacy.efficient_box
    for role, color in {"brick": (0.56, 0.19, 0.10), "mycelium": (0.73, 0.67, 0.43),
                        "premium": (0.35, 0.17, 0.065), "super_mycelium": (0.70, 0.35, 0.10)}.items():
        V.H.material(role, color)
    for stage, color in V.ROOF_COLORS.items():
        V.H.material(f"vertical_roof_{stage}", color)
    V.ORIGINAL_HIP_ROOF = V.legacy.hip_roof
    V.ORIGINAL_GABLE_ROOF = V.H.roof
    V.ORIGINAL_ROOF_MATERIAL = V.H.MATS["roof"]
    items = [item for level in levels for item in build(level, scene, args.full)]
    path = OUTPUT / ("states-generation-report.json" if args.full else "states-preview-report.json")
    if args.full and path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in previous["items"]}
        by_id.update({item["id"]: item for item in items})
        items = sorted(by_id.values(), key=lambda item: (item["level"], item["state"]))
    path.write_text(json.dumps({"generator": "tools/assets/blender/build_town_hall_vertical_states.py",
                                "source": "tools/assets/staging/town_hall_vertical_test/*_active.blend",
                                "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("REPORT", path, flush=True)


if __name__ == "__main__":
    main()
