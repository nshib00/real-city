"""Build Blender master/runtime assets for oilseed field levels 1-7."""
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
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/oilseed_field"
BLEND_PATH = OUT_DIR / "oilseed_field_l01_l07.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-oilseed-field-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.23
LEVELS = list(range(1, 8))

MATERIALS = {
    "grass": (0.27, 0.49, 0.08, 1),
    "grass_light": (0.39, 0.60, 0.13, 1),
    "soil_dry": (0.58, 0.38, 0.18, 1),
    "soil_warm": (0.46, 0.28, 0.13, 1),
    "soil_shadow": (0.25, 0.16, 0.08, 1),
    "plank": (0.72, 0.50, 0.26, 1),
    "premium_plank": (0.46, 0.27, 0.13, 1),
    "wood_dark": (0.30, 0.18, 0.09, 1),
    "stone": (0.58, 0.56, 0.48, 1),
    "iron": (0.55, 0.57, 0.52, 1),
    "fabric": (0.90, 0.67, 0.27, 1),
    "leaf": (0.33, 0.57, 0.16, 1),
    "leaf_dark": (0.20, 0.39, 0.13, 1),
    "seed_head": (0.93, 0.72, 0.18, 1),
    "seed_dark": (0.55, 0.34, 0.08, 1),
    "oil_drop": (0.95, 0.58, 0.08, 1),
    "gold": (1.00, 0.78, 0.22, 1),
    "mechanism": (0.62, 0.57, 0.46, 1),
    "damage": (0.24, 0.15, 0.08, 1),
    "super_seed": (1.00, 0.88, 0.28, 1),
}


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        return BLENDER_ROOT + "\\" + raw[len(root):].lstrip("\\")
    if str(path).startswith("/tmp/") or raw.lower().startswith("\\tmp\\"):
        return r"\\wsl.localhost\Debian" + raw
    return raw


def ensure_dir() -> None:
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)


def mat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new("MAT_oilseed_field_" + name)
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
        if name in {"gold", "super_seed", "oil_drop"} and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 0.12
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_oilseed_field_"):
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


def add_ellipsoid(coll, name, loc, scale, material, subdivisions=2, rot=(0, 0, 0)):
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
    return obj


