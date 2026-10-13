"""Blender MCP: generate(), validate_roundtrip().

Builds the Ground Road modular kit for Real City.
"""

import json
import math
import random
import importlib.util
import os
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "roads" / "ground_road"
GRASS_TEXTURE_PATH = ROOT / "frontend" / "public" / "assets" / "terrain" / "tiles" / "grass.png"
BLENDER_ROOT = r"\\wsl.localhost\Debian\home\nshib\projects\real-city"
SIZE = 512
FOOTPRINT = 3.6
ROAD_WIDTH = FOOTPRINT * 0.90
WAGON_TRACK_OFFSET = 0.58
STATES = ("active", "construction", "damaged", "ruined")
SHAPES = {
    "single": (),
    "end_n": ("n",),
    "end_e": ("e",),
    "end_s": ("s",),
    "end_w": ("w",),
    "straight_ns": ("n", "s"),
    "straight_ew": ("e", "w"),
    "corner_ne": ("n", "e"),
    "corner_es": ("e", "s"),
    "corner_sw": ("s", "w"),
    "corner_wn": ("w", "n"),
    "t_nes": ("n", "e", "s"),
    "t_esw": ("e", "s", "w"),
    "t_swn": ("s", "w", "n"),
    "t_wne": ("w", "n", "e"),
    "cross": ("n", "e", "s", "w"),
}

MATS = {}
COLLECTIONS = {}
REPORT = {}
SCENE = None


def blender_path(path: Path) -> str:
    raw = str(path).replace("/", "\\")
    root = str(ROOT).replace("/", "\\")
    if raw.lower().startswith(root.lower()):
        relative = raw[len(root) :].lstrip("\\")
        return BLENDER_ROOT + "\\" + relative
    return raw


def material(role, color, roughness=0.82):
    mat = bpy.data.materials.new("MAT_ground_road_" + role)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = roughness
    MATS[role] = mat
    return mat


def palette():
    for role, color in {
        "earth_side": (0.30, 0.20, 0.105),
        "grass": (0.26, 0.48, 0.08),
        "grass_light": (0.37, 0.59, 0.13),
        "clay": (0.72, 0.34, 0.20),
        "clay_light": (0.94, 0.50, 0.30),
        "clay_fresh": (0.80, 0.42, 0.24),
        "rut": (0.43, 0.20, 0.12),
        "dry_edge": (0.75, 0.48, 0.25),
        "pebble": (0.58, 0.63, 0.59),
        "stake": (0.49, 0.27, 0.10),
        "string": (0.76, 0.61, 0.33),
        "shadow_mud": (0.27, 0.14, 0.09),
    }.items():
        material(role, color)
    for role in ("grass", "grass_light"):
        MATS[role]["terrain_source"] = "frontend/public/assets/terrain/tiles/grass.png"


def link_object(obj, collection, role):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(MATS[role])
    return obj


