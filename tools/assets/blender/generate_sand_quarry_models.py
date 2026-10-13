"""Generate Blender mid-poly models for Real City sand quarry levels 1-11."""

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

from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "sand_quarry"
BLEND_PATH = OUT_DIR / "sand_quarry_levels.blend"
GLB_PATH = OUT_DIR / "sand_quarry_levels.glb"
REPORT_PATH = OUT_DIR / "generation-report.json"
ROUNDTRIP_PATH = OUT_DIR / "roundtrip-validation.json"
STATES = ("active", "construction", "damaged")
LEVELS = range(1, 12)

spec = importlib.util.spec_from_file_location("housing_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def add_material(role: str, color, roughness: float = 0.78, metallic: float = 0.0, emission=None, emission_strength: float = 0.0):
    mat = bpy.data.materials.new("MAT_sand_quarry_" + role)
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
    # Match the established terrain ground color used by sawmills.
    H.MATS["grass"].diffuse_color = (0.26, 0.48, 0.08, 1)
    bsdf = shader(H.MATS["grass"])
    if bsdf and "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (0.26, 0.48, 0.08, 1)
    add_material("sand", (0.82, 0.58, 0.22), 0.86)
    add_material("sand_light", (0.98, 0.77, 0.35), 0.86)
    add_material("sand_shadow", (0.50, 0.31, 0.13), 0.92)
    add_material("rope", (0.70, 0.48, 0.22), 0.84)
    add_material("metal", (0.34, 0.38, 0.37), 0.44, 0.35)
    add_material("iron", (0.42, 0.44, 0.42), 0.46, 0.45)
    add_material("steel", (0.60, 0.64, 0.60), 0.38, 0.60)
    add_material("copper", (0.84, 0.45, 0.20), 0.42, 0.45)
    add_material("brick", (0.62, 0.23, 0.12), 0.82)
    add_material("premium_wood", (0.78, 0.52, 0.22), 0.64)
    add_material("rune_tile", (0.33, 0.20, 0.48), 0.50, 0.0, (0.14, 0.08, 0.28), 0.08)
    add_material("gold", (1.00, 0.66, 0.18), 0.34, 0.70)
    add_material("blue_salt", (0.18, 0.74, 0.96), 0.34, 0.0, (0.10, 0.55, 0.90), 0.22)
    add_material("dust", (0.72, 0.61, 0.42), 0.95)
    add_material("canvas", (0.78, 0.63, 0.38), 0.82)


def cylinder(name, center, radius, depth, role, axis=(0, 0, 1), segments=14):
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


def ring_band(name, cx, cy, z, rx, ry, width, height, role, segments=36, wobble=0.025):
    verts, faces = [], []
    for layer, zz in enumerate((z, z + height)):
        for radius in (1.0, 1.0 - width):
            for i in range(segments):
                angle = math.tau * i / segments
                wave = 1 + wobble * math.sin(angle * 4.0 + layer * 0.9)
                verts.append((cx + rx * radius * math.cos(angle) * wave, cy + ry * radius * math.sin(angle), zz))
    for i in range(segments):
        n = (i + 1) % segments
        outer0, inner0 = i, segments + i
        outer1, inner1 = n, segments + n
        outer0t, inner0t = segments * 2 + i, segments * 3 + i
        outer1t, inner1t = segments * 2 + n, segments * 3 + n
        faces.append((outer0, outer1, outer1t, outer0t))
        faces.append((inner1, inner0, inner0t, inner1t))
        faces.append((outer0t, outer1t, inner1t, inner0t))
        faces.append((outer1, outer0, inner0, inner1))
    obj = H.mesh(name, verts, faces, role)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def plank_walkway(prefix, points, width=0.30, role="wood", broken=False):
    for i, (x, y, z, angle) in enumerate(points):
        if broken and i % 3 == 1:
            role_i, tilt = "char", (0.20, -0.08, angle + 0.16)
            z -= 0.10
        else:
            role_i, tilt = role, (0.02 if i % 2 else 0.0, 0.0, angle)
        H.box(prefix + "_plank", (x, y, z), (width, 0.50, 0.075), role_i, 0.014, rotation=tilt)
    if not broken:
        start = points[0]
        end = points[-1]
        H.beam(prefix + "_side_rail_a", (start[0] - 0.20, start[1] + 0.20, start[2] + 0.16), (end[0] - 0.20, end[1] + 0.20, end[2] + 0.16), 0.04, "beam")
        H.beam(prefix + "_side_rail_b", (start[0] + 0.20, start[1] - 0.20, start[2] + 0.16), (end[0] + 0.20, end[1] - 0.20, end[2] + 0.16), 0.04, "beam")


def sack(name, x, y, z, sx=0.24, sy=0.17, sz=0.18, role="dust"):
    obj = frustum(name, x, y, z, sx, sy, sz, 0.78, role, rings=4, segments=14, wobble=0.055)
    obj.rotation_euler.z = 0.20 * math.sin(x * 7.0 + y * 3.0)
    H.beam(name + "_tie", (x - sx * 0.62, y, z + sz * 0.86), (x + sx * 0.62, y, z + sz * 0.86), 0.018, "rope")
    return obj


def bucket(name, x, y, z, role="wood"):
    frustum(name + "_body", x, y, z, 0.12, 0.10, 0.18, 0.72, role, rings=3, segments=12, wobble=0.015)
    H.beam(name + "_handle", (x - 0.10, y, z + 0.18), (x + 0.10, y, z + 0.18), 0.018, "metal")


def ladder(name, x, y, z, angle, length=0.82, role="wood"):
    dx, dy = math.cos(angle) * length * 0.5, math.sin(angle) * length * 0.5
    nx, ny = -math.sin(angle) * 0.11, math.cos(angle) * 0.11
    for side in (-1, 1):
        H.beam(name + "_rail", (x - dx + nx * side, y - dy + ny * side, z), (x + dx + nx * side, y + dy + ny * side, z + 0.16), 0.035, role)
    for i in range(5):
        t = i / 4
        px, py, pz = x - dx + 2 * dx * t, y - dy + 2 * dy * t, z + 0.16 * t
        H.beam(name + "_rung", (px - nx, py - ny, pz), (px + nx, py + ny, pz), 0.026, role)


def sieve_screen(name, x, y, z, angle, damaged=False):
    role = "char" if damaged else "wood"
    H.box(name + "_frame_top", (x, y, z), (0.58, 0.055, 0.055), role, 0.01, rotation=(0.35, 0, angle))
    H.box(name + "_frame_bottom", (x, y + 0.34, z - 0.10), (0.58, 0.055, 0.055), role, 0.01, rotation=(0.35, 0, angle))
    H.box(name + "_frame_l", (x - 0.28, y + 0.17, z - 0.05), (0.055, 0.38, 0.055), role, 0.01, rotation=(0.35, 0, angle))
    H.box(name + "_frame_r", (x + 0.28, y + 0.17, z - 0.05), (0.055, 0.38, 0.055), role, 0.01, rotation=(0.35, 0, angle))
    for i in range(4):
        H.beam(name + "_wire_v", (x - 0.18 + i * 0.12, y + 0.02, z - 0.02), (x - 0.18 + i * 0.12, y + 0.32, z - 0.11), 0.010, "metal")
    for i in range(3):
        H.beam(name + "_wire_h", (x - 0.25, y + 0.09 + i * 0.09, z - 0.04 - i * 0.025), (x + 0.25, y + 0.09 + i * 0.09, z - 0.04 - i * 0.025), 0.010, "metal")


def quarry_canopy(level, state):
    if level < 2:
        return
    damaged = state == "damaged"
    post_role = "char" if damaged else "beam"
    ztop = 0.92 if level == 2 else 1.04
    for x, y in ((-1.14, 0.74), (-0.34, 0.92), (-1.02, 1.28), (-0.22, 1.46)):
        top = ztop - (0.22 if damaged and x < -0.8 else 0)
        H.beam("sorting_canopy_post", (x, y, 0.13), (x, y, top), 0.055, post_role)
    if damaged:
        H.beam("collapsed_canvas_beam", (-1.10, 0.78, 0.78), (-0.20, 1.42, 0.46), 0.055, "char")
        H.box("torn_canvas_panel", (-0.66, 1.10, 0.53), (0.78, 0.42, 0.045), "canvas", 0.010, rotation=(0.42, -0.10, 0.50))
        return
    H.beam("sorting_canopy_front", (-1.18, 0.72, ztop), (-0.30, 0.92, ztop + 0.03), 0.055, "beam")
    H.beam("sorting_canopy_back", (-1.08, 1.28, ztop), (-0.18, 1.46, ztop + 0.03), 0.055, "beam")
    for i in range(4):
        H.box("canvas_strip", (-0.76 + i * 0.16, 1.08 + i * 0.035, ztop + 0.035), (0.18, 0.70, 0.045), "canvas", 0.010, rotation=(0.04, 0.08, 0.20))
    H.box("sorting_table", (-0.70, 0.92, 0.34), (0.58, 0.34, 0.12), "wood", 0.016, rotation=(0, 0, 0.20))
    for x, y in ((-0.94, 0.78), (-0.46, 0.90), (-0.92, 1.02), (-0.44, 1.14)):
        H.beam("sorting_table_leg", (x, y, 0.13), (x, y, 0.36), 0.035, "beam")
    H.beam("sorting_chute", (-0.46, 0.78, 0.36), (0.10, 0.38, 0.24), 0.075, "wood")


def frustum(name, cx, cy, z, rx, ry, height, top_scale, role, rings=3, segments=28, wobble=0.04):
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


def sand_mound(name, x, y, rx, ry, height, role="sand_light"):
    return frustum(name, x, y, 0.09, rx, ry, height, 0.10, role, rings=5, segments=24, wobble=0.08)


def salt_crystal(name, x, y, z, height=0.28):
    radius = height * 0.18
    verts = [(x, y, z + height)]
    for level, zz in enumerate((z + height * 0.18, z + height * 0.68)):
        scale = 1.0 if level == 0 else 0.72
        for i in range(6):
            angle = math.tau * i / 6 + math.radians(30)
            verts.append((x + radius * scale * math.cos(angle), y + radius * scale * math.sin(angle), zz))
    verts.append((x, y, z))
    faces = []
    for i in range(6):
        a = 1 + i
        b = 1 + (i + 1) % 6
        c = 7 + i
        d = 7 + (i + 1) % 6
        faces.append((a, b, d, c))
        faces.append((0, d, c))
        faces.append((13, a, b))
    return H.mesh(name, verts, faces, "blue_salt")


def gear(name, x, y, z, radius=0.18, thickness=0.055, role="iron", teeth=10, angle=0.0):
    cylinder(name + "_hub", (x, y, z), radius * 0.54, thickness, role, axis=(0, 1, 0), segments=18)
    cylinder(name + "_rim", (x, y, z), radius, thickness * 0.58, role, axis=(0, 1, 0), segments=24)
    for i in range(teeth):
        a = angle + math.tau * i / teeth
        H.box(
            name + "_tooth",
            (x + math.cos(a) * radius * 0.98, y, z + math.sin(a) * radius * 0.98),
            (radius * 0.28, thickness * 1.35, radius * 0.13),
            role,
            0.008,
            rotation=(0, a, 0),
        )


def conveyor(name, x, y, z, length, angle, role="iron", belt_role="sand_shadow", damaged=False):
    lean = -0.10 if damaged else 0.0
    H.box(name + "_belt", (x, y, z), (length, 0.34, 0.075), belt_role, 0.018, rotation=(lean, 0, angle))
    H.box(name + "_side_l", (x, y + 0.20, z + 0.08), (length, 0.055, 0.11), role, 0.012, rotation=(lean, 0, angle))
    H.box(name + "_side_r", (x, y - 0.20, z + 0.08), (length, 0.055, 0.11), role, 0.012, rotation=(lean, 0, angle))
    for offset in (-0.42, 0.0, 0.42):
        px = x + math.cos(angle) * offset * length * 0.42
        py = y + math.sin(angle) * offset * length * 0.42
        H.beam(name + "_leg_l", (px, py + 0.16, 0.13), (px, py + 0.16, z + 0.03), 0.035, role)
        H.beam(name + "_leg_r", (px, py - 0.16, 0.13), (px, py - 0.16, z + 0.03), 0.035, role)
    cylinder(name + "_roller_a", (x - math.cos(angle) * length * 0.48, y - math.sin(angle) * length * 0.48, z + 0.05), 0.10, 0.38, role, axis=(math.sin(angle), -math.cos(angle), 0), segments=16)
    cylinder(name + "_roller_b", (x + math.cos(angle) * length * 0.48, y + math.sin(angle) * length * 0.48, z + 0.05), 0.10, 0.38, role, axis=(math.sin(angle), -math.cos(angle), 0), segments=16)


def brick_retainers(level, state):
    if level < 4:
        return
    damaged = state == "damaged"
    for i, (x, y, angle) in enumerate(((-1.04, -0.42, 0.24), (-0.58, -0.62, 0.08), (0.68, -0.60, -0.16), (1.14, -0.26, -0.36), (-1.12, 0.28, -0.18), (-0.44, 0.58, 0.10), (0.46, 0.58, -0.08))):
        role = "char" if damaged and i in (2, 5) else "brick"
        H.box("brick_retaining_course", (x, y, 0.38 if not damaged or i % 2 else 0.20), (0.34, 0.19, 0.17), role, 0.018, rotation=(0, 0, angle))
    if level >= 5:
        for i, (x, y) in enumerate(((-1.23, -0.18), (-0.10, -0.78), (1.10, 0.12), (-0.70, 0.70))):
            H.box("copper_corner_clamp", (x, y, 0.53), (0.17, 0.10, 0.08), "copper", 0.012, rotation=(0, 0, i * 0.35))


def winch_and_chute(level, state):
    if level < 4:
        return
    damaged = state == "damaged"
    main_role = "char" if damaged else ("premium_wood" if level >= 7 else "wood")
    metal_role = "steel" if level >= 8 else "iron" if level >= 6 else "copper" if level >= 5 else "metal"
    top = 1.36 + min(level - 4, 5) * 0.045
    for x, y in ((-0.92, 1.18), (-0.20, 1.28)):
        H.beam("winch_frame_post", (x, y, 0.13), (x, y, top if not damaged else top * 0.55), 0.07, main_role)
    if not damaged:
        H.beam("winch_frame_cross", (-1.02, 1.18, top), (-0.10, 1.28, top + 0.04), 0.075, main_role)
        cylinder("winch_drum", (-0.56, 1.24, top - 0.18), 0.16, 0.58, metal_role, axis=(1, 0, 0), segments=18)
        H.beam("winch_rope_drop", (-0.56, 1.24, top - 0.16), (-0.08, 0.42, 0.58), 0.023, "rope")
        H.box("lift_skip", (-0.04, 0.36, 0.46), (0.38, 0.28, 0.20), "wood", 0.025, rotation=(0.04, 0, -0.20))
        H.box("sand_chute", (0.70, -0.04, 0.61), (1.00, 0.24, 0.12), "premium_wood" if level >= 8 else "wood", 0.018, rotation=(-0.18, 0.06, -0.40))
        if level >= 5:
            gear("winch_copper_gear", -0.94, 1.17, top - 0.18, 0.16, 0.050, "copper", teeth=9, angle=0.10)
    else:
        H.beam("broken_winch_frame", (-0.98, 1.16, 0.72), (-0.18, 1.04, 0.36), 0.075, "char")
        H.box("fallen_lift_skip", (0.02, 0.34, 0.22), (0.40, 0.26, 0.16), "char", 0.022, rotation=(0.38, -0.10, -0.38))


def mechanized_processing(level, state):
    if level < 6:
        return
    damaged = state == "damaged"
    frame_role = "char" if damaged else "steel" if level >= 8 else "iron"
    wood_role = "char" if damaged else "premium_wood" if level >= 8 else "wood"
    H.box("mechanical_sifter_body", (0.96, 0.78, 0.52 if not damaged else 0.35), (0.74, 0.44, 0.30), wood_role, 0.025, rotation=(0.10 if damaged else 0.0, 0.0, -0.20))
    for x, y in ((0.66, 0.60), (1.24, 0.48), (0.72, 0.98), (1.30, 0.86)):
        H.beam("sifter_leg", (x, y, 0.13), (x, y, 0.48 if not damaged else 0.28), 0.045, frame_role)
    gear("sifter_drive_gear_a", 0.58, 0.72, 0.62, 0.14, 0.045, "copper" if level < 8 else "steel", teeth=10)
    gear("sifter_drive_gear_b", 0.43, 0.72, 0.42, 0.11, 0.040, "iron", teeth=8, angle=0.2)
    if level >= 8:
        conveyor("main_conveyor", 0.22, 0.42, 0.74 if not damaged else 0.42, 1.50, -0.42, "steel", "sand_shadow", damaged)
        for x, y in ((-0.56, 0.98), (-0.18, 1.16), (0.20, 1.04), (0.58, 0.82)):
            H.beam("steel_truss_arc", (x, y, 0.30), (x + 0.18, y - 0.12, 1.18 if not damaged else 0.70), 0.042, frame_role)
    if level >= 9:
        H.box("operator_platform", (-1.18, 0.72, 0.58 if not damaged else 0.36), (0.62, 0.52, 0.14), "premium_wood" if not damaged else "char", 0.018, rotation=(0, 0, 0.18))
        for x, y in ((-1.44, 0.54), (-0.96, 0.62), (-1.36, 0.92), (-0.88, 1.00)):
            H.beam("operator_platform_leg", (x, y, 0.13), (x, y, 0.62 if not damaged else 0.34), 0.045, frame_role)
        if not damaged:
            H.box("operator_cabin", (-1.16, 0.84, 0.91), (0.46, 0.38, 0.38), "wood", 0.024, rotation=(0, 0, 0.16))
            H.box("operator_cabin_roof", (-1.16, 0.84, 1.16), (0.56, 0.46, 0.10), "steel", 0.018, rotation=(0.02, 0, 0.16))
    if level >= 10:
        roof_role = "rune_tile" if not damaged else "char"
        H.box("rune_tile_roof", (0.96, 0.80, 1.03 if not damaged else 0.62), (0.88, 0.56, 0.10), roof_role, 0.018, rotation=(0.08 if damaged else 0.0, 0.0, -0.20))
        for i in range(4):
            salt_crystal("deep_blue_salt_vein", -0.10 + i * 0.16, -0.16 + i * 0.04, 0.34 + i * 0.02, 0.17)
    if level >= 11:
        H.box("super_mechanism_core", (0.96, 0.28, 0.78 if not damaged else 0.42), (0.42, 0.34, 0.42), frame_role, 0.035, rotation=(0.0, 0.0, -0.08))
        gear("super_mechanism_gold_dial", 0.74, 0.26, 0.88 if not damaged else 0.52, 0.13, 0.035, "gold", teeth=12)
        gear("super_mechanism_steel_wheel", 1.18, 0.26, 0.84 if not damaged else 0.48, 0.18, 0.045, "steel", teeth=12, angle=0.15)
        conveyor("return_conveyor", 0.38, -0.78, 0.54 if not damaged else 0.30, 1.36, 0.18, "steel", "sand", damaged)


def ground(level):
    H.base()
    H.box("sand_yard", (0, -0.08, 0.085), (2.92, 2.42, 0.055), "sand", 0.035, rotation=(0, 0, 0.02))
    H.box("cart_track_a", (-0.46, -0.98, 0.135), (1.64, 0.08, 0.035), "sand_shadow", 0.01, rotation=(0, 0, -0.18))
    H.box("cart_track_b", (-0.40, -1.17, 0.135), (1.50, 0.07, 0.035), "sand_shadow", 0.01, rotation=(0, 0, -0.18))
    frustum("pit_outer_terrace", 0, -0.03, 0.11, 1.05 + level * 0.08, 0.78 + level * 0.045, 0.12, 0.64, "sand_light", rings=4, segments=44)
    ring_band("pit_cut_lip", 0.01, -0.035, 0.225, 0.86 + level * 0.07, 0.61 + level * 0.04, 0.22, 0.045, "sand_shadow", segments=44)
    frustum("pit_inner_shadow", 0.02, -0.04, 0.19, 0.68 + level * 0.06, 0.48 + level * 0.035, 0.08, 0.42, "sand_shadow", rings=3, segments=36, wobble=0.03)
    frustum("pit_floor", 0.04, -0.04, 0.255, 0.36 + level * 0.04, 0.25 + level * 0.03, 0.035, 0.84, "sand", rings=2, segments=30, wobble=0.02)
    for i, angle in enumerate((-0.76, -0.45, -0.14)):
        H.box("terrace_step", (-0.66 + i * 0.28, -0.36 - i * 0.10, 0.30 + i * 0.035), (0.30, 0.13, 0.055), "sand_light", 0.012, rotation=(0.03, 0.00, angle))
    ladder("pit_ladder", -0.43, 0.28, 0.30, -0.82, 0.74, "wood")
    for obj in H.COL.objects:
        obj["ground"] = True


def copy_ground(active):
    for original in active.objects:
        if original.get("ground"):
            obj = original.copy()
            obj.data = original.data.copy()
            obj.name = original.name.replace("_active", "_" + H.PREFIX.rsplit("_", 1)[-1])
            H.COL.objects.link(obj)


def tools(level, state):
    damaged = state == "damaged"
    for idx, (x, y, angle) in enumerate(((1.24, -0.76, 0.15), (-1.12, -0.54, -0.46), (0.96, 0.70, 0.70))):
        H.beam("tool_handle", (x, y, 0.17), (x + 0.45 * math.cos(angle), y + 0.45 * math.sin(angle), 0.34), 0.045, "wood" if not damaged else "char")
        H.box("tool_head", (x + 0.48 * math.cos(angle), y + 0.48 * math.sin(angle), 0.36), (0.16, 0.055, 0.12), "metal", 0.012, rotation=(0, 0, angle))
    H.box("wheelbarrow_bin", (-1.28, 0.78, 0.24), (0.46, 0.28, 0.20), "wood" if not damaged else "char", 0.035, rotation=(0, 0, -0.22))
    cylinder("wheelbarrow_wheel", (-1.50, 0.84, 0.15), 0.09, 0.055, "metal", axis=(0, 1, 0), segments=14)
    H.beam("wheelbarrow_handle_l", (-1.12, 0.66, 0.26), (-0.78, 0.53, 0.25), 0.045, "wood")
    H.beam("wheelbarrow_handle_r", (-1.10, 0.90, 0.26), (-0.76, 1.03, 0.25), 0.045, "wood")
    for i, (x, y) in enumerate(((1.34, -0.48), (1.10, -0.62), (-1.34, 0.28))):
        bucket(f"work_bucket_{i+1}", x, y, 0.15, "char" if damaged and i == 1 else "wood")
    for i, (x, y) in enumerate(((0.88, -1.12), (1.14, -1.02), (1.38, -0.92))):
        sack(f"sand_sack_{i+1}", x, y, 0.14, 0.18, 0.13, 0.15, "dust")
    if level >= 2:
        sieve_screen("tilted_sieve", 1.13, -0.04, 0.54, -0.22, damaged)
    if level >= 3:
        H.box("salt_crate", (1.24, 0.54, 0.23), (0.42, 0.30, 0.24), "wood", 0.025, rotation=(0, 0, -0.18))
        H.box("salt_crate_lid", (1.24, 0.54, 0.38), (0.47, 0.34, 0.045), "beam", 0.012, rotation=(0.04, 0, -0.18))
        for x, y in ((0.32, -0.12), (0.18, 0.04), (0.55, 0.12)):
            salt_crystal("blue_salt_crystal", x, y, 0.28, 0.20)


def bridge(level, state):
    if level < 2:
        return
    damaged = state == "damaged"
    angle = -0.32 if not damaged else -0.72
    z = 0.47 if not damaged else 0.25
    plank_walkway(
        "bridge",
        [(-0.68 + i * 0.30, -0.08 - i * 0.095, z + (0.02 if i % 2 else 0), angle) for i in range(5 if not damaged else 4)],
        0.23,
        "wood",
        broken=damaged,
    )
    for x, y in ((-0.96, 0.00), (0.48, -0.48), (1.18, -0.05), (-1.24, 0.20)):
        top = 0.70 if not damaged else 0.42
        H.beam("rope_post", (x, y, 0.13), (x, y, top), 0.06, "beam" if not damaged else "char")
    if not damaged:
        H.beam("rope_rail_a", (-1.24, 0.20, 0.66), (-0.96, 0.00, 0.68), 0.035, "rope")
        H.beam("rope_rail_b", (-0.96, 0.00, 0.68), (0.48, -0.48, 0.66), 0.035, "rope")
        H.beam("rope_rail_c", (0.48, -0.48, 0.66), (1.18, -0.05, 0.66), 0.035, "rope")


def retaining_and_hoist(level, state):
    damaged = state == "damaged"
    if level >= 3:
        ring_band("stone_retaining_ring", 0.02, -0.04, 0.33, 1.04, 0.76, 0.10, 0.12, "stone", segments=36, wobble=0.01)
        for i, (x, y, angle) in enumerate(((-0.90, -0.52, 0.25), (-0.52, -0.64, 0.10), (0.86, -0.50, -0.20), (1.08, -0.18, -0.34), (-0.96, 0.44, -0.15), (-0.34, 0.58, 0.08))):
            if damaged and i in (1, 4):
                z, role = 0.13, "char"
            else:
                z, role = 0.24, "stone"
            H.box("stone_retaining_block", (x, y, z), (0.36, 0.22, 0.19), role, 0.025, rotation=(0, 0, angle))
        left_top = 1.34 if not damaged else 0.62
        right_top = 1.34 if not damaged else 0.86
        H.beam("hoist_left_post", (-0.55, 0.72, 0.14), (-0.55, 0.72, left_top), 0.08, "beam" if not damaged else "char")
        H.beam("hoist_right_post", (0.55, 0.72, 0.14), (0.55, 0.72, right_top), 0.08, "beam")
        if not damaged:
            H.beam("hoist_crossbeam", (-0.72, 0.72, 1.34), (0.72, 0.72, 1.34), 0.10, "beam")
            H.beam("hoist_roof_ridge", (-0.64, 0.68, 1.50), (0.64, 0.68, 1.50), 0.045, "wood")
            for x in (-0.36, 0.0, 0.36):
                H.beam("hoist_wind_brace", (x, 0.72, 1.34), (x + 0.12, 0.48, 1.49), 0.038, "wood")
            H.beam("hoist_rope", (0.05, 0.72, 1.32), (0.05, 0.72, 0.58), 0.024, "rope")
            H.box("lift_bucket", (0.05, 0.72, 0.45), (0.34, 0.26, 0.22), "wood", 0.025, rotation=(0, 0, 0.10))
            cylinder("hoist_pulley", (0.05, 0.72, 1.28), 0.13, 0.060, "metal", axis=(1, 0, 0), segments=16)
        else:
            H.beam("broken_hoist_crossbeam", (-0.40, 0.72, 0.72), (0.46, 0.55, 0.38), 0.08, "char")


def construction_overlay(level):
    for x in (-1.28, -0.42, 0.42, 1.28):
        H.beam("scaffold_post", (x, -1.12, 0.12), (x, -1.12, 0.86), 0.055, "wood")
    H.beam("scaffold_front_rail", (-1.34, -1.12, 0.82), (1.34, -1.12, 0.82), 0.06, "wood")
    H.beam("scaffold_mid_rail", (-1.25, -1.12, 0.48), (1.25, -1.12, 0.48), 0.05, "wood")
    H.beam("scaffold_diag", (-1.24, -1.12, 0.18), (1.18, -1.12, 0.78), 0.045, "rope")
    for i in range(5):
        H.box("loose_upgrade_board", (-0.58 + i * 0.28, 1.16, 0.16 + i * 0.03), (0.52, 0.10, 0.065), "wood", 0.012, rotation=(0, 0, 0.20 - i * 0.08))
    H.box("unfinished_sorting_table", (1.08, 0.30, 0.25), (0.60, 0.36, 0.09), "wood", 0.014, rotation=(0, 0, -0.16))
    for x, y in ((0.84, 0.18), (1.32, 0.18), (0.86, 0.43), (1.30, 0.43)):
        H.beam("unfinished_table_leg", (x, y, 0.12), (x, y, 0.28), 0.035, "beam")
    sieve_screen("uninstalled_sieve", 0.78, 0.74, 0.28, 0.35, damaged=False)
    if level >= 3:
        for i in range(3):
            H.box("unplaced_stone_block", (0.78 + i * 0.18, -0.92, 0.16), (0.22, 0.18, 0.16), "stone", 0.025, rotation=(0, 0, i * 0.18))
        H.beam("half_hoist_post", (-0.45, 0.72, 0.14), (-0.45, 0.72, 0.78), 0.075, "beam")
        H.beam("half_hoist_post", (0.45, 0.72, 0.14), (0.45, 0.72, 0.62), 0.075, "beam")
    if level >= 4:
        for i in range(5):
            H.box("stacked_upgrade_brick", (-1.22 + i * 0.18, -0.70 + 0.05 * (i % 2), 0.16 + 0.05 * (i // 2)), (0.20, 0.13, 0.08), "brick", 0.012, rotation=(0, 0, -0.20 + i * 0.10))
        H.beam("unmounted_winch_axle", (-1.10, 1.10, 0.26), (-0.38, 1.20, 0.32), 0.055, "copper" if level >= 5 else "metal")
    if level >= 6:
        H.box("packed_iron_frame", (1.18, 0.86, 0.24), (0.62, 0.18, 0.12), "iron", 0.014, rotation=(0, 0, -0.22))
        gear("unmounted_sifter_gear", 1.02, 0.60, 0.30, 0.12, 0.040, "copper" if level < 8 else "steel", teeth=9)
    if level >= 8:
        H.box("half_conveyor_belt", (0.26, 0.48, 0.42), (0.98, 0.28, 0.065), "sand_shadow", 0.012, rotation=(-0.12, 0, -0.42))
        for i in range(3):
            H.beam("unbolted_steel_truss", (-0.32 + i * 0.26, 1.06, 0.20), (0.08 + i * 0.26, 0.90, 0.48), 0.038, "steel")
    if level >= 10:
        for i in range(4):
            H.box("rune_tile_stack", (-1.36 + i * 0.13, 0.24, 0.17 + i * 0.025), (0.16, 0.12, 0.045), "rune_tile", 0.008, rotation=(0, 0, i * 0.08))
    if level >= 11:
        H.box("crated_super_mechanism", (0.78, -1.02, 0.27), (0.48, 0.34, 0.28), "steel", 0.025, rotation=(0, 0, 0.18))
        H.box("gold_calibration_parts", (1.16, -0.94, 0.45), (0.18, 0.12, 0.08), "gold", 0.012, rotation=(0, 0, -0.14))
    frustum("construction_dust", -0.18, -0.22, 0.28, 0.28, 0.18, 0.16, 0.20, "dust", rings=3, segments=14, wobble=0.02)


def damaged_overlay(level):
    H.box("caved_sand_edge", (-0.80, -0.20, 0.27), (0.76, 0.44, 0.20), "sand_shadow", 0.04, rotation=(0.04, 0.10, 0.28))
    H.box("collapsed_lip_slab", (0.42, 0.22, 0.29), (0.58, 0.24, 0.12), "sand_shadow", 0.025, rotation=(0.16, -0.12, -0.26))
    for i in range(10):
        role = "char" if i % 3 == 0 else "stone" if level >= 3 and i % 2 else "wood"
        H.box("fallen_debris", (-0.92 + i * 0.20, -1.02 - 0.06 * (i % 2), 0.14), (0.18 + 0.04 * (i % 2), 0.12, 0.10), role, 0.015, rotation=(0.08 * (i % 2), 0.10, i * 0.31))
    H.beam("broken_walkway_beam", (-0.70, -0.32, 0.18), (0.52, -0.72, 0.34), 0.09, "char")
    H.beam("snapped_rope", (-1.08, 0.08, 0.42), (-0.62, -0.12, 0.18), 0.026, "rope")
    H.box("overturned_cart_bin", (-1.22, 0.80, 0.19), (0.44, 0.24, 0.17), "char", 0.025, rotation=(0.38, 0.14, 0.62))
    if level >= 3:
        for i in range(3):
            H.box("fallen_stone_block", (0.62 + i * 0.20, -0.72 + i * 0.04, 0.16), (0.24, 0.18, 0.15), "stone", 0.02, rotation=(0.08, 0.16, -0.35 + i * 0.22))
    if level >= 4:
        for i in range(5):
            H.box("fallen_brick_block", (-1.20 + i * 0.20, 0.42 - i * 0.04, 0.15), (0.19, 0.13, 0.09), "brick" if i % 2 else "char", 0.014, rotation=(0.08, 0.12, -0.30 + i * 0.18))
    if level >= 6:
        gear("fallen_drive_gear", 1.14, 0.50, 0.23, 0.15, 0.040, "iron", teeth=10, angle=0.12)
        H.beam("bent_iron_frame", (0.48, 0.82, 0.18), (1.22, 0.56, 0.46), 0.052, "char")
    if level >= 8:
        H.box("collapsed_conveyor_plate", (0.34, 0.44, 0.28), (0.88, 0.30, 0.075), "char", 0.016, rotation=(0.34, -0.12, -0.62))
        H.beam("bent_steel_truss", (-0.36, 1.00, 0.18), (0.62, 0.76, 0.42), 0.045, "steel")
    if level >= 10:
        H.box("cracked_rune_tile_roof_piece", (0.92, 0.88, 0.28), (0.42, 0.26, 0.07), "rune_tile", 0.014, rotation=(0.18, -0.20, -0.18))
    if level >= 11:
        H.box("dead_super_core", (0.88, 0.22, 0.24), (0.36, 0.26, 0.24), "char", 0.022, rotation=(0.20, -0.10, 0.18))
        H.box("lost_gold_cog_cover", (1.24, 0.16, 0.20), (0.16, 0.10, 0.06), "gold", 0.010, rotation=(0.10, 0.22, -0.40))
    frustum("damage_dust", 0.40, -0.10, 0.34, 0.32, 0.20, 0.20, 0.22, "dust", rings=3, segments=14, wobble=0.03)


def quarry(level, state, active=None):
    collection = bpy.data.collections.new(f"sand_quarry_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    H.COL = collection
    H.PREFIX = collection.name
    collection["level"] = level
    collection["state"] = state
    collection["ground_source"] = f"sand_quarry_l{level:02d}_active"
    if active is None:
        ground(level)
    else:
        copy_ground(active)
    for idx, (x, y, rx, ry) in enumerate(((-1.12, 0.28, 0.30, 0.20), (1.12, 0.22, 0.34, 0.23), (0.60, -0.86, 0.24, 0.16), (-0.74, -0.82, 0.20, 0.13))):
        sand_mound(f"sand_pile_{idx+1}", x, y, rx + level * 0.015, ry + level * 0.010, 0.22 + level * 0.025, "sand_light" if idx % 2 else "sand")
    if level >= 2:
        H.box("timber_retainer_front", (0.0, -1.28, 0.22), (1.76, 0.12, 0.16), "wood" if state != "damaged" else "char", 0.018, rotation=(0, 0, -0.04))
        for x in (-0.82, -0.28, 0.28, 0.82):
            H.beam("retainer_stake", (x, -1.32, 0.12), (x, -1.32, 0.42 if state != "damaged" else 0.27), 0.045, "beam" if state != "damaged" else "char")
    tools(level, state)
    bridge(level, state)
    quarry_canopy(level, state)
    retaining_and_hoist(level, state)
    brick_retainers(level, state)
    winch_and_chute(level, state)
    mechanized_processing(level, state)
    if state == "construction":
        construction_overlay(level)
    if state == "damaged":
        damaged_overlay(level)
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
        """# Песчаный карьер

Сюда Blender-генератор сохраняет runtime-модели Песчаного карьера:

```bash
\"/mnt/d/programs/Blender/5.2/blender.exe\" --background --python tools/assets/blender/generate_sand_quarry_models.py
```

Ожидаемые файлы:

- `sand_quarry_levels.blend`;
- `sand_quarry_levels.glb`;
- `sand_quarry_l01_active.glb` ... `sand_quarry_l11_damaged.glb`;
- `sand_quarry_l01_active.png` ... `sand_quarry_l11_damaged.png`;
- `generation-report.json`;
- `roundtrip-validation.json`;
- `state-review.png`.

Runtime-карта использует PNG-спрайты `sand_quarry_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.
""",
        encoding="utf-8",
    )


def write_manifest(report):
    manifest = {
        "family": "sand_quarry",
        "displayName": "Песчаный карьер",
        "source": "sand_quarry_levels.blend",
        "combinedModel": "sand_quarry_levels.glb",
        "generator": "tools/assets/blender/generate_sand_quarry_models.py",
        "levels": list(LEVELS),
        "states": list(STATES),
        "spriteSize": [512, 384],
        "files": sorted(f"{name}.png" for name in report),
        "models": sorted(f"{name}.glb" for name in report),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contact_sheet():
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return
    sheet = Image.new("RGBA", (256 * 3, 214 * len(list(LEVELS))), (35, 51, 43, 255))
    draw = ImageDraw.Draw(sheet)
    for row, level in enumerate(LEVELS):
        for col, state in enumerate(STATES):
            name = f"sand_quarry_l{level:02d}_{state}"
            with Image.open(OUT_DIR / f"{name}.png") as image:
                thumb = image.resize((256, 192), Image.Resampling.LANCZOS)
            y = row * 214
            sheet.alpha_composite(thumb, (col * 256, y))
            draw.text((col * 256 + 10, y + 194), name, fill=(255, 255, 255, 255))
    sheet.save(OUT_DIR / "state-review.png")


def clear_previous_build():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("sand_quarry_"):
            bpy.data.objects.remove(obj)
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Sand_Quarry") or scene.name.startswith("Sand_Quarry_Roundtrip"):
            bpy.data.scenes.remove(scene)
    for collection in list(bpy.data.collections):
        if collection.name.startswith("sand_quarry_"):
            bpy.data.collections.remove(collection)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("sand_quarry_"):
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_sand_quarry_"):
            bpy.data.materials.remove(material)


def main(output=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    directory = Path(output or OUT_DIR)
    clear_previous_build()
    scene = bpy.data.scenes.new("Real_City_Sand_Quarry_Models")
    bpy.context.window.scene = scene
    palette()
    H.setup_camera(scene)
    scene["style_reference"] = "Real City bright fantasy stylized mid-poly; camera/palette based on regenerate_early_housing.py and regenerate_sawmills.py"
    report, active, collections = {}, {}, []
    note = bpy.data.texts.new("sand_quarry_asset_notes")
    note.write(
        "Real City sand_quarry levels 1-11, states active/construction/damaged. "
        "Visual anchor: central sand excavation with warm piles, tools, rope/wood progression, stone retaining blocks and blue salt from level 3. "
        "Costs mapped to visible materials: stone/stone blocks -> retaining blocks, planks -> bridge/scaffold/tools, rope -> rails/hoist, "
        "brick -> pit courses, copper -> winch gears/clamps, iron/steel -> frames/gears/conveyors, premium planks -> platform decking, "
        "rune tile -> late protective roof, gold -> calibration dials, super mechanism -> compact sorting core. "
        "No fallback sprite generator was used for this build."
    )
    for level in LEVELS:
        for state in STATES:
            collection = quarry(level, state, active.get(level))
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
            report[name] = {
                "level": level,
                "state": state,
                "triangles": triangles(collection),
                "bounds": bounds(collection),
                "ground_source": collection["ground_source"],
                "style": "bright fantasy stylized mid-poly Blender",
                "alpha_bounds": alpha_bounds(directory / f"{name}.png"),
            }
            collections.append(collection)
            REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("SAND_QUARRY_DONE " + name, flush=True)
    hide_all(collections)
    for collection in collections:
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_active_scene=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    write_readme()
    write_manifest(report)
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id="sand_quarry",
            display_name="Песчаный карьер",
            category="industry",
            output_dir=directory,
            levels=LEVELS,
            states=STATES,
            source_blend=BLEND_PATH,
            combined_glb=GLB_PATH,
            generator="tools/assets/blender/generate_sand_quarry_models.py",
            style_reference="Real City sand quarry migrated to shared scene/export/report layer",
        )
    )
    contact_sheet()

    qa = bpy.data.scenes.new("Sand_Quarry_Roundtrip_QA")
    bpy.context.window.scene = qa
    for name, entry in report.items():
        bpy.ops.import_scene.gltf(filepath=str(directory / f"{name}.glb"))
        count = 0
        for obj in qa.objects:
            if obj.type != "MESH":
                continue
            obj.data.calc_loop_triangles()
            count += len(obj.data.loop_triangles)
        assert count == entry["triangles"], (name, count, entry["triangles"])
        bpy.data.batch_remove(ids=list(qa.objects))
    ROUNDTRIP_PATH.write_text(json.dumps({"models": len(report), "triangles_matched": True}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SAND_QUARRY_COMPLETE " + str(len(report)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main(args.output)
