"""Generate Blender mid-poly models for Real City mine levels 1-12."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
BLENDER_TOOLS_DIR = ROOT / "tools" / "assets" / "blender"
if str(BLENDER_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(BLENDER_TOOLS_DIR))

from real_city.components import industry as industry_components
from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation

OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "mine"
BLEND_PATH = OUT_DIR / "mine_levels.blend"
GLB_PATH = OUT_DIR / "mine_levels.glb"
REPORT_PATH = OUT_DIR / "generation-report.json"
ROUNDTRIP_PATH = OUT_DIR / "roundtrip-validation.json"
STATES = ("active", "construction", "damaged")
LEVELS = range(1, 13)
MINE_XY_SCALE = 1.10
MINE_Z_SCALE = 1.02

spec = importlib.util.spec_from_file_location("housing_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def add_material(role: str, color, roughness: float = 0.78, metallic: float = 0.0, emission=None, emission_strength: float = 0.0):
    mat = bpy.data.materials.new("MAT_mine_" + role)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = shader(mat)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (*color, 1)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if emission is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    H.MATS[role] = mat
    return mat


def palette():
    H.palette()
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_housing_"):
            material.name = material.name.replace("MAT_housing_", "MAT_mine_base_")
    # Keep terrain close to the existing building ground palette.
    H.MATS["grass"].diffuse_color = (0.26, 0.48, 0.08, 1)
    bsdf = shader(H.MATS["grass"])
    if bsdf and "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (0.26, 0.48, 0.08, 1)
    add_material("rock_warm", (0.42, 0.40, 0.34), 0.88)
    add_material("rock_light", (0.60, 0.58, 0.49), 0.84)
    add_material("slate_dark", (0.075, 0.080, 0.075), 0.92)
    add_material("cave_mid", (0.115, 0.120, 0.105), 0.93)
    add_material("cave_wall", (0.205, 0.195, 0.165), 0.92)
    add_material("cave_floor", (0.160, 0.135, 0.095), 0.94)
    add_material("cave_far", (0.020, 0.023, 0.021), 0.96)
    add_material("coal", (0.030, 0.028, 0.026), 0.86)
    add_material("rail_iron", (0.31, 0.32, 0.30), 0.48, 0.35)
    add_material("copper_hint", (0.68, 0.34, 0.15), 0.54, 0.25)
    add_material("rope", (0.68, 0.45, 0.20), 0.86)
    add_material("lamp_amber", (1.00, 0.56, 0.16), 0.44, 0.0, (1.0, 0.40, 0.10), 0.24)
    add_material("fuel_red", (0.62, 0.10, 0.07), 0.64, 0.1)
    add_material("dust", (0.50, 0.39, 0.25), 0.95)
    add_material("brick_red", (0.58, 0.22, 0.13), 0.82)
    add_material("concrete", (0.54, 0.56, 0.52), 0.88)
    add_material("reinforced_concrete", (0.42, 0.44, 0.43), 0.82)
    add_material("steel_light", (0.58, 0.61, 0.58), 0.45, 0.45)
    add_material("brass", (0.82, 0.54, 0.22), 0.48, 0.35)
    add_material("protective_plate", (0.26, 0.29, 0.29), 0.52, 0.55)
    add_material("explosive_red", (0.70, 0.12, 0.08), 0.58, 0.04)
    add_material("premium_wood", (0.70, 0.45, 0.22), 0.70)
    add_material("crystal_amethyst", (0.55, 0.27, 0.92), 0.22, 0.0, (0.45, 0.16, 0.95), 0.55)
    add_material("glass_cyan", (0.42, 0.76, 0.86), 0.20, 0.0, (0.20, 0.55, 0.65), 0.12)
    aliases = {
        "wood_dark": "beam",
        "wood_beam": "wood",
        "wood_pale": "wood",
        "elite_plank": "premium_wood",
        "elite_plank_highlight": "premium_wood",
        "stone_light": "rock_light",
        "stone_shadow": "rock_warm",
        "stone_block": "rock_light",
        "brick_warm": "brick_red",
        "brick_light": "brick_red",
        "metal_worn": "rail_iron",
        "dark_metal": "protective_plate",
        "armor": "protective_plate",
        "steel_light": "steel_light",
        "copper": "copper_hint",
        "window_warm": "lamp_amber",
        "earth_warm": "dust",
        "soil": "cave_floor",
        "damage_char": "char",
        "damage_crack": "slate_dark",
        "moss": "grass",
        "amethyst": "crystal_amethyst",
        "runic_glow": "crystal_amethyst",
    }
    for alias, source in aliases.items():
        if source in H.MATS:
            H.MATS[alias] = H.MATS[source]


def cylinder(name, center, radius, depth, role, axis=(0, 0, 1), segments=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=depth)
    mesh = bpy.data.meshes.new(H.PREFIX + "_" + name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    H.COL.objects.link(obj)
    mesh.materials.append(H.MATS[role])
    obj.location = center
    obj.rotation_euler = Vector(axis).to_track_quat("Z", "Y").to_euler()
    return obj


def frustum(name, cx, cy, z, rx, ry, height, top_scale, role, rings=4, segments=28, wobble=0.03):
    verts, faces = [], []
    for ring in range(rings):
        t = ring / (rings - 1)
        scale = 1 + (top_scale - 1) * t
        for i in range(segments):
            angle = math.tau * i / segments
            wave = 1 + wobble * math.sin(angle * 3.0 + t * 1.7)
            verts.append((cx + rx * scale * math.cos(angle) * wave, cy + ry * scale * math.sin(angle), z + height * t))
    for ring in range(rings - 1):
        for i in range(segments):
            a = ring * segments + i
            b = ring * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range((rings - 1) * segments, rings * segments)))
    obj = H.mesh(name, verts, faces, role)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def jagged_rock(name, x, y, z, rx, ry, height, role, *, segments=7, top_scale=0.22, twist=0.0, lean=(0.0, 0.0)):
    verts, faces = [], []
    rings = (0.0, 0.46, 0.80, 1.0)
    for ring_index, t in enumerate(rings):
        scale = 1.0 + (top_scale - 1.0) * t
        cx = x + lean[0] * t
        cy = y + lean[1] * t
        for i in range(segments):
            angle = math.tau * i / segments + twist * t
            uneven = 0.84 + 0.22 * ((i * 37 + ring_index * 13) % 5) / 4.0
            verts.append((cx + rx * scale * math.cos(angle) * uneven, cy + ry * scale * math.sin(angle) * uneven, z + height * t))
    for ring in range(len(rings) - 1):
        for i in range(segments):
            a = ring * segments + i
            b = ring * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range((len(rings) - 1) * segments, len(rings) * segments)))
    obj = H.mesh(name, verts, faces, role)
    return obj


def mine_arch_variant(level):
    if level <= 2:
        return "wood"
    if level <= 4:
        return "stone"
    if level == 5:
        return "brick"
    if level <= 7:
        return "metal"
    if level <= 10:
        return "reinforced_concrete"
    return "crystal_reinforced"


def ground(level):
    H.base()
    H.box("mine_yard_gravel", (0, -0.04, 0.09), (2.88, 2.34, 0.06), "rock_warm", 0.035, rotation=(0, 0, 0.025))
    H.box("front_work_path", (0, -1.08, 0.14), (1.72, 0.36, 0.045), "dust", 0.02, rotation=(0, 0, -0.04))
    for i, (x, y, s) in enumerate(((-1.16, 0.62, 0.18), (1.22, 0.48, 0.20), (-1.28, -0.40, 0.13), (1.12, -0.74, 0.14))):
        frustum(f"yard_rock_{i+1}", x, y, 0.13, s, s * 0.72, s * 0.56, 0.22, "rock_light", rings=3, segments=12, wobble=0.055)
    for offset in (-0.13, 0.13):
        H.box("cart_track_rail", (offset, -0.79, 0.185), (0.055, 1.34, 0.045), "rail_iron", 0.008, rotation=(0, 0, -0.03))
    for i in range(5):
        H.box("cart_track_sleeper", (0, -1.34 + i * 0.23, 0.155), (0.52, 0.07, 0.045), "wood", 0.008, rotation=(0, 0, 0.04 if i % 2 else -0.02))
    for obj in H.COL.objects:
        obj["ground"] = True


def copy_ground(active):
    for original in active.objects:
        if original.get("ground"):
            obj = original.copy()
            obj.data = original.data.copy()
            obj.name = original.name.replace("_active", "_" + H.PREFIX.rsplit("_", 1)[-1])
            H.COL.objects.link(obj)


def cave_depth(level, width, height, y, damaged=False, construction=False):
    if construction:
        depth_layers = (
            (0.12, width * 0.82, height * 0.74, "slate_dark"),
            (0.36, width * 0.58, height * 0.54, "cave_far"),
        )
    else:
        depth_layers = (
            (0.04, width * 0.92, height * 0.86, "cave_mid"),
            (0.30, width * 0.70, height * 0.66, "slate_dark"),
            (0.58, width * 0.46, height * 0.44, "cave_far"),
        )
    for idx, (dy, w, h, role) in enumerate(depth_layers):
        H.box(
            f"deep_tunnel_plane_{idx+1}",
            (0, y + dy, 0.22 + h * 0.50),
            (w, 0.075, h),
            role,
            0.030,
        )
    for idx, dy in enumerate((0.02, 0.26, 0.50)):
        if construction and idx == 2:
            continue
        h = height * (0.72 - idx * 0.14)
        half = width * (0.46 - idx * 0.07)
        z_mid = 0.22 + h * 0.50
        role = "char" if damaged and idx == 0 else "slate_dark"
        H.box(f"tunnel_left_wall_{idx+1}", (-half - 0.055, y + dy, z_mid), (0.11, 0.16, h), role, 0.020)
        H.box(f"tunnel_right_wall_{idx+1}", (half + 0.055, y + dy, z_mid), (0.11, 0.16, h), role, 0.020)
        H.box(f"tunnel_roof_band_{idx+1}", (0, y + dy, 0.22 + h + 0.03), (half * 2 + 0.26, 0.15, 0.095), role, 0.020)
    H.box("tunnel_floor", (0, y + 0.22, 0.155), (width * 0.72, 0.76, 0.050), "cave_floor" if not damaged else "slate_dark", 0.018)
    H.box("visible_cave_mouth_floor", (0, y - 0.30, 0.170), (width * 0.70, 0.34, 0.055), "cave_floor" if not damaged else "slate_dark", 0.018)
    for offset in (-0.12, 0.12):
        H.box("front_mouth_rail", (offset, y - 0.32, 0.225), (0.040, 0.42, 0.036), "rail_iron", 0.006, rotation=(0, 0, -0.025))
    for side in (-1, 1):
        H.beam(
            "visible_cave_side_recede",
            (side * width * 0.39, y - 0.34, 0.24),
            (side * width * 0.22, y + 0.42, height * 0.58),
            0.045,
            "cave_wall" if not damaged else "slate_dark",
        )
        H.beam(
            "visible_cave_roof_recede",
            (side * width * 0.33, y - 0.32, height * 0.88),
            (side * width * 0.18, y + 0.36, height * 0.68),
            0.040,
            "cave_wall" if not damaged else "slate_dark",
        )
    for offset in (-0.09, 0.09):
        H.box("inner_tunnel_rail", (offset, y + 0.17, 0.215), (0.038, 0.92, 0.034), "rail_iron", 0.006, rotation=(0, 0, -0.025))
    if not damaged:
        for x in (-width * 0.27, width * 0.27):
            H.beam("deep_lamp_hook", (x, y + 0.18, height * 0.60), (x, y + 0.15, height * 0.72), 0.014, "rail_iron")
            cylinder("deep_tunnel_lamp", (x, y + 0.13, height * 0.55), 0.042, 0.060, "lamp_amber", segments=10)


def portal_arch(level, damaged=False, construction=False):
    level_growth = 1.0 + (level - 1) * 0.015
    width = 1.24 + 0.045 * level
    height = 1.02 * level_growth
    y = -0.18
    role = "char" if damaged else "beam"
    rock_role = "rock_warm" if not damaged else "slate_dark"
    rock_height = 1.12 * level_growth
    rock_rx = 1.47 + min(level, 8) * 0.035
    rock_ry = 0.78 + min(level, 8) * 0.022
    front_y = y - 0.58
    frustum("compact_shattered_rock_mass", 0, y + 0.34, 0.12, rock_rx, rock_ry, rock_height, 0.48, rock_role, rings=6, segments=18, wobble=0.115)
    for i, (x, z, sx, sz) in enumerate(((-0.96, 0.48, 0.28, 0.42), (-0.68, 0.86, 0.24, 0.36), (0.82, 0.54, 0.30, 0.46), (0.50, 0.98, 0.22, 0.32))):
        jagged_rock(
            f"visible_sharp_rock_chunk_{i+1}",
            x,
            y + 0.02 + 0.05 * i,
            z,
            sx,
            sx * 0.70,
            sz * (1.04 + level * 0.005),
            rock_role,
            segments=7 + (i % 2),
            top_scale=0.20 + 0.03 * (i % 2),
            twist=0.35 - i * 0.12,
            lean=(0.06 * (-1 if x < 0 else 1), 0.02 * i),
        )
    extra_count = min(4 + level // 2, 10)
    for i in range(extra_count):
        side = -1 if i % 2 == 0 else 1
        px = side * (0.42 + 0.12 * (i % 4))
        py = y + 0.10 + 0.08 * (i % 3)
        pz = 0.70 + 0.07 * (i % 4)
        jagged_rock(
            f"angular_face_chip_{i:02d}",
            px,
            py,
            pz,
            0.11 + 0.012 * level,
            0.08 + 0.006 * level,
            0.24 + 0.018 * min(level, 8),
            "rock_light" if i % 3 == 0 and not damaged else rock_role,
            segments=6,
            top_scale=0.12,
            twist=0.50 + i * 0.15,
            lean=(side * 0.05, 0.02),
        )
    for i, side in enumerate((-1, 1)):
        jagged_rock(
            f"front_blade_rock_{i}",
            side * (0.72 + min(level, 8) * 0.012),
            front_y + 0.22,
            0.23,
            0.18 + min(level, 8) * 0.010,
            0.11,
            0.54 + min(level, 10) * 0.020,
            "rock_light" if not damaged else "slate_dark",
            segments=6,
            top_scale=0.10,
            twist=side * 0.42,
            lean=(side * 0.07, -0.02),
        )
    for i, x in enumerate((-0.42, -0.10, 0.24, 0.56)):
        if i > 1 and level < 4:
            continue
        jagged_rock(
            f"upper_sharp_crown_{i}",
            x,
            y + 0.42 + 0.02 * i,
            rock_height * (0.86 + 0.02 * (i % 2)),
            0.12 + 0.010 * min(level, 8),
            0.08,
            0.34 + 0.015 * min(level, 8),
            rock_role,
            segments=6,
            top_scale=0.08,
            twist=0.30 + i * 0.20,
            lean=(0.03 * (-1 if x < 0 else 1), 0.04),
        )
    cave_depth(level, width, height, y - 0.07, damaged=damaged, construction=construction)
    # One outside arch frames a visible cave cavity; do not add a smaller inner arch.
    front_w = width * (0.72 if construction else 0.84)
    front_h = height * (0.66 if construction else 0.78)
    H.box("visible_adit_deep_void", (0, front_y, 0.30 + front_h * 0.48), (front_w * 0.98, 0.110, front_h), "cave_far", 0.035)
    H.box("visible_adit_mid_cavity", (0, front_y + 0.16, 0.29 + front_h * 0.42), (front_w * 0.76, 0.080, front_h * 0.70), "slate_dark", 0.030)
    H.box("visible_adit_floor_plane", (0, front_y - 0.03, 0.185), (front_w * 0.76, 0.22, 0.055), "cave_floor" if not damaged else "slate_dark", 0.014)
    for side in (-1, 1):
        cheek_x = side * (front_w * 0.50 + 0.07)
        H.box(
            "front_rock_cheek_cut",
            (cheek_x, front_y + 0.015, 0.34 + front_h * 0.43),
            (0.18, 0.16, front_h * 0.86),
            rock_role,
            0.026,
            rotation=(0, 0, side * 0.05),
        )
        H.beam(
            "front_visible_cave_recede",
            (side * front_w * 0.34, front_y - 0.04, 0.25),
            (side * front_w * 0.18, front_y + 0.30, front_h * 0.68),
            0.036,
            "cave_wall" if not damaged else "slate_dark",
        )
    H.box("outside_arch_threshold", (0, front_y - 0.13, 0.24), (front_w + 0.36, 0.13, 0.085), "wood" if not damaged else "char", 0.012)
    for offset in (-0.13, 0.13):
        H.box("front_visible_rail_into_void", (offset, front_y - 0.12, 0.245), (0.040, 0.45, 0.036), "rail_iron", 0.006, rotation=(0, 0, -0.020))
    if level >= 5:
        trim_role = "char" if damaged else ("brick_red" if level < 8 else "concrete")
        for side in (-1, 1):
            H.box("front_masonry_trim", (side * (front_w * 0.50 + 0.17), front_y - 0.09, 0.42 + front_h * 0.42), (0.12, 0.08, front_h * 0.80), trim_role, 0.014)
        for i in range(4):
            H.box("front_block_face", (-front_w * 0.36 + i * front_w * 0.24, front_y - 0.12, 0.30), (0.22, 0.06, 0.12), trim_role, 0.010)
    if level >= 8:
        frame_role = "char" if damaged else ("reinforced_concrete" if level >= 9 else "concrete")
        metal_role = "char" if damaged else ("steel_light" if level >= 10 else "brass")
        H.box("front_concrete_header", (0, front_y - 0.13, front_h + 0.48), (front_w + 0.64, 0.12, 0.16), frame_role, 0.018)
        for side in (-1, 1):
            H.box("front_metal_anchor_strip", (side * (front_w * 0.50 + 0.27), front_y - 0.16, 0.48 + front_h * 0.36), (0.055, 0.055, front_h * 0.70), metal_role, 0.008)
            for j in range(3):
                cylinder("front_anchor_bolt", (side * (front_w * 0.50 + 0.27), front_y - 0.205, 0.40 + j * front_h * 0.22), 0.028, 0.018, "rail_iron", axis=(0, 1, 0), segments=10)
    if level >= 10 and not construction:
        gear_role = "char" if damaged else "brass"
        cylinder("front_lift_gear", (-front_w * 0.42, front_y - 0.20, front_h + 0.30), 0.13, 0.045, gear_role, axis=(0, 1, 0), segments=18)
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            H.beam(
                "front_lift_gear_tooth",
                (-front_w * 0.42, front_y - 0.22, front_h + 0.30),
                (-front_w * 0.42 + math.cos(angle) * 0.20, front_y - 0.22, front_h + 0.30 + math.sin(angle) * 0.20),
                0.018,
                gear_role,
            )
        H.box("front_operator_lamp_box", (front_w * 0.42, front_y - 0.18, front_h + 0.23), (0.20, 0.08, 0.15), "lamp_amber" if not damaged else "slate_dark", 0.010)
    if level >= 11 and not damaged:
        cylinder("front_lightcrystal_socket", (0, front_y - 0.18, front_h + 0.42), 0.065, 0.050, "brass", segments=12)
        cylinder("front_lightcrystal_visible", (0, front_y - 0.18, front_h + 0.55), 0.060, 0.24, "crystal_amethyst", segments=6)
    arch_width = front_w + 0.42 + min(level, 9) * 0.025
    arch_height = front_h + 0.28 + min(level, 10) * 0.018
    if not construction:
        industry_components.add_mine_arch(
            "component_scaled_outer_portal",
            H.COL,
            H.MATS,
            loc=(0, front_y - 0.18, 0.18),
            width=arch_width,
            height=arch_height,
            depth=0.25 + min(level, 9) * 0.010,
            variant=mine_arch_variant(level),
            damaged=damaged,
            reinforced=level >= 6,
        )
        H.box("rock_overhang_above_outer_arch", (0, front_y + 0.05, front_h + 0.43), (front_w + 0.70, 0.30, 0.18), rock_role, 0.040)
        for side in (-1, 1):
            H.box("outer_arch_rock_cheek_touch", (side * (front_w * 0.50 + 0.20), front_y + 0.00, 0.38 + front_h * 0.36), (0.20, 0.24, front_h * 0.80), rock_role, 0.030, rotation=(0, 0, side * 0.05))
        for i, x in enumerate((-0.34, 0.34)):
            H.beam("cave_side_reinforcement_not_arch", (x, y + 0.06, 0.20), (x * 0.72, y + 0.36, height * 0.70), 0.045, "wood" if not damaged or i != 1 else "char")
    else:
        industry_components.add_mine_arch(
            "component_unfinished_outer_portal",
            H.COL,
            H.MATS,
            loc=(0, front_y - 0.18, 0.18),
            width=arch_width * 0.82,
            height=arch_height * 0.88,
            depth=0.23,
            variant=mine_arch_variant(max(1, level - 1)),
            damaged=False,
            reinforced=level >= 7,
        )
        H.box("missing_arch_section_marker", (front_w * 0.46, front_y - 0.22, front_h + 0.34), (0.42, 0.16, 0.22), "slate_dark", 0.012, rotation=(0.0, 0.0, 0.20))
        H.box("unfinished_outer_rock_cheek", (0.46, front_y + 0.02, height * 0.58), (0.28, 0.24, height * 0.62), rock_role, 0.030)
        H.beam("loose_outer_arch_post_waiting", (0.48, front_y - 0.34, 0.17), (0.98, front_y - 0.08, 0.56), 0.065, "wood")
    if level >= 2 and not construction:
        H.box("planked_threshold", (0, y - 0.40, 0.20), (width + 0.40, 0.25, 0.08), "wood" if not damaged else "char", 0.018)
        for i in range(3):
            H.beam("rope_lashing", (-width / 2 - 0.18, y - 0.25, 0.30 + i * 0.18), (width / 2 + 0.18, y - 0.25, 0.31 + i * 0.18), 0.024, "rope")
    if level >= 3:
        for x in (-0.86, 0.86):
            H.box("outer_stone_buttress", (x, front_y - 0.04, 0.40), (0.28, 0.30, 0.58 if not damaged else 0.34), "rock_light", 0.025)
        H.box("outer_stone_cap_lintel", (0, front_y - 0.12, front_h + 0.46 if not damaged else front_h * 0.72), (1.70, 0.24, 0.14), "rock_light", 0.025, rotation=(0.0, 0.0, 0.0 if not damaged else -0.18))


def coal_and_stone_piles(level, state):
    damaged = state == "damaged"
    for i, (x, y, role) in enumerate(((-1.02, -0.18, "rock_light"), (1.08, -0.20, "coal"), (0.88, -0.98, "rock_warm"))):
        frustum(f"ore_pile_{i+1}", x, y, 0.13, 0.24 + level * 0.025, 0.16 + level * 0.016, 0.17 + level * 0.025, 0.12, "slate_dark" if damaged and i == 1 else role, rings=3, segments=16, wobble=0.07)
    if level >= 2:
        H.box("rare_find_crate", (-1.20, 0.08, 0.24), (0.34, 0.25, 0.22), "wood" if not damaged else "char", 0.02, rotation=(0, 0, -0.18))
        H.box("rare_find_crate_lid", (-1.20, 0.08, 0.39), (0.39, 0.30, 0.045), "beam", 0.01, rotation=(0, 0, -0.18))
    if level >= 3:
        cylinder("fuel_barrel_body", (1.25, 0.38, 0.34), 0.16, 0.42, "fuel_red" if not damaged else "char", segments=16)
        for z in (0.20, 0.48):
            cylinder("fuel_barrel_hoop", (1.25, 0.38, z), 0.168, 0.035, "rail_iron", segments=16)
        H.box("barrel_warning_plate", (1.25, 0.215, 0.35), (0.16, 0.025, 0.11), "lamp_amber", 0.006)


def cart(level, damaged=False, construction=False):
    x, y, z = (-0.18, -1.10, 0.30)
    if construction:
        x, y = (0.74, -0.86)
    role = "char" if damaged else "wood"
    H.box("mine_cart_bin", (x, y, z), (0.52 + level * 0.04, 0.34, 0.22), role, 0.03, rotation=(0.0 if not damaged else 0.25, 0.0, -0.06))
    H.box("mine_cart_load", (x, y, z + 0.17), (0.42, 0.24, 0.08), "coal" if level >= 2 else "rock_light", 0.02, rotation=(0, 0, -0.06))
    for dx in (-0.22, 0.22):
        for dy in (-0.15, 0.15):
            cylinder("cart_wheel", (x + dx, y + dy, 0.18), 0.075, 0.05, "rail_iron", axis=(0, 1, 0), segments=14)
    if level >= 2 and not damaged:
        H.beam("cart_pull_handle", (x - 0.38, y - 0.02, 0.27), (x - 0.70, y - 0.02, 0.34), 0.035, "rail_iron")


def tools_and_lamps(level, damaged=False):
    for i, (x, y, angle) in enumerate(((1.14, -0.62, 0.45), (-1.12, -0.70, -0.28), (0.70, 0.82, 0.98))):
        H.beam("pick_handle", (x, y, 0.16), (x + 0.42 * math.cos(angle), y + 0.42 * math.sin(angle), 0.36), 0.035, "wood" if not damaged else "char")
        H.box("pick_head", (x + 0.44 * math.cos(angle), y + 0.44 * math.sin(angle), 0.37), (0.18, 0.045, 0.08), "rail_iron", 0.008, rotation=(0, 0, angle))
    for x in (-0.46, 0.46):
        H.beam("lamp_hook", (x, -0.04, 0.72), (x, -0.10, 0.86), 0.018, "rail_iron")
        cylinder("hanging_lamp", (x, -0.12, 0.67), 0.06, 0.09, "lamp_amber" if not damaged else "slate_dark", segments=10)
    if level >= 2 and not damaged:
        for x in (-0.92, 0.92):
            H.beam("yard_rope_post", (x, -1.36, 0.14), (x, -1.36, 0.58), 0.05, "beam")
        H.beam("front_safety_rope", (-0.92, -1.36, 0.53), (0.92, -1.36, 0.53), 0.028, "rope")


def stone_and_brick_reinforcement(level, damaged=False, construction=False):
    if level < 4:
        return
    side_role = "slate_dark" if damaged else ("brick_red" if level >= 5 else "rock_light")
    cap_role = "char" if damaged else ("reinforced_concrete" if level >= 9 else side_role)
    for side in (-1, 1):
        H.box(
            "side_masonry_cheek",
            (side * (0.98 + level * 0.025), -0.10, 0.56),
            (0.22, 0.42, 0.74 if not damaged else 0.44),
            side_role,
            0.030,
            rotation=(0, 0, side * 0.04),
        )
        if level >= 8:
            H.box(
                "concrete_side_retainer",
                (side * 1.30, 0.20, 0.46),
                (0.24, 0.66, 0.60 if not damaged else 0.34),
                "reinforced_concrete" if level >= 9 else "concrete",
                0.028,
                rotation=(0, 0, side * 0.08),
            )
    if not construction:
        H.box("masonry_crown", (0, -0.07, 1.33 + level * 0.045), (2.18, 0.34, 0.16), cap_role, 0.024)
    for i in range(min(level - 3, 6)):
        x = -1.05 + i * 0.42
        H.box(
            "laid_stone_block_course",
            (x, -0.40, 0.26 + 0.07 * (i % 2)),
            (0.26, 0.18, 0.13),
            "rock_light" if not damaged else "slate_dark",
            0.014,
            rotation=(0, 0, -0.08 + i * 0.035),
        )


def rail_extension(level, damaged=False):
    if level < 5:
        return
    rail_role = "rail_iron"
    length = 0.65 + min(level, 10) * 0.06
    for offset in (-0.16, 0.16):
        H.box(
            "extended_front_rail",
            (offset, -1.36, 0.225),
            (0.050, length, 0.040),
            rail_role,
            0.006,
            rotation=(0.08 if damaged else 0, 0, -0.035),
        )
    for i in range(4):
        H.box(
            "front_rail_sleeper",
            (0, -1.65 + i * 0.17, 0.165),
            (0.60, 0.060, 0.045),
            "char" if damaged and i == 2 else "wood",
            0.008,
            rotation=(0, 0, 0.06 if i % 2 else -0.04),
        )


def hoist_and_mechanics(level, damaged=False, construction=False):
    if level < 6:
        return
    frame_role = "char" if damaged else ("steel_light" if level >= 9 else "rail_iron")
    wood_role = "char" if damaged else ("premium_wood" if level >= 7 else "beam")
    z_top = 1.40 + min(level, 10) * 0.055
    if not construction:
        for x in (-0.64, 0.64):
            H.beam("hoist_leg", (x, -0.55, 0.22), (x * 0.72, -0.34, z_top), 0.065, frame_role)
        H.beam("hoist_crossbar", (-0.62, -0.34, z_top), (0.62, -0.34, z_top), 0.070, frame_role)
        cylinder("hoist_winch_drum", (0, -0.48, z_top - 0.16), 0.135, 0.62, wood_role, axis=(1, 0, 0), segments=18)
        for x in (-0.38, 0.38):
            cylinder("hoist_side_wheel", (x, -0.48, z_top - 0.16), 0.20, 0.045, frame_role, axis=(1, 0, 0), segments=18)
        H.beam("hoist_drop_cable", (0, -0.48, z_top - 0.18), (0, -0.36, 0.62), 0.022, "rail_iron")
        H.box("lift_bucket", (0, -0.32, 0.50), (0.32, 0.22, 0.22), "rail_iron" if not damaged else "char", 0.020)
    else:
        H.beam("unfinished_hoist_leg_left", (-0.62, -0.55, 0.22), (-0.44, -0.36, z_top * 0.78), 0.060, frame_role)
        H.beam("unfinished_hoist_leg_right_grounded", (0.56, -0.72, 0.16), (0.94, -0.46, 0.62), 0.060, frame_role)
        H.box("packed_winch_parts", (0.15, 0.94, 0.24), (0.54, 0.32, 0.20), "rail_iron", 0.020)


def explosive_and_fuel_yard(level, damaged=False, construction=False):
    if level < 6:
        return
    count = 2 + min(level - 6, 3)
    for i in range(count):
        x = -1.22 + i * 0.18
        y = 0.62 + 0.06 * (i % 2)
        H.box(
            "explosive_crate",
            (x, y, 0.25),
            (0.22, 0.20, 0.18),
            "char" if damaged and i == 0 else "explosive_red",
            0.016,
            rotation=(0, 0, -0.20 + i * 0.09),
        )
        H.box("explosive_crate_strap", (x, y - 0.105, 0.25), (0.24, 0.020, 0.19), "rail_iron", 0.004, rotation=(0, 0, -0.20 + i * 0.09))
    if level >= 8:
        for i, x in enumerate((1.14, 1.34)):
            cylinder(
                "protected_fuel_tank",
                (x, 0.72 + i * 0.13, 0.38),
                0.135,
                0.46,
                "fuel_red" if not damaged else "char",
                segments=16,
            )
            H.box("fuel_tank_cage", (x, 0.72 + i * 0.13, 0.39), (0.34, 0.06, 0.42), "protective_plate", 0.006)


def ventilation_and_late_tech(level, damaged=False, construction=False):
    if level < 8:
        return
    pipe_role = "char" if damaged else ("brass" if level < 10 else "steel_light")
    heights = [0.86 + level * 0.035]
    if level >= 10:
        heights.append(1.05 + level * 0.035)
    for i, h in enumerate(heights):
        x = 1.02 + i * 0.27
        cylinder("vent_pipe_stack", (x, 0.10 + i * 0.24, h * 0.5 + 0.14), 0.080, h, pipe_role, segments=16)
        cylinder("vent_pipe_cap", (x, 0.10 + i * 0.24, h + 0.18), 0.125, 0.045, pipe_role, segments=16)
        H.box("vent_grille_slit", (x, -0.01 + i * 0.24, h * 0.72), (0.16, 0.022, 0.05), "slate_dark", 0.004)
    if level >= 9:
        for side in (-1, 1):
            H.box("armored_portal_plate", (side * 0.74, -0.36, 0.94), (0.20, 0.10, 0.72), "protective_plate" if not damaged else "char", 0.018)
    if level >= 10 and not construction:
        cylinder("super_mechanism_core", (-0.82, 0.58, 0.42), 0.22, 0.28, "steel_light" if not damaged else "char", segments=22)
        for angle in (0, math.tau / 3, math.tau * 2 / 3):
            H.beam(
                "super_mechanism_spoke",
                (-0.82, 0.58, 0.42),
                (-0.82 + math.cos(angle) * 0.31, 0.58 + math.sin(angle) * 0.31, 0.42),
                0.028,
                "brass" if not damaged else "char",
            )
        H.box("operator_post", (-1.08, 0.38, 0.42), (0.34, 0.30, 0.42), "reinforced_concrete" if not damaged else "slate_dark", 0.022)
    if level >= 11 and not damaged:
        for x in (-0.30, 0.30):
            cylinder("cave_crystal_socket", (x, -0.33, 0.74), 0.055, 0.070, "brass", segments=12)
            cylinder("cave_lightcrystal", (x, -0.33, 0.86), 0.055, 0.22, "crystal_amethyst", segments=6)
    if level >= 12 and not construction:
        for side in (-1, 1):
            H.box("final_protective_wing_plate", (side * 1.18, -0.26, 0.88), (0.18, 0.42, 0.82), "protective_plate" if not damaged else "char", 0.020, rotation=(0, 0, side * 0.14))


def upgrade_richness_decor(level, damaged=False, construction=False):
    if construction:
        visible_level = max(1, level - 1)
    else:
        visible_level = level
    if visible_level >= 2:
        for side in (-1, 1):
            H.box("side_rope_tie_plate", (side * 0.83, -0.62, 0.56), (0.18, 0.035, 0.10), "rope" if not damaged else "char", 0.006, rotation=(0, 0, side * 0.08))
    if visible_level >= 4:
        for row in range(2):
            for index in range(4):
                x = -0.52 + index * 0.34 + (0.08 if row else 0.0)
                H.box(
                    "front_masonry_detail_block",
                    (x, -0.88, 0.42 + row * 0.16),
                    (0.22, 0.045, 0.105),
                    "rock_light" if not damaged else "slate_dark",
                    0.008,
                    rotation=(0, 0, -0.03 + index * 0.02),
                )
    if visible_level >= 5:
        for side in (-1, 1):
            for z in (0.58, 0.78):
                H.box("iron_strap_on_arch_cheek", (side * 0.88, -0.92, z), (0.055, 0.035, 0.26), "rail_iron" if not damaged else "char", 0.004)
                cylinder("round_arch_rivet", (side * 0.88, -0.945, z + 0.10), 0.024, 0.014, "steel_light" if not damaged else "char", axis=(0, 1, 0), segments=10)
                cylinder("round_arch_rivet", (side * 0.88, -0.945, z - 0.10), 0.024, 0.014, "steel_light" if not damaged else "char", axis=(0, 1, 0), segments=10)
    if visible_level >= 7:
        for side in (-1, 1):
            H.box("premium_deck_side_trim", (side * 0.68, -1.08, 0.28), (0.44, 0.070, 0.080), "premium_wood" if not damaged else "char", 0.010, rotation=(0, 0, side * 0.06))
            H.box("copper_depth_marker", (side * 0.58, -0.98, 0.76), (0.12, 0.030, 0.20), "copper_hint" if not damaged else "char", 0.006)
    if visible_level >= 8:
        for index, x in enumerate((-0.58, -0.30, 0.30, 0.58)):
            H.box("concrete_face_capstone", (x, -0.965, 1.02 + 0.02 * (index % 2)), (0.20, 0.055, 0.09), "concrete" if not damaged else "slate_dark", 0.008)
    if visible_level >= 9:
        for side in (-1, 1):
            H.box("protected_charge_warning_panel", (side * 1.05, 0.46, 0.54), (0.20, 0.040, 0.24), "explosive_red" if not damaged else "char", 0.006, rotation=(0, 0, side * 0.12))
            for j in range(3):
                cylinder("armor_bolt_column", (side * 1.02, -0.78, 0.46 + j * 0.18), 0.026, 0.016, "steel_light" if not damaged else "char", axis=(0, 1, 0), segments=10)
    if visible_level >= 10:
        for angle in (0.0, math.tau / 4, math.tau / 2, math.tau * 3 / 4):
            H.beam(
                "super_mechanism_guard_spoke",
                (-0.82, 0.58, 0.62),
                (-0.82 + math.cos(angle) * 0.28, 0.58 + math.sin(angle) * 0.28, 0.62),
                0.018,
                "protective_plate" if not damaged else "char",
            )
    if visible_level >= 11 and not damaged:
        for side in (-1, 1):
            cylinder("small_lightcrystal_marker", (side * 0.76, -0.90, 1.10), 0.035, 0.14, "crystal_amethyst", segments=6)
    if visible_level >= 12:
        for side in (-1, 1):
            H.box("final_armor_nameplate", (side * 0.44, -1.03, 1.20), (0.26, 0.030, 0.10), "protective_plate" if not damaged else "char", 0.006, rotation=(0, 0, side * 0.04))


def construction_overlay(level):
    for x in (-1.22, -0.40, 0.40, 1.22):
        H.beam("scaffold_post", (x, -0.98, 0.12), (x, -0.98, 0.86), 0.052, "wood")
    H.beam("scaffold_top_rail", (-1.30, -0.98, 0.82), (1.30, -0.98, 0.82), 0.055, "wood")
    H.beam("scaffold_mid_rail", (-1.24, -0.98, 0.46), (1.24, -0.98, 0.46), 0.045, "wood")
    H.beam("scaffold_diag_rope", (-1.20, -0.98, 0.20), (1.18, -0.98, 0.76), 0.028, "rope")
    for i in range(5):
        H.box("upgrade_board_stack", (-0.76 + i * 0.22, 1.08, 0.16 + i * 0.025), (0.46, 0.10, 0.06), "wood", 0.012, rotation=(0, 0, 0.20 - i * 0.07))
    for i in range(3 + level):
        H.box("coiled_rope_piece", (-1.26 + i * 0.12, 0.68, 0.18 + 0.02 * (i % 2)), (0.16, 0.12, 0.055), "rope", 0.014, rotation=(0, 0, i * 0.25))
    if level >= 3:
        for i in range(4):
            H.box("unplaced_stone_block", (0.76 + i * 0.17, -0.62 + 0.04 * (i % 2), 0.16), (0.22, 0.18, 0.14), "rock_light", 0.018, rotation=(0, 0, -0.18 + i * 0.16))
        H.box("sealed_fuel_barrel_waiting", (1.22, 0.78, 0.28), (0.26, 0.26, 0.28), "fuel_red", 0.03)
    if level >= 5:
        for i in range(3):
            H.box("waiting_brick_stack", (-1.12 + i * 0.18, 0.34, 0.18 + i * 0.035), (0.24, 0.15, 0.10), "brick_red", 0.012, rotation=(0, 0, 0.10 * i))
    if level >= 8:
        for i in range(3):
            H.box("waiting_concrete_slab", (0.84 + i * 0.15, 0.94, 0.18 + i * 0.04), (0.30, 0.20, 0.08), "concrete", 0.012, rotation=(0, 0, -0.12 + i * 0.07))
    if level >= 10:
        H.box("crated_super_mechanism", (-0.90, 0.92, 0.26), (0.42, 0.32, 0.24), "steel_light", 0.020)


def damaged_overlay(level):
    H.box("fallen_lintel", (0.32, -0.24, 0.44), (0.86, 0.17, 0.13), "char", 0.018, rotation=(0.26, -0.08, -0.36))
    H.box("portal_rubble_shadow", (-0.12, -0.14, 0.25), (0.68, 0.34, 0.18), "slate_dark", 0.035, rotation=(0.08, 0.06, 0.18))
    for i in range(10):
        role = "rock_light" if i % 2 else "char"
        H.box("fallen_mine_debris", (-0.90 + i * 0.20, -0.78 - 0.05 * (i % 2), 0.14), (0.18 + 0.03 * (i % 3), 0.12, 0.09), role, 0.012, rotation=(0.08, 0.12, i * 0.31))
    H.beam("snapped_track_left", (-0.20, -1.26, 0.19), (-0.42, -0.58, 0.26), 0.045, "rail_iron")
    H.beam("snapped_track_right", (0.18, -1.24, 0.19), (0.44, -0.62, 0.23), 0.045, "rail_iron")
    if level >= 3:
        H.box("dented_fuel_barrel", (1.26, 0.42, 0.22), (0.31, 0.22, 0.18), "char", 0.02, rotation=(0.42, 0.18, -0.30))
    if level >= 6:
        H.box("collapsed_hoist_chunk", (-0.44, -0.58, 0.34), (0.62, 0.18, 0.14), "char", 0.016, rotation=(0.30, -0.16, 0.48))
        H.beam("slack_broken_cable", (-0.20, -0.48, 0.74), (-0.80, -0.78, 0.20), 0.020, "rail_iron")
    if level >= 9:
        H.box("cracked_concrete_plate", (0.86, -0.20, 0.54), (0.46, 0.18, 0.32), "reinforced_concrete", 0.018, rotation=(0.16, -0.12, -0.34))
    if level >= 11:
        H.box("fallen_crystal_case", (-0.76, -0.86, 0.22), (0.32, 0.18, 0.12), "brass", 0.012, rotation=(0.20, 0.10, -0.28))


def scale_mine_body(collection):
    for obj in collection.objects:
        if obj.type != "MESH" or obj.get("ground"):
            continue
        obj.location.x *= MINE_XY_SCALE
        obj.location.y *= MINE_XY_SCALE
        obj.location.z *= MINE_Z_SCALE
        obj.scale.x *= MINE_XY_SCALE
        obj.scale.y *= MINE_XY_SCALE
        obj.scale.z *= MINE_Z_SCALE


def mine(level, state, active=None):
    collection = bpy.data.collections.new(f"mine_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    H.COL = collection
    H.PREFIX = collection.name
    collection["level"] = level
    collection["state"] = state
    collection["ground_source"] = f"mine_l{level:02d}_active"
    if active is None:
        ground(level)
    else:
        copy_ground(active)
    damaged = state == "damaged"
    construction = state == "construction"
    portal_arch(level, damaged=damaged, construction=construction)
    stone_and_brick_reinforcement(level, damaged=damaged, construction=construction)
    coal_and_stone_piles(level, state)
    if not construction or level >= 2:
        cart(level, damaged=damaged, construction=construction)
    rail_extension(level, damaged=damaged)
    hoist_and_mechanics(level, damaged=damaged, construction=construction)
    explosive_and_fuel_yard(level, damaged=damaged, construction=construction)
    ventilation_and_late_tech(level, damaged=damaged, construction=construction)
    upgrade_richness_decor(level, damaged=damaged, construction=construction)
    tools_and_lamps(level, damaged=damaged)
    if construction:
        construction_overlay(level)
    if damaged:
        damaged_overlay(level)
    scale_mine_body(collection)
    H.clean_meshes(collection)
    for obj in collection.objects:
        if obj.type == "MESH":
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.calc_loop_triangles()
    return collection


def hide_all(collections):
    for collection in collections:
        collection.hide_render = True
        collection.hide_viewport = True


def select_collection(collection):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        if obj.type == "MESH":
            obj.select_set(True)


def triangles(collection):
    total = 0
    for obj in collection.objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            total += len(obj.data.loop_triangles)
    return total


def bounds(collection):
    coords = [obj.matrix_world @ Vector(corner) for obj in collection.objects if obj.type == "MESH" for corner in obj.bound_box]
    return [[round(min(v[i] for v in coords), 3) for i in range(3)], [round(max(v[i] for v in coords), 3) for i in range(3)]]


def alpha_bounds(path):
    try:
        from PIL import Image
    except Exception:
        return None
    with Image.open(path) as image:
        return image.getchannel("A").getbbox()


def write_readme():
    (OUT_DIR / "README.md").write_text(
        """# Шахта

