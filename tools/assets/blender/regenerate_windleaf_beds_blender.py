"""Build Blender master/runtime assets for windleaf beds levels 1-3."""
from __future__ import annotations

import json
import math
import os
import importlib.util
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path("/home/nshib/projects/real-city")
OUT_DIR = ROOT / "frontend/public/assets/buildings/fields/windleaf_bed"
BLEND_PATH = OUT_DIR / "windleaf_bed_l01_l03.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
GRASS_TEXTURE_PATH = ROOT / "frontend/public/assets/terrain/tiles/grass.png"
ANCHOR = [256, 292]
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
BED_MODEL_SCALE = 1.28
SUPER_WINDLEAF_GROWTH = {
    1: {"leaves": 4, "length": 1.12, "width": 0.32, "z": 0.54, "stem": 0.94},
    2: {"leaves": 5, "length": 1.38, "width": 0.38, "z": 0.62, "stem": 1.14},
    3: {"leaves": 6, "length": 1.72, "width": 0.46, "z": 0.72, "stem": 1.38},
    4: {"leaves": 7, "length": 2.08, "width": 0.54, "z": 0.82, "stem": 1.62},
    5: {"leaves": 8, "length": 2.44, "width": 0.62, "z": 0.92, "stem": 1.88},
    6: {"leaves": 9, "length": 2.84, "width": 0.70, "z": 1.02, "stem": 2.16},
}


def blender_path(path: Path) -> str:
    """Return a path Blender can write when it runs on Windows against WSL."""
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        relative = raw[len(root) :].lstrip("\\")
        return BLENDER_ROOT + "\\" + relative
    return raw


def blender_exists(path: Path) -> bool:
    return os.path.exists(blender_path(path))


MATERIALS = {
    "grass": (0.26, 0.48, 0.08, 1),
    "grass_light": (0.37, 0.59, 0.13, 1),
    "earth": (0.46, 0.27, 0.15, 1),
    "earth_dark": (0.30, 0.18, 0.10, 1),
    "soil": (0.38, 0.22, 0.12, 1),
    "soil_light": (0.56, 0.36, 0.20, 1),
    "wood": (0.70, 0.45, 0.23, 1),
    "wood_dark": (0.43, 0.26, 0.13, 1),
    "wood_cut": (0.86, 0.63, 0.34, 1),
    "plank": (0.78, 0.55, 0.30, 1),
    "flax": (0.84, 0.78, 0.54, 1),
    "rope": (0.73, 0.58, 0.32, 1),
    "stone": (0.54, 0.56, 0.50, 1),
    "iron": (0.28, 0.32, 0.34, 1),
    "cloth": (0.16, 0.55, 0.58, 1),
    "leaf": (0.15, 0.62, 0.22, 1),
    "leaf_light": (0.49, 0.92, 0.38, 1),
    "leaf_dark": (0.07, 0.36, 0.14, 1),
    "leaf_vein": (0.73, 1.00, 0.52, 1),
    "super_leaf": (0.20, 0.82, 0.32, 1),
    "super_glow": (0.52, 1.00, 0.48, 0.48),
}


def ensure_dir() -> None:
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)


