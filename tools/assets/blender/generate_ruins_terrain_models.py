"""Generate capturable ruins terrain variants for Real City.

Run with Blender:
  blender --background --python tools/assets/blender/generate_ruins_terrain_models.py
"""
import importlib.util
import json
import math
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend/public/assets/terrain/tiles"
VARIANT_DIR = OUT_DIR / "ruins_variants"

spec = importlib.util.spec_from_file_location(
    "terrain_geometry",
    Path(__file__).with_name("regenerate_early_housing.py"),
)
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

VARIANTS = (
    ("ruins_town_square", "Старая ратушная площадь"),
    ("ruins_archive", "Архив чертежей"),
    ("ruins_mint", "Монетный двор"),
    ("ruins_storage", "Старый складской узел"),
    ("ruins_greenhouse", "Заросшая оранжерея"),
    ("ruins_water_station", "Водяная станция"),
    ("ruins_bastion", "Каменный бастион"),
    ("ruins_mechanic_workshop", "Мастерская механизмов"),
    ("ruins_wind_shrine", "Святилище ветра"),
    ("ruins_ore_obelisk", "Залежный обелиск"),
    ("ruins_rift_watch", "Разломная сторожевая"),
    ("ruins_river_lighthouse", "Речной маяк"),
)

SCENE = None
COLLECTIONS = {}
REPORT = {}


def material(role, color, *, metallic=0.0, roughness=0.78, emission=0.0):
    mat = bpy.data.materials.new("MAT_ruins_" + role)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if emission:
        shader.inputs["Emission Color"].default_value = (*color, 1)
        shader.inputs["Emission Strength"].default_value = emission
    H.MATS[role] = mat


def palette():
    for role, color, metallic, roughness, emission in (
        ("grass", (0.26, 0.48, 0.08), 0, 0.86, 0),
        ("grass_light", (0.37, 0.59, 0.13), 0, 0.82, 0),
        ("moss", (0.13, 0.35, 0.08), 0, 0.88, 0),
        ("earth", (0.33, 0.21, 0.11), 0, 0.88, 0),
        ("stone", (0.57, 0.56, 0.45), 0, 0.8, 0),
        ("stone_light", (0.72, 0.70, 0.57), 0, 0.74, 0),
        ("stone_dark", (0.35, 0.36, 0.32), 0, 0.84, 0),
        ("wood", (0.52, 0.30, 0.12), 0, 0.78, 0),
        ("wood_dark", (0.24, 0.12, 0.06), 0, 0.82, 0),
        ("metal", (0.45, 0.42, 0.34), 0.45, 0.5, 0),
        ("brass", (0.83, 0.54, 0.18), 0.55, 0.42, 0),
        ("glass", (0.54, 0.86, 0.86), 0, 0.25, 0.08),
        ("crystal", (0.58, 0.36, 0.92), 0, 0.34, 0.18),
        ("water", (0.08, 0.49, 0.64), 0, 0.26, 0.03),
        ("amber", (0.95, 0.48, 0.10), 0, 0.42, 0.18),
        ("danger", (0.72, 0.13, 0.08), 0, 0.66, 0.08),
    ):
        material(role, color, metallic=metallic, roughness=roughness, emission=emission)


def mesh_from_bmesh(bm, name, pos, role):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    data = bpy.data.meshes.new(H.PREFIX + "_" + name)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(data.name, data)
    H.COL.objects.link(obj)
    obj.location = pos
    data.materials.append(H.MATS[role])
    return obj


def cylinder(name, pos, radius, height, role, segments=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=height,
    )
    return mesh_from_bmesh(bm, name, pos, role)


def rough_rock(name, pos, size, role="stone", seed=0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1)
    for vertex in bm.verts:
        wobble = 1 + 0.08 * math.sin(vertex.co.x * 11 + vertex.co.y * 7 + vertex.co.z * 13 + seed)
        vertex.co = Vector((vertex.co.x * size[0] * wobble, vertex.co.y * size[1] * wobble, vertex.co.z * size[2] * wobble))
    return mesh_from_bmesh(bm, name, pos, role)


