import importlib.util
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "src" / "assets" / "buildings" / "center" / "town_hall"
BLEND_PATH = OUT_DIR / "town_hall_levels.blend"
GLB_PATH = OUT_DIR / "town_hall_levels.glb"
STATE_GLB_TEMPLATE = "town_hall_l{level:02d}_{state}.glb"
STATES = ("active", "construction", "damaged")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color, roughness=0.72, metallic=0.0, alpha=1.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (color[0], color[1], color[2], alpha))
    set_input(bsdf, "Alpha", alpha)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Metallic", metallic)
    if emission is not None:
        set_input(bsdf, "Emission Color", emission)
        set_input(bsdf, "Emission Strength", emission_strength)
    if alpha < 1:
        material.blend_method = "BLEND"
        material.use_screen_refraction = True
    return material


MATS = {}


def make_materials():
    global MATS
    MATS = {
        "tile_grass": mat("tile_grass", (0.49, 0.78, 0.35)),
        "plaza_dirt": mat("plaza_dirt", (0.72, 0.52, 0.31)),
        "plaza_stone": mat("plaza_stone", (0.7, 0.7, 0.66)),
        "wood_log": mat("wood_log", (0.62, 0.36, 0.16)),
        "wood_pale": mat("wood_pale", (0.88, 0.66, 0.38)),
        "wood_trim": mat("wood_trim", (0.96, 0.78, 0.46)),
        "stone_light": mat("stone_light", (0.72, 0.72, 0.68)),
        "stone_shadow": mat("stone_shadow", (0.48, 0.5, 0.48)),
        "brick_warm": mat("brick_warm", (0.73, 0.32, 0.22)),
        "roof_leaf": mat("roof_leaf", (0.33, 0.65, 0.28)),
        "roof_teal": mat("roof_teal", (0.08, 0.56, 0.62)),
        "roof_red": mat("roof_red", (0.82, 0.18, 0.12)),
        "roof_gold": mat("roof_gold", (0.92, 0.58, 0.12)),
        "window_light": mat("window_light", (1.0, 0.76, 0.34), 0.28, emission=(1.0, 0.55, 0.16, 1), emission_strength=0.55),
        "glass_soft": mat("glass_soft", (0.82, 0.94, 1.0), 0.28, alpha=0.72, emission=(0.55, 0.72, 1.0, 1), emission_strength=0.1),
        "banner_red": mat("banner_red", (0.9, 0.13, 0.1)),
        "banner_blue": mat("banner_blue", (0.14, 0.36, 0.78)),
        "amethyst_small": mat("amethyst_small", (0.56, 0.32, 0.86), 0.34, alpha=0.88, emission=(0.42, 0.22, 0.76, 1), emission_strength=0.22),
        "construction_plank": mat("construction_plank", (0.86, 0.62, 0.34)),
        "rope": mat("rope", (0.73, 0.56, 0.34)),
        "dust": mat("dust", (0.76, 0.67, 0.53), 0.94, alpha=0.48),
        "damage_char": mat("damage_char", (0.1, 0.08, 0.06)),
        "damage_crack": mat("damage_crack", (0.04, 0.035, 0.03)),
        "smoke_soft": mat("smoke_soft", (0.7, 0.74, 0.72), 0.95, alpha=0.58),
    }


