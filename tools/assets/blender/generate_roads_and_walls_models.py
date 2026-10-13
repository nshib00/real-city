"""Blender MCP: generate(), validate_roundtrip().

Builds modular road and wall kits for Real City.
Ground/clay road is intentionally excluded because it has its own generator.
"""

import json
import math
import os
import random
import importlib.util
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
ROADS_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "roads"
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
SIZE = 512
FOOTPRINT = 3.6
STATES = ("active", "construction", "damaged", "ruined")
SHAPES = {
    "single": (),
    "end_n": ("n",),
    "end_e": ("e",),
    "end_s": ("s",),
    "end_w": ("w",),
    "straight_ns": ("n", "s"),
    "straight_ew": ("e", "w"),
    "corner_ne": ("n", "e"),
    "corner_es": ("e", "s"),
    "corner_sw": ("s", "w"),
    "corner_wn": ("w", "n"),
    "t_nes": ("n", "e", "s"),
    "t_esw": ("e", "s", "w"),
    "t_swn": ("s", "w", "n"),
    "t_wne": ("w", "n", "e"),
    "cross": ("n", "e", "s", "w"),
}

KITS = {
    "common_road": {
        "display_name": "Обычная дорога",
        "kind": "road",
        "style": "light gravel city road with wood and stone edging",
        "materials": {
            "stone": "мелкая светлая каменная крошка и ремонтные камни",
            "wood": "редкие деревянные края и временные строительные планки",
        },
    },
    "paved_road": {
        "display_name": "Мостовая",
        "kind": "road",
        "style": "warm stone and muted brick paved city road",
        "materials": {
            "stone_block": "плиты и светлые каменные края",
            "brick": "теплые кирпичные вставки в швах и узлах",
        },
    },
    "wooden_wall": {
        "display_name": "Деревянная стена",
        "kind": "wall",
        "style": "rough timber palisade with braces and rope ties",
        "materials": {
            "wood": "вертикальные бревна частокола",
            "planks": "поперечные балки и ремонтные заплаты",
            "rope": "веревочные стяжки на узлах",
        },
    },
    "stone_wall": {
        "display_name": "Каменная стена",
        "kind": "wall",
        "style": "solid warm stone wall with block pillars",
        "materials": {
            "stone": "основная кладка",
            "stone_block": "угловые опоры и торцевые тумбы",
        },
    },
    "reinforced_wall": {
        "display_name": "Усиленная стена",
        "kind": "wall",
        "style": "late reinforced concrete and metal wall segment",
        "materials": {
            "reinforced_concrete": "массивная бетонная основа",
            "steel": "металлические пластины, скобы и анкеры",
            "armor_plates": "темные защитные накладки",
        },
    },
}

MATS = {}
COLLECTIONS = {}
REPORT = {}
SCENE = None
OUT_DIR = None
CURRENT_KIT = None


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        relative = raw[len(root) :].lstrip("\\")
        return BLENDER_ROOT + "\\" + relative
    return raw