Сюда Blender-генератор сохраняет runtime-модели Шахты:

```bash
\"/mnt/d/programs/Blender/5.2/blender.exe\" --background --python tools/assets/blender/generate_mine_models.py
```

Ожидаемые файлы:

- `mine_levels.blend`;
- `mine_levels.glb`;
- `mine_l01_active.glb` ... `mine_l12_damaged.glb`;
- `mine_l01_active.png` ... `mine_l12_damaged.png`;
- `generation-report.json`;
- `roundtrip-validation.json`;
- `state-review.png`.

Runtime-карта использует PNG-спрайты `mine_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.
""",
        encoding="utf-8",
    )


def write_manifest(report):
    manifest = {
        "family": "mine",
        "displayName": "Шахта",
        "source": "mine_levels.blend",
        "combinedModel": "mine_levels.glb",
        "generator": "tools/assets/blender/generate_mine_models.py",
        "levels": list(LEVELS),
        "states": list(STATES),
        "spriteSize": [512, 384],
        "files": sorted(f"{name}.png" for name in report),
        "models": sorted(f"{name}.glb" for name in report),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contact_sheet(levels=None):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return
    rows = list(levels or LEVELS)
    sheet = Image.new("RGBA", (256 * 3, 214 * len(rows)), (35, 51, 43, 255))
    draw = ImageDraw.Draw(sheet)
    for row, level in enumerate(rows):
        for col, state in enumerate(STATES):
            name = f"mine_l{level:02d}_{state}"
            with Image.open(OUT_DIR / f"{name}.png") as image:
                thumb = image.resize((256, 192), Image.Resampling.LANCZOS)
            y = row * 214
            sheet.alpha_composite(thumb, (col * 256, y))
            draw.text((col * 256 + 10, y + 194), name, fill=(255, 255, 255, 255))
    sheet.save(OUT_DIR / "state-review.png")


def clear_previous_build():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("mine_"):
            bpy.data.objects.remove(obj)
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Mine") or scene.name.startswith("Mine_Roundtrip"):
            bpy.data.scenes.remove(scene)
    for collection in list(bpy.data.collections):
        if collection.name.startswith("mine_"):
            bpy.data.collections.remove(collection)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("mine_"):
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_mine_"):
            bpy.data.materials.remove(material)


def parse_levels(raw):
    if not raw:
        return list(LEVELS)
    selected = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = (int(value) for value in part.split("-", 1))
            selected.update(range(start, end + 1))
        else:
            selected.add(int(part))
    invalid = [level for level in sorted(selected) if level not in LEVELS]
    if invalid:
        raise ValueError(f"Unsupported mine levels: {invalid}")
    return sorted(selected)


def main(output=None, levels=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    directory = Path(output or OUT_DIR)
    selected_levels = list(levels or LEVELS)
    partial = selected_levels != list(LEVELS)
    clear_previous_build()
    scene = bpy.data.scenes.new("Real_City_Mine_Models")
    bpy.context.window.scene = scene
    palette()
    H.setup_camera(scene)
    scene["style_reference"] = "Real City bright fantasy stylized mid-poly; mine levels 1-12 from docs/buildings/industry/mine.md"
    note = bpy.data.texts.new("mine_asset_notes")
    note.write(
        "Real City mine levels 1-12, states active/construction/damaged. "
        "Visual anchor: dark adit portal, timber supports, cart rails, mine cart, stone/coal piles, lamps and ropes. "
        "Revision: the mine body fills about 95 percent of the 1x1 ground tile, the rock rises only 1-2 percent per level, "
        "has visible receding cave layers inside the portal, and uses exactly one outside arch/canopy around the adit mouth. "
        "There is no smaller second arch inside the cave; the interior remains a dark rock cavity. "
        "Costs mapped to visible materials: wood/planks -> portal supports, threshold, cart and scaffolds; rope -> lashings and safety rope; "
        "stone on level 3 -> buttresses/cap stones; gasoline on level 3 -> red fuel barrel outside the portal; "
        "stone blocks/tools on level 4 -> masonry cheeks and tool crates; bricks/iron on level 5 -> brick portal courses, rails and cart; "
        "mechanisms/explosives on level 6 -> hoist and explosive yard; copper/premium planks on level 7 -> metal wheels and upgraded decking; "
        "concrete/copper details on level 8 -> retaining slabs and ventilation; reinforced concrete/explosives on level 9 -> armored portal and protected charge crates; "
        "reinforced beams/super mechanism on level 10 -> operator post and main lift; lightcrystal on levels 11-12 -> restrained cave lighting; "
        "protective plates on level 12 -> final armored wing plates. "
        "Ground for construction/damaged is copied from the active collection of the same level. No low-poly fallback or sprite-only generation was used."
    )
    if partial and REPORT_PATH.exists():
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        report = {}
    active, collections = {}, []
    for level in selected_levels:
        for state in STATES:
            collection = mine(level, state, active.get(level))
            if state == "active":
                active[level] = collection
            hide_all(collections)
            collection.hide_render = False
            collection.hide_viewport = False
            bpy.context.view_layer.update()
            select_collection(collection)
            name = collection.name
            glb_path = directory / f"{name}.glb"
            bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True, use_active_scene=True)
            scene.render.filepath = str(directory / f"{name}.png")
            bpy.ops.render.render(write_still=True)
            tri_count = triangles(collection)
            assert 1800 <= tri_count <= 14000, (name, tri_count)
            report[name] = {
                "level": level,
                "state": state,
                "triangles": tri_count,
                "bounds": bounds(collection),
                "ground_source": collection["ground_source"],
                "style": "bright fantasy stylized mid-poly Blender",
                "alpha_bounds": alpha_bounds(directory / f"{name}.png"),
            }
            collections.append(collection)
            REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("MINE_DONE " + name, flush=True)
    hide_all(collections)
    for collection in collections:
        collection.hide_render = False
        collection.hide_viewport = False
    if partial:
        suffix = f"l{selected_levels[0]:02d}_l{selected_levels[-1]:02d}"
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / f"mine_levels_preview_{suffix}.blend"))
    else:
        bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_active_scene=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    write_readme()
    write_manifest(report)
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id="mine",
            display_name="Шахта",
            category="industry",
            output_dir=directory,
            levels=selected_levels,
            states=STATES,
            source_blend=OUT_DIR / (f"mine_levels_preview_l{selected_levels[0]:02d}_l{selected_levels[-1]:02d}.blend" if partial else BLEND_PATH.name),
            combined_glb=None if partial else GLB_PATH,
            generator="tools/assets/blender/generate_mine_models.py",
            style_reference="Real City mine migrated to shared scene/export/report layer",
        )
    )
    contact_sheet(selected_levels if partial else None)

    qa = bpy.data.scenes.new("Mine_Roundtrip_QA")
    bpy.context.window.scene = qa
    selected_names = {f"mine_l{level:02d}_{state}" for level in selected_levels for state in STATES}
    for name, entry in sorted((name, entry) for name, entry in report.items() if name in selected_names):
        bpy.ops.import_scene.gltf(filepath=str(directory / f"{name}.glb"))
        count = 0
        for obj in qa.objects:
            if obj.type != "MESH":
                continue
            obj.data.calc_loop_triangles()
            count += len(obj.data.loop_triangles)
        assert count == entry["triangles"], (name, count, entry["triangles"])
        bpy.data.batch_remove(ids=list(qa.objects))
    ROUNDTRIP_PATH.write_text(
        json.dumps(
            {"models": len(selected_levels) * len(STATES), "levels": selected_levels, "triangles_matched": True},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bpy.context.window.scene = scene
    for collection in collections:
        collection.hide_viewport = True
        collection.hide_render = True
    active[selected_levels[-1]].hide_viewport = False
    active[selected_levels[-1]].hide_render = False
    bpy.context.view_layer.update()
    print("MINE_COMPLETE " + str(len(selected_levels) * len(STATES)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--levels", help="Comma-separated levels or ranges, for example 1-3 or 1,3,12.")
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    main(args.output, parse_levels(args.levels))