def base():
    H.box("tile_surface", (0, 0, -0.015), (3.6, 3.6, 0.03), "grass", 0)
    for x, y, sx, sy, rot in (
        (-0.78, -0.42, 0.82, 0.50, 0.08),
        (0.16, -0.44, 0.84, 0.48, -0.04),
        (0.72, 0.22, 0.62, 0.42, 0.12),
        (-0.46, 0.34, 0.74, 0.44, -0.1),
    ):
        H.box("sunken_paving", (x, y, 0.035), (sx, sy, 0.07), "stone", 0.025, rotation=(0, 0, rot))
    for x, y, scale in ((-1.32, 0.82, 1.2), (1.18, -1.0, 1.0), (-1.12, -1.06, 0.85), (1.22, 0.76, 0.95)):
        tuft(x, y, scale)


def tuft(x, y, scale=1.0):
    for i in range(3):
        H.beam(
            "grass_tuft",
            (x + (i - 1) * 0.04, y, 0.008),
            (x + (i - 1) * 0.08, y + 0.035, 0.13 * scale + (i % 2) * 0.04),
            0.025,
            "grass_light",
        )


def broken_wall(x, y, width=0.42, height=1.0, blocks=4, role="stone", rot=0):
    for i in range(blocks):
        z = 0.16 + i * height / blocks
        h = height / blocks * (0.82 if i == blocks - 1 else 0.95)
        if i == blocks - 1 and (x + y) > 0.2:
            continue
        H.box("broken_wall_block", (x, y, z), (width, 0.30, h), role, 0.035, rotation=(0, 0, rot))


def arch(cx, cy, radius=0.62, role="stone"):
    broken_wall(cx - radius, cy, 0.34, 1.0, 4, role)
    broken_wall(cx + radius, cy, 0.34, 0.82, 3, role)
    for i in range(6):
        angle = math.pi * (0.12 + i * 0.15)
        x = cx + radius * math.cos(angle)
        z = 0.98 + radius * math.sin(angle)
        H.box("arch_voussoir", (x, cy, z), (0.25, 0.34, 0.22), role, 0.025, rotation=(0, angle - math.pi / 2, 0))


def fallen_stones(seed=0, count=8):
    for i in range(count):
        x = -1.08 + ((i * 0.47 + seed * 0.19) % 2.1)
        y = -0.96 + ((i * 0.31 + seed * 0.11) % 1.6)
        if -0.28 < x < 0.36 and -0.26 < y < 0.28:
            x += 0.48
        H.box("fallen_masonry", (x, y, 0.10), (0.25, 0.20, 0.16), "stone", 0.03, rotation=(0.08 * i, 0.04 * seed, 0.41 * i))


def flag_stub(x, y, role="wood"):
    H.beam("broken_flagpole", (x, y, 0.08), (x + 0.08, y, 0.72), 0.045, role)
    H.box("torn_banner", (x + 0.12, y - 0.02, 0.54), (0.20, 0.035, 0.18), "danger", 0.008)


def fountain():
    cylinder("dry_fountain_basin", (0.0, -0.18, 0.12), 0.42, 0.16, "stone_light")
    cylinder("fountain_inner", (0.0, -0.18, 0.24), 0.26, 0.08, "stone")
    cylinder("broken_fountain_core", (0.03, -0.15, 0.42), 0.11, 0.28, "stone_light")


def town_square():
    base()
    arch(-0.35, 0.42, 0.54)
    broken_wall(0.94, 0.18, 0.36, 0.72, 3)
    fountain()
    flag_stub(-1.03, -0.22)
    fallen_stones(1, 7)
    rough_rock("moss_patch", (-0.84, 0.58, 0.14), (0.28, 0.17, 0.08), "moss", 2)