def mat(name, color, roughness=0.84):
    material = bpy.data.materials.new("MAT_roads_walls_" + name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = roughness
    MATS[name] = material
    return material


def palette():
    for name, color in {
        "grass": (0.26, 0.49, 0.09),
        "grass_light": (0.39, 0.62, 0.15),
        "earth": (0.30, 0.21, 0.11),
        "gravel": (0.62, 0.58, 0.49),
        "gravel_light": (0.78, 0.74, 0.63),
        "road_shadow": (0.34, 0.31, 0.27),
        "dry_dust": (0.66, 0.55, 0.37),
        "paver": (0.70, 0.68, 0.60),
        "paver_light": (0.86, 0.82, 0.70),
        "brick": (0.63, 0.30, 0.20),
        "wood": (0.55, 0.33, 0.15),
        "wood_light": (0.74, 0.48, 0.23),
        "wood_dark": (0.32, 0.18, 0.09),
        "rope": (0.76, 0.62, 0.35),
        "stone": (0.58, 0.58, 0.52),
        "stone_light": (0.76, 0.75, 0.67),
        "stone_dark": (0.34, 0.35, 0.34),
        "concrete": (0.47, 0.50, 0.49),
        "concrete_light": (0.65, 0.68, 0.66),
        "metal": (0.32, 0.34, 0.35),
        "metal_light": (0.55, 0.58, 0.58),
        "damage_dark": (0.16, 0.14, 0.12),
        "marking": (0.88, 0.73, 0.38),
    }.items():
        mat(name, color)
    for role in ("grass", "grass_light"):
        MATS[role]["terrain_source"] = "frontend/public/assets/terrain/tiles/grass.png"


def box(collection, name, pos, size, role, bevel=0.015, rotation=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vertex in bm.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.22), segments=1, affect="EDGES")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(f"SM_{CURRENT_KIT}_{name}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = rotation
    mesh.materials.append(MATS[role])
    return obj


def cylinder(collection, name, pos, radius, depth, role, vertices=12, scale=(1, 1, 1), rotation=(0, 0, 0), radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=vertices,
        radius1=radius,
        radius2=radius if radius2 is None else radius2,
        depth=depth,
    )
    for vertex in bm.verts:
        vertex.co.x *= scale[0]
        vertex.co.y *= scale[1]
        vertex.co.z *= scale[2]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(f"SM_{CURRENT_KIT}_{name}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = rotation
    mesh.materials.append(MATS[role])
    return obj


def beam(collection, name, a, b, width, role, bevel=None):
    delta = Vector(b) - Vector(a)
    obj = box(collection, name, (Vector(a) + Vector(b)) / 2, (width, width, delta.length), role, bevel=bevel or width * 0.18)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def base_tile(collection):
    box(collection, "earth_tile", (0, 0, -0.015), (FOOTPRINT, FOOTPRINT, 0.03), "earth", bevel=0.0)
    box(collection, "grass_tile", (0, 0, 0.004), (FOOTPRINT * 0.99, FOOTPRINT * 0.99, 0.008), "grass", bevel=0.0)
    for index, (x, y) in enumerate(((-1.35, 1.10), (1.27, 1.15), (-1.18, -1.15), (1.18, -1.05))):
        tuft(collection, x, y, 0.68 + 0.12 * (index % 2))


def tuft(collection, x, y, scale=1.0):
    for index, offset in enumerate((-0.04, 0.0, 0.04)):
        beam(
            collection,
            "grass_tuft",
            (x + offset, y, 0.035),
            (x + offset * 1.5 + 0.03 * (index - 1), y + 0.05, 0.12 * scale),
            0.016,
            "grass_light",
        )


def segment_center(direction, length):
    half = length / 2
    return {
        "n": (0, half),
        "s": (0, -half),
        "e": (half, 0),
        "w": (-half, 0),
    }[direction]


def segment_box(collection, name, direction, length, width, height, role, z, bevel=0.04):
    x, y = segment_center(direction, length)
    if direction in ("n", "s"):
        return box(collection, name + "_" + direction, (x, y, z), (width, length, height), role, bevel=bevel)
    return box(collection, name + "_" + direction, (x, y, z), (length, width, height), role, bevel=bevel)


def endpoint(direction, distance=1.52):
    return {
        "n": (0, distance),
        "s": (0, -distance),
        "e": (distance, 0),
        "w": (-distance, 0),
    }[direction]


def add_road(collection, kit_id, shape, state):
    dirs = SHAPES[shape]
    rng = random.Random(hash((kit_id, shape, state)) & 0xFFFFFFFF)
    ruined = state == "ruined"
    damaged = state in ("damaged", "ruined")
    width = 1.82 if kit_id == "common_road" else 1.92
    seg_len = {"active": 1.82, "construction": 1.45, "damaged": 1.66, "ruined": 1.10}[state]
    surface_role = "gravel" if kit_id == "common_road" else "paver"
    light_role = "gravel_light" if kit_id == "common_road" else "paver_light"
    edge_role = "wood" if kit_id == "common_road" else "stone_dark"
    if state == "construction":
        surface_role = "dry_dust"
    if ruined:
        surface_role = "road_shadow"

    center = width if dirs else 1.18
    box(collection, "road_center", (0, 0, 0.05), (center, center, 0.035), surface_role, bevel=0.07)
    for direction in dirs:
        segment_box(collection, "road_surface", direction, seg_len, width, 0.035, surface_role, 0.05, bevel=0.065)
        if kit_id == "common_road":
            if direction in ("n", "s"):
                segment_box(collection, "road_edge_left", direction, seg_len, 0.065, 0.05, edge_role, 0.08, bevel=0.018).location.x -= width * 0.52
                segment_box(collection, "road_edge_right", direction, seg_len, 0.065, 0.05, edge_role, 0.08, bevel=0.018).location.x += width * 0.52
            else:
                segment_box(collection, "road_edge_left", direction, seg_len, 0.065, 0.05, edge_role, 0.08, bevel=0.018).location.y -= width * 0.52
                segment_box(collection, "road_edge_right", direction, seg_len, 0.065, 0.05, edge_role, 0.08, bevel=0.018).location.y += width * 0.52
        else:
            paver_count = 4
            for i in range(paver_count):
                offset = -seg_len * 0.38 + i * seg_len * 0.25
                role = light_role if i % 2 == 0 else surface_role
                if direction in ("n", "s"):
                    y = offset if direction == "n" else -offset
                    box(collection, "paver_slab", (0, y, 0.083), (width * 0.82, 0.22, 0.026), role, bevel=0.018, rotation=(0, 0, rng.uniform(-0.03, 0.03)))
                else:
                    x = offset if direction == "e" else -offset
                    box(collection, "paver_slab", (x, 0, 0.083), (0.22, width * 0.82, 0.026), role, bevel=0.018, rotation=(0, 0, rng.uniform(-0.03, 0.03)))

    detail_count = {"active": 10, "construction": 18, "damaged": 16, "ruined": 20}[state]
    for i in range(detail_count):
        if dirs:
            direction = rng.choice(dirs)
            x, y = endpoint(direction, rng.uniform(0.25, 1.35))
            if direction in ("n", "s"):
                x += rng.uniform(-0.65, 0.65)
            else:
                y += rng.uniform(-0.65, 0.65)
        else:
            x, y = rng.uniform(-0.55, 0.55), rng.uniform(-0.55, 0.55)
        role = rng.choice((light_role, "dry_dust", "stone_light", "brick" if kit_id == "paved_road" else "gravel_light"))
        cylinder(collection, "road_detail", (x, y, 0.095), rng.uniform(0.025, 0.065), rng.uniform(0.012, 0.032), role, vertices=8, scale=(rng.uniform(0.8, 1.7), rng.uniform(0.5, 1.2), 1), rotation=(0, 0, rng.random() * math.tau))
        if damaged and i % 4 == 0:
            cylinder(collection, "road_gap", (x + rng.uniform(-0.08, 0.08), y + rng.uniform(-0.08, 0.08), 0.112), rng.uniform(0.07, 0.13), 0.014, "damage_dark", vertices=10, scale=(1.4, 0.8, 1), rotation=(0, 0, rng.random() * math.tau))

    if state == "construction":
        for direction in dirs or ("n",):
            x, y = endpoint(direction, 1.20)
            beam(collection, "layout_string", (0, 0, 0.16), (x, y, 0.16), 0.012, "marking")
            cylinder(collection, "supply_pile", (x * 0.7 + 0.10, y * 0.7 - 0.06, 0.10), 0.14, 0.12, light_role, vertices=9, scale=(1.45, 0.85, 1), rotation=(0, 0, rng.random() * math.tau))

    if len(dirs) >= 3 and not ruined:
        cylinder(collection, "junction_wear", (0, 0, 0.105), width * 0.38, 0.014, light_role, vertices=18, scale=(1.25, 0.92, 1), rotation=(0, 0, math.pi / 4))


def add_wood_wall_segment(collection, direction, length, state, rng):
    count = {"active": 5, "construction": 3, "damaged": 3, "ruined": 1}[state]
    for i in range(count):
        t = -0.45 + i * (0.9 / max(count - 1, 1))
        if direction in ("n", "s"):
            y = segment_center(direction, length)[1] + t * length * 0.45 * (1 if direction == "n" else -1)
            x = rng.uniform(-0.03, 0.03)
            rot = (0, 0, rng.uniform(-0.05, 0.05))
        else:
            x = segment_center(direction, length)[0] + t * length * 0.45 * (1 if direction == "e" else -1)
            y = rng.uniform(-0.03, 0.03)
            rot = (0, 0, math.pi / 2 + rng.uniform(-0.05, 0.05))
        height = rng.uniform(0.62, 0.86)
        if state == "damaged" and i % 2 == 0:
            height *= 0.55
        if state == "ruined":
            cylinder(collection, "fallen_log", (x, y, 0.12), 0.055, rng.uniform(0.45, 0.70), "wood_dark", vertices=10, scale=(1, 1, 1), rotation=(math.pi / 2, 0, rng.random() * math.tau))
        else:
            cylinder(collection, "palisade_post", (x, y, 0.08 + height / 2), 0.065, height, "wood", vertices=10, scale=(0.85, 1.15, 1), rotation=rot)
    if state != "ruined":
        z_values = (0.38,) if state == "construction" else (0.32, 0.60)
        for z in z_values:
            a = endpoint(direction, 0.18)
            b = endpoint(direction, length - 0.16)
            beam(collection, "cross_beam", (a[0], a[1], z), (b[0], b[1], z), 0.07, "wood_light")


def add_wall(collection, kit_id, shape, state):
    dirs = SHAPES[shape]
    rng = random.Random(hash((kit_id, shape, state)) & 0xFFFFFFFF)
    length = {"active": 1.72, "construction": 1.32, "damaged": 1.52, "ruined": 0.95}[state]
    if not dirs:
        dirs = ("n",)
        length = 0.70

    base_role = {
        "wooden_wall": "wood_dark",
        "stone_wall": "stone_dark",
        "reinforced_wall": "concrete",
    }[kit_id]
    wall_role = {
        "wooden_wall": "wood",
        "stone_wall": "stone",
        "reinforced_wall": "concrete_light",
    }[kit_id]
    cap_role = {
        "wooden_wall": "rope",
        "stone_wall": "stone_light",
        "reinforced_wall": "metal_light",
    }[kit_id]
    height = {"wooden_wall": 0.78, "stone_wall": 0.68, "reinforced_wall": 0.82}[kit_id]
    thickness = {"wooden_wall": 0.30, "stone_wall": 0.46, "reinforced_wall": 0.54}[kit_id]

    for direction in dirs:
        segment_box(collection, "wall_footing", direction, length, thickness + 0.18, 0.08, base_role, 0.055, bevel=0.025)
        if kit_id == "wooden_wall":
            add_wood_wall_segment(collection, direction, length, state, rng)
        else:
            if state == "ruined":
                visible_height = height * 0.25
            elif state == "construction":
                visible_height = height * 0.45
            elif state == "damaged":
                visible_height = height * 0.65
            else:
                visible_height = height
            segment_box(collection, "wall_body", direction, length, thickness, visible_height, wall_role, 0.10 + visible_height / 2, bevel=0.045)
            if state in ("active", "damaged"):
                segment_box(collection, "wall_cap", direction, length * 0.96, thickness * 1.04, 0.10, cap_role, 0.16 + visible_height, bevel=0.035)
            block_count = 3 if state != "ruined" else 2
            for i in range(block_count):
                t = -0.36 + i * 0.36
                if direction in ("n", "s"):
                    x, y = rng.uniform(-0.02, 0.02), segment_center(direction, length)[1] + t * length * (1 if direction == "n" else -1)
                    size = (thickness * 1.08, 0.08, 0.09)
                else:
                    x, y = segment_center(direction, length)[0] + t * length * (1 if direction == "e" else -1), rng.uniform(-0.02, 0.02)
                    size = (0.08, thickness * 1.08, 0.09)
                role = "stone_light" if kit_id == "stone_wall" else ("metal" if kit_id == "reinforced_wall" else cap_role)
                box(collection, "wall_reinforcement", (x, y, 0.34 + visible_height * 0.25), size, role, bevel=0.018)

    node_dirs = SHAPES[shape]
    node_count = max(1, len(node_dirs))
    node_size = {
        "wooden_wall": (0.30, 0.30, 0.72),
        "stone_wall": (0.56, 0.56, 0.74),
        "reinforced_wall": (0.66, 0.66, 0.88),
    }[kit_id]
    if state == "construction":
        node_size = (node_size[0], node_size[1], node_size[2] * 0.55)
    if state == "damaged":
        node_size = (node_size[0], node_size[1], node_size[2] * 0.72)
    if state == "ruined":
        node_size = (node_size[0], node_size[1], node_size[2] * 0.20)
    if kit_id == "wooden_wall":
        cylinder(collection, "wall_node", (0, 0, 0.10 + node_size[2] / 2), node_size[0] * 0.42, node_size[2], wall_role, vertices=10, scale=(1, 1, 1.0))
        if state not in ("ruined", "construction"):
            cylinder(collection, "rope_wrap", (0, 0, 0.58), node_size[0] * 0.48, 0.045, "rope", vertices=12, scale=(1.18, 1.18, 1))
    else:
        box(collection, "wall_node", (0, 0, 0.10 + node_size[2] / 2), node_size, wall_role, bevel=0.055)
        if kit_id == "reinforced_wall" and state != "ruined":
            box(collection, "armor_plate_front", (0, -0.23, 0.58), (0.46, 0.055, 0.32), "metal", bevel=0.012)
            box(collection, "armor_plate_side", (-0.23, 0, 0.58), (0.055, 0.46, 0.32), "metal", bevel=0.012)

    debris_count = {"active": 2, "construction": 9, "damaged": 12, "ruined": 18}[state]
    for i in range(debris_count):
        direction = rng.choice(dirs)
        x, y = endpoint(direction, rng.uniform(0.15, 1.30))
        if direction in ("n", "s"):
            x += rng.uniform(-0.42, 0.42)
        else:
            y += rng.uniform(-0.42, 0.42)
        role = rng.choice((wall_role, cap_role, base_role, "damage_dark"))
        if kit_id == "wooden_wall":
            cylinder(collection, "wall_debris", (x, y, 0.08), rng.uniform(0.025, 0.055), rng.uniform(0.18, 0.38), role, vertices=8, rotation=(math.pi / 2, 0, rng.random() * math.tau))
        else:
            box(collection, "wall_debris", (x, y, 0.07), (rng.uniform(0.08, 0.20), rng.uniform(0.07, 0.18), rng.uniform(0.04, 0.12)), role, bevel=0.018, rotation=(0, 0, rng.random() * math.tau))

    if state == "construction":
        for direction in dirs[:3]:
            x, y = endpoint(direction, 1.08)
            beam(collection, "construction_string", (0, 0, 0.18), (x, y, 0.18), 0.012, "marking")


def clean_collection(collection):
    for obj in collection.all_objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            obj.data.update()
            obj.select_set(False)


def build_asset(kit_id, shape, state):
    name = f"{kit_id}_{shape}_{state}"
    collection = bpy.data.collections.new(name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[name] = collection
    base_tile(collection)
    if KITS[kit_id]["kind"] == "road":
        add_road(collection, kit_id, shape, state)
    else:
        add_wall(collection, kit_id, shape, state)
    clean_collection(collection)
    return collection


def setup_scene():
    global SCENE
    SCENE = bpy.data.scenes.new("Real_City_Roads_And_Walls")
    bpy.context.window.scene = SCENE
    palette()
    spec = importlib.util.spec_from_file_location("terrain_camera", Path(__file__).with_name("regenerate_early_housing.py"))
    terrain_camera = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(terrain_camera)
    terrain_camera.setup_camera(SCENE)
    SCENE.render.resolution_x = SIZE
    SCENE.render.resolution_y = SIZE
    SCENE.camera.data.ortho_scale = FOOTPRINT * math.sqrt(2) * SIZE / 480
    SCENE.camera.data.shift_y = 0
    bpy.context.view_layer.update()
    initial = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y
    SCENE.camera.data.shift_y = 0.1
    delta = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y - initial
    SCENE.camera.data.shift_y = ((1 - 320 / SIZE) - initial) * 0.1 / delta
    SCENE.render.film_transparent = True
    if "PNG" in [item.identifier for item in SCENE.render.image_settings.bl_rna.properties["file_format"].enum_items]:
        SCENE.render.image_settings.file_format = "PNG"
    if "RGBA" in [item.identifier for item in SCENE.render.image_settings.bl_rna.properties["color_mode"].enum_items]:
        SCENE.render.image_settings.color_mode = "RGBA"
    return SCENE


def show_only(collection_name):
    for name, collection in COLLECTIONS.items():
        hidden = name != collection_name
        collection.hide_viewport = hidden
        collection.hide_render = hidden
    for obj in SCENE.objects:
        obj.select_set(False)
    for obj in COLLECTIONS[collection_name].all_objects:
        obj.select_set(True)
    bpy.context.view_layer.update()


def export_asset(kit_id, shape, state):
    name = f"{kit_id}_{shape}_{state}"
    show_only(name)
    triangles = 0
    objects = 0
    for obj in COLLECTIONS[name].all_objects:
        if obj.type != "MESH":
            continue
        objects += 1
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        assert all(edge.is_manifold for edge in bm.edges), obj.name
        bm.free()
    assert triangles < 6500, (name, triangles)
    family_dir = OUT_DIR / kit_id
    os.makedirs(blender_path(family_dir), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=blender_path(family_dir / f"{name}.glb"),
        export_format="GLB",
        use_selection=True,
        use_active_scene=True,
    )
    SCENE.render.filepath = blender_path(family_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    REPORT[kit_id][name] = {
        "shape": shape,
        "state": state,
        "level": 1,
        "triangles": triangles,
        "objects": objects,
        "png": f"{name}.png",
        "glb": f"{name}.glb",
    }


def save_family_manifest(kit_id):
    family_dir = OUT_DIR / kit_id
    sample_name = f"{kit_id}_cross_active"
    show_only(sample_name)
    bpy.data.libraries.write(blender_path(family_dir / f"{kit_id}.blend"), {SCENE}, fake_user=True)
    manifest = {
        "id": kit_id,
        "display_name": KITS[kit_id]["display_name"],
        "building_type": KITS[kit_id]["kind"],
        "style": KITS[kit_id]["style"],
        "size": [SIZE, SIZE],
        "footprint": FOOTPRINT,
        "anchor": [256, 320],
        "levels": [1],
        "shapes": list(SHAPES.keys()),
        "states": list(STATES),
        "materials": KITS[kit_id]["materials"],
        "assets": REPORT[kit_id],
    }
    Path(blender_path(family_dir / "manifest.json")).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def generate(output_dir=None, kits=None):
    global OUT_DIR, CURRENT_KIT
    OUT_DIR = Path(output_dir or ROADS_DIR)
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)
    setup_scene()
    selected = kits or list(KITS.keys())
    for kit_id in selected:
        CURRENT_KIT = kit_id
        REPORT[kit_id] = {}
        os.makedirs(blender_path(OUT_DIR / kit_id), exist_ok=True)
        for shape in SHAPES:
            for state in STATES:
                build_asset(kit_id, shape, state)
        for shape in SHAPES:
            for state in STATES:
                export_asset(kit_id, shape, state)
        save_family_manifest(kit_id)
    print(f"Generated {sum(len(v) for v in REPORT.values())} road/wall assets into {OUT_DIR}")


def validate_roundtrip(output_dir=None, kits=None):
    out_dir = Path(output_dir or ROADS_DIR)
    selected = kits or list(KITS.keys())
    previous = bpy.context.scene
    qa_scene = bpy.data.scenes.new("roads_walls_roundtrip_qa")
    bpy.context.window.scene = qa_scene
    try:
        for kit_id in selected:
            family_dir = out_dir / kit_id
            manifest = json.loads(Path(blender_path(family_dir / "manifest.json")).read_text(encoding="utf-8"))
            results = []
            for name, info in manifest["assets"].items():
                bpy.ops.import_scene.gltf(filepath=blender_path(family_dir / info["glb"]))
                triangles = 0
                for obj in list(qa_scene.objects):
                    if obj.type == "MESH":
                        obj.data.calc_loop_triangles()
                        triangles += len(obj.data.loop_triangles)
                        bm = bmesh.new()
                        bm.from_mesh(obj.data)
                        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
                        assert all(edge.is_manifold for edge in bm.edges), (name, obj.name)
                        bm.free()
                    bpy.data.objects.remove(obj, do_unlink=True)
                assert triangles == info["triangles"], (name, triangles, info["triangles"])
                results.append({"asset": name, "triangles": triangles, "nonmanifold_edges": 0})
            Path(blender_path(family_dir / "roundtrip-validation.json")).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Roundtrip validated {len(results)} {kit_id} assets")
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa_scene)


if __name__ == "__main__":
    generate()
    validate_roundtrip()
