"""Generate Real City glass workshop levels 1-12 in the shared building style."""

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
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "glass_workshop"
BLEND_PATH = OUT_DIR / "glass_workshop_levels.blend"
GLB_PATH = OUT_DIR / "glass_workshop_levels.glb"
REPORT_PATH = OUT_DIR / "generation-report.json"
MANIFEST_PATH = OUT_DIR / "manifest.json"

ASSET_ID = "glass_workshop"
LEVELS = range(1, 13)
STATES = ("active", "construction", "damaged", "idle_no_input", "idle_no_fuel", "ready", "ruined")

spec = importlib.util.spec_from_file_location("housing_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def add_material(role: str, color, roughness: float = 0.78, metallic: float = 0.0, alpha: float = 1.0, emission=None, emission_strength: float = 0.0):
    mat = bpy.data.materials.new("MAT_glass_workshop_" + role)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    if alpha < 1:
        mat.blend_method = "BLEND"
        mat.show_transparent_back = True
    bsdf = shader(mat)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (*color, alpha)
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
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
            material.name = material.name.replace("MAT_housing_", "MAT_glass_base_")
    # Same terrain family as mine/sand quarry/lumber yard.
    H.MATS["grass"].diffuse_color = (0.26, 0.48, 0.08, 1)
    bsdf = shader(H.MATS["grass"])
    if bsdf and "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (0.26, 0.48, 0.08, 1)
    add_material("earth_warm", (0.55, 0.36, 0.18), 0.92)
    add_material("packed_dust", (0.69, 0.53, 0.28), 0.94)
    add_material("sand", (0.92, 0.70, 0.34), 0.88)
    add_material("sand_light", (1.00, 0.81, 0.42), 0.86)
    add_material("clay", (0.70, 0.36, 0.19), 0.86)
    add_material("brick", (0.58, 0.22, 0.12), 0.84)
    add_material("stone_light", (0.62, 0.60, 0.50), 0.86)
    add_material("stone_shadow", (0.39, 0.37, 0.32), 0.9)
    add_material("wood_pale", (0.78, 0.52, 0.24), 0.72)
    add_material("wood_dark", (0.34, 0.18, 0.08), 0.82)
    add_material("canvas", (0.78, 0.64, 0.40), 0.84)
    add_material("rope", (0.70, 0.49, 0.22), 0.88)
    add_material("iron", (0.38, 0.41, 0.39), 0.48, 0.36)
    add_material("iron_dark", (0.14, 0.15, 0.14), 0.58, 0.45)
    add_material("copper", (0.86, 0.45, 0.20), 0.44, 0.38)
    add_material("steel", (0.60, 0.64, 0.60), 0.38, 0.60)
    add_material("brass", (0.84, 0.56, 0.22), 0.42, 0.38)
    add_material("concrete", (0.55, 0.57, 0.52), 0.86)
    add_material("reinforced_concrete", (0.43, 0.45, 0.43), 0.82)
    add_material("premium_wood", (0.82, 0.56, 0.25), 0.64)
    add_material("coal", (0.035, 0.032, 0.030), 0.86)
    add_material("char", (0.050, 0.040, 0.032), 0.95)
    add_material("heat", (1.00, 0.46, 0.12), 0.42, 0.0, 1.0, (1.0, 0.34, 0.06), 0.85)
    add_material("heat_dim", (0.35, 0.13, 0.05), 0.74, 0.0, 1.0, (0.20, 0.05, 0.01), 0.08)
    add_material("glass_cyan", (0.47, 0.84, 0.90), 0.18, 0.0, 0.48, (0.18, 0.52, 0.58), 0.10)
    add_material("glass_edge", (0.22, 0.62, 0.70), 0.28, 0.0, 0.72)
    add_material("glass_broken", (0.58, 0.90, 0.95), 0.34, 0.0, 0.44)
    add_material("star_glass", (0.55, 0.31, 0.94), 0.22, 0.0, 0.60, (0.36, 0.12, 0.82), 0.38)
    add_material("light_crystal", (0.42, 0.92, 1.0), 0.18, 0.0, 0.62, (0.20, 0.70, 1.0), 0.45)


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


def frustum(name, cx, cy, z, rx, ry, height, top_scale, role, rings=4, segments=18, wobble=0.025):
    verts, faces = [], []
    for ring in range(rings):
        t = ring / (rings - 1)
        scale = 1 + (top_scale - 1) * t
        for i in range(segments):
            angle = math.tau * i / segments
            wave = 1 + wobble * math.sin(angle * 3.0 + t * 1.6)
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


def pane(name, x, y, z, width, height, angle=0.0, broken=False, star=False):
    mat = "star_glass" if star else ("glass_broken" if broken else "glass_cyan")
    H.box(name + "_sheet", (x, y, z), (width, 0.040, height), mat, 0.010, rotation=(0.0, 0.0, angle))
    H.box(name + "_edge_top", (x, y - 0.004, z + height * 0.52), (width + 0.060, 0.052, 0.028), "glass_edge", 0.004, rotation=(0.0, 0.0, angle))
    H.box(name + "_edge_bottom", (x, y - 0.004, z - height * 0.52), (width + 0.060, 0.052, 0.028), "glass_edge", 0.004, rotation=(0.0, 0.0, angle))
    if broken:
        H.beam(name + "_crack_a", (x - width * 0.32, y - 0.036, z + height * 0.18), (x + width * 0.28, y - 0.036, z - height * 0.20), 0.010, "glass_edge")
        H.beam(name + "_crack_b", (x - width * 0.12, y - 0.038, z - height * 0.18), (x + width * 0.12, y - 0.038, z + height * 0.22), 0.009, "glass_edge")


def sack(name, x, y, z, role="sand"):
    obj = frustum(name, x, y, z, 0.16, 0.115, 0.19, 0.74, role, rings=4, segments=14, wobble=0.05)
    obj.rotation_euler.z = 0.25 * math.sin(x * 6.3 + y * 4.1)
    H.beam(name + "_tie", (x - 0.11, y, z + 0.16), (x + 0.11, y, z + 0.16), 0.014, "rope")
    return obj


def crate(name, x, y, z, sx, sy, sz, role="wood_pale", empty=False):
    H.box(name + "_base", (x, y, z), (sx, sy, sz), role, 0.018)
    for dx in (-sx * 0.44, sx * 0.44):
        H.box(name + "_side_x", (x + dx, y, z + sz * 0.18), (0.035, sy * 1.05, sz * 0.62), "wood_dark", 0.006)
    for dy in (-sy * 0.44, sy * 0.44):
        H.box(name + "_side_y", (x, y + dy, z + sz * 0.18), (sx * 1.05, 0.035, sz * 0.62), "wood_dark", 0.006)
    if not empty:
        H.box(name + "_fill", (x, y, z + sz * 0.58), (sx * 0.76, sy * 0.72, sz * 0.18), "sand_light", 0.010)


def ground():
    H.base()
    H.box("workpad_stone_dust", (0.04, -0.05, 0.110), (2.42, 1.74, 0.070), "packed_dust", 0.035, rotation=(0, 0, 0.04))
    H.box("front_paver_left", (-0.35, -1.22, 0.155), (0.52, 0.24, 0.055), "stone_light", 0.020, rotation=(0, 0, -0.08))
    H.box("front_paver_right", (0.23, -1.17, 0.155), (0.48, 0.22, 0.055), "stone_light", 0.020, rotation=(0, 0, 0.05))
    H.box("sand_spill", (-0.96, -0.54, 0.160), (0.70, 0.42, 0.040), "sand", 0.018, rotation=(0, 0, -0.18))
    for i, (x, y, sx, sy) in enumerate(((-1.24, 0.50, 0.24, 0.14), (1.16, 0.56, 0.22, 0.13), (-1.30, -0.52, 0.18, 0.12), (1.18, -0.66, 0.20, 0.12))):
        frustum(f"yard_edge_pebble_{i}", x, y, 0.145, sx, sy, 0.09, 0.55, "stone_light", rings=3, segments=10, wobble=0.06)
    for obj in H.COL.objects:
        obj["ground"] = True


def furnace(level, state):
    construction = state == "construction"
    damaged = state in ("damaged", "ruined")
    no_fuel = state == "idle_no_fuel"
    if construction:
        foundation_role = "reinforced_concrete" if level >= 8 else ("concrete" if level >= 6 else "stone_light")
        H.box("furnace_foundation_blocks", (0.05, -0.04, 0.265), (1.05 + min(level, 8) * 0.025, 0.78 + min(level, 8) * 0.015, 0.22), foundation_role, 0.030)
        H.box("half_firebox_left", (-0.24, -0.34, 0.545), (0.36, 0.16, 0.50), "brick" if level >= 4 else "clay", 0.024)
        H.box("half_firebox_right", (0.33, -0.34, 0.485), (0.26, 0.15, 0.38), "brick" if level >= 4 else "clay", 0.024)
        for x in (-0.55, 0.58):
            H.beam("temporary_furnace_upright", (x, -0.42, 0.16), (x, -0.42, 1.08 + min(level, 9) * 0.045), 0.045, "wood_dark" if level < 7 else "iron")
        H.beam("loose_arch_form", (-0.54, -0.42, 1.00 + level * 0.05), (0.56, -0.42, 1.10 + level * 0.05), 0.040, "wood_pale")
        if level >= 5:
            H.box("unmounted_copper_pipe", (0.55, 0.18, 0.48), (0.36, 0.055, 0.055), "copper", 0.010, rotation=(0, 0, 0.28))
        if level >= 8:
            H.box("stacked_reinforced_forms", (0.72, 0.62, 0.24), (0.42, 0.18, 0.16), "reinforced_concrete", 0.018)
        return

    if damaged:
        body_role = "char"
    elif level >= 8:
        body_role = "concrete"
    elif level >= 4:
        body_role = "brick"
    elif level >= 2:
        body_role = "brick"
    else:
        body_role = "clay"
    if damaged:
        cap_role = "stone_shadow"
    elif level >= 8:
        cap_role = "reinforced_concrete"
    elif level >= 3:
        cap_role = "stone_light"
    else:
        cap_role = "clay"
    loss = 0.60 if state == "ruined" else 1.0
    growth = min(level - 1, 9)
    body_x = 1.10 + growth * 0.035
    body_y = 0.82 + growth * 0.020
    body_z = 0.60 + growth * 0.018
    H.box("kiln_block_lower", (0.05, -0.04, (0.30 + body_z * 0.20) * loss), (body_x, body_y, body_z * loss), body_role, 0.055)
    frustum("rounded_kiln_crown", 0.05, -0.04, (0.52 + body_z * 0.33) * loss, 0.61 + growth * 0.018, 0.47 + growth * 0.014, (0.44 + growth * 0.010) * loss, 0.58, cap_role, rings=5, segments=24, wobble=0.025)
    if state != "ruined":
        H.box("iron_firebox_frame", (0.05, -0.485, 0.410), (0.58, 0.11, 0.36), "iron_dark", 0.022)
        H.box("firebox_glow", (0.05, -0.550, 0.410), (0.42, 0.040, 0.235), "heat_dim" if no_fuel or damaged else "heat", 0.010)
        H.box("ash_lip", (0.05, -0.635, 0.230), (0.72, 0.18, 0.095), "stone_shadow", 0.016)
    else:
        H.box("collapsed_firebox_black", (-0.02, -0.48, 0.245), (0.80, 0.18, 0.25), "char", 0.018, rotation=(0, 0, -0.09))

    if level >= 2 and state != "ruined":
        cylinder("short_round_chimney", (0.36, 0.35, 1.18 + min(level, 8) * 0.025), 0.135 + min(level, 8) * 0.004, 0.58 + min(level, 8) * 0.025, "stone_shadow" if damaged else ("concrete" if level >= 8 else "brick"), segments=16)
        cylinder("chimney_rim", (0.36, 0.35, 1.50 + min(level, 8) * 0.040), 0.18, 0.09, "steel" if level >= 6 and not damaged else ("iron" if not damaged else "char"), segments=16)
    if level >= 3 and state != "ruined":
        H.box("stone_quality_shelf", (0.76, -0.06, 0.63), (0.13, 0.72, 0.08), "stone_light", 0.012)
        pane("quality_test_pane", 0.82, -0.06, 0.88, 0.045, 0.42, broken=damaged)
        cylinder("small_copper_thermostat", (-0.44, -0.44, 0.67), 0.060, 0.055, "copper", axis=(0, 1, 0), segments=12)
    if level >= 4 and state != "ruined":
        H.beam("copper_heat_pipe_left", (-0.52, 0.20, 0.52), (-0.52, 0.58, 1.06), 0.024, "copper" if not damaged else "char")
        H.beam("copper_heat_pipe_right", (0.56, 0.20, 0.52), (0.56, 0.58, 1.06), 0.024, "copper" if not damaged else "char")
    if level >= 6 and state != "ruined":
        H.box("mechanical_feed_housing", (-0.55, 0.40, 0.45), (0.30, 0.36, 0.30), "iron" if not damaged else "char", 0.020)
        cylinder("feed_gear", (-0.55, 0.18, 0.52), 0.12, 0.050, "brass" if not damaged else "char", axis=(0, 1, 0), segments=14)
    if level >= 8 and state != "ruined":
        H.box("reinforced_kiln_band_front", (0.05, -0.51, 0.76), (1.26, 0.075, 0.090), "steel" if not damaged else "char", 0.012)
        H.box("operator_side_panel", (0.70, -0.38, 0.58), (0.14, 0.20, 0.32), "iron" if not damaged else "char", 0.012)
    if level >= 10 and state != "ruined":
        pane("optical_calibration_lens", -0.70, -0.38, 0.86, 0.12, 0.18, star=True)
        cylinder("lens_brass_mount", (-0.70, -0.39, 0.86), 0.115, 0.035, "brass" if not damaged else "char", axis=(0, 1, 0), segments=16)
    if level >= 11 and state != "ruined":
        pane("light_crystal_probe", 0.48, -0.48, 0.88, 0.075, 0.16, star=True)


def inputs_and_fuel(level, state):
    no_input = state == "idle_no_input"
    no_fuel = state == "idle_no_fuel"
    ruined = state == "ruined"
    if no_input or ruined:
        crate("empty_sand_hopper", -0.94, -0.31, 0.245, 0.54, 0.42, 0.24, "wood_dark", empty=True)
    else:
        crate("sand_hopper", -0.94, -0.31, 0.255, 0.56, 0.44, 0.26, "wood_pale" if level < 7 else "premium_wood")
        for idx in range(min(3 + level, 8)):
            sack(f"sand_sack_{idx}", -1.18 + 0.18 * (idx % 3), -0.72 + 0.16 * (idx // 3), 0.170)
        if level >= 6 and state != "construction":
            H.beam("mechanical_sand_chute", (-0.70, -0.18, 0.48), (-0.30, 0.04, 0.68), 0.040, "iron")
    if state == "construction":
        return
    if no_fuel or ruined:
        crate("empty_coal_box", 0.88, -0.68, 0.215, 0.44, 0.34, 0.20, "wood_dark", empty=True)
    else:
        crate("coal_box", 0.88, -0.68, 0.215, 0.44, 0.34, 0.20, "wood_dark", empty=True)
        for idx in range(5):
            cylinder(f"coal_lump_{idx}", (0.76 + 0.055 * idx, -0.68 + 0.035 * (idx % 2), 0.35), 0.042, 0.042, "coal", segments=7)
        if level >= 6:
            for idx, x in enumerate((1.08, 1.26)):
                cylinder(f"late_fuel_canister_{idx}", (x, -0.34, 0.34), 0.075, 0.32, "iron" if state != "damaged" else "char", segments=12)
                H.box(f"late_fuel_cap_{idx}", (x, -0.34, 0.52), (0.11, 0.11, 0.04), "brass" if state != "damaged" else "char", 0.006)


def bench_and_racks(level, state):
    construction = state == "construction"
    damaged = state in ("damaged", "ruined")
    if construction:
        for idx in range(5):
            H.box("stacked_construction_board", (-0.72 + idx * 0.12, 0.76, 0.18 + idx * 0.038), (0.62, 0.095, 0.060), "wood_pale", 0.010, rotation=(0, 0, 0.10))
        H.box("loose_forming_tabletop", (-0.40, -0.94, 0.260), (0.86, 0.32, 0.095), "wood_pale", 0.014, rotation=(0, 0, -0.08))
        H.beam("unfixed_table_leg_a", (-0.74, -1.06, 0.14), (-0.66, -0.88, 0.40), 0.025, "wood_dark")
        H.beam("unfixed_table_leg_b", (0.00, -1.03, 0.12), (0.04, -0.86, 0.36), 0.025, "wood_dark")
        return

    H.box("forming_tabletop", (-0.36, -0.96, 0.335), (0.96, 0.36, 0.13), "char" if damaged else "wood_pale", 0.025, rotation=(0, 0, -0.06))
    for x in (-0.78, 0.06):
        H.beam("forming_table_leg", (x, -1.08, 0.15), (x, -1.02, 0.33), 0.036, "wood_dark")
    H.beam("blowing_pipe", (-0.84, -0.95, 0.47), (0.22, -1.05, 0.52), 0.018, "iron")
    H.beam("iron_tongs", (-0.65, -0.82, 0.45), (-0.18, -0.82, 0.45), 0.018, "iron")

    rack_role = "char" if damaged else ("iron" if level >= 3 else "wood_dark")
    rack_height = 0.82 + min(max(level - 3, 0), 6) * 0.035 if level >= 2 else 0.62
    for x in (-0.38, 0.30):
        H.beam("cooling_rack_upright", (x, 0.76, 0.15), (x, 0.76, rack_height), 0.030, rack_role)
    H.beam("cooling_rack_top", (-0.42, 0.76, rack_height), (0.34, 0.76, rack_height), 0.028, rack_role)
    sheet_count = min(1 + level, 6)
    for idx in range(sheet_count):
        pane(f"cooling_sheet_{idx}", -0.34 + idx * 0.14, 0.73, 0.42 + 0.04 * (idx % 2), 0.28, 0.33, broken=damaged)
    if level >= 3:
        H.box("inspection_tool_rail", (-0.86, 0.25, 0.62), (0.10, 0.70, 0.08), "wood_dark", 0.010)
        for y in (0.04, 0.22, 0.40):
            H.beam("hanging_tongs", (-0.86, y, 0.25), (-0.86, y + 0.04, 0.72), 0.012, "iron")
        pane("tiny_star_glass_sample", -0.56, 0.34, 0.49, 0.10, 0.14, star=True)
    if level >= 7:
        H.box("protected_sorting_drawer", (0.48, 0.48, 0.34), (0.38, 0.28, 0.18), "premium_wood" if not damaged else "char", 0.016)
        H.beam("steel_sorting_handle", (0.34, 0.31, 0.40), (0.62, 0.31, 0.40), 0.014, "steel" if not damaged else "char")
    if level >= 9:
        H.box("optical_blank_case", (0.82, 0.05, 0.34), (0.26, 0.34, 0.18), "steel" if not damaged else "char", 0.014)
        pane("case_star_glass_hint", 0.82, -0.13, 0.48, 0.10, 0.12, star=True)


def canopy(level, state):
    if level < 2 or state == "ruined":
        return
    construction = state == "construction"
    damaged = state == "damaged"
    post_role = "char" if damaged else "wood_dark"
    for x, y in ((-0.76, 0.58), (0.64, 0.58), (-0.76, -0.18), (0.64, -0.18)):
        if construction and x > 0.4 and y > 0.4:
            continue
        top = 1.10 + 0.08 * level - (0.22 if damaged and x < -0.5 else 0)
        H.beam("canopy_post", (x, y, 0.13), (x, y, top), 0.046, post_role)
    if construction:
        H.beam("partial_canopy_lintel", (-0.80, 0.58, 1.14), (0.18, 0.58, 1.22), 0.040, "wood_dark")
        H.box("half_canopy_roof", (-0.42, 0.24, 1.25), (0.88, 0.74, 0.080), "canvas", 0.016, rotation=(0.10, 0.03, -0.06))
        return
    if damaged:
        H.beam("collapsed_canopy_beam", (-0.82, 0.58, 0.96), (0.58, -0.18, 0.56), 0.046, "char")
        H.box("torn_canopy_panel", (-0.18, 0.28, 0.74), (1.10, 0.58, 0.055), "canvas", 0.012, rotation=(0.34, -0.08, -0.16))
        if level >= 8:
            H.box("fallen_steel_roof_plate", (0.34, 0.28, 0.32), (0.72, 0.20, 0.055), "char", 0.010, rotation=(0.18, 0.04, -0.32))
        return
    roof_role = "steel" if level >= 10 else ("concrete" if level >= 8 else "canvas")
    lip_role = "steel" if level >= 8 else "wood_dark"
    roof_z = 1.26 + min(level, 9) * 0.04
    H.box("wind_bent_canvas_roof", (-0.05, 0.22, roof_z), (1.66, 1.04, 0.085), roof_role, 0.025, rotation=(0.10, 0.02, -0.045))
    H.box("front_roof_lip", (-0.05, -0.34, roof_z - 0.06), (1.72, 0.10, 0.10), lip_role, 0.014, rotation=(0.10, 0.02, -0.045))
    if level >= 3:
        cylinder("small_copper_roof_vent", (-0.45, 0.60, 1.48 + min(level, 7) * 0.025), 0.095, 0.12, "copper" if level < 8 else "brass", segments=12)
        for angle in (0, math.pi / 2):
            H.box("tiny_wind_vent_blade", (-0.45, 0.60, 1.58 + min(level, 7) * 0.025), (0.34, 0.030, 0.045), "copper" if level < 8 else "brass", 0.004, rotation=(0, 0, angle))
    if level >= 8:
        for x in (-0.70, 0.58):
            H.beam("reinforced_roof_strut", (x, -0.24, roof_z - 0.18), (x, 0.64, roof_z - 0.06), 0.025, "steel")


def ready_output(level):
    H.box("packed_output_crate", (0.80, 0.38, 0.235), (0.52, 0.38, 0.22), "premium_wood" if level >= 7 else "wood_pale", 0.018)
    for idx in range(min(2 + level, 7)):
        pane(f"ready_glass_stack_{idx}", 0.62 + 0.055 * idx, 0.36, 0.45 + idx * 0.042, 0.27, 0.22, angle=0.04)
    if level >= 9:
        pane("ready_optical_blank", 0.98, 0.24, 0.58, 0.12, 0.16, star=True)
    if level >= 11:
        pane("ready_light_crystal_sample", 0.54, 0.18, 0.66, 0.08, 0.14, star=True)


def damage_debris(level, state):
    if state not in ("damaged", "ruined"):
        return
    count = 7 if state == "damaged" else 12
    for idx in range(count):
        x = -0.72 + 0.28 * (idx % 6)
        y = -0.10 + 0.25 * (idx // 6)
        role = "glass_broken" if idx % 3 == 0 else ("char" if idx % 2 else "stone_shadow")
        H.box("fallen_shard_or_brick", (x, y, 0.185 + idx * 0.004), (0.22, 0.070, 0.045), role, 0.006, rotation=(0, 0, idx * 0.37))
    if state == "ruined":
        H.beam("fallen_chimney_piece", (0.30, 0.36, 0.20), (0.86, 0.10, 0.32), 0.075, "char")
        H.box("collapsed_cooling_rack", (-0.16, 0.76, 0.235), (0.78, 0.08, 0.08), "iron_dark", 0.010, rotation=(0, 0, -0.26))
        H.beam("broken_roof_prop", (-0.72, 0.54, 0.24), (-0.08, 0.16, 0.70), 0.040, "char")


def workshop(level, state):
    H.PREFIX = f"{ASSET_ID}_l{level:02d}_{state}"
    H.COL = bpy.data.collections.new(H.PREFIX)
    bpy.context.scene.collection.children.link(H.COL)
    ground()
    furnace(level, state)
    inputs_and_fuel(level, state)
    bench_and_racks(level, state)
    canopy(level, state)
    if state == "ready":
        ready_output(level)
    if state == "idle_no_input":
        H.box("input_empty_marker_plank", (-1.02, 0.02, 0.25), (0.34, 0.08, 0.07), "wood_dark", 0.008, rotation=(0, 0, -0.28))
    if state == "idle_no_fuel":
        H.box("cold_firebox_plate", (0.05, -0.555, 0.410), (0.44, 0.035, 0.24), "iron_dark", 0.006)
    damage_debris(level, state)
    H.clean_meshes(H.COL)
    H.COL["asset_id"] = ASSET_ID
    H.COL["level"] = level
    H.COL["state"] = state
    H.COL["style_reference"] = "Real City mine/sand_quarry/town_hall/dugout bright stylized mid-poly"
    return H.COL


def clear_previous_build():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(ASSET_ID + "_") or obj.name.startswith(("housing_", "glass_workshop_")):
            bpy.data.objects.remove(obj)
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Glass_Workshop") or scene.name.startswith("Glass_Workshop_Roundtrip"):
            bpy.data.scenes.remove(scene)
    for collection in list(bpy.data.collections):
        if collection.name.startswith(ASSET_ID + "_"):
            bpy.data.collections.remove(collection)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith(ASSET_ID + "_"):
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_glass_workshop_") or material.name.startswith("MAT_glass_base_"):
            bpy.data.materials.remove(material)


def hide_all(collections):
    for collection in collections:
        collection.hide_render = True
        collection.hide_viewport = True


def select_collection(collection):
    bpy.ops.object.select_all(action="DESELECT")
    first = None
    for obj in collection.all_objects:
        obj.select_set(True)
        if first is None:
            first = obj
    bpy.context.view_layer.objects.active = first


def bounds(collection):
    coords = [obj.matrix_world @ Vector(corner) for obj in collection.all_objects if obj.type == "MESH" for corner in obj.bound_box]
    return [[round(min(v[i] for v in coords), 4), round(max(v[i] for v in coords), 4)] for i in range(3)]


def triangles(collection):
    total = 0
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total


def alpha_bounds(path):
    # Blender's bundled Python on Windows does not necessarily include Pillow.
    # The repository-side validation fills exact bounds after generation.
    return None


def contact_sheet():
    # Built locally by the repository validation step, not inside Blender.
    return None


def write_manifest(report):
    items = []
    for level in LEVELS:
        for state in STATES:
            name = f"{ASSET_ID}_l{level:02d}_{state}"
            items.append({
                "id": name,
                "level": level,
                "state": state,
                "glb": f"frontend/public/assets/buildings/industry/glass_workshop/{name}.glb",
                "png": f"frontend/public/assets/buildings/industry/glass_workshop/{name}.png",
                "triangles": report[name]["triangles"],
                "alpha_bounds": report[name]["alpha_bounds"],
            })
    manifest = {
        "asset_id": ASSET_ID,
        "display_name": "Стекольная мастерская",
        "category": "industry",
        "levels": list(LEVELS),
        "states": list(STATES),
        "source_blend": "frontend/public/assets/buildings/industry/glass_workshop/glass_workshop_levels.blend",
        "combined_glb": "frontend/public/assets/buildings/industry/glass_workshop/glass_workshop_levels.glb",
        "style_reference": "dugout, mine, sand_quarry, town_hall Real City bright stylized mid-poly",
        "material_map": {
            "доски": "навес, стойки, верстак, ящики и строительные леса",
            "камень": "основание, плашки рабочей площадки и ранний фундамент печи",
            "песок": "мешки, песчаный бункер и россыпь на земле",
            "глина": "тело ранней печи и недостроенный огнеупорный блок",
            "каменные блоки": "усиленный фундамент и контрольная полка уровня 3",
            "инструменты": "щипцы, выдувная труба и инструментальная рейка",
            "кирпичи": "кирпичный корпус печи уровней 4-7",
            "медные детали": "тепловые трубы, вентиль и датчик температуры",
            "механизмы": "механическая подача песка и шестерни",
            "железные слитки": "стойки, корпус подачи, крепеж и защитные ручки",
            "железобетон": "позднее основание и закрытый корпус печи",
            "усиленные балки": "стальные стропила и крышные усиления",
            "звездное стекло": "оптические линзы и калибровочные образцы",
        },
        "items": items,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(output=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    directory = Path(output or OUT_DIR)
    clear_previous_build()
    scene = bpy.data.scenes.new("Real_City_Glass_Workshop_Models")
    bpy.context.window.scene = scene
    scene.unit_settings.system = "METRIC"
    palette()
    H.setup_camera(scene)
    scene.cycles.samples = 18
    scene["style_reference"] = "Real City bright fantasy stylized mid-poly; scale/camera follows early housing, mine and sand_quarry generators."
    note = bpy.data.texts.new("glass_workshop_asset_notes")
    note.write(
        "Glass workshop l01-l12 generated in the same Real City style as dugouts, mines, sand quarries and town hall: "
        "shared ground scale, warm daylight, bright materials, bevelled mid-poly forms, oversized readable props. "
        "Levels 4-12 follow the user's explicit asset request and add brick, copper, mechanisms, steel, reinforced concrete and optical glass accents."
    )

    report, collections = {}, []
    for level in LEVELS:
        for state in STATES:
            collection = workshop(level, state)
            hide_all(collections)
            collection.hide_render = False
            collection.hide_viewport = False
            bpy.context.view_layer.update()
            select_collection(collection)
            name = collection.name
            glb_path = directory / f"{name}.glb"
            bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True, use_active_scene=True, export_extras=True)
            scene.render.filepath = str(directory / f"{name}.png")
            bpy.ops.render.render(write_still=True)
            report[name] = {
                "level": level,
                "state": state,
                "triangles": triangles(collection),
                "bounds": bounds(collection),
                "materials": sorted({mat.name for obj in collection.all_objects if obj.type == "MESH" for mat in obj.data.materials}),
                "alpha_bounds": alpha_bounds(directory / f"{name}.png"),
                "style": "bright fantasy stylized mid-poly Blender",
            }
            collections.append(collection)
            REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("GLASS_WORKSHOP_DONE " + name, flush=True)

    hide_all(collections)
    for collection in collections:
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(directory / GLB_PATH.name), export_format="GLB", use_active_scene=True, export_extras=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(directory / BLEND_PATH.name))
    write_manifest(report)
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id=ASSET_ID,
            display_name="Стекольная мастерская",
            category="industry",
            output_dir=directory,
            levels=LEVELS,
            states=STATES,
            source_blend=directory / BLEND_PATH.name,
            combined_glb=directory / GLB_PATH.name,
            generator="tools/assets/blender/generate_glass_workshop_models.py",
            style_reference="Real City glass workshop migrated to shared scene/export/report layer",
        )
    )
    contact_sheet()
    print("GLASS_WORKSHOP_COMPLETE " + str(len(report)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main(args.output)