def add_leaf(coll, name, center, length, width, material, yaw=0, pitch=0.50, roll=0):
    verts = [
        (0, 0, length * 0.52), (-width * 0.46, 0, length * 0.10), (-width * 0.24, 0, -length * 0.36),
        (0, 0, -length * 0.52), (width * 0.24, 0, -length * 0.36), (width * 0.46, 0, length * 0.10),
        (0, width * 0.05, length * 0.02),
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
    return obj


def octagon_points(width=2.24, depth=1.58):
    sx = width * 0.5
    sy = depth * 0.5
    cut_x = sx * 0.42
    cut_y = sy * 0.42
    return [
        (-cut_x, -sy), (cut_x, -sy), (sx, -cut_y), (sx, cut_y),
        (cut_x, sy), (-cut_x, sy), (-sx, cut_y), (-sx, -cut_y),
    ]


def add_ground(coll, mats):
    add_cube(coll, "oilseed_field_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.23, 0.92), (1.16, 1.02), (1.18, -1.00), (-1.14, -1.05)]):
        for j in range(3):
            beam_between(coll, "terrain_grass_tuft", (x + (j - 1) * 0.045, y, 0.008), (x + (j - 1) * 0.083, y + 0.033, 0.11 + 0.03 * (i % 2)), 0.025, mats["grass_light"], 6)
    add_ellipsoid(coll, "dry_octagonal_soil_mound", (0, 0, 0.090), (1.34, 0.93, 0.105), mats["soil_dry"], subdivisions=3)
    for y in (-0.34, -0.11, 0.12, 0.35):
        add_cube(coll, "warm_seed_furrow", (0.00, y, 0.205), (1.56, 0.052, 0.034), mats["soil_warm"], (0, 0, 0.025), 0.008, True)
        add_cube(coll, "dry_shadow_trench", (0.00, y + 0.060, 0.190), (1.34, 0.028, 0.024), mats["soil_shadow"], (0, 0, 0.025), 0.004, True)


def add_octagonal_wall(coll, level, mats, *, construction=False, damaged=False, ruined=False):
    height = 0.13 + level * 0.052
    radius = 0.034 + level * 0.003
    pts = octagon_points()
    skip = set()
    if construction:
        skip = {2, 3, 4}
    if damaged:
        skip = {0, 6}
    if ruined:
        skip = {0, 1, 2, 3, 4, 6}
    for idx, (x1, y1) in enumerate(pts):
        if idx in skip:
            continue
        x2, y2 = pts[(idx + 1) % len(pts)]
        if (idx + 1) % len(pts) in skip and not construction:
            continue
        z = 0.12 + height * 0.48
        mat_name = "premium_plank" if level >= 5 else "plank"
        beam_between(coll, "octagonal_seed_lower_rail", (x1, y1, z), (x2, y2, z), radius, mats[mat_name], 10)
        if level >= 2:
            beam_between(coll, "octagonal_seed_upper_rail", (x1, y1, z + height * 0.42), (x2, y2, z + height * 0.42), radius * 0.88, mats[mat_name], 10)
        if level >= 3 and idx % 2 == 0 and not ruined:
            mid = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, z + height * 0.58)
            add_cylinder(coll, "carved_seed_wall_disc", mid, 0.055, 0.026, mats["seed_head"], 12, rot=(math.pi / 2, 0, math.atan2(y2 - y1, x2 - x1)), bevel=0.004)
        if level >= 6 and not construction:
            beam_between(coll, "iron_seed_wall_band", (x1, y1, z + height * 0.68), (x2, y2, z + height * 0.68), radius * 0.38, mats["iron"], 7)
    for idx, (x, y) in enumerate(pts):
        if ruined and idx not in {5, 7}:
            continue
        if construction and idx in {2, 3, 4}:
            continue
        post_h = height + 0.20 + (0.06 if level >= 6 else 0)
        beam_between(coll, "thick_press_style_post", (x, y, 0.02), (x, y, post_h), radius * 0.82, mats["wood_dark" if level < 5 else "premium_plank"], 9)
        if level >= 2:
            for ring in range(1, 1 + min(3, level // 2)):
                add_cylinder(coll, "iron_post_ring", (x, y, 0.16 + ring * 0.12), radius * 1.06, 0.025, mats["iron"], 10, rot=(math.pi / 2, 0, 0), bevel=0.002)
        if level >= 5:
            add_cube(coll, "stone_octagon_corner_foot", (x, y, 0.08), (0.20, 0.16, 0.10), mats["stone"], (0, 0, idx * 0.18), 0.018, True)
    if damaged or ruined:
        for x, y, yaw in [(-0.68, -0.72, 0.34), (0.86, 0.48, -0.26), (0.08, 0.82, 0.10)]:
            add_cube(coll, "fallen_seed_wall_piece", (x, y, 0.17), (0.50, 0.10, 0.075), mats["wood_dark"], (0.14, 0.16, yaw), 0.014, True)


def add_seed_plant(coll, x, y, height, mats, *, damaged=False, super_crop=False, lean=0.0):
    stem_mat = mats["leaf_dark"] if damaged else mats["leaf"]
    top = (x + math.sin(lean) * 0.06, y + math.cos(lean) * 0.03, 0.24 + height)
    beam_between(coll, "oilseed_green_stem", (x, y, 0.22), top, 0.013 + height * 0.003, stem_mat, 7)
    if not damaged:
        add_leaf(coll, "broad_oilseed_leaf_a", (x + 0.025, y, 0.31 + height * 0.20), 0.18 + height * 0.10, 0.050, mats["leaf"], yaw=lean + 0.65, pitch=0.68)
        add_leaf(coll, "broad_oilseed_leaf_b", (x - 0.030, y, 0.29 + height * 0.18), 0.16 + height * 0.08, 0.046, mats["leaf_dark"], yaw=lean - 0.55, pitch=0.70)
    if height > 0.22:
        mat_name = "super_seed" if super_crop else "seed_head"
        head_scale = 1.25 if super_crop else 1.0
        add_ellipsoid(coll, "round_yellow_seed_head", (top[0], top[1], top[2] + 0.045), (0.070 * head_scale, 0.028 * head_scale, 0.070 * head_scale), mats[mat_name], subdivisions=2, rot=(0.20, 0.05, lean))
        add_ellipsoid(coll, "dark_seed_center", (top[0] + 0.006, top[1] - 0.010, top[2] + 0.047), (0.032 * head_scale, 0.012 * head_scale, 0.032 * head_scale), mats["seed_dark"], subdivisions=1)


def add_oilseed_cluster(coll, x, y, stage, level, mats, *, damaged=False, super_crop=False):
    count = max(2, min(8, stage + 2 + level // 3))
    for i in range(count):
        px = x + (i - count / 2) * 0.040
        py = y + math.sin(i * 1.45) * 0.035
        height = (0.13 + stage * 0.095 + level * 0.026) * (1.18 if super_crop else 1.0)
        if damaged and i > count // 2:
            height *= 0.38
        add_seed_plant(coll, px, py, height, mats, damaged=damaged, super_crop=super_crop and i == count // 2, lean=(i - count / 2) * 0.08)
    if stage >= 3 and not damaged:
        beam_between(coll, "soft_fabric_seed_tie", (x - 0.14, y, 0.38), (x + 0.14, y, 0.39), 0.014, mats["fabric"], 7)


def add_crops(coll, level, stage, mats, *, super_crop=False, damaged=False, ruined=False):
    positions = [(-0.54, -0.28), (-0.18, -0.08), (0.20, -0.30), (0.54, -0.02), (-0.42, 0.28), (0.02, 0.32), (0.42, 0.26)]
    visible = min(len(positions), 2 + stage + level // 2)
    if ruined:
        visible = 2
    for idx, (x, y) in enumerate(positions[:visible]):
        if damaged and idx % 3 == 1:
            add_cube(coll, "flattened_oilseed_patch", (x, y, 0.265), (0.36, 0.12, 0.042), mats["damage"], (0.05, 0.12, idx * 0.18), 0.010, True)
            continue
        add_oilseed_cluster(coll, x, y, stage, level, mats, damaged=damaged, super_crop=super_crop and idx == 2)
    if super_crop:
        add_oilseed_cluster(coll, 0.04, 0.02, min(6, stage + 1), level + 1, mats, super_crop=True)
        for x, y in [(-0.28, 0.16), (0.34, -0.16), (0.38, 0.20)]:
            add_ellipsoid(coll, "super_seed_glow_kernel", (x, y, 0.255), (0.035, 0.024, 0.022), mats["super_seed"], subdivisions=1)


def add_basket(coll, name, x, y, z, mats, scale=1.0, spilled=False):
    add_cylinder(coll, name + "_basket_body", (x, y, z + 0.07 * scale), 0.105 * scale, 0.14 * scale, mats["plank"], 12, rot=(0.03, 0.02, 0.0), bevel=0.006)
    add_cylinder(coll, name + "_basket_inner_seeds", (x, y, z + 0.155 * scale), 0.088 * scale, 0.028 * scale, mats["seed_head"], 12, bevel=0.002)
    beam_between(coll, name + "_basket_handle", (x - 0.08 * scale, y, z + 0.18 * scale), (x + 0.08 * scale, y, z + 0.18 * scale), 0.012 * scale, mats["wood_dark"], 7)
    if spilled:
        for i in range(7):
            add_ellipsoid(coll, name + "_spilled_seed", (x + 0.12 * scale + i * 0.025 * scale, y - 0.07 * scale + math.sin(i) * 0.025, z + 0.012), (0.018 * scale, 0.014 * scale, 0.010 * scale), mats["seed_head"], subdivisions=1)


def add_press_props(coll, level, mats, *, damaged=False):
    if level < 4:
        return
    base_x, base_y = 0.82, -0.36
    add_cube(coll, "mini_press_stone_base", (base_x, base_y, 0.17), (0.34, 0.24, 0.10), mats["stone"], (0, 0, -0.12), 0.018, True)
    beam_between(coll, "mini_press_screw_post", (base_x, base_y, 0.20), (base_x, base_y, 0.70 + level * 0.020), 0.030, mats["iron"], 10)
    add_cube(coll, "mini_press_crossbar", (base_x, base_y, 0.52 + level * 0.014), (0.42, 0.08, 0.07), mats["premium_plank"], (0, 0, -0.12), 0.014, True)
    lever_z = 0.58 + level * 0.012
    if damaged:
        add_cube(coll, "fallen_press_lever", (base_x + 0.08, base_y - 0.28, 0.20), (0.54, 0.055, 0.050), mats["wood_dark"], (0.0, 0.12, -0.62), 0.012, True)
    else:
        beam_between(coll, "small_press_lever", (base_x - 0.28, base_y, lever_z), (base_x + 0.24, base_y + 0.08, lever_z + 0.02), 0.024, mats["wood_dark"], 8)
    add_ellipsoid(coll, "warm_oil_drop_in_groove", (base_x - 0.18, base_y - 0.05, 0.235), (0.040, 0.022, 0.014), mats["oil_drop"], subdivisions=1)
    if level >= 6:
        add_cylinder(coll, "small_press_gear", (base_x + 0.18, base_y + 0.02, 0.47), 0.070, 0.030, mats["mechanism"], 12, rot=(math.pi / 2, 0, 0.2), bevel=0.003)


def add_level_props(coll, level, mats, *, super_crop=False, damaged=False):
    add_basket(coll, "front_seed_basket", -0.86, -0.62, 0.10, mats, 0.92, spilled=damaged)
    if level >= 2:
        add_cube(coll, "ochre_fabric_drying_strip", (-0.22, 0.72, 0.34), (0.58, 0.055, 0.10), mats["fabric"], (0, 0, 0.08), 0.006, True)
        add_basket(coll, "rear_seed_basket", 0.86, 0.58, 0.10, mats, 0.82)
    if level >= 3:
        for x, y, yaw in [(-0.58, 0.68, 0.12), (0.16, 0.78, -0.06)]:
            add_cube(coll, "low_drying_rail", (x, y, 0.44), (0.50, 0.060, 0.060), mats["plank"], (0, 0, yaw), 0.012, True)
            for off in (-0.16, 0.0, 0.16):
                add_ellipsoid(coll, "hanging_seed_head_disc", (x + off, y, 0.35), (0.050, 0.018, 0.050), mats["seed_head"], subdivisions=1)
    if level >= 4:
        add_press_props(coll, level, mats, damaged=damaged)
        add_cube(coll, "small_oil_runoff_groove", (0.52, -0.56, 0.22), (0.42, 0.050, 0.026), mats["oil_drop"], (0, 0, -0.18), 0.006, True)
    if level >= 5:
        add_basket(coll, "large_corner_seed_basket", -0.98, 0.34, 0.10, mats, 1.05)
        add_cube(coll, "gold_quality_tag", (-0.62, -0.80, 0.34), (0.10, 0.060, 0.080), mats["gold"], (0, 0, 0.18), 0.006, True)
    if level >= 6:
        for x, y, yaw in [(-0.80, -0.44, 0.20), (0.74, 0.40, -0.18)]:
            add_cube(coll, "iron_octagon_bracket", (x, y, 0.44), (0.19, 0.036, 0.055), mats["iron"], (0, 0, yaw), 0.006, True)
        add_cylinder(coll, "gold_measure_cup", (0.42, 0.72, 0.25), 0.055, 0.080, mats["gold"], 12, bevel=0.004)
    if level >= 7:
        add_cube(coll, "protected_super_seed_case", (0.08, -0.84, 0.29), (0.46, 0.22, 0.14), mats["premium_plank"], (0, 0, 0.06), 0.018, True)
        add_ellipsoid(coll, "case_super_seed_sample", (0.08, -0.84, 0.39), (0.085, 0.050, 0.035), mats["super_seed"], subdivisions=1)
    if super_crop:
        add_cube(coll, "super_oilseed_sample_tray", (-0.16, -0.82, 0.29), (0.46, 0.20, 0.10), mats["premium_plank"], (0, 0, 0.06), 0.016, True)
        add_ellipsoid(coll, "super_sample_kernel", (-0.16, -0.82, 0.37), (0.075, 0.045, 0.034), mats["super_seed"], subdivisions=1)
    if damaged:
        add_cube(coll, "broken_drying_rail_piece", (-0.38, 0.78, 0.18), (0.55, 0.060, 0.055), mats["wood_dark"], (0.10, 0.18, -0.30), 0.012, True)
        add_ellipsoid(coll, "dark_trampled_seed_soil", (0.22, -0.20, 0.24), (0.55, 0.24, 0.030), mats["damage"], subdivisions=1, rot=(0, 0, 0.20))


def add_construction(coll, level, mats):
    add_octagonal_wall(coll, level, mats, construction=True)
    add_crops(coll, level, 1, mats)
    for x, y, yaw in [(-0.58, 0.86, 0.28), (0.10, 0.92, -0.10), (0.62, 0.76, -0.34)]:
        add_cube(coll, "loose_octagon_wall_plank", (x, y, 0.17), (0.52, 0.070, 0.060), mats["plank"], (0.06, 0.10, yaw), 0.014, True)
    add_basket(coll, "empty_construction_basket", 0.86, -0.72, 0.10, mats, 0.86)
    add_cube(coll, "folded_drying_fabric", (0.40, -0.78, 0.18), (0.38, 0.16, 0.045), mats["fabric"], (0.04, 0.03, 0.20), 0.010, True)
    beam_between(coll, "loose_iron_press_screw", (-0.62, 0.64, 0.25), (-0.10, 0.86, 0.27), 0.022, mats["iron"], 8)


def add_damage(coll, level, mats, *, ruined=False):
    add_octagonal_wall(coll, level, mats, damaged=not ruined, ruined=ruined)
    add_crops(coll, level, 1 if ruined else 2, mats, damaged=True, ruined=ruined)
    add_level_props(coll, min(level, 6), mats, damaged=True)
    add_ellipsoid(coll, "scattered_oilseed_soil_smear", (0.05, -0.03, 0.25), (0.78 if not ruined else 1.02, 0.40 if not ruined else 0.64, 0.040), mats["damage"], subdivisions=1, rot=(0, 0, 0.12))
    if ruined:
        for x, y, yaw in ((0.66, -0.92, 0.42), (-0.96, 0.80, -0.56), (0.28, 0.72, 0.18)):
            add_cube(coll, "ruined_dry_seed_stake", (x, y, 0.17), (0.54, 0.058, 0.058), mats["wood_dark"], (0.0, 0.0, yaw), 0.012, True)


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("oilseed_field_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "oilseed_field"
    coll["level"] = level
    coll["state"] = state
    add_ground(coll, mats)
    if state == "construction":
        add_construction(coll, level, mats)
    elif state == "damaged":
        add_damage(coll, level, mats)
    elif state == "ruined":
        add_damage(coll, level, mats, ruined=True)
    elif state.startswith("super_stage"):
        add_octagonal_wall(coll, level, mats)
        add_level_props(coll, level, mats, super_crop=True)
        add_crops(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        stage = 3 if state == "active" else int(state[-2:])
        add_octagonal_wall(coll, level, mats)
        add_level_props(coll, level, mats)
        add_crops(coll, level, stage, mats)
    scale_model_to_tile(coll)
    return coll


def asset_variants():
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    variants = []
    for level in LEVELS:
        for state in states:
            variants.append((f"oilseed_field_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"oilseed_field_l{level:02d}_{state}", level, state))
    return variants


def setup_camera(scene):
    data = bpy.data.cameras.new("oilseed_field_isometric_camera")
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
    for lname, pos, energy, size in (("key", (-3, -5, 8), 960, 5), ("fill", (5, 1, 6), 620, 5)):
        light = bpy.data.lights.new("oilseed_field_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("oilseed_field_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.64, 0.74, 0.88, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"


def create_asset_scene(name: str, level: int, state: str, mats):
    scene = bpy.data.scenes.new("Real_City_Oilseed_Field_Render_" + name)
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
        if scene.name.startswith("Real_City_Oilseed_Field_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("oilseed_field_"):
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
        "asset_id": "oilseed_field",
        "category": "fields",
        "display_name": "Масличное поле",
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
        "asset": "oilseed_field",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": LEVELS,
        "states": states,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "dry warm octagonal oilseed field, distinct from wet reed basin, dark mushroom grove, herb apothecary bed and straight flax rows",
            "level upgrades raise the octagonal rails and add press-style posts, iron rings, seed wall discs, baskets, drying rails, stone feet, hand press, gold quality tags and protected super-seed case",
            "construction/damaged/ruined keep the same terrain ground and change only wall/decor/crop geometry",
            "super stages add larger golden seed heads, super kernels and protected sample tray",
            "resource visibility by ids: seeds in round heads, baskets and wall seed discs; planks early rails and drying frames; premium_planks late rails, press frame and seed case; fabric drying strips and row ties; stone_block corner feet and press base; iron_ingot post rings, wall bands and screw post; mechanism hand press and gear; gold_ingot quality tags and measuring cup; super-seeds glowing super heads and sample case",
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
        handle.write(f"\nOILSEED_FIELD_BLENDER_COMPLETE {len(report_items)}\n")
    print(f"OILSEED_FIELD_BLENDER_COMPLETE {len(report_items)}")


if __name__ == "__main__":
    main()