def archive():
    base()
    broken_wall(-0.72, 0.22, 0.38, 1.35, 5)
    broken_wall(0.10, 0.24, 0.34, 1.08, 4)
    arch(-0.32, 0.24, 0.42)
    for i in range(3):
        H.box("fallen_bookshelf", (0.55, -0.46 + i * 0.22, 0.24), (0.46, 0.10, 0.32), "wood", 0.015, rotation=(0.1, 0.0, 0.12 * i))
    for x, z in ((-0.68, 0.98), (-0.05, 0.82), (0.52, 0.30)):
        H.box("archive_glass_shard", (x, -0.06, z), (0.12, 0.035, 0.26), "glass", 0.006, rotation=(0, 0.18, 0))
    H.box("glowing_rune_slab", (0.05, -0.78, 0.12), (0.54, 0.36, 0.08), "crystal", 0.025)
    fallen_stones(2, 6)


def mint():
    base()
    broken_wall(-0.72, 0.18, 0.46, 0.92, 4)
    broken_wall(0.58, 0.20, 0.46, 0.76, 3)
    H.box("cracked_vault", (0.0, -0.36, 0.36), (0.74, 0.48, 0.58), "stone_dark", 0.045)
    H.box("vault_door_slab", (0.03, -0.64, 0.38), (0.52, 0.10, 0.48), "metal", 0.025, rotation=(0.0, 0.0, -0.12))
    cylinder("coin_press_base", (0.72, -0.08, 0.22), 0.22, 0.24, "brass")
    H.beam("coin_press_arm", (0.50, -0.08, 0.52), (1.02, -0.08, 0.70), 0.045, "metal")
    for i in range(8):
        cylinder("scattered_coin", (-0.34 + i * 0.10, -0.86 + (i % 3) * 0.07, 0.06), 0.055, 0.018, "brass", 12)
    fallen_stones(3, 5)


def storage():
    base()
    broken_wall(-0.86, 0.15, 0.36, 0.92, 4, "stone")
    broken_wall(0.88, 0.10, 0.36, 0.78, 3, "stone")
    for i, (x, y, rot) in enumerate(((-0.32, -0.34, 0.1), (0.24, -0.36, -0.18), (0.62, -0.62, 0.26))):
        H.box("broken_crate", (x, y, 0.19), (0.42, 0.35, 0.30), "wood", 0.025, rotation=(0.0, 0.0, rot))
        H.beam("crate_slat", (x - 0.19, y - 0.20, 0.36), (x + 0.19, y + 0.14, 0.36), 0.035, "wood_dark")
    H.beam("fallen_lift_frame", (-0.70, 0.46, 0.12), (0.50, 0.42, 0.48), 0.06, "wood_dark")
    H.box("cart_wheel", (0.88, -0.22, 0.19), (0.10, 0.32, 0.32), "wood_dark", 0.02)
    fallen_stones(4, 5)


def greenhouse():
    base()
    for x in (-0.68, 0.0, 0.68):
        arch(x, 0.08, 0.34, "stone_light")
    for i, x in enumerate((-0.58, -0.18, 0.22, 0.62)):
        H.box("glass_panel_shard", (x, -0.18, 0.76 - i * 0.05), (0.24, 0.032, 0.32), "glass", 0.006, rotation=(0.24, 0, 0.12 * i))
    for x, y, s in ((-0.76, -0.66, 1.25), (-0.24, -0.70, 1.0), (0.38, -0.62, 1.18), (0.82, 0.34, 1.1)):
        tuft(x, y, s)
        rough_rock("rare_plant", (x + 0.08, y + 0.04, 0.18), (0.13 * s, 0.10 * s, 0.16 * s), "moss", int(x * 10))
    fallen_stones(5, 5)