def mat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new("MAT_windleaf_bed_" + name)
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
        if name in {"grass", "grass_light"}:
            material["terrain_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    material.use_screen_refraction = False
    material.blend_method = "BLEND" if color[3] < 1 else "OPAQUE"
    return material


def reset_scene() -> dict[str, bpy.types.Material]:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("windleaf_bed"):
            bpy.data.collections.remove(coll)
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_windleaf_bed_"):
            bpy.data.materials.remove(material)
    return {name: mat(name, color) for name, color in MATERIALS.items()}


def make_materials(prefix: str = "") -> dict[str, bpy.types.Material]:
    return {name: mat(prefix + name, color) for name, color in MATERIALS.items()}


def link_obj(coll: bpy.types.Collection, obj: bpy.types.Object) -> bpy.types.Object:
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


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
    obj.name = name
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_midpoly_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    if ground:
        obj["ground"] = True
    return obj


def add_cylinder(coll, name, loc, radius, depth, material, vertices=10, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=vertices,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    mesh = bpy.data.meshes.new(name + "_mesh")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.name = name
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_cap_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
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


def add_leaf(coll, name, center, length, width, material, vein_material, yaw=0, pitch=0.55, roll=0, vein=True):
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
        tip = transform @ Vector((0, 0.01, length * 0.45))
        root = transform @ Vector((0, 0.01, -length * 0.40))
        beam_between(coll, name + "_vein", root, tip, max(0.01, width * 0.045), vein_material, 6)
    return obj


def add_stone(coll, name, x, y, z, sx, sy, sz, mats, rot=0):
    return add_cube(coll, name, (x, y, z), (sx, sy, sz), mats["stone"], (0, 0, rot), 0.025)


def add_grass_tuft(coll, x, y, mats, scale=1.0):
    for i in range(3):
        beam_between(
            coll,
            "terrain_grass_tuft",
            (x + (i - 1) * 0.045, y, 0.008),
            (x + (i - 1) * 0.085, y + 0.035, 0.13 * scale + (i % 2) * 0.04),
            0.028,
            mats["grass_light"],
            6,
        )


def add_log_wall(coll, name, level, mats):
    rows = 2 if level == 1 else 3
    radius = 0.065
    y_front, y_back = -0.70, 0.70
    x_left, x_right = -0.98, 0.98
    for row in range(rows):
        z = radius + row * radius * 1.75
        material = mats["wood"] if row % 2 else mats["wood_dark"]
        beam_between(coll, name + "_front_log", (x_left, y_front, z), (x_right, y_front, z), radius, material, 10)
        beam_between(coll, name + "_back_log", (x_left, y_back, z), (x_right, y_back, z), radius, material, 10)
        beam_between(coll, name + "_left_log", (x_left, y_front, z), (x_left, y_back, z), radius, material, 10)
        beam_between(coll, name + "_right_log", (x_right, y_front, z), (x_right, y_back, z), radius, material, 10)
    for x in (x_left, x_right):
        for y in (y_front, y_back):
            post_h = 0.44 + level * 0.04
            add_cube(coll, "grounded_corner_post", (x, y, post_h / 2), (0.22, 0.22, post_h), mats["wood_dark"], bevel=0.04, ground=True)
            add_cube(coll, "supported_post_cap", (x, y, post_h + 0.04), (0.27, 0.27, 0.08), mats["wood_cut"], (0, 0, 0.2), 0.03, True)


def add_ground(coll, level, mats):
    add_cube(coll, "windleaf_bed_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for x, y in ((-1.25, 0.85), (1.18, 1.12), (1.24, -0.92), (-1.16, -1.12)):
        add_grass_tuft(coll, x, y, mats, 0.78)
    add_cube(coll, "warm_earth_bed", (0, 0, 0.075), (1.72, 1.52, 0.16), mats["earth"], bevel=0.06, ground=True)
    for y in (-0.38, 0.0, 0.38):
        add_cube(coll, "raised_soil_row", (0, y, 0.185), (1.34, 0.23, 0.12), mats["soil"], bevel=0.04, ground=True)
        add_cube(coll, "soil_highlight", (-0.08, y - 0.035, 0.257), (0.98, 0.045, 0.018), mats["soil_light"], bevel=0.012, ground=True)
    if level <= 2:
        add_log_wall(coll, "bed_log_wall", level, mats)
    else:
        for y in (-0.69, 0.69):
            add_cube(coll, "grounded_plank_rail", (0, y, 0.11), (2.20, 0.16, 0.22), mats["plank"], bevel=0.035, ground=True)
        for x in (-0.98, 0.98):
            add_cube(coll, "grounded_plank_side_rail", (x, 0, 0.11), (0.16, 1.66, 0.22), mats["plank"], bevel=0.035, ground=True)
        for x in (-0.99, 0.99):
            for y in (-0.71, 0.71):
                post_h = 0.54
                add_cube(coll, "grounded_corner_post", (x, y, post_h / 2), (0.22, 0.22, post_h), mats["wood_dark"], bevel=0.04, ground=True)
                add_cube(coll, "supported_post_cap", (x, y, post_h + 0.04), (0.27, 0.27, 0.08), mats["wood_cut"], (0, 0, 0.2), 0.03, True)
    if level >= 2:
        for y in (-0.52, 0.52):
            beam_between(coll, "flax_tie_front", (-0.88, y, 0.49), (0.88, y, 0.49), 0.025, mats["flax"], 8)
        add_cube(coll, "grounded_field_sign_post", (-1.08, -0.20, 0.30), (0.08, 0.08, 0.60), mats["wood_dark"], bevel=0.014)
        add_cube(coll, "supported_field_sign_board", (-1.10, -0.24, 0.62), (0.42, 0.07, 0.24), mats["wood_cut"], (0, 0, -0.08), 0.018)
    if level >= 3:
        for y in (-0.80, 0.80):
            add_cube(coll, "supported_plank_cap_long", (0, y, 0.43), (2.08, 0.11, 0.11), mats["plank"], bevel=0.025, ground=True)
        for x in (-1.09, 1.09):
            add_cube(coll, "supported_plank_cap_side", (x, 0, 0.43), (0.11, 1.64, 0.11), mats["plank"], bevel=0.025, ground=True)
        for x in (-0.62, 0.62):
            beam_between(coll, "grounded_leaf_support_post", (x, -0.60, 0.00), (x, -0.60, 0.92), 0.045, mats["wood_dark"], 8)
            beam_between(coll, "grounded_leaf_support_post", (x, 0.60, 0.00), (x, 0.60, 0.92), 0.045, mats["wood_dark"], 8)
            beam_between(coll, "upper_support_rope", (x, -0.60, 0.84), (x, 0.60, 0.84), 0.025, mats["rope"], 8)
        add_cube(coll, "aeolian_cloth_ribbon", (0.0, 0.88, 0.70), (0.58, 0.035, 0.16), mats["cloth"], (0.04, 0.0, 0.18), 0.018)
    for i, (x, y) in enumerate([(-0.82, 0.88), (0.68, -0.88), (1.10, 0.18), (-1.12, -0.18)]):
        add_stone(coll, "field_edge_stone", x, y, 0.11, 0.18 + 0.03 * (i % 2), 0.13, 0.09, mats, 0.25 * i)


def add_crop(coll, level, stage, mats, super_crop=False, damaged=False):
    if super_crop:
        growth = SUPER_WINDLEAF_GROWTH[stage]
        count = growth["leaves"]
        for i in range(count):
            yaw = i * math.tau / count + 0.14
            length = growth["length"] * (0.90 + (i % 2) * 0.14)
            width = growth["width"] * (1.0 + (i % 3) * 0.05)
            add_leaf(coll, "super_windleaf_blade", (0.0, 0.0, growth["z"]), length, width, mats["super_leaf"], mats["leaf_vein"], yaw, 0.48 + 0.035 * (i % 2), (i - count / 2) * 0.05)
        beam_between(coll, "super_windleaf_stem", (0, 0, 0.30), (0, 0, growth["stem"]), 0.070 + stage * 0.010, mats["leaf_dark"], 9)
        if stage >= 4:
            support_z = 0.78 + stage * 0.16
            for x in (-0.45, 0.45):
                beam_between(coll, "super_support_post", (x, -0.54, 0.00), (x, -0.54, support_z), 0.026, mats["wood_dark"], 8)
                beam_between(coll, "super_support_rope", (x, -0.54, support_z), (0, 0, growth["stem"] * 0.82), 0.018, mats["rope"], 6)
        return
    clusters = [(-0.46, -0.32), (0.0, 0.12), (0.48, -0.18)]
    if level >= 2:
        clusters.append((-0.28, 0.42))
    if level >= 3:
        clusters.append((0.42, 0.38))
    leaves_by_stage = [2, 3, 4, 5][stage - 1]
    for ci, (cx, cy) in enumerate(clusters):
        for i in range(leaves_by_stage):
            yaw = (i - leaves_by_stage / 2) * 0.46 + ci * 0.2
            length = 0.20 + stage * 0.105 + level * 0.025
            width = 0.070 + stage * 0.028
            z = 0.32 + stage * 0.045
            if damaged and i > 1:
                yaw += 0.8
                z -= 0.08
            add_leaf(coll, "windleaf_blade", (cx, cy, z), length, width, mats["leaf"] if i % 2 else mats["leaf_light"], mats["leaf_vein"], yaw, 0.65, (i - 2) * 0.07, stage >= 3)
        beam_between(coll, "windleaf_stem", (cx, cy, 0.25), (cx, cy, 0.40 + stage * 0.035), 0.018 + stage * 0.004, mats["leaf_dark"], 6)


def add_construction(coll, level, mats):
    for x in (-0.54, 0.0, 0.54):
        add_cube(coll, "loose_plank_stack", (x, -1.03, 0.18), (0.42, 0.15, 0.09), mats["plank" if level >= 3 else "wood"], (0, 0, 0.08 * x), 0.018)
    add_cube(coll, "seed_bag", (0.72, 0.82, 0.23), (0.28, 0.20, 0.30), mats["flax"], (0.1, 0.0, -0.25), 0.055)
    add_cube(coll, "unfinished_rail_gap_marker", (0.58, 0.70, 0.48), (0.44, 0.12, 0.10), mats["wood_cut"], (0, 0, 0.3), 0.02)
    beam_between(coll, "builder_rope_coil", (-0.55, 0.86, 0.20), (-0.18, 0.86, 0.20), 0.028, mats["rope"], 8)
    add_crop(coll, level, 1, mats)


def add_damage(coll, level, mats):
    add_cube(coll, "snapped_front_rail", (-0.42, -0.72, 0.43), (0.80, 0.12, 0.12), mats["wood_dark"], (0.38, -0.04, -0.42), 0.02)
    add_cube(coll, "fallen_post", (0.86, 0.40, 0.28), (0.16, 0.16, 0.74), mats["wood_dark"], (0.0, 1.05, 0.45), 0.025)
    add_cube(coll, "trampled_soil", (0.30, -0.05, 0.29), (0.70, 0.42, 0.045), mats["earth_dark"], (0, 0, -0.16), 0.025)
    if level >= 2:
        beam_between(coll, "torn_flax_tie", (-0.78, 0.54, 0.56), (-0.25, 0.24, 0.38), 0.02, mats["flax"], 6)
    if level >= 3:
        add_cube(coll, "torn_ribbon", (0.24, 0.84, 0.35), (0.34, 0.035, 0.13), mats["cloth"], (0.4, -0.2, 0.1), 0.015)
    add_crop(coll, level, 3, mats, damaged=True)


def make_variant(name: str, level: int, state: str, mats, root_coll):
    existing = bpy.data.collections.get(name)
    if existing:
        bpy.data.collections.remove(existing)
    coll = bpy.data.collections.new(name)
    root_coll.children.link(coll)
    coll["asset_id"] = "windleaf_bed"
    coll["level"] = level
    coll["state"] = state
    add_ground(coll, level, mats)
    if state == "construction":
        add_construction(coll, level, mats)
    elif state == "damaged":
        add_damage(coll, level, mats)
    elif state.startswith("super_stage"):
        add_crop(coll, level, int(state[-2:]), mats, super_crop=True)
    else:
        stage = 4 if state == "active" else int(state[-2:])
        add_crop(coll, level, stage, mats)
    scale_model_to_building_tile(coll)
    return coll


def scale_model_to_building_tile(coll):
    """Scale the bed itself to match earlier building footprint while keeping the tile exact."""
    for obj in coll.objects:
        if obj.name.startswith("windleaf_bed_tile_base"):
            continue
        obj.location.x *= BED_MODEL_SCALE
        obj.location.y *= BED_MODEL_SCALE
        obj.scale.x *= BED_MODEL_SCALE
        obj.scale.y *= BED_MODEL_SCALE


def asset_variants():
    variants = []
    for level in range(1, 4):
        for stage in range(1, 5):
            variants.append((f"windleaf_bed_l{level:02d}_stage{stage:02d}", level, f"stage{stage:02d}"))
        variants.append((f"windleaf_bed_l{level:02d}_active", level, "active"))
        variants.append((f"windleaf_bed_l{level:02d}_construction", level, "construction"))
        variants.append((f"windleaf_bed_l{level:02d}_damaged", level, "damaged"))
    for level in range(1, 4):
        for stage in range(1, 7):
            variants.append((f"windleaf_bed_l{level:02d}_super_stage{stage:02d}", level, f"super_stage{stage:02d}"))
    return variants


def collect_assets(mats, root_coll):
    variants = asset_variants()
    return [make_variant(name, level, state, mats, root_coll) for name, level, state in variants]


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(scene=None):
    scene = scene or bpy.context.scene
    spec = importlib.util.spec_from_file_location("terrain_camera", Path(__file__).with_name("regenerate_early_housing.py"))
    terrain_camera = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(terrain_camera)
    terrain_camera.setup_camera(scene)
    scene.render.resolution_x = 512
    scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    return scene.camera


def set_collection_visible(collections, visible):
    for coll in collections:
        coll.hide_viewport = not visible.get(coll.name, False)
        coll.hide_render = not visible.get(coll.name, False)


def export_collection(coll):
    for obj in bpy.data.objects:
        obj.select_set(False)
    for obj in coll.all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(iter(coll.all_objects), None)
    bpy.ops.export_scene.gltf(filepath=blender_path(OUT_DIR / f"{coll.name}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)


def render_collection(coll, collections):
    set_collection_visible(collections, {coll.name: True})
    bpy.context.scene.render.filepath = blender_path(OUT_DIR / f"{coll.name}.png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)


def create_asset_scene(name: str, level: int, state: str, mats):
    scene = bpy.data.scenes.new("Real_City_Windleaf_Render_" + name)
    root = bpy.data.collections.new(name + "_root")
    scene.collection.children.link(root)
    coll = make_variant(name, level, state, mats, root)
    setup_camera(scene)
    return scene, coll


def render_scene(scene: bpy.types.Scene, name: str):
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.render.filepath = blender_path(OUT_DIR / f"{name}.png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)


def arrange_review_layout(collections):
    set_collection_visible(collections, {coll.name: True for coll in collections})
    cols = 7
    spacing_x = 3.25
    spacing_y = 2.75
    for index, coll in enumerate(collections):
        col = index % cols
        row = index // cols
        offset = Vector(((col - 3) * spacing_x, -(row - 1.5) * spacing_y, 0))
        for obj in coll.objects:
            obj.location += offset
    bpy.context.scene.camera.data.ortho_scale = 13.5
    bpy.context.scene.camera.location = (9.0, -12.0, 9.0)
    look_at(bpy.context.scene.camera, (0, -2.2, 0.35))


def save_manifest(collections):
    assets = []
    for coll in collections:
        assets.append(
            {
                "id": coll.name,
                "level": int(coll["level"]),
                "state": coll["state"],
                "model": f"{coll.name}.glb",
                "sprite": f"{coll.name}.png",
                "anchor": ANCHOR,
            }
        )
    manifest_payload = {"asset": "windleaf_bed", "assets": assets}
    report_payload = {
        "asset": "windleaf_bed",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(collections),
        "levels": [1, 2, 3],
        "states": [
            "stage01",
            "stage02",
            "stage03",
            "stage04",
            "active",
            "construction",
            "damaged",
            "super_stage01",
            "super_stage02",
            "super_stage03",
            "super_stage04",
            "super_stage05",
            "super_stage06",
        ],
        "png_size": [512, 384],
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "ground tile uses the terrain/grass palette and the same daylight setup as terrain tile renders",
            f"bed footprint is scaled by {BED_MODEL_SCALE} on the standard 3.6 tile",
            "L1/L2 walls are log-built; supports are grounded",
            "all levels include six super-windleaf stages",
            "runtime PNGs render from isolated per-asset Blender scenes via OpenGL camera render",
        ],
    }
    with open(blender_path(OUT_DIR / "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, ensure_ascii=False, indent=2)
    with open(blender_path(REPORT_PATH), "w", encoding="utf-8") as handle:
        json.dump(report_payload, handle, ensure_ascii=False, indent=2)


def save_manifest_from_variants():
    assets = []
    for name, level, state in asset_variants():
        assets.append(
            {
                "id": name,
                "level": level,
                "state": state,
                "model": f"{name}.glb",
                "sprite": f"{name}.png",
                "anchor": ANCHOR,
            }
        )
    manifest_payload = {"asset": "windleaf_bed", "assets": assets}
    report_payload = {
        "asset": "windleaf_bed",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(assets),
        "levels": [1, 2, 3],
        "states": [
            "stage01",
            "stage02",
            "stage03",
            "stage04",
            "active",
            "construction",
            "damaged",
            "super_stage01",
            "super_stage02",
            "super_stage03",
            "super_stage04",
            "super_stage05",
            "super_stage06",
        ],
        "png_size": [512, 384],
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "notes": [
            "ground tile uses the terrain/grass palette and the same daylight setup as terrain tile renders",
            f"bed footprint is scaled by {BED_MODEL_SCALE} on the standard 3.6 tile",
            "L1/L2 walls are log-built; supports are grounded",
            "all levels include six super-windleaf stages",
            "runtime PNGs render from isolated per-asset Blender scenes via the terrain daylight render pipeline",
        ],
    }
    with open(blender_path(OUT_DIR / "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, ensure_ascii=False, indent=2)
    with open(blender_path(REPORT_PATH), "w", encoding="utf-8") as handle:
        json.dump(report_payload, handle, ensure_ascii=False, indent=2)


def cleanup_generated_collections():
    prefixes = ("ground_road_", "windleaf_bed_")
    for coll in list(bpy.data.collections):
        if not coll.name.startswith(prefixes):
            continue
        for obj in list(coll.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)


def generate_range(start=0, end=None, save_blend=False):
    ensure_dir()
    cleanup_generated_collections()
    variants = asset_variants()[start:end]
    mats = make_materials()
    collections = []
    for name, level, state in variants:
        scene, coll = create_asset_scene(name, level, state, mats)
        collections.append(coll)
        if bpy.context.window:
            bpy.context.window.scene = scene
        export_collection(coll)
        render_scene(scene, name)
    if save_blend and collections:
        if bpy.context.window:
            scene = bpy.data.scenes.get("Real_City_Windleaf_Render_" + collections[-1].name)
            if scene:
                bpy.context.window.scene = scene
        bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    print("WINDLEAF_BED_RANGE_COMPLETE", start, end, len(collections))
    return [coll.name for coll in collections]


def main():
    ensure_dir()
    mats = make_materials()
    collections = []
    for name, level, state in asset_variants():
        scene, coll = create_asset_scene(name, level, state, mats)
        collections.append(coll)
        if bpy.context.window:
            bpy.context.window.scene = scene
        export_collection(coll)
        render_scene(scene, name)
    if collections and bpy.context.window:
        scene = bpy.data.scenes.get("Real_City_Windleaf_Render_" + collections[-1].name)
        if scene:
            bpy.context.window.scene = scene
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    save_manifest_from_variants()
    print("WINDLEAF_BED_BLENDER_COMPLETE", len(collections), str(BLEND_PATH))


if __name__ == "__main__":
    main()
