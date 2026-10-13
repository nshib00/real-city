"""Blender MCP: generate(), validate_roundtrip().

Builds the Real City coin storage upgrade chain in all gameplay states.
"""

import json
import math
import importlib.util
from datetime import date
from pathlib import Path

import bpy
from mathutils import Vector

from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "storage" / "coin_storage"
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ASSET_ID = "coin_storage"
DISPLAY_NAME = "Хранилище монет"
LEVELS = tuple(range(1, 13))
STATES = ("active", "construction", "damaged", "ruined")
SIZE = (512, 384)
ANCHOR = (256, 292)
FOOTPRINT = 3.6

MATS = {}


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        relative = raw[len(root) :].lstrip("\\")
        return BLENDER_ROOT + "\\" + relative
    return raw


def set_input(node, name, value):
    if node and name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color, roughness=0.74, metallic=0.0, alpha=1.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.new(f"MAT_{ASSET_ID}_{name}")
    material.diffuse_color = (color[0], color[1], color[2], alpha)
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    set_input(shader, "Base Color", (color[0], color[1], color[2], alpha))
    set_input(shader, "Roughness", roughness)
    set_input(shader, "Metallic", metallic)
    set_input(shader, "Alpha", alpha)
    if emission:
        set_input(shader, "Emission Color", emission)
        set_input(shader, "Emission Strength", emission_strength)
    if alpha < 1:
        material.blend_method = "BLEND"
        material.use_screen_refraction = False
    MATS[name] = material
    return material


def make_materials():
    MATS.clear()
    for name, color, roughness, metallic in (
        ("grass", (0.64, 0.82, 0.43), 0.86, 0.0),
        ("grass_light", (0.73, 0.90, 0.50), 0.88, 0.0),
        ("earth", (0.42, 0.30, 0.16), 0.9, 0.0),
        ("path", (0.72, 0.52, 0.31), 0.86, 0.0),
        ("wood", (0.62, 0.36, 0.16), 0.72, 0.0),
        ("wood_light", (0.88, 0.66, 0.38), 0.7, 0.0),
        ("wood_dark", (0.30, 0.16, 0.08), 0.76, 0.0),
        ("stone", (0.64, 0.64, 0.56), 0.82, 0.0),
        ("stone_light", (0.76, 0.74, 0.66), 0.8, 0.0),
        ("brick", (0.73, 0.32, 0.22), 0.78, 0.0),
        ("brick_light", (0.86, 0.45, 0.30), 0.78, 0.0),
        ("concrete", (0.68, 0.70, 0.66), 0.8, 0.0),
        ("metal", (0.48, 0.50, 0.48), 0.52, 0.16),
        ("metal_light", (0.72, 0.72, 0.66), 0.45, 0.12),
        ("dark_metal", (0.22, 0.24, 0.24), 0.52, 0.28),
        ("armor", (0.52, 0.56, 0.54), 0.5, 0.18),
        ("armor_dark", (0.34, 0.37, 0.36), 0.48, 0.32),
        ("gold", (0.95, 0.70, 0.22), 0.38, 0.35),
        ("gold_line", (1.0, 0.76, 0.20), 0.36, 0.45),
        ("cloth", (0.74, 0.56, 0.33), 0.9, 0.0),
        ("roof", (0.23, 0.66, 0.62), 0.72, 0.0),
        ("roof_green", (0.27, 0.58, 0.35), 0.74, 0.0),
        ("roof_brick", (0.66, 0.31, 0.22), 0.78, 0.0),
        ("roof_stone", (0.58, 0.60, 0.56), 0.82, 0.0),
        ("roof_coral", (0.84, 0.43, 0.31), 0.72, 0.0),
        ("damage", (0.24, 0.20, 0.16), 0.88, 0.0),
        ("crack_dark", (0.08, 0.07, 0.06), 0.9, 0.0),
        ("dust", (0.76, 0.67, 0.53), 0.94, 0.0),
        ("super_mechanism", (0.32, 0.36, 0.40), 0.42, 0.30),
    ):
        mat(name, color, roughness, metallic)
    mat("glass", (0.72, 0.92, 0.98), 0.28, 0.0, alpha=0.72, emission=(0.42, 0.70, 0.88, 1), emission_strength=0.12)
    mat("crystal", (0.64, 0.40, 0.94), 0.32, 0.0, alpha=0.9, emission=(0.48, 0.28, 0.86, 1), emission_strength=0.32)
    mat("window_warm", (1.0, 0.78, 0.36), 0.3, 0.0, emission=(1.0, 0.58, 0.20, 1), emission_strength=0.55)
    MATS["grass"]["terrain_source"] = "frontend/public/assets/terrain/tiles/grass.png"


