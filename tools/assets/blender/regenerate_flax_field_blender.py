"""Build Blender master/runtime assets for flax field levels 1-10.

This is the Blender/MCP production route. It deliberately does not call the
legacy pure-Python fallback generator.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

ROOT = Path("/home/nshib/projects/real-city")
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/flax_field"
BLEND_PATH = OUT_DIR / "flax_field_l01_l10.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-flax-field-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.24
LEVELS = list(range(1, 11))

MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "earth": (0.46, 0.27, 0.15, 1),
    "earth_dark": (0.30, 0.18, 0.10, 1),
    "seed_soil": (0.49, 0.29, 0.14, 1),
    "seed_soil_light": (0.70, 0.47, 0.25, 1),
    "wood": (0.70, 0.45, 0.23, 1),
    "wood_dark": (0.42, 0.25, 0.12, 1),
    "wood_cut": (0.86, 0.63, 0.34, 1),
    "plank": (0.78, 0.55, 0.30, 1),
    "plank_light": (0.94, 0.70, 0.38, 1),
    "rope": (0.73, 0.58, 0.32, 1),
    "flax": (0.84, 0.78, 0.54, 1),
    "cloth_teal": (0.34, 0.55, 0.72, 1),
    "sprout": (0.55, 0.78, 0.58, 1),
    "sprout_light": (0.73, 0.90, 0.73, 1),
    "leaf_deep": (0.32, 0.57, 0.46, 1),
    "leaf_vein": (0.72, 0.92, 0.82, 1),
    "seed_pod": (0.56, 0.73, 0.96, 1),
    "seed_pod_light": (0.76, 0.88, 1.00, 1),
    "seed_gold": (0.96, 0.84, 0.55, 1),
    "seed_super": (0.96, 0.90, 0.64, 1),
    "bag": (0.78, 0.66, 0.45, 1),
    "bag_dark": (0.48, 0.36, 0.20, 1),
    "tray": (0.72, 0.45, 0.20, 1),
    "tray_light": (0.92, 0.66, 0.35, 1),
    "stone": (0.54, 0.56, 0.50, 1),
    "stone_block": (0.64, 0.66, 0.60, 1),
    "brick": (0.63, 0.34, 0.22, 1),
    "fabric": (0.76, 0.82, 0.92, 1),
    "premium_plank": (0.49, 0.30, 0.15, 1),
    "metal": (0.54, 0.57, 0.58, 1),
    "gold": (0.95, 0.72, 0.26, 1),
    "super_seed": (0.88, 0.95, 0.52, 1),
    "quality_blue": (0.45, 0.82, 0.98, 1),
}


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        relative = raw[len(root) :].lstrip("\\")
        return BLENDER_ROOT + "\\" + relative
    if str(path).startswith("/tmp/") or raw.lower().startswith("\\tmp\\"):
        return r"\\wsl.localhost\Debian" + raw
    return raw


def ensure_dir() -> None:
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)


def mat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new("MAT_flax_field_" + name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.78
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = color[3]
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_flax_field_"):
            bpy.data.materials.remove(material)
    return {name: mat(name, color) for name, color in MATERIALS.items()}


def add_cube(coll, name, loc, scale, material, rot=(0, 0, 0), bevel=0.015, ground=False):
    sx, sy, sz = scale[0] * 0.5, scale[1] * 0.5, scale[2] * 0.5
    verts = [
        (-sx, -sy, -sz),
        (sx, -sy, -sz),
        (sx, sy, -sz),
        (-sx, sy, -sz),
        (-sx, -sy, sz),
        (sx, -sy, sz),
        (sx, sy, sz),
        (-sx, sy, sz),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("soft_midpoly_edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    if ground:
        obj["ground"] = True
    return obj


def add_cylinder(coll, name, loc, radius, depth, material, vertices=10, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices, radius1=radius, radius2=radius, depth=depth)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("soft_cap_edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def beam_between(coll, name, start, end, radius, material, vertices=8):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) * 0.5
    direction = end_v - start_v
    obj = add_cylinder(coll, name, mid, radius, direction.length, material, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def add_leaf(coll, name, center, length, width, material, vein_material, yaw=0, pitch=0.58, roll=0, vein=True):
    verts = [
        (0, 0, length * 0.52),
        (-width * 0.52, 0, length * 0.08),
        (-width * 0.30, 0, -length * 0.30),
        (0, 0, -length * 0.48),
        (width * 0.30, 0, -length * 0.30),
        (width * 0.52, 0, length * 0.08),
        (0, width * 0.07, length * 0.08),
    ]
    faces = [(0, 1, 6), (1, 2, 6), (2, 3, 6), (3, 4, 6), (4, 5, 6), (5, 0, 6)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.data.materials.append(material)
    transform = Matrix.Translation(Vector(center)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(pitch, 4, "X") @ Matrix.Rotation(roll, 4, "Y")
    obj.data.transform(transform)
    obj.modifiers.new("leaf_weighted_normals", "WEIGHTED_NORMAL")
    if vein:
        tip = transform @ Vector((0, 0.01, length * 0.43))
        root = transform @ Vector((0, 0.01, -length * 0.38))
        beam_between(coll, name + "_vein", root, tip, max(0.009, width * 0.04), vein_material, 6)
    return obj


def add_ground(coll, mats):
    add_cube(coll, "flax_field_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.25, 0.86), (1.18, 1.12), (1.24, -0.92), (-1.16, -1.12)]):
        for j in range(3):
            beam_between(
                coll,
                "terrain_grass_tuft",
                (x + (j - 1) * 0.045, y, 0.008),
                (x + (j - 1) * 0.085, y + 0.035, 0.11 + 0.03 * (i % 2)),
                0.025,
                mats["grass_light"],
                6,
            )
    add_cube(coll, "warm_flax_plot", (0, 0, 0.075), (2.60, 1.82, 0.16), mats["seed_soil"], bevel=0.06, ground=True)
    add_cube(coll, "raised_flax_bed", (-0.06, -0.02, 0.18), (2.25, 1.42, 0.06), mats["seed_soil_light"], bevel=0.035, ground=True)
    for y in (-0.51, -0.17, 0.17, 0.51):
        add_cube(coll, "dark_flax_furrow", (-0.04, y, 0.25), (2.08, 0.050, 0.035), mats["earth_dark"], bevel=0.010, ground=True)
        add_cube(coll, "raised_flax_ridge", (-0.04, y + 0.08, 0.275), (1.92, 0.045, 0.030), mats["seed_soil_light"], bevel=0.012, ground=True)


def add_flax_board(coll, name, loc, scale, material, mats, *, orientation="front", detail=1, damaged=False):
    add_cube(coll, name, loc, scale, material, (0, 0, 0.01 if orientation == "front" else -0.01), 0.026, True)
    x, y, z = loc
    sx, sy, sz = scale
    if detail >= 1 and not damaged:
        groove_count = 4 if orientation in {"front", "back"} else 3
        for index in range(groove_count):
            if orientation in {"front", "back"}:
                gx = x - sx * 0.36 + index * sx * 0.24
                add_cube(coll, name + "_flax_groove", (gx, y - sy * 0.54, z + sz * 0.18), (0.018, sy * 0.22, sz * 0.56), mats["wood_dark"], bevel=0.004, ground=True)
            else:
                gy = y - sy * 0.34 + index * sy * 0.34
                add_cube(coll, name + "_flax_groove", (x - sx * 0.54, gy, z + sz * 0.18), (sx * 0.20, 0.018, sz * 0.56), mats["wood_dark"], bevel=0.004, ground=True)
    if detail >= 2:
        if orientation in {"front", "back"}:
            add_cube(coll, name + "_linen_blue_inlay", (x, y - sy * 0.58, z + sz * 0.36), (sx * 0.72, sy * 0.16, 0.032), mats["cloth_teal"], bevel=0.006, ground=True)
        else:
            add_cube(coll, name + "_linen_blue_inlay", (x - sx * 0.58, y, z + sz * 0.36), (sx * 0.16, sy * 0.72, 0.032), mats["cloth_teal"], bevel=0.006, ground=True)
        if orientation in {"front", "back"}:
            for marker_x in (x - sx * 0.31, x + sx * 0.31):
                add_cube(coll, name + "_linen_tie_block", (marker_x, y - sy * 0.61, z + sz * 0.68), (0.11, sy * 0.18, 0.050), mats["rope"], (0, 0, 0.05), 0.005, True)
        else:
            for marker_y in (y - sy * 0.30, y + sy * 0.30):
                add_cube(coll, name + "_linen_tie_block", (x - sx * 0.61, marker_y, z + sz * 0.68), (sx * 0.18, 0.11, 0.050), mats["rope"], (0, 0, 0.05), 0.005, True)
    if detail >= 3 and not damaged:
        if orientation in {"front", "back"}:
            face_y = y - sy * 0.64
            for index, marker_x in enumerate((x - sx * 0.36, x, x + sx * 0.36)):
                add_cube(coll, name + "_carved_flax_panel", (marker_x, face_y, z + sz * 0.58), (0.20, sy * 0.20, 0.060), mats["wood_dark"], (0, 0, 0.12 * (index - 1)), 0.006, True)
                add_cube(coll, name + "_blue_fiber_knot", (marker_x, face_y - 0.004, z + sz * 0.80), (0.105, sy * 0.18, 0.052), mats["quality_blue"], (0, 0, -0.10 * (index - 1)), 0.006, True)
            for marker_x, yaw in ((x - sx * 0.19, 0.48), (x + sx * 0.19, -0.48)):
                add_cube(coll, name + "_diagonal_fiber_stitch", (marker_x, face_y - 0.005, z + sz * 0.28), (0.32, sy * 0.16, 0.045), mats["rope"], (0, 0, yaw), 0.005, True)
        else:
            face_x = x - sx * 0.64
            for index, marker_y in enumerate((y - sy * 0.36, y, y + sy * 0.36)):
                add_cube(coll, name + "_carved_flax_panel", (face_x, marker_y, z + sz * 0.58), (sx * 0.20, 0.20, 0.060), mats["wood_dark"], (0, 0, -0.12 * (index - 1)), 0.006, True)
                add_cube(coll, name + "_blue_fiber_knot", (face_x - 0.004, marker_y, z + sz * 0.80), (sx * 0.18, 0.105, 0.052), mats["quality_blue"], (0, 0, 0.10 * (index - 1)), 0.006, True)
            for marker_y, yaw in ((y - sy * 0.19, 1.05), (y + sy * 0.19, -1.05)):
                add_cube(coll, name + "_diagonal_fiber_stitch", (face_x - 0.005, marker_y, z + sz * 0.28), (sx * 0.16, 0.32, 0.045), mats["rope"], (0, 0, yaw), 0.005, True)


def add_flax_corner_post(coll, name, x, y, post_h, mats, *, level, damaged=False):
    width = 0.15 + level * 0.015
    add_cube(coll, name + "_post", (x, y, post_h / 2), (width, width, post_h), mats["wood_dark"], (0, 0, 0.10), 0.030, True)
    if damaged:
        return
    add_cube(coll, name + "_cap", (x, y, post_h + 0.035), (width * 1.45, width * 1.45, 0.07), mats["plank_light"], (0, 0, 0.18), 0.022, True)
    if level >= 2:
        add_cube(coll, name + "_linen_wrap", (x, y, post_h * 0.58), (width * 1.14, width * 1.14, 0.045), mats["rope"], (0, 0, -0.18), 0.008, True)
    if level >= 3:
        add_cube(coll, name + "_blue_tag", (x + 0.02, y - width * 0.66, post_h * 0.80), (0.030, 0.16, 0.09), mats["cloth_teal"], (0, 0, 0.08), 0.006, True)


def add_flax_frame_decor(coll, level, mats, *, incomplete=False, damaged=False, ruined=False):
    if damaged or ruined:
        return
    if level >= 1:
        for x in (-0.64, 0.0, 0.64):
            beam_between(coll, "front_linen_tie", (x - 0.18, -1.135, 0.38), (x + 0.18, -1.135, 0.38), 0.014, mats["rope"], 6)
    if level >= 2 and not incomplete:
        for y in (-0.52, 0.52):
            beam_between(coll, "side_fiber_guide", (-1.18, y, 0.44), (1.18, y, 0.44), 0.018, mats["rope"], 8)
        for x in (-0.92, 0.92):
            add_cube(coll, "small_linen_comb", (x, -1.16, 0.46), (0.22, 0.045, 0.12), mats["plank_light"], (0, 0, 0.02), 0.010, True)
            for tooth in range(3):
                add_cube(coll, "small_linen_comb_tooth", (x - 0.07 + tooth * 0.07, -1.20, 0.36), (0.018, 0.035, 0.16), mats["wood_cut"], bevel=0.004, ground=True)
    if level >= 3:
        for y in (-1.12, 1.12):
            for x in (-0.94, -0.34, 0.34, 0.94):
                add_cube(coll, "flax_blue_edge_marker", (x, y, 0.50), (0.16, 0.035, 0.055), mats["cloth_teal"], (0, 0, 0.14), 0.006, True)
        for x in (-0.72, 0.0, 0.72):
            add_cube(coll, "front_carved_linen_rosette", (x, -1.205, 0.62), (0.13, 0.035, 0.13), mats["quality_blue"], (0, 0, 0.78), 0.010, True)
            add_cube(coll, "back_carved_linen_rosette", (x, 1.205, 0.62), (0.13, 0.035, 0.13), mats["quality_blue"], (0, 0, -0.78), 0.010, True)
        for y in (-0.66, 0.0, 0.66):
            add_cube(coll, "left_side_linen_rosette", (-1.42, y, 0.62), (0.035, 0.13, 0.13), mats["quality_blue"], (0, 0, 0.78), 0.010, True)
            add_cube(coll, "right_side_linen_rosette", (1.42, y, 0.62), (0.035, 0.13, 0.13), mats["quality_blue"], (0, 0, -0.78), 0.010, True)
        add_flax_bundle(coll, "frame_tied_flax_bundle_l", (-1.18, -0.62, 0.37), 0.48, mats, quality=True)
        add_flax_bundle(coll, "frame_tied_flax_bundle_r", (1.18, 0.62, 0.37), 0.48, mats, quality=True)
    if level >= 4 and not incomplete:
        for y in (-0.72, -0.24, 0.24, 0.72):
            beam_between(coll, "tier4_cross_linen_guide", (-1.18, y, 0.54), (1.18, y, 0.54), 0.014, mats["rope"], 8)
    if level >= 5:
        for x, y in ((-1.08, -0.84), (1.08, -0.84), (-1.08, 0.84), (1.08, 0.84)):
            add_cube(coll, "tier5_stone_corner_foot", (x, y, 0.09), (0.30, 0.24, 0.16), mats["stone_block"], (0, 0, 0.18 if x * y > 0 else -0.18), 0.024, True)
    if level >= 6:
        for x in (-0.84, -0.28, 0.28, 0.84):
            add_cube(coll, "tier6_front_brick_inset", (x, -1.20, 0.30), (0.22, 0.055, 0.10), mats["brick"], (0, 0, 0.05), 0.010, True)
            add_cube(coll, "tier6_back_brick_inset", (x, 1.20, 0.30), (0.22, 0.055, 0.10), mats["brick"], (0, 0, -0.05), 0.010, True)
    if level >= 7:
        for x in (-0.58, 0.58):
            beam_between(coll, "tier7_low_fabric_bar", (x, -0.80, 0.00), (x, -0.80, 0.88), 0.022, mats["wood_dark"], 8)
        beam_between(coll, "tier7_fabric_support_rope", (-0.66, -0.80, 0.86), (0.66, -0.80, 0.86), 0.018, mats["rope"], 8)
        add_cube(coll, "tier7_folded_fabric_strip", (0.00, -0.82, 0.76), (0.96, 0.055, 0.11), mats["fabric"], (0, 0, 0.05), 0.014, True)
    if level >= 8:
        for x, y in ((-1.22, -0.96), (1.22, -0.96), (-1.22, 0.96), (1.22, 0.96)):
            add_cube(coll, "tier8_metal_corner_band", (x, y, 0.62), (0.06, 0.22, 0.13), mats["metal"], (0, 0, 0.18), 0.008, True)
    if level >= 9:
        for x in (-0.82, 0.0, 0.82):
            add_cube(coll, "tier9_gold_quality_mark", (x, -1.245, 0.70), (0.11, 0.035, 0.11), mats["gold"], (0, 0, 0.72), 0.009, True)
            add_cube(coll, "tier9_back_gold_quality_mark", (x, 1.245, 0.70), (0.11, 0.035, 0.11), mats["gold"], (0, 0, -0.72), 0.009, True)
    if level >= 10:
        add_cube(coll, "tier10_super_seed_locker", (0.92, -0.18, 0.46), (0.38, 0.24, 0.22), mats["premium_plank"], (0, 0, -0.16), 0.024, True)
        add_cube(coll, "tier10_locker_super_seed", (0.92, -0.18, 0.61), (0.18, 0.12, 0.08), mats["super_seed"], (0, 0, -0.16), 0.018, True)


def add_frame(coll, level, mats, incomplete=False, damaged=False, ruined=False):
    rail_mat = mats["wood_cut"] if level == 1 else (mats["premium_plank"] if level >= 8 else mats["plank_light"])
    side_mat = mats["wood"] if level == 1 else (mats["premium_plank"] if level >= 8 else mats["plank"])
    h = 0.18 + level * 0.040
    rail_thickness = 0.125 + min(level, 6) * 0.012
    side_length = 1.88 + min(level, 4) * 0.040
    rail_length = 2.52 + min(level, 4) * 0.070
    detail = min(3, level)
    segments = [
        ("front_flax_rail", (0, -1.00, h / 2), (rail_length, rail_thickness, h), "front"),
        ("back_flax_rail", (0, 1.00, h / 2), (rail_length, rail_thickness, h), "back"),
        ("left_flax_rail", (-1.32, 0, h / 2), (rail_thickness, side_length, h), "left"),
        ("right_flax_rail", (1.32, 0, h / 2), (rail_thickness, side_length, h), "right"),
    ]
    for name, loc, scale, orientation in segments:
        if incomplete and name == "back_flax_rail":
            add_flax_board(coll, name + "_unfinished_left", (-0.74, 1.00, h / 2), (0.76, rail_thickness, h), rail_mat, mats, orientation="back", detail=detail)
            add_cube(coll, "back_missing_rail_fiber_guide", (0.34, 1.02, h + 0.04), (0.52, 0.055, 0.055), mats["rope"], (0, 0, 0.18), 0.010, True)
            continue
        if ruined and name in {"front_flax_rail", "right_flax_rail"}:
            continue
        if damaged and name == "front_flax_rail":
            add_cube(coll, "snapped_front_flax_rail", (0.35, -1.04, h + 0.04), (0.92, 0.12, 0.12), mats["wood_dark"], (0.30, -0.04, 0.28), 0.020, True)
            add_cube(coll, "loose_blue_edge_strip", (-0.42, -1.10, 0.25), (0.48, 0.035, 0.045), mats["cloth_teal"], (0.12, 0, -0.34), 0.006, True)
            continue
        material = rail_mat if orientation in {"front", "back"} else side_mat
        add_flax_board(coll, name, loc, scale, material, mats, orientation=orientation, detail=detail, damaged=damaged)
    for x in (-0.78, 0.0, 0.78):
        if not incomplete:
            add_cube(coll, "front_flax_cap_slat", (x, -1.12, h + 0.035), (0.50, 0.050, 0.050), mats["plank_light" if level >= 2 else "wood_cut"], bevel=0.015, ground=True)
        if not ruined:
            add_cube(coll, "back_flax_cap_slat", (x, 1.12, h + 0.035), (0.50, 0.050, 0.050), mats["plank_light" if level >= 2 else "wood_cut"], bevel=0.015, ground=True)
    if level >= 2 and not damaged:
        for y in (-1.08, 1.08):
            for x in (-0.48, 0.48):
                add_cube(coll, "raised_linen_mid_rail", (x, y, h * 0.58), (0.54, 0.045, 0.050), mats["rope"], (0, 0, 0.06 if y < 0 else -0.06), 0.008, True)
    if level >= 3 and not damaged:
        for x in (-0.90, -0.30, 0.30, 0.90):
            if not incomplete:
                add_cube(coll, "front_upper_carved_slat", (x, -1.16, h + 0.115), (0.34, 0.045, 0.055), mats["plank_light"], (0, 0, 0.18), 0.012, True)
            if not ruined:
                add_cube(coll, "back_upper_carved_slat", (x, 1.16, h + 0.115), (0.34, 0.045, 0.055), mats["plank_light"], (0, 0, -0.18), 0.012, True)
        for y in (-0.62, 0.0, 0.62):
            add_cube(coll, "left_upper_carved_slat", (-1.40, y, h + 0.095), (0.045, 0.30, 0.055), mats["plank_light"], (0, 0, -0.14), 0.012, True)
            if not ruined:
                add_cube(coll, "right_upper_carved_slat", (1.40, y, h + 0.095), (0.045, 0.30, 0.055), mats["plank_light"], (0, 0, 0.14), 0.012, True)
    for x in (-1.28, 1.28):
        for y in (-0.96, 0.96):
            post_h = 0.36 + level * 0.15
            if ruined and (x, y) in {(1.28, -0.96), (1.28, 0.96)}:
                continue
            add_flax_corner_post(coll, "flax_bobbin_corner", x, y, post_h, mats, level=level, damaged=damaged)
    add_flax_frame_decor(coll, level, mats, incomplete=incomplete, damaged=damaged, ruined=ruined)


def add_level_props(coll, level, mats, rare=False):
    add_seed_bag(coll, "seed_bag_a", (-0.96, -0.66, 0.23), 1.0, mats)
    add_label(coll, "sort_label_a", -1.13, -0.28, level, mats, rare=False)
    if level >= 2:
        add_seed_bag(coll, "seed_bag_b", (1.02, 0.63, 0.22), 0.74, mats)
        add_drying_rack(coll, "small_flax_drying_rack", (0.92, -0.56, 0.28), 0.82, mats)
        for y in (-0.34, 0.34):
            beam_between(coll, "flax_layout_rope", (-1.00, y, 0.48), (1.00, y, 0.48), 0.022, mats["rope"], 8)
    if level >= 3:
        add_drying_rack(coll, "large_flax_drying_rack", (-0.88, 0.70, 0.34), 1.08, mats)
        add_cube(coll, "fiber_sorting_tray", (0.82, 0.70, 0.36), (0.64, 0.38, 0.14), mats["plank"], (0, 0, -0.18), 0.025, True)
        add_cube(coll, "tray_dry_flax_layer", (0.82, 0.70, 0.47), (0.52, 0.26, 0.04), mats["seed_gold"], (0, 0, -0.18), 0.010, True)
        for x in (-0.78, 0.78):
            beam_between(coll, "tall_flax_support_post", (x, 0.00, 0.00), (x, 0.00, 1.04), 0.026, mats["wood_dark"], 8)
        beam_between(coll, "tall_flax_support_rope", (-0.84, 0.00, 0.96), (0.84, 0.00, 0.96), 0.024, mats["rope"], 8)
        add_cube(coll, "blue_flax_marker_flag", (1.42, -0.66, 0.72), (0.055, 0.38, 0.16), mats["cloth_teal"], (0.04, 0.0, -0.38), 0.016, True)
        add_label(coll, "rare_label", 1.14, 0.18, level, mats, rare=True)
        if rare:
            add_cube(coll, "quality_fiber_box", (-0.02, -0.86, 0.35), (0.54, 0.26, 0.18), mats["tray"], (0, 0, 0.08), 0.025, True)
            add_cube(coll, "quality_fiber_lid", (-0.02, -0.86, 0.48), (0.42, 0.14, 0.035), mats["quality_blue"], (0, 0, 0.08), 0.010, True)
    if level >= 4:
        for y in (-0.44, 0.44):
            beam_between(coll, "tier4_tie_line", (-1.04, y, 0.62), (1.04, y, 0.62), 0.016, mats["rope"], 8)
    if level >= 5:
        add_cube(coll, "tier5_stone_seed_weight_a", (-0.52, 0.84, 0.20), (0.24, 0.16, 0.14), mats["stone"], (0, 0, 0.22), 0.022, True)
        add_cube(coll, "tier5_stone_seed_weight_b", (0.50, -0.84, 0.20), (0.24, 0.16, 0.14), mats["stone"], (0, 0, -0.24), 0.022, True)
    if level >= 6:
        add_cube(coll, "tier6_folded_fabric_roll", (-0.52, -0.88, 0.33), (0.42, 0.16, 0.15), mats["fabric"], (0, 0, 0.10), 0.026, True)
        add_cube(coll, "tier6_brick_tool_block", (0.48, 0.88, 0.22), (0.36, 0.18, 0.13), mats["brick"], (0, 0, -0.20), 0.018, True)
    if level >= 7:
        add_drying_rack(coll, "secondary_flax_drying_rack", (0.12, 0.86, 0.30), 0.70, mats)
        add_cube(coll, "tier7_bound_fabric_roll", (-0.12, -0.88, 0.33), (0.36, 0.15, 0.14), mats["fabric"], (0, 0, -0.08), 0.024, True)
    if level >= 8:
        add_cube(coll, "tier8_premium_fiber_chest", (-0.86, 0.02, 0.38), (0.42, 0.28, 0.24), mats["premium_plank"], (0, 0, 0.16), 0.030, True)
        add_cube(coll, "tier8_metal_chest_band", (-0.86, 0.02, 0.53), (0.46, 0.04, 0.06), mats["metal"], (0, 0, 0.16), 0.006, True)
    if level >= 9:
        add_cube(coll, "tier9_gold_linen_token_a", (-0.92, -0.38, 0.48), (0.14, 0.08, 0.06), mats["gold"], (0, 0, 0.30), 0.010, True)
        add_cube(coll, "tier9_gold_linen_token_b", (0.78, 0.38, 0.48), (0.14, 0.08, 0.06), mats["gold"], (0, 0, -0.30), 0.010, True)
    if level >= 10:
        add_cube(coll, "tier10_super_seed_case", (0.38, -0.86, 0.43), (0.40, 0.22, 0.21), mats["premium_plank"], (0, 0, 0.10), 0.028, True)
        add_cube(coll, "tier10_case_gold_latch", (0.38, -0.98, 0.47), (0.16, 0.035, 0.07), mats["gold"], (0, 0, 0.10), 0.006, True)
        add_cube(coll, "tier10_case_super_seed_glow", (0.38, -0.86, 0.60), (0.16, 0.11, 0.07), mats["super_seed"], (0, 0, 0.10), 0.014, True)
    for i, (x, y) in enumerate([(-1.12, 0.84), (1.10, -0.82), (1.12, 0.14), (-1.10, -0.14)]):
        add_cube(coll, "field_edge_stone", (x, y, 0.10), (0.16 + 0.03 * (i % 2), 0.12, 0.08), mats["stone"], (0, 0, 0.25 * i), 0.025, True)


def add_drying_rack(coll, name, center, scale, mats):
    x, y, z = center
    h = 0.68 * scale
    beam_between(coll, name + "_left_post", (x - 0.24 * scale, y, z), (x - 0.24 * scale, y, z + h), 0.028, mats["wood_dark"], 8)
    beam_between(coll, name + "_right_post", (x + 0.24 * scale, y, z), (x + 0.24 * scale, y, z + h), 0.028, mats["wood_dark"], 8)
    beam_between(coll, name + "_top_bar", (x - 0.34 * scale, y, z + h), (x + 0.34 * scale, y, z + h), 0.030, mats["wood"], 8)
    for index, offset in enumerate((-0.18, 0.0, 0.18)):
        add_flax_bundle(coll, f"{name}_hanging_bundle_{index}", (x + offset * scale, y - 0.02, z + h * 0.35), 0.70 * scale, mats, quality=False)


def add_flax_bundle(coll, name, center, scale, mats, quality=False, fallen=False):
    material = mats["seed_super" if quality else "seed_gold"]
    x, y, z = center
    if fallen:
        for index, offset in enumerate((-0.10, 0.0, 0.10)):
            add_cube(coll, f"{name}_fallen_stem_{index}", (x + offset * scale, y + 0.02 * index, z), (0.42 * scale, 0.040 * scale, 0.055 * scale), material, (0.16, 0.55, -0.30 + 0.08 * index), 0.010, True)
        add_cube(coll, name + "_tie", (x, y, z + 0.035 * scale), (0.30 * scale, 0.07 * scale, 0.035 * scale), mats["rope"], (0, 0, -0.16), 0.008, True)
        return
    for index, offset in enumerate((-0.09, 0.0, 0.09)):
        height = 0.56 * scale
        beam_between(coll, f"{name}_stem_{index}", (x + offset * scale, y, z), (x + offset * scale * 1.12, y + 0.018 * index, z + height), 0.017 * scale, material, 6)
    add_cube(coll, name + "_tie", (x, y, z + 0.28 * scale), (0.31 * scale, 0.07 * scale, 0.045 * scale), mats["rope"], (0, 0, 0.08), 0.010, True)


def add_seed_bag(coll, name, center, scale, mats, torn=False):
    mat_name = "bag_dark" if torn else "bag"
    add_cube(coll, name + "_body", center, (0.30 * scale, 0.24 * scale, 0.34 * scale), mats[mat_name], (0.08, 0.0, 0.25), 0.055, True)
    add_cube(coll, name + "_neck", (center[0], center[1], center[2] + 0.20 * scale), (0.18 * scale, 0.12 * scale, 0.10 * scale), mats["flax"], (0.08, 0.0, 0.30), 0.025, True)
    if torn:
        add_cube(coll, name + "_spilled_flax", (center[0] + 0.20, center[1] - 0.08, 0.18), (0.38, 0.16, 0.035), mats["seed_gold"], (0, 0, -0.25), 0.012, True)


def add_label(coll, name, x, y, level, mats, rare=False):
    beam_between(coll, name + "_post", (x, y, 0.00), (x, y, 0.64), 0.025, mats["wood_dark"], 6)
    add_cube(coll, name + "_board", (x, y, 0.72), (0.08, 0.31, 0.16), mats["plank_light"], (0, 0, 0.06), 0.016, True)
    add_cube(coll, name + "_mark", (x - 0.04, y, 0.74), (0.034, 0.13 + level * 0.02, 0.045), mats["quality_blue" if rare else "seed_pod"], (0, 0, 0.06), 0.006, True)


def add_plants(coll, level, stage, mats, super_crop=False, damaged=False):
    rows = [-0.50, -0.17, 0.17, 0.50] if not super_crop else [-0.42, -0.14, 0.14, 0.42]
    for row_index, y in enumerate(rows):
        count = 5 + level + (1 if super_crop else 0)
        for index in range(count):
            if damaged and (index + row_index) % 4 == 0:
                continue
            x = -0.96 + index * (1.92 / max(1, count - 1))
            jitter = 0.025 * ((index + row_index) % 3 - 1)
            plant_stage = min(6, stage + (1 if super_crop else 0))
            height = (0.22 + plant_stage * 0.15 + level * 0.05) * (1.10 if super_crop else 1.0)
            z0 = 0.27
            stem_mat = mats["seed_super"] if super_crop and stage >= 5 else (mats["sprout_light"] if plant_stage >= 3 else mats["sprout"])
            top_x = x + 0.025 * ((index + row_index) % 3 - 1)
            beam_between(coll, "flax_stem", (x, y + jitter, z0), (top_x, y + jitter, z0 + height), 0.012 + plant_stage * 0.002, stem_mat, 6)
            if plant_stage >= 2:
                for side in (-1, 1):
                    leaf_tip = (x + 0.08 * side, y + jitter + 0.025 * side, z0 + height * 0.46)
                    beam_between(coll, "thin_flax_leaf", (x, y + jitter, z0 + height * 0.34), leaf_tip, 0.008, mats["leaf_deep"], 5)
            if plant_stage >= 2:
                bloom = mats["seed_pod_light"] if super_crop else mats["seed_pod"]
                add_cube(coll, "flax_blue_bloom", (top_x, y + jitter, z0 + height + 0.035), (0.085, 0.070, 0.045), bloom, (0, 0, 0.15 * ((index % 3) - 1)), 0.014, True)
    if super_crop and stage >= 3:
        support_h = 0.72 + stage * 0.12
        for x in (-0.78, 0.78):
            beam_between(coll, "super_support_post", (x, 0.0, 0.00), (x, 0.0, support_h), 0.028, mats["wood"], 8)
        beam_between(coll, "super_support_rope", (-0.82, 0.0, support_h), (0.82, 0.0, support_h), 0.026, mats["rope"], 8)
    if stage >= 3 and not super_crop:
        add_flax_bundle(coll, "ready_flax_bundle_a", (-1.04, -0.76, 0.30), 0.82, mats)
        if level >= 2:
            add_flax_bundle(coll, "ready_flax_bundle_b", (1.08, 0.76, 0.30), 0.76, mats)
    if super_crop and stage >= 4:
        add_flax_bundle(coll, "quality_flax_bundle_a", (-1.02, -0.76, 0.31), 0.88, mats, quality=True)


def add_construction(coll, level, mats):
    add_plants(coll, level, 1, mats)
    for x in (-0.42, 0.12, 0.66):
        add_cube(coll, "loose_plank_stack", (x, -1.06, 0.16), (0.54, 0.13, 0.08), mats["plank" if level >= 2 else "wood"], (0, 0, -0.28 + x * 0.1), 0.018, True)
    add_seed_bag(coll, "builder_seed_bag", (0.74, 0.78, 0.22), 0.82, mats)
    beam_between(coll, "loose_layout_rope", (-0.58, 0.68, 0.30), (-0.08, 0.88, 0.30), 0.023, mats["rope"], 8)
    add_cube(coll, "unfinished_back_gap_marker", (0.58, 0.92, 0.46), (0.42, 0.12, 0.10), mats["wood_cut"], (0, 0, 0.30), 0.018, True)


def add_damage(coll, level, mats, ruined=False):
    stage = 1 if ruined else 2
    add_plants(coll, level, stage, mats, damaged=True)
    add_seed_bag(coll, "torn_seed_bag", (-0.72 if ruined else 0.82, -0.72, 0.20), 0.78, mats, torn=True)
    add_flax_bundle(coll, "fallen_flax_bundle", (0.64, -0.74, 0.24), 0.90, mats, fallen=True)
    add_cube(coll, "fallen_stake", (-0.86, 0.64, 0.23), (0.74, 0.11, 0.09), mats["wood_dark"], (0.05, 0.65, -0.70), 0.020, True)
    add_cube(coll, "trampled_seed_soil", (0.12, -0.02, 0.31), (1.02 if not ruined else 1.36, 0.58 if not ruined else 0.90, 0.05), mats["earth_dark"], (0, 0, 0.18), 0.020, True)
    if ruined:
        for x, y, yaw in ((0.64, -0.98, 0.42), (-1.02, 0.88, -0.58), (0.32, 0.76, 0.18)):
            add_cube(coll, "ruin_plank", (x, y, 0.18), (0.68, 0.10, 0.08), mats["wood_dark"], (0.0, 0.0, yaw), 0.018, True)


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("flax_field_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "flax_field"
    coll["level"] = level
    coll["state"] = state
    add_ground(coll, mats)
    if state == "construction":
        add_frame(coll, level, mats, incomplete=True)
        add_construction(coll, level, mats)
    elif state == "damaged":
        add_frame(coll, level, mats, damaged=True)
        add_damage(coll, level, mats)
    elif state == "ruined":
        add_frame(coll, level, mats, ruined=True)
        add_damage(coll, level, mats, ruined=True)
    elif state.startswith("super_stage"):
        add_frame(coll, level, mats)
        add_level_props(coll, level, mats, rare=True)
        add_plants(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        add_frame(coll, level, mats)
        add_level_props(coll, level, mats)
        add_plants(coll, level, 3 if state == "active" else int(state[-2:]), mats)
    scale_model_to_tile(coll)
    return coll


def asset_variants():
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    variants = []
    for level in LEVELS:
        for state in states:
            variants.append((f"flax_field_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"flax_field_l{level:02d}_{state}", level, state))
    return variants


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(scene):
    data = bpy.data.cameras.new("flax_field_isometric_camera")
    cam = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(cam)
    cam.location = (8, -8, math.sqrt(128) / math.sqrt(3))
    cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = 512 * 3.6 * math.sqrt(2) / 278
    scene.camera = cam
    scene.render.resolution_x = PNG_SIZE[0]
    scene.render.resolution_y = PNG_SIZE[1]
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    target_y = 1 - ANCHOR[1] / PNG_SIZE[1]
    initial = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y
    data.shift_y = 0.1
    delta = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y - initial
    data.shift_y = (target_y - initial) * 0.1 / delta
    for lname, pos, energy, size in (("key", (-3, -5, 8), 1000, 5), ("fill", (5, 1, 6), 650, 5)):
        light = bpy.data.lights.new("flax_field_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("flax_field_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.65, 0.75, 0.90, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"


def create_asset_scene(name: str, level: int, state: str, mats):
    scene = bpy.data.scenes.new("Real_City_Flax_Field_Render_" + name)
    root = bpy.data.collections.new(name + "_root")
    scene.collection.children.link(root)
    coll = make_variant(name, level, state, mats, root)
    setup_camera(scene)
    return scene, coll


def clean_collection_meshes(coll):
    bpy.context.view_layer.update()
    for obj in coll.all_objects:
        if obj.type != "MESH":
            continue
        obj.data.calc_loop_triangles()


def triangle_count(coll) -> int:
    total = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in coll.all_objects:
        if obj.type != "MESH":
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        eval_obj.to_mesh_clear()
    return total


def export_collection(coll):
    for obj in bpy.data.objects:
        obj.select_set(False)
    objects = list(coll.all_objects)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None
    bpy.ops.export_scene.gltf(filepath=blender_path(OUT_DIR / f"{coll.name}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)


def render_scene(scene, name):
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.render.filepath = blender_path(OUT_DIR / f"{name}.png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)


def cleanup_generated():
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Flax_Field_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("flax_field_") or coll.name.endswith("_root"):
            for obj in list(coll.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(coll)


def save_manifest(report_items):
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined", "super_stage01", "super_stage02", "super_stage03", "super_stage04", "super_stage05", "super_stage06"]
    manifest = {
        "asset_id": "flax_field",
        "category": "fields",
        "display_name": "Льняное поле",
        "style": "Aeolian bright fantasy stylized mid-poly",
        "pipeline": "blender_mcp_midpoly",
        "levels": LEVELS,
        "states": states,
        "sprite": {"size": PNG_SIZE, "anchor": ANCHOR},
        "source_blend": BLEND_PATH.name,
        "items": [
            {
                "id": item["name"],
                "level": item["level"],
                "state": item["state"],
                "glb": f"{item['name']}.glb",
                "png": f"{item['name']}.png",
                "anchor": ANCHOR,
                "triangles": item["triangles"],
            }
            for item in report_items
        ],
    }
    report = {
        "asset": "flax_field",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": LEVELS,
        "states": states,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "MCP/Blender generation route; legacy pure-Python fallback is not used",
            "level 1 uses a simple low flax frame with pale rails, grooves and seed bag",
            "level 2 raises the bed walls and adds linen-blue inlays, rope tie blocks, guide ropes and a small drying rack",
            "level 3 raises the frame again and adds carved panels, diagonal fiber stitches, double upper slats, blue rosettes, a larger drying rack and quality fiber props",
            "levels 4-10 progressively add more tie lines, stone pads, brick insets, fabric supports, premium wood, metal bands, gold quality marks and a super-seed case",
            "construction/damaged/ruined keep the same ground tile and change only overlay geometry",
        ],
        "assets": report_items,
    }
    with open(blender_path(OUT_DIR / "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(blender_path(REPORT_PATH), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    ensure_dir()
    cleanup_generated()
    mats = make_materials()
    report_items = []
    lines = []
    last_scene = None
    for name, level, state in asset_variants():
        scene, coll = create_asset_scene(name, level, state, mats)
        last_scene = scene
        if bpy.context.window:
            bpy.context.window.scene = scene
        clean_collection_meshes(coll)
        tris = triangle_count(coll)
        export_collection(coll)
        render_scene(scene, name)
        report_items.append({"name": name, "level": level, "state": state, "triangles": tris})
        lines.append(f"{name}: triangles={tris}")
    if last_scene and bpy.context.window:
        bpy.context.window.scene = last_scene
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    save_manifest(report_items)
    with open(blender_path(LOG_PATH), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write(f"\nFLAX_FIELD_BLENDER_COMPLETE {len(report_items)}\n")
    print("FLAX_FIELD_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
