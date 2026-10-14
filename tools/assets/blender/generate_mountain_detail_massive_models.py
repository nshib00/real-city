"""Generate separate massive mountain and mine staging models for Real City.

This does not replace the previous four mountain_detail_staging assets. New
files are written beside them with distinct names and a separate manifest.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "terrain" / "tiles" / "mountain_detail_staging"
BLEND_PATH = OUT_DIR / "mountain_detail_massive_staging.blend"
MANIFEST_PATH = OUT_DIR / "manifest_massive.json"
REPORT_PATH = OUT_DIR / "generation-report-massive.json"
ROUNDTRIP_PATH = OUT_DIR / "roundtrip-validation-massive.json"
CONTACT_SHEET_PATH = OUT_DIR / "mountain_detail_massive_contact_sheet.png"

spec = importlib.util.spec_from_file_location("terrain_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

MOUNTAIN_ASSETS = (
    "mountain_detail_ridge_massive",
    "mountain_detail_spire_massive",
    "mountain_detail_snowcap_massive",
)
MINE_STATES = ("active", "construction", "damaged")
MINE_ASSETS = tuple(
    f"mine_l{level:02d}_{state}_mountain_detail"
    for level in range(1, 13)
    for state in MINE_STATES
    if not (level == 1 and state == "active")
)
ASSETS = MOUNTAIN_ASSETS + MINE_ASSETS

COLLECTIONS: dict[str, bpy.types.Collection] = {}
REPORT: dict[str, dict] = {}
SCENE = None


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def add_material(role, color, roughness=0.78, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new("MAT_mountain_detail_massive_" + role)
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
    H.MATS[role] = mat
    return mat


def palette():
    colors = {
        "grass": (0.26, 0.48, 0.08),
        "grass_light": (0.37, 0.59, 0.13),
        "earth": (0.30, 0.20, 0.105),
        "stone_shadow": (0.25, 0.28, 0.28),
        "stone_warm": (0.42, 0.43, 0.38),
        "stone_mid": (0.50, 0.51, 0.45),
        "stone_light": (0.64, 0.65, 0.57),
        "cliff_highlight": (0.74, 0.74, 0.64),
        "moss": (0.12, 0.32, 0.07),
        "snow": (0.86, 0.90, 0.84),
        "cave_far": (0.016, 0.018, 0.018),
        "cave_mid": (0.075, 0.082, 0.078),
        "wood": (0.56, 0.31, 0.12),
        "premium_wood": (0.70, 0.45, 0.18),
        "beam": (0.19, 0.075, 0.029),
        "brick": (0.56, 0.22, 0.13),
        "concrete": (0.55, 0.55, 0.50),
        "reinforced": (0.37, 0.39, 0.38),
        "rail_iron": (0.31, 0.32, 0.30),
        "steel": (0.52, 0.54, 0.52),
        "copper": (0.73, 0.38, 0.16),
        "coal": (0.035, 0.032, 0.030),
        "rope": (0.68, 0.45, 0.20),
        "lamp_amber": (1.0, 0.56, 0.16),
        "fuel": (0.50, 0.16, 0.08),
        "explosive": (0.72, 0.18, 0.10),
        "crystal": (0.38, 0.86, 1.0),
        "heart": (0.58, 0.36, 0.82),
        "char": (0.04, 0.035, 0.032),
        "warning": (0.94, 0.68, 0.14),
    }
    for role, color in colors.items():
        add_material(role, color)
    for role, metallic, roughness in (("rail_iron", 0.35, 0.48), ("steel", 0.55, 0.42), ("copper", 0.45, 0.48)):
        bsdf = shader(H.MATS[role])
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    for role, emission, strength in (("lamp_amber", (1.0, 0.38, 0.08), 0.35), ("crystal", (0.20, 0.72, 1.0), 0.65)):
        bsdf = shader(H.MATS[role])
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength


def setup_terrain_camera(scene):
    H.setup_camera(scene)
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 3.6 * math.sqrt(2) * 512 / 480
    scene.camera.data.shift_y = 0
    bpy.context.view_layer.update()
    initial = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0))).y
    scene.camera.data.shift_y = 0.1
    delta = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0))).y - initial
    scene.camera.data.shift_y = ((1 - 320 / 512) - initial) * 0.1 / delta


def base(role="grass"):
    H.box("tile_surface", (0, 0, -0.015), (3.6, 3.6, 0.03), role, 0)


def tuft(x, y, scale=1.0):
    for i in range(3):
        H.beam(
            "grass_tuft",
            (x + (i - 1) * 0.045, y, 0.008),
            (x + (i - 1) * 0.08, y + 0.035, 0.12 * scale + (i % 2) * 0.035),
            0.025,
            "grass_light",
        )


def faceted_mesh(name, verts, faces, material_roles):
    data = bpy.data.meshes.new(H.PREFIX + "_" + name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(data.name, data)
    H.COL.objects.link(obj)
    for role in material_roles:
        data.materials.append(H.MATS[role])
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.update()
    return obj


def peak_mesh(
    name,
    x,
    y,
    rx,
    ry,
    height,
    *,
    segments=22,
    rings=8,
    twist=0.0,
    lean=(0.0, 0.0),
    snow=False,
    damage=0.0,
    pointiness=1.0,
    crag=0.0,
):
    verts = []
    for ring in range(rings):
        t = ring / (rings - 1)
        taper = 1.0 - t * 0.955
        if pointiness != 1.0:
            taper = max(0.0, 1.0 - t**(0.82 / pointiness))
        radius = max(0.012 if pointiness > 1.0 else 0.035, taper)
        cx = x + lean[0] * t
        cy = y + lean[1] * t
        for i in range(segments):
            angle = math.tau * i / segments + twist * t
            angular = 0.84 + (0.24 + crag * 0.09) * ((i * 7 + ring * 5) % 7) / 6
            ridge_boost = 1.0 + ((0.14 + crag * 0.12) if i in (0, 4, 8, 13, 17) else (-0.035 - crag * 0.025))
            broken = 1.0 - damage * (0.12 if ring > rings * 0.55 and i in (3, 4, 5) else 0.0)
            vertical_ridge = 1.0 + crag * 0.035 * math.sin(angle * 3.0 + ring * 0.85)
            verts.append(
                (
                    cx + rx * radius * math.cos(angle) * angular * ridge_boost * broken,
                    cy + ry * radius * math.sin(angle) * angular * broken,
                    0.08 + height * (t**1.10) * vertical_ridge - damage * 0.20 * max(0, t - 0.65),
                )
            )
    faces = []
    for ring in range(rings - 1):
        for i in range(segments):
            a = ring * segments + i
            b = ring * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range((rings - 1) * segments, rings * segments)))
    obj = faceted_mesh(name, verts, faces, ["stone_shadow", "stone_warm", "stone_mid", "stone_light", "cliff_highlight", "snow", "char"])
    for poly in obj.data.polygons:
        center = poly.center
        if damage and center.z > height * 0.62 and center.x > x + rx * 0.12:
            poly.material_index = 6
        elif snow and center.z > height * 0.77:
            poly.material_index = 5
        elif poly.normal.x < -0.25 or poly.normal.y > 0.35:
            poly.material_index = 3
        elif poly.normal.z > 0.66:
            poly.material_index = 4
        elif poly.normal.y < -0.35:
            poly.material_index = 0
        elif poly.normal.x > 0.3:
            poly.material_index = 2
        else:
            poly.material_index = 1
        poly.use_smooth = False
    return obj


def mine_l01_peak_mesh(name, x, y, rx, ry, height, *, segments=9, rings=5, twist=0.0, lean=(0.0, 0.0), damage=0.0):
    verts = []
    for ring in range(rings):
        t = ring / (rings - 1)
        radius = max(0.05, 1.0 - t * 0.93)
        cx = x + lean[0] * t
        cy = y + lean[1] * t
        for i in range(segments):
            angle = math.tau * i / segments + twist * t
            angular = 0.86 + 0.20 * ((i * 7 + ring * 3) % 5) / 4
            ridge_boost = 1.0 + (0.10 if i in (0, 3, 6) else -0.035)
            damaged_drop = damage * 0.16 * max(0, t - 0.62)
            verts.append(
                (
                    cx + rx * radius * math.cos(angle) * angular * ridge_boost,
                    cy + ry * radius * math.sin(angle) * angular,
                    0.08 + height * (t**1.10) - damaged_drop,
                )
            )
    faces = []
    for ring in range(rings - 1):
        for i in range(segments):
            a = ring * segments + i
            b = ring * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range((rings - 1) * segments, rings * segments)))
    obj = faceted_mesh(name, verts, faces, ["stone_shadow", "stone_warm", "stone_light", "cliff_highlight", "char"])
    for poly in obj.data.polygons:
        center = poly.center
        if damage and center.z > height * 0.62 and center.x > x + rx * 0.12:
            poly.material_index = 4
        elif poly.normal.x < -0.25 or poly.normal.y > 0.35:
            poly.material_index = 2
        elif poly.normal.z > 0.68:
            poly.material_index = 3
        elif poly.normal.y < -0.35:
            poly.material_index = 0
        else:
            poly.material_index = 1
        poly.use_smooth = False
    return obj


def add_l01_mine_rock_shell(state):
    damaged = state == "damaged"
    damage = 0.18 if damaged else 0.0
    mine_l01_peak_mesh("mine_back_mountain", -0.18, 0.10, 1.42, 1.02, 1.78, segments=10, rings=5, twist=0.45, lean=(-0.08, 0.06), damage=damage)
    mine_l01_peak_mesh("mine_left_cheek", -0.98, -0.28, 0.64, 0.54, 1.10, segments=7, rings=4, twist=-0.20, lean=(-0.03, -0.02), damage=damage)
    mine_l01_peak_mesh("mine_right_cheek", 0.82, -0.24, 0.62, 0.50, 1.02, segments=7, rings=4, twist=0.32, lean=(0.04, -0.02), damage=damage)
    mine_l01_peak_mesh("mine_front_lip", -0.08, -0.78, 1.06, 0.36, 0.58, segments=7, rings=4, twist=-0.10, damage=damage)


def talus(name, x, y, rx, ry, rz, role="stone_light", seed=0):
    verts = []
    segments = 12
    for z, scale in ((0.0, 1.0), (0.38, 0.82), (1.0, 0.26)):
        for i in range(segments):
            angle = math.tau * i / segments + seed * 0.13 * z
            wobble = 0.76 + 0.28 * ((i * 11 + seed * 5) % 7) / 6
            verts.append((x + rx * scale * math.cos(angle) * wobble, y + ry * scale * math.sin(angle) * wobble, 0.04 + rz * z))
    faces = []
    for ring in range(2):
        for i in range(segments):
            faces.append((ring * segments + i, ring * segments + (i + 1) % segments, (ring + 1) * segments + (i + 1) % segments, (ring + 1) * segments + i))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(2 * segments, 3 * segments)))
    return faceted_mesh(name, verts, faces, [role])


def scatter_talus(name, placements, role="stone_light", seed_base=0):
    for i, (x, y, rx, ry, rz, rotation_seed) in enumerate(placements):
        talus(name, x, y, rx, ry, rz, role=role, seed=seed_base + rotation_seed + i * 3)


def ridge_beam(name, a, b, width, role="cliff_highlight"):
    return H.beam(name, a, b, width, role)


def mountain_ridge_massive():
    base()
    peak_mesh("main_peak", -0.42, 0.02, 1.48, 1.24, 4.68, segments=24, rings=9, twist=0.52, lean=(-0.16, 0.13), snow=True)
    peak_mesh("side_peak_east", 0.82, 0.32, 1.08, 0.88, 3.28, segments=22, rings=8, twist=-0.30, lean=(0.16, -0.04))
    peak_mesh("front_buttress", -0.20, -0.90, 1.26, 0.62, 2.12, segments=20, rings=7, twist=0.24, lean=(0.0, -0.10))
    peak_mesh("rear_low_shoulder", -1.18, 0.62, 0.66, 0.50, 1.68, segments=18, rings=6, twist=-0.38, lean=(-0.04, 0.02))
    for start, end in (
        ((-1.50, -0.32, 0.40), (-0.54, 0.04, 4.22)),
        ((-0.24, -0.78, 0.36), (-0.48, 0.08, 4.04)),
        ((0.90, -0.16, 0.34), (-0.34, 0.14, 3.70)),
        ((1.46, 0.40, 0.32), (0.66, 0.30, 2.68)),
    ):
        ridge_beam("sharp_cliff_ridge", start, end, 0.060)
    scatter_talus(
        "angular_talus",
        (
            (-1.50, -1.10, 0.18, 0.12, 0.16, 2),
            (-1.10, -1.34, 0.14, 0.10, 0.14, 11),
            (-0.56, -1.18, 0.16, 0.11, 0.16, 5),
            (0.06, -1.42, 0.13, 0.09, 0.13, 17),
            (0.76, -1.12, 0.17, 0.11, 0.16, 23),
            (1.38, -0.52, 0.14, 0.10, 0.13, 31),
            (-1.45, 0.56, 0.12, 0.09, 0.12, 37),
            (1.22, 0.86, 0.15, 0.10, 0.14, 41),
        ),
        seed_base=0,
    )
    for x, y in ((1.42, -0.98), (-1.42, 1.00)):
        tuft(x, y, 1.2)


def mountain_spire_massive():
    base()
    peak_mesh("needle_peak", -0.20, 0.08, 1.24, 1.08, 5.44, segments=24, rings=9, twist=0.95, lean=(-0.20, 0.08), snow=True)
    peak_mesh("rear_shoulder", 0.82, 0.58, 1.00, 0.76, 3.28, segments=22, rings=8, twist=-0.55, lean=(0.12, 0.03))
    peak_mesh("front_scree_wall", -0.30, -0.94, 1.34, 0.62, 1.92, segments=20, rings=7, twist=0.15)
    peak_mesh("left_lower_spur", -1.24, 0.04, 0.62, 0.58, 1.96, segments=18, rings=6, twist=0.62, lean=(-0.05, 0.03))
    for start, end in (
        ((-0.92, -0.44, 0.42), (-0.24, 0.10, 4.92)),
        ((0.18, -0.58, 0.38), (-0.16, 0.12, 4.68)),
        ((0.94, -0.02, 0.34), (-0.08, 0.16, 4.12)),
        ((-1.36, 0.42, 0.34), (-0.20, 0.12, 3.80)),
    ):
        ridge_beam("needle_ridge", start, end, 0.055)
    scatter_talus(
        "spine_scree",
        (
            (-1.45, -1.00, 0.15, 0.10, 0.15, 4),
            (-1.15, -1.36, 0.13, 0.09, 0.13, 13),
            (-0.60, -1.18, 0.16, 0.11, 0.15, 22),
            (-0.05, -1.48, 0.12, 0.09, 0.13, 7),
            (0.52, -1.04, 0.17, 0.11, 0.15, 29),
            (1.08, -1.20, 0.13, 0.09, 0.13, 35),
            (1.43, -0.54, 0.16, 0.11, 0.16, 43),
            (-1.45, 0.38, 0.12, 0.09, 0.12, 47),
            (1.18, 0.90, 0.14, 0.10, 0.14, 53),
        ),
        seed_base=20,
    )
    for x, y in ((1.40, -0.90), (-1.38, 0.76)):
        tuft(x, y, 0.95)


def mountain_snowcap_massive():
    base()
    peak_mesh("broad_peak", -0.54, 0.12, 1.56, 1.24, 4.28, segments=24, rings=9, twist=0.35, lean=(-0.07, 0.08), snow=True)
    peak_mesh("right_ridge_peak", 0.78, 0.18, 1.12, 0.88, 3.44, segments=22, rings=8, twist=-0.18, lean=(0.12, 0.03), snow=True)
    peak_mesh("left_cliff_foot", -1.18, -0.64, 0.78, 0.62, 1.88, segments=18, rings=6, twist=0.12)
    peak_mesh("front_rock_fan", 0.04, -0.98, 0.98, 0.48, 1.64, segments=18, rings=6, twist=-0.40)
    for start, end in (
        ((-1.42, -0.54, 0.36), (-0.62, 0.14, 3.64)),
        ((-0.34, -0.74, 0.34), (-0.52, 0.16, 3.72)),
        ((0.60, -0.44, 0.32), (0.58, 0.18, 3.04)),
        ((1.42, 0.08, 0.30), (0.72, 0.20, 2.58)),
    ):
        ridge_beam("snowcap_edge", start, end, 0.064)
    H.box("snow_slab_left", (-0.72, 0.00, 3.70), (0.58, 0.30, 0.08), "snow", 0.025, rotation=(0.12, -0.42, -0.16))
    H.box("snow_slab_right", (0.55, 0.06, 2.94), (0.50, 0.26, 0.07), "snow", 0.02, rotation=(-0.04, 0.36, 0.22))
    scatter_talus(
        "snowcap_talus",
        (
            (-1.46, -0.94, 0.15, 0.10, 0.14, 3),
            (-1.04, -1.34, 0.13, 0.09, 0.13, 9),
            (-0.48, -1.10, 0.16, 0.11, 0.15, 18),
            (0.10, -1.42, 0.14, 0.10, 0.14, 26),
            (0.72, -0.96, 0.16, 0.11, 0.15, 34),
            (1.38, -0.62, 0.13, 0.09, 0.13, 45),
            (-1.36, 0.34, 0.12, 0.09, 0.12, 51),
        ),
        seed_base=40,
    )
    for x, y in ((1.42, -0.98), (-1.38, 0.90)):
        tuft(x, y, 1.1)


def add_lamps(level, y=-0.86):
    for x in (-0.74, 0.54):
        H.box("lamp", (x, y, 0.72), (0.09, 0.06, 0.13), "lamp_amber", 0.015)
    if level >= 11:
        H.box("light_crystal", (-0.03, y - 0.08, 0.94), (0.08, 0.08, 0.28), "crystal", 0.018, rotation=(0.18, 0.12, 0.2))


def add_rails(level, damaged=False):
    length = 1.08 + min(level, 10) * 0.045
    for x in (-0.20, 0.12):
        H.box("cart_track_rail", (x, -1.05, 0.125), (0.045, length, 0.04), "rail_iron", 0.006, rotation=(0, 0, -0.025))
    sleeper_count = 4 + min(level // 3, 3)
    for i in range(sleeper_count):
        y = -1.48 + i * (length / max(1, sleeper_count - 1))
        H.box("cart_track_sleeper", (-0.04, y, 0.105), (0.58, 0.065, 0.04), "char" if damaged and i == 1 else "wood", 0.006, rotation=(0, 0, -0.04 if i % 2 else 0.035))


def add_cart(level, damaged=False):
    x = 0.58 if level < 8 else 0.70
    y = -1.08
    role = "char" if damaged else "wood"
    H.box("mine_cart", (x, y, 0.25), (0.50, 0.34, 0.20), role, 0.025, rotation=(0, 0, -0.12 if damaged else -0.08))
    H.box("cart_ore_load", (x, y, 0.42), (0.38, 0.24, 0.11), "coal", 0.02, rotation=(0, 0, -0.08))
    for dx in (-0.18, 0.18):
        H.box("cart_wheel", (x + dx, y - 0.19, 0.13), (0.105, 0.06, 0.105), "rail_iron", 0.02)


def add_material_props(level, state):
    damaged = state == "damaged"
    construction = state == "construction"
    if level <= 4 or construction:
        for i, x in enumerate((-1.10, -0.82, 1.10)):
            H.box("plank_stack", (x, -1.08 + i * 0.16, 0.15), (0.52, 0.10, 0.07), "premium_wood" if level >= 7 else "wood", 0.01, rotation=(0, 0, 0.18 - i * 0.17))
    if level >= 3:
        H.box("fuel_barrel", (1.12, -0.70, 0.28), (0.26, 0.26, 0.42), "fuel", 0.04, rotation=(0.0, 0.08, 0.10))
    if level >= 5:
        H.box("tool_chest", (-1.10, -0.62, 0.20), (0.42, 0.28, 0.22), "wood", 0.025)
        for x in (-1.18, -1.02):
            H.box("iron_ingot_stack", (x, -0.42, 0.16), (0.22, 0.12, 0.08), "rail_iron", 0.01)
    if level >= 6:
        for i in range(2 + min(3, level - 6)):
            H.box("explosive_crate", (-1.18 + 0.16 * i, 0.86, 0.20), (0.22, 0.22, 0.20), "explosive", 0.02)
            H.box("warning_strap", (-1.18 + 0.16 * i, 0.86, 0.32), (0.23, 0.035, 0.035), "warning", 0.004)
    if level >= 8:
        H.beam("vent_pipe", (1.08, 0.70, 0.18), (1.22, 0.84, 1.48 + 0.04 * level), 0.07, "copper" if level < 10 else "steel")
        H.box("vent_cap", (1.26, 0.88, 1.50 + 0.04 * level), (0.34, 0.16, 0.12), "steel", 0.02)
    if level >= 10:
        H.box("operator_post", (1.08, -0.18, 0.42), (0.42, 0.34, 0.62), "reinforced", 0.025)
        H.box("super_mechanism_case", (0.82, 0.58, 0.46), (0.44, 0.34, 0.36), "steel", 0.035)
        H.beam("super_mechanism_arm", (0.66, 0.46, 0.66), (0.18, -0.64, 1.30), 0.05, "steel")
    if level >= 11:
        H.box("heart_container", (-0.86, 0.58, 0.36), (0.34, 0.30, 0.34), "heart", 0.025)
    if damaged:
        H.box("fallen_beam", (-0.72, -1.24, 0.17), (0.82, 0.12, 0.10), "char", 0.014, rotation=(0, 0, -0.38))
        H.box("broken_crate", (1.02, -1.22, 0.12), (0.34, 0.18, 0.12), "char", 0.012, rotation=(0, 0, 0.22))


def arch_materials(level):
    if level <= 2:
        return {"frame": "wood", "facing": "premium_wood", "trim": "rope", "socket": "stone_warm", "accent": "rope"}
    if level <= 4:
        return {"frame": "stone_warm", "facing": "stone_light", "trim": "wood", "socket": "stone_warm", "accent": "stone_light"}
    if level == 5:
        return {"frame": "brick", "facing": "brick", "trim": "rail_iron", "socket": "stone_mid", "accent": "rail_iron"}
    if level <= 7:
        return {"frame": "rail_iron", "facing": "stone_mid", "trim": "copper", "socket": "stone_mid", "accent": "copper"}
    if level == 8:
        return {"frame": "concrete", "facing": "concrete", "trim": "copper", "socket": "concrete", "accent": "steel"}
    if level <= 10:
        return {"frame": "reinforced", "facing": "concrete", "trim": "steel", "socket": "reinforced", "accent": "steel"}
    return {"frame": "reinforced", "facing": "reinforced", "trim": "steel", "socket": "reinforced", "accent": "crystal"}


def add_open_portal_wall(level, state):
    damaged = state == "damaged"
    construction = state == "construction"
    rock_role = "stone_shadow" if level <= 5 else "stone_mid" if level <= 8 else "reinforced"
    brow_role = "stone_warm" if level <= 4 else "stone_mid" if level <= 8 else "concrete"
    H.box("portal_left_rock_cheek", (-0.64, -0.79, 0.56), (0.30, 0.24, 0.86), rock_role, 0.032, rotation=(0.03, -0.08, 0.03))
    H.box("portal_right_rock_cheek", (0.44, -0.79, 0.56), (0.30, 0.24, 0.86), rock_role, 0.032, rotation=(-0.02, 0.08, -0.03))
    H.box("portal_upper_rock_brow", (-0.10, -0.79, 0.98), (1.24, 0.24, 0.20), brow_role, 0.032, rotation=(0.02, 0, 0.01))
    H.box("cave_far_shadow", (-0.10, -1.04, 0.52), (0.72, 0.09, 0.58), "cave_far", 0.028, rotation=(0.02, 0, 0))
    H.box("cave_mid_wall_left", (-0.51, -0.94, 0.51), (0.15, 0.14, 0.58), "cave_mid", 0.022, rotation=(0.0, -0.12, 0.05))
    H.box("cave_mid_wall_right", (0.31, -0.94, 0.51), (0.15, 0.14, 0.58), "cave_mid", 0.022, rotation=(0.0, 0.12, -0.05))
    H.box("cave_roof_shadow", (-0.10, -0.96, 0.84), (0.78, 0.12, 0.12), "cave_mid", 0.018, rotation=(0.02, 0, 0.01))
    H.box("cave_floor_depth", (-0.10, -1.04, 0.105), (0.66, 0.30, 0.055), "earth", 0.014, rotation=(0, 0, -0.02))
    if construction:
        H.box("unfinished_portal_left_fill", (-0.56, -0.90, 0.74), (0.18, 0.12, 0.30), "stone_warm", 0.018, rotation=(0, 0, -0.04))
    if damaged:
        H.box("fallen_portal_chip_left", (-0.48, -1.02, 0.22), (0.24, 0.16, 0.12), "stone_shadow", 0.016, rotation=(0, 0, 0.22))
        H.box("cracked_portal_brow_piece", (0.34, -0.92, 0.89), (0.26, 0.14, 0.12), "stone_shadow", 0.014, rotation=(0.08, 0.02, -0.18))


def add_external_arch(level, state):
    damaged = state == "damaged"
    construction = state == "construction"
    materials = arch_materials(level)
    left_x, right_x = -0.68, 0.48
    y = -0.93
    post_h = 0.90 + 0.025 * min(level, 8)
    if not construction:
        for x in (left_x, right_x):
            H.beam("outer_portal_post", (x, y, 0.13), (x + (0.04 if damaged and x > 0 else 0), y + 0.02, post_h), 0.095, materials["frame"])
            H.box("post_socket", (x, -0.78, 0.22), (0.20, 0.20, 0.22), materials["socket"], 0.014)
            H.box("side_arch_facing", (x, -1.00, 0.58), (0.18, 0.08, 0.78), materials["facing"], 0.014, rotation=(0, 0, 0.02 if x < 0 else -0.02))
            H.box("side_arch_trim", (x, -1.055, 0.62), (0.07, 0.055, 0.64), materials["trim"], 0.008)
        H.beam("outer_portal_lintel", (left_x - 0.08, y, post_h + 0.04), (right_x + 0.10, y, post_h + (0.08 if damaged else 0.06)), 0.110, materials["frame"])
        H.box("top_arch_facing", (-0.10, -1.00, post_h + 0.05), (1.24, 0.08, 0.13), materials["facing"], 0.012)
        H.box("top_arch_trim", (-0.10, -1.055, post_h + 0.16), (1.06, 0.055, 0.07), materials["trim"], 0.008)
    else:
        H.beam("partial_portal_post_left", (left_x, y, 0.13), (left_x, y, post_h * 0.80), 0.095, materials["frame"])
        H.beam("partial_portal_post_right", (right_x, y, 0.13), (right_x, y, post_h * 0.48), 0.085, materials["frame"])
        H.box("loose_lintel_ready", (-0.04, -1.24, 0.16), (1.14, 0.12, 0.10), materials["frame"], 0.014, rotation=(0, 0, -0.08))
        H.box("loose_trim_strip", (-0.10, -1.31, 0.24), (0.74, 0.05, 0.05), materials["trim"], 0.006, rotation=(0, 0, -0.08))
        H.box("post_socket_left", (left_x, -0.78, 0.22), (0.20, 0.20, 0.22), materials["socket"], 0.014)
    if level >= 4 and not construction:
        H.box("stone_portal_cap", (-0.10, -0.78, post_h + 0.04), (1.36, 0.20, 0.18), materials["facing"], 0.025)
    if level >= 6 and not construction:
        for x in (-0.42, 0.22):
            H.box("portal_bolt_plate", (x, -1.075, 0.80), (0.16, 0.045, 0.08), materials["accent"], 0.006)
    if level >= 9 and not construction:
        for x in (-0.84, 0.64):
            H.box("armor_side_plate", (x, -0.82, 0.68), (0.12, 0.15, 0.74), materials["socket"], 0.018)
    if level >= 12 and not construction:
        H.box("shielded_top_plate", (-0.10, -0.86, 1.20), (1.50, 0.18, 0.14), "steel", 0.018)
        H.box("crystal_safety_marker", (-0.10, -1.07, 1.33), (0.18, 0.045, 0.12), "crystal", 0.008)


def mine_model(level, state):
    base()
    construction = state == "construction"
    damaged = state == "damaged"
    add_l01_mine_rock_shell(state)
    add_open_portal_wall(level, state)
    add_external_arch(level, state)
    add_lamps(level)
    add_rails(level, damaged=damaged)
    if not construction:
        add_cart(level, damaged=damaged)
    if level >= 6 and not construction:
        H.beam("hoist_left_leg", (-0.82, -0.38, 0.16), (-0.44, -0.58, 1.42), 0.055, "rail_iron")
        H.beam("hoist_right_leg", (0.62, -0.38, 0.16), (0.22, -0.58, 1.42), 0.055, "rail_iron")
        H.beam("hoist_cross_beam", (-0.48, -0.58, 1.42), (0.28, -0.58, 1.42), 0.060, "steel" if level >= 8 else "rail_iron")
        H.box("hoist_winch", (-0.10, -0.62, 1.22), (0.34, 0.18, 0.18), "copper" if level >= 7 else "rail_iron", 0.025)
        H.beam("hoist_cable", (-0.10, -0.68, 1.12), (-0.10, -0.88, 0.48), 0.022, "rope" if level < 8 else "steel")
    add_material_props(level, state)
    scatter_talus(
        "mine_fallen_chip",
        (
            (-1.42, -1.02, 0.13, 0.09, 0.12, 2),
            (-1.02, -1.34, 0.12, 0.09, 0.12, 8),
            (1.08, -0.96, 0.15, 0.10, 0.13, 16),
            (1.44, -0.36, 0.13, 0.09, 0.12, 27),
            (-1.42, 0.66, 0.13, 0.10, 0.13, 35),
            (1.22, 0.56, 0.11, 0.08, 0.11, 44),
        ),
        seed_base=70 + level,
    )
    for x, y in ((1.38, -0.98), (-1.42, 1.00)):
        tuft(x, y, 1.1)


def clear_generated_scene_data():
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Mountain_Detail_Massive") or scene.name.startswith("Mountain_Detail_Massive_Roundtrip"):
            bpy.data.scenes.remove(scene)
    for collection in list(bpy.data.collections):
        if collection.name in ASSETS:
            bpy.data.collections.remove(collection)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("SM_mountain_detail_massive_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_mountain_detail_massive_"):
            bpy.data.materials.remove(material)


def build_collection(name, builder):
    collection = bpy.data.collections.new(name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[name] = collection
    H.COL = collection
    H.PREFIX = "SM_mountain_detail_massive_" + name
    builder()
    H.clean_meshes(collection)
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.calc_loop_triangles()
    return collection


def hide_all():
    for collection in COLLECTIONS.values():
        collection.hide_render = True
        collection.hide_viewport = True


def show(name):
    hide_all()
    collection = COLLECTIONS[name]
    collection.hide_render = False
    collection.hide_viewport = False
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.all_objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.update()


def triangles(collection):
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
    except Exception:
        return None
    with Image.open(path) as image:
        return image.getchannel("A").getbbox()


def export_asset(name):
    show(name)
    tri_count = triangles(COLLECTIONS[name])
    assert 1200 <= tri_count <= 12000, (name, tri_count)
    for obj in COLLECTIONS[name].all_objects:
        if obj.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        loose = [vert for vert in bm.verts if not vert.link_edges]
        bm.free()
        assert not loose, (name, obj.name, len(loose))
    bpy.ops.export_scene.gltf(filepath=str(OUT_DIR / f"{name}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)
    SCENE.render.filepath = str(OUT_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    kind = "mountain" if name in MOUNTAIN_ASSETS else "mine"
    entry = {
        "kind": kind,
        "triangles": tri_count,
        "objects": len([obj for obj in COLLECTIONS[name].all_objects if obj.type == "MESH"]),
        "bounds": bounds(COLLECTIONS[name]),
        "png": f"{name}.png",
        "glb": f"{name}.glb",
        "alpha_bounds": alpha_bounds(OUT_DIR / f"{name}.png"),
    }
    if kind == "mine":
        parts = name.split("_")
        entry["level"] = int(parts[1][1:])
        entry["state"] = parts[2]
    REPORT[name] = entry
    print("MOUNTAIN_DETAIL_MASSIVE_DONE", name, tri_count, flush=True)


def write_manifest():
    manifest = {
        "family": "mountain_detail_massive_staging",
        "displayName": "Массивные детальные горы и шахты L1-L12, staging",
        "style": "Aeolian bright fantasy stylized mid-poly",
        "size": [512, 512],
        "footprint": 3.6,
        "footprint_pixels": 480,
        "anchor": [256, 320],
        "source": BLEND_PATH.name,
        "generator": "tools/assets/blender/generate_mountain_detail_massive_models.py",
        "runtimeIntegration": "not connected; separate staging assets only",
        "backupOfPreviousBatch": "backup_2026-10-13_thicker_v1",
        "retainedSeparateActiveL1": "mine_l01_active_mountain_detail remains in manifest.json",
        "assets": REPORT,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    REPORT_PATH.write_text(json.dumps(REPORT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def contact_sheet():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    columns = 6
    rows = math.ceil(len(ASSETS) / columns)
    sheet = Image.new("RGBA", (columns * 220, rows * 252), (37, 55, 47, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 11) if font_path.is_file() else ImageFont.load_default()
    for index, name in enumerate(ASSETS):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            thumb = image.resize((220, 220), Image.Resampling.LANCZOS)
        x = (index % columns) * 220
        y = (index // columns) * 252
        sheet.alpha_composite(thumb, (x, y))
        draw.text((x + 5, y + 224), name, fill=(255, 255, 255, 255), font=font)
    sheet.save(CONTACT_SHEET_PATH)


def validate_roundtrip():
    previous = bpy.context.window.scene
    qa = bpy.data.scenes.new("Mountain_Detail_Massive_Roundtrip_QA")
    bpy.context.window.scene = qa
    results = []
    try:
        for name in ASSETS:
            bpy.ops.import_scene.gltf(filepath=str(OUT_DIR / f"{name}.glb"))
            tri_count = 0
            loose_vertices = 0
            for obj in list(qa.objects):
                if obj.type != "MESH":
                    continue
                obj.data.calc_loop_triangles()
                tri_count += len(obj.data.loop_triangles)
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                loose_vertices += len([vert for vert in bm.verts if not vert.link_edges])
                bm.free()
            assert tri_count == REPORT[name]["triangles"], (name, tri_count, REPORT[name]["triangles"])
            assert loose_vertices == 0, (name, loose_vertices)
            results.append({"asset": name, "triangles": tri_count, "loose_vertices": loose_vertices})
            bpy.data.batch_remove(ids=list(qa.objects))
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa)
    ROUNDTRIP_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_notes():
    note = bpy.data.texts.new("mountain_detail_massive_staging_notes")
    note.write(
        "Separate staging set for massive Real City mountain redesign. "
        "Old four models are backed up and not overwritten. "
        "The new mountain variants use much thicker cliff masses, approximately 90-95 percent tile coverage and about double previous height. "
        "Mine level 1 construction/damaged states and levels 2-12 follow the level-1 sample: one external portal arch attached to the rock wall, visible cave depth, rails, cart/hoist props, and material progression. "
        "The active level-1 staging model is kept in the original manifest.json set and is not duplicated here. "
        "States are active, construction and damaged according to docs/buildings/industry/mine.md."
    )


def prepare():
    global SCENE
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_generated_scene_data()
    SCENE = bpy.data.scenes.new("Real_City_Mountain_Detail_Massive_Staging")
    bpy.context.window.scene = SCENE
    palette()
    setup_terrain_camera(SCENE)
    write_notes()
    builders = {
        "mountain_detail_ridge_massive": mountain_ridge_massive,
        "mountain_detail_spire_massive": mountain_spire_massive,
        "mountain_detail_snowcap_massive": mountain_snowcap_massive,
    }
    for name in MOUNTAIN_ASSETS:
        build_collection(name, builders[name])
    for level in range(1, 13):
        for state in MINE_STATES:
            if level == 1 and state == "active":
                continue
            build_collection(f"mine_l{level:02d}_{state}_mountain_detail", lambda level=level, state=state: mine_model(level, state))
    print("Prepared mountain detail massive staging collections", flush=True)


def finish():
    hide_all()
    for collection in COLLECTIONS.values():
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    write_manifest()
    contact_sheet()
    validate_roundtrip()
    show("mountain_detail_ridge_massive")
    print("MOUNTAIN_DETAIL_MASSIVE_COMPLETE", len(ASSETS), flush=True)


def main():
    prepare()
    for name in ASSETS:
        export_asset(name)
    finish()


if __name__ == "__main__":
    main()
