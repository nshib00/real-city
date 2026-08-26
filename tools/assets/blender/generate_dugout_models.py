import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "src" / "assets" / "buildings" / "housing" / "dugout"
BLEND_PATH = OUT_DIR / "dugout_levels.blend"
GLB_PATH = OUT_DIR / "dugout_levels.glb"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def mat(name, color, roughness=0.7):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return material


MATS = {}


def make_materials():
    global MATS
    MATS = {
        "grass_bright": mat("grass_bright", (0.38, 0.75, 0.28, 1)),
        "grass_dark": mat("grass_dark", (0.19, 0.48, 0.18, 1)),
        "earth_warm": mat("earth_warm", (0.48, 0.31, 0.18, 1)),
        "earth_dark": mat("earth_dark", (0.28, 0.18, 0.12, 1)),
        "wood_pale": mat("wood_pale", (0.72, 0.48, 0.26, 1)),
        "wood_dark": mat("wood_dark", (0.39, 0.22, 0.11, 1)),
        "stone_light": mat("stone_light", (0.58, 0.58, 0.54, 1)),
        "stone_dark": mat("stone_dark", (0.36, 0.36, 0.34, 1)),
        "moss": mat("moss", (0.22, 0.54, 0.22, 1)),
        "warm_light": mat("warm_light", (1.0, 0.66, 0.25, 1), 0.35),
        "windleaf_green": mat("windleaf_green", (0.45, 0.86, 0.52, 1)),
    }


