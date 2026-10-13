"""Build Blender master/runtime assets for rope yard levels 1-8.

This is the Blender/MCP production route. It deliberately does not call the
legacy pure-Python fallback generator.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path("/home/nshib/projects/real-city")
OUT_DIR = ROOT / "frontend/public/assets/buildings/industry/rope_yard"
BLEND_PATH = OUT_DIR / "rope_yard_l01_l08.blend"
REPORT_PATH = OUT_DIR / "generation-report.json"
LOG_PATH = Path("/tmp/real-city-rope-yard-generation.log")
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
ANCHOR = [256, 292]
PNG_SIZE = [512, 384]
STATES = ["active", "ready", "idle_no_input", "idle_no_workers", "construction", "damaged", "ruined"]

MATERIALS = {
    "grass": (0.27, 0.50, 0.09, 1),
    "grass_light": (0.41, 0.65, 0.16, 1),
    "earth": (0.48, 0.31, 0.16, 1),
    "earth_light": (0.67, 0.47, 0.25, 1),
    "earth_dark": (0.30, 0.18, 0.10, 1),
    "wood": (0.70, 0.45, 0.23, 1),
    "wood_dark": (0.43, 0.25, 0.12, 1),
    "wood_cut": (0.86, 0.63, 0.34, 1),
    "plank": (0.78, 0.55, 0.30, 1),
    "plank_light": (0.94, 0.70, 0.38, 1),
    "premium_wood": (0.39, 0.21, 0.10, 1),
    "rope": (0.73, 0.58, 0.32, 1),
    "rope_dark": (0.48, 0.32, 0.15, 1),
    "fine_rope": (0.95, 0.82, 0.55, 1),
    "flax": (0.86, 0.73, 0.44, 1),
    "windleaf": (0.36, 0.68, 0.30, 1),
    "cloth": (0.62, 0.46, 0.32, 1),
    "stone": (0.56, 0.58, 0.52, 1),
    "stone_block": (0.68, 0.69, 0.62, 1),
    "iron": (0.34, 0.36, 0.36, 1),
    "mechanism": (0.28, 0.32, 0.32, 1),
    "copper": (0.76, 0.42, 0.22, 1),
    "gold": (0.96, 0.72, 0.25, 1),
    "tag_blue": (0.35, 0.63, 0.82, 1),
}


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        return BLENDER_ROOT + "\\" + raw[len(root) :].lstrip("\\")
    if str(path).startswith("/tmp/") or raw.lower().startswith("\\tmp\\"):
        return r"\\wsl.localhost\Debian" + raw
    return raw


def ensure_dir() -> None:
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)


def mat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new("MAT_rope_yard_" + name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.76
        if "Metallic" in bsdf.inputs and name in {"iron", "mechanism", "copper", "gold"}:
            bsdf.inputs["Metallic"].default_value = 0.55
    return material


def make_materials() -> dict[str, bpy.types.Material]:
    for material in list(bpy.data.materials):
        if material.name.startswith("MAT_rope_yard_"):
            bpy.data.materials.remove(material)
    return {name: mat(name, color) for name, color in MATERIALS.items()}


def add_cube(coll, name, loc, scale, material, rot=(0, 0, 0), bevel=0.018, ground=False):
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
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("soft_midpoly_edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    if ground:
        obj["ground"] = True
    return obj


def add_cylinder(coll, name, loc, radius, depth, material, vertices=16, rot=(0, 0, 0), bevel=0.004):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices, radius1=radius, radius2=radius, depth=depth)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("soft_cap_edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return obj


def beam_between(coll, name, start, end, radius, material, vertices=10):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) * 0.5
    direction = end_v - start_v
    obj = add_cylinder(coll, name, mid, radius, direction.length, material, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def add_torus(coll, name, loc, major_radius, minor_radius, material, rot=(0, 0, 0), segments=24, minor_segments=6):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=segments,
        minor_segments=minor_segments,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_mesh"
    obj.data.materials.append(material)
    for source in list(obj.users_collection):
        if source != coll:
            source.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)
    obj.modifiers.new("coil_weighted_normals", "WEIGHTED_NORMAL")
    return obj


def add_ground(coll, mats):
    add_cube(coll, "rope_yard_tile_base", (0, 0, -0.04), (3.60, 3.60, 0.08), mats["grass"], bevel=0.012, ground=True)
    coll["ground_source"] = "frontend/public/assets/terrain/tiles/grass.png"
    for i, (x, y) in enumerate([(-1.35, 1.12), (1.24, 1.18), (1.36, -1.12), (-1.25, -1.16)]):
        for j in range(3):
            beam_between(
                coll,
                "terrain_grass_tuft",
                (x + (j - 1) * 0.045, y, 0.004),
                (x + (j - 1) * 0.080, y + 0.030, 0.12 + 0.025 * (i % 2)),
                0.023,
                mats["grass_light"],
                6,
            )
    add_cube(coll, "rope_yard_work_soil", (0, 0, 0.07), (3.22, 2.34, 0.14), mats["earth"], bevel=0.055, ground=True)
    add_cube(coll, "rope_yard_twist_lane", (-0.12, -0.10, 0.17), (2.62, 0.48, 0.065), mats["earth_light"], (0, 0, 0.02), 0.030, True)


def add_platform(coll, level, state, mats):
    add_ground(coll, mats)
    frame_mat = mats["premium_wood"] if level >= 6 else mats["plank" if level >= 2 else "wood"]
    for y in (-1.04, 1.04):
        add_cube(coll, "yard_long_frame", (0, y, 0.26), (2.72, 0.14, 0.15), frame_mat, (0, 0, 0.01 * y), 0.026, True)
    for x in (-1.36, 1.36):
        add_cube(coll, "yard_side_frame", (x, 0, 0.25), (0.14, 2.04, 0.13), frame_mat, (0, 0, -0.01 * x), 0.026, True)
    if level >= 3:
        for x in (-1.12, 0, 1.12):
            add_cube(coll, "stone_post_pad", (x, -0.20, 0.20), (0.36, 0.30, 0.18), mats["stone"], (0, 0, 0.07), 0.025, True)
    if level >= 4:
        for x, y in ((-1.34, -0.98), (1.34, -0.98), (-1.34, 0.98), (1.34, 0.98)):
            add_cube(coll, "stone_block_corner", (x, y, 0.20), (0.34, 0.26, 0.22), mats["stone_block"], (0, 0, 0.08), 0.025, True)
    if state == "ruined":
        add_cube(coll, "scuffed_lane_overlay", (0.0, -0.08, 0.23), (1.75, 0.52, 0.055), mats["earth_dark"], (0, 0, -0.04), 0.015, True)


def add_flax_bundle(coll, name, x, y, mats, count=5, empty=False):
    if empty:
        add_cube(coll, name + "_empty_mat", (x, y, 0.22), (0.56, 0.34, 0.04), mats["earth_light"], (0, 0, -0.20), 0.012, True)
        return
    for i in range(count):
        add_cube(coll, name + "_stem", (x + i * 0.035, y + i * 0.025, 0.28 + i * 0.028), (0.48, 0.060, 0.065), mats["flax"], (0, 0, -0.24 + i * 0.10), 0.012)
    add_cube(coll, name + "_tie", (x + 0.06, y + 0.05, 0.40), (0.44, 0.045, 0.04), mats["rope"], (0, 0, -0.16), 0.008)


def add_rope_coil(coll, name, loc, mats, radius=0.18, material="rope", fallen=False):
    x, y, z = loc
    rot = (0.0, 0.0, 0.25 if fallen else 0.0)
    add_torus(coll, name + "_outer", (x, y, z), radius, 0.023, mats[material], rot, 24, 6)
    add_torus(coll, name + "_inner", (x, y, z + 0.022), radius * 0.68, 0.020, mats[material], rot, 20, 6)
    add_torus(coll, name + "_core", (x, y, z + 0.042), radius * 0.38, 0.018, mats[material], rot, 16, 6)
    add_cube(coll, name + "_tag", (x + radius * 0.55, y - radius * 0.34, z + 0.045), (0.15, 0.045, 0.035), mats["tag_blue" if material == "fine_rope" else "plank_light"], (0, 0, -0.30), 0.006)


def add_post(coll, name, x, y, height, mats, material="wood_dark", damaged=False):
    if damaged:
        beam_between(coll, name + "_fallen_post", (x - 0.02, y, 0.23), (x + 0.35, y + 0.15, height * 0.55), 0.060, mats[material], 10)
        return
    beam_between(coll, name + "_post", (x, y, 0.20), (x, y, height), 0.060, mats[material], 12)
    add_cube(coll, name + "_hook", (x, y - 0.07, height + 0.04), (0.25, 0.06, 0.065), mats["iron" if height > 0.76 else "wood"], (0, 0, -0.12), 0.010)


def add_rope_line(coll, level, state, mats):
    empty_input = state == "idle_no_input"
    damaged = state in {"damaged", "ruined"}
    post_count = 2 + min(3, level // 2)
    xs = [-1.12 + i * (2.24 / max(1, post_count - 1)) for i in range(post_count)]
    height = 0.68 + level * 0.04
    for index, x in enumerate(xs):
        material = "iron" if level >= 7 and index % 2 == 0 else ("premium_wood" if level >= 6 else "wood_dark")
        add_post(coll, f"twist_line_post_{index}", x, -0.20, height, mats, material, damaged and index % 2 == 0)
    if not empty_input and state not in {"construction", "ruined"}:
        lane_count = 1 + min(3, level // 2)
        for lane in range(lane_count):
            y = -0.34 + lane * 0.13
            z = height + lane * 0.035
            material = "fine_rope" if state == "ready" and level >= 3 and lane == lane_count - 1 else "rope"
            beam_between(coll, f"twisted_rope_lane_{lane}", (-1.26, y, z), (1.26, y + 0.05, z + 0.02), 0.027 + level * 0.002, mats[material], 12)
    if state == "damaged":
        beam_between(coll, "snapped_rope_a", (-1.05, -0.31, height), (-0.45, -0.04, 0.38), 0.027, mats["rope_dark"], 10)
        beam_between(coll, "snapped_rope_b", (0.28, -0.23, height + 0.04), (0.88, 0.04, 0.34), 0.026, mats["rope_dark"], 10)


def add_canopy(coll, level, state, mats):
    if level < 2 or state == "ruined":
        return
    incomplete = state == "construction"
    for x in (-0.38, 0.48):
        beam_between(coll, "canopy_post", (x, 0.91, 0.22), (x, 0.91, 0.92), 0.045, mats["wood_dark"], 10)
    if not incomplete:
        add_cube(coll, "canopy_roof", (0.05, 0.92, 1.02), (1.04, 0.56, 0.11), mats["plank"], (0, 0, -0.03), 0.026)
        add_cube(coll, "canopy_wind_flag", (0.56, 0.71, 1.13), (0.18, 0.035, 0.13), mats["cloth"], (0, 0, -0.10), 0.005)


def add_drum(coll, name, loc, level, mats, spinning=False, broken=False):
    x, y, z = loc
    core = "mechanism" if level >= 6 else ("iron" if level >= 5 else "wood_dark")
    side = "copper" if level >= 7 else ("iron" if level >= 5 else "wood")
    rot = (math.pi / 2, 0, 0.12 if spinning else -0.08)
    add_cylinder(coll, name + "_core", (x, y, z), 0.18, 0.46, mats[core], 18, rot, 0.006)
    add_cylinder(coll, name + "_left_plate", (x, y - 0.26, z), 0.22, 0.045, mats[side], 18, rot, 0.006)
    add_cylinder(coll, name + "_right_plate", (x, y + 0.26, z), 0.22, 0.045, mats[side], 18, rot, 0.006)
    if broken:
        beam_between(coll, name + "_broken_axle", (x + 0.23, y - 0.20, z - 0.12), (x + 0.56, y - 0.02, z - 0.20), 0.030, mats["iron"], 10)


def add_quality_rack(coll, level, mats):
    if level < 3:
        return
    for x in (1.18, 1.52):
        beam_between(coll, "quality_rack_post", (x, 0.70, 0.20), (x, 0.70, 0.78), 0.040, mats["wood_dark"], 10)
    beam_between(coll, "quality_rack_bar", (1.12, 0.70, 0.78), (1.58, 0.66, 0.78), 0.035, mats["wood"], 10)
    add_rope_coil(coll, "quality_fine_rope", (1.36, 0.58, 0.31), mats, 0.15, "fine_rope")
    if level >= 8:
        add_cube(coll, "gold_quality_calibrator", (1.62, 0.43, 0.53), (0.16, 0.12, 0.20), mats["gold"], (0, 0, -0.18), 0.014)


def add_level_details(coll, level, state, mats):
    damaged = state in {"damaged", "ruined"}
    add_flax_bundle(coll, "input_flax_stack", -1.20, 0.58, mats, 3 + min(3, level), state == "idle_no_input")
    if level == 1:
        add_cube(coll, "windleaf_binder_bundle", (-1.34, -0.70, 0.30), (0.42, 0.18, 0.16), mats["windleaf"], (0, 0, -0.18), 0.018)
    add_canopy(coll, level, state, mats)
    if level >= 5:
        for x in (-0.44, 0.44):
            add_cube(coll, "cloth_tension_band", (x, -0.70, 0.52), (0.42, 0.06, 0.08), mats["cloth"], (0, 0, 0.12), 0.010)
        add_cube(coll, "iron_hook_rack", (0.80, -0.74, 0.62), (0.44, 0.08, 0.11), mats["iron"], (0, 0, -0.08), 0.010)
    if level >= 6:
        add_cube(coll, "gear_box", (-0.06, -0.82, 0.42), (0.38, 0.30, 0.24), mats["mechanism"], (0, 0, 0.10), 0.018)
        add_cylinder(coll, "gear_cap", (-0.06, -0.82, 0.58), 0.14, 0.055, mats["iron"], 14, (0, 0, 0), 0.004)
    if level >= 7:
        for x in (-0.22, 0.22, 0.66):
            add_cylinder(coll, "copper_bushing", (x, -0.42, 0.62), 0.060, 0.10, mats["copper"], 12, (math.pi / 2, 0, 0.20), 0.004)
    drum_count = 1 + (level >= 3) + (level >= 7)
    for index in range(drum_count):
        add_drum(coll, f"rope_drum_{index}", (-0.70 + index * 0.52, -0.72, 0.42), level, mats, state == "active", damaged and index == 0)
    if state == "ready":
        for index in range(2 + level // 2):
            add_rope_coil(coll, f"ready_rope_coil_{index}", (-0.72 + index * 0.31, 0.70, 0.30), mats, 0.15 + level * 0.008, "rope")
    elif state != "idle_no_input":
        add_rope_coil(coll, "work_rope_coil", (0.84, 0.62, 0.30), mats, 0.17 + level * 0.010, "rope", damaged)
    if state == "idle_no_workers":
        add_cube(coll, "empty_worker_bench", (-0.86, 0.66, 0.30), (0.60, 0.28, 0.16), mats["plank"], (0, 0, 0.10), 0.016)
    add_quality_rack(coll, level, mats)
    if state == "construction":
        add_cube(coll, "loose_board_a", (0.58, -0.28, 0.30), (0.92, 0.10, 0.08), mats["plank"], (0, 0, -0.38), 0.012)
        add_cube(coll, "loose_board_b", (0.76, -0.08, 0.38), (0.66, 0.09, 0.07), mats["wood"], (0, 0, -0.16), 0.012)
        add_flax_bundle(coll, "construction_flax_materials", -0.90, 0.84, mats, 3, False)
    if damaged:
        beam_between(coll, "snapped_stand_ground", (-0.82, -0.05, 0.24), (-0.22, 0.12, 0.30), 0.055, mats["wood_dark"], 10)
    if state == "ruined":
        for i, (x, y, yaw) in enumerate(((0.48, -0.84, 0.46), (-0.96, 0.10, -0.56), (0.98, 0.20, 0.22), (0.18, 0.86, -0.24))):
            add_cube(coll, f"ruin_plank_{i}", (x, y, 0.24), (0.74, 0.12, 0.09), mats["wood_dark"], (0, 0, yaw), 0.012)


def make_variant(name: str, level: int, state: str, mats, root):
    coll = bpy.data.collections.new(name)
    root.children.link(coll)
    coll["asset_id"] = "rope_yard"
    coll["level"] = level
    coll["state"] = state
    add_platform(coll, level, state, mats)
    if state == "construction":
        add_rope_line(coll, level, "idle_no_input", mats)
    else:
        add_rope_line(coll, level, state, mats)
    add_level_details(coll, level, state, mats)
    return coll


def asset_variants():
    for level in range(1, 9):
        for state in STATES:
            yield f"rope_yard_l{level:02d}_{state}", level, state


def setup_camera(scene):
    cam_data = bpy.data.cameras.new("rope_yard_isometric_camera")
    cam = bpy.data.objects.new("rope_yard_isometric_camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (8.0, -8.0, 6.53)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 8.65
    scene.camera = cam
    scene.render.resolution_x = PNG_SIZE[0]
    scene.render.resolution_y = PNG_SIZE[1]
    scene.render.film_transparent = True
    initial = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y
    target_y = ANCHOR[1] / PNG_SIZE[1]
    cam_data.shift_y = 0.1
    delta = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y - initial
    cam_data.shift_y = (target_y - initial) * 0.1 / delta
    for lname, pos, energy, size in (("key", (-3, -5, 8), 1050, 5), ("fill", (5, 1, 6), 650, 5)):
        light = bpy.data.lights.new("rope_yard_" + lname, "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("rope_yard_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.65, 0.75, 0.90, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"


def create_asset_scene(name: str, level: int, state: str, mats):
    scene = bpy.data.scenes.new("Real_City_Rope_Yard_Render_" + name)
    root = bpy.data.collections.new(name + "_root")
    scene.collection.children.link(root)
    coll = make_variant(name, level, state, mats, root)
    setup_camera(scene)
    return scene, coll


def triangle_count(coll) -> int:
    total = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in coll.all_objects:
        if obj.type != "MESH":
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        eval_obj.to_mesh_clear()
    return total


def export_collection(coll):
    for obj in bpy.data.objects:
        obj.select_set(False)
    objects = list(coll.all_objects)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None
    bpy.ops.export_scene.gltf(filepath=blender_path(OUT_DIR / f"{coll.name}.glb"), export_format="GLB", use_selection=True, use_active_scene=True)


def render_scene(scene, name):
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.render.filepath = blender_path(OUT_DIR / f"{name}.png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)


def cleanup_generated():
    for scene in list(bpy.data.scenes):
        if scene.name.startswith("Real_City_Rope_Yard_Render_"):
            bpy.data.scenes.remove(scene)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("rope_yard_") or coll.name.endswith("_root"):
            for obj in list(coll.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(coll)


def save_manifest(report_items):
    manifest = {
        "asset_id": "rope_yard",
        "category": "industry",
        "display_name": "Канатный двор",
        "style": "Aeolian bright fantasy stylized mid-poly open craft rope yard",
        "pipeline": "blender_mcp_midpoly",
        "levels": list(range(1, 9)),
        "states": STATES,
        "sprite": {"size": PNG_SIZE, "anchor": ANCHOR},
        "source_blend": BLEND_PATH.name,
        "items": [
            {
                "id": item["name"],
                "level": item["level"],
                "state": item["state"],
                "glb": f"{item['name']}.glb",
                "png": f"{item['name']}.png",
                "anchor": ANCHOR,
                "triangles": item["triangles"],
            }
            for item in report_items
        ],
    }
    report = {
        "asset": "rope_yard",
        "pipeline": "blender_mcp_midpoly",
        "blend": BLEND_PATH.name,
        "count": len(report_items),
        "levels": list(range(1, 9)),
        "states": STATES,
        "png_size": PNG_SIZE,
        "anchor": ANCHOR,
        "style": "Aeolian bright fantasy mid-poly",
        "material_mapping": {
            "wood/planks": "yard frame, canopy, loose construction boards",
            "flax": "input bundles near the work lane",
            "windleaf": "level 1 natural binder bundle",
            "stone/stone_block": "post pads and late stable corner blocks",
            "rope": "twist lanes, coils, lashings and ready output",
            "fabric": "tension bands from level 5",
            "iron/mechanism": "hooks, drums and gear box from levels 5-6",
            "copper/gold": "late bushings and quality calibrator",
        },
        "notes": [
            "MCP/Blender generation route; legacy pure-Python fallback is not used",
            "open 1x1 craft yard remains readable from isometric camera",
            "levels add real material/shape progression from manual wood frame to mechanized rope station",
            "production states change input, workers, ready coils, construction and destruction geometry",
            "construction/damaged/ruined keep the same ground tile and alter only overlay geometry",
        ],
        "assets": report_items,
    }
    with open(blender_path(OUT_DIR / "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(blender_path(REPORT_PATH), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    ensure_dir()
    cleanup_generated()
    mats = make_materials()
    report_items = []
    lines = []
    last_scene = None
    for name, level, state in asset_variants():
        scene, coll = create_asset_scene(name, level, state, mats)
        last_scene = scene
        if bpy.context.window:
            bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        tris = triangle_count(coll)
        export_collection(coll)
        render_scene(scene, name)
        report_items.append({"name": name, "level": level, "state": state, "triangles": tris})
        lines.append(f"{name}: triangles={tris}")
    if last_scene and bpy.context.window:
        bpy.context.window.scene = last_scene
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    save_manifest(report_items)
    with open(blender_path(LOG_PATH), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write(f"\nROPE_YARD_BLENDER_COMPLETE {len(report_items)}\n")
    print("ROPE_YARD_BLENDER_COMPLETE", len(report_items), str(BLEND_PATH))


if __name__ == "__main__":
    main()
