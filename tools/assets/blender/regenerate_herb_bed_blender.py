"""Build Blender master/runtime assets for herb bed levels 1-9.

This is the Blender/MCP production route for `herb_bed`: a rounded
apothecary crop bed with wicker walls, Y-posts, drying bundles and rare
flower/glass accents. It is intentionally distinct from seed/flax/reed beds.
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
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/herb_bed"
BLEND_PATH = OUT_DIR / "herb_bed_l01_l09.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-herb-bed-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.23
LEVELS = list(range(1, 10))

MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "soil": (0.45, 0.29, 0.15, 1),
    "soil_dark": (0.30, 0.20, 0.12, 1),
    "soil_light": (0.60, 0.40, 0.22, 1),
    "wicker": (0.56, 0.36, 0.18, 1),
    "wicker_dark": (0.36, 0.22, 0.11, 1),
    "plank": (0.76, 0.55, 0.31, 1),
    "premium_plank": (0.88, 0.67, 0.39, 1),
    "rope": (0.70, 0.54, 0.30, 1),
    "fabric_teal": (0.18, 0.58, 0.55, 1),
    "fabric_cream": (0.86, 0.78, 0.58, 1),
    "herb": (0.16, 0.50, 0.18, 1),
    "herb_light": (0.45, 0.78, 0.28, 1),
    "herb_dark": (0.08, 0.32, 0.13, 1),
    "dry_herb": (0.58, 0.54, 0.30, 1),
    "flower_white": (0.94, 0.90, 0.72, 1),
    "flower_lilac": (0.70, 0.52, 0.90, 1),
    "flower_red": (0.88, 0.28, 0.30, 1),
    "stone": (0.52, 0.55, 0.50, 1),
    "stone_light": (0.70, 0.72, 0.64, 1),
    "iron": (0.56, 0.61, 0.56, 1),
    "glass": (0.66, 0.90, 0.88, 0.42),
    "blue_salt": (0.36, 0.76, 0.92, 1),
    "emerald": (0.24, 0.92, 0.54, 1),
    "tray": (0.68, 0.42, 0.20, 1),
    "clay": (0.62, 0.34, 0.20, 1),
    "damage": (0.22, 0.15, 0.10, 1),
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
    material = bpy.data.materials.new("MAT_herb_bed_" + name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.80
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = color[3]
        if name in {"blue_salt", "emerald"} and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = 0.18
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_herb_bed_"):
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


def add_leaf(coll, name, center, length, width, material, vein_material, yaw=0, pitch=0.60, roll=0, vein=True):
    verts = [
        (0, 0, length * 0.52), (-width * 0.50, 0, length * 0.10), (-width * 0.24, 0, -length * 0.30),
        (0, 0, -length * 0.48), (width * 0.24, 0, -length * 0.30), (width * 0.50, 0, length * 0.10),
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
        beam_between(coll, name + "_vein", root, tip, max(0.008, width * 0.045), vein_material, 6)
    return obj


def rounded_points(width=2.28, depth=1.62):
    return [
        (-width * 0.50, -depth * 0.18), (-width * 0.40, -depth * 0.45), (-width * 0.12, -depth * 0.54),
        (width * 0.18, -depth * 0.52), (width * 0.44, -depth * 0.36), (width * 0.52, -depth * 0.06),
        (width * 0.46, depth * 0.28), (width * 0.18, depth * 0.50), (-width * 0.18, depth * 0.50),
        (-width * 0.44, depth * 0.28), (-width * 0.52, depth * 0.02),
    ]


def add_ground(coll, mats):
    add_cube(coll, "herb_bed_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.25, 0.90), (1.18, 1.08), (1.22, -1.00), (-1.16, -1.10)]):
        for j in range(3):
            beam_between(coll, "terrain_grass_tuft", (x + (j - 1) * 0.045, y, 0.008), (x + (j - 1) * 0.085, y + 0.035, 0.11 + 0.03 * (i % 2)), 0.025, mats["grass_light"], 6)
    add_ellipsoid(coll, "rounded_apothecary_soil", (0, 0, 0.095), (1.30, 0.96, 0.110), mats["soil"], subdivisions=3)
    for y in (-0.42, -0.14, 0.14, 0.42):
        add_cube(coll, "soft_herb_row", (-0.03, y, 0.205), (1.62, 0.10, 0.070), mats["soil_light"], (0, 0, 0.03), 0.020, True)
        add_cube(coll, "dark_herb_furrow", (-0.03, y + 0.08, 0.238), (1.42, 0.035, 0.026), mats["soil_dark"], (0, 0, 0.03), 0.006, True)


def add_wicker_wall(coll, level, mats, *, construction=False, damaged=False, ruined=False):
    height = 0.16 + level * 0.040
    radius = 0.035 + min(level, 8) * 0.003
    points = rounded_points()
    skip = set()
    if construction:
        skip = {5, 6, 7}
    if damaged:
        skip = {1, 8}
    if ruined:
        skip = {0, 1, 5, 6, 7, 8}
    for idx, (x1, y1) in enumerate(points):
        if idx in skip:
            continue
        x2, y2 = points[(idx + 1) % len(points)]
        if (idx + 1) % len(points) in skip and not construction:
            continue
        z = 0.11 + height * 0.48
        mat_name = "wicker" if idx % 2 else "wicker_dark"
        beam_between(coll, "rounded_wicker_rail_low", (x1, y1, z), (x2, y2, z + 0.014 * math.sin(idx)), radius, mats[mat_name], 8)
        if level >= 2:
            beam_between(coll, "rounded_wicker_rail_high", (x1, y1, z + height * 0.45), (x2, y2, z + height * 0.45 + 0.012 * math.cos(idx)), radius * 0.88, mats["wicker"], 8)
        if level >= 5 and not ruined:
            mid = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, 0.075)
            add_cube(coll, "low_stone_sockle", mid, (0.24, 0.12, 0.12), mats["stone"], (0, 0, math.atan2(y2 - y1, x2 - x1)), 0.024, True)
    post_indexes = range(0, len(points), 2)
    for post_index, idx in enumerate(post_indexes):
        if ruined and post_index > 1:
            continue
        x, y = points[idx]
        post_h = height + 0.24 + (0.08 if level >= 7 else 0)
        beam_between(coll, "forked_y_post_stem", (x, y, 0.02), (x, y, post_h), radius * 0.95, mats["wicker_dark"], 8)
        if not construction:
            beam_between(coll, "forked_y_post_left", (x, y, post_h - 0.08), (x - 0.08, y + 0.05, post_h + 0.13), radius * 0.62, mats["wicker_dark"], 8)
            beam_between(coll, "forked_y_post_right", (x, y, post_h - 0.08), (x + 0.08, y + 0.05, post_h + 0.13), radius * 0.62, mats["wicker_dark"], 8)
            add_ellipsoid(coll, "rope_knot_on_y_post", (x, y + 0.025, post_h - 0.03), (0.045, 0.030, 0.032), mats["rope"], subdivisions=1)
    if level >= 4 and not construction:
        top_mat = mats["premium_plank"] if level >= 5 else mats["plank"]
        for idx in (0, 3, 6, 9):
            x1, y1 = points[idx]
            x2, y2 = points[(idx + 1) % len(points)]
            beam_between(coll, "carved_leaf_top_rail", (x1, y1, height + 0.22), (x2, y2, height + 0.22), 0.028, top_mat, 8)
            if level >= 6 and not damaged:
                mid = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, height + 0.25)
                add_leaf(coll, "tiny_leaf_ornament", mid, 0.16, 0.045, mats["herb_light"], mats["herb_dark"], yaw=math.atan2(y2 - y1, x2 - x1), pitch=0.10, vein=False)
    if damaged or ruined:
        for x, y, yaw in [(-0.76, -0.74, 0.45), (0.78, 0.62, -0.35), (0.10, -0.94, 0.12)]:
            add_cube(coll, "fallen_wicker_panel", (x, y, 0.18), (0.58, 0.10, 0.08), mats["wicker_dark"], (0.18, 0.28, yaw), 0.018, True)


def add_herb_clump(coll, x, y, scale, mats, *, stage=3, super_crop=False, damaged=False):
    stem_mat = mats["emerald"] if super_crop else (mats["herb_dark"] if damaged else mats["herb"])
    count = max(2, min(7, stage + 2))
    for i in range(count):
        yaw = i * math.tau / count + 0.18 * ((i % 2) - 0.5)
        length = (0.16 + stage * 0.060) * scale * (1.18 if super_crop else 1.0)
        width = (0.035 + stage * 0.010) * scale
        z = 0.30 + (0.012 * i) - (0.05 if damaged and i > count // 2 else 0)
        add_leaf(coll, "medicinal_leaf", (x, y, z), length, width, mats["herb_light"] if i % 2 else stem_mat, mats["herb_dark"], yaw=yaw, pitch=0.58, roll=0.08 * ((i % 3) - 1), vein=stage >= 2)
    if stage >= 3 and not damaged:
        flower_mat = mats["flower_lilac"] if super_crop else (mats["flower_white"] if (x + y) < 0 else mats["flower_red"])
        add_ellipsoid(coll, "small_herb_flower", (x, y, 0.34 + stage * 0.055 * scale), (0.045 * scale, 0.038 * scale, 0.025 * scale), flower_mat, subdivisions=1)


def add_herbs(coll, level, stage, mats, *, super_crop=False, damaged=False, ruined=False):
    positions = [(-0.64, -0.36), (-0.22, -0.14), (0.28, -0.34), (0.62, 0.02), (-0.48, 0.30), (0.08, 0.42), (0.48, 0.36)]
    visible = min(len(positions), 2 + stage + level // 2)
    if ruined:
        visible = 2
    for idx, (x, y) in enumerate(positions[:visible]):
        if damaged and idx % 3 == 1:
            add_ellipsoid(coll, "trampled_herb_patch", (x, y, 0.265), (0.16, 0.08, 0.025), mats["damage"], subdivisions=1, rot=(0, 0, idx * 0.2))
            continue
        add_herb_clump(coll, x, y, 0.75 + level * 0.035 + idx * 0.015, mats, stage=stage, super_crop=super_crop, damaged=damaged)
    if super_crop:
        add_herb_clump(coll, 0.02, 0.04, 1.46 + stage * 0.035, mats, stage=min(6, stage + 1), super_crop=True)
        for x, y in [(-0.30, 0.25), (0.34, -0.24), (0.40, 0.22)]:
            add_ellipsoid(coll, "emerald_dew_node", (x, y, 0.265), (0.040, 0.032, 0.018), mats["emerald"], subdivisions=1)


def add_label(coll, name, x, y, level, mats, rare=False):
    beam_between(coll, name + "_post", (x, y, 0.00), (x, y, 0.52), 0.020, mats["wicker_dark"], 6)
    add_cube(coll, name + "_blank_board", (x, y, 0.58), (0.07, 0.26, 0.13), mats["premium_plank" if level >= 5 else "plank"], (0, 0, 0.05), 0.014, True)
    add_cube(coll, name + "_leaf_mark", (x - 0.035, y, 0.60), (0.030, 0.10, 0.036), mats["emerald" if rare else "herb_light"], (0, 0, 0.05), 0.004, True)


def add_herb_bundle(coll, name, x, y, z, mats, scale=1.0, hanging=False):
    if hanging:
        beam_between(coll, name + "_tie", (x, y, z + 0.10 * scale), (x, y, z + 0.20 * scale), 0.014 * scale, mats["rope"], 6)
    for i in range(4):
        yaw = -0.35 + i * 0.22
        beam_between(coll, name + "_stem", (x, y, z), (x + 0.05 * math.sin(yaw), y + 0.02 * i, z + 0.22 * scale), 0.010 * scale, mats["dry_herb"], 5)
        add_leaf(coll, name + "_dry_leaf", (x + 0.02 * i, y + 0.01 * i, z + 0.11 * scale), 0.14 * scale, 0.030 * scale, mats["dry_herb"], mats["herb_dark"], yaw=yaw, pitch=0.72, vein=False)


def add_glass_cloche(coll, name, x, y, mats, scale=1.0):
    add_cylinder(coll, name + "_glass_dome", (x, y, 0.43 * scale), 0.13 * scale, 0.28 * scale, mats["glass"], vertices=14, bevel=0.006)
    add_ellipsoid(coll, name + "_glass_cap", (x, y, 0.58 * scale), (0.13 * scale, 0.13 * scale, 0.055 * scale), mats["glass"], subdivisions=2)
    add_cube(coll, name + "_stone_base", (x, y, 0.27), (0.34 * scale, 0.25 * scale, 0.055), mats["stone_light"], (0, 0, 0.12), 0.014, True)


def add_level_props(coll, level, mats, *, super_crop=False, damaged=False):
    add_label(coll, "front_apothecary_label", -1.04, -0.52, level, mats)
    add_cube(coll, "seed_tray", (0.92, -0.54, 0.28), (0.48, 0.28, 0.10), mats["tray"], (0, 0, -0.16), 0.022, True)
    add_cube(coll, "tray_seed_marks", (0.92, -0.54, 0.36), (0.36, 0.16, 0.030), mats["soil_light"], (0, 0, -0.16), 0.008, True)
    if level >= 2:
        add_cube(coll, "small_clay_jug", (-0.92, 0.58, 0.28), (0.22, 0.18, 0.28), mats["clay"], (0.04, 0.0, 0.24), 0.045, True)
        add_cube(coll, "teal_wall_ribbon", (0.0, -1.03, 0.35), (0.78, 0.040, 0.12), mats["fabric_teal"], (0, 0, 0.02), 0.008, True)
    if level >= 3:
        for x in (-0.72, 0.72):
            beam_between(coll, "drying_frame_post", (x, 0.58, 0.00), (x, 0.58, 0.86), 0.026, mats["wicker_dark"], 8)
        beam_between(coll, "drying_frame_crossbar", (-0.78, 0.58, 0.80), (0.78, 0.58, 0.80), 0.024, mats["wicker"], 8)
        for i, x in enumerate((-0.44, -0.12, 0.20, 0.50)):
            add_herb_bundle(coll, "hanging_dry_herb_bundle", x, 0.58, 0.51 - 0.02 * (i % 2), mats, 0.86, hanging=True)
        add_label(coll, "rear_rare_label", 1.02, 0.18, level, mats, rare=True)
    if level >= 4:
        for x, y in [(-1.08, -0.82), (1.08, 0.76), (-1.10, 0.14), (1.12, -0.04)]:
            add_cube(coll, "stone_corner_foot", (x, y, 0.09), (0.22, 0.16, 0.10), mats["stone_light"], (0, 0, 0.22), 0.024, True)
        add_cube(coll, "cream_wall_ribbon", (0.0, 1.02, 0.39), (0.66, 0.040, 0.11), mats["fabric_cream"], (0, 0, -0.02), 0.008, True)
    if level >= 5:
        add_cube(coll, "tiny_watering_can_body", (-0.72, -0.72, 0.24), (0.26, 0.18, 0.18), mats["iron"], (0, 0, 0.12), 0.028, True)
        beam_between(coll, "watering_can_spout", (-0.58, -0.72, 0.27), (-0.42, -0.70, 0.34), 0.018, mats["iron"], 7)
        for x, y in [(-0.24, -0.34), (0.54, 0.18)]:
            add_ellipsoid(coll, "blue_salt_marker", (x, y, 0.285), (0.035, 0.025, 0.020), mats["blue_salt"], subdivisions=1)
    if level >= 6:
        add_cube(coll, "apothecary_tag_shelf", (-0.82, 0.10, 0.50), (0.10, 0.58, 0.08), mats["premium_plank"], (0, 0, 0.02), 0.016, True)
        for y in (-0.12, 0.08, 0.28):
            add_cube(coll, "blank_hanging_tag", (-0.82, y, 0.59), (0.035, 0.12, 0.060), mats["fabric_cream"], (0, 0, -0.05), 0.006, True)
    if level >= 7:
        add_glass_cloche(coll, "rare_flower_cloche_a", -0.18, 0.08, mats, 0.86)
        add_herb_clump(coll, -0.18, 0.08, 0.62, mats, stage=4, super_crop=True)
    if level >= 8:
        add_glass_cloche(coll, "rare_flower_cloche_b", 0.42, -0.18, mats, 0.78)
        add_ellipsoid(coll, "emerald_powder_dish", (0.86, 0.38, 0.31), (0.12, 0.08, 0.026), mats["emerald"], subdivisions=1)
    if level >= 9:
        add_ellipsoid(coll, "central_rare_flower_bloom", (0.06, -0.02, 0.72), (0.12, 0.10, 0.055), mats["flower_lilac"], subdivisions=2)
        add_cube(coll, "protected_super_seed_box", (0.74, -0.16, 0.34), (0.44, 0.24, 0.16), mats["premium_plank"], (0, 0, -0.10), 0.022, True)
        add_ellipsoid(coll, "super_seed_glow", (0.74, -0.16, 0.45), (0.12, 0.06, 0.030), mats["emerald"], subdivisions=1)
    if super_crop:
        add_cube(coll, "super_herb_sample_tray", (0.04, -0.84, 0.31), (0.48, 0.24, 0.12), mats["premium_plank"], (0, 0, 0.05), 0.020, True)
    if damaged:
        add_cube(coll, "torn_herb_cloth", (0.50, -0.92, 0.25), (0.62, 0.08, 0.05), mats["fabric_teal"], (0.22, 0.18, 0.35), 0.008, True)


def add_construction(coll, level, mats):
    add_wicker_wall(coll, level, mats, construction=True)
    add_herbs(coll, level, 1, mats)
    for x, y, yaw in [(-0.54, 0.88, 0.32), (0.16, 0.94, -0.12), (0.70, 0.70, -0.36)]:
        add_cube(coll, "loose_wicker_rod", (x, y, 0.18), (0.52, 0.08, 0.07), mats["wicker"], (0.06, 0.12, yaw), 0.016, True)
    add_cube(coll, "folded_fabric_strip", (0.76, -0.76, 0.16), (0.48, 0.12, 0.07), mats["fabric_cream"], (0.04, 0.02, 0.24), 0.014, True)
    beam_between(coll, "loose_layout_rope", (-0.60, 0.66, 0.30), (-0.10, 0.88, 0.30), 0.020, mats["rope"], 8)


def add_damage(coll, level, mats, *, ruined=False):
    add_wicker_wall(coll, level, mats, damaged=not ruined, ruined=ruined)
    add_herbs(coll, level, 1 if ruined else 2, mats, damaged=True, ruined=ruined)
    add_level_props(coll, min(level, 5), mats, damaged=True)
    add_cube(coll, "trampled_apothecary_soil", (0.10, -0.02, 0.30), (1.06 if not ruined else 1.36, 0.54 if not ruined else 0.84, 0.05), mats["damage"], (0, 0, 0.18), 0.018, True)
    add_herb_bundle(coll, "fallen_dry_bundle", -0.72, -0.66, 0.18, mats, 0.94)
    if ruined:
        for x, y, yaw in ((0.66, -0.94, 0.42), (-1.00, 0.84, -0.58), (0.30, 0.74, 0.18)):
            add_cube(coll, "ruined_wicker_piece", (x, y, 0.17), (0.58, 0.08, 0.07), mats["wicker_dark"], (0.0, 0.0, yaw), 0.016, True)


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("herb_bed_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "herb_bed"
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
        add_wicker_wall(coll, level, mats)
        add_level_props(coll, level, mats, super_crop=True)
        add_herbs(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        stage = 3 if state == "active" else int(state[-2:])
        add_wicker_wall(coll, level, mats)
        add_level_props(coll, level, mats)
        add_herbs(coll, level, stage, mats)
    scale_model_to_tile(coll)
    return coll


def asset_variants():
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    variants = []
    for level in LEVELS:
        for state in states:
            variants.append((f"herb_bed_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"herb_bed_l{level:02d}_{state}", level, state))
    return variants


def setup_camera(scene):
    data = bpy.data.cameras.new("herb_bed_isometric_camera")
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
        light = bpy.data.lights.new("herb_bed_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("herb_bed_daylight")
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
    scene = bpy.data.scenes.new("Real_City_Herb_Bed_Render_" + name)
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
        if scene.name.startswith("Real_City_Herb_Bed_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("herb_bed_"):
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
        "asset_id": "herb_bed",
        "category": "fields",
        "display_name": "Травяная грядка",
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
        "asset": "herb_bed",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": LEVELS,
        "states": states,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "rounded wicker apothecary bed, distinct from rectangular seed/flax beds",
            "level upgrades raise the rounded wicker walls and add Y-posts, drying bundles, fabric strips, stone feet, iron brackets, glass cloches and rare flowers",
            "construction/damaged/ruined keep the same terrain ground and change only bed/decor/crop geometry",
            "super stages add emerald dew nodes, a taller central herb clump and protected sample tray",
            "resource visibility by ids: seeds in tray_seed_marks and protected_super_seed_box; planks early wicker walls; premium_planks carved top rails/tag shelf/super tray; fabric teal/cream strips; rope knots and hanging ties; windleaf leaf ornaments; stone_block sockles and glass-cloche bases; iron_ingot watering can/brackets; blue_salt markers; emerald_dust dew and powder dish",
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
        handle.write(f"\nHERB_BED_BLENDER_COMPLETE {len(report_items)}\n")
    print("HERB_BED_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
