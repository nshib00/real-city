"""Build Blender master/runtime assets for seed garden levels 1-10.

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
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/seed_garden"
LEVELS = list(range(1, 11))
BLEND_PATH = OUT_DIR / "seed_garden_l01_l10.blend"
REVIEW_PATH = OUT_DIR / "seed_garden_l01_l10_review.png"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-seed-garden-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
MODEL_SCALE = 1.24

MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "earth": (0.46, 0.27, 0.15, 1),
    "earth_dark": (0.30, 0.18, 0.10, 1),
    "seed_soil": (0.50, 0.29, 0.13, 1),
    "seed_soil_light": (0.70, 0.44, 0.20, 1),
    "wood": (0.70, 0.45, 0.23, 1),
    "wood_dark": (0.42, 0.25, 0.12, 1),
    "wood_cut": (0.86, 0.63, 0.34, 1),
    "plank": (0.78, 0.55, 0.30, 1),
    "plank_light": (0.94, 0.70, 0.38, 1),
    "rope": (0.73, 0.58, 0.32, 1),
    "flax": (0.84, 0.78, 0.54, 1),
    "cloth_teal": (0.16, 0.55, 0.58, 1),
    "cloth_berry": (0.58, 0.20, 0.48, 1),
    "paint_red": (0.78, 0.22, 0.15, 1),
    "paint_blue": (0.16, 0.36, 0.82, 1),
    "paint_white": (0.92, 0.88, 0.66, 1),
    "sprout": (0.28, 0.68, 0.22, 1),
    "sprout_light": (0.62, 0.92, 0.34, 1),
    "leaf_deep": (0.08, 0.36, 0.14, 1),
    "leaf_vein": (0.74, 1.00, 0.52, 1),
    "seed_pod": (0.83, 0.67, 0.34, 1),
    "seed_pod_light": (0.96, 0.82, 0.45, 1),
    "seed_gold": (1.00, 0.80, 0.24, 1),
    "seed_super": (0.72, 1.00, 0.38, 1),
    "bag": (0.78, 0.66, 0.45, 1),
    "bag_dark": (0.48, 0.36, 0.20, 1),
    "tray": (0.72, 0.45, 0.20, 1),
    "tray_light": (0.92, 0.66, 0.35, 1),
    "stone": (0.54, 0.56, 0.50, 1),
    "stone_light": (0.72, 0.73, 0.64, 1),
    "brick_warm": (0.62, 0.31, 0.19, 1),
    "metal_worn": (0.56, 0.60, 0.55, 1),
    "brass": (0.92, 0.68, 0.26, 1),
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
    material = bpy.data.materials.new("MAT_seed_garden_" + name)
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
        if material.name.startswith("MAT_seed_garden_"):
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
    add_cube(coll, "seed_garden_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
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
    add_cube(coll, "warm_seed_plot", (0, 0, 0.075), (2.35, 1.78, 0.16), mats["seed_soil"], bevel=0.06, ground=True)
    add_cube(coll, "raised_seed_bed", (-0.06, -0.02, 0.18), (2.02, 1.40, 0.06), mats["seed_soil_light"], bevel=0.035, ground=True)
    for y in (-0.51, -0.17, 0.17, 0.51):
        add_cube(coll, "dark_seed_furrow", (-0.04, y, 0.25), (1.90, 0.055, 0.035), mats["earth_dark"], bevel=0.010, ground=True)
        add_cube(coll, "raised_seed_ridge", (-0.04, y + 0.08, 0.275), (1.72, 0.045, 0.030), mats["seed_soil_light"], bevel=0.012, ground=True)


def add_frame(coll, level, mats, incomplete=False, damaged=False, ruined=False):
    rail_mat = mats["wood"] if level == 1 else mats["plank"]
    cap_mat = mats["wood_cut"] if level == 1 else mats["plank_light"]
    h = 0.19 + level * 0.038
    board_w = 0.17 + min(level, 8) * 0.008
    segments = [
        ("front_board", (0, -1.00, h / 2), (2.72, board_w, h), 0.01),
        ("back_board", (0, 1.00, h / 2), (2.72, board_w, h), -0.01),
        ("left_board", (-1.32, 0, h / 2), (board_w, 2.04, h), -0.02),
        ("right_board", (1.32, 0, h / 2), (board_w, 2.04, h), 0.02),
    ]
    for name, loc, scale, yaw in segments:
        if incomplete and name == "back_board":
            add_cube(coll, name + "_unfinished_left", (-0.72, 1.00, h / 2), (0.82, board_w, h), rail_mat, (0, 0, yaw), 0.03, True)
            continue
        if ruined and name in {"front_board", "right_board"}:
            continue
        if damaged and name == "front_board":
            add_cube(coll, "snapped_front_board", (0.35, -1.04, h + 0.04), (0.92, 0.14, 0.13), mats["wood_dark"], (0.30, -0.04, 0.28), 0.02, True)
            continue
        add_cube(coll, name, loc, scale, rail_mat, (0, 0, yaw), 0.035, True)
    add_frame_decor(coll, level, mats, h, incomplete=incomplete, damaged=damaged, ruined=ruined)
    for x in (-0.74, 0.0, 0.74):
        if not incomplete:
            add_cube(coll, "front_cap_plank", (x, -1.12, h + 0.035), (0.56, 0.055, 0.055), cap_mat, bevel=0.018, ground=True)
        if not ruined:
            add_cube(coll, "back_cap_plank", (x, 1.12, h + 0.035), (0.56, 0.055, 0.055), cap_mat, bevel=0.018, ground=True)
    for x in (-1.28, 1.28):
        for y in (-0.96, 0.96):
            post_h = 0.46 + level * 0.09
            if ruined and (x, y) in {(1.28, -0.96), (1.28, 0.96)}:
                continue
            add_cube(coll, "grounded_corner_stake", (x, y, post_h / 2), (0.18, 0.18, post_h), mats["wood_dark"], (0, 0, 0.10), 0.035, True)
            if not damaged:
                add_cube(coll, "supported_stake_cap", (x, y, post_h + 0.035), (0.24, 0.24, 0.07), cap_mat, (0, 0, 0.18), 0.026, True)


def add_frame_decor(coll, level, mats, h, incomplete=False, damaged=False, ruined=False):
    if ruined:
        return
    if level >= 2 and not damaged:
        for x in (-0.88, -0.30, 0.30, 0.88):
            add_cube(coll, "front_seed_mark", (x, -1.105, h * 0.60), (0.16, 0.025, 0.055), mats["paint_white"], (0, 0, 0.02), 0.004, True)
            add_cube(coll, "back_seed_mark", (x, 1.105, h * 0.60), (0.16, 0.025, 0.055), mats["paint_blue"], (0, 0, -0.02), 0.004, True)
    if level >= 4:
        for x in (-0.56, 0.0, 0.56):
            add_cube(coll, "carved_front_panel", (x, -1.115, h * 0.48), (0.28, 0.035, 0.075), mats["paint_red" if x else "paint_blue"], (0, 0, 0.01), 0.006, True)
            if not incomplete:
                add_cube(coll, "carved_back_panel", (x, 1.115, h * 0.48), (0.28, 0.035, 0.075), mats["paint_white"], (0, 0, -0.01), 0.006, True)
    if level >= 5:
        for x, y in ((-1.34, -1.02), (1.34, -1.02), (-1.34, 1.02), (1.34, 1.02)):
            if ruined and x > 0:
                continue
            add_cube(coll, "stone_corner_pad", (x, y, 0.075), (0.32, 0.28, 0.15), mats["stone_light"], (0, 0, 0.16), 0.03, True)
    if level >= 6 and not incomplete:
        for y in (-1.145, 1.145):
            add_cube(coll, "double_top_rail", (0, y, h + 0.105), (2.30, 0.045, 0.045), mats["plank_light"], (0, 0, 0.0), 0.012, True)
    if level >= 7:
        band_mat = mats["metal_worn"] if level < 9 else mats["brass"]
        for x in (-1.35, 1.35):
            for y in (-0.52, 0.0, 0.52):
                add_cube(coll, "side_metal_band", (x, y, h * 0.66), (0.035, 0.18, 0.040), band_mat, (0, 0, 0.02), 0.006, True)
        for x in (-0.72, 0.0, 0.72):
            add_cube(coll, "front_metal_band", (x, -1.13, h * 0.78), (0.16, 0.035, 0.040), band_mat, (0, 0, 0.02), 0.006, True)
    if level >= 8:
        for x in (-0.96, -0.48, 0.0, 0.48, 0.96):
            add_cube(coll, "painted_seed_diamond", (x, -1.155, h + 0.005), (0.09, 0.032, 0.09), mats["seed_gold"], (0, 0, 0.78), 0.006, True)
    if level >= 10 and not damaged:
        for x in (-0.40, 0.40):
            add_cube(coll, "brass_nameplate", (x, -1.165, h * 0.46), (0.22, 0.040, 0.070), mats["brass"], (0, 0, 0.02), 0.008, True)


def add_level_props(coll, level, mats, rare=False):
    add_seed_bag(coll, "seed_bag_a", (-0.96, -0.66, 0.23), 1.0, mats)
    add_label(coll, "sort_label_a", -1.13, -0.28, level, mats, rare=False)
    if level >= 2:
        add_seed_bag(coll, "seed_bag_b", (1.02, 0.63, 0.22), 0.86, mats)
        add_cube(coll, "drying_tray", (0.88, -0.44, 0.33), (0.58, 0.32, 0.12), mats["tray"], (0, 0, -0.18), 0.025, True)
        add_cube(coll, "tray_seed_layer", (0.88, -0.44, 0.42), (0.48, 0.22, 0.035), mats["seed_pod"], (0, 0, -0.18), 0.010, True)
        for y in (-0.34, 0.34):
            beam_between(coll, "sorting_rope", (-1.00, y, 0.48), (1.00, y, 0.48), 0.025, mats["rope"], 8)
    if level >= 3:
        add_cube(coll, "large_sorting_table", (-0.84, 0.74, 0.31), (0.66, 0.40, 0.15), mats["plank"], (0, 0, 0.22), 0.025, True)
        add_cube(coll, "table_seed_layer", (-0.84, 0.74, 0.42), (0.50, 0.28, 0.035), mats["seed_pod_light"], (0, 0, 0.22), 0.010, True)
        for x in (-0.78, 0.78):
            beam_between(coll, "rare_row_post", (x, 0.00, 0.00), (x, 0.00, 1.00), 0.030, mats["wood_dark"], 8)
        beam_between(coll, "rare_row_rope", (-0.84, 0.00, 0.96), (0.84, 0.00, 0.96), 0.030, mats["rope"], 8)
        add_cube(coll, "aeolian_marker_flag", (1.42, -0.66, 0.72), (0.055, 0.38, 0.16), mats["cloth_teal"], (0.04, 0.0, -0.38), 0.016, True)
        add_label(coll, "rare_label", 1.14, 0.18, level, mats, rare=True)
        if rare:
            add_cube(coll, "protected_seed_box", (-0.02, -0.86, 0.35), (0.54, 0.26, 0.18), mats["tray"], (0, 0, 0.08), 0.025, True)
            add_cube(coll, "protected_seed_glow", (-0.02, -0.86, 0.48), (0.42, 0.14, 0.035), mats["seed_super"], (0, 0, 0.08), 0.010, True)
    if level >= 4:
        for i, x in enumerate((-0.34, 0.02, 0.38)):
            add_cube(coll, "painted_seed_jar", (x, 0.88, 0.34), (0.18, 0.16, 0.24), mats["tray_light"], (0, 0, 0.08 * i), 0.035, True)
            add_cube(coll, "jar_color_lid", (x, 0.88, 0.49), (0.14, 0.12, 0.055), mats[["paint_red", "paint_blue", "seed_gold"][i]], (0, 0, 0.08 * i), 0.015, True)
    if level >= 5:
        for x in (-1.02, 1.02):
            beam_between(coll, "raised_sort_post", (x, -0.58, 0.00), (x, -0.58, 0.82), 0.026, mats["wood_dark"], 8)
        beam_between(coll, "raised_sort_rope", (-1.06, -0.58, 0.78), (1.06, -0.58, 0.78), 0.024, mats["rope"], 8)
    if level >= 6:
        for i, (x, y) in enumerate(((-1.12, 0.48), (1.10, -0.18))):
            add_cube(coll, "woven_side_panel", (x, y, 0.48), (0.075, 0.38, 0.18), mats["cloth_berry" if i else "cloth_teal"], (0, 0, 0.02), 0.014, True)
            add_cube(coll, "woven_panel_thread", (x, y, 0.56), (0.085, 0.28, 0.030), mats["paint_white"], (0, 0, -0.16), 0.004, True)
    if level >= 7:
        add_cube(coll, "ledger_board", (-0.22, -0.92, 0.50), (0.48, 0.26, 0.07), mats["plank_light"], (0, 0, -0.10), 0.018, True)
        for x in (-0.32, -0.18, -0.04):
            add_cube(coll, "ledger_seed_dot", (x, -0.92, 0.56), (0.055, 0.040, 0.025), mats["seed_pod_light"], (0, 0, -0.10), 0.005, True)
    if level >= 8:
        add_cube(coll, "polished_sorting_table", (0.84, 0.26, 0.38), (0.54, 0.36, 0.16), mats["plank_light"], (0, 0, -0.20), 0.026, True)
        add_cube(coll, "sorted_seed_pattern", (0.84, 0.26, 0.49), (0.40, 0.20, 0.035), mats["seed_gold"], (0, 0, -0.20), 0.010, True)
    if level >= 9:
        add_cube(coll, "brass_seed_chest", (0.08, -0.72, 0.34), (0.58, 0.30, 0.22), mats["tray"], (0, 0, 0.05), 0.030, True)
        add_cube(coll, "brass_chest_band", (0.08, -0.72, 0.47), (0.62, 0.04, 0.05), mats["brass"], (0, 0, 0.05), 0.006, True)
    if level >= 10:
        for x in (-0.78, 0.78):
            beam_between(coll, "festival_post", (x, 0.54, 0.00), (x, 0.54, 1.12), 0.027, mats["wood_dark"], 8)
        beam_between(coll, "festival_rope", (-0.82, 0.54, 1.08), (0.82, 0.54, 1.08), 0.025, mats["rope"], 8)
        for i, x in enumerate((-0.46, 0.0, 0.46)):
            add_cube(coll, "small_seed_pennant", (x, 0.54, 1.02), (0.045, 0.22, 0.13), mats[["cloth_teal", "seed_gold", "cloth_berry"][i]], (0.05, 0, 0.14), 0.010, True)
    for i, (x, y) in enumerate([(-1.12, 0.84), (1.10, -0.82), (1.12, 0.14), (-1.10, -0.14)]):
        add_cube(coll, "field_edge_stone", (x, y, 0.10), (0.16 + 0.03 * (i % 2), 0.12, 0.08), mats["stone"], (0, 0, 0.25 * i), 0.025, True)


def add_seed_bag(coll, name, center, scale, mats, torn=False):
    mat_name = "bag_dark" if torn else "bag"
    add_cube(coll, name + "_body", center, (0.30 * scale, 0.24 * scale, 0.34 * scale), mats[mat_name], (0.08, 0.0, 0.25), 0.055, True)
    add_cube(coll, name + "_neck", (center[0], center[1], center[2] + 0.20 * scale), (0.18 * scale, 0.12 * scale, 0.10 * scale), mats["flax"], (0.08, 0.0, 0.30), 0.025, True)
    if torn:
        add_cube(coll, name + "_spilled_seeds", (center[0] + 0.20, center[1] - 0.08, 0.18), (0.38, 0.16, 0.035), mats["seed_pod"], (0, 0, -0.25), 0.012, True)


def add_label(coll, name, x, y, level, mats, rare=False):
    beam_between(coll, name + "_post", (x, y, 0.00), (x, y, 0.64), 0.025, mats["wood_dark"], 6)
    add_cube(coll, name + "_board", (x, y, 0.72), (0.08, 0.31, 0.16), mats["plank_light"], (0, 0, 0.06), 0.016, True)
    add_cube(coll, name + "_mark", (x - 0.04, y, 0.74), (0.034, 0.13 + level * 0.02, 0.045), mats["seed_super" if rare else "sprout_light"], (0, 0, 0.06), 0.006, True)


def add_plants(coll, level, stage, mats, super_crop=False, damaged=False):
    rows = [-0.50, -0.17, 0.17, 0.50] if not super_crop else [-0.42, 0.0, 0.42]
    for row_index, y in enumerate(rows):
        count = 4 + level + (1 if super_crop else 0)
        for index in range(count):
            if damaged and (index + row_index) % 4 == 0:
                continue
            x = -0.82 + index * (1.64 / max(1, count - 1))
            jitter = 0.025 * ((index + row_index) % 3 - 1)
            plant_stage = min(6, stage + 1) if super_crop else stage
            height = (0.13 + plant_stage * 0.12 + level * 0.035) * (1.35 if super_crop else 1.0)
            width = (0.040 + plant_stage * 0.012) * (1.45 if super_crop else 1.0)
            z0 = 0.27
            stem_mat = mats["seed_super"] if super_crop else mats["leaf_deep"]
            beam_between(coll, "seedling_stem", (x, y + jitter, z0), (x, y + jitter, z0 + height * 0.68), 0.014 + plant_stage * 0.003, stem_mat, 6)
            for side in (-1, 1):
                yaw = math.pi / 2 + side * (0.55 + 0.08 * ((index + row_index) % 2))
                add_leaf(
                    coll,
                    "seedling_leaf",
                    (x, y + jitter, z0 + height * 0.38),
                    height * 0.56,
                    width,
                    mats["seed_super"] if super_crop else (mats["sprout_light"] if plant_stage >= 3 else mats["sprout"]),
                    mats["leaf_vein"],
                    yaw,
                    0.62,
                    side * 0.08,
                    plant_stage >= 2,
                )
            if plant_stage >= 2:
                add_cube(coll, "seed_pod", (x, y + jitter, z0 + height * 0.82), (0.10, 0.075, 0.075), mats["seed_super"] if super_crop else mats["seed_pod"], (0, 0, 0.15 * ((index % 3) - 1)), 0.018, True)
            if plant_stage >= 3:
                pod_mat = mats["seed_gold"] if super_crop and stage >= 5 else mats["seed_pod_light"]
                add_cube(coll, "open_seed_pod", (x + 0.025, y + jitter, z0 + height * 0.97), (0.12, 0.035, 0.040), pod_mat, (0, 0, 0.25), 0.012, True)
    if super_crop and stage >= 3:
        support_h = 0.72 + stage * 0.12
        for x in (-0.78, 0.78):
            beam_between(coll, "super_support_post", (x, 0.0, 0.00), (x, 0.0, support_h), 0.028, mats["wood"], 8)
        beam_between(coll, "super_support_rope", (-0.82, 0.0, support_h), (0.82, 0.0, support_h), 0.026, mats["rope"], 8)


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
    add_cube(coll, "fallen_stake", (-0.86, 0.64, 0.23), (0.74, 0.11, 0.09), mats["wood_dark"], (0.05, 0.65, -0.70), 0.020, True)
    add_cube(coll, "trampled_seed_soil", (0.12, -0.02, 0.31), (1.02 if not ruined else 1.36, 0.58 if not ruined else 0.90, 0.05), mats["earth_dark"], (0, 0, 0.18), 0.020, True)
    if ruined:
        for x, y, yaw in ((0.64, -0.98, 0.42), (-1.02, 0.88, -0.58), (0.32, 0.76, 0.18)):
            add_cube(coll, "ruin_plank", (x, y, 0.18), (0.68, 0.10, 0.08), mats["wood_dark"], (0.0, 0.0, yaw), 0.018, True)


def scale_model_to_tile(coll):
    for obj in coll.objects:
        if obj.name.startswith("seed_garden_tile_base"):
            continue
        obj.location.x *= MODEL_SCALE
        obj.location.y *= MODEL_SCALE
        obj.scale.x *= MODEL_SCALE
        obj.scale.y *= MODEL_SCALE


def make_variant(name: str, level: int, state: str, mats, root_coll):
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "seed_garden"
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
            variants.append((f"seed_garden_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            variants.append((f"seed_garden_l{level:02d}_{state}", level, state))
    return variants


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(scene):
    data = bpy.data.cameras.new("seed_garden_isometric_camera")
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
        light = bpy.data.lights.new("seed_garden_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("seed_garden_daylight")
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
    scene = bpy.data.scenes.new("Real_City_Seed_Garden_Render_" + name)
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
        if scene.name.startswith("Real_City_Seed_Garden_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("seed_garden_") or coll.name.endswith("_root"):
            for obj in list(coll.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(coll)


def save_manifest(report_items):
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined", "super_stage01", "super_stage02", "super_stage03", "super_stage04", "super_stage05", "super_stage06"]
    manifest = {
        "asset_id": "seed_garden",
        "category": "fields",
        "display_name": "Семенной огород",
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
        "asset": "seed_garden",
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
            "level 1 uses wood stakes and windleaf-like green sort markers",
            "level 2 adds extra bags, drying tray and rope sorting layout",
            "level 3 adds rare seed row, rope supports, teal marker flag and super-seed container",
            "levels 4-10 progressively raise bed walls and add painted panels, stone pads, double rails, metal bands, seed diamonds, jars, fabric panels, ledgers, brass chest and festival pennants",
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
                alpha = pixels[row_offset + x * 4 + 3]
                if alpha >= (8 / 255):
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x + 1)
                    bottom = max(bottom, y + 1)
        if right < 0:
            return None
        # Blender image pixels are bottom-up; convert to PIL-style top-down bounds.
        return [left, height - bottom, right, height - top]
    finally:
        bpy.data.images.remove(image)


def make_review_sheet(report_items):
    # Blender's bundled Python may not include Pillow. The review sheet is
    # created by tools/assets/make_asset_contact_sheet.py after export.
    return


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
    make_review_sheet(report_items)
    with open(blender_path(LOG_PATH), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write(f"\nSEED_GARDEN_BLENDER_COMPLETE {len(report_items)}\n")
    print("SEED_GARDEN_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
