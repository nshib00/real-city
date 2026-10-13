#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "oil_well"
ASSET_ID = "oil_well"
LEVELS = (1, 2, 3)
STATES = ("active", "construction", "damaged", "ruined")


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.82):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def setup_materials():
    return {
        "grass": material("grass_bright", (0.36, 0.73, 0.29, 1)),
        "earth": material("earth_oil_stained", (0.34, 0.23, 0.13, 1)),
        "oil": material("oil_black_gloss", (0.015, 0.012, 0.011, 1), 0.28),
        "wood": material("wood_pale", (0.67, 0.45, 0.24, 1)),
        "metal": material("metal_worn", (0.40, 0.43, 0.42, 1)),
        "dark_metal": material("metal_dark", (0.14, 0.16, 0.17, 1)),
        "concrete": material("concrete_light", (0.60, 0.59, 0.54, 1)),
        "copper": material("copper_oiled", (0.74, 0.39, 0.17, 1)),
        "amber": material("amber_accent", (1.0, 0.58, 0.12, 1)),
        "aeolian": material("aeolian_alloy_blue", (0.36, 0.70, 0.84, 1)),
        "warning": material("warning_yellow", (0.95, 0.72, 0.18, 1)),
    }


def set_origin_name(obj, name: str, mat=None):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_cube(name: str, loc, scale, mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if min(scale) > 0.035:
        bevel = obj.modifiers.new("soft_bevel", "BEVEL")
        bevel.width = min(scale) * 0.08
        bevel.segments = 2
        obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return set_origin_name(obj, name, mat)


def add_cylinder(name: str, loc, radius: float, depth: float, mat=None, vertices=16, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return set_origin_name(obj, name, mat)


def add_cylinder_between(name: str, start, end, radius: float, mat=None, vertices=12):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) * 0.5
    direction = end_v - start_v
    length = direction.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return set_origin_name(obj, name, mat)


def add_diamond(name: str, radius: float, z: float, mat):
    mesh = bpy.data.meshes.new(name)
    verts = [(0, radius, z), (radius, 0, z), (0, -radius, z), (-radius, 0, z)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_oil_pool(mats):
    add_diamond("oil_stained_ground", 1.05, 0.018, mats["earth"])
    add_cylinder("glossy_oil_pool", (0, 0, 0.035), 0.58, 0.018, mats["oil"], vertices=32)
    for index, (x, y, r) in enumerate([(-0.32, 0.12, 0.055), (0.18, -0.22, 0.04), (0.34, 0.20, 0.032)]):
        add_cylinder(f"oil_bubble_{index}", (x, y, 0.055), r, 0.014, mats["oil"], vertices=12)


def add_barrel(name: str, x: float, y: float, mat, band_mat):
    add_cylinder(name, (x, y, 0.23), 0.12, 0.34, mat, vertices=18, rot=(math.pi / 2, 0, 0))
    add_cylinder(f"{name}_front_band", (x, y - 0.17, 0.23), 0.123, 0.025, band_mat, vertices=18, rot=(math.pi / 2, 0, 0))
    add_cylinder(f"{name}_back_band", (x, y + 0.17, 0.23), 0.123, 0.025, band_mat, vertices=18, rot=(math.pi / 2, 0, 0))


def add_tower(level: int, state: str, mats):
    height = {1: 1.1, 2: 1.45, 3: 1.75}[level]
    spread = {1: 0.55, 2: 0.70, 3: 0.82}[level]
    top = {1: 0.20, 2: 0.25, 3: 0.30}[level]
    metal = mats["wood"] if level == 1 else mats["metal"]
    brace = mats["metal"] if level < 3 else mats["dark_metal"]
    completion = {"active": 1.0, "construction": 0.58, "damaged": 0.86, "ruined": 0.38}[state]
    tilt = 0.16 if state in {"damaged", "ruined"} else 0.0

    corners = [(-spread, -spread), (spread, -spread), (spread, spread), (-spread, spread)]
    top_corners = [(-top + tilt, -top), (top + tilt, -top), (top + tilt, top), (-top + tilt, top)]
    for i, ((bx, by), (tx, ty)) in enumerate(zip(corners, top_corners)):
        if state == "ruined" and i == 1:
            end = (tx * 1.4, ty - 0.45, height * 0.25)
        else:
            end = (tx, ty, height * completion)
        add_cylinder_between(f"derrick_leg_{i}", (bx, by, 0.08), end, 0.035 + level * 0.005, metal)

    if state != "ruined":
        for z in [height * 0.35, height * 0.68]:
            if z <= height * completion + 0.05:
                add_cylinder_between(f"derrick_cross_a_{z:.1f}", (-spread * 0.82, -spread, z), (spread * 0.82, spread, z + 0.08), 0.022, brace)
                add_cylinder_between(f"derrick_cross_b_{z:.1f}", (spread, -spread * 0.82, z), (-spread, spread * 0.82, z + 0.08), 0.022, brace)
    else:
        add_cylinder_between("fallen_derrick_beam_a", (-0.65, -0.48, 0.08), (0.72, 0.34, 0.22), 0.035, brace)
        add_cylinder_between("fallen_derrick_beam_b", (-0.42, 0.52, 0.08), (0.56, -0.58, 0.18), 0.03, brace)

    if state != "construction":
        add_cylinder("wellhead", (0, 0, 0.18), 0.10, 0.28, mats["dark_metal"], vertices=16)
        add_cylinder_between("pump_rod", (0, 0, 0.32), (0.0 + tilt, 0.0, min(height * completion, height - 0.2)), 0.018, mats["dark_metal"], vertices=10)

    if state in {"active", "damaged"}:
        beam_z = min(height * 0.88, height * completion)
        add_cylinder_between("walking_beam", (-0.55, -0.06, beam_z), (0.72 + tilt, 0.06, beam_z + (0.08 if state == "damaged" else 0.0)), 0.045, brace)
        add_cube("horsehead", (0.82 + tilt, 0.07, beam_z - 0.05), (0.10, 0.10, 0.30), brace)
        add_cylinder("counterweight", (-0.65, -0.08, beam_z - 0.12), 0.13, 0.08, mats["dark_metal"], vertices=18, rot=(math.pi / 2, 0, 0))

    if level >= 2 and state != "ruined":
        add_cube("concrete_service_pad", (0.58, -0.58, 0.055), (0.76, 0.34, 0.08), mats["concrete"])
        add_cylinder_between("outlet_pipe_a", (0.15, -0.15, 0.14), (0.78, -0.58, 0.14), 0.035, mats["dark_metal"])
        add_cylinder_between("outlet_pipe_b", (0.78, -0.58, 0.14), (1.12, -0.42, 0.14), 0.035, mats["dark_metal"])
        add_cylinder("small_tank", (-0.88, 0.42, 0.32), 0.18, 0.52, mats["metal"], vertices=20)
    if level >= 3 and state != "ruined":
        add_cylinder("protected_reservoir", (-0.95, -0.36, 0.38), 0.24, 0.62, mats["dark_metal"], vertices=22)
        add_cube("motor_block", (0.98, 0.42, 0.20), (0.42, 0.28, 0.26), mats["dark_metal"])
        add_cylinder_between("aeolian_feed_line", (0.78, 0.34, 0.32), (0.25, 0.15, 0.55), 0.026, mats["aeolian"])
        add_cylinder("amber_pressure_gauge", (0.62, 0.03, 0.62), 0.045, 0.025, mats["amber"], vertices=12, rot=(math.pi / 2, 0, 0))

    if state == "construction":
        add_cube("stacked_planks", (-0.88, -0.34, 0.10), (0.48, 0.16, 0.10), mats["wood"])
        add_cube("mechanism_crate", (0.90, 0.30, 0.12), (0.30, 0.24, 0.22), mats["metal"])
    if state in {"damaged", "ruined"}:
        add_cylinder_between("broken_pipe_leak", (0.25, -0.28, 0.12), (0.78, -0.64, 0.08), 0.035, mats["dark_metal"])
        add_diamond("fresh_oil_leak", 0.32, 0.05, mats["oil"])


def build_asset(level: int, state: str) -> int:
    clear_scene()
    mats = setup_materials()
    add_diamond("terrain_ground_cell", 1.8, 0.0, mats["grass"])
    add_oil_pool(mats)
    add_tower(level, state, mats)
    add_barrel("oil_barrel_a", -1.15, 0.78, mats["dark_metal"], mats["copper"])
    if level >= 2:
        add_barrel("oil_barrel_b", -1.38, 0.56, mats["metal"], mats["warning"])
    for i, (x, y) in enumerate([(-1.35, -0.35), (-1.0, 1.0), (1.18, 0.96), (1.35, -0.82)]):
        add_cylinder(f"survey_stake_{i}", (x, y, 0.15), 0.018, 0.30, mats["wood"], vertices=8)

    tri_count = sum(len(poly.vertices) - 2 for obj in bpy.context.scene.objects if obj.type == "MESH" for poly in obj.data.polygons)
    return tri_count


def setup_camera() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -3.8, 6.2))
    light = bpy.context.object
    light.name = "softbox_key"
    light.data.energy = 480
    light.data.size = 5.0
    bpy.ops.object.camera_add(location=(4.5, -5.2, 4.2), rotation=(math.radians(60), 0, math.radians(42)))
    camera = bpy.context.object
    direction = Vector((0, 0, 0.52)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.9
    bpy.context.scene.camera = camera
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 384
    bpy.context.view_layer.update()
    target_y = 1 - 292 / 384
    initial = world_to_camera_view(bpy.context.scene, camera, Vector((0, 0, 0))).y
    camera.data.shift_y = 0.1
    delta = world_to_camera_view(bpy.context.scene, camera, Vector((0, 0, 0))).y - initial
    camera.data.shift_y = (target_y - initial) * 0.1 / delta
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.eevee.taa_render_samples = 64
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.look = "Medium High Contrast"
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.view_settings.gamma = 1


def export_asset(level: int, state: str) -> dict:
    triangles = build_asset(level, state)
    setup_camera()
    name = f"{ASSET_ID}_l{level:02d}_{state}"
    png_path = OUT_DIR / f"{name}.png"
    glb_path = OUT_DIR / f"{name}.glb"
    bpy.context.scene.render.filepath = str(png_path)
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB")
    return {"level": level, "state": state, "png": png_path.name, "glb": glb_path.name, "triangles": triangles}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for level in LEVELS:
        for state in STATES:
            entries.append(export_asset(level, state))
    manifest = {
        "asset_id": ASSET_ID,
        "building_type": "oil_well",
        "category": "industry",
        "display_name": "Нефтяная вышка",
        "levels": list(LEVELS),
        "states": list(STATES),
        "anchor": [256, 292],
        "size": [512, 384],
        "assets": entries,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / "oil_well_levels.blend"))
    print(json.dumps({"generated": len(entries), "out": str(OUT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