def water_station():
    base()
    H.box("stone_channel", (-0.18, -0.66, 0.065), (1.80, 0.36, 0.10), "water", 0.015)
    broken_wall(-0.84, 0.16, 0.34, 0.84, 3)
    broken_wall(0.74, 0.18, 0.34, 0.70, 3)
    cylinder("pump_body", (-0.28, -0.10, 0.36), 0.18, 0.40, "metal")
    H.beam("pump_handle", (-0.46, -0.10, 0.62), (0.12, -0.10, 0.82), 0.045, "brass")
    for i in range(8):
        angle = i * math.tau / 8
        H.beam("broken_waterwheel_spoke", (0.74, -0.40, 0.52), (0.74 + 0.34 * math.cos(angle), -0.40, 0.52 + 0.34 * math.sin(angle)), 0.035, "wood")
    cylinder("waterwheel_hub", (0.74, -0.40, 0.52), 0.10, 0.12, "wood")
    fallen_stones(6, 5)


def bastion():
    base()
    for x, y in ((-0.82, 0.34), (0.0, 0.42), (0.82, 0.28)):
        broken_wall(x, y, 0.46, 1.15 if x == 0 else 0.85, 4, "stone_dark")
        H.box("battlement_gap", (x, y - 0.18, 0.94), (0.18, 0.16, 0.20), "stone", 0.012)
    H.box("fallen_battlement", (0.55, -0.44, 0.18), (0.72, 0.36, 0.22), "stone_dark", 0.035, rotation=(0.0, 0.2, -0.38))
    flag_stub(-0.44, -0.20, "metal")
    fallen_stones(7, 9)


def mechanic_workshop():
    base()
    broken_wall(-0.68, 0.16, 0.36, 0.94, 4)
    broken_wall(0.72, 0.18, 0.36, 0.72, 3)
    cylinder("large_gear", (0.02, -0.34, 0.28), 0.34, 0.08, "brass", 18)
    for i in range(8):
        angle = i * math.tau / 8
        H.box("gear_tooth", (0.02 + 0.33 * math.cos(angle), -0.34 + 0.33 * math.sin(angle), 0.30), (0.10, 0.06, 0.10), "brass", 0.01, rotation=(0, 0, angle))
    H.box("broken_workbench", (-0.54, -0.58, 0.23), (0.68, 0.30, 0.22), "wood", 0.025, rotation=(0.0, 0, 0.16))
    H.beam("bent_crane_arm", (0.54, 0.18, 0.18), (0.96, 0.02, 0.86), 0.06, "metal")
    H.beam("hanging_chain", (0.96, 0.02, 0.86), (0.94, 0.04, 0.42), 0.025, "metal")
    fallen_stones(8, 5)


def wind_shrine():
    base()
    for x in (-0.64, 0.64):
        broken_wall(x, 0.18, 0.28, 1.24, 5, "stone_light")
    arch(0.0, 0.18, 0.58, "stone_light")
    cylinder("wind_shrine_dais", (0.0, -0.38, 0.14), 0.45, 0.16, "stone")
    H.beam("bent_vane_pole", (0.0, -0.38, 0.22), (0.08, -0.34, 1.00), 0.045, "metal")
    for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
        H.beam("wind_vane_blade", (0.08, -0.34, 0.96), (0.08 + 0.26 * math.cos(angle), -0.34, 0.96 + 0.26 * math.sin(angle)), 0.035, "brass")
    for i in range(3):
        H.beam("torn_wind_ribbon", (-0.58 + i * 0.58, -0.06, 0.72 - i * 0.08), (-0.38 + i * 0.58, -0.10, 0.64 - i * 0.08), 0.026, "amber")
    fallen_stones(9, 5)


