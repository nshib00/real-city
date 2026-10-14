"""Generate separate experimental detailed mountain models for Real City.

This staging generator intentionally does not replace or register the current
terrain/building assets. Outputs are written to:
frontend/public/assets/terrain/tiles/mountain_detail_staging/
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "terrain" / "tiles" / "mountain_detail_staging"
BLEND_PATH = OUT_DIR / "mountain_detail_staging.blend"
MANIFEST_PATH = OUT_DIR / "manifest.json"
REPORT_PATH = OUT_DIR / "generation-report.json"
ROUNDTRIP_PATH = OUT_DIR / "roundtrip-validation.json"
CONTACT_SHEET_PATH = OUT_DIR / "mountain_detail_contact_sheet.png"

spec = importlib.util.spec_from_file_location("terrain_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

ASSETS = (
    "mountain_detail_ridge",
    "mountain_detail_spire",
    "mountain_detail_snowcap",
    "mine_l01_active_mountain_detail",
)
COLLECTIONS = {}
REPORT = {}
SCENE = None


def shader(material):
    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def add_material(role, color, roughness=0.78, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new("MAT_mountain_detail_" + role)
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
        "stone_shadow": (0.31, 0.34, 0.32),
        "stone_warm": (0.44, 0.45, 0.39),
        "stone_light": (0.62, 0.64, 0.56),
        "cliff_highlight": (0.72, 0.73, 0.64),
        "moss": (0.13, 0.34, 0.07),
        "snow": (0.86, 0.90, 0.84),
        "cave_far": (0.018, 0.021, 0.020),
        "cave_mid": (0.09, 0.095, 0.085),
        "wood": (0.49, 0.25, 0.09),
        "beam": (0.20, 0.08, 0.035),
        "rail_iron": (0.31, 0.32, 0.30),
        "coal": (0.035, 0.032, 0.030),
        "rope": (0.68, 0.45, 0.20),
        "lamp_amber": (1.00, 0.56, 0.16),
    }
    for role, color in colors.items():
        add_material(role, color)
    bsdf = shader(H.MATS["rail_iron"])
    if bsdf:
        bsdf.inputs["Metallic"].default_value = 0.35
        bsdf.inputs["Roughness"].default_value = 0.48
    bsdf = shader(H.MATS["lamp_amber"])
    if bsdf and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.38, 0.08, 1)
        bsdf.inputs["Emission Strength"].default_value = 0.25


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


def peak_mesh(name, x, y, rx, ry, height, *, segments=9, rings=5, twist=0.0, lean=(0.0, 0.0), snow=False):
    segments = max(segments, 18)
    rings = max(rings, 7)
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
            verts.append(
                (
                    cx + rx * radius * math.cos(angle) * angular * ridge_boost,
                    cy + ry * radius * math.sin(angle) * angular,
                    0.08 + height * (t ** 1.10),
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
    obj = faceted_mesh(name, verts, faces, ["stone_shadow", "stone_warm", "stone_light", "cliff_highlight", "snow"])
    for poly in obj.data.polygons:
        center = poly.center
        if snow and center.z > height * 0.78:
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


def talus(name, x, y, rx, ry, rz, role="stone_light", seed=0):
    verts = []
    segments = 12
    for z, scale in ((0.0, 1.0), (0.42, 0.86), (1.0, 0.28)):
        for i in range(segments):
            angle = math.tau * i / segments + seed * 0.17 * z
            wobble = 0.78 + 0.26 * ((i * 11 + seed * 5) % 6) / 5
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


def mountain_ridge():
    base()
    peak_mesh("main_peak", -0.48, 0.08, 1.03, 0.92, 2.34, segments=10, rings=6, twist=0.55, lean=(-0.12, 0.10), snow=True)
    peak_mesh("side_peak_east", 0.58, 0.28, 0.78, 0.68, 1.64, segments=8, rings=5, twist=-0.30, lean=(0.12, -0.04))
    peak_mesh("front_buttress", -0.24, -0.76, 0.88, 0.52, 1.06, segments=7, rings=4, twist=0.24, lean=(0.0, -0.10))
    peak_mesh("rear_low_shoulder", -1.02, 0.56, 0.46, 0.36, 0.84, segments=7, rings=4, twist=-0.38, lean=(-0.04, 0.02))
    for start, end in (
        ((-1.12, -0.22, 0.38), (-0.52, 0.05, 2.10)),
        ((-0.16, -0.58, 0.34), (-0.52, 0.10, 2.00)),
        ((0.66, -0.10, 0.32), (-0.42, 0.12, 1.86)),
        ((1.12, 0.36, 0.30), (0.52, 0.30, 1.34)),
    ):
        ridge_beam("sharp_cliff_ridge", start, end, 0.052)
    scatter_talus(
        "angular_talus",
        (
            (-1.32, -0.94, 0.20, 0.14, 0.18, 2),
            (-0.88, -1.21, 0.15, 0.11, 0.16, 11),
            (-0.44, -0.88, 0.18, 0.13, 0.17, 5),
            (0.14, -1.17, 0.14, 0.10, 0.15, 17),
            (0.63, -0.81, 0.18, 0.12, 0.18, 23),
            (1.18, -0.44, 0.14, 0.10, 0.14, 31),
            (-1.20, 0.38, 0.13, 0.09, 0.13, 37),
            (0.98, 0.72, 0.16, 0.11, 0.16, 41),
        ),
        seed_base=0,
    )
    for x, y in ((1.22, -0.92), (-1.28, 0.92)):
        tuft(x, y, 1.2)


def mountain_spire():
    base()
    peak_mesh("needle_peak", -0.20, 0.10, 0.88, 0.76, 2.72, segments=9, rings=7, twist=0.95, lean=(-0.16, 0.06), snow=True)
    peak_mesh("rear_shoulder", 0.64, 0.52, 0.76, 0.58, 1.64, segments=8, rings=5, twist=-0.55, lean=(0.10, 0.02))
    peak_mesh("front_scree_wall", -0.34, -0.78, 1.00, 0.50, 0.96, segments=8, rings=4, twist=0.15)
    peak_mesh("left_lower_spur", -1.12, 0.04, 0.42, 0.42, 0.98, segments=7, rings=4, twist=0.62, lean=(-0.05, 0.03))
    for start, end in (
        ((-0.78, -0.34, 0.38), (-0.26, 0.10, 2.46)),
        ((0.14, -0.46, 0.36), (-0.18, 0.12, 2.34)),
        ((0.76, 0.02, 0.32), (-0.08, 0.16, 2.08)),
        ((-1.12, 0.38, 0.34), (-0.20, 0.12, 1.90)),
    ):
        ridge_beam("needle_ridge", start, end, 0.048)
    scatter_talus(
        "spine_scree",
        (
            (-1.32, -0.82, 0.15, 0.10, 0.16, 4),
            (-1.05, -1.20, 0.13, 0.10, 0.15, 13),
            (-0.56, -0.96, 0.16, 0.11, 0.17, 22),
            (-0.08, -1.28, 0.12, 0.09, 0.14, 7),
            (0.38, -0.82, 0.17, 0.12, 0.17, 29),
            (0.88, -1.02, 0.13, 0.09, 0.14, 35),
            (1.22, -0.48, 0.18, 0.12, 0.18, 43),
            (-1.30, 0.32, 0.12, 0.09, 0.13, 47),
            (0.90, 0.82, 0.14, 0.10, 0.14, 53),
        ),
        seed_base=20,
    )
    for x, y in ((1.20, -0.82), (-1.22, 0.72)):
        tuft(x, y, 0.95)


def mountain_snowcap():
    base()
    peak_mesh("broad_peak", -0.54, 0.16, 1.12, 0.96, 2.14, segments=11, rings=6, twist=0.35, lean=(-0.06, 0.08), snow=True)
    peak_mesh("right_ridge_peak", 0.62, 0.18, 0.82, 0.68, 1.72, segments=9, rings=5, twist=-0.18, lean=(0.10, 0.02), snow=True)
    peak_mesh("left_cliff_foot", -1.02, -0.58, 0.66, 0.52, 0.94, segments=7, rings=4, twist=0.12)
    peak_mesh("front_rock_fan", 0.02, -0.86, 0.72, 0.38, 0.82, segments=7, rings=4, twist=-0.40)
    for start, end in (
        ((-1.22, -0.48, 0.34), (-0.60, 0.16, 1.82)),
        ((-0.28, -0.62, 0.32), (-0.52, 0.18, 1.86)),
        ((0.48, -0.38, 0.30), (0.54, 0.18, 1.52)),
        ((1.18, 0.08, 0.28), (0.62, 0.20, 1.30)),
    ):
        ridge_beam("snowcap_edge", start, end, 0.058)
    H.box("snow_slab_left", (-0.66, 0.00, 1.84), (0.46, 0.24, 0.07), "snow", 0.025, rotation=(0.12, -0.42, -0.16))
    H.box("snow_slab_right", (0.45, 0.06, 1.47), (0.40, 0.22, 0.06), "snow", 0.02, rotation=(-0.04, 0.36, 0.22))
    scatter_talus(
        "snowcap_talus",
        (
            (-1.30, -0.80, 0.16, 0.11, 0.15, 3),
            (-0.96, -1.18, 0.13, 0.10, 0.14, 9),
            (-0.46, -0.94, 0.17, 0.11, 0.16, 18),
            (0.04, -1.24, 0.14, 0.10, 0.14, 26),
            (0.58, -0.78, 0.16, 0.11, 0.15, 34),
            (1.18, -0.56, 0.13, 0.09, 0.13, 45),
            (-1.20, 0.28, 0.12, 0.09, 0.13, 51),
        ),
        seed_base=40,
    )
    for x, y in ((1.28, -0.90), (-1.25, 0.82)):
        tuft(x, y, 1.1)


def mine_l01_active():
    base()
    peak_mesh("mine_back_mountain", -0.18, 0.10, 1.42, 1.02, 1.78, segments=10, rings=5, twist=0.45, lean=(-0.08, 0.06))
    peak_mesh("mine_left_cheek", -0.98, -0.28, 0.64, 0.54, 1.10, segments=7, rings=4, twist=-0.20, lean=(-0.03, -0.02))
    peak_mesh("mine_right_cheek", 0.82, -0.24, 0.62, 0.50, 1.02, segments=7, rings=4, twist=0.32, lean=(0.04, -0.02))
    peak_mesh("mine_front_lip", -0.08, -0.78, 1.06, 0.36, 0.58, segments=7, rings=4, twist=-0.10)
    H.box("portal_stone_backing", (-0.10, -0.74, 0.52), (1.22, 0.26, 0.86), "stone_shadow", 0.035, rotation=(0.02, 0, 0.01))
    H.box("cave_far_shadow", (-0.10, -0.88, 0.50), (0.72, 0.14, 0.62), "cave_far", 0.04, rotation=(0.02, 0, 0))
    H.box("cave_mid_wall_left", (-0.46, -0.82, 0.50), (0.18, 0.20, 0.58), "cave_mid", 0.025, rotation=(0.0, -0.10, 0.06))
    H.box("cave_mid_wall_right", (0.22, -0.82, 0.49), (0.18, 0.20, 0.56), "cave_mid", 0.025, rotation=(0.0, 0.10, -0.06))
    H.box("cave_floor_depth", (-0.10, -0.96, 0.17), (0.78, 0.30, 0.08), "earth", 0.02, rotation=(0, 0, -0.02))
    for x in (-0.58, 0.38):
        H.beam("outer_timber_post", (x, -0.94, 0.13), (x, -0.92, 0.90), 0.09, "beam")
        H.box("post_socket_stone", (x, -0.78, 0.30), (0.18, 0.20, 0.36), "stone_warm", 0.018)
    H.beam("outer_timber_lintel", (-0.66, -0.93, 0.92), (0.46, -0.93, 0.94), 0.105, "wood")
    H.box("lintel_stone_seam", (-0.10, -0.78, 0.94), (1.30, 0.18, 0.18), "stone_warm", 0.025)
    H.beam("left_safety_rope", (-0.60, -0.84, 0.40), (-0.10, -0.86, 0.52), 0.025, "rope")
    H.beam("right_safety_rope", (-0.10, -0.86, 0.52), (0.40, -0.84, 0.40), 0.025, "rope")
    for x in (-0.20, 0.10):
        H.box("cart_track_rail", (x, -1.00, 0.125), (0.045, 0.98, 0.04), "rail_iron", 0.006, rotation=(0, 0, -0.025))
    for i in range(4):
        H.box("cart_track_sleeper", (-0.05, -1.34 + i * 0.22, 0.105), (0.52, 0.065, 0.04), "wood", 0.006, rotation=(0, 0, -0.03 if i % 2 else 0.04))
    H.box("small_mine_cart", (0.52, -1.06, 0.25), (0.48, 0.34, 0.20), "wood", 0.025, rotation=(0, 0, -0.08))
    H.box("cart_coal_load", (0.52, -1.06, 0.41), (0.36, 0.24, 0.10), "coal", 0.02, rotation=(0, 0, -0.08))
    for dx in (-0.18, 0.18):
        H.box("cart_wheel", (0.52 + dx, -1.24, 0.13), (0.10, 0.06, 0.10), "rail_iron", 0.02)
    H.box("lamp_left", (-0.68, -0.82, 0.62), (0.08, 0.055, 0.12), "lamp_amber", 0.015)
    H.box("lamp_right", (0.48, -0.82, 0.60), (0.08, 0.055, 0.12), "lamp_amber", 0.015)
    scatter_talus(
        "mine_fallen_chip",
        (
            (-1.28, -0.96, 0.14, 0.10, 0.13, 2),
            (-0.88, -1.24, 0.12, 0.09, 0.12, 8),
            (0.92, -0.86, 0.15, 0.10, 0.13, 16),
            (1.25, -0.34, 0.13, 0.09, 0.12, 27),
            (-1.20, 0.58, 0.13, 0.10, 0.13, 35),
            (1.06, 0.48, 0.11, 0.08, 0.11, 44),
        ),
        seed_base=70,
    )
    for x, y in ((1.26, -0.88), (-1.30, 0.92)):
        tuft(x, y, 1.15)


def clear_previous():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("SM_mountain_detail_") or obj.name.startswith("mountain_detail_") or obj.name.startswith("mine_l01_active_mountain_detail"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name in ASSETS:
            bpy.data.collections.remove(collection)
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Mountain_Detail") or scene.name.startswith("Mountain_Detail_Roundtrip"):
            bpy.data.scenes.remove(scene)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_mountain_detail_"):
            bpy.data.materials.remove(material)


def build_collection(name, builder):
    collection = bpy.data.collections.new(name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[name] = collection
    H.COL = collection
    H.PREFIX = "SM_mountain_detail_" + name
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
    assert 900 <= tri_count <= 8000, (name, tri_count)
    for obj in COLLECTIONS[name].all_objects:
        if obj.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold = [edge for edge in bm.edges if not edge.is_manifold]
        loose = [vert for vert in bm.verts if not vert.link_edges]
        bm.free()
        assert not non_manifold and not loose, (name, obj.name, len(non_manifold), len(loose))
    bpy.ops.export_scene.gltf(filepath=str(OUT_DIR / f"{name}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)
    SCENE.render.filepath = str(OUT_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    REPORT[name] = {
        "triangles": tri_count,
        "objects": len([obj for obj in COLLECTIONS[name].all_objects if obj.type == "MESH"]),
        "bounds": bounds(COLLECTIONS[name]),
        "png": f"{name}.png",
        "glb": f"{name}.glb",
        "alpha_bounds": alpha_bounds(OUT_DIR / f"{name}.png"),
    }
    print("MOUNTAIN_DETAIL_DONE", name, tri_count, flush=True)


def write_manifest():
    manifest = {
        "family": "mountain_detail_staging",
        "displayName": "Детальные горы и шахта, staging",
        "style": "Aeolian bright fantasy stylized mid-poly",
        "size": [512, 512],
        "footprint": 3.6,
        "footprint_pixels": 480,
        "anchor": [256, 320],
        "source": BLEND_PATH.name,
        "generator": "tools/assets/blender/generate_mountain_detail_models.py",
        "runtimeIntegration": "not connected; separate staging assets only",
        "assets": REPORT,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(REPORT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def contact_sheet():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    sheet = Image.new("RGBA", (2 * 256, 2 * 292), (37, 55, 47, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 13) if font_path.is_file() else ImageFont.load_default()
    for index, name in enumerate(ASSETS):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            thumb = image.resize((256, 256), Image.Resampling.LANCZOS)
        x = (index % 2) * 256
        y = (index // 2) * 292
        sheet.alpha_composite(thumb, (x, y))
        draw.text((x + 8, y + 260), name, fill=(255, 255, 255, 255), font=font)
    sheet.save(CONTACT_SHEET_PATH)


def validate_roundtrip():
    previous = bpy.context.window.scene
    qa = bpy.data.scenes.new("Mountain_Detail_Roundtrip_QA")
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
    ROUNDTRIP_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_notes():
    note = bpy.data.texts.new("mountain_detail_staging_notes")
    note.write(
        "Separate staging set for Real City mountain redesign. "
        "The three terrain variants replace rounded boulder piles with one dominant peak, side ridges, angular cliff faces, talus fans, warm grey stone, moss, and restrained snow. "
        "The mine_l01_active_mountain_detail model is a level-1 active mine concept using the same faceted rock kit: one external timber arch, visible cave depth, rails, cart, lamps, and no second inner arch. "
        "These assets are not registered in frontend runtime and do not replace existing terrain or mine files."
    )


def prepare():
    global SCENE
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_previous()
    SCENE = bpy.data.scenes.new("Real_City_Mountain_Detail_Staging")
    bpy.context.window.scene = SCENE
    palette()
    setup_terrain_camera(SCENE)
    write_notes()
    builders = {
        "mountain_detail_ridge": mountain_ridge,
        "mountain_detail_spire": mountain_spire,
        "mountain_detail_snowcap": mountain_snowcap,
        "mine_l01_active_mountain_detail": mine_l01_active,
    }
    for name in ASSETS:
        build_collection(name, builders[name])
    print("Prepared mountain detail staging collections", flush=True)


def finish():
    hide_all()
    for collection in COLLECTIONS.values():
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    write_manifest()
    contact_sheet()
    validate_roundtrip()
    show("mountain_detail_ridge")
    print("MOUNTAIN_DETAIL_COMPLETE", len(ASSETS), flush=True)


def main():
    prepare()
    for name in ASSETS:
        export_asset(name)
    finish()


if __name__ == "__main__":
    main()