def clear_scene():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(f"{ASSET_ID}_") or obj.name.startswith("coin_storage_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name.startswith(f"{ASSET_ID}_"):
            bpy.data.collections.remove(collection)
    for material in list(bpy.data.materials):
        if material.name.startswith(f"MAT_{ASSET_ID}_"):
            bpy.data.materials.remove(material)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.name.startswith(f"{ASSET_ID}_"):
            bpy.data.meshes.remove(mesh)
    for camera in list(bpy.data.cameras):
        if camera.users == 0 and camera.name.startswith(f"{ASSET_ID}_"):
            bpy.data.cameras.remove(camera)
    for light in list(bpy.data.lights):
        if light.users == 0 and light.name.startswith(f"{ASSET_ID}_"):
            bpy.data.lights.remove(light)


def link_to(collection, obj):
    for item in list(obj.users_collection):
        item.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def cube(collection, name, loc, scale, material, rot=(0, 0, 0), bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = f"{ASSET_ID}_{name}"
    obj.dimensions = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_bevel", "BEVEL")
        modifier.width = min(bevel, min(scale) * 0.22)
        modifier.segments = 1
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return link_to(collection, obj)


def shade_smooth(obj):
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def cylinder(collection, name, loc, radius, depth, material, vertices=16, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = f"{ASSET_ID}_{name}"
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return shade_smooth(link_to(collection, obj))


def sphere(collection, name, loc, scale, material, segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = f"{ASSET_ID}_{name}"
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return shade_smooth(link_to(collection, obj))


def prism_roof(collection, name, loc, size, material):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (0, -y, height), (0, y, height)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new(f"{ASSET_ID}_{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"{ASSET_ID}_{name}", mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    obj.modifiers.new("soft_bevel", "BEVEL").width = 0.035
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def hipped_roof(collection, name, loc, size, material, cap=0.34):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    top_x = max(0.24, x * cap)
    top_y = max(0.18, y * cap)
    verts = [
        (-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0),
        (-top_x, -top_y, height), (top_x, -top_y, height),
        (top_x, top_y, height), (-top_x, top_y, height),
    ]
    faces = [
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        (4, 5, 6, 7), (0, 3, 2, 1),
    ]
    mesh = bpy.data.meshes.new(f"{ASSET_ID}_{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"{ASSET_ID}_{name}", mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    obj.modifiers.new("soft_bevel", "BEVEL").width = 0.04
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def beam(collection, name, a, b, width, material):
    delta = Vector(b) - Vector(a)
    obj = cube(collection, name, (Vector(a) + Vector(b)) / 2, (width, width, delta.length), material, bevel=width * 0.18)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def add_base(collection):
    cube(collection, "tile_earth", (0, 0, -0.04), (FOOTPRINT, FOOTPRINT, 0.08), MATS["earth"], bevel=0.0)
    cube(collection, "tile_grass", (0, 0, 0.005), (FOOTPRINT * 0.99, FOOTPRINT * 0.99, 0.025), MATS["grass"], bevel=0.0)
    cube(collection, "front_path", (0, -1.05, 0.035), (1.35, 1.18, 0.04), MATS["path"], bevel=0.02)
    for i, (x, y) in enumerate(((-1.38, 1.12), (1.25, 1.15), (-1.27, -1.23), (1.35, -1.05))):
        for j, dx in enumerate((-0.04, 0.0, 0.045)):
            beam(collection, f"grass_tuft_{i}_{j}", (x + dx, y, 0.055), (x + dx * 1.4, y + 0.04, 0.16), 0.018, MATS["grass_light"])


def add_stone_courses(collection, name, width, depth, z, rows, material, damaged=False):
    block_h = 0.12
    for row in range(rows):
        count = 5 + row % 2
        y = -depth / 2 - 0.045
        for index in range(count):
            if damaged and (row + index) % 7 == 0:
                continue
            x = -width / 2 + (index + 0.5) * width / count
            cube(
                collection,
                f"{name}_front_block_{row:02d}_{index:02d}",
                (x, y, z + row * block_h),
                (width / count * 0.82, 0.08, block_h * 0.84),
                material,
                bevel=0.012,
            )
    for index in range(max(3, rows)):
        x = -width / 2 - 0.055
        y = -depth / 2 + (index + 0.5) * depth / max(3, rows)
        cube(collection, f"{name}_side_block_l_{index:02d}", (x, y, z + 0.12), (0.08, depth / max(3, rows) * 0.72, 0.16), material, bevel=0.012)
        cube(collection, f"{name}_side_block_r_{index:02d}", (-x, y, z + 0.12), (0.08, depth / max(3, rows) * 0.72, 0.16), material, bevel=0.012)


def add_window(collection, name, loc, size, mat_glass=None, damaged=False):
    mat_glass = mat_glass or (MATS["glass"] if not damaged else MATS["damage"])
    x, y, z = loc
    w, d, h = size
    cube(collection, f"{name}_frame", (x, y, z), (w + 0.09, d, h + 0.09), MATS["metal" if damaged else "wood_dark"], bevel=0.012)
    cube(collection, f"{name}_pane", (x, y - 0.01, z), (w, d * 0.62, h), mat_glass, bevel=0.01)
    cube(collection, f"{name}_cross_v", (x, y - 0.025, z), (0.035, d * 0.55, h + 0.03), MATS["metal_light"], bevel=0.006)
    cube(collection, f"{name}_cross_h", (x, y - 0.026, z), (w + 0.02, d * 0.55, 0.035), MATS["metal_light"], bevel=0.006)


def add_safe_cells(collection, level, width, depth, z, damaged=False):
    cols = 3 if level < 10 else 4
    rows = 2 if level < 11 else 3
    for row in range(rows):
        for col in range(cols):
            if damaged and (row + col) % 4 == 0:
                continue
            x = -0.36 + (col - (cols - 1) / 2) * 0.24
            cube(collection, f"safe_cell_{row}_{col}", (x, -depth / 2 - 0.082, z + row * 0.18), (0.17, 0.035, 0.12), MATS["metal_light" if not damaged else "damage"], bevel=0.012)
            cylinder(collection, f"safe_cell_knob_{row}_{col}", (x + 0.048, -depth / 2 - 0.112, z + row * 0.18), 0.015, 0.012, MATS["gold"], vertices=10, rot=(math.radians(90), 0, 0))


def add_wind_marker(collection, name, loc, scale=1.0, damaged=False):
    x, y, z = loc
    pole_mat = MATS["metal" if damaged else "metal_light"]
    cylinder(collection, f"{name}_pole", (x, y, z + 0.16 * scale), 0.018 * scale, 0.32 * scale, pole_mat, vertices=8)
    cube(collection, f"{name}_banner", (x + 0.08 * scale, y, z + 0.30 * scale), (0.18 * scale, 0.018 * scale, 0.08 * scale), MATS["roof_coral" if not damaged else "damage"], bevel=0.006)


def add_plank_course(collection, name, width, depth, z, height, count, damaged=False):
    mat_body = MATS["wood_dark"] if damaged else MATS["wood"]
    for index in range(count):
        x = -width / 2 + (index + 0.5) * width / count
        cube(collection, f"{name}_front_plank_{index:02d}", (x, -depth / 2 - 0.025, z), (width / count * 0.78, 0.055, height), mat_body, bevel=0.018)
    cube(collection, f"{name}_back_wall", (0, depth / 2 + 0.015, z), (width, 0.055, height), mat_body, bevel=0.018)


def add_bags(collection, level, damaged=False, ruined=False):
    color = MATS["dust"] if damaged else MATS["cloth"]
    positions = [(-0.75, -0.78), (0.72, -0.72), (-0.92, 0.38)]
    if level >= 2:
        positions += [(0.86, 0.28), (-0.35, -0.92)]
    if level >= 3:
        positions += [(0.38, 0.80)]
    for index, (x, y) in enumerate(positions):
        if ruined and index % 3 == 0:
            continue
        sphere(collection, f"money_bag_{index:02d}", (x, y, 0.16), (0.16, 0.13, 0.15), color, segments=12)
        cylinder(collection, f"bag_tie_{index:02d}", (x, y, 0.32), 0.035, 0.04, MATS["wood_dark"], vertices=8)


def add_coin_accent(collection, x, y, z, count=3, damaged=False):
    for index in range(count):
        cylinder(
            collection,
            f"coin_token_{x:.1f}_{y:.1f}_{index}",
            (x + index * 0.045, y - index * 0.018, z + index * 0.012),
            0.065,
            0.018,
            MATS["gold" if not damaged else "dust"],
            vertices=18,
            rot=(math.radians(90), 0, 0),
            scale=(1.0, 0.72, 1.0),
        )


def add_lock(collection, level, damaged=False):
    mat_lock = MATS["metal"] if damaged else MATS["metal_light"]
    cube(collection, "front_lock_plate", (0, -0.79, 0.62 + level * 0.04), (0.28, 0.06, 0.28), mat_lock, bevel=0.025)
    cylinder(collection, "lock_ring_left", (-0.09, -0.83, 0.81 + level * 0.04), 0.055, 0.025, mat_lock, vertices=12, rot=(math.radians(90), 0, 0))
    cylinder(collection, "lock_ring_right", (0.09, -0.83, 0.81 + level * 0.04), 0.055, 0.025, mat_lock, vertices=12, rot=(math.radians(90), 0, 0))


def add_level_one(collection, state):
    damaged = state in ("damaged", "ruined")
    ruined = state == "ruined"
    chest_z = 0.28
    cube(collection, "stone_corner_nw", (-0.76, 0.48, 0.09), (0.24, 0.24, 0.16), MATS["stone"], bevel=0.03)
    cube(collection, "stone_corner_ne", (0.76, 0.48, 0.09), (0.24, 0.24, 0.16), MATS["stone"], bevel=0.03)
    if state == "construction":
        add_plank_course(collection, "unfinished_chest", 1.35, 0.82, chest_z + 0.2, 0.38, 5)
        for x in (-0.82, 0.82):
            beam(collection, f"canopy_post_{x}", (x, -0.5, 0.06), (x, -0.5, 0.98), 0.07, MATS["wood"])
            beam(collection, f"canopy_rear_post_{x}", (x, 0.42, 0.06), (x, 0.42, 0.90), 0.065, MATS["wood"])
            beam(collection, f"scaffold_{x}", (x, -0.72, 0.82), (x * 0.72, 0.55, 1.08), 0.045, MATS["wood_light"])
        beam(collection, "canopy_rear_rail", (-0.92, 0.42, 0.88), (0.92, 0.42, 0.88), 0.045, MATS["wood_light"])
        add_bags(collection, 1)
        return
    chest_w = 1.22 if not ruined else 0.95
    cube(collection, "heavy_chest_body", (0, -0.08, chest_z + 0.24), (chest_w, 0.82, 0.48), MATS["wood_dark"] if damaged else MATS["wood"], bevel=0.055)
    prism_roof(collection, "curved_chest_lid", (0, -0.08, chest_z + 0.48), (chest_w + 0.12, 0.9, 0.34), MATS["wood"] if not damaged else MATS["damage"])
    for x in (-0.36, 0.36):
        cube(collection, f"gold_band_{x}", (x, -0.51, chest_z + 0.43), (0.09, 0.08, 0.55), MATS["gold"], bevel=0.012)
    add_lock(collection, 1, damaged)
    if not ruined:
        post_mat = MATS["wood_dark"] if damaged else MATS["wood"]
        beam(collection, "small_canopy_left", (-0.85, -0.55, 0.06), (-0.85, -0.55, 1.14), 0.07, post_mat)
        beam(collection, "small_canopy_right", (0.85, -0.55, 0.06), (0.85, -0.55, 1.14), 0.07, post_mat)
        beam(collection, "small_canopy_rear_left", (-0.85, 0.43, 0.06), (-0.85, 0.43, 1.04), 0.07, post_mat)
        beam(collection, "small_canopy_rear_right", (0.85, 0.43, 0.06), (0.85, 0.43, 1.04), 0.07, post_mat)
        beam(collection, "small_canopy_back_rail", (-0.94, 0.43, 0.96), (0.94, 0.43, 0.96), 0.045, MATS["wood_light" if not damaged else "wood_dark"])
        prism_roof(collection, "cloth_canopy", (0, -0.1, 1.05), (1.95, 1.2, 0.28), MATS["roof" if not damaged else "damage"])
        for x in (-0.52, 0.0, 0.52):
            beam(collection, f"canopy_front_trim_{x}", (x - 0.18, -0.70, 1.02), (x + 0.18, -0.70, 1.05), 0.035, MATS["wood_light"])
        if damaged:
            cube(collection, "torn_canopy_hole", (-0.28, -0.35, 1.10), (0.42, 0.26, 0.045), MATS["crack_dark"], rot=(0.08, 0.12, 0.18), bevel=0.0)
            beam(collection, "splintered_rear_post", (0.85, 0.43, 0.08), (0.72, 0.47, 0.62), 0.055, MATS["wood_dark"])
            cube(collection, "chest_side_crack", (-0.52, -0.52, 0.63), (0.045, 0.035, 0.34), MATS["crack_dark"], rot=(0, 0, -0.3), bevel=0.0)
    else:
        cube(collection, "broken_lid_slab", (0.42, -0.18, 0.54), (0.56, 0.38, 0.08), MATS["damage"], rot=(0.0, -0.1, 0.4), bevel=0.02)
        beam(collection, "fallen_front_post", (-0.88, -0.58, 0.09), (-0.25, -0.82, 0.18), 0.065, MATS["wood_dark"])
        beam(collection, "fallen_rear_post", (0.78, 0.38, 0.08), (0.25, 0.66, 0.16), 0.065, MATS["wood_dark"])
        cube(collection, "crushed_canopy_cloth", (-0.20, 0.28, 0.16), (0.82, 0.42, 0.055), MATS["damage"], rot=(0.02, 0.08, -0.26), bevel=0.018)
    add_bags(collection, 1, damaged, ruined)
    add_coin_accent(collection, -0.48, -0.67, 0.13, 2, damaged)


def add_level_two(collection, state):
    damaged = state in ("damaged", "ruined")
    ruined = state == "ruined"
    if state == "construction":
        cube(collection, "stone_footing", (0, 0, 0.12), (1.82, 1.28, 0.22), MATS["stone"], bevel=0.035)
        add_plank_course(collection, "half_storehouse", 1.64, 1.06, 0.45, 0.68, 7)
        for x in (-1.0, -0.35, 0.35, 1.0):
            beam(collection, f"wall_frame_{x}", (x, -0.66, 0.18), (x, -0.66, 1.1), 0.065, MATS["wood_light"])
        prism_roof(collection, "partial_roof", (-0.28, 0.0, 1.04), (1.25, 1.28, 0.34), MATS["roof"])
        add_bags(collection, 2)
        return
    width = 1.72 if not ruined else 1.38
    cube(collection, "stone_footing", (0, 0, 0.12), (width + 0.28, 1.35, 0.24), MATS["stone"], bevel=0.04)
    cube(collection, "wooden_vault_body", (0, 0, 0.55), (width, 1.04, 0.82), MATS["wood_dark"] if damaged else MATS["wood"], bevel=0.045)
    add_plank_course(collection, "vault_planks", width + 0.02, 1.04, 0.56, 0.72, 8, damaged)
    if not ruined:
        prism_roof(collection, "locked_store_roof", (0, 0, 0.98), (width + 0.28, 1.22, 0.38), MATS["roof"])
        cube(collection, "front_roof_lip", (0, -0.67, 1.02), (width + 0.42, 0.08, 0.09), MATS["wood_light"], bevel=0.018)
    else:
        prism_roof(collection, "collapsed_roof_piece", (-0.42, 0.12, 0.34), (0.85, 1.0, 0.18), MATS["damage"])
        cube(collection, "crushed_wall_opening", (0.30, -0.56, 0.54), (0.46, 0.05, 0.38), MATS["crack_dark"], rot=(0, 0, -0.2), bevel=0.0)
    cube(collection, "front_door", (0, -0.56, 0.48), (0.52, 0.07, 0.62), MATS["metal"] if damaged else MATS["wood_dark"], bevel=0.035)
    add_lock(collection, 2, damaged)
    for x in (-1.05, 1.05):
        cylinder(collection, f"guard_lantern_post_{x}", (x, -0.58, 0.42), 0.04, 0.74, MATS["wood_dark"], vertices=10)
        cube(collection, f"guard_lantern_{x}", (x, -0.58, 0.84), (0.18, 0.12, 0.18), MATS["window_warm"], bevel=0.02)
    cube(collection, "ledger_shelf", (-0.58, -0.60, 0.78), (0.26, 0.06, 0.16), MATS["wood_light"], bevel=0.014)
    add_bags(collection, 2, damaged, ruined)
    add_coin_accent(collection, 0.56, -0.72, 0.13, 3, damaged)
    if damaged:
        for index, (x, z) in enumerate(((-0.48, 0.75), (0.28, 0.54), (0.02, 1.02))):
            cube(collection, f"level2_wall_crack_{index}", (x, -0.595, z), (0.045, 0.03, 0.26), MATS["crack_dark"], rot=(0, 0, -0.4 + index * 0.35), bevel=0.0)
        cube(collection, "level2_roof_breach", (-0.34, -0.30, 1.04), (0.38, 0.22, 0.045), MATS["crack_dark"], rot=(0.03, 0.12, 0.24), bevel=0.0)


def add_level_three(collection, state):
    damaged = state in ("damaged", "ruined")
    ruined = state == "ruined"
    if state == "construction":
        cube(collection, "stone_plinth", (0, 0, 0.18), (2.08, 1.46, 0.34), MATS["stone"], bevel=0.04)
        add_plank_course(collection, "unfinished_board_walls", 1.84, 1.16, 0.67, 0.92, 8)
        for x in (-0.98, 0.98):
            beam(collection, f"iron_door_frame_{x}", (x * 0.38, -0.64, 0.22), (x * 0.38, -0.64, 1.16), 0.05, MATS["metal"])
        prism_roof(collection, "half_accounting_roof", (0.34, 0.0, 1.2), (1.32, 1.36, 0.36), MATS["roof"])
        cube(collection, "loose_counter_window", (-0.55, -0.67, 0.82), (0.38, 0.06, 0.28), MATS["window_warm"], bevel=0.02)
        add_bags(collection, 3)
        return
    width = 2.02 if not ruined else 1.62
    cube(collection, "raised_stone_plinth", (0, 0, 0.18), (width + 0.34, 1.52, 0.34), MATS["stone"], bevel=0.04)
    cube(collection, "boarded_treasury_body", (0, 0, 0.74), (width, 1.12, 1.04), MATS["wood_light"] if not damaged else MATS["wood_dark"], bevel=0.045)
    for x in (-0.86, 0.86):
        cube(collection, f"stone_side_pillar_{x}", (x, -0.01, 0.78), (0.22, 1.24, 1.12), MATS["stone_light"] if not damaged else MATS["stone"], bevel=0.035)
    cube(collection, "iron_safe_door", (0, -0.61, 0.68), (0.56, 0.075, 0.78), MATS["metal"] if not damaged else MATS["damage"], bevel=0.035)
    for x in (-0.24, 0.24):
        cube(collection, f"iron_door_band_{x}", (x, -0.665, 0.68), (0.06, 0.035, 0.84), MATS["metal_light"], bevel=0.01)
    cube(collection, "accounting_window", (-0.58, -0.63, 0.92), (0.34, 0.055, 0.28), MATS["window_warm"], bevel=0.02)
    if not ruined:
        prism_roof(collection, "compact_treasury_roof", (0, 0, 1.25), (width + 0.34, 1.34, 0.42), MATS["roof"])
        cylinder(collection, "small_weather_pin", (0.54, -0.1, 1.62), 0.035, 0.42, MATS["metal_light"], vertices=10)
        cube(collection, "gold_seal", (0.54, -0.59, 1.02), (0.22, 0.045, 0.22), MATS["gold"], bevel=0.03)
        add_window(collection, "accounting_window_detail", (-0.58, -0.665, 0.92), (0.28, 0.05, 0.22), damaged=damaged)
        add_wind_marker(collection, "tiny_wind_marker", (0.54, -0.1, 1.62), 0.55, damaged)
    else:
        prism_roof(collection, "fallen_roof_half", (-0.44, 0.1, 0.38), (1.05, 1.05, 0.2), MATS["damage"])
        cube(collection, "broken_safe_slab", (0.45, -0.52, 0.46), (0.42, 0.09, 0.42), MATS["metal"], rot=(0.05, -0.15, -0.35), bevel=0.02)
    add_bags(collection, 3, damaged, ruined)
    add_coin_accent(collection, 0.66, -0.78, 0.13, 4, damaged)
    if damaged:
        for x, z in ((-0.36, 0.86), (0.44, 0.52), (0.12, 1.1)):
            cube(collection, f"large_crack_{x}_{z}", (x, -0.68, z), (0.05, 0.03, 0.34), MATS["damage"], rot=(0, 0, 0.45), bevel=0.0)


def add_debris(collection, level, ruined=False):
    for index in range(4 + level):
        x = -0.9 + index * 0.32
        y = 0.75 + (index % 2) * 0.18
        cube(collection, f"debris_plank_{index:02d}", (x, y, 0.08), (0.34, 0.08, 0.08), MATS["wood_dark"], rot=(0, 0, index * 0.47), bevel=0.01)
    if ruined:
        for index in range(3 + level):
            cube(collection, f"fallen_stone_{index:02d}", (-0.74 + index * 0.35, -0.15 + (index % 2) * 0.22, 0.08), (0.18, 0.15, 0.12), MATS["stone"], rot=(0, 0, index * 0.35), bevel=0.02)


def level_wall_mat(level, damaged=False):
    if damaged:
        return MATS["damage"]
    if level <= 4:
        return MATS["stone_light"]
    if level <= 6:
        return MATS["brick"]
    if level <= 8:
        return MATS["metal_light"]
    return MATS["armor"]


def level_roof_mat(level, damaged=False):
    if damaged:
        return MATS["damage"]
    if level <= 2:
        return MATS["roof"]
    if level <= 5:
        return MATS["roof_green"]
    if level <= 6:
        return MATS["roof_brick"]
    if level <= 8:
        return MATS["roof_stone"]
    if level == 9:
        return MATS["concrete"]
    return MATS["armor_dark"]


def late_foundation_height(level, progress):
    height = 0.34 + min(progress, 5) * 0.035
    if level >= 8:
        height += 0.08
    if level >= 9:
        height += 0.08
    if level >= 10:
        height += 0.06
    if level >= 11:
        height += 0.04
    if level >= 12:
        height += 0.04
    return height


def late_foundation_material(level, damaged=False):
    if damaged:
        return MATS["damage"]
    if level <= 6:
        return MATS["stone"]
    return MATS["concrete"]


def add_late_foundation_reinforcement(collection, level, width, depth, foundation_h, damaged=False):
    if level < 8:
        return
    front_y = -depth / 2 - 0.19
    side_mat = MATS["damage"] if damaged else MATS["concrete"]
    steel_mat = MATS["damage"] if damaged else MATS["dark_metal"]
    gold_mat = MATS["dust"] if damaged else MATS["gold_line"]
    tiers = 1 if level == 8 else 2 if level == 9 else 3
    for index in range(tiers):
        z = 0.11 + index * max(0.11, foundation_h / (tiers + 1))
        cube(collection, f"reinforced_concrete_foundation_band_{index}", (0, front_y, z), (width + 0.58 + index * 0.08, 0.08, 0.09), side_mat, bevel=0.014)
    if level >= 10:
        cube(collection, "steel_foundation_front_guard", (0, front_y - 0.045, foundation_h * 0.60), (width + 0.74, 0.055, foundation_h * 0.42), steel_mat, bevel=0.016)
        for x in (-width * 0.42, 0, width * 0.42):
            cube(collection, f"steel_foundation_vertical_guard_{x:.1f}", (x, front_y - 0.082, foundation_h * 0.60), (0.08, 0.045, foundation_h * 0.48), steel_mat, bevel=0.01)
    if level >= 11:
        count = 3 if level == 11 else 5
        for index in range(count):
            x = -width / 2 + (index + 0.5) * width / count
            cube(collection, f"gold_foundation_inlay_{index}", (x, front_y - 0.112, foundation_h * 0.78), (width / count * 0.46, 0.030, 0.045), gold_mat, bevel=0.006)
    if level >= 12:
        cube(collection, "thin_gold_foundation_top_line", (0, front_y - 0.118, foundation_h + 0.015), (width + 0.38, 0.026, 0.032), gold_mat, bevel=0.004)


def add_battlements(collection, level, width, depth, z, damaged=False):
    material = MATS["stone"] if level < 8 and not damaged else MATS["dark_metal" if not damaged else "damage"]
    count = 4 if level < 7 else 5
    for index in range(count):
        x = -width / 2 + (index + 0.5) * width / count
        if damaged and index in (1, count - 2):
            continue
        cube(collection, f"front_battlement_{index:02d}", (x, -depth / 2 - 0.025, z), (0.22, 0.10, 0.24), material, bevel=0.018)
        cube(collection, f"back_battlement_{index:02d}", (x, depth / 2 + 0.025, z), (0.22, 0.10, 0.24), material, bevel=0.018)


def add_mechanism(collection, level, damaged=False):
    material = MATS["metal"] if damaged else MATS["metal_light"]
    cube(collection, "mechanical_counter_box", (0.58, -0.67, 1.16), (0.46, 0.08, 0.26), material, bevel=0.02)
    for index in range(3):
        cylinder(
            collection,
            f"counter_dial_{index:02d}",
            (0.44 + index * 0.14, -0.725, 1.17),
            0.045,
            0.018,
            MATS["gold" if not damaged else "dust"],
            vertices=14,
            rot=(math.radians(90), 0, 0),
        )
    if level >= 10:
        cylinder(collection, "large_combo_wheel", (-0.08, -0.735, 0.82), 0.14, 0.035, material, vertices=18, rot=(math.radians(90), 0, 0))


def add_crystal_indicator(collection, level, damaged=False):
    if level < 11 or damaged:
        return
    height = 0.34 if level == 11 else 0.46
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.11, radius2=0.04, depth=height, location=(0.0, -0.80, 1.64 + height / 2))
    obj = bpy.context.object
    obj.name = f"{ASSET_ID}_embedded_light_crystal"
    obj.rotation_euler = (0, 0, math.radians(30))
    obj.data.materials.append(MATS["crystal"])
    link_to(collection, obj)
    cube(collection, "crystal_socket", (0.0, -0.77, 1.67), (0.34, 0.08, 0.24), MATS["dark_metal"], bevel=0.018)


def add_metal_wall_skin(collection, level, width, depth, foundation_h, body_height, damaged=False):
    if level < 7:
        return
    front_y = -depth / 2 - 0.072
    skin_mat = MATS["damage"] if damaged else (MATS["armor_dark"] if level >= 9 else MATS["dark_metal"])
    panel_count = 4 if level < 10 else 5
    panel_w = width / panel_count * 0.72
    panel_h = body_height * (0.46 if level < 11 else 0.62)
    for index in range(panel_count):
        if damaged and index == 2:
            continue
        x = -width / 2 + (index + 0.5) * width / panel_count
        z = foundation_h + body_height * (0.48 if level < 11 else 0.54)
        cube(collection, f"front_metal_skin_{index:02d}", (x, front_y, z), (panel_w, 0.045, panel_h), skin_mat, bevel=0.012)
    for x in (-width / 2 - 0.095, width / 2 + 0.095):
        cube(collection, f"thick_dark_side_beam_{x:.1f}", (x, -0.02, foundation_h + body_height * 0.54), (0.16, depth + 0.18, body_height * 0.96), MATS["dark_metal" if not damaged else "damage"], bevel=0.025)
    if level >= 11:
        for index, x in enumerate((-0.72, -0.24, 0.24, 0.72)):
            cube(collection, f"wall_protection_plate_{index}", (x, front_y - 0.026, foundation_h + body_height * 0.72), (0.34, 0.04, 0.28), skin_mat, bevel=0.012)
            cone_z = foundation_h + body_height * 0.88
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.055 if level == 11 else 0.075, radius2=0.0, depth=0.18 if level == 11 else 0.25, location=(x, front_y - 0.07, cone_z), rotation=(math.radians(90), 0, 0))
            spike = bpy.context.object
            spike.name = f"{ASSET_ID}_front_wall_spike_{index}"
            spike.data.materials.append(MATS["dark_metal" if not damaged else "damage"])
            link_to(collection, spike)
    if level >= 12 and not damaged:
        for index, x in enumerate((-0.78, -0.39, 0.0, 0.39, 0.78)):
            cube(collection, f"gold_wall_line_{index}", (x, front_y - 0.052, foundation_h + body_height * 0.64), (0.035, 0.025, body_height * 0.48), MATS["gold_line"], bevel=0.006)


def add_roof_upgrade_details(collection, level, width, depth, roof_z, roof_height, damaged=False):
    if level < 3:
        return
    front_y = -depth / 2 - 0.13
    ridge_mat = MATS["damage"] if damaged else (MATS["dark_metal"] if level >= 6 else MATS["wood_light"])
    cube(collection, "roof_front_reinforced_lip", (0, front_y, roof_z + 0.09), (width + 0.48, 0.075, 0.10), ridge_mat, bevel=0.012)
    cube(collection, "roof_back_reinforced_lip", (0, depth / 2 + 0.13, roof_z + 0.09), (width + 0.42, 0.07, 0.09), ridge_mat, bevel=0.012)
    if level >= 6:
        for index, x in enumerate((-0.72, 0.0, 0.72)):
            cube(collection, f"brick_metal_roof_band_{index}", (x, front_y + 0.05, roof_z + 0.22), (0.12, depth + 0.22, 0.055), MATS["dark_metal" if not damaged else "damage"], rot=(0, 0, 0.0), bevel=0.008)
    if level >= 7:
        for index, x in enumerate((-0.84, -0.28, 0.28, 0.84)):
            z = roof_z + 0.22 + (index % 2) * 0.035
            cube(collection, f"stepped_roof_plate_{index}", (x, -0.05, z), (0.42, depth * 0.62, 0.075), MATS["armor_dark" if level >= 9 and not damaged else "metal_light" if not damaged else "damage"], rot=(0, 0, 0.05 if index % 2 else -0.05), bevel=0.012)
    if level >= 9:
        count = 3 if level == 9 else 5
        plate_mat = MATS["damage"] if damaged else MATS["armor_dark"]
        for index in range(count):
            x = -width / 2 + (index + 0.5) * width / count
            y_offset = -0.20 if level == 9 and index % 2 == 0 else 0.08
            cube(collection, f"protective_roof_plate_{index}", (x, y_offset, roof_z + roof_height * 0.62), (width / count * 0.72, depth * (0.42 if level == 9 else 0.70), 0.07), plate_mat, bevel=0.012)
    if level >= 10:
        for index, y in enumerate((-0.44, -0.12, 0.20, 0.52)):
            cube(collection, f"full_roof_scale_plate_{index}", (0, y, roof_z + roof_height * (0.72 + index * 0.012)), (width * 0.86, 0.18, 0.06), MATS["armor_dark" if not damaged else "damage"], bevel=0.01)
    if level >= 11:
        for index, x in enumerate((-0.86, -0.43, 0.0, 0.43, 0.86)):
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.05 if level == 11 else 0.07, radius2=0.0, depth=0.20 if level == 11 else 0.28, location=(x, front_y - 0.02, roof_z + roof_height * 0.86), rotation=(math.radians(90), 0, 0))
            spike = bpy.context.object
            spike.name = f"{ASSET_ID}_roof_spike_{index}"
            spike.data.materials.append(MATS["dark_metal" if not damaged else "damage"])
            link_to(collection, spike)
    if level >= 7:
        add_roof_pin_canopies(collection, level, width, depth, roof_z, roof_height, damaged)
    if level >= 10 and not damaged:
        gold_rows = {10: ((-0.16,), width * 0.34), 11: ((-0.26, 0.22), width * 0.48), 12: ((-0.34, 0.02, 0.38), width * 0.62)}
        rows, row_width = gold_rows[level]
        for index, y in enumerate(rows):
            cube(collection, f"gold_roof_inlay_{index}", (0, y, roof_z + roof_height * 0.91), (row_width, 0.035, 0.035), MATS["gold_line"], bevel=0.004)
    if level >= 12 and not damaged:
        for index, y in enumerate((-0.34, 0.02, 0.38)):
            cube(collection, f"gold_roof_side_cap_{index}", (-width * 0.34 + index * width * 0.34, front_y - 0.01, roof_z + roof_height * 0.74), (0.20, 0.035, 0.05), MATS["gold_line"], bevel=0.005)


def add_roof_pin_canopies(collection, level, width, depth, roof_z, roof_height, damaged=False):
    front_y = -depth / 2 - 0.22
    canopy_mat, pin_mat, plate_mat = roof_pin_canopy_materials(level, damaged)
    count = 3 if level <= 8 else 4 if level == 9 else 5
    for index in range(count):
        if damaged and index == count - 2:
            continue
        x = -width * 0.40 + index * (width * 0.80 / max(1, count - 1))
        pin_z = roof_z + roof_height * (0.78 + 0.02 * (index % 2))
        cylinder(collection, f"roof_canopy_pin_{index}", (x, front_y + 0.04, pin_z + 0.08), 0.022 if level < 11 else 0.027, 0.28 if level < 11 else 0.34, pin_mat, vertices=8)
        cube(collection, f"roof_pin_canopy_slab_{index}", (x, front_y - 0.02, pin_z + 0.26), (0.34 if level < 10 else 0.40, 0.24, 0.055), canopy_mat, rot=(0, 0, 0.10 if index % 2 else -0.10), bevel=0.010)
        if level >= 10:
            cube(collection, f"roof_pin_canopy_armor_cap_{index}", (x, front_y - 0.045, pin_z + 0.30), (0.30 if level == 10 else 0.36, 0.18, 0.035), plate_mat, rot=(0, 0, 0.10 if index % 2 else -0.10), bevel=0.008)
        if level >= 11 and not damaged:
            cube(collection, f"roof_pin_canopy_gold_edge_{index}", (x, front_y - 0.16, pin_z + 0.31), (0.24 if level == 11 else 0.32, 0.026, 0.026), MATS["gold_line"], bevel=0.004)


def roof_pin_canopy_materials(level, damaged=False):
    if damaged:
        return MATS["damage"], MATS["damage"], MATS["damage"]
    if level <= 8:
        return MATS["metal_light"], MATS["dark_metal"], MATS["metal_light"]
    if level == 9:
        return MATS["concrete"], MATS["dark_metal"], MATS["concrete"]
    return MATS["concrete"], MATS["dark_metal"], MATS["armor_dark"]


def add_unmounted_roof_pin_canopy_parts(collection, level, ruined=False):
    canopy_mat, pin_mat, plate_mat = roof_pin_canopy_materials(level, damaged=ruined)
    y = 0.88 if not ruined else 0.62
    z = 0.50 if not ruined else 0.16
    count = 2 if level <= 8 else 3
    for index in range(count):
        x = -0.42 + index * 0.42
        cube(collection, f"loose_roof_pin_canopy_slab_{index}", (x, y + 0.05 * (index % 2), z + 0.05 * index), (0.36 if level < 10 else 0.42, 0.24, 0.055), canopy_mat, rot=(0.03 * index, 0.02, -0.35 + index * 0.24), bevel=0.010)
        cylinder(collection, f"loose_roof_canopy_pin_{index}", (x - 0.08, y - 0.11, z + 0.09 + 0.03 * index), 0.022 if level < 11 else 0.027, 0.24 if level < 11 else 0.30, pin_mat, vertices=8, rot=(math.radians(82), 0.24, -0.20 + index * 0.18))
        if level >= 10:
            cube(collection, f"loose_roof_canopy_armor_cap_{index}", (x + 0.03, y - 0.02, z + 0.095 + 0.05 * index), (0.31 if level == 10 else 0.36, 0.18, 0.034), plate_mat, rot=(0.04, 0.01, -0.35 + index * 0.24), bevel=0.008)
        if level >= 11 and not ruined:
            cube(collection, f"loose_roof_canopy_gold_edge_{index}", (x + 0.04, y - 0.14, z + 0.12 + 0.05 * index), (0.24 if level == 11 else 0.32, 0.024, 0.024), MATS["gold_line"], rot=(0, 0, -0.35 + index * 0.24), bevel=0.004)


def add_super_mechanism(collection, level, depth, foundation_h, body_height, damaged=False):
    if level < 11:
        return
    material = MATS["damage"] if damaged else MATS["super_mechanism"]
    gold_mat = MATS["dust"] if damaged else MATS["gold_line"]
    front_y = -depth / 2 - 0.14
    z = foundation_h + body_height * 0.48
    cube(collection, "super_mechanism_case", (0.54, front_y, z), (0.42, 0.10, 0.52), material, bevel=0.02)
    cylinder(collection, "super_mechanism_main_gear", (0.54, front_y - 0.065, z + 0.08), 0.17 if level == 11 else 0.21, 0.035, gold_mat, vertices=18, rot=(math.radians(90), 0, 0))
    for index, offset in enumerate((-0.15, 0.15)):
        cylinder(collection, f"super_mechanism_side_gear_{index}", (0.54 + offset, front_y - 0.072, z - 0.16), 0.08, 0.03, material, vertices=14, rot=(math.radians(90), 0, 0))
    if level >= 12:
        cube(collection, "super_mechanism_gold_frame", (0.54, front_y - 0.075, z), (0.50, 0.035, 0.60), MATS["gold_line"] if not damaged else MATS["dust"], bevel=0.012)
        cube(collection, "super_mechanism_upper_module", (0.19, front_y - 0.012, z + 0.24), (0.28, 0.085, 0.24), material, bevel=0.018)
        cylinder(collection, "super_mechanism_upper_gear", (0.19, front_y - 0.066, z + 0.25), 0.10, 0.026, gold_mat, vertices=16, rot=(math.radians(90), 0, 0))
    elif not damaged:
        cube(collection, "super_mechanism_small_gold_tick", (0.54, front_y - 0.079, z + 0.28), (0.34, 0.026, 0.035), MATS["gold_line"], bevel=0.004)


def add_late_gold_wall_accents(collection, level, width, depth, foundation_h, body_height, damaged=False):
    if level < 10 or damaged:
        return
    front_y = -depth / 2 - 0.128
    if level == 10:
        positions = ((0.0, body_height * 0.84, 0.26),)
    elif level == 11:
        positions = ((-0.42, body_height * 0.72, 0.28), (0.42, body_height * 0.72, 0.28), (0.0, body_height * 0.92, 0.36))
    else:
        positions = ((-0.66, body_height * 0.68, 0.34), (-0.22, body_height * 0.78, 0.30), (0.22, body_height * 0.78, 0.30), (0.66, body_height * 0.68, 0.34), (0.0, body_height * 0.96, 0.44))
    for index, (x, z_offset, size) in enumerate(positions):
        cube(collection, f"progressive_gold_wall_plate_{index}", (x, front_y, foundation_h + z_offset), (size, 0.030, 0.045), MATS["gold_line"], bevel=0.005)
    if level >= 12:
        for x in (-width / 2 - 0.08, width / 2 + 0.08):
            cube(collection, f"gold_corner_pier_trim_{x:.1f}", (x, front_y + 0.12, foundation_h + body_height * 0.55), (0.040, 0.030, body_height * 0.58), MATS["gold_line"], bevel=0.004)


def add_cracks(collection, name, y, z_base, height, count, damaged=True):
    material = MATS["crack_dark"] if damaged else MATS["damage"]
    for index in range(count):
        x = -0.58 + index * (1.16 / max(1, count - 1))
        cube(collection, f"{name}_crack_{index:02d}", (x, y, z_base + height * (0.25 + 0.12 * (index % 4))), (0.04, 0.026, 0.28 + 0.04 * (index % 2)), material, rot=(0, 0, -0.45 + index * 0.27), bevel=0.0)


def add_late_damage(collection, level, width, depth, foundation_h, body_height, ruined=False):
    front_y = -depth / 2 - 0.108
    add_cracks(collection, "front_wall", front_y - 0.018, foundation_h, body_height, 5 if level >= 7 else 3)
    cube(collection, "front_wall_breach_dark", (0.38, front_y - 0.006, foundation_h + body_height * 0.58), (0.48, 0.04, 0.44), MATS["crack_dark"], rot=(0, 0, -0.18), bevel=0.0)
    roof_crack_z = foundation_h + body_height * (0.78 if ruined else 1.0) + 0.16
    cube(collection, "roof_crack_long", (-0.28, -depth / 2 - 0.01, roof_crack_z), (0.54, 0.04, 0.06), MATS["crack_dark"], rot=(0, 0, 0.28), bevel=0.0)
    cube(collection, "bent_door_corner", (-0.18, front_y - 0.02, foundation_h + body_height * 0.26), (0.34, 0.045, 0.24), MATS["metal"], rot=(0.08, 0.1, 0.34), bevel=0.012)
    for index, x in enumerate((-0.62, -0.30, 0.08, 0.48, 0.78)):
        mat_name = "brick" if level <= 6 else "metal" if level >= 7 else "stone"
        cube(collection, f"fallen_facade_chunk_{index}", (x, front_y - 0.30 - 0.04 * (index % 2), 0.10), (0.24, 0.15, 0.10), MATS[mat_name], rot=(0, 0, index * 0.37), bevel=0.018)
    if ruined:
        cube(collection, "low_collapsed_roof_slab_left", (-0.48, 0.05, 0.42), (0.82, 0.54, 0.10), MATS["damage"], rot=(0.02, -0.12, 0.34), bevel=0.018)
        cube(collection, "low_collapsed_roof_slab_right", (0.42, 0.28, 0.34), (0.70, 0.48, 0.10), MATS["metal"], rot=(-0.04, 0.10, -0.42), bevel=0.018)
        cube(collection, "upper_wall_torn_gap", (0.30, front_y - 0.02, foundation_h + body_height * 0.82), (0.72, 0.052, 0.42), MATS["crack_dark"], rot=(0, 0, -0.10), bevel=0.0)
        cube(collection, "torn_front_wall_lower", (-0.26, front_y - 0.02, foundation_h + body_height * 0.33), (0.56, 0.05, 0.36), MATS["damage"], rot=(0, 0, 0.18), bevel=0.0)
        for index, x in enumerate((-0.82, -0.42, 0.18, 0.64)):
            beam(collection, f"grounded_broken_beam_{index}", (x, 0.58, 0.08), (x + 0.36, 0.28, 0.18), 0.06 if level < 7 else 0.08, MATS["wood_dark" if level < 7 else "dark_metal"])


def add_late_level(collection, level, state):
    damaged = state in ("damaged", "ruined")
    ruined = state == "ruined"
    progress = level - 4
    width = 2.05 + min(progress, 5) * 0.06 + (0.05 if level >= 9 else 0.0)
    depth = 1.38 + min(progress, 5) * 0.035 + (0.04 if level >= 10 else 0.0)
    body_height = 1.02 + min(progress, 7) * 0.07
    if state == "construction":
        foundation_h = late_foundation_height(level, progress)
        cube(collection, "construction_foundation", (0, 0, foundation_h / 2), (width + 0.36, depth + 0.28, foundation_h), late_foundation_material(level), bevel=0.04)
        add_stone_courses(collection, "construction_foundation_courses", width + 0.28, depth + 0.18, 0.08, 2 + min(level // 3, 2) + (2 if level >= 9 else 0), MATS["stone_light" if level <= 6 else "concrete"])
        add_late_foundation_reinforcement(collection, level, width, depth, foundation_h)
        partial_h = body_height * 0.58
        cube(collection, "unfinished_back_wall", (0, 0.38, foundation_h + partial_h / 2), (width, 0.18, partial_h), level_wall_mat(level), bevel=0.03)
        cube(collection, "unfinished_left_wall", (-width / 2 + 0.08, 0, foundation_h + partial_h / 2), (0.16, depth, partial_h), level_wall_mat(level), bevel=0.03)
        if level >= 6:
            cube(collection, "unfinished_right_wall", (width / 2 - 0.08, 0.18, foundation_h + partial_h / 2), (0.16, depth * 0.62, partial_h * 0.88), level_wall_mat(level), bevel=0.03)
        for x in (-0.8, -0.25, 0.3, 0.85):
            beam(collection, f"scaffold_upright_{x}", (x, -0.78, 0.06), (x, -0.78, 1.38 + progress * 0.04), 0.055, MATS["wood_light"])
        beam(collection, "scaffold_front_rail_low", (-1.05, -0.82, 0.72), (1.05, -0.82, 0.9), 0.045, MATS["wood_light"])
        beam(collection, "scaffold_front_rail_high", (-1.0, -0.82, 1.12), (1.0, -0.82, 1.32), 0.045, MATS["wood_light"])
        if level >= 8:
            cube(collection, "loose_steel_beam", (0.24, 0.72, 0.38), (1.0, 0.08, 0.08), MATS["metal"], rot=(0, 0, 0.24), bevel=0.015)
            cylinder(collection, "loose_counter_wheel", (-0.48, 0.68, 0.22), 0.12, 0.05, MATS["metal_light"], vertices=16, rot=(math.radians(90), 0, 0))
            cube(collection, "stacked_concrete_foundation_slabs", (-0.72, 0.72, 0.30), (0.58, 0.32, 0.16), MATS["concrete"], bevel=0.018)
        if level >= 7:
            add_unmounted_roof_pin_canopy_parts(collection, level)
        if level >= 10:
            cube(collection, "unmounted_large_armor_roof_canopy", (0.54, 0.96, 0.70), (0.62, 0.30, 0.08), MATS["armor_dark"], rot=(0, 0, 0.18), bevel=0.012)
            add_coin_accent(collection, 0.98, 0.64, 0.19, 2 if level == 10 else 3)
        if level >= 11:
            cube(collection, "sealed_crystal_crate", (-0.82, 0.62, 0.16), (0.32, 0.28, 0.22), MATS["wood"], bevel=0.02)
            cube(collection, "wrapped_super_mechanism", (0.72, 0.62, 0.22), (0.50, 0.36, 0.28), MATS["super_mechanism"], bevel=0.02)
            cylinder(collection, "visible_super_mechanism_gear_in_crate", (0.72, 0.43, 0.25), 0.12 if level == 11 else 0.16, 0.035, MATS["gold_line"], vertices=18, rot=(math.radians(90), 0, 0))
        add_bags(collection, min(level, 6))
        return

    foundation_h = late_foundation_height(level, progress)
    cube(collection, "vault_foundation", (0, 0, foundation_h / 2), (width + 0.42, depth + 0.32, foundation_h), late_foundation_material(level, damaged), bevel=0.045)
    add_stone_courses(collection, "vault_foundation_courses", width + 0.30, depth + 0.18, 0.08, 2 + min(level // 3, 3) + (2 if level >= 9 else 0), MATS["stone_light" if level <= 6 else "concrete"], damaged)
    add_late_foundation_reinforcement(collection, level, width, depth, foundation_h, damaged)
    if ruined:
        cube(collection, "vault_body_lower_remnant", (0, 0, foundation_h + body_height * 0.34), (width, depth, body_height * 0.68), level_wall_mat(level, damaged), bevel=0.045)
        cube(collection, "vault_back_wall_broken_remnant", (-0.12, depth / 2 - 0.04, foundation_h + body_height * 0.78), (width * 0.76, 0.18, body_height * 0.34), level_wall_mat(level, damaged), rot=(0, 0, -0.04), bevel=0.035)
        cube(collection, "vault_left_wall_broken_remnant", (-width / 2 + 0.08, 0.10, foundation_h + body_height * 0.74), (0.18, depth * 0.68, body_height * 0.30), level_wall_mat(level, damaged), rot=(0, 0, 0.06), bevel=0.035)
        cube(collection, "vault_right_wall_broken_remnant", (width / 2 - 0.08, 0.18, foundation_h + body_height * 0.62), (0.18, depth * 0.54, body_height * 0.22), level_wall_mat(level, damaged), rot=(0, 0, -0.10), bevel=0.035)
    else:
        cube(collection, "vault_body", (0, 0, foundation_h + body_height / 2), (width, depth, body_height), level_wall_mat(level, damaged), bevel=0.045)
    if level in (5, 6) and not damaged:
        for index, x in enumerate((-0.62, 0.0, 0.62)):
            cube(collection, f"brick_front_panel_{index}", (x, -depth / 2 - 0.052, foundation_h + body_height * 0.54), (0.42, 0.045, body_height * 0.72), MATS["brick_light"], bevel=0.014)
    for x in (-width / 2 - 0.02, width / 2 + 0.02):
        cube(collection, f"corner_pier_{x}", (x, 0, foundation_h + body_height / 2), (0.22 if level < 7 else 0.30, depth + 0.12, body_height + 0.08), MATS["stone_light" if level <= 6 and not damaged else "dark_metal" if not damaged else "damage"], bevel=0.035)
        cube(collection, f"corner_pier_cap_{x}", (x, -depth / 2 - 0.02, foundation_h + body_height + 0.05), (0.30, 0.20, 0.14), MATS["stone_light" if level <= 7 and not damaged else "metal_light"], bevel=0.025)
    door_mat = MATS["metal"] if level < 9 and not damaged else MATS["armor"]
    if damaged:
        door_mat = MATS["damage"]
    cube(collection, "heavy_safe_door", (0, -depth / 2 - 0.045, foundation_h + body_height * 0.46), (0.62, 0.08, body_height * 0.72), door_mat, bevel=0.035)
    for x in (-0.24, 0.24):
        cube(collection, f"door_reinforcing_band_{x}", (x, -depth / 2 - 0.095, foundation_h + body_height * 0.46), (0.065, 0.035, body_height * 0.78), MATS["metal_light"], bevel=0.01)
    add_window(collection, "cashier_window", (-0.62, -depth / 2 - 0.065, foundation_h + body_height * 0.68), (0.34, 0.055, 0.28), MATS["glass" if level >= 5 and not damaged else "window_warm"], damaged)
    cube(collection, "cashier_counter_sill", (-0.62, -depth / 2 - 0.09, foundation_h + body_height * 0.47), (0.44, 0.08, 0.08), MATS["wood_light" if level <= 6 else "metal_light"], bevel=0.012)
    add_metal_wall_skin(collection, level, width, depth, foundation_h, body_height, damaged)
    if not ruined:
        roof_material = level_roof_mat(level, damaged)
        roof_height = 0.34 + min(progress, 4) * 0.03 + (0.04 if level >= 9 else 0.0)
        if level <= 6:
            hipped_roof(collection, "secure_roof", (0, 0, foundation_h + body_height), (width + 0.36, depth + 0.30, roof_height), roof_material, cap=0.32 if level < 7 else 0.46)
        else:
            prism_roof(collection, "secure_roof", (0, 0, foundation_h + body_height), (width + 0.32, depth + 0.26, roof_height), roof_material)
        cube(collection, "front_eave_trim", (0, -depth / 2 - 0.12, foundation_h + body_height + 0.08), (width + 0.46, 0.08, 0.10), MATS["dark_metal" if level >= 7 and not damaged else "metal_light" if level >= 7 else "wood_light"], bevel=0.014)
        add_roof_upgrade_details(collection, level, width, depth, foundation_h + body_height, roof_height, damaged)
        add_battlements(collection, level, width, depth, foundation_h + body_height + 0.18, damaged)
        add_wind_marker(collection, "roof_wind_marker", (width * 0.27, -0.12, foundation_h + body_height + 0.34), 0.72, damaged)
    else:
        cube(collection, "collapsed_roof_plate_left", (-0.48, 0.04, 0.42), (0.82, 0.62, 0.10), MATS["damage"], rot=(0.02, -0.12, 0.34), bevel=0.018)
        cube(collection, "collapsed_roof_plate_right", (0.46, 0.16, 0.34), (0.64, 0.54, 0.10), MATS["metal"], rot=(-0.02, 0.10, -0.42), bevel=0.018)
    if level >= 5:
        cube(collection, "guard_lantern_left", (-1.14, -0.62, 0.72), (0.18, 0.13, 0.22), MATS["window_warm"], bevel=0.02)
        cube(collection, "guard_lantern_right", (1.14, -0.62, 0.72), (0.18, 0.13, 0.22), MATS["window_warm"], bevel=0.02)
    if level >= 7:
        add_mechanism(collection, level, damaged)
        add_safe_cells(collection, level, width, depth, foundation_h + body_height * 0.34, damaged)
    if level >= 8:
        for x in (-0.58, 0.58):
            cube(collection, f"steel_side_brace_{x}", (x, -depth / 2 - 0.075, foundation_h + body_height * 0.72), (0.08, 0.04, body_height * 0.7), MATS["metal_light"], rot=(0, 0, 0.18 if x < 0 else -0.18), bevel=0.01)
        for x in (-1.0, 1.0):
            cube(collection, f"guard_bollard_{x}", (x, -depth / 2 - 0.34, 0.30), (0.14, 0.14, 0.45), MATS["concrete"], bevel=0.03)
    if level >= 9:
        for x in (-0.78, 0.0, 0.78):
            cube(collection, f"armor_plate_{x}", (x, -depth / 2 - 0.085, foundation_h + body_height * 0.33), (0.34, 0.045, 0.34), MATS["armor" if not damaged else "damage"], bevel=0.016)
    if level >= 10:
        cylinder(collection, "gold_limit_emblem", (0.0, -depth / 2 - 0.095, foundation_h + body_height * 0.84), 0.13, 0.035, MATS["gold"], vertices=18, rot=(math.radians(90), 0, 0))
        cylinder(collection, "large_combo_wheel_outer", (0.0, -depth / 2 - 0.128, foundation_h + body_height * 0.52), 0.20, 0.035, MATS["metal_light"], vertices=20, rot=(math.radians(90), 0, 0))
        cylinder(collection, "large_combo_wheel_gold_pin", (0.0, -depth / 2 - 0.155, foundation_h + body_height * 0.52), 0.06, 0.026, MATS["gold"], vertices=14, rot=(math.radians(90), 0, 0))
        add_late_gold_wall_accents(collection, level, width, depth, foundation_h, body_height, damaged)
    add_super_mechanism(collection, level, depth, foundation_h, body_height, damaged)
    add_crystal_indicator(collection, level, damaged)
    add_bags(collection, min(level, 6), damaged, ruined)
    add_coin_accent(collection, 0.88, -0.82, 0.13, 2 + min(level - 3, 4), damaged)
    if damaged:
        add_late_damage(collection, level, width, depth, foundation_h, body_height, ruined)
        if ruined and level >= 7:
            add_unmounted_roof_pin_canopy_parts(collection, level, ruined=True)


def build_variant(level, state):
    collection = bpy.data.collections.new(f"{ASSET_ID}_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    add_base(collection)
    if level == 1:
        add_level_one(collection, state)
    elif level == 2:
        add_level_two(collection, state)
    elif level == 3:
        add_level_three(collection, state)
    else:
        add_late_level(collection, level, state)
    if state in ("damaged", "ruined"):
        add_debris(collection, level, ruined=state == "ruined")
    for obj in collection.objects:
        obj["real_city_asset"] = ASSET_ID
        obj["level"] = level
        obj["state"] = state
    return collection


def setup_scene():
    scene = bpy.context.scene
    housing_path = Path(__file__).with_name("regenerate_early_housing.py")
    spec = importlib.util.spec_from_file_location("housing_camera", housing_path)
    housing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(housing)
    housing.setup_camera(scene)
    scene.camera.name = "coin_storage_iso_camera"
    scene.camera.data.name = "coin_storage_iso_camera"
    scene.render.resolution_x = SIZE[0]
    scene.render.resolution_y = SIZE[1]
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1


def set_visible_collection(target):
    for collection in bpy.data.collections:
        collection.hide_render = collection != target
        collection.hide_viewport = collection != target
    target.hide_render = False
    target.hide_viewport = False


def export_collection(collection, path):
    set_visible_collection(collection)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=blender_path(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )


def render_collection(collection, path):
    set_visible_collection(collection)
    scene = bpy.context.scene
    scene.render.filepath = blender_path(path)
    enum_values = {item.identifier for item in scene.render.image_settings.bl_rna.properties["file_format"].enum_items}
    if "PNG" in enum_values:
        scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)


def mesh_stats(collection):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = list(collection.objects)
    tris = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        tris += sum(len(poly.vertices) - 2 for poly in mesh.polygons)
        evaluated.to_mesh_clear()
    return {"objects": len(objects), "triangles": tris}


def write_manifest(collections, report, levels):
    manifest = {
        "asset_id": ASSET_ID,
        "display_name": DISPLAY_NAME,
        "category": "storage",
        "generated_at": date.today().isoformat(),
        "levels": list(levels),
        "states": list(STATES),
        "footprint": {"width": 1, "height": 1},
        "sprite": {"size": list(SIZE), "anchor": list(ANCHOR)},
        "material_mapping": {
            "wood": "сундук, дощатые стены, навес, каркас стройки",
            "stone": "камни по углам и цоколь",
            "planks": "дощатая кладовая и ранние стены",
            "iron": "полосы сейфовой двери, замок, решетки и ранние механизмы",
            "brick": "корпус городской казны уровней 5-6 и основа под металлическую обшивку позднее",
            "glass": "кассовые окна средних уровней",
            "reinforced_concrete": "основание уровней 7-12 и усиленный фундамент с 9 уровня",
            "steel": "механический счетчик, толстые темно-серые балки, силовые полосы, козырьки уровней 7-8 и защита фундамента с 10 уровня",
            "armor_plates": "бронеплиты крыши с 9 уровня, полная крыша и козырьки с 10 уровня, стены и шипы с 11 уровня",
            "gold_ingot": "золотая печать, лимитный диск и постепенная позолота с 10 уровня, усиленная на 11-12 уровнях",
            "crystal": "видимый встроенный светокристалл только на уровнях 11-12",
            "coins": "не моделируются как нематериальная стоимость; золото используется только как небольшой акцент",
        },
        "files": [
            {
                "id": collection.name,
                "level": item["level"],
                "state": item["state"],
                "glb": item["glb"],
                "png": item["png"],
                "objects": item["objects"],
                "triangles": item["triangles"],
            }
            for collection, item in report
        ],
        "source_blend": f"{ASSET_ID}_levels.blend",
        "notes": [
            "Цепочка развивается от сундука под навесом к каменной казне, кирпичному корпусу, железобетонному сейфу и поздней бронированной казне.",
            "Сохранены основные признаки: сундук/закрытая кладовая, тяжелая сейфовая дверь, решетки, счетчик лимита, мешки и малые золотые акценты.",
            "Construction варианты имеют незавершенную геометрию, а не готовую модель с лесами.",
            "Damaged/ruined варианты используют крупные проломы стен и крыши, трещины и отдельные обломки без висящих в воздухе частей.",
            "Уровни 7-8 используют треугольную каменную крышу и стальные козырьки на кровельных штырьках.",
            "Уровень 9 переводит крышные козырьки и фундамент в железобетон; уровень 10 усиливает фундамент сталью и добавляет бронеплиты.",
            "Позолота начинается с 10 уровня, заметно растет на 11 и становится самой выраженной на 12, но железобетонный фундамент остается читаемым.",
            "Супер-механизмы на уровнях 11-12 вынесены на фасад и дополнительно видны в construction-вариантах.",
            "Освещение пересобрано под мягкий дневной изометрический стиль Real City: key sun, area fill, warm rim и нечерные тени.",
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(levels=LEVELS, states=STATES):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    levels = tuple(levels)
    states = tuple(states)
    clear_scene()
    make_materials()
    setup_scene()
    collections = []
    report = []
    for level in levels:
        for state in states:
            collection = build_variant(level, state)
            collections.append(collection)
            glb_name = f"{ASSET_ID}_l{level:02d}_{state}.glb"
            png_name = f"{ASSET_ID}_l{level:02d}_{state}.png"
            stats = mesh_stats(collection)
            export_collection(collection, OUT_DIR / glb_name)
            render_collection(collection, OUT_DIR / png_name)
            report.append((collection, {"level": level, "state": state, "glb": glb_name, "png": png_name, **stats}))
            print(f"COIN_STORAGE_VARIANT_DONE l{level:02d}_{state} tris={stats['triangles']} objects={stats['objects']}")
    for collection in bpy.data.collections:
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.ops.export_scene.gltf(
        filepath=blender_path(OUT_DIR / f"{ASSET_ID}_levels.glb"),
        export_format="GLB",
        use_active_scene=True,
        export_extras=True,
    )
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(OUT_DIR / f"{ASSET_ID}_levels.blend"))
    write_manifest(collections, report, levels)
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id=ASSET_ID,
            display_name=DISPLAY_NAME,
            category="storage",
            output_dir=OUT_DIR,
            levels=levels,
            states=states,
            source_blend=OUT_DIR / f"{ASSET_ID}_levels.blend",
            combined_glb=OUT_DIR / f"{ASSET_ID}_levels.glb",
            generator="tools/assets/blender/generate_coin_storage_models.py",
            style_reference="Real City storage chain migrated to shared scene/export/report layer",
        )
    )
    return {"asset_id": ASSET_ID, "variants": len(report), "out_dir": str(OUT_DIR)}


def validate_roundtrip(levels=LEVELS, states=STATES):
    levels = tuple(levels)
    states = tuple(states)
    report = []
    for level in levels:
        for state in states:
            path = OUT_DIR / f"{ASSET_ID}_l{level:02d}_{state}.glb"
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=blender_path(path))
            imported = [obj for obj in bpy.data.objects if obj not in before]
            tris = 0
            for obj in imported:
                if obj.type == "MESH":
                    tris += sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
            report.append({"file": path.name, "objects": len(imported), "triangles": tris, "ok": bool(imported) and tris > 0})
            bpy.ops.object.select_all(action="DESELECT")
            for obj in imported:
                obj.select_set(True)
            bpy.ops.object.delete()
    (OUT_DIR / "roundtrip-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"validated": len(report), "ok": sum(1 for item in report if item["ok"])}