def ore_obelisk():
    base()
    rough_rock("ore_outcrop", (-0.56, -0.38, 0.22), (0.50, 0.38, 0.26), "stone_dark", 10)
    rough_rock("ore_outcrop", (0.58, -0.48, 0.18), (0.38, 0.30, 0.22), "stone_dark", 11)
    H.box("cracked_obelisk_base", (0.06, 0.18, 0.18), (0.54, 0.46, 0.30), "stone", 0.035)
    H.box("leaning_obelisk", (0.10, 0.22, 0.86), (0.32, 0.28, 1.22), "stone_light", 0.035, rotation=(0.22, 0.0, -0.10))
    H.box("crystal_vein", (-0.02, 0.06, 0.96), (0.08, 0.05, 0.54), "crystal", 0.012, rotation=(0.22, 0.0, -0.10))
    for i, (x, y) in enumerate(((-0.72, -0.22), (0.72, -0.12), (0.38, 0.62))):
        H.box("small_crystal", (x, y, 0.21), (0.11, 0.09, 0.30), "crystal", 0.015, rotation=(0.12, 0.0, i * 0.4))
    fallen_stones(10, 4)


def rift_watch():
    base()
    broken_wall(-0.72, 0.24, 0.36, 0.94, 4, "stone_dark")
    broken_wall(0.68, 0.24, 0.36, 0.82, 3, "stone_dark")
    H.box("rift_crack", (0.0, -0.46, 0.08), (1.34, 0.16, 0.05), "danger", 0.008, rotation=(0, 0, 0.20))
    H.box("rift_crack_branch", (-0.42, -0.30, 0.09), (0.55, 0.11, 0.05), "danger", 0.008, rotation=(0, 0, -0.55))
    for x in (-0.52, 0.52):
        H.box("watch_slab", (x, -0.02, 0.46), (0.24, 0.22, 0.76), "stone_dark", 0.025, rotation=(0.0, 0.0, x * 0.16))
        H.box("warning_glyph", (x, -0.15, 0.54), (0.13, 0.030, 0.22), "danger", 0.006, rotation=(0.0, 0.0, x * 0.16))
    fallen_stones(11, 7)


def river_lighthouse():
    base()
    H.box("water_edge", (0.34, -0.84, 0.06), (1.72, 0.52, 0.09), "water", 0.02)
    for x in (-0.64, -0.24, 0.16):
        H.beam("broken_pier_pile", (x, -1.08, 0.04), (x + 0.02, -1.08, 0.46), 0.06, "wood_dark")
    cylinder("lighthouse_lower", (-0.30, 0.12, 0.44), 0.31, 0.72, "stone_light")
    cylinder("lighthouse_upper_broken", (-0.26, 0.12, 1.02), 0.22, 0.42, "stone")
    H.box("lamp_housing", (-0.22, 0.02, 1.30), (0.30, 0.24, 0.22), "glass", 0.02, rotation=(0.0, 0.0, 0.10))
    H.beam("fallen_lamp_frame", (0.16, -0.12, 0.24), (0.78, -0.42, 0.58), 0.05, "brass")
    broken_wall(0.72, 0.22, 0.32, 0.66, 3)
    fallen_stones(12, 5)


BUILDERS = {
    "ruins_town_square": town_square,
    "ruins_archive": archive,
    "ruins_mint": mint,
    "ruins_storage": storage,
    "ruins_greenhouse": greenhouse,
    "ruins_water_station": water_station,
    "ruins_bastion": bastion,
    "ruins_mechanic_workshop": mechanic_workshop,
    "ruins_wind_shrine": wind_shrine,
    "ruins_ore_obelisk": ore_obelisk,
    "ruins_rift_watch": rift_watch,
    "ruins_river_lighthouse": river_lighthouse,
}