def box(collection, name, pos, size, role, bevel=0.015, rotation=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vertex in bm.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.22), segments=1, affect="EDGES")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new("SM_ground_road_" + name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = rotation
    mesh.materials.append(MATS[role])
    return obj


def cylinder(collection, name, pos, radius, depth, role, vertices=14, scale=(1, 1, 1), rotation=(0, 0, 0)):
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
    for vertex in bm.verts:
        vertex.co.x *= scale[0]
        vertex.co.y *= scale[1]
        vertex.co.z *= scale[2]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new("SM_ground_road_" + name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = rotation
    mesh.materials.append(MATS[role])
    return obj


def beam(collection, name, a, b, width, role):
    delta = Vector(b) - Vector(a)
    obj = box(collection, name, (Vector(a) + Vector(b)) / 2, (width, width, delta.length), role, bevel=width * 0.18)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def base_tile(collection):
    box(collection, "earth_tile", (0, 0, -0.015), (FOOTPRINT, FOOTPRINT, 0.03), "grass", bevel=0.0)
    box(collection, "grass_tile", (0, 0, 0.004), (FOOTPRINT * 0.99, FOOTPRINT * 0.99, 0.008), "grass", bevel=0.0)
    for i, (x, y) in enumerate(((-1.28, 1.05), (1.26, 1.18), (-1.10, -1.16), (1.16, -0.98))):
        tuft(collection, x, y, 0.75 + 0.1 * (i % 2))


def tuft(collection, x, y, scale=1.0):
    for index, offset in enumerate((-0.045, 0.0, 0.045)):
        beam(
            collection,
            "grass_tuft",
            (x + offset, y, 0.035),
            (x + offset * 1.5 + 0.035 * (index - 1), y + 0.05, 0.15 * scale),
            0.018,
            "grass_light",
        )


def strip_for_dir(collection, direction, length, width, role, z, suffix):
    half = length / 2
    if direction == "n":
        box(collection, "road_" + suffix + "_n", (0, half, z), (width, length, 0.030), role, bevel=0.050)
    elif direction == "s":
        box(collection, "road_" + suffix + "_s", (0, -half, z), (width, length, 0.030), role, bevel=0.050)
    elif direction == "e":
        box(collection, "road_" + suffix + "_e", (half, 0, z), (length, width, 0.030), role, bevel=0.050)
    elif direction == "w":
        box(collection, "road_" + suffix + "_w", (-half, 0, z), (length, width, 0.030), role, bevel=0.050)


def rut_for_dir(collection, direction, length, z, state, seed):
    rng = random.Random(seed)
    offsets = (-WAGON_TRACK_OFFSET, WAGON_TRACK_OFFSET)
    role = "rut" if state != "ruined" else "shadow_mud"
    if direction in ("n", "s"):
        y_center = length / 2 if direction == "n" else -length / 2
        for lane_x in offsets:
            box(collection, "wagon_rut_" + direction, (lane_x, y_center, z), (0.155, length * 0.90, 0.012), role, bevel=0.045)
            for i in range(3):
                y = (0.24 + i * 0.42 + rng.uniform(-0.045, 0.045)) * (1 if direction == "n" else -1)
                x = lane_x + rng.uniform(-0.035, 0.035)
                cylinder(collection, "wheel_imprint_" + direction, (x, y, z + 0.008), 0.070, 0.011, role, vertices=8, scale=(0.75, 1.75, 1), rotation=(0, 0, rng.uniform(-0.08, 0.08)))
            box(collection, "rut_inner_crumble_" + direction, (lane_x * 0.86, y_center, z + 0.009), (0.035, length * 0.82, 0.010), "dry_edge", bevel=0.018)
    else:
        x_center = length / 2 if direction == "e" else -length / 2
        for lane_y in offsets:
            box(collection, "wagon_rut_" + direction, (x_center, lane_y, z), (length * 0.90, 0.155, 0.012), role, bevel=0.045)
            for i in range(3):
                x = (0.24 + i * 0.42 + rng.uniform(-0.045, 0.045)) * (1 if direction == "e" else -1)
                y = lane_y + rng.uniform(-0.035, 0.035)
                cylinder(collection, "wheel_imprint_" + direction, (x, y, z + 0.008), 0.070, 0.011, role, vertices=8, scale=(1.75, 0.75, 1), rotation=(0, 0, rng.uniform(-0.08, 0.08)))
            box(collection, "rut_inner_crumble_" + direction, (x_center, lane_y * 0.86, z + 0.009), (length * 0.82, 0.035, 0.010), "dry_edge", bevel=0.018)


def clay_clumps(collection, dirs, state, seed):
    rng = random.Random(seed)
    count = {"active": 10, "construction": 16, "damaged": 14, "ruined": 18}[state]
    for index in range(count):
        if dirs:
            direction = rng.choice(dirs)
            distance = rng.uniform(0.15, 1.42)
            if direction == "n":
                x, y = rng.uniform(-0.44, 0.44), distance
            elif direction == "s":
                x, y = rng.uniform(-0.44, 0.44), -distance
            elif direction == "e":
                x, y = distance, rng.uniform(-0.44, 0.44)
            else:
                x, y = -distance, rng.uniform(-0.44, 0.44)
        else:
            x, y = rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45)
        role = rng.choice(("clay_light", "dry_edge", "pebble"))
        cylinder(
            collection,
            "road_detail",
            (x, y, 0.055 + rng.uniform(0, 0.014)),
            rng.uniform(0.018, 0.050),
            rng.uniform(0.010, 0.030),
            role,
            vertices=8,
            scale=(rng.uniform(0.7, 1.6), rng.uniform(0.45, 1.1), 1),
            rotation=(0, 0, rng.random() * math.tau),
        )


def construction_details(collection, dirs, seed):
    rng = random.Random(seed)
    endpoints = endpoint_positions(dirs or ("n",))
    for index, (x, y) in enumerate(endpoints[:4]):
        sign_x = 1 if x >= 0 else -1
        sign_y = 1 if y >= 0 else -1
        beam(collection, "survey_stake", (x * 0.82, y * 0.82, 0.045), (x * 0.82, y * 0.82, 0.34), 0.035, "stake")
        box(collection, "clay_pile", (x * 0.60 + 0.05 * sign_y, y * 0.60 - 0.05 * sign_x, 0.080), (0.22, 0.15, 0.09), "clay_fresh", bevel=0.035, rotation=(0, 0, rng.random() * 0.8))
        if index % 2 == 0:
            beam(collection, "layout_string", (0.0, 0.0, 0.16), (x * 0.86, y * 0.86, 0.16), 0.012, "string")


def endpoint_positions(dirs):
    positions = []
    for direction in dirs:
        if direction == "n":
            positions.append((0, 1.52))
        elif direction == "s":
            positions.append((0, -1.52))
        elif direction == "e":
            positions.append((1.52, 0))
        elif direction == "w":
            positions.append((-1.52, 0))
    return positions


def damaged_details(collection, dirs, seed, ruined=False):
    rng = random.Random(seed)
    for index in range(5 if not ruined else 7):
        if dirs:
            direction = rng.choice(dirs)
            distance = rng.uniform(0.05, 1.35)
            if direction == "n":
                x, y = rng.uniform(-0.32, 0.32), distance
            elif direction == "s":
                x, y = rng.uniform(-0.32, 0.32), -distance
            elif direction == "e":
                x, y = distance, rng.uniform(-0.32, 0.32)
            else:
                x, y = -distance, rng.uniform(-0.32, 0.32)
        else:
            x, y = rng.uniform(-0.40, 0.40), rng.uniform(-0.40, 0.40)
        cylinder(collection, "pothole", (x, y, 0.073), rng.uniform(0.13, 0.22), 0.012, "shadow_mud", vertices=13, scale=(rng.uniform(1.0, 1.8), rng.uniform(0.55, 1.0), 1), rotation=(0, 0, rng.random() * math.tau))
        if ruined or index % 2 == 0:
            tuft(collection, x + rng.uniform(-0.12, 0.12), y + rng.uniform(-0.12, 0.12), rng.uniform(0.55, 0.95))


def road_surface(collection, shape, state):
    dirs = SHAPES[shape]
    width = ROAD_WIDTH
    role = {"active": "clay", "construction": "clay_fresh", "damaged": "clay", "ruined": "dry_edge"}[state]
    z = 0.050
    center_size = width if dirs else 1.15
    box(collection, "road_center", (0, 0, z), (center_size, center_size, 0.032), role, bevel=0.070)
    segment_length = {"active": 1.80, "construction": 1.55, "damaged": 1.72, "ruined": 1.20}[state]
    for direction in dirs:
        strip_for_dir(collection, direction, segment_length, width, role, z, state)
        if state in ("active", "damaged", "ruined"):
            rut_for_dir(collection, direction, segment_length, z + 0.021, state, hash((shape, state, direction)) & 0xFFFF)
    if len(dirs) >= 3:
        cylinder(collection, "worn_crossing_center", (0, 0, z + 0.027), width * 0.56, 0.012, "rut", vertices=18, scale=(1.25, 0.86, 1), rotation=(0, 0, math.pi / 4))
    clay_clumps(collection, dirs, state, hash((shape, state, "clumps")) & 0xFFFF)
    if state == "construction":
        construction_details(collection, dirs, hash((shape, state, "construction")) & 0xFFFF)
    if state in ("damaged", "ruined"):
        damaged_details(collection, dirs, hash((shape, state, "damage")) & 0xFFFF, ruined=state == "ruined")


def build_asset(shape, state):
    collection_name = f"ground_road_{shape}_{state}"
    collection = bpy.data.collections.new(collection_name)
    SCENE.collection.children.link(collection)
    COLLECTIONS[collection_name] = collection
    base_tile(collection)
    road_surface(collection, shape, state)
    clean_collection(collection)
    return collection


def clean_collection(collection):
    for obj in collection.all_objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            obj.data.update()
            obj.select_set(False)


def setup_scene(output_dir):
    global SCENE, OUT_DIR
    OUT_DIR = Path(output_dir)
    os.makedirs(blender_path(OUT_DIR), exist_ok=True)
    SCENE = bpy.data.scenes.new("Real_City_Ground_Road")
    bpy.context.window.scene = SCENE
    palette()
    spec = importlib.util.spec_from_file_location("terrain_camera", Path(__file__).with_name("regenerate_early_housing.py"))
    terrain_camera = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(terrain_camera)
    terrain_camera.setup_camera(SCENE)
    SCENE.render.resolution_x = SIZE
    SCENE.render.resolution_y = SIZE
    SCENE.camera.data.ortho_scale = FOOTPRINT * math.sqrt(2) * SIZE / 480
    SCENE.camera.data.shift_y = 0
    bpy.context.view_layer.update()
    initial = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y
    SCENE.camera.data.shift_y = 0.1
    delta = world_to_camera_view(SCENE, SCENE.camera, Vector((0, 0, 0))).y - initial
    SCENE.camera.data.shift_y = ((1 - 320 / SIZE) - initial) * 0.1 / delta
    SCENE.render.film_transparent = True
    if "PNG" in [item.identifier for item in SCENE.render.image_settings.bl_rna.properties["file_format"].enum_items]:
        SCENE.render.image_settings.file_format = "PNG"
    if "RGBA" in [item.identifier for item in SCENE.render.image_settings.bl_rna.properties["color_mode"].enum_items]:
        SCENE.render.image_settings.color_mode = "RGBA"
    return SCENE


def show_only(collection_name):
    for name, collection in COLLECTIONS.items():
        hidden = name != collection_name
        collection.hide_viewport = hidden
        collection.hide_render = hidden
    for obj in SCENE.objects:
        obj.select_set(False)
    for obj in COLLECTIONS[collection_name].all_objects:
        obj.select_set(True)
    bpy.context.view_layer.update()


def export_asset(shape, state):
    name = f"ground_road_{shape}_{state}"
    show_only(name)
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
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        assert all(edge.is_manifold for edge in bm.edges), obj.name
        bm.free()
    assert triangles < 4000, (name, triangles)
    bpy.ops.export_scene.gltf(
        filepath=blender_path(OUT_DIR / f"{name}.glb"),
        export_format="GLB",
        use_selection=True,
        use_active_scene=True,
    )
    SCENE.render.filepath = blender_path(OUT_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    REPORT[name] = {
        "shape": shape,
        "state": state,
        "triangles": triangles,
        "objects": objects,
        "png": f"{name}.png",
        "glb": f"{name}.glb",
    }


def save_manifest():
    show_only("ground_road_cross_active")
    bpy.data.libraries.write(blender_path(OUT_DIR / "ground_road.blend"), {SCENE}, fake_user=True)
    manifest = {
        "id": "ground_road",
        "building_type": "road",
        "display_name": "Грунтовая дорога",
        "style": "Aeolian bright fantasy stylized mid-poly light clay modular road kit",
        "size": [SIZE, SIZE],
        "footprint": FOOTPRINT,
        "anchor": [256, 320],
        "shapes": list(SHAPES.keys()),
        "states": list(STATES),
        "materials": {
            "coins": "не моделируются как нематериальная стоимость",
            "clay": "светло-коричневое глиняное дорожное покрытие цвета игрового ресурса глины, широкая полоса 90% тайла и колея от повозок",
        },
        "assets": REPORT,
    }
    Path(blender_path(OUT_DIR / "manifest.json")).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def generate(output_dir=None):
    setup_scene(output_dir or OUT_DIR)
    for shape in SHAPES:
        for state in STATES:
            build_asset(shape, state)
    for shape in SHAPES:
        for state in STATES:
            export_asset(shape, state)
    save_manifest()
    print(f"Generated {len(REPORT)} ground road assets into {OUT_DIR}")


def validate_roundtrip(output_dir=None):
    out_dir = Path(output_dir or OUT_DIR)
    previous = bpy.context.scene
    qa_scene = bpy.data.scenes.new("ground_road_roundtrip_qa")
    bpy.context.window.scene = qa_scene
    results = []
    try:
        manifest = json.loads(Path(blender_path(out_dir / "manifest.json")).read_text(encoding="utf-8"))
        for name, info in manifest["assets"].items():
            bpy.ops.import_scene.gltf(filepath=blender_path(out_dir / info["glb"]))
            triangles = 0
            for obj in list(qa_scene.objects):
                if obj.type == "MESH":
                    obj.data.calc_loop_triangles()
                    triangles += len(obj.data.loop_triangles)
                    bm = bmesh.new()
                    bm.from_mesh(obj.data)
                    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
                    assert all(edge.is_manifold for edge in bm.edges), (name, obj.name)
                    bm.free()
                bpy.data.objects.remove(obj, do_unlink=True)
            assert triangles == info["triangles"], (name, triangles, info["triangles"])
            results.append({"asset": name, "triangles": triangles, "nonmanifold_edges": 0})
    finally:
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(qa_scene)
    Path(blender_path(out_dir / "roundtrip-validation.json")).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Roundtrip validated {len(results)} ground road assets")


if __name__ == "__main__":
    generate()
    validate_roundtrip()
