"""Build Blender master/runtime assets for mushroom grove levels 1-10.

This is the Blender/MCP production route. It creates a distinct dark, organic
field asset for `mushroom_grove`, not a recolored plank crop bed.
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
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/mushroom_grove"
BLEND_PATH = OUT_DIR / "mushroom_grove_l01_l10.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-mushroom-grove-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.22
LEVELS = list(range(1, 11))

MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "soil_wet": (0.20, 0.13, 0.10, 1),
    "soil_shadow": (0.12, 0.08, 0.06, 1),
    "moss": (0.18, 0.43, 0.16, 1),
    "moss_light": (0.38, 0.64, 0.24, 1),
    "root": (0.33, 0.20, 0.11, 1),
    "root_dark": (0.20, 0.12, 0.07, 1),
    "wood_rot": (0.42, 0.29, 0.17, 1),
    "wood_cut": (0.74, 0.52, 0.29, 1),
    "wood_fence": (0.58, 0.36, 0.18, 1),
    "premium_wood": (0.72, 0.43, 0.18, 1),
    "resin": (0.86, 0.46, 0.14, 1),
    "rope": (0.62, 0.48, 0.27, 1),
    "cloth_shadow": (0.22, 0.28, 0.24, 0.36),
    "cloth_moss": (0.30, 0.46, 0.32, 0.34),
    "clay": (0.55, 0.32, 0.18, 1),
    "brick": (0.62, 0.20, 0.12, 1),
    "stone": (0.48, 0.50, 0.45, 1),
    "stone_light": (0.64, 0.66, 0.58, 1),
    "stone_block": (0.55, 0.57, 0.53, 1),
    "metal": (0.30, 0.33, 0.35, 1),
    "metal_light": (0.55, 0.58, 0.57, 1),
    "emerald_dust": (0.12, 0.78, 0.48, 1),
    "cap_brown": (0.55, 0.31, 0.18, 1),
    "cap_tan": (0.76, 0.54, 0.34, 1),
    "cap_red": (0.64, 0.22, 0.17, 1),
    "cap_pale": (0.86, 0.77, 0.58, 1),
    "stem": (0.82, 0.72, 0.56, 1),
    "stem_shadow": (0.58, 0.48, 0.35, 1),
    "glow_blue": (0.42, 0.76, 0.96, 1),
    "glow_soft": (0.60, 0.90, 1.00, 1),
    "bag": (0.70, 0.58, 0.38, 1),
    "bag_dark": (0.42, 0.31, 0.18, 1),
}


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        return BLENDER_ROOT + "\\" + raw[len(root) :].lstrip("\\")
    if str(path).startswith("/tmp/") or raw.lower().startswith("\\tmp\\"):
        return r"\\wsl.localhost\Debian" + raw
    return raw


def ensure_dir() -> None:
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)


def mat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new("MAT_mushroom_grove_" + name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.82
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = color[3]
    if name.startswith("glow"):
        material.diffuse_color = color
        if bsdf and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
        if bsdf and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.35
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_mushroom_grove_"):
            bpy.data.materials.remove(material)
    return {name: mat(name, color) for name, color in MATERIALS.items()}


def add_cube(coll, name, loc, scale, material, rot=(0, 0, 0), bevel=0.015, ground=False):
    sx, sy, sz = scale[0] * 0.5, scale[1] * 0.5, scale[2] * 0.5
    verts = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
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


def add_cylinder(coll, name, loc, radius, depth, material, vertices=12, rot=(0, 0, 0), bevel=0.0):
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


def add_ellipsoid(coll, name, loc, scale, material, vertices=12, subdivisions=2, rot=(0, 0, 0), bevel=False):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    if bevel:
        mod = obj.modifiers.new("soft_organic_edges", "BEVEL")
        mod.width = 0.006
        mod.segments = 1
    return obj


def add_ground(coll, mats):
    add_cube(coll, "mushroom_grove_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.26, 0.96), (1.24, 1.02), (1.18, -1.10), (-1.20, -1.02)]):
        for j in range(3):
            beam_between(
                coll,
                "terrain_grass_tuft",
                (x + (j - 1) * 0.045, y, 0.008),
                (x + (j - 1) * 0.085, y + 0.030, 0.105 + 0.026 * (i % 2)),
                0.025,
                mats["grass_light"],
                6,
            )
    add_ellipsoid(coll, "wet_oval_substrate", (0, 0, 0.095), (1.34, 1.02, 0.105), mats["soil_wet"], subdivisions=3)
    add_ellipsoid(coll, "dark_center_humus", (-0.04, -0.02, 0.175), (0.92, 0.68, 0.050), mats["soil_shadow"], subdivisions=2)
    for x, y, sx, sy in [(-0.72, 0.34, 0.40, 0.14), (0.58, -0.38, 0.46, 0.16), (0.02, 0.58, 0.38, 0.12)]:
        add_ellipsoid(coll, "moss_patch", (x, y, 0.215), (sx, sy, 0.026), mats["moss"], subdivisions=1, rot=(0, 0, 0.3))


def late_bed_scale(level: int) -> float:
    if level < 5:
        return 1.0
    return 1.10 + min(level - 5, 5) * 0.035


def wall_radii(level: int) -> tuple[float, float]:
    if level < 5:
        return 1.10, 0.88
    scale = late_bed_scale(level)
    return 1.10 * scale, 0.88 * scale


def circular_points(count: int, rx: float = 1.10, ry: float = 0.88, phase: float = 0.0):
    return [
        (math.cos(phase + i * math.tau / count) * rx, math.sin(phase + i * math.tau / count) * ry)
        for i in range(count)
    ]


def wall_profile(level: int):
    height = [0, 0.10, 0.18, 0.30, 0.38, 0.48, 0.62, 0.54, 0.58, 0.62, 0.66][level]
    if level == 1:
        return {"height": height, "lower": None, "upper": None, "posts": "root_dark", "segments": 10}
    if level == 2:
        return {"height": height, "lower": "wood_fence", "upper": "wood_fence", "posts": "wood_fence", "segments": 12}
    if level == 3:
        return {"height": height, "lower": "wood_fence", "upper": "wood_fence", "posts": "wood_fence", "segments": 12}
    if level == 4:
        return {"height": height, "lower": "clay", "upper": "wood_fence", "posts": "wood_fence", "segments": 14}
    if level == 5:
        return {"height": height, "lower": "stone", "upper": "wood_fence", "posts": "wood_fence", "segments": 14}
    if level == 6:
        return {"height": height, "lower": "stone_block", "upper": "stone_light", "posts": "stone_block", "segments": 16}
    if level == 7:
        return {"height": height, "lower": "stone_block", "upper": "stone_light", "posts": "stone_block", "segments": 16}
    if level == 8:
        return {"height": height, "lower": "brick", "upper": "stone_block", "posts": "premium_wood", "segments": 18}
    if level == 9:
        return {"height": height, "lower": "stone_block", "upper": "stone_block", "posts": "stone_block", "segments": 18}
    return {"height": height, "lower": "stone_block", "upper": "stone_block", "posts": "metal", "segments": 20}


def add_level_substrate(coll, level, mats):
    if level < 5:
        return
    scale = late_bed_scale(level)
    add_ellipsoid(coll, "expanded_wet_mushroom_bed", (0, 0, 0.205), (1.20 * scale, 0.91 * scale, 0.052), mats["soil_wet"], subdivisions=2)
    add_ellipsoid(coll, "open_dark_mushroom_rows", (-0.03, -0.02, 0.255), (0.86 * scale, 0.61 * scale, 0.026), mats["soil_shadow"], subdivisions=2)
    for i, (x, y, sx, sy, yaw) in enumerate([
        (-0.56, 0.44, 0.34, 0.10, 0.22),
        (0.62, -0.42, 0.38, 0.11, -0.16),
        (0.18, 0.62, 0.30, 0.09, 0.08),
    ]):
        add_ellipsoid(coll, "expanded_moss_lace", (x * scale, y * scale, 0.290), (sx, sy, 0.018), mats["moss_light"], subdivisions=1, rot=(0, 0, yaw))


def add_wall_decor(coll, level, mats, x, y, yaw, z, idx):
    if level >= 3:
        add_cube(coll, "small_mushroom_wall_shelf", (x, y, z + 0.03), (0.16, 0.038, 0.055), mats["cap_tan"], (0, 0, yaw), 0.012, True)
    if level >= 4 and idx % 2 == 0:
        add_ellipsoid(coll, "clay_roundel", (x, y, z + 0.08), (0.050, 0.018, 0.050), mats["clay"], subdivisions=1, rot=(0, 0, yaw))
    if level >= 6:
        add_cube(coll, "carved_stone_plate", (x, y, z + 0.12), (0.18, 0.035, 0.070), mats["stone_light"], (0, 0, yaw), 0.010, True)
        if idx % 2 == 0:
            add_ellipsoid(coll, "moss_gem_wall_dot", (x, y, z + 0.02), (0.042, 0.014, 0.032), mats["moss_light"], subdivisions=1, rot=(0, 0, yaw))
        else:
            add_cube(coll, "resin_wall_streak", (x, y, z - 0.02), (0.050, 0.028, 0.100), mats["resin"], (0, 0, yaw), 0.008, True)
    if level >= 8 and idx % 3 == 0:
        add_cube(coll, "premium_wood_trim", (x, y, z + 0.20), (0.20, 0.030, 0.045), mats["premium_wood"], (0, 0, yaw), 0.010, True)
    if level >= 9 and idx % 2 == 1:
        add_ellipsoid(coll, "metal_wall_stud", (x, y, z + 0.16), (0.035, 0.014, 0.035), mats["metal_light"], subdivisions=1, rot=(0, 0, yaw))
        add_cube(coll, "metal_decor_strap", (x, y, z + 0.05), (0.030, 0.022, 0.180), mats["metal"], (0, 0, yaw), 0.006, True)
    if level >= 10 and idx % 2 == 0:
        add_ellipsoid(coll, "emerald_dust_inlay", (x, y, 0.17), (0.045, 0.012, 0.025), mats["emerald_dust"], subdivisions=1, rot=(0, 0, yaw))


def add_round_wall(coll, level, mats, *, construction=False, damaged=False, ruined=False):
    profile = wall_profile(level)
    rx, ry = wall_radii(level)
    points = circular_points(profile["segments"], rx=rx, ry=ry, phase=0.10)
    gate_idx = None
    if level >= 6:
        gate_idx = min(
            range(profile["segments"]),
            key=lambda i: (points[i][1] + points[(i + 1) % profile["segments"]][1]) * 0.5,
        )
    skip = set()
    if construction:
        skip = set(range(profile["segments"] // 5, profile["segments"] // 5 + 4))
    if damaged:
        skip = {2, 3, profile["segments"] - 2}
    if ruined:
        skip = set(range(1, 5)) | {profile["segments"] - 2, profile["segments"] - 1}
    if gate_idx is not None and not construction and not damaged and not ruined:
        skip.add(gate_idx)

    if level == 1:
        for idx, (x, y) in enumerate(points[::2]):
            add_cube(coll, "low_mossy_root_marker", (x, y, 0.135), (0.30, 0.11, 0.11), mats["root_dark"], (0.08, 0.16, math.atan2(y, x) + math.pi / 2), 0.024, True)
        return

    lower_h = profile["height"] * (0.15 if level == 7 else 0.40 if level == 8 else 0.55 if level == 5 else 0.46)
    if level == 9:
        lower_h = profile["height"] * 0.28
    if level == 10:
        lower_h = profile["height"] * 0.22
    upper_h = max(0.05, profile["height"] - lower_h)
    thickness = 0.115 + min(level, 10) * 0.005

    for idx, (x1, y1) in enumerate(points):
        if idx in skip:
            continue
        x2, y2 = points[(idx + 1) % len(points)]
        if (idx + 1) % len(points) in skip and not construction:
            continue
        mx, my = (x1 + x2) * 0.5, (y1 + y2) * 0.5
        yaw = math.atan2(y2 - y1, x2 - x1)
        length = math.dist((x1, y1), (x2, y2)) * 1.07
        add_cube(coll, "round_wall_lower_course", (mx, my, 0.135 + lower_h * 0.5), (length, thickness, lower_h), mats[profile["lower"]], (0, 0, yaw), 0.022, True)
        if upper_h > 0.06:
            add_cube(coll, "round_wall_upper_course", (mx, my, 0.135 + lower_h + upper_h * 0.5), (length, thickness * 0.94, upper_h), mats[profile["upper"]], (0, 0, yaw), 0.020, True)
        if level >= 3:
            for rail_z in (0.135 + lower_h + upper_h * 0.34, 0.135 + lower_h + upper_h * 0.75):
                add_cube(coll, "continuous_fence_rail", (mx, my, rail_z), (length * 0.98, thickness * 1.08, 0.035), mats["premium_wood" if level >= 8 else "wood_fence"], (0, 0, yaw), 0.010, True)
        decor_x = mx + math.cos(yaw + math.pi / 2) * 0.065
        decor_y = my + math.sin(yaw + math.pi / 2) * 0.065
        add_wall_decor(coll, level, mats, decor_x, decor_y, yaw, 0.135 + lower_h, idx)

    post_step = 1 if level >= 7 else 2
    for idx, (x, y) in enumerate(points):
        if idx in skip and not construction:
            continue
        post_mat = mats["metal"] if level >= 10 else mats[profile["posts"]]
        post_h = profile["height"] + (0.16 if level >= 7 else 0.09 if level >= 3 else 0.04)
        radius = 0.055 + level * 0.005
        if idx % post_step == 0:
            add_cylinder(coll, "round_wall_post", (x, y, 0.135 + post_h * 0.5), radius, post_h, post_mat, 10, bevel=0.012)
            if level >= 7:
                add_cube(coll, "stone_post_cap", (x, y, 0.155 + post_h), (0.16, 0.16, 0.055), mats["stone_light" if level < 10 else "metal_light"], (0, 0, idx * 0.2), 0.014, True)
    if gate_idx is not None and not damaged and not ruined:
        add_gate(coll, level, mats, points, gate_idx, profile["height"], construction=construction)
    if damaged or ruined:
        rubble_mat = "stone_block" if level >= 5 else "wood_fence"
        for x, y, yaw in [(-0.72, -0.78, 0.5), (0.72, 0.70, -0.4), (0.12, -0.98, 0.1)]:
            add_cube(coll, "fallen_round_wall_piece", (x, y, 0.22), (0.62, 0.15, 0.14), mats[rubble_mat], (0.12, 0.28, yaw), 0.026, True)


def add_gate(coll, level, mats, points, gate_idx, wall_height, *, construction=False):
    x1, y1 = points[gate_idx]
    x2, y2 = points[(gate_idx + 1) % len(points)]
    mx, my = (x1 + x2) * 0.5, (y1 + y2) * 0.5
    yaw = math.atan2(y2 - y1, x2 - x1)
    length = min(0.44 + level * 0.018, math.dist((x1, y1), (x2, y2)) * 0.86)
    door_h = max(0.32, wall_height * (0.80 if level < 9 else 0.90))
    if construction:
        add_cube(coll, "unfinished_gate_threshold", (mx, my, 0.165), (length, 0.12, 0.060), mats["stone_block"], (0, 0, yaw), 0.014, True)
        return
    if level >= 9:
        gate_mat = mats["metal"]
        trim_mat = mats["metal_light"]
        name = "decorated_metal_mushroom_door"
    elif level == 8:
        gate_mat = mats["brick"]
        trim_mat = mats["stone_light"]
        name = "brick_tone_gate"
    else:
        gate_mat = mats["stone_block"]
        trim_mat = mats["stone_light"]
        name = "stone_tone_gate"
    add_cube(coll, name, (mx, my, 0.135 + door_h * 0.5), (length, 0.105, door_h), gate_mat, (0, 0, yaw), 0.018, True)
    add_cube(coll, "gate_top_trim", (mx, my, 0.155 + door_h), (length * 1.08, 0.125, 0.050), trim_mat, (0, 0, yaw), 0.010, True)
    add_cube(coll, "gate_vertical_trim", (mx - math.cos(yaw) * length * 0.25, my - math.sin(yaw) * length * 0.25, 0.135 + door_h * 0.52), (0.035, 0.128, door_h * 0.78), trim_mat, (0, 0, yaw), 0.008, True)
    add_cube(coll, "gate_vertical_trim", (mx + math.cos(yaw) * length * 0.25, my + math.sin(yaw) * length * 0.25, 0.135 + door_h * 0.52), (0.035, 0.128, door_h * 0.78), trim_mat, (0, 0, yaw), 0.008, True)
    if level >= 9:
        add_ellipsoid(coll, "gate_metal_boss", (mx, my, 0.135 + door_h * 0.62), (0.050, 0.018, 0.050), mats["metal_light"], subdivisions=1, rot=(0, 0, yaw))
        add_cube(coll, "gate_emerald_inlay", (mx, my, 0.135 + door_h * 0.34), (0.140, 0.020, 0.028), mats["emerald_dust"], (0, 0, yaw), 0.006, True)


def add_mushroom(coll, name, x, y, scale, mats, *, cap="cap_brown", glow=False, fallen=False):
    if fallen:
        add_cylinder(coll, name + "_fallen_stem", (x, y, 0.26), 0.045 * scale, 0.42 * scale, mats["stem_shadow"], 10, rot=(math.pi / 2, 0, 0.35), bevel=0.010)
        add_ellipsoid(coll, name + "_fallen_cap", (x + 0.24 * scale, y + 0.05, 0.25), (0.18 * scale, 0.15 * scale, 0.055 * scale), mats[cap], subdivisions=2, rot=(0.12, 0.2, 0.1))
        return
    h = 0.20 * scale
    add_cylinder(coll, name + "_stem", (x, y, 0.26 + h * 0.45), 0.040 * scale, h, mats["stem"], 10, bevel=0.008)
    add_ellipsoid(coll, name + "_cap", (x, y, 0.29 + h), (0.16 * scale, 0.14 * scale, 0.065 * scale), mats["glow_soft" if glow else cap], subdivisions=2)
    if scale > 1.05:
        add_ellipsoid(coll, name + "_cap_spot", (x - 0.035 * scale, y - 0.030 * scale, 0.33 + h), (0.030 * scale, 0.022 * scale, 0.008 * scale), mats["cap_pale"], subdivisions=1)
        add_ellipsoid(coll, name + "_cap_spot", (x + 0.045 * scale, y + 0.018 * scale, 0.34 + h), (0.024 * scale, 0.020 * scale, 0.008 * scale), mats["cap_pale"], subdivisions=1)


def add_mushroom_groups(coll, level, stage, mats, *, super_crop=False, damaged=False, ruined=False):
    stage_factor = max(1, stage)
    spread = 1.0 if level < 5 else 1.04 + min(level - 5, 5) * 0.025
    groups = [
        (-0.52, -0.30, 0.80), (-0.18, 0.12, 0.70), (0.42, -0.18, 0.90),
        (0.58, 0.38, 0.62), (-0.66, 0.42, 0.58), (0.04, -0.58, 0.54),
    ]
    visible_count = min(len(groups), 2 + stage_factor + level // 3)
    if ruined:
        visible_count = 2
    for idx, (gx, gy, base) in enumerate(groups[:visible_count]):
        gx *= spread
        gy *= spread
        if damaged and idx % 3 == 1:
            add_mushroom(coll, "broken_mushroom", gx, gy, base * 0.9, mats, cap="cap_tan", fallen=True)
            continue
        cap = "cap_red" if (idx + level) % 4 == 0 and stage_factor >= 3 else ("cap_tan" if idx % 2 else "cap_brown")
        glow = super_crop or (level >= 8 and stage_factor >= 3 and idx in {0, 3})
        count = 1 + (stage_factor >= 2) + (stage_factor >= 3 and idx % 2 == 0)
        for j in range(count):
            offset = (j - (count - 1) * 0.5) * 0.12
            scale = (base + 0.10 * stage_factor + 0.035 * level) * (1.22 if super_crop else 1.0)
            add_mushroom(coll, "mushroom_cluster", gx + offset, gy + 0.06 * ((j % 2) - 0.5), scale, mats, cap=cap, glow=glow)
    if super_crop:
        add_mushroom(coll, "central_super_mushroom", 0.05, 0.02, 1.70 + stage * 0.08, mats, cap="cap_pale", glow=True)
        for x, y in [(-0.30, 0.30), (0.32, -0.30), (0.42, 0.22)]:
            add_ellipsoid(coll, "blue_mycelium_node", (x, y, 0.265), (0.055, 0.040, 0.025), mats["glow_blue"], subdivisions=1)


def add_level_props(coll, level, mats, *, super_crop=False):
    add_cube(coll, "half_buried_log", (-0.80, 0.05, 0.30), (0.86, 0.20, 0.18), mats["wood_rot"], (0.05, 0.25, -0.68), 0.040, True)
    add_cube(coll, "fresh_cut_log_side", (-1.12, -0.09, 0.31), (0.08, 0.22, 0.16), mats["wood_cut"], (0.05, 0.25, -0.68), 0.018, True)
    if level >= 2:
        add_cube(coll, "substrate_sack", (0.92, -0.60, 0.22), (0.30, 0.24, 0.34), mats["bag"], (0.06, 0.0, 0.30), 0.050, True)
        add_cube(coll, "mossy_stone", (-0.94, 0.64, 0.14), (0.24, 0.18, 0.12), mats["stone"], (0, 0, -0.18), 0.030, True)
        add_ellipsoid(coll, "moss_on_stone", (-0.94, 0.64, 0.215), (0.13, 0.08, 0.018), mats["moss_light"], subdivisions=1)
    if level >= 3:
        for x in (-0.72, 0.72):
            beam_between(coll, "thin_canopy_rod", (x, -0.54, 0.14), (x * 0.82, 0.48, 0.72), 0.018, mats["root_dark"], 8)
    if level >= 4:
        for x, y in [(-0.92, -0.42), (0.84, 0.56)]:
            add_cube(coll, "resin_brace_block", (x, y, 0.40), (0.18, 0.12, 0.22), mats["resin"], (0, 0, 0.22), 0.018, True)
    if level >= 5:
        add_canopy(coll, level, mats)
    if level >= 6:
        span = late_bed_scale(level)
        for y in (-0.76 * span, 0.76 * span):
            beam_between(coll, "premium_canopy_beam", (-1.02 * span, y, 1.18), (1.02 * span, y * 0.78, 1.26), 0.040, mats["premium_wood"], 8)
        add_cube(coll, "hanging_moss_cloth", (-0.48 * span, 0.82 * span, 1.04), (0.10, 0.32, 0.20), mats["cloth_moss"], (0.08, 0.02, 0.18), 0.010, True)
    if level >= 8:
        for x, y in [(-0.62, -0.62), (0.64, 0.60), (0.78, -0.12)]:
            add_ellipsoid(coll, "soft_blue_spore_lamp", (x, y, 0.42), (0.050, 0.040, 0.070), mats["glow_blue"], subdivisions=1)
        for x, y, yaw in [(-0.44, -0.82, -0.08), (0.52, 0.78, 0.12)]:
            add_cube(coll, "polished_premium_board_stack", (x, y, 0.34), (0.42, 0.10, 0.10), mats["premium_wood"], (0.02, 0.0, yaw), 0.018, True)
    if level >= 10:
        for x, y, s in [(-0.88, 0.08, 1.15), (0.92, -0.10, 1.05), (0.0, 0.90, 0.96)]:
            add_ellipsoid(coll, "super_mushroom_cap_arch_piece", (x, y, 1.03), (0.19 * s, 0.13 * s, 0.055 * s), mats["glow_soft"], subdivisions=2, rot=(0.06, 0.04, 0.2))
    if super_crop and level >= 7:
        add_cube(coll, "protected_spore_crate", (0.18, -0.86, 0.36), (0.52, 0.26, 0.18), mats["wood_rot"], (0, 0, 0.08), 0.026, True)
        add_ellipsoid(coll, "glowing_spore_sample", (0.18, -0.86, 0.49), (0.16, 0.06, 0.035), mats["glow_soft"], subdivisions=1)


def add_canopy(coll, level, mats, *, construction=False, damaged=False):
    if level < 5:
        return
    if level == 5:
        z = 1.22
        scale = late_bed_scale(level)
        for x in (-0.86 * scale, 0.86 * scale):
            beam_between(coll, "thin_canopy_support_rod", (x, -0.68 * scale, 0.18), (x * 0.84, 0.68 * scale, z), 0.016, mats["root_dark"], 8)
        if not construction:
            add_cube(coll, "high_full_thin_cloth_canopy", (0.0, 0.02, z), (2.20 * scale, 1.45 * scale, 0.045), mats["cloth_shadow"], (0.08, 0.025, 0.04), 0.012, True)
    elif level in {6, 7}:
        z = 1.42 if level == 6 else 1.50
        scale = late_bed_scale(level)
        for x in (-0.98 * scale, 0.98 * scale):
            beam_between(coll, "premium_canopy_support", (x, -0.76 * scale, 0.18), (x * 0.86, 0.76 * scale, z), 0.042, mats["premium_wood"], 8)
        if not construction:
            add_cube(coll, "high_full_thick_canopy_panel", (0.0, 0.00, z), (2.38 * scale, 1.52 * scale, 0.085), mats["cloth_moss"], (0.08, 0.025, 0.02), 0.018, True)
            for x in (-0.58 * scale, 0.0, 0.58 * scale):
                add_cube(coll, "premium_canopy_rib", (x, 0.0, z + 0.055), (0.08, 1.62 * scale, 0.055), mats["premium_wood"], (0.08, 0.02, 0.02), 0.012, True)
    elif level in {8, 9}:
        z = 1.62 if level == 8 else 1.72
        scale = late_bed_scale(level)
        for x in (-1.02 * scale, -0.34 * scale, 0.34 * scale, 1.02 * scale):
            beam_between(coll, "premium_roof_rafter", (x, -0.78 * scale, 0.22), (x * 0.72, 0.0, z + 0.24), 0.045, mats["premium_wood"], 8)
            beam_between(coll, "premium_roof_rafter", (x, 0.78 * scale, 0.22), (x * 0.72, 0.0, z + 0.24), 0.045, mats["premium_wood"], 8)
        if not construction:
            add_cube(coll, "high_sloped_left_canopy_roof", (-0.55 * scale, 0.0, z), (1.18 * scale, 1.72 * scale, 0.080), mats["cloth_moss"], (0.0, -0.24, 0.0), 0.018, True)
            add_cube(coll, "high_sloped_right_canopy_roof", (0.55 * scale, 0.0, z), (1.18 * scale, 1.72 * scale, 0.080), mats["cloth_shadow"], (0.0, 0.24, 0.0), 0.018, True)
            if level >= 9:
                add_cube(coll, "metal_roof_ridge", (0.0, 0.0, z + 0.24), (0.12, 1.88 * scale, 0.08), mats["metal"], (0, 0, 0), 0.012, True)
    else:
        z = 1.86
        scale = late_bed_scale(level)
        for x in (-1.10 * scale, -0.38 * scale, 0.38 * scale, 1.10 * scale):
            beam_between(coll, "metal_complex_canopy_strut", (x, -0.82 * scale, 0.24), (x * 0.66, 0.0, z + 0.30), 0.050, mats["metal"], 10)
            beam_between(coll, "metal_complex_canopy_strut", (x, 0.82 * scale, 0.24), (x * 0.66, 0.0, z + 0.30), 0.050, mats["metal"], 10)
        if not construction:
            add_cube(coll, "high_complex_canopy_left_slab", (-0.68 * scale, 0.0, z), (1.12 * scale, 1.88 * scale, 0.100), mats["cloth_moss"], (0.0, -0.30, 0.0), 0.020, True)
            add_cube(coll, "high_complex_canopy_right_slab", (0.68 * scale, 0.0, z), (1.12 * scale, 1.88 * scale, 0.100), mats["cloth_shadow"], (0.0, 0.30, 0.0), 0.020, True)
            add_cube(coll, "premium_canopy_crown", (0.0, 0.0, z + 0.33), (0.20, 2.02 * scale, 0.10), mats["premium_wood"], (0, 0, 0), 0.018, True)
            for y in (-0.62 * scale, 0.0, 0.62 * scale):
                add_ellipsoid(coll, "super_cap_roof_tile", (0.0, y, z + 0.43), (0.20, 0.12, 0.050), mats["glow_soft"], subdivisions=2)
    if damaged:
        add_cube(coll, "collapsed_canopy_panel", (-0.20, 0.58, 0.34), (1.02, 0.20, 0.085), mats["cloth_shadow"], (0.34, 0.14, -0.34), 0.018, True)


def add_construction(coll, level, mats):
    add_round_wall(coll, level, mats, construction=True)
    add_mushroom_groups(coll, level, 1, mats)
    add_canopy(coll, level, mats, construction=True)
    for x, y, yaw in [(-0.48, 0.86, 0.32), (0.18, 0.92, -0.10), (0.70, 0.72, -0.34)]:
        add_cube(coll, "loose_wall_material", (x, y, 0.20), (0.54, 0.12, 0.11), mats["stone_block" if level >= 6 else "wood_fence"], (0.06, 0.14, yaw), 0.022, True)
    add_cube(coll, "open_substrate_bag", (0.82, -0.70, 0.20), (0.34, 0.26, 0.30), mats["bag"], (0.08, 0.0, 0.26), 0.050, True)
    add_ellipsoid(coll, "spilled_dark_substrate", (0.58, -0.70, 0.20), (0.28, 0.13, 0.025), mats["soil_shadow"], subdivisions=1)


def add_damage(coll, level, mats, *, ruined=False):
    add_round_wall(coll, level, mats, ruined=ruined, damaged=not ruined)
    add_mushroom_groups(coll, level, 1 if ruined else 2, mats, damaged=True, ruined=ruined)
    add_canopy(coll, level, mats, damaged=True)
    if level < 5:
        add_cube(coll, "collapsed_shadow_cloth", (-0.18, 0.52, 0.30), (0.92, 0.16, 0.08), mats["cloth_shadow"], (0.30, 0.12, -0.32), 0.018, True)
    add_cube(coll, "torn_substrate_bag", (-0.78, -0.62, 0.19), (0.34, 0.24, 0.30), mats["bag_dark"], (0.06, 0.0, -0.20), 0.045, True)
    add_ellipsoid(coll, "dry_dead_moss", (0.20, -0.10, 0.245), (0.74 if ruined else 0.54, 0.36, 0.025), mats["root_dark"], subdivisions=1, rot=(0, 0, 0.12))


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("mushroom_grove_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "mushroom_grove"
    coll["level"] = level
    coll["state"] = state
    add_ground(coll, mats)
    add_level_substrate(coll, level, mats)
    if state == "construction":
        add_construction(coll, level, mats)
    elif state == "damaged":
        add_damage(coll, level, mats)
    elif state == "ruined":
        add_damage(coll, level, mats, ruined=True)
    elif state.startswith("super_stage"):
        add_round_wall(coll, level, mats)
        add_level_props(coll, level, mats, super_crop=True)
        add_mushroom_groups(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        stage = 3 if state == "active" else int(state[-2:])
        add_round_wall(coll, level, mats)
        add_level_props(coll, level, mats)
        add_mushroom_groups(coll, level, stage, mats)
    scale_model_to_tile(coll)
    return coll


def asset_variants():
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    variants = []
    for level in LEVELS:
        for state in states:
            variants.append((f"mushroom_grove_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"mushroom_grove_l{level:02d}_{state}", level, state))
    return variants


def setup_camera(scene):
    data = bpy.data.cameras.new("mushroom_grove_isometric_camera")
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
    for lname, pos, energy, size in (("key", (-3, -5, 8), 950, 5), ("fill", (5, 1, 6), 560, 5)):
        light = bpy.data.lights.new("mushroom_grove_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("mushroom_grove_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.58, 0.68, 0.74, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.42
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"


def create_asset_scene(name: str, level: int, state: str, mats):
    scene = bpy.data.scenes.new("Real_City_Mushroom_Grove_Render_" + name)
    root = bpy.data.collections.new(name + "_root")
    scene.collection.children.link(root)
    coll = make_variant(name, level, state, mats, root)
    setup_camera(scene)
    return scene, coll


def clean_collection_meshes(coll):
    bpy.context.view_layer.update()
    for obj in coll.all_objects:
        if obj.type == "MESH":
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
        if scene.name.startswith("Real_City_Mushroom_Grove_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("mushroom_grove_"):
            for obj in list(coll.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(coll)


def png_alpha_bounds(path: Path) -> list[int] | None:
    image = bpy.data.images.load(blender_path(path), check_existing=False)
    try:
        width, height = image.size
        pixels = list(image.pixels)
        left = width
        top = height
        right = -1
        bottom = -1
        for y in range(height):
            row_offset = y * width * 4
            for x in range(width):
                if pixels[row_offset + x * 4 + 3] >= (8 / 255):
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x + 1)
                    bottom = max(bottom, y + 1)
        if right < 0:
            return None
        return [left, height - bottom, right, height - top]
    finally:
        bpy.data.images.remove(image)


def save_manifest(report_items):
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined", "super_stage01", "super_stage02", "super_stage03", "super_stage04", "super_stage05", "super_stage06"]
    manifest = {
        "asset_id": "mushroom_grove",
        "category": "fields",
        "display_name": "Грибница",
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
                "alpha_bounds": item["alpha_bounds"],
                "png_size": PNG_SIZE,
                "glb_bytes": item["glb_bytes"],
            }
            for item in report_items
        ],
    }
    report = {
        "asset": "mushroom_grove",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": LEVELS,
        "states": states,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "round mushroom grove, distinct from rectangular crop beds",
            "level upgrades: l02 low wooden border, l03 taller picket fence, l04 clay foundation, l05 stone lower course plus thin cloth canopy, l06 taller full-stone fence with premium beams, l07 higher posts and stone-block foundation, l08 brick/stone wall with sloped canopy, l09 thicker block fence with metal details, l10 metal posts, complex roof, super-mushroom cap parts and emerald dust inlays",
            "visibility revision: levels 5-10 use a wider mushroom bed; canopies cover the whole oval but sit higher and use translucent cloth so mushroom caps remain visible from the game camera; levels 7-10 use lower decorated walls; levels 6-8 add wall-colored gates and levels 9-10 add decorated metal doors",
            "resource visibility by ids: wood/premium_planks in boards, rails, beams and canopy ribs; clay/brick/stone/stone_blocks in wall courses and foundations; resin in amber brace blocks; fabric in cloth canopy panels and moss cloth; blue_salt in cold blue spore lamps; iron_ingot in metal studs, ridge and posts; emerald_dust in foundation inlays; super_mushrooms in glowing cap roof pieces",
            "construction/damaged/ruined keep the same ground tile and alter only fence sections, canopy, mushrooms and debris",
            "super stages add pale glowing central mushrooms, blue mycelium nodes and late super-cap roof accents",
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
        png_path = OUT_DIR / f"{name}.png"
        glb_path = OUT_DIR / f"{name}.glb"
        report_items.append({
            "name": name,
            "level": level,
            "state": state,
            "triangles": tris,
            "alpha_bounds": png_alpha_bounds(png_path),
            "glb_bytes": glb_path.stat().st_size if glb_path.exists() else 0,
        })
        lines.append(f"{name}: triangles={tris}")
    if last_scene and bpy.context.window:
        bpy.context.window.scene = last_scene
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    save_manifest(report_items)
    with open(blender_path(LOG_PATH), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write(f"\nMUSHROOM_GROVE_BLENDER_COMPLETE {len(report_items)}\n")
    print("MUSHROOM_GROVE_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
