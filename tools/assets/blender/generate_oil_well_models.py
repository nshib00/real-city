#!/usr/bin/env python3
"""Generate mid-poly Real City oil derrick building models."""

from __future__ import annotations

import json
import math
import sys
import argparse
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
BLENDER_TOOLS_DIR = ROOT / "tools" / "assets" / "blender"
if str(BLENDER_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(BLENDER_TOOLS_DIR))

from real_city import RenderProfile
from real_city import ground as real_city_ground
from real_city import scene as real_city_scene

OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "oil_well"
ASSET_ID = "oil_well"
LEVELS = (1, 2, 3)
STATES = ("active", "construction", "damaged", "ruined")
REVISION = "oil-well-no-side-rods-2026-10-14"
BACKUP_NAME = "backup_2026-10-14_pre_remove_side_rods"
BLEND_PATH = OUT_DIR / "oil_well_levels.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
ROUNDTRIP_PATH = OUT_DIR / "roundtrip-validation.json"
CONTACT_SHEET_PATH = OUT_DIR / "state-review.png"

SCENE = None
MATS: dict[str, bpy.types.Material] = {}
COLLECTIONS: dict[str, bpy.types.Collection] = {}
REPORT: dict[str, dict] = {}
CURRENT_COLLECTION: bpy.types.Collection | None = None


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def material(role, name, color, roughness=0.78, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = shader(mat)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    MATS[role] = mat


def setup_materials():
    material("grass", "MAT_oil_well_grass_bright", (0.26, 0.48, 0.08), 0.86)
    material("grass_light", "MAT_oil_well_grass_light", (0.37, 0.59, 0.13), 0.86)
    material("earth", "MAT_oil_well_earth_oil_stained", (0.34, 0.23, 0.12), 0.88)
    material("gravel", "MAT_oil_well_light_gravel", (0.62, 0.60, 0.50), 0.86)
    material("oil", "MAT_oil_well_oil_black_gloss", (0.014, 0.014, 0.018), 0.20)
    material("oil_deep", "MAT_oil_well_deep_black_oil_pit", (0.001, 0.001, 0.003), 0.12)
    material("wood", "MAT_oil_well_wood_pale", (0.70, 0.45, 0.20), 0.70)
    material("beam", "MAT_oil_well_wood_dark", (0.34, 0.17, 0.065), 0.78)
    material("rope", "MAT_oil_well_rope", (0.70, 0.48, 0.20), 0.86)
    material("metal", "MAT_oil_well_metal_worn", (0.48, 0.53, 0.50), 0.46, 0.35)
    material("dark_metal", "MAT_oil_well_metal_dark", (0.20, 0.24, 0.24), 0.50, 0.55)
    material("steel", "MAT_oil_well_steel_light", (0.70, 0.72, 0.66), 0.40, 0.55)
    material("concrete", "MAT_oil_well_concrete_light", (0.64, 0.62, 0.54), 0.86)
    material("reinforced", "MAT_oil_well_reinforced_concrete", (0.47, 0.50, 0.47), 0.78)
    material("premium_wood", "MAT_oil_well_premium_planks", (0.78, 0.52, 0.22), 0.62)
    material("copper", "MAT_oil_well_copper_oiled", (0.78, 0.42, 0.18), 0.50, 0.35)
    material("paint_red", "MAT_oil_well_painted_warning_red", (0.74, 0.18, 0.10), 0.62)
    material("paint_blue", "MAT_oil_well_painted_aeolian_blue", (0.28, 0.56, 0.70), 0.54, 0.15)
    material("amber", "MAT_oil_well_amber_warning", (1.0, 0.58, 0.12), 0.42, 0.0, (1.0, 0.42, 0.08), 0.22)
    material("aeolian", "MAT_oil_well_aeolian_alloy_blue", (0.36, 0.70, 0.84), 0.34, 0.4, (0.20, 0.50, 0.65), 0.10)
    material("char", "MAT_oil_well_charred_damage", (0.045, 0.040, 0.035), 0.92)
    material("warning", "MAT_oil_well_warning_yellow", (0.95, 0.72, 0.18), 0.58)
    MATS["earth_warm"] = MATS["earth"]
    MATS["grass_bright"] = MATS["grass"]
    MATS["stone_light"] = MATS["gravel"]


def link_to_current(obj):
    assert CURRENT_COLLECTION is not None
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    CURRENT_COLLECTION.objects.link(obj)
    return obj


def box(name, loc, size, role, bevel=0.018, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    obj = link_to_current(bpy.context.object)
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(MATS[role])
    if bevel:
        mod = obj.modifiers.new("soft_bevel", "BEVEL")
        mod.width = min(bevel, min(size) * 0.28)
        mod.segments = 1
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, loc, radius, depth, role, vertices=16, rotation=(0, 0, 0), bevel=False):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = link_to_current(bpy.context.object)
    obj.name = name
    obj.data.materials.append(MATS[role])
    if bevel:
        mod = obj.modifiers.new("rim_bevel", "BEVEL")
        mod.width = radius * 0.08
        mod.segments = 1
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def cone(name, loc, radius1, radius2, depth, role, vertices=4, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rotation)
    obj = link_to_current(bpy.context.object)
    obj.name = name
    obj.data.materials.append(MATS[role])
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def beam(name, start, end, radius, role, vertices=10):
    start_v = Vector(start)
    end_v = Vector(end)
    delta = end_v - start_v
    obj = cylinder(name, (start_v + end_v) * 0.5, radius, delta.length, role, vertices=vertices)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def diamond(name, radius, z, role):
    mesh = bpy.data.meshes.new(name)
    verts = [(0, radius, z), (radius, 0, z), (0, -radius, z), (-radius, 0, z)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    CURRENT_COLLECTION.objects.link(obj)
    obj.data.materials.append(MATS[role])
    return obj


def irregular_pool(name, x, y, z, rx, ry, role, seed, rings=3, segments=28):
    verts, faces = [], []
    for ring in range(rings):
        t = ring / (rings - 1)
        scale = 1.0 - t * 0.92
        for i in range(segments):
            angle = math.tau * i / segments
            wobble = 0.86 + 0.18 * ((i * 17 + ring * 9 + seed) % 7) / 6
            verts.append((x + rx * scale * math.cos(angle) * wobble, y + ry * scale * math.sin(angle) * wobble, z + t * 0.008))
    center_index = len(verts)
    verts.append((x, y, z + 0.012))
    for ring in range(rings - 1):
        for i in range(segments):
            faces.append((ring * segments + i, ring * segments + (i + 1) % segments, (ring + 1) * segments + (i + 1) % segments, (ring + 1) * segments + i))
    last = (rings - 1) * segments
    for i in range(segments):
        faces.append((last + i, last + (i + 1) % segments, center_index))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    CURRENT_COLLECTION.objects.link(obj)
    obj.data.materials.append(MATS[role])
    return obj


def apply_mesh_cleanup(collection):
    bpy.context.view_layer.update()
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        obj.data.transform(obj.matrix_world)
        obj.matrix_world.identity()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.calc_loop_triangles()
    bpy.context.view_layer.update()


def add_ground(level, state):
    real_city_ground.add_ground_tile(CURRENT_COLLECTION, MATS, prefix=ASSET_ID, include_path=False)
    irregular_pool("oil_stained_ground", 0.0, -0.02, 0.090, 0.96, 0.64, "earth", level * 7)
    irregular_pool("gravel_work_area", 0.22, -0.18, 0.098, 0.72, 0.42, "gravel", 80 + level)
    irregular_pool("deep_black_oil_pit", -0.02, -0.04, 0.116, 0.82, 0.58, "oil_deep", level * 13, rings=2, segments=36)
    irregular_pool("glossy_oil_pool", -0.03, -0.04, 0.128, 0.64, 0.44, "oil", level * 17, rings=2, segments=36)
    irregular_pool("visible_front_oil_shaft", -0.05, -0.30, 0.152, 0.54, 0.28, "oil_deep", 180 + level, rings=2, segments=32)
    if state in {"damaged", "ruined"}:
        irregular_pool("fresh_oil_leak", 0.42, -0.52, 0.120, 0.34, 0.16, "oil", 44 + level)
    for i, (x, y) in enumerate(((-1.42, 0.76), (1.36, -0.96), (-1.28, -0.58), (1.38, 0.98))):
        beam(f"survey_stake_{i}", (x, y, 0.02), (x + 0.02, y - 0.01, 0.30), 0.020, "wood", vertices=8)
        beam(f"survey_rope_{i}", (x, y, 0.26), (x * 0.86, y * 0.86, 0.24), 0.010, "rope", vertices=6)
    for i, (x, y, scale) in enumerate(((1.36, -0.58, 1.0), (-1.36, 0.92, 0.9))):
        for j in range(3):
            beam(f"grass_tuft_{i}_{j}", (x + (j - 1) * 0.04, y, 0.02), (x + (j - 1) * 0.08, y + 0.04, 0.12 * scale + j * 0.02), 0.018, "grass_light", vertices=6)
    for i, (x, y, sx, sy) in enumerate(((-1.18, 0.06, 0.26, 0.16), (1.18, 0.12, 0.22, 0.14), (-0.82, -1.06, 0.18, 0.12), (0.84, -1.10, 0.20, 0.13))):
        box(f"edge_service_stone_{i}", (x, y, 0.045), (sx, sy, 0.07), "gravel", 0.010, rotation=(0, 0, 0.14 * (i - 1)))


def add_barrel(name, x, y, role="dark_metal", leaking=False):
    cylinder(name, (x, y, 0.25), 0.13, 0.38, role, vertices=18, rotation=(math.pi / 2, 0, 0), bevel=True)
    cylinder(name + "_front_band", (x, y - 0.20, 0.25), 0.135, 0.026, "copper", vertices=18, rotation=(math.pi / 2, 0, 0))
    cylinder(name + "_back_band", (x, y + 0.20, 0.25), 0.135, 0.026, "copper", vertices=18, rotation=(math.pi / 2, 0, 0))
    if leaking:
        irregular_pool(name + "_leak", x + 0.15, y - 0.13, 0.055, 0.18, 0.10, "oil", 31)


def add_tank(name, x, y, level, damaged=False, ruined=False):
    mat = "dark_metal" if level >= 3 else "metal"
    height = 0.52 + 0.12 * level
    radius = 0.18 + 0.04 * level
    z = radius + 0.08 if ruined else height / 2 + 0.10
    rot = (math.pi / 2, 0.0, 0.22) if ruined else (0, 0, 0)
    cylinder(name, (x, y, z), radius, height, mat, vertices=22, rotation=rot, bevel=True)
    if level >= 3 and not ruined:
        box(name + "_armor_band_a", (x, y, 0.25), (radius * 2.18, 0.055, 0.08), "reinforced", 0.01)
        box(name + "_armor_band_b", (x, y, height + 0.02), (radius * 2.18, 0.055, 0.08), "reinforced", 0.01)
    if damaged or ruined:
        irregular_pool(name + "_spill", x + 0.18, y - 0.18, 0.055, 0.28, 0.12, "oil", 68)


def add_protective_fence(level, state):
    if level < 2:
        return
    damaged = state == "damaged"
    ruined = state == "ruined"
    construction = state == "construction"
    wall_role = "reinforced"
    metal_role = "dark_metal" if level >= 3 else "metal"
    height = 0.30 if level == 2 else 0.48
    thickness = 0.20 if level == 2 else 0.30
    base_height = 0.16 if level == 2 else 0.24
    ground_z = 0.10
    base_z = ground_z + base_height * 0.5
    wall_center_z = ground_z + base_height + height * 0.5
    y_front = -1.38
    y_back = 1.38
    x_left = -1.50
    x_right = 1.50
    segments = (
        ("north_left", (-0.75, y_back, wall_center_z), (1.56, thickness, height), 0.0),
        ("north_right", (0.75, y_back, wall_center_z), (1.56, thickness, height), 0.0),
        ("south_left", (-0.75, y_front, wall_center_z), (1.56, thickness, height), 0.0),
        ("south_right", (0.75, y_front, wall_center_z), (1.56, thickness, height), 0.0),
        ("west", (x_left, 0.00, wall_center_z), (thickness, 2.66, height), 0.0),
        ("east", (x_right, 0.00, wall_center_z), (thickness, 2.66, height), 0.0),
    )
    for index, (suffix, loc, size, rot) in enumerate(segments):
        if ruined and index in {0, 5}:
            box(f"collapsed_concrete_fence_{suffix}", (loc[0] * 0.94, loc[1] * 0.94, base_z), (size[0], size[1], base_height), "reinforced", 0.018, rotation=(0.14, 0.08, 0.20 if index == 0 else -0.24))
            continue
        wall_z = loc[2] - (0.08 if damaged and index in {2, 4} else 0.0)
        foundation_z = base_z - (0.04 if damaged and index in {2, 4} else 0.0)
        box(f"dark_reinforced_fence_foundation_{suffix}", (loc[0], loc[1], foundation_z), (size[0] * 1.06, size[1] * 1.10, base_height), "dark_metal" if level >= 3 else "reinforced", 0.018, rotation=(0, 0, rot))
        box(f"concrete_protective_fence_{suffix}", (loc[0], loc[1], wall_z), size, wall_role, 0.018, rotation=(0, 0, rot))
        if construction:
            box(f"unfinished_rebar_fence_{suffix}", (loc[0], loc[1], wall_z + height * 0.32), (size[0] * 0.75, size[1] * 0.70, 0.08), "metal", 0.010, rotation=(0, 0, rot))
        if level >= 3 and not construction:
            horizontal = size[0] > size[1]
            plate_size = (size[0] * 0.86, 0.050, 0.13) if horizontal else (0.050, size[1] * 0.86, 0.13)
            for layer in (-0.18, 0.16):
                box(f"metal_cladding_plate_{suffix}_{layer}", (loc[0], loc[1], wall_z + height * layer), plate_size, metal_role, 0.006, rotation=(0, 0, rot))

    spike_role = "steel" if level == 2 else "aeolian"
    if level >= 3:
        spike_points = [(-1.36, y_back), (-0.88, y_back), (-0.40, y_back), (0.08, y_back), (0.56, y_back), (1.04, y_back), (1.44, y_back),
                        (-1.36, y_front), (-0.88, y_front), (-0.40, y_front), (0.08, y_front), (0.56, y_front), (1.04, y_front), (1.44, y_front),
                        (x_left, -1.08), (x_left, -0.54), (x_left, 0.0), (x_left, 0.54), (x_left, 1.08),
                        (x_right, -1.08), (x_right, -0.54), (x_right, 0.0), (x_right, 0.54), (x_right, 1.08)]
    else:
        spike_points = [(-1.32, y_back), (-0.54, y_back), (0.54, y_back), (1.32, y_back), (-1.32, y_front), (-0.54, y_front), (0.54, y_front), (1.32, y_front), (x_left, -0.72), (x_left, 0.72), (x_right, -0.72), (x_right, 0.72)]
    for i, (x, y) in enumerate(spike_points):
        if construction and i % 4 == 1:
            continue
        if ruined and i % 3 == 0:
            beam(f"fallen_fence_spike_{i}", (x - 0.10, y, 0.10), (x + 0.12, y + 0.06, 0.18), 0.020, spike_role, vertices=6)
        else:
            spike_depth = 0.24 if level == 2 else 0.38
            cone(f"protective_spike_{i}", (x, y, wall_center_z + height * 0.5 + spike_depth * 0.5), 0.055 if level == 2 else 0.080, 0.006, spike_depth, spike_role, vertices=4, rotation=(0, 0, math.radians(45)))
            if level >= 3 and not construction and i % 2 == 0:
                box(f"secondary_spike_base_plate_{i}", (x, y, wall_center_z + height * 0.50), (0.16, 0.09, 0.045), metal_role, 0.004, rotation=(0, 0, 0.0))


def add_upgrade_materials(level, state):
    if level < 2:
        return
    construction = state == "construction"
    damaged = state == "damaged"
    ruined = state == "ruined"
    y = 1.04
    for i in range(3):
        box(f"iron_ingot_stack_{i}", (-0.98 + i * 0.18, y, 0.16 + i * 0.025), (0.24, 0.11, 0.07), "steel", 0.008, rotation=(0, 0, 0.10 * i))
    for i in range(3 if level == 2 else 4):
        box(f"premium_plank_bundle_{i}", (-0.96 + i * 0.16, -1.04, 0.14 + i * 0.018), (0.42, 0.08, 0.045), "premium_wood", 0.007, rotation=(0, 0, -0.10))
    cylinder("mechanism_gear_core", (0.94, 0.78, 0.28), 0.18 if level == 2 else 0.23, 0.07, "copper", vertices=18, rotation=(math.pi / 2, 0, 0), bevel=True)
    for angle in (0, math.pi / 2):
        box(f"mechanism_gear_tooth_{angle:.1f}", (0.94, 0.78, 0.28), (0.44, 0.055, 0.08), "metal" if level == 2 else "dark_metal", 0.006, rotation=(0, 0, angle))
    if level >= 3:
        box("super_mechanism_housing", (0.78, 0.66, 0.34), (0.46, 0.34, 0.32), "dark_metal", 0.020, rotation=(0, 0, 0.10))
        cylinder("super_mechanism_amber_core", (0.78, 0.46, 0.43), 0.090, 0.055, "amber", vertices=16, rotation=(math.pi / 2, 0, 0), bevel=True)
        for i, x in enumerate((-0.72, -0.46, -0.20)):
            beam(f"reinforced_beam_stack_{i}", (x, -1.14, 0.18 + i * 0.055), (x + 0.54, -1.00, 0.20 + i * 0.055), 0.045, "reinforced", vertices=8)
        for i in range(3):
            cylinder(f"amber_essence_vial_{i}", (1.24 + i * 0.09, -0.86, 0.23), 0.040, 0.18, "amber", vertices=12, bevel=True)
        beam("aeolian_alloy_guard_rail", (-0.54, 0.98, 0.48), (0.42, 1.02, 0.52), 0.030, "aeolian", vertices=8)
        beam("aeolian_alloy_power_line", (0.68, 0.58, 0.44), (0.18, 0.12, 0.82), 0.026, "aeolian", vertices=8)
    if construction:
        box("reinforced_concrete_sections_waiting", (-1.18, 0.62, 0.17), (0.46, 0.20, 0.20), "reinforced", 0.018, rotation=(0, 0, 0.18))
        box("open_mechanism_crate", (1.18, 0.62, 0.16), (0.42, 0.30, 0.22), "premium_wood", 0.014, rotation=(0, 0, -0.12))
    if damaged:
        box("cracked_reinforced_concrete_piece", (-1.18, 0.48, 0.13), (0.34, 0.22, 0.12), "reinforced", 0.012, rotation=(0.10, 0.0, 0.42))
    if ruined:
        box("scattered_super_mechanism_case" if level >= 3 else "scattered_mechanism_case", (1.02, 0.42, 0.14), (0.38, 0.28, 0.16), "dark_metal", 0.014, rotation=(0.08, 0.16, -0.36))


def add_pumpjack_mechanism(level, state, height, tilt):
    if state in {"ruined"}:
        box("smashed_internal_pumpjack_body", (0.14, -0.18, 0.22), (0.50, 0.30, 0.20), "dark_metal", 0.018, rotation=(0.08, 0.10, -0.34))
        beam("fallen_pumpjack_walking_beam", (-0.58, -0.10, 0.24), (0.66, -0.02, 0.34), 0.060, "beam" if level == 1 else "steel", vertices=10)
        beam("bent_pump_rod_to_oil_pit", (0.08, -0.02, 0.26), (-0.08, -0.04, 0.12), 0.022, "dark_metal", vertices=8)
        return
    body_role = "dark_metal"
    beam_role = "copper" if level == 1 else ("steel" if level == 2 else "aeolian")
    support_role = "wood" if level == 1 else "steel"
    completion = {"active": 1.0, "construction": 0.55, "damaged": 0.86}.get(state, 1.0)
    base_z = 0.20
    frame_top = min(height * 0.68, height * completion)
    if state == "construction":
        frame_top = min(frame_top, height * 0.46)
    if state != "construction":
        box("internal_pumpjack_engine_block", (-0.36, -0.18, base_z + 0.12), (0.42, 0.26, 0.24), body_role, 0.018, rotation=(0, 0, -0.08))
        cylinder("internal_pumpjack_flywheel", (-0.64, -0.18, base_z + 0.28), 0.18 + 0.03 * level, 0.055, "copper" if level <= 2 else "amber", vertices=20, rotation=(math.pi / 2, 0, 0), bevel=True)
        for angle in (0, math.pi / 2):
            box(f"internal_flywheel_spoke_{angle:.1f}", (-0.64, -0.18, base_z + 0.28), (0.34, 0.035, 0.040), "dark_metal", 0.004, rotation=(0, 0, angle))
    else:
        box("uninstalled_pumpjack_engine_block", (-0.48, -0.18, base_z + 0.08), (0.34, 0.24, 0.16), body_role, 0.014, rotation=(0, 0, 0.16))
        beam("construction_pumpjack_left_support", (-0.18, -0.10, base_z + 0.05), (0.00, -0.08, frame_top), 0.034 + 0.005 * level, support_role, vertices=8)
        beam("construction_pumpjack_right_support", (0.24, 0.02, base_z + 0.05), (0.00, -0.08, frame_top), 0.034 + 0.005 * level, support_role, vertices=8)
        beam("construction_unmounted_walking_beam", (-0.54, -0.10, frame_top + 0.02), (0.56, 0.02, frame_top + 0.06), 0.050 + 0.006 * level, beam_role, vertices=10)
        box("construction_pumpjack_horsehead", (0.66, 0.04, frame_top - 0.02), (0.13, 0.10, 0.25), beam_role, 0.012, rotation=(0, 0.08, 0.02))
        beam("construction_sucker_rod_into_black_pit", (0.46, -0.02, frame_top - 0.08), (-0.02, -0.22, 0.150), 0.018, "dark_metal", vertices=8)
    if state != "construction":
        beam("pumpjack_left_support", (-0.22, -0.10, base_z + 0.06), (0.02, -0.08, frame_top), 0.036 + 0.006 * level, support_role, vertices=8)
        beam("pumpjack_right_support", (0.28, 0.02, base_z + 0.06), (0.02, -0.08, frame_top), 0.036 + 0.006 * level, support_role, vertices=8)
        beam("pumpjack_walking_beam", (-0.64, -0.10, frame_top + 0.02), (0.76 + tilt * 0.28, 0.04, frame_top + (0.08 if state == "damaged" else 0.0)), 0.058 + 0.008 * level, beam_role, vertices=10)
        box("pumpjack_horsehead_inside_tower", (0.86 + tilt * 0.28, 0.05, frame_top - 0.04), (0.16, 0.12, 0.34), beam_role, 0.014, rotation=(0, 0.12 if state == "damaged" else 0, 0.04))
        beam("vertical_sucker_rod_into_black_pit", (0.58 + tilt * 0.14, 0.02, frame_top - 0.18), (0.02, -0.04, 0.135), 0.020, "dark_metal", vertices=8)
        beam("crank_link_to_engine", (-0.48, -0.18, base_z + 0.34), (-0.16, -0.10, frame_top - 0.12), 0.020, "steel", vertices=8)
        if level >= 3:
            cylinder("amber_pump_gauge", (-0.20, -0.32, base_z + 0.32), 0.055, 0.030, "amber", vertices=14, rotation=(math.pi / 2, 0, 0), bevel=True)


def add_derrick(level, state):
    ruined = state == "ruined"
    damaged = state == "damaged"
    construction = state == "construction"
    height = {1: 1.46, 2: 1.88, 3: 2.22}[level]
    spread = {1: 0.76, 2: 0.94, 3: 1.08}[level]
    top = {1: 0.22, 2: 0.28, 3: 0.34}[level]
    completion = {"active": 1.0, "construction": 0.58, "damaged": 0.90, "ruined": 0.34}[state]
    leg_role = "beam" if level == 1 else ("metal" if level == 2 else "dark_metal")
    brace_role = "wood" if level == 1 else ("metal" if level == 2 else "steel")
    tilt = 0.18 if damaged else 0.34 if ruined else 0.0

    corners = [(-spread, -spread), (spread, -spread), (spread, spread), (-spread, spread)]
    top_corners = [(-top + tilt, -top), (top + tilt, -top), (top + tilt, top), (-top + tilt, top)]

    if not ruined:
        for i, ((bx, by), (tx, ty)) in enumerate(zip(corners, top_corners)):
            target = (tx, ty, height * completion)
            if construction and i == 2:
                target = (tx, ty, height * 0.34)
            beam(f"derrick_leg_{i}", (bx, by, 0.11), target, 0.052 + level * 0.008, leg_role, vertices=12)
        completed_height = height * completion
        for z_factor in (0.24, 0.48, 0.72):
            if z_factor > completion + 0.05:
                continue
            z = height * z_factor
            for x in (-spread * 0.55, spread * 0.55):
                box(f"derrick_bolt_plate_{z_factor}_{x}", (x + tilt * 0.25, -spread - 0.025, z + 0.035), (0.16, 0.045, 0.075), "copper" if level >= 2 else "metal", 0.006)
        if not construction:
            box("top_crown_frame", (tilt * 0.5, 0, height * completion + 0.04), (top * 2.7, top * 2.4, 0.09), brace_role, 0.015, rotation=(0, 0, 0.12))
            box("top_roof_plate", (tilt * 0.5, 0, height * completion + 0.12), (top * 2.25, top * 1.95, 0.045), "paint_blue" if level >= 3 else "wood" if level == 1 else "steel", 0.010, rotation=(0, 0, 0.12))
    else:
        debris = (
            ((-0.72, -0.58, 0.12), (0.82, 0.30, 0.34), 0.044),
            ((0.64, -0.68, 0.10), (-0.52, 0.58, 0.26), 0.040),
            ((-0.28, 0.72, 0.12), (0.74, 0.92, 0.22), 0.034),
            ((-0.92, -0.06, 0.10), (-0.16, -0.78, 0.20), 0.036),
        )
        for i, (start, end, radius) in enumerate(debris):
            beam(f"fallen_derrick_beam_{i}", start, end, radius, leg_role)
        box("crushed_top_frame", (0.24, -0.20, 0.22), (0.62, 0.18, 0.13), brace_role, 0.018, rotation=(0.12, 0.0, -0.48))

    if state != "construction":
        cylinder("wellhead", (0, 0, 0.19), 0.105, 0.30, "dark_metal", vertices=18, bevel=True)
        beam("pump_rod", (0, 0, 0.34), (tilt * 0.55, 0.02, max(0.56, height * completion - 0.12)), 0.018, "dark_metal", vertices=10)

    add_pumpjack_mechanism(level, state, height, tilt)


def add_level_equipment(level, state):
    damaged = state == "damaged"
    ruined = state == "ruined"
    construction = state == "construction"

    if level == 1:
        box("wood_plank_deck", (0.00, -0.54, 0.075), (1.42, 0.50, 0.08), "wood", 0.016, rotation=(0, 0, -0.03))
        for x in (-0.54, -0.18, 0.18, 0.54):
            box("deck_plank", (x, -0.54, 0.135), (0.12, 0.56, 0.045), "wood", 0.008)
        add_barrel("oil_barrel_a", -1.26, 0.78, "dark_metal", leaking=damaged or ruined)
        add_barrel("oil_barrel_b", -1.48, 0.48, "metal", leaking=False)
        beam("rope_guy_left", (-0.68, -0.68, 0.58), (-1.36, -1.12, 0.06), 0.016, "rope", vertices=8)
        beam("rope_guy_right", (0.68, 0.68, 0.60), (1.38, 1.12, 0.06), 0.016, "rope", vertices=8)
        box("tool_crate_planks", (1.14, 0.62, 0.16), (0.42, 0.28, 0.20), "wood", 0.014, rotation=(0, 0, 0.12))
    else:
        add_protective_fence(level, state)
        pad_role = "concrete" if level == 2 else "reinforced"
        box("service_pad", (0.48, -0.62, 0.095), (1.12, 0.56, 0.10), pad_role, 0.020)
        if level == 2:
            box("premium_plank_operator_walkway", (-0.34, 0.66, 0.20), (0.82, 0.28, 0.08), "premium_wood", 0.014, rotation=(0, 0, 0.10))
        else:
            box("reinforced_operator_walkway", (-0.32, 0.66, 0.23), (0.92, 0.30, 0.10), "dark_metal", 0.014, rotation=(0, 0, 0.10))
            box("aeolian_walkway_inlay", (-0.32, 0.66, 0.295), (0.72, 0.045, 0.025), "aeolian", 0.004, rotation=(0, 0, 0.10))
        beam("outlet_pipe_a", (0.08, -0.10, 0.17), (0.82, -0.62, 0.17), 0.044, "dark_metal")
        beam("outlet_pipe_b", (0.82, -0.62, 0.17), (1.42, -0.38, 0.17), 0.044, "dark_metal")
        add_tank("small_reservoir", -1.12, 0.48, level, damaged=damaged, ruined=ruined)
        box("mechanical_pump_block", (1.02, 0.46, 0.20), (0.48 + level * 0.09, 0.34, 0.30), "dark_metal", 0.024)
        cylinder("flywheel", (1.25, 0.23, 0.42), 0.20 + 0.035 * level, 0.060, "metal", vertices=24, rotation=(math.pi / 2, 0, 0), bevel=True)
        box("painted_access_panel", (1.04, 0.25, 0.42), (0.30, 0.045, 0.16), "paint_red" if damaged else "paint_blue", 0.006)
        add_upgrade_materials(level, state)
    if level >= 3:
        add_tank("protected_reservoir", -1.18, -0.46, level, damaged=damaged, ruined=ruined)
        beam("aeolian_feed_line", (0.88, 0.36, 0.34), (0.24, 0.10, 0.68), 0.030, "aeolian")
        cylinder("amber_pressure_gauge", (0.62, 0.02, 0.68), 0.058, 0.032, "amber", vertices=14, rotation=(math.pi / 2, 0, 0), bevel=True)
        box("reinforced_beam_crate", (1.24, 0.92, 0.17), (0.48, 0.30, 0.24), "reinforced", 0.018)

    if construction:
        box("stacked_planks", (-0.98, -0.42, 0.14), (0.68, 0.22, 0.12), "wood", 0.014, rotation=(0, 0, 0.12))
        box("mechanism_crate", (1.14, 0.82, 0.15), (0.38, 0.30, 0.24), "metal", 0.016)
        for i in range(3):
            beam(f"loose_pipe_{i}", (-1.12 + i * 0.16, -0.92, 0.08), (-0.76 + i * 0.14, -0.70, 0.10), 0.020, "dark_metal")
    if damaged:
        beam("broken_pipe_leak", (0.24, -0.28, 0.14), (0.86, -0.68, 0.08), 0.036, "dark_metal")
        box("warning_lamp", (0.58, -0.20, 0.70), (0.08, 0.08, 0.12), "amber", 0.010)
        box("charred_deck_gap", (-0.28, -0.50, 0.16), (0.34, 0.16, 0.035), "char", 0.006, rotation=(0, 0, 0.18))
    if ruined:
        for i, (x, y, rot) in enumerate(((-0.60, -0.96, -0.20), (-0.10, -1.10, 0.34), (0.42, -0.92, -0.48), (0.92, 0.18, 0.12))):
            box(f"ruin_debris_plank_{i}", (x, y, 0.10), (0.48, 0.12, 0.08), "char" if i % 2 else "wood", 0.010, rotation=(0.08, 0.0, rot))
        box("smashed_pump_block", (0.42, -0.30, 0.16), (0.46, 0.28, 0.20), "dark_metal", 0.018, rotation=(0.0, 0.12, -0.36))


def build_collection(level, state):
    global CURRENT_COLLECTION
    name = f"{ASSET_ID}_l{level:02d}_{state}"
    collection = bpy.data.collections.new(name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[name] = collection
    CURRENT_COLLECTION = collection
    add_ground(level, state)
    add_derrick(level, state)
    add_level_equipment(level, state)
    apply_mesh_cleanup(collection)
    collection["level"] = level
    collection["state"] = state
    return collection


def setup_scene():
    global SCENE
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for material_item in list(bpy.data.materials):
        if material_item.name.startswith("MAT_oil_well_"):
            bpy.data.materials.remove(material_item)
    SCENE = bpy.data.scenes.new("Real_City_Oil_Well_Models")
    bpy.context.window.scene = SCENE
    setup_materials()
    real_city_scene.configure_asset_scene(SCENE, RenderProfile(), light_prefix="oil_well")


def show_only(name):
    for key, collection in COLLECTIONS.items():
        collection.hide_render = key != name
        collection.hide_viewport = key != name
    bpy.ops.object.select_all(action="DESELECT")
    for obj in COLLECTIONS[name].all_objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.update()


def mesh_triangles(collection):
    total = 0
    for obj in collection.all_objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            total += len(obj.data.loop_triangles)
    return total


def bounds(collection):
    coords = [obj.matrix_world @ Vector(corner) for obj in collection.all_objects if obj.type == "MESH" for corner in obj.bound_box]
    return [[round(min(v[i] for v in coords), 3) for i in range(3)], [round(max(v[i] for v in coords), 3) for i in range(3)]]


def alpha_bounds(path):
    try:
        from PIL import Image
        with Image.open(path) as image:
            bounds = image.getchannel("A").getbbox()
            return list(bounds) if bounds else None
    except Exception:
        pass

    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = image.size
        pixels = list(image.pixels)
        min_x, min_y = width, height
        max_x, max_y = -1, -1
        for y in range(height):
            row = y * width * 4
            for x in range(width):
                if pixels[row + x * 4 + 3] > 0.01:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 1)
        if max_x < 0:
            return None
        # Blender image pixels are bottom-up; report PIL-style top-left bounds.
        return [min_x, height - max_y, max_x, height - min_y]
    finally:
        bpy.data.images.remove(image)


def export_collection(name):
    show_only(name)
    glb_path = OUT_DIR / f"{name}.glb"
    png_path = OUT_DIR / f"{name}.png"
    SCENE.render.filepath = str(png_path)
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True, use_active_scene=True)
    collection = COLLECTIONS[name]
    level = int(collection["level"])
    state = str(collection["state"])
    REPORT[name] = {
        "id": name,
        "level": level,
        "state": state,
        "png": png_path.name,
        "glb": glb_path.name,
        "triangles": mesh_triangles(collection),
        "bounds": bounds(collection),
        "alpha_bounds": alpha_bounds(png_path),
    }
    print("OIL_WELL_DONE", name, REPORT[name]["triangles"], flush=True)


def roundtrip_validate():
    previous = bpy.context.window.scene
    qa = bpy.data.scenes.new("Oil_Well_Roundtrip_QA")
    bpy.context.window.scene = qa
    results = []
    try:
        for name in sorted(REPORT):
            bpy.ops.import_scene.gltf(filepath=str(OUT_DIR / f"{name}.glb"))
            triangles = 0
            loose_vertices = 0
            for obj in list(qa.objects):
                if obj.type != "MESH":
                    continue
                obj.data.calc_loop_triangles()
                triangles += len(obj.data.loop_triangles)
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                loose_vertices += len([vert for vert in bm.verts if not vert.link_edges])
                bm.free()
            results.append({"name": name, "triangles": triangles, "loose_vertices": loose_vertices})
            REPORT[name]["triangles"] = triangles
            bpy.data.batch_remove(ids=list(qa.objects))
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa)
    ROUNDTRIP_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _merge_items(existing_items, new_items):
    merged = {item["id"]: item for item in existing_items or [] if "id" in item}
    for item in new_items:
        merged[item["id"]] = item
    return [merged[name] for name in sorted(merged, key=lambda key: (merged[key].get("level", 0), STATES.index(merged[key].get("state", "active")) if merged[key].get("state") in STATES else 99))]