def link_to(collection, obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def cube(name, collection, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return link_to(collection, obj)


def cylinder(name, collection, loc, radius, depth, material, vertices=12, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def sphere(name, collection, loc, scale, material, segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return link_to(collection, obj)


def cone(name, collection, loc, radius1, radius2, depth, material, vertices=7, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def add_base(collection):
    cube("dugout_tile_base", collection, (0, 0, -0.035), (3.6, 3.6, 0.07), MATS["grass_bright"])
    cube("dugout_trampled_path", collection, (0, -1.03, 0.006), (0.86, 1.05, 0.026), MATS["earth_warm"])


def add_mound(collection, level):
    width = 1.55 + level * 0.17
    depth = 1.28 + level * 0.14
    height = 0.44 + level * 0.045
    sphere("dugout_earth_mound", collection, (0, 0.15, 0.24), (width / 2, depth / 2, height), MATS["earth_warm"])
    sphere("dugout_turf_roof", collection, (0, 0.18, 0.37 + level * 0.018), (width / 2.08, depth / 2.1, height * 0.54), MATS["grass_dark"])


def add_door(collection, level):
    door_w = 0.36 + level * 0.035
    door_h = 0.46 + level * 0.035
    cube("dugout_door", collection, (0, -0.53, 0.28), (door_w, 0.08, door_h), MATS["wood_dark"])
    cube("dugout_door_frame_top", collection, (0, -0.59, 0.54 + level * 0.03), (door_w + 0.18, 0.12, 0.08), MATS["wood_pale"])
    cube("dugout_door_frame_left", collection, (-door_w / 2 - 0.07, -0.59, 0.31), (0.08, 0.12, door_h + 0.12), MATS["wood_pale"])
    cube("dugout_door_frame_right", collection, (door_w / 2 + 0.07, -0.59, 0.31), (0.08, 0.12, door_h + 0.12), MATS["wood_pale"])
    if level >= 4:
        cube("dugout_warm_window", collection, (0.48, -0.51, 0.38), (0.18, 0.055, 0.16), MATS["warm_light"])


def add_chimney(collection, level):
    x = -0.42 - level * 0.025
    z = 0.64 + level * 0.055
    cylinder("dugout_chimney_stack", collection, (x, 0.2, z), 0.085 + level * 0.008, 0.42 + level * 0.09, MATS["stone_dark"], vertices=9)
    cube("dugout_chimney_cap", collection, (x, 0.2, z + 0.25 + level * 0.05), (0.26, 0.22, 0.055), MATS["stone_light"])
    if level >= 2:
        for i in range(2):
            sphere(f"dugout_smoke_puff_{i+1}", collection, (x + i * 0.05, 0.2, z + 0.42 + i * 0.13), (0.085 + i * 0.025, 0.085 + i * 0.025, 0.055), MATS["stone_light"], segments=12)


def add_logs(collection, level):
    count = 2 + min(level, 4)
    for i in range(count):
        x = -1.05 + (i % 3) * 0.17
        y = -0.86 - (i // 3) * 0.12
        cylinder(
            f"dugout_log_{i+1:02d}",
            collection,
            (x, y, 0.12 + (i // 3) * 0.08),
            0.055,
            0.42,
            MATS["wood_pale"],
            vertices=10,
            rot=(0, math.radians(90), 0),
        )


def add_stones(collection, level):
    for i in range(3 + level):
        angle = -0.85 + i * 0.28
        x = math.sin(angle) * (0.75 + level * 0.05)
        y = -0.43 + math.cos(angle) * 0.18
        sphere(f"dugout_entry_stone_{i+1:02d}", collection, (x, y, 0.06), (0.08, 0.06, 0.04), MATS["stone_light"], segments=10)


def add_supports(collection, level):
    if level < 3:
        return
    for side, x in [("left", -0.78), ("right", 0.78)]:
        cylinder(
            f"dugout_side_support_{side}",
            collection,
            (x, -0.27, 0.33),
            0.045,
            0.7,
            MATS["wood_pale"],
            vertices=8,
            rot=(math.radians(23 if x < 0 else -23), 0, 0),
        )
    if level >= 4:
        cube("dugout_plank_awning", collection, (0, -0.76, 0.71), (0.92, 0.54, 0.09), MATS["wood_pale"])
        cube("dugout_front_plank_face", collection, (0, -0.61, 0.42), (1.14, 0.055, 0.2), MATS["wood_pale"])
    if level >= 5:
        cube("dugout_reinforced_facade", collection, (0, -0.64, 0.28), (1.28, 0.06, 0.28), MATS["wood_pale"])
        cube("dugout_stone_threshold", collection, (0, -0.81, 0.07), (0.82, 0.2, 0.08), MATS["stone_light"])


def add_fence_and_props(collection, level):
    if level >= 3:
        for i, x in enumerate([-0.95, -0.55, 0.55, 0.95]):
            cube(f"dugout_fence_post_{i+1:02d}", collection, (x, 0.93, 0.18), (0.07, 0.07, 0.35), MATS["wood_pale"])
        cube("dugout_fence_rail", collection, (0, 0.93, 0.28), (2.0, 0.055, 0.06), MATS["wood_pale"])
    if level >= 4:
        cube("dugout_tool_crate", collection, (0.92, -0.8, 0.12), (0.28, 0.22, 0.18), MATS["wood_dark"])
        cylinder("dugout_rope_coil", collection, (1.12, -0.48, 0.06), 0.13, 0.045, MATS["wood_pale"], vertices=18)
    if level >= 5:
        cube("dugout_small_bench", collection, (-0.72, -0.55, 0.16), (0.48, 0.15, 0.09), MATS["wood_pale"])


def add_grass_and_windleaves(collection, level):
    for i in range(5 + level * 2):
        angle = i * 2.37
        radius = 1.0 + (i % 3) * 0.18
        x = math.sin(angle) * radius
        y = math.cos(angle) * radius * 0.75 + 0.1
        cone(f"dugout_grass_tuft_{i+1:02d}", collection, (x, y, 0.11), 0.055, 0.0, 0.22, MATS["moss"], vertices=5)
    if level >= 3:
        for i in range(level - 1):
            angle = i * 1.8 + 0.35
            x = math.sin(angle) * 0.95
            y = math.cos(angle) * 0.72 + 0.24
            cone(f"dugout_windleaf_{i+1:02d}", collection, (x, y, 0.18), 0.035, 0.01, 0.32, MATS["windleaf_green"], vertices=6, rot=(math.radians(8), 0, angle))


def add_level(level, x_offset):
    collection = bpy.data.collections.new(f"dugout_l{level:02d}_active")
    bpy.context.scene.collection.children.link(collection)
    empty = bpy.data.objects.new(f"dugout_l{level:02d}_origin", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.35
    empty.location = (x_offset, 0, 0)
    collection.objects.link(empty)

    local = bpy.data.collections.new(f"dugout_l{level:02d}_parts")
    collection.children.link(local)

    def move_recent(obj):
        obj.location.x += x_offset
        return obj

    before = set(bpy.data.objects)
    add_base(local)
    add_mound(local, level)
    add_door(local, level)
    add_chimney(local, level)
    add_logs(local, level)
    add_stones(local, level)
    add_supports(local, level)
    add_fence_and_props(local, level)
    add_grass_and_windleaves(local, level)

    for obj in set(bpy.data.objects) - before:
        if obj.type == "MESH":
            obj.location.x += x_offset


def add_lighting_and_camera():
    bpy.ops.object.light_add(type="SUN", location=(0, -6, 8))
    sun = bpy.context.object
    sun.name = "preview_sun"
    sun.data.energy = 2.2
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))

    bpy.ops.object.camera_add(location=(0, -10, 7), rotation=(math.radians(60), 0, 0))
    camera = bpy.context.object
    camera.name = "preview_isometric_camera"
    camera.data.lens = 55
    bpy.context.scene.camera = camera


def write_asset_notes():
    note = bpy.data.texts.new("dugout_asset_notes")
    note.write(
        "Real City dugout active models, levels 1-5. "
        "Source docs: docs/buildings/houses/dugout.md. "
        "Footprint: 1x1 tile. Origin empties mark tile base centers. "
        "Level progression: earth shelter -> reinforced turf dugout -> pre-wood-house half-dugout."
    )


def export_glb():
    try:
        bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB")
        return True
    except Exception as exc:
        print(f"GLB export skipped: {exc}")
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    make_materials()
    for level, x_offset in enumerate([-8, -4, 0, 4, 8], start=1):
        add_level(level, x_offset)
    add_lighting_and_camera()
    write_asset_notes()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    export_glb()
    print(f"Saved {BLEND_PATH}")
    print(f"Exported {GLB_PATH}")


if __name__ == "__main__":
    main()