def prepare():
    global SCENE
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    SCENE = bpy.data.scenes.new("Real_City_Ruins_Terrain")
    bpy.context.window.scene = SCENE
    palette()
    H.setup_camera(SCENE)
    SCENE.render.resolution_x = 512
    SCENE.render.resolution_y = 512
    SCENE.camera.data.ortho_scale = 3.6 * math.sqrt(2) * 512 / 480
    SCENE.camera.data.shift_y = 0
    bpy.context.view_layer.update()
    initial = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y
    SCENE.camera.data.shift_y = 0.1
    delta = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y - initial
    SCENE.camera.data.shift_y = ((1 - 320 / 512) - initial) * 0.1 / delta
    for name, _label in VARIANTS:
        collection = bpy.data.collections.new("terrain_tile_" + name)
        SCENE.collection.children.link(collection)
        COLLECTIONS[name] = collection
        H.COL = collection
        H.PREFIX = "SM_terrain_" + name
        BUILDERS[name]()
        H.clean_meshes(collection)
    print("Prepared", len(VARIANTS), "ruins terrain variants")


def show(name):
    bpy.context.window.scene = SCENE
    for key, collection in COLLECTIONS.items():
        collection.hide_render = key != name
        collection.hide_viewport = key != name
    bpy.context.view_layer.update()
    for obj in SCENE.objects:
        obj.select_set(False)
    for obj in COLLECTIONS[name].all_objects:
        obj.select_set(True)


def export_tile(name, label):
    show(name)
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
        assert all(edge.is_manifold for edge in bm.edges), obj.name
        bm.free()
        assert all(abs(vertex.co.x) <= 1.801 and abs(vertex.co.y) <= 1.801 for vertex in obj.data.vertices), obj.name
    assert triangles < 8000, (name, triangles)
    for target in (VARIANT_DIR, OUT_DIR):
        bpy.ops.export_scene.gltf(filepath=str(target / (name + ".glb")), export_format="GLB", use_selection=True, use_active_scene=True)
    SCENE.render.filepath = str(VARIANT_DIR / (name + ".png"))
    bpy.ops.render.render(write_still=True)
    (OUT_DIR / (name + ".png")).write_bytes((VARIANT_DIR / (name + ".png")).read_bytes())
    REPORT[name] = {
        "label": label,
        "triangles": triangles,
        "objects": objects,
        "png": name + ".png",
        "glb": name + ".glb",
    }
    print("Exported", name, triangles)


def roundtrip():
    previous = bpy.context.scene
    qa = bpy.data.scenes.new("ruins_variants_export_qa")
    bpy.context.window.scene = qa
    results = []
    try:
        for name, _label in VARIANTS:
            bpy.ops.import_scene.gltf(filepath=str(VARIANT_DIR / (name + ".glb")))
            triangles = 0
            failures = 0
            for obj in list(qa.objects):
                if obj.type == "MESH":
                    obj.data.calc_loop_triangles()
                    triangles += len(obj.data.loop_triangles)
                    bm = bmesh.new()
                    bm.from_mesh(obj.data)
                    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
                    if not all(edge.is_manifold for edge in bm.edges):
                        failures += 1
                    bm.free()
                bpy.data.objects.remove(obj, do_unlink=True)
            assert triangles == REPORT[name]["triangles"], name
            assert failures == 0, name
            results.append({"terrain": name, "triangles": triangles, "nonmanifold_edges": 0})
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa)
    (VARIANT_DIR / "roundtrip-validation.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))


def finish():
    show("ruins_town_square")
    bpy.data.libraries.write(str(VARIANT_DIR / "ruins_variants.blend"), {SCENE}, fake_user=True)
    manifest = {
        "style": "Aeolian bright fantasy stylized mid-poly",
        "size": [512, 512],
        "footprint": 3.6,
        "footprint_pixels": 480,
        "anchor": [256, 320],
        "camera_elevation": 30,
        "variants": REPORT,
        "notes": "Root PNG/GLB copies are also written to frontend/public/assets/terrain/tiles/ for terrain runtime use.",
    }
    (VARIANT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    (OUT_DIR / "ruins_variants_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    roundtrip()
    print("Saved ruins terrain variants")


if __name__ == "__main__":
    prepare()
    for variant_name, variant_label in VARIANTS:
        export_tile(variant_name, variant_label)
    finish()