def link_to(collection, obj):
    for item in list(obj.users_collection):
        item.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def cube(name, collection, loc, scale, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
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


def sphere(name, collection, loc, scale, material, segments=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return link_to(collection, obj)


def cone(name, collection, loc, radius1, radius2, depth, material, vertices=4, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def flag(name, collection, loc, width, height, material):
    verts = [(0, 0, 0), (width, 0, height * 0.34), (0, 0, height)]
    faces = [(0, 1, 2)]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def gable_roof(name, collection, loc, size, material):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (0, -y, height), (0, y, height)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def roof_mat(level):
    if level <= 2:
        return MATS["roof_leaf"]
    if level <= 5:
        return MATS["roof_teal"]
    if level <= 8:
        return MATS["roof_red"]
    return MATS["roof_gold"]


def wall_mat(level):
    if level <= 2:
        return MATS["wood_log"]
    if level <= 6:
        return MATS["wood_pale"]
    if level <= 8:
        return MATS["stone_light"]
    return MATS["brick_warm"]


def trim_mat(level):
    if level <= 6:
        return MATS["wood_trim"]
    return MATS["stone_shadow"]


def add_base(collection, level):
    cube("town_hall_tile_base", collection, (0, 0, -0.045), (6.8, 6.8, 0.09), MATS["tile_grass"])
    plaza = MATS["plaza_dirt"] if level < 7 else MATS["plaza_stone"]
    cube("town_hall_front_plaza", collection, (0, -1.82, 0.012), (2.5 + level * 0.08, 1.22, 0.035), plaza)
    if level >= 5:
        cube("town_hall_plaza_step", collection, (0, -2.42, 0.045), (2.1, 0.28, 0.07), MATS["stone_light"])
    if level >= 8:
        for i, x in enumerate([-1.05, -0.35, 0.35, 1.05]):
            cube(f"town_hall_plaza_tile_{i+1:02d}", collection, (x, -1.82, 0.05), (0.42, 0.42, 0.026), MATS["stone_light"])


def add_main_body(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    width = 1.55 + min(level, 7) * 0.18
    depth = 1.3 + min(level, 6) * 0.13
    body_h = 0.58 + min(level, 8) * 0.08
    foundation_h = 0.12 + min(level, 6) * 0.026
    if level >= 7:
        foundation_h += 0.05
    cube("town_hall_foundation" + suffix, collection, (0, 0, foundation_h / 2), (width + 0.36, depth + 0.3, foundation_h), MATS["stone_light" if level >= 5 else "plaza_dirt"])
    cube("town_hall_main_body" + suffix, collection, (0, 0, foundation_h + body_h / 2), (width, depth, body_h), wall_mat(level))
    cube("town_hall_front_panel" + suffix, collection, (0, -depth / 2 - 0.052, foundation_h + body_h * 0.56), (width * 0.68, 0.042, body_h * 0.56), MATS["wood_pale" if level <= 8 else "stone_light"])
    for side, x in (("left", -width / 2 - 0.04), ("right", width / 2 + 0.04)):
        cube(f"town_hall_corner_post_{side}{suffix}", collection, (x, 0, foundation_h + body_h / 2), (0.09, depth + 0.1, body_h + 0.06), trim_mat(level))
    if level >= 3:
        annex_w = 0.62 + level * 0.035
        cube("town_hall_side_annex_left" + suffix, collection, (-width / 2 - annex_w / 2 + 0.04, 0.06, foundation_h + 0.36), (annex_w, depth * 0.72, 0.72), wall_mat(level))
    if level >= 5:
        annex_w = 0.68 + level * 0.03
        cube("town_hall_side_annex_right" + suffix, collection, (width / 2 + annex_w / 2 - 0.04, 0.03, foundation_h + 0.38), (annex_w, depth * 0.78, 0.76), wall_mat(level))
    if level >= 9:
        for i, x in enumerate([-width * 0.32, width * 0.32]):
            cube(f"town_hall_brick_pier_{i+1:02d}{suffix}", collection, (x, -depth / 2 - 0.065, foundation_h + body_h * 0.52), (0.18, 0.07, body_h * 0.82), MATS["brick_warm"])


def add_roofs(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    main_z = 0.8 + min(level, 8) * 0.106
    roof = gable_roof("town_hall_main_roof" + suffix, collection, (0, 0, main_z), (2.25 + level * 0.18, 1.84 + level * 0.08, 0.38 + level * 0.025), roof_mat(level))
    if damaged:
        roof.rotation_euler[1] = math.radians(2.5)
    cube("town_hall_roof_ridge" + suffix, collection, (0, 0, main_z + 0.42 + level * 0.025), (0.09, 1.94 + level * 0.08, 0.08), trim_mat(level))
    if level >= 3:
        gable_roof("town_hall_left_annex_roof" + suffix, collection, (-1.18 - level * 0.06, 0.06, 0.84), (0.96, 1.1, 0.22), roof_mat(level))
    if level >= 5:
        gable_roof("town_hall_right_annex_roof" + suffix, collection, (1.18 + level * 0.06, 0.02, 0.9), (1.04, 1.16, 0.24), roof_mat(level))
    if damaged:
        cube("town_hall_roof_broken_patch", collection, (0.44, -0.3, main_z + 0.2), (0.46, 0.32, 0.04), MATS["damage_char"], rot=(0, 0, math.radians(12)))


def add_tower(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    lower_h = 0.92 + level * 0.13
    tower_w = 0.55 + min(level, 7) * 0.035
    z = 0.36 + lower_h / 2
    tower_material = wall_mat(level if level < 7 else max(7, level))
    cube("town_hall_central_tower" + suffix, collection, (0, -0.04, z), (tower_w, tower_w, lower_h), tower_material)
    if level >= 4:
        cube("town_hall_tower_second_tier" + suffix, collection, (0, -0.04, lower_h + 0.72), (tower_w * 0.84, tower_w * 0.84, 0.7 + level * 0.035), tower_material)
    cone("town_hall_tower_roof" + suffix, collection, (0, -0.04, lower_h + 0.9 + level * 0.06), tower_w * 0.62, tower_w * 0.18, 0.58 + level * 0.04, roof_mat(level), vertices=4, rot=(0, 0, math.radians(45)))
    cylinder("town_hall_flag_pole" + suffix, collection, (0, -0.04, lower_h + 1.34 + level * 0.09), 0.022, 0.74, MATS["wood_trim"], vertices=8)
    if not damaged:
        flag("town_hall_main_flag" + suffix, collection, (0.02, -0.04, lower_h + 1.52 + level * 0.09), 0.42, 0.3, MATS["banner_red" if level % 2 else "banner_blue"])
    if level >= 7:
        for side, x in (("left", -1.08 - level * 0.05), ("right", 1.08 + level * 0.05)):
            cube(f"town_hall_side_tower_{side}{suffix}", collection, (x, 0.06, 0.62), (0.42, 0.42, 1.08 + level * 0.04), tower_material)
            cone(f"town_hall_side_tower_roof_{side}{suffix}", collection, (x, 0.06, 1.34 + level * 0.045), 0.34, 0.08, 0.4, roof_mat(level), vertices=4, rot=(0, 0, math.radians(45)))


def add_details(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    door_mat = MATS["damage_char"] if damaged else MATS["wood_log"]
    cube("town_hall_front_door" + suffix, collection, (0, -0.84, 0.42), (0.42 + level * 0.018, 0.08, 0.58), door_mat)
    cube("town_hall_door_header" + suffix, collection, (0, -0.895, 0.73), (0.66 + level * 0.024, 0.06, 0.08), trim_mat(level))
    for i in range(3):
        cube(f"town_hall_front_step_{i+1:02d}{suffix}", collection, (0, -1.02 - i * 0.12, 0.08 - i * 0.01), (0.78 + i * 0.2, 0.13, 0.055), MATS["stone_light"])
    window_positions = [(-0.52, -0.82, 0.56), (0.52, -0.82, 0.56)]
    if level >= 4:
        window_positions.extend([(-0.22, -0.35, 1.22), (0.22, -0.35, 1.22)])
    if level >= 6:
        window_positions.extend([(-1.16, -0.56, 0.62), (1.16, -0.56, 0.62)])
    if level >= 9:
        window_positions.extend([(-0.42, -0.82, 1.04), (0.42, -0.82, 1.04)])
    for i, loc in enumerate(window_positions):
        material = MATS["damage_crack"] if damaged and i % 3 == 0 else MATS["window_light"]
        cube(f"town_hall_window_{i+1:02d}{suffix}", collection, loc, (0.2, 0.05, 0.22), material)
        cube(f"town_hall_window_frame_{i+1:02d}{suffix}", collection, (loc[0], loc[1] - 0.018, loc[2]), (0.28, 0.035, 0.04), trim_mat(level))
    if level >= 8:
        cylinder("town_hall_clock_face" + suffix, collection, (0, -0.355, 1.5 + level * 0.07), 0.18, 0.035, MATS["plaza_stone"], vertices=24, rot=(math.radians(90), 0, 0))
        cube("town_hall_clock_hand_h" + suffix, collection, (0.05, -0.382, 1.5 + level * 0.07), (0.14, 0.018, 0.018), MATS["damage_crack"])
        cube("town_hall_clock_hand_v" + suffix, collection, (0, -0.384, 1.55 + level * 0.07), (0.018, 0.018, 0.12), MATS["damage_crack"])
    if level >= 6:
        cylinder("town_hall_weather_vane" + suffix, collection, (0.16, -0.04, 2.35 + level * 0.12), 0.018, 0.38, MATS["stone_shadow"], vertices=8, rot=(0, math.radians(90), 0))
    if level >= 9 and not damaged:
        sphere("town_hall_amethyst_seal", collection, (0, -0.91, 0.86), (0.07, 0.025, 0.1), MATS["amethyst_small"], segments=12)
    if damaged:
        cube("town_hall_cracked_facade", collection, (0.38, -0.91, 0.76), (0.06, 0.035, 0.48), MATS["damage_crack"], rot=(0, 0, math.radians(-14)))
        sphere("town_hall_damage_smoke", collection, (-0.18, -0.2, 1.85), (0.14, 0.12, 0.08), MATS["smoke_soft"], segments=12)


def add_props(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    if level <= 4:
        for i in range(2 + level):
            cube(f"town_hall_blueprint_crate_{i+1:02d}{suffix}", collection, (-1.55 + i * 0.24, -1.34, 0.1), (0.2, 0.22, 0.16), MATS["wood_pale"])
    if level >= 3:
        cube("town_hall_notice_board" + suffix, collection, (1.32, -1.24, 0.36), (0.5, 0.08, 0.46), MATS["wood_pale"])
        cylinder("town_hall_notice_post" + suffix, collection, (1.12, -1.24, 0.26), 0.026, 0.52, MATS["wood_log"], vertices=8)
        cylinder("town_hall_notice_post_2" + suffix, collection, (1.52, -1.24, 0.26), 0.026, 0.52, MATS["wood_log"], vertices=8)
    if level >= 5:
        cube("town_hall_archive_box" + suffix, collection, (-1.38, -1.18, 0.13), (0.34, 0.24, 0.2), MATS["wood_trim"])
    if level >= 10 and not damaged:
        cube("town_hall_front_balcony" + suffix, collection, (0, -0.92, 1.16), (0.82, 0.18, 0.08), MATS["stone_light"])
        for i, x in enumerate([-0.32, -0.11, 0.11, 0.32]):
            cylinder(f"town_hall_balcony_post_{i+1:02d}", collection, (x, -1.0, 1.31), 0.022, 0.28, MATS["stone_shadow"], vertices=8)


def add_construction_overlay(collection, level):
    h = 1.1 + level * 0.13
    for i, x in enumerate([-1.32, 1.32]):
        cylinder(f"town_hall_scaffold_post_{i+1:02d}", collection, (x, -1.0, h / 2), 0.036, h, MATS["construction_plank"], vertices=7)
    for z in [h * 0.42, h * 0.7, h]:
        cube(f"town_hall_scaffold_rail_{int(z * 100):03d}", collection, (0, -1.0, z), (2.85, 0.06, 0.07), MATS["construction_plank"])
    for i in range(4):
        cube(f"town_hall_plank_stack_{i+1:02d}", collection, (-1.62, -1.56, 0.06 + i * 0.052), (0.72, 0.13, 0.044), MATS["construction_plank"])
    cylinder("town_hall_rope_coil", collection, (1.62, -1.46, 0.08), 0.13, 0.045, MATS["rope"], vertices=18)
    for i in range(4):
        sphere(f"town_hall_dust_{i+1:02d}", collection, (-0.48 + i * 0.3, -1.48, 0.13 + i * 0.025), (0.13, 0.09, 0.05), MATS["dust"], segments=10)


def add_state(level, state, x_offset):
    collection = bpy.data.collections.new(f"town_hall_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    empty = bpy.data.objects.new(f"town_hall_l{level:02d}_{state}_origin", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.45
    empty.location = (x_offset, 0, 0)
    collection.objects.link(empty)

    local = bpy.data.collections.new(f"town_hall_l{level:02d}_{state}_parts")
    collection.children.link(local)

    before = set(bpy.data.objects)
    damaged = state == "damaged"
    add_base(local, level)
    add_main_body(local, level, damaged)
    add_roofs(local, level, damaged)
    add_tower(local, level, damaged)
    add_details(local, level, damaged)
    add_props(local, level, damaged)
    if state == "construction":
        add_construction_overlay(local, level)

    for obj in set(bpy.data.objects) - before:
        if obj.type == "MESH":
            obj.location.x += x_offset


def add_lighting_and_camera():
    bpy.ops.object.light_add(type="SUN", location=(0, -8, 10))
    sun = bpy.context.object
    sun.name = "preview_sun"
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.ops.object.camera_add(location=(0, -18, 12), rotation=(math.radians(60), 0, 0))
    camera = bpy.context.object
    camera.name = "preview_isometric_camera"
    camera.data.lens = 58
    bpy.context.scene.camera = camera


def write_asset_notes():
    note = bpy.data.texts.new("town_hall_asset_notes")
    note.write(
        "Real City town_hall models, levels 1-10, states active/construction/damaged. "
        "Source docs: docs/buildings/center/town-hall.md and shared/catalog/buildings.ts. "
        "Footprint: 2x2 tile. Origins mark tile base centers. "
        "Progression: small wooden first-settler tower -> wider timber administration -> stone-backed civic hall -> compact brick city center. "
        "Materials emphasize bright Eolia readability: pale wood, leaf/teal/red roofs, light stone, warm brick, restrained amethyst seal only at late levels. "
        "Local reference direction: dense bright isometric map, large silhouette, front plaza, readable flag and big details without copying original-game IP."
    )


def export_glb():
    try:
        bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB")
        return True
    except Exception as exc:
        print(f"GLB export skipped: {exc}")
        return False


def export_state_glbs():
    exported = []
    for level in range(1, 11):
        for state in STATES:
            collection_name = f"town_hall_l{level:02d}_{state}"
            collection = bpy.data.collections.get(collection_name)
            if collection is None:
                print(f"State export skipped, missing collection: {collection_name}")
                continue
            bpy.ops.object.select_all(action="DESELECT")
            for obj in collection.all_objects:
                if obj.type == "MESH":
                    obj.select_set(True)
            filepath = OUT_DIR / STATE_GLB_TEMPLATE.format(level=level, state=state)
            try:
                bpy.ops.export_scene.gltf(filepath=str(filepath), export_format="GLB", use_selection=True)
                exported.append(filepath)
            except Exception as exc:
                print(f"State GLB export skipped for {collection_name}: {exc}")
    return exported


def main():
    # Keep the historical CLI entry point on the current structural-state pipeline.
    source = Path(__file__).with_name("regenerate_town_halls.py")
    spec = importlib.util.spec_from_file_location("town_hall_pipeline", source)
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    pipeline.prepare()
    for level in range(1, 11):
        pipeline.level(level)
    pipeline.finish()


if __name__ == "__main__":
    main()