def write_manifest():
    entries = [REPORT[name] for name in sorted(REPORT, key=lambda key: (REPORT[key]["level"], STATES.index(REPORT[key]["state"])))]
    existing_manifest = _load_json(OUT_DIR / "manifest.json") or {}
    manifest_entries = _merge_items(existing_manifest.get("assets", existing_manifest.get("items", [])), entries)
    manifest = {
        "asset_id": ASSET_ID,
        "building_type": "oil_well",
        "category": "industry",
        "display_name": "Нефтяная вышка",
        "levels": list(LEVELS),
        "states": list(STATES),
        "anchor": [256, 292],
        "size": [512, 384],
        "sprite": {"size": [512, 384], "anchor": [256, 292]},
        "source": BLEND_PATH.name,
        "generator": "tools/assets/blender/generate_oil_well_models.py",
        "revision": REVISION,
        "style": "Aeolian bright fantasy stylized mid-poly",
        "runtime_integration": "connected to frontend building registry through oil_well asset family",
        "backup_of_previous_runtime": BACKUP_NAME,
        "assets": manifest_entries,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    existing_report = _load_json(REPORT_PATH) or {}
    report_entries = _merge_items(existing_report.get("items", []), entries)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "asset_id": ASSET_ID,
                "revision": REVISION,
                "items": report_entries,
                "material_resources": {
                    "metal": "level 1 worn metal pump, fasteners, bands and barrels",
                    "planks": "level 1 plank deck, wooden derrick beams, tool crate and construction stacks",
                    "oil": "deep black open oil pit, visible front shaft and localized damaged-state leaks",
                },
                "backup_of_previous_runtime": BACKUP_NAME,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def contact_sheet():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    columns = len(STATES)
    rows = len(LEVELS)
    cell_w = 512
    cell_h = 412
    sheet = Image.new("RGBA", (columns * cell_w, rows * cell_h), (234, 239, 232, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 14) if font_path.is_file() else ImageFont.load_default()
    for row, level in enumerate(LEVELS):
        for col, state in enumerate(STATES):
            name = f"{ASSET_ID}_l{level:02d}_{state}"
            with Image.open(OUT_DIR / f"{name}.png") as image:
                sheet.alpha_composite(image, (col * cell_w, row * cell_h))
            draw.text((col * cell_w + 8, row * cell_h + 388), name, fill=(30, 38, 34, 255), font=font)
    sheet.save(CONTACT_SHEET_PATH)


def preview_contact_sheet(names):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    if not names:
        return
    cell_w = 512
    cell_h = 412
    sheet = Image.new("RGBA", (cell_w * len(names), cell_h), (234, 239, 232, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 14) if font_path.is_file() else ImageFont.load_default()
    for col, name in enumerate(names):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            sheet.alpha_composite(image, (col * cell_w, 0))
        draw.text((col * cell_w + 8, 388), name, fill=(30, 38, 34, 255), font=font)
    sheet.save(OUT_DIR / "oil_well_l01_active_preview.png")


def write_notes():
    note = bpy.data.texts.new("oil_well_asset_notes")
    note.write(
        "Real City oil derrick levels 1-3, states active/construction/damaged/ruined. "
        "The asset is a building placed only on an oil_well terrain/resource node. "
        "The 2026-10-14 style revision increases the runtime footprint to match other Real City buildings, keeps the terrain cell bright, and uses larger readable props. "
        "Ground keeps the dark oil seep visible in every state without making the whole asset gloomy. "
        "Level 1 uses wood/planks/rope with a broad simple derrick, tool crate and barrels; level 2 adds concrete supports, pipes, mechanisms, painted panels and tank; "
        "level 3 adds reinforced/dark metal, protected reservoirs, amber warning accents and aeolian alloy line. "
        "Construction variants intentionally omit 30-45 percent of the upper frame and show loose materials. "
        "Damaged variants bend the derrick, leak oil and break pipes. Ruined variants collapse the frame and leave debris over the oil source."
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--levels", default=",".join(str(level) for level in LEVELS), help="Comma-separated levels to generate.")
    parser.add_argument("--states", default=",".join(STATES), help="Comma-separated states to generate.")
    parser.add_argument("--exclude", default="", help="Comma-separated asset ids to leave untouched, for example oil_well_l01_active.")
    parser.add_argument("--preview-only", action="store_true", help="Write a small preview contact sheet instead of the full family sheet.")
    return parser.parse_args()


def _parse_levels(value):
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def _parse_states(value):
    states = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = [state for state in states if state not in STATES]
    if unknown:
        raise SystemExit(f"Unknown states: {', '.join(unknown)}")
    return states


def main():
    args = parse_args()
    levels = _parse_levels(args.levels)
    states = _parse_states(args.states)
    excluded = {item.strip() for item in args.exclude.split(",") if item.strip()}
    setup_scene()
    write_notes()
    for level in levels:
        for state in states:
            if f"{ASSET_ID}_l{level:02d}_{state}" in excluded:
                continue
            build_collection(level, state)
    for name in sorted(COLLECTIONS, key=lambda key: (COLLECTIONS[key]["level"], STATES.index(COLLECTIONS[key]["state"]))):
        export_collection(name)
    roundtrip_validate()
    write_manifest()
    if args.preview_only:
        preview_contact_sheet(sorted(COLLECTIONS, key=lambda key: (COLLECTIONS[key]["level"], STATES.index(COLLECTIONS[key]["state"]))))
    else:
        contact_sheet()
    for collection in COLLECTIONS.values():
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(json.dumps({"generated": len(REPORT), "out": str(OUT_DIR)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
