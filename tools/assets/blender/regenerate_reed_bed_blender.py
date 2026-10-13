"""Build Blender master/runtime assets for reed bed levels 1-10.

This is the Blender/MCP production route for `reed_bed`: a cold wet,
boat-shaped reed basin with narrow clay walls, vertical reed bundles, water
grooves, measuring boards and drainage props. It is intentionally distinct
from sugar, herb, seed and flax beds.
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
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/reed_bed"
BLEND_PATH = OUT_DIR / "reed_bed_l01_l10.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-reed-bed-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.24
LEVELS = list(range(1, 11))

MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "wet_sand": (0.48, 0.38, 0.22, 1),
    "mud": (0.30, 0.23, 0.14, 1),
    "mud_dark": (0.20, 0.16, 0.10, 1),
    "water": (0.23, 0.64, 0.70, 0.58),
    "water_dark": (0.10, 0.38, 0.44, 0.72),
    "clay": (0.62, 0.36, 0.22, 1),
    "clay_dark": (0.42, 0.24, 0.16, 1),
    "plank": (0.70, 0.50, 0.28, 1),
    "premium_plank": (0.82, 0.62, 0.36, 1),
    "wood_dark": (0.31, 0.21, 0.12, 1),
    "reed": (0.39, 0.68, 0.24, 1),
    "reed_dark": (0.18, 0.42, 0.16, 1),
    "reed_light": (0.62, 0.78, 0.30, 1),
    "reed_head": (0.64, 0.47, 0.24, 1),
    "rope": (0.72, 0.56, 0.32, 1),
    "fabric_cold": (0.42, 0.78, 0.76, 1),
    "brick": (0.66, 0.31, 0.20, 1),
    "stone": (0.55, 0.58, 0.54, 1),
    "stone_light": (0.72, 0.74, 0.66, 1),
    "iron": (0.54, 0.59, 0.57, 1),
    "blue_salt": (0.35, 0.80, 0.94, 1),
    "light_crystal": (0.62, 0.74, 0.98, 1),
    "damage": (0.23, 0.16, 0.10, 1),
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
    material = bpy.data.materials.new("MAT_reed_bed_" + name)
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
        if name in {"blue_salt", "light_crystal"} and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 0.20
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_reed_bed_"):
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


def add_leaf(coll, name, center, length, width, material, yaw=0, pitch=0.58, roll=0):
    verts = [
        (0, 0, length * 0.54), (-width * 0.38, 0, length * 0.06), (-width * 0.18, 0, -length * 0.36),
        (0, 0, -length * 0.50), (width * 0.18, 0, -length * 0.36), (width * 0.38, 0, length * 0.06),
        (0, width * 0.045, length * 0.04),
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


def boat_points(width=2.42, depth=1.56):
    return [
        (-width * 0.50, 0.00),
        (-width * 0.38, -depth * 0.40),
        (-width * 0.06, -depth * 0.52),
        (width * 0.28, -depth * 0.42),
        (width * 0.50, 0.00),
        (width * 0.28, depth * 0.42),
        (-width * 0.06, depth * 0.52),
        (-width * 0.38, depth * 0.40),
    ]


def add_ground(coll, mats):
    add_cube(coll, "reed_bed_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.24, 0.90), (1.18, 1.02), (1.18, -1.02), (-1.16, -1.08)]):
        for j in range(3):
            beam_between(coll, "terrain_grass_tuft", (x + (j - 1) * 0.045, y, 0.008), (x + (j - 1) * 0.085, y + 0.035, 0.11 + 0.03 * (i % 2)), 0.025, mats["grass_light"], 6)
    add_ellipsoid(coll, "wet_boat_basin_mud", (0, 0, 0.095), (1.36, 0.86, 0.105), mats["wet_sand"], subdivisions=3)
    for y in (-0.34, 0.0, 0.34):
        add_cube(coll, "cold_water_groove", (0.00, y, 0.212), (1.58, 0.095, 0.032), mats["water"], (0, 0, 0.03), 0.012, True)
        add_cube(coll, "dark_wet_furrow", (0.00, y + 0.07, 0.190), (1.36, 0.035, 0.025), mats["mud_dark"], (0, 0, 0.03), 0.006, True)


def add_basin_wall(coll, level, mats, *, construction=False, damaged=False, ruined=False):
    height = 0.15 + level * 0.044
    rail_radius = 0.032 + min(level, 8) * 0.003
    points = boat_points()
    skip = set()
    if construction:
        skip = {3, 4, 5}
    if damaged:
        skip = {1, 6}
    if ruined:
        skip = {1, 2, 3, 4, 5, 6}
    for idx, (x1, y1) in enumerate(points):
        if idx in skip:
            continue
        x2, y2 = points[(idx + 1) % len(points)]
        if (idx + 1) % len(points) in skip and not construction:
            continue
        yaw = math.atan2(y2 - y1, x2 - x1)
        mat_name = "clay_dark" if idx % 2 else "clay"
        z = 0.10 + height * 0.50
        beam_between(coll, "boat_clay_lower_lip", (x1, y1, z), (x2, y2, z + 0.010 * math.sin(idx)), rail_radius, mats[mat_name], 9)
        if level >= 2:
            beam_between(coll, "boat_clay_upper_lip", (x1, y1, z + height * 0.42), (x2, y2, z + height * 0.42), rail_radius * 0.92, mats["clay"], 9)
        if level >= 4 and not ruined:
            add_cube(coll, "stone_bank_foot", ((x1 + x2) * 0.5, (y1 + y2) * 0.5, 0.080), (0.26, 0.11, 0.10), mats["stone"], (0, 0, yaw), 0.020, True)
        if level >= 7 and not construction and idx in {0, 2, 4, 6}:
            beam_between(coll, "iron_bank_band", (x1, y1, z + height * 0.62), (x2, y2, z + height * 0.62), rail_radius * 0.42, mats["iron"], 7)
    for idx, (x, y) in enumerate(points):
        if ruined and idx not in {0, 7}:
            continue
        if construction and idx in {3, 4, 5}:
            continue
        post_h = height + 0.20 + (0.07 if level >= 8 else 0)
        beam_between(coll, "ribbed_reed_side_post", (x, y, 0.02), (x, y, post_h), rail_radius * 0.78, mats["wood_dark" if level < 6 else "clay_dark"], 8)
        for notch in range(1, min(4, level // 2 + 1)):
            add_cube(coll, "water_measure_notch", (x, y, 0.16 + notch * 0.11), (0.105, 0.020, 0.018), mats["fabric_cold" if level >= 3 else "rope"], (0, 0, idx * 0.18), 0.003, True)
    if level >= 3 and not construction:
        add_cube(coll, "small_plank_bridge", (-0.10, -0.66, 0.34 + level * 0.012), (0.96, 0.14, 0.075), mats["premium_plank" if level >= 6 else "plank"], (0, 0, 0.08), 0.018, True)
    if level >= 4 and not construction:
        add_cube(coll, "corner_drain_spout", (1.18, -0.10, 0.20), (0.34, 0.10, 0.08), mats["clay_dark"], (0, 0, -0.18), 0.014, True)
        add_cube(coll, "spout_water_tip", (1.36, -0.12, 0.19), (0.13, 0.06, 0.028), mats["water"], (0, 0, -0.18), 0.006, True)
    if damaged or ruined:
        for x, y, yaw in [(-0.78, -0.70, 0.42), (0.86, 0.58, -0.30), (0.12, 0.84, 0.16)]:
            add_cube(coll, "fallen_clay_bank_piece", (x, y, 0.17), (0.54, 0.10, 0.08), mats["clay_dark"], (0.18, 0.20, yaw), 0.016, True)


def add_reed_stalk(coll, x, y, height, mats, *, damaged=False, super_crop=False, lean=0.0):
    stem_mat = mats["light_crystal"] if super_crop else (mats["reed_dark"] if damaged else mats["reed"])
    top = (x + math.sin(lean) * 0.10, y + math.cos(lean) * 0.04, 0.24 + height)
    beam_between(coll, "thin_reed_stalk", (x, y, 0.22), top, 0.014 + height * 0.004, stem_mat, 7)
    add_cylinder(coll, "reed_seed_head", (top[0] + 0.012, top[1], top[2] + 0.075), 0.030 + height * 0.006, 0.16, mats["reed_head"], 8, rot=(0.08, 0.04, lean), bevel=0.002)
    if not damaged:
        add_leaf(coll, "narrow_reed_leaf_a", (x + 0.03, y, 0.40 + height * 0.28), 0.24 + height * 0.12, 0.030, mats["reed_light"], yaw=lean + 0.55, pitch=0.74)
        add_leaf(coll, "narrow_reed_leaf_b", (x - 0.03, y, 0.34 + height * 0.20), 0.20 + height * 0.10, 0.026, mats["reed_dark"], yaw=lean - 0.55, pitch=0.72)


def add_reed_cluster(coll, x, y, stage, level, mats, *, damaged=False, super_crop=False):
    count = max(2, min(8, stage + 2 + level // 4))
    for i in range(count):
        px = x + (i - count / 2) * 0.035
        py = y + math.sin(i * 1.7) * 0.030
        height = (0.22 + stage * 0.14 + level * 0.030) * (1.16 if super_crop else 1.0)
        if damaged and i > count // 2:
            height *= 0.42
        add_reed_stalk(coll, px, py, height, mats, damaged=damaged, super_crop=super_crop, lean=(i - count / 2) * 0.09)
    if stage >= 3 and not damaged:
        beam_between(coll, "wet_rope_bundle_tie", (x - 0.16, y, 0.44), (x + 0.16, y, 0.46), 0.018, mats["rope"], 7)


def add_reeds(coll, level, stage, mats, *, super_crop=False, damaged=False, ruined=False):
    positions = [(-0.58, -0.30), (-0.20, -0.08), (0.22, -0.32), (0.58, -0.02), (-0.44, 0.28), (0.02, 0.34), (0.46, 0.30)]
    visible = min(len(positions), 2 + stage + level // 2)
    if ruined:
        visible = 2
    for idx, (x, y) in enumerate(positions[:visible]):
        if damaged and idx % 3 == 1:
            add_cube(coll, "flattened_reed_patch", (x, y, 0.27), (0.42, 0.12, 0.045), mats["damage"], (0.05, 0.12, idx * 0.16), 0.010, True)
            continue
        add_reed_cluster(coll, x, y, stage, level, mats, damaged=damaged, super_crop=super_crop and idx == 2)
    if super_crop:
        add_reed_cluster(coll, 0.04, 0.02, min(6, stage + 1), level + 2, mats, super_crop=True)
        for x, y in [(-0.30, 0.18), (0.34, -0.18), (0.44, 0.18)]:
            add_ellipsoid(coll, "blue_salt_dew", (x, y, 0.265), (0.040, 0.030, 0.020), mats["blue_salt"], subdivisions=1)


def add_reed_bundle_prop(coll, name, x, y, z, mats, scale=1.0, broken=False):
    for i in range(6):
        yaw = -0.34 + i * 0.14
        beam_between(coll, name + "_cut_stalk", (x, y + i * 0.014, z), (x + 0.36 * scale, y + i * 0.014 + math.sin(yaw) * 0.04, z + 0.03 * (i % 2)), 0.012 * scale, mats["reed_head" if broken else "reed_dark"], 6)
    beam_between(coll, name + "_wet_tie", (x + 0.12 * scale, y - 0.03, z + 0.03), (x + 0.16 * scale, y + 0.10, z + 0.03), 0.014 * scale, mats["rope"], 6)


def add_level_props(coll, level, mats, *, super_crop=False, damaged=False):
    add_cube(coll, "front_water_measure_board", (-1.04, -0.42, 0.48), (0.08, 0.34, 0.52), mats["plank" if level < 6 else "premium_plank"], (0, 0, 0.04), 0.014, True)
    for z in (0.36, 0.48, 0.60):
        add_cube(coll, "measure_blue_tick", (-1.085, -0.42, z), (0.024, 0.20, 0.022), mats["fabric_cold"], (0, 0, 0.04), 0.002, True)
    add_reed_bundle_prop(coll, "cut_reed_bundle_front", 0.62, -0.72, 0.18, mats, 0.88)
    if level >= 2:
        for x, y in [(-1.00, 0.44), (1.02, 0.46)]:
            add_cube(coll, "brick_bank_patch", (x, y, 0.18), (0.20, 0.11, 0.12), mats["brick"], (0, 0, -0.15), 0.010, True)
    if level >= 3:
        add_cube(coll, "cold_fabric_level_flag", (-0.34, 0.72, 0.56), (0.08, 0.28, 0.14), mats["fabric_cold"], (0, 0, 0.12), 0.006, True)
        beam_between(coll, "drip_tube_left", (-0.76, 0.50, 0.34), (0.66, 0.48, 0.34), 0.012, mats["water_dark"], 7)
    if level >= 5:
        add_reed_bundle_prop(coll, "rear_cut_reed_bundle", -0.92, 0.62, 0.18, mats, 0.82)
        add_cube(coll, "secondary_water_channel", (0.00, 0.82, 0.19), (1.06, 0.055, 0.030), mats["water"], (0, 0, -0.04), 0.006, True)
    if level >= 6:
        for x, y in [(-0.16, -0.36), (0.44, 0.16)]:
            add_ellipsoid(coll, "blue_salt_water_marker", (x, y, 0.272), (0.035, 0.026, 0.018), mats["blue_salt"], subdivisions=1)
    if level >= 7:
        for x, y, yaw in [(-0.82, -0.58, 0.20), (0.86, 0.54, -0.18)]:
            add_cube(coll, "iron_wall_bracket", (x, y, 0.46), (0.20, 0.035, 0.06), mats["iron"], (0, 0, yaw), 0.006, True)
    if level >= 8:
        add_cylinder(coll, "thin_light_crystal_marker", (0.98, -0.32, 0.44), 0.035, 0.26, mats["light_crystal"], 6, rot=(0.18, 0.06, 0.22), bevel=0.004)
    if level >= 10:
        add_cube(coll, "protected_reed_sample_box", (0.76, -0.10, 0.34), (0.42, 0.22, 0.15), mats["premium_plank"], (0, 0, -0.08), 0.020, True)
        add_ellipsoid(coll, "sample_cold_glow", (0.76, -0.10, 0.44), (0.10, 0.055, 0.030), mats["light_crystal"], subdivisions=1)
    if super_crop:
        add_cube(coll, "super_reed_sample_tray", (-0.10, -0.84, 0.30), (0.50, 0.22, 0.11), mats["premium_plank"], (0, 0, 0.06), 0.018, True)
    if damaged:
        add_reed_bundle_prop(coll, "broken_reed_bundle", -0.52, -0.82, 0.16, mats, 0.94, broken=True)
        add_cube(coll, "washed_out_clay_smear", (0.28, -0.56, 0.205), (0.74, 0.14, 0.040), mats["damage"], (0, 0, 0.25), 0.010, True)


def add_construction(coll, level, mats):
    add_basin_wall(coll, level, mats, construction=True)
    add_reeds(coll, level, 1, mats)
    for x, y, yaw in [(-0.54, 0.86, 0.32), (0.16, 0.92, -0.12), (0.70, 0.72, -0.36)]:
        add_cube(coll, "loose_reed_wall_stake", (x, y, 0.18), (0.54, 0.070, 0.060), mats["wood_dark"], (0.06, 0.12, yaw), 0.014, True)
    add_cube(coll, "wet_clay_stack", (0.82, -0.76, 0.17), (0.42, 0.22, 0.10), mats["clay"], (0.03, 0.02, 0.24), 0.018, True)
    beam_between(coll, "loose_wet_rope", (-0.62, 0.66, 0.28), (-0.06, 0.88, 0.29), 0.020, mats["rope"], 8)


def add_damage(coll, level, mats, *, ruined=False):
    add_basin_wall(coll, level, mats, damaged=not ruined, ruined=ruined)
    add_reeds(coll, level, 1 if ruined else 2, mats, damaged=True, ruined=ruined)
    add_level_props(coll, min(level, 6), mats, damaged=True)
    add_cube(coll, "muddy_trampled_channel", (0.06, -0.02, 0.29), (1.14 if not ruined else 1.42, 0.50 if not ruined else 0.80, 0.05), mats["damage"], (0, 0, 0.16), 0.018, True)
    if ruined:
        for x, y, yaw in ((0.66, -0.94, 0.42), (-1.00, 0.84, -0.58), (0.30, 0.74, 0.18)):
            add_cube(coll, "ruined_dry_reed_stake", (x, y, 0.17), (0.56, 0.060, 0.060), mats["reed_head"], (0.0, 0.0, yaw), 0.012, True)


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("reed_bed_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "reed_bed"
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
        add_basin_wall(coll, level, mats)
        add_level_props(coll, level, mats, super_crop=True)
        add_reeds(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        stage = 3 if state == "active" else int(state[-2:])
        add_basin_wall(coll, level, mats)
        add_level_props(coll, level, mats)
        add_reeds(coll, level, stage, mats)
    scale_model_to_tile(coll)
    return coll


def asset_variants():
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    variants = []
    for level in LEVELS:
        for state in states:
            variants.append((f"reed_bed_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"reed_bed_l{level:02d}_{state}", level, state))
    return variants


def setup_camera(scene):
    data = bpy.data.cameras.new("reed_bed_isometric_camera")
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
        light = bpy.data.lights.new("reed_bed_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("reed_bed_daylight")
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
    scene = bpy.data.scenes.new("Real_City_Reed_Bed_Render_" + name)
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
        if scene.name.startswith("Real_City_Reed_Bed_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("reed_bed_"):
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
        "asset_id": "reed_bed",
        "category": "fields",
        "display_name": "Тростниковая грядка",
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
        "asset": "reed_bed",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": LEVELS,
        "states": states,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "boat-shaped wet clay reed basin, distinct from rectangular seed/flax beds and thick sugar cane bed",
            "level upgrades raise the narrow clay walls and add ribbed posts, water gauges, plank bridges, brick patches, stone feet, iron bands, blue salt and light-crystal markers",
            "construction/damaged/ruined keep the same terrain ground and change only basin/decor/crop geometry",
            "super stages add colder reed highlights, blue salt dew nodes and protected sample tray",
            "resource visibility by ids: wood legacy early stakes; planks and premium_planks bridges/rails; clay basin; rope ties; brick patches; fabric water marks; stone_block feet; iron_ingot bands; blue_salt dew; light_crystal water markers",
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
        handle.write(f"\nREED_BED_BLENDER_COMPLETE {len(report_items)}\n")
    print("REED_BED_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
