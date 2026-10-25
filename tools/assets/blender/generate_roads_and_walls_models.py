"""Blender MCP: generate(), validate_roundtrip().

Builds modular road and wall kits for Real City.
Ground/clay road is intentionally excluded because it has its own generator.
"""

import json
import math
import os
import random
import importlib.util
import struct
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
WOOD_LEVELS = (1, 2, 3)
STONE_LEVELS = (4, 5, 6, 7)
CONCRETE_LEVELS = (8, 9, 10)
MODERN_LEVELS = (11, 12, 13)
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
        "style": "tall continuous defensive timber palisade with pointed logs, braces and level-specific reinforcement",
        "materials": {
            "wood": "вертикальные бревна частокола",
            "planks": "поперечные балки и ремонтные заплаты",
            "rope": "веревочные стяжки на узлах",
            "stone": "каменная подошва уровня 3",
        },
    },
    "stone_wall": {
        "display_name": "Каменная стена",
        "kind": "wall",
        "style": "continuous defensive masonry with brick courses, cut-stone buttresses and late steel ties",
        "materials": {
            "stone": "непрерывное ядро и рельефная кладка уровней 4-5",
            "brick": "кирпичные пояса и ремонтная облицовка",
            "stone_block": "тесаные блоки, парапет и контрфорсы уровней 6-7",
            "steel": "стальные связи и скобы уровня 7",
        },
    },
    "concrete_wall": {
        "display_name": "Бетонная стена",
        "kind": "wall",
        "style": "continuous concrete rampart with steel reinforcement, armoured joints and heavy terminal pylons",
        "materials": {
            "concrete": "широкий бетонный сердечник и цоколь уровня 8",
            "stone_block": "каменные блоки подошвы уровня 8",
            "steel": "силовые ребра, арматура и стальные анкеры",
            "reinforced_concrete": "двухслойные панели уровней 9-10",
            "armor_plates": "защитные накладки швов уровней 9-10",
            "reinforced_beams": "верхний пояс и пилоны уровня 10",
        },
    },
    "modern_wall": {
        "display_name": "Современная стена",
        "kind": "wall",
        "style": "premium aeolian late-game barrier with porcelain armour, teal diagnostics, copper circuits and sculpted steel pylons",
        "materials": {
            "steel": "силовой каркас, фаски и ребра",
            "electronics": "светящиеся диагностические окна и медные трассы",
            "reinforced_concrete": "сплошное несущие ядро",
            "armor_plates": "светлая сегментированная броня",
            "reinforced_beams": "двойной верхний пояс уровней 12-13",
            "super_mechanism": "центральный защищенный узел уровня 13",
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


def write_json_lf(path: Path, data):
    with Path(blender_path(path)).open("w", encoding="utf-8", newline="\n") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")


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
        "stone_light": (0.66, 0.65, 0.57),
        "stone_dark": (0.34, 0.35, 0.34),
        "mortar": (0.43, 0.43, 0.39),
        "concrete": (0.47, 0.50, 0.49),
        "concrete_light": (0.65, 0.68, 0.66),
        "metal": (0.32, 0.34, 0.35),
        "metal_light": (0.55, 0.58, 0.58),
        "damage_dark": (0.16, 0.14, 0.12),
        "marking": (0.88, 0.73, 0.38),
        "porcelain_armor": (0.78, 0.86, 0.83),
        "pearl_edge": (0.94, 0.92, 0.76),
        "teal_glow": (0.08, 0.78, 0.71),
        "copper_trace": (0.78, 0.43, 0.20),
        "steel_blue": (0.20, 0.35, 0.43),
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


def add_defensive_wood_wall(collection, shape, state, level):
    """Continuous 1x1 palisade: arms reach tile edges and adjoining logs overlap."""
    dirs = SHAPES[shape] or ("n", "s")
    extent = 0.82 if shape == "single" else FOOTPRINT / 2
    height = {1: 1.30, 2: 1.56, 3: 1.85}[level]
    post_radius = {1: 0.106, 2: 0.116, 3: 0.126}[level]
    post_spacing = 0.18
    stone_top = 0.17 if level == 3 else 0.035
    for direction in dirs:
        axis = (0, 1) if direction in ("n", "s") else (1, 0)
        sign = 1 if direction in ("n", "e") else -1
        if level == 3:
            segment_box(collection, "stone_footing", direction, extent, 0.40, 0.15, "stone", 0.085, bevel=0.025)
        else:
            segment_box(collection, "timber_sill", direction, extent, 0.32, 0.08, "wood_dark", 0.055, bevel=0.02)
        count = max(3, math.ceil(extent / post_spacing))
        for i in range(count):
            distance = min(extent - 0.055, 0.115 + i * post_spacing)
            x, y = axis[0] * sign * distance, axis[1] * sign * distance
            missing = state == "construction" and i % 2 == 1
            broken = state == "damaged" and i % 4 in (1, 2)
            if missing:
                continue
            if state == "ruined":
                body_height = 0.20 + 0.09 * (i % 3)
            elif broken:
                body_height = height * (0.34 + 0.09 * (i % 2))
            elif state == "construction":
                body_height = height * (0.65 + 0.12 * (i % 3 == 0))
            else:
                body_height = height - 0.16 + 0.035 * (i % 3)
            body_bottom = stone_top - 0.015
            cylinder(collection, "palisade_log", (x, y, body_bottom + body_height / 2), post_radius, body_height, "wood" if i % 3 else "wood_light", vertices=12, scale=(0.93, 1.06, 1))
            if state == "active" or (state == "construction" and i % 3 == 0) or (state == "damaged" and not broken):
                cylinder(collection, "pointed_crown", (x, y, body_bottom + body_height + 0.105), post_radius * 1.01, 0.21, "wood_light", vertices=12, radius2=0.0)
            if state in ("active", "damaged") and i % 3 == 0 and not broken:
                cylinder(collection, "rope_collar", (x, y, min(height * 0.72, body_bottom + body_height - 0.07)), post_radius * 1.17, 0.055, "rope", vertices=12)
        if state in ("active", "damaged"):
            rail_end = extent if state == "active" else extent * 0.57
            for z in (0.46, height * 0.67) + ((height * 0.87,) if level >= 2 else ()):
                start = (axis[0] * sign * 0.04, axis[1] * sign * 0.04, z)
                end = (axis[0] * sign * rail_end, axis[1] * sign * rail_end, z)
                beam(collection, "cross_rail", start, end, 0.11 if level == 1 else 0.13, "wood_dark", bevel=0.018)
        if level >= 2 and state == "active":
            # One continuous outer belt covers the logs without dark gaps between
            # short panels; the pointed crowns remain visible above it.
            shield = segment_box(collection, "plank_shield", direction, extent, 0.12, 0.44, "wood_light", 0.57, bevel=0.018)
            if direction in ("n", "s"):
                shield.location.x += 0.16
            else:
                shield.location.y += 0.16
            # Battens and wooden pegs make the plank upgrade legible from the
            # game camera while the continuous board still seals the segment.
            for distance in (0.42, 0.92, 1.42):
                if distance >= extent - 0.08:
                    continue
                x, y = axis[0] * sign * distance, axis[1] * sign * distance
                if direction in ("n", "s"):
                    box(collection, "plank_batten", (x + 0.235, y, 0.57), (0.055, 0.095, 0.50), "wood_dark", bevel=0.014)
                else:
                    box(collection, "plank_batten", (x, y + 0.235, 0.57), (0.095, 0.055, 0.50), "wood_dark", bevel=0.014)
            if level == 3:
                # The final timber tier has a second crown beam, carried by
                # the palisade posts rather than floating above the wall.
                start = (axis[0] * sign * 0.04, axis[1] * sign * 0.04, height * 0.96)
                end = (axis[0] * sign * extent, axis[1] * sign * extent, height * 0.96)
                beam(collection, "upper_belt", start, end, 0.105, "wood_dark", bevel=0.018)
        if level == 3 and state in ("active", "damaged"):
            # Cut-stone facing belongs to the wall itself, not to loose props.
            for distance in (0.37, 0.89, 1.41):
                if distance >= extent - 0.07 or (state == "damaged" and distance == 0.89):
                    continue
                x, y = axis[0] * sign * distance, axis[1] * sign * distance
                if direction in ("n", "s"):
                    box(collection, "stone_footing_face", (x + 0.21, y, 0.095), (0.055, 0.40, 0.16), "stone_light", bevel=0.015)
                else:
                    box(collection, "stone_footing_face", (x, y + 0.21, 0.095), (0.40, 0.055, 0.16), "stone_light", bevel=0.015)
        if state == "active":
            brace_d = min(extent * 0.70, 1.15)
            bx, by = axis[0] * sign * brace_d, axis[1] * sign * brace_d
            side = 0.36 if direction in ("n", "s") else -0.36
            foot = (bx + (side if direction in ("n", "s") else 0), by + (side if direction in ("e", "w") else 0), 0.06)
            head = (bx, by, height * 0.72)
            beam(collection, "grounded_brace", foot, head, 0.105, "wood_dark", bevel=0.018)
        if state in ("construction", "damaged", "ruined"):
            for i in range(3 if state != "ruined" else 6):
                d = min(extent - 0.1, 0.28 + i * 0.24)
                x, y = axis[0] * sign * d, axis[1] * sign * d
                offset = 0.30 + 0.10 * (i % 2)
                pos = (x + (offset if axis[1] else 0), y + (offset if axis[0] else 0), 0.12)
                cylinder(collection, "fallen_timber", pos, 0.07, 0.36 + 0.10 * (i % 3), "wood_dark", vertices=10, rotation=(math.pi / 2, 0, i * 0.73))
    node_height = height if state == "active" else height * {"construction": 0.56, "damaged": 0.56, "ruined": 0.18}[state]
    cylinder(collection, "junction_post", (0, 0, stone_top + node_height / 2), post_radius * 1.45, node_height, "wood_dark", vertices=12)
    if state == "active":
        cylinder(collection, "junction_spike", (0, 0, stone_top + node_height + 0.11), post_radius * 1.45, 0.22, "wood_light", vertices=12, radius2=0.0)


def add_defensive_stone_wall(collection, shape, state, level):
    """Continuous masonry arms meet at a heavy pier; exposed block faces keep their relief."""
    dirs = SHAPES[shape] or ("n", "s")
    extent = 0.82 if shape == "single" else FOOTPRINT / 2
    height = {4: 1.18, 5: 1.35, 6: 1.52, 7: 1.68}[level]
    width = {4: 0.48, 5: 0.52, 6: 0.57, 7: 0.62}[level]
    core_height = height if state == "active" else height * {"construction": 0.48, "damaged": 0.42, "ruined": 0.19}[state]
    base_height = 0.16
    for direction in dirs:
        segment_box(collection, "continuous_foundation", direction, extent, width + 0.14, base_height, "stone_dark", base_height / 2, bevel=0.026)
        segment_box(collection, "masonry_core", direction, extent, width, core_height, "mortar", base_height + core_height / 2 - 0.018, bevel=0.035)
        # Staggered, large readable courses. The core keeps all neighbouring cells joined.
        row_count = 1 if state == "ruined" else (2 if state == "construction" else (4 if level >= 6 else 3))
        for row in range(row_count):
            if state == "damaged" and row >= 2:
                continue
            if state == "construction" and row >= 1 and direction in ("e", "s"):
                continue
            course_z = base_height + 0.16 + row * (height - 0.25) / (4 if level >= 6 else 3)
            if course_z > base_height + core_height + 0.02:
                continue
            brick_course = level <= 5 and row == (1 if level == 4 else 2)
            for index in range(7):
                if state == "damaged" and row == 1 and index in (2, 3, 4):
                    continue
                d = min(extent - 0.10, 0.12 + index * (extent - 0.17) / 7 + (0.055 if row % 2 else 0))
                x, y = endpoint(direction, d)
                role = "brick" if brick_course or (level >= 6 and row == 1 and index % 3 == 0) else ("stone_light" if (index + row) % 3 else "stone")
                for side in (-1, 1):
                    block_length = (extent - 0.17) / 7 * 0.90
                    if direction in ("n", "s"):
                        pos, size = (side * (width / 2 + 0.015), y, course_z), (0.07, block_length, 0.18)
                    else:
                        pos, size = (x, side * (width / 2 + 0.015), course_z), (block_length, 0.07, 0.18)
                    box(collection, "brick_facing" if brick_course else "stone_facing", pos, size, role, bevel=0.014)
        if state == "active":
            segment_box(collection, "cut_stone_cap", direction, extent, width + 0.11, 0.13, "stone_light", base_height + height + 0.038, bevel=0.026)
            if level >= 6:
                for index in range(3):
                    d = 0.32 + index * (extent - 0.36) / 3
                    x, y = endpoint(direction, d)
                    size = (width + 0.15, 0.25, 0.17) if direction in ("n", "s") else (0.25, width + 0.15, 0.17)
                    box(collection, "parapet_merlon", (x, y, base_height + height + 0.16), size, "stone_light", bevel=0.025)
            if level == 7:
                for d in (0.52, 1.28):
                    if d >= extent:
                        continue
                    x, y = endpoint(direction, d)
                    size = (width + 0.13, 0.10, 0.13) if direction in ("n", "s") else (0.10, width + 0.13, 0.13)
                    box(collection, "steel_clamp", (x, y, base_height + height * 0.72), size, "metal", bevel=0.013)
        if state == "construction":
            d = min(extent * 0.68, 1.12)
            x, y = endpoint(direction, d)
            for side in (-1, 1):
                offset = side * (width / 2 + 0.29)
                px, py = (offset, y) if direction in ("n", "s") else (x, offset)
                beam(collection, "scaffold_upright", (px, py, 0.045), (px, py, height * 0.76), 0.075, "wood", bevel=0.012)
            a = (-(width / 2 + 0.29), y, height * 0.69) if direction in ("n", "s") else (x, -(width / 2 + 0.29), height * 0.69)
            b = ((width / 2 + 0.29), y, height * 0.69) if direction in ("n", "s") else (x, (width / 2 + 0.29), height * 0.69)
            beam(collection, "scaffold_crossbar", a, b, 0.075, "wood_light", bevel=0.012)
        if state == "damaged":
            for index in (1, 4, 6):
                d = min(extent - 0.14, 0.13 + index * (extent - 0.17) / 7)
                x, y = endpoint(direction, d)
                size = (width * 0.84, 0.20, 0.30 + 0.08 * (index % 2)) if direction in ("n", "s") else (0.20, width * 0.84, 0.30 + 0.08 * (index % 2))
                box(collection, "broken_upper_block", (x, y, base_height + core_height + size[2] / 2 - 0.025), size, "stone_light", bevel=0.034)
        if level >= 6 and state in ("active", "damaged"):
            d = min(1.18, extent * 0.72)
            x, y = endpoint(direction, d)
            for side in (-1, 1):
                offset = side * (width / 2 + 0.10)
                px, py = (offset, y) if direction in ("n", "s") else (x, offset)
                box(collection, "cut_stone_buttress", (px, py, 0.44), (0.25, 0.33, 0.88), "stone_light", bevel=0.035)
        if state in ("construction", "damaged", "ruined"):
            for index in range(3 if state != "ruined" else 5):
                d = min(extent - 0.12, 0.35 + index * 0.25)
                x, y = endpoint(direction, d)
                px, py = (0.48 + 0.11 * (index % 2), y) if direction in ("n", "s") else (x, 0.48 + 0.11 * (index % 2))
                box(collection, "fallen_masonry", (px, py, 0.085), (0.20, 0.15, 0.15), "brick" if index % 3 == 0 else "stone_light", bevel=0.022, rotation=(0, 0, index * 0.28))
    pier_height = height + base_height if state == "active" else base_height + core_height
    box(collection, "junction_pier", (0, 0, pier_height / 2), (width + 0.24, width + 0.24, pier_height), "stone_light" if level >= 6 else "stone", bevel=0.045)
    if state == "active":
        box(collection, "pier_cap", (0, 0, pier_height + 0.055), (width + 0.35, width + 0.35, 0.13), "stone_light", bevel=0.03)
        if level == 7:
            for side in (-1, 1):
                box(collection, "pier_steel_tie", (side * (width / 2 + 0.12), 0, height * 0.72), (0.075, width + 0.28, 0.14), "metal", bevel=0.012)


def add_defensive_concrete_wall(collection, shape, state, level):
    """A continuous engineered barrier, with distinct construction and collapse."""
    dirs = SHAPES[shape] or ("n", "s")
    extent = 0.82 if shape == "single" else FOOTPRINT / 2
    height = {8: 1.78, 9: 1.94, 10: 2.10}[level]
    width = {8: 0.66, 9: 0.72, 10: 0.80}[level]
    core_fraction = {"active": 1.0, "construction": 0.46, "damaged": 0.48, "ruined": 0.18}[state]
    core_height = height * core_fraction
    footing = 0.17
    for direction in dirs:
        segment_box(collection, "stone_block_footing", direction, extent, width + 0.16, footing, "stone_dark", footing / 2, bevel=0.02)
        segment_box(collection, "concrete_core", direction, extent, width, core_height, "concrete", footing + core_height / 2 - 0.015, bevel=0.048)
        if state in ("active", "damaged"):
            # Surface panels sit against a solid core, so adjoining arms have no gaps.
            panel_count = 4 if state == "active" else 2
            for index in range(panel_count):
                d = 0.17 + index * (extent - 0.17) / 4
                x, y = endpoint(direction, d)
                for side in (-1, 1):
                    offset = side * (width / 2 + 0.016)
                    pos = (offset, y, footing + core_height * 0.57) if direction in ("n", "s") else (x, offset, footing + core_height * 0.57)
                    size = (0.075, (extent - 0.19) / 4 * 0.91, core_height * 0.73) if direction in ("n", "s") else ((extent - 0.19) / 4 * 0.91, 0.075, core_height * 0.73)
                    box(collection, "reinforced_concrete_panel" if level >= 9 else "concrete_panel", pos, size, "concrete_light", bevel=0.022)
            if state == "active":
                segment_box(collection, "steel_coping", direction, extent, width + 0.10, 0.11, "metal_light", footing + height + 0.04, bevel=0.019)
                if level >= 9:
                    for d in (0.50, 1.32):
                        if d >= extent:
                            continue
                        x, y = endpoint(direction, d)
                        size = (width + 0.19, 0.15, 0.39) if direction in ("n", "s") else (0.15, width + 0.19, 0.39)
                        box(collection, "armor_joint_plate", (x, y, footing + height * 0.66), size, "metal", bevel=0.022)
                if level == 10:
                    segment_box(collection, "reinforced_beam_crown", direction, extent, width + 0.21, 0.18, "metal", footing + height + 0.17, bevel=0.026)
                    for d in (0.56, 1.38):
                        if d < extent:
                            x, y = endpoint(direction, d)
                            box(collection, "steel_anchor", (x, y, footing + height + 0.29), (0.10, 0.10, 0.06), "metal_light", bevel=0.014)
        if state == "construction":
            # The exposed bars grow from the installed footing and incomplete core.
            for d in (0.30, 0.80, 1.30):
                if d >= extent:
                    continue
                x, y = endpoint(direction, d)
                beam(collection, "exposed_rebar", (x, y, footing + core_height - 0.04), (x, y, footing + height * 0.82), 0.045, "metal", bevel=0.008)
            d = min(1.12, extent * 0.68)
            x, y = endpoint(direction, d)
            for side in (-1, 1):
                px, py = (side * (width / 2 + 0.30), y) if direction in ("n", "s") else (x, side * (width / 2 + 0.30))
                beam(collection, "scaffold_upright", (px, py, 0.04), (px, py, height * 0.74), 0.07, "wood", bevel=0.012)
        if state == "damaged":
            for d in (0.38, 1.12):
                if d >= extent:
                    continue
                x, y = endpoint(direction, d)
                beam(collection, "bent_rebar", (x, y, footing + core_height - 0.07), (x + 0.12, y + 0.08, footing + core_height + 0.26), 0.045, "metal", bevel=0.008)
        if state != "active":
            for index in range(3 if state != "ruined" else 5):
                d = min(extent - 0.12, 0.31 + index * 0.24)
                x, y = endpoint(direction, d)
                px, py = (width / 2 + 0.30, y) if direction in ("n", "s") else (x, width / 2 + 0.30)
                size = (0.24, 0.19, 0.15) if index % 2 else (0.17, 0.26, 0.14)
                box(collection, "fallen_concrete", (px, py, size[2] / 2), size, "concrete_light" if index % 2 else "stone", bevel=0.026, rotation=(0, 0, index * 0.24))
    pier_height = footing + core_height
    box(collection, "junction_pylon", (0, 0, pier_height / 2), (width + 0.22, width + 0.22, pier_height), "concrete_light", bevel=0.055)
    if state == "active":
        box(collection, "pylon_crown", (0, 0, pier_height + 0.07), (width + 0.34, width + 0.34, 0.14), "metal_light", bevel=0.025)
        if level >= 9:
            for side in (-1, 1):
                box(collection, "pylon_armor", (side * (width / 2 + 0.13), 0, pier_height * 0.57), (0.08, width + 0.28, pier_height * 0.42), "metal", bevel=0.014)
        if level == 10:
            box(collection, "heavy_pylon_crown", (0, 0, pier_height + 0.21), (width + 0.49, width + 0.49, 0.15), "metal", bevel=0.025)


def add_modern_wall(collection, shape, state, level):
    """A luminous, decorated late-game barrier distinct from exposed concrete."""
    dirs = SHAPES[shape] or ("n", "s")
    extent = 0.82 if shape == "single" else FOOTPRINT / 2
    height = {11: 2.25, 12: 2.27, 13: 2.35}[level]
    width = {11: 0.72, 12: 0.78, 13: 0.84}[level]
    core_height = height * {"active": 1.0, "construction": 0.46, "damaged": 0.43, "ruined": 0.15}[state]
    footing = 0.13
    for direction in dirs:
        vertical = direction in ("n", "s")
        segment_box(collection, "steel_footing", direction, extent, width + 0.18, footing, "steel_blue", footing / 2, bevel=0.025)
        segment_box(collection, "reinforced_concrete_core", direction, extent, width, core_height, "concrete", footing + core_height / 2 - 0.01, bevel=0.055)
        if state in ("active", "damaged"):
            panel_count = 4 if state == "active" else 2
            for index in range(panel_count):
                d = 0.18 + index * (extent - 0.22) / 4
                x, y = endpoint(direction, d)
                for side in (-1, 1):
                    outer = side * (width / 2 + 0.038)
                    pos = (outer, y, footing + core_height * 0.58) if vertical else (x, outer, footing + core_height * 0.58)
                    size = (0.11, (extent - 0.22) / 4 * 0.86, core_height * 0.69) if vertical else ((extent - 0.22) / 4 * 0.86, 0.11, core_height * 0.69)
                    box(collection, "porcelain_armor_plate", pos, size, "porcelain_armor", bevel=0.031)
                    if state == "active":
                        # Recessed dark insert and cyan diagnostic lens form a readable tech motif.
                        outer2 = side * (width / 2 + 0.102)
                        lens_pos = (outer2, y, footing + height * 0.69) if vertical else (x, outer2, footing + height * 0.69)
                        lens_size = (0.028, size[1] * 0.46, 0.10) if vertical else (size[0] * 0.46, 0.028, 0.10)
                        box(collection, "diagnostic_recess", lens_pos, lens_size, "steel_blue", bevel=0.009)
                        lens_pos = (outer2 + side * 0.015, y, footing + height * 0.69) if vertical else (x, outer2 + side * 0.015, footing + height * 0.69)
                        box(collection, "electronics_lens", lens_pos, (0.018, lens_size[1] * 0.73, 0.055) if vertical else (lens_size[0] * 0.73, 0.018, 0.055), "teal_glow", bevel=0.007)
                        outer3 = side * (width / 2 + 0.121)
                        strip_pos = (outer3, y, footing + height * 0.47) if vertical else (x, outer3, footing + height * 0.47)
                        strip_size = (0.024, size[1] * 0.18, core_height * 0.23) if vertical else (size[0] * 0.18, 0.024, core_height * 0.23)
                        box(collection, "electronics_light_strip", strip_pos, strip_size, "teal_glow", bevel=0.008)
                        trim_pos = (outer3, y, footing + height * 0.25) if vertical else (x, outer3, footing + height * 0.25)
                        trim_size = (0.024, size[1] * 0.68, 0.045) if vertical else (size[0] * 0.68, 0.024, 0.045)
                        box(collection, "copper_panel_trim", trim_pos, trim_size, "copper_trace", bevel=0.007)
            if state == "active":
                segment_box(collection, "steel_upper_rail", direction, extent, width + 0.10, 0.15, "steel_blue", footing + height + 0.045, bevel=0.031)
                segment_box(collection, "pearl_coping", direction, extent, width + 0.20, 0.065, "pearl_edge", footing + height + 0.15, bevel=0.019)
                segment_box(collection, "luminous_crown_seam", direction, extent, width + 0.24, 0.028, "teal_glow", footing + height + 0.201, bevel=0.006)
                if level >= 12:
                    segment_box(collection, "reinforced_beam_crown", direction, extent, width + 0.31, 0.12, "metal_light", footing + height + 0.25, bevel=0.023)
                if level == 13:
                    segment_box(collection, "ceremonial_armor_spine", direction, extent, width + 0.09, 0.10, "porcelain_armor", footing + height + 0.24, bevel=0.026)
                for d in (0.52, 1.28):
                    if d >= extent:
                        continue
                    x, y = endpoint(direction, d)
                    for side in (-1, 1):
                        outer = side * (width / 2 + 0.092)
                        pos = (outer, y, footing + height * 0.37) if vertical else (x, outer, footing + height * 0.37)
                        size = (0.026, 0.055, height * 0.33) if vertical else (0.055, 0.026, height * 0.33)
                        box(collection, "copper_circuit_inlay", pos, size, "copper_trace", bevel=0.006)
                for d in (0.48, 1.30):
                    if d >= extent:
                        continue
                    x, y = endpoint(direction, d)
                    for side in (-1, 1):
                        outer = side * (width / 2 + 0.14)
                        pos = (outer, y, footing + height * 0.47) if vertical else (x, outer, footing + height * 0.47)
                        rotation = (math.pi / 4, 0, 0) if vertical else (0, math.pi / 4, 0)
                        box(collection, "ornate_steel_badge", pos, (0.038, 0.28, 0.28) if vertical else (0.28, 0.038, 0.28), "steel_blue", bevel=0.015, rotation=rotation)
                        pos = (outer + side * 0.028, y, footing + height * 0.47) if vertical else (x, outer + side * 0.028, footing + height * 0.47)
                        box(collection, "badge_teal_inlay", pos, (0.025, 0.13, 0.13) if vertical else (0.13, 0.025, 0.13), "teal_glow", bevel=0.008, rotation=rotation)
        if state == "construction":
            # Core is under half height; exposed frame and unmounted armour show assembly order.
            for d in (0.40, 1.16):
                if d >= extent:
                    continue
                x, y = endpoint(direction, d)
                beam(collection, "unclad_steel_upright", (x, y, footing + core_height - 0.03), (x, y, footing + height * 0.76), 0.07, "steel_blue", bevel=0.013)
                px, py = (width / 2 + 0.31, y) if vertical else (x, width / 2 + 0.31)
                box(collection, "unmounted_armor_plate", (px, py, 0.08), (0.22, 0.35, 0.16), "porcelain_armor", bevel=0.022)
        if state == "damaged":
            for d in (0.44, 1.14):
                if d >= extent:
                    continue
                x, y = endpoint(direction, d)
                beam(collection, "buckled_steel_frame", (x, y, footing + core_height - 0.04), (x + 0.12, y + 0.06, footing + core_height + 0.21), 0.07, "steel_blue", bevel=0.012)
        if state != "active":
            for index in range(4 if state != "ruined" else 6):
                d = min(extent - 0.12, 0.27 + index * 0.23)
                x, y = endpoint(direction, d)
                px, py = (width / 2 + 0.30, y) if vertical else (x, width / 2 + 0.30)
                box(collection, "fallen_armor", (px, py, 0.075), (0.22, 0.18, 0.15), "porcelain_armor" if index % 2 else "steel_blue", bevel=0.024, rotation=(0, 0, index * 0.22))
    pier_height = footing + core_height
    box(collection, "sculpted_steel_pylon", (0, 0, pier_height / 2), (width + 0.22, width + 0.22, pier_height), "steel_blue", bevel=0.07)
    if state == "active":
        bridge_z = footing + height + (0.20 if level == 11 else 0.28)
        box(collection, "junction_top_bridge", (0, 0, bridge_z), (width + 0.68, width + 0.68, 0.12), "porcelain_armor", bevel=0.035)
        for side in (-1, 1):
            box(collection, "pylon_armor_wing", (side * (width / 2 + 0.11), 0, pier_height * 0.59), (0.11, width + 0.30, pier_height * 0.63), "porcelain_armor", bevel=0.03)
        box(collection, "pylon_copper_collar", (0, 0, pier_height * 0.70), (width + 0.43, width + 0.43, 0.07), "copper_trace", bevel=0.012)
        box(collection, "pylon_pearl_cap", (0, 0, pier_height + 0.08), (width + 0.50, width + 0.50, 0.15), "pearl_edge", bevel=0.035)
        cylinder(collection, "electronics_beacon", (0, 0, pier_height + 0.20), 0.11, 0.13, "teal_glow", vertices=6)
        if level >= 12:
            box(collection, "double_crown", (0, 0, pier_height + 0.23), (width + 0.67, width + 0.67, 0.10), "porcelain_armor", bevel=0.028)
        if level == 13:
            cylinder(collection, "super_mechanism_housing", (0, 0, pier_height + 0.25), 0.21, 0.13, "steel_blue", vertices=8)
            cylinder(collection, "super_mechanism_core", (0, 0, pier_height + 0.31), 0.095, 0.07, "teal_glow", vertices=6)


def add_wall(collection, kit_id, shape, state, level=1):
    if kit_id == "wooden_wall":
        add_defensive_wood_wall(collection, shape, state, level)
        return
    if kit_id == "stone_wall":
        add_defensive_stone_wall(collection, shape, state, level)
        return
    if kit_id == "concrete_wall":
        add_defensive_concrete_wall(collection, shape, state, level)
        return
    if kit_id == "modern_wall":
        add_modern_wall(collection, shape, state, level)
        return
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


def asset_name(kit_id, shape, state, level=1):
    return f"{kit_id}_l{level:02d}_{shape}_{state}" if kit_id in ("wooden_wall", "stone_wall", "concrete_wall", "modern_wall") else f"{kit_id}_{shape}_{state}"


def build_asset(kit_id, shape, state, level=1):
    name = asset_name(kit_id, shape, state, level)
    collection = bpy.data.collections.new(name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[name] = collection
    base_tile(collection)
    if KITS[kit_id]["kind"] == "road":
        add_road(collection, kit_id, shape, state)
    else:
        add_wall(collection, kit_id, shape, state, level)
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


def export_asset(kit_id, shape, state, level=1):
    name = asset_name(kit_id, shape, state, level)
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
    assert triangles < (24000 if kit_id == "modern_wall" else 18000 if kit_id in ("stone_wall", "concrete_wall") else 9000 if kit_id == "wooden_wall" else 6500), (name, triangles)
    family_dir = OUT_DIR / kit_id
    os.makedirs(blender_path(family_dir), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=blender_path(family_dir / f"{name}{'_LOD0' if kit_id in ('wooden_wall', 'stone_wall', 'concrete_wall', 'modern_wall') else ''}.glb"),
        export_format="GLB",
        use_selection=True,
        use_active_scene=True,
    )
    if kit_id in ("wooden_wall", "stone_wall", "concrete_wall", "modern_wall"):
        original = [obj for obj in COLLECTIONS[name].all_objects if obj.type == "MESH"]
        lod_omissions = (("LOD1", ("grass_tuft", "rope_collar", "pointed_crown")), ("LOD2", ("grass_tuft", "rope_collar", "pointed_crown", "fallen_timber", "plank_shield", "grounded_brace"))) if kit_id == "wooden_wall" else (("LOD1", ("grass_tuft", "fallen_concrete", "steel_anchor")), ("LOD2", ("grass_tuft", "fallen_concrete", "steel_anchor", "concrete_panel", "reinforced_concrete_panel", "bent_rebar"))) if kit_id == "concrete_wall" else (("LOD1", ("grass_tuft", "brick_facing", "fallen_masonry")), ("LOD2", ("grass_tuft", "brick_facing", "fallen_masonry", "stone_facing", "parapet_merlon", "steel_clamp")))
        if kit_id == "modern_wall":
            lod_omissions = (("LOD1", ("grass_tuft", "copper_circuit_inlay", "copper_panel_trim", "fallen_armor")), ("LOD2", ("grass_tuft", "copper_circuit_inlay", "copper_panel_trim", "fallen_armor", "diagnostic_recess", "electronics_lens", "electronics_light_strip", "badge_teal_inlay", "unmounted_armor_plate", "electronics_beacon")))
        for lod, omit in lod_omissions:
            for obj in original:
                obj.select_set(not any(token in obj.name for token in omit))
            bpy.ops.export_scene.gltf(filepath=blender_path(family_dir / f"{name}_{lod}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)
        for obj in original:
            obj.select_set(True)
    SCENE.render.filepath = blender_path(family_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    REPORT[kit_id][name] = {
        "shape": shape,
        "state": state,
        "level": level,
        "triangles": triangles,
        "objects": objects,
        "png": f"{name}.png",
        "glb": f"{name}{'_LOD0' if kit_id in ('wooden_wall', 'stone_wall', 'concrete_wall', 'modern_wall') else ''}.glb",
    }


def save_family_manifest(kit_id):
    family_dir = OUT_DIR / kit_id
    sample_name = asset_name(kit_id, "cross", "active", 3 if kit_id == "wooden_wall" else 7 if kit_id == "stone_wall" else 10 if kit_id == "concrete_wall" else 13 if kit_id == "modern_wall" else 1)
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
        "levels": list(WOOD_LEVELS if kit_id == "wooden_wall" else STONE_LEVELS if kit_id == "stone_wall" else CONCRETE_LEVELS if kit_id == "concrete_wall" else MODERN_LEVELS if kit_id == "modern_wall" else (1,)),
        "shapes": list(SHAPES.keys()),
        "states": list(STATES),
        "materials": KITS[kit_id]["materials"],
        "assets": REPORT[kit_id],
    }
    if kit_id in ("wooden_wall", "stone_wall", "concrete_wall", "modern_wall"):
        spec_path = ROOT / "docs" / "assets" / "specs" / "roads" / f"{kit_id}.json"
        manifest["lod_policy"] = json.loads(Path(blender_path(spec_path)).read_text(encoding="utf-8"))["lod_policy"]
        for name, item in manifest["assets"].items():
            records = []
            for lod in ("LOD0", "LOD1", "LOD2"):
                filename = f"{name}_{lod}.glb"
                data = Path(blender_path(family_dir / filename)).read_bytes()
                json_size, _ = struct.unpack_from("<II", data, 12)
                glb = json.loads(data[20 : 20 + json_size])
                triangles = sum(glb["accessors"][primitive["indices"]]["count"] // 3 for mesh in glb.get("meshes", ()) for primitive in mesh["primitives"] if "indices" in primitive)
                records.append({"name": lod, "glb": filename, "triangles": triangles})
            item["lods"] = records
    write_json_lf(family_dir / "manifest.json", manifest)


def generate(output_dir=None, kits=None, reuse_wood_level_one=False, levels=None, shapes=None, states=None, preview=False):
    global OUT_DIR, CURRENT_KIT
    OUT_DIR = Path(output_dir or ROADS_DIR)
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)
    setup_scene()
    selected = kits or list(KITS.keys())
    for kit_id in selected:
        CURRENT_KIT = kit_id
        REPORT[kit_id] = {}
        os.makedirs(blender_path(OUT_DIR / kit_id), exist_ok=True)
        for level in (levels or (WOOD_LEVELS if kit_id == "wooden_wall" else STONE_LEVELS if kit_id == "stone_wall" else CONCRETE_LEVELS if kit_id == "concrete_wall" else MODERN_LEVELS if kit_id == "modern_wall" else (1,))):
            for shape in (shapes or SHAPES):
                for state in (states or STATES):
                    collection = build_asset(kit_id, shape, state, level)
                    name = asset_name(kit_id, shape, state, level)
                    family_dir = OUT_DIR / kit_id
                    outputs = [family_dir / f"{name}.png"] + [family_dir / f"{name}_{lod}.glb" for lod in ("LOD0", "LOD1", "LOD2")]
                    if kit_id == "wooden_wall" and level == 1 and reuse_wood_level_one and all(Path(blender_path(path)).exists() for path in outputs):
                        meshes = [obj for obj in collection.all_objects if obj.type == "MESH"]
                        triangles = 0
                        for obj in meshes:
                            obj.data.calc_loop_triangles()
                            triangles += len(obj.data.loop_triangles)
                        REPORT[kit_id][name] = {"shape": shape, "state": state, "level": level, "triangles": triangles, "objects": len(meshes), "png": f"{name}.png", "glb": f"{name}_LOD0.glb"}
                    else:
                        if preview:
                            show_only(name)
                            SCENE.render.filepath = blender_path(family_dir / f"{name}.png")
                            bpy.ops.render.render(write_still=True)
                            REPORT[kit_id][name] = {"shape": shape, "state": state, "level": level, "png": f"{name}.png"}
                        else:
                            export_asset(kit_id, shape, state, level)
        if not preview:
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
                    mesh = obj.data if obj.type == "MESH" else None
                    if obj.type == "MESH":
                        obj.data.calc_loop_triangles()
                        triangles += len(obj.data.loop_triangles)
                        bm = bmesh.new()
                        bm.from_mesh(obj.data)
                        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
                        assert all(edge.is_manifold for edge in bm.edges), (name, obj.name)
                        bm.free()
                    bpy.data.objects.remove(obj, do_unlink=True)
                    if mesh is not None and mesh.users == 0:
                        bpy.data.meshes.remove(mesh)
                for material in list(bpy.data.materials):
                    if material.users == 0:
                        bpy.data.materials.remove(material)
                assert triangles == info["triangles"], (name, triangles, info["triangles"])
                results.append({"asset": name, "triangles": triangles, "nonmanifold_edges": 0})
            write_json_lf(family_dir / "roundtrip-validation.json", results)
            print(f"Roundtrip validated {len(results)} {kit_id} assets")
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa_scene)


if __name__ == "__main__":
    generate()
    validate_roundtrip()
