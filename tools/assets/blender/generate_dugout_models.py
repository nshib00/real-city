import math
from pathlib import Path

import bpy

from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "src" / "assets" / "buildings" / "housing" / "dugout"
BLEND_PATH = OUT_DIR / "dugout_levels.blend"
GLB_PATH = OUT_DIR / "dugout_levels.glb"
STATE_GLB_TEMPLATE = "dugout_l{level:02d}_{state}.glb"
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


def mat(name, color, roughness=0.7, metallic=0.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Metallic", metallic)
    if emission is not None:
        set_input(bsdf, "Emission Color", emission)
        set_input(bsdf, "Emission Strength", emission_strength)
    return material


MATS = {}


def make_materials():
    global MATS
    MATS = {
        "wood_cut": mat("wood_cut", (0.86, 0.62, 0.33, 1)),
        "wood_bark": mat("wood_bark", (0.42, 0.23, 0.1, 1)),
        "stone_cool": mat("stone_cool", (0.52, 0.57, 0.6, 1)),
        "stone_warm": mat("stone_warm", (0.67, 0.61, 0.5, 1)),
        "moss": mat("moss", (0.22, 0.56, 0.24, 1)),
        "smoke_soft": mat("smoke_soft", (0.72, 0.76, 0.73, 0.62), 0.95),
        "warm_light": mat("warm_light", (1.0, 0.63, 0.2, 1), 0.28, emission=(1.0, 0.48, 0.12, 1), emission_strength=0.55),
        "windleaf_green": mat("windleaf_green", (0.48, 0.9, 0.52, 1)),
        "flower_yellow": mat("flower_yellow", (1.0, 0.86, 0.25, 1)),
        "flower_lilac": mat("flower_lilac", (0.78, 0.53, 0.96, 1)),
        "flower_red": mat("flower_red", (0.95, 0.18, 0.16, 1)),
        "flower_white": mat("flower_white", (0.95, 0.92, 0.78, 1)),
        "cloth_teal": mat("cloth_teal", (0.06, 0.58, 0.62, 1)),
        "banner_red": mat("banner_red", (0.92, 0.12, 0.1, 1)),
        "banner_gold": mat("banner_gold", (1.0, 0.74, 0.22, 1)),
        "water_blue": mat("water_blue", (0.14, 0.66, 0.86, 1), 0.35),
        "tool_iron": mat("tool_iron", (0.42, 0.46, 0.47, 1), 0.48, metallic=0.15),
        "construction_plank": mat("construction_plank", (0.86, 0.62, 0.34, 1)),
        "dust": mat("dust", (0.76, 0.67, 0.53, 0.55), 0.92),
        "damage_char": mat("damage_char", (0.12, 0.1, 0.08, 1)),
        "damage_crack": mat("damage_crack", (0.05, 0.04, 0.035, 1)),
        "rope": mat("rope", (0.73, 0.57, 0.33, 1)),
    }
    level_palettes = {
        1: {
            "grass": (0.53, 0.82, 0.34, 1),
            "path": (0.64, 0.45, 0.24, 1),
            "earth": (0.52, 0.33, 0.18, 1),
            "roof": (0.25, 0.55, 0.22, 1),
            "door": (0.38, 0.2, 0.1, 1),
            "trim": (0.78, 0.49, 0.22, 1),
            "plank": (0.75, 0.51, 0.28, 1),
            "accent": (0.72, 0.18, 0.12, 1),
            "roof_patch": (0.44, 0.72, 0.26, 1),
        },
        2: {
            "grass": (0.43, 0.78, 0.34, 1),
            "path": (0.7, 0.49, 0.26, 1),
            "earth": (0.57, 0.36, 0.2, 1),
            "roof": (0.3, 0.62, 0.24, 1),
            "door": (0.16, 0.48, 0.46, 1),
            "trim": (0.92, 0.66, 0.28, 1),
            "plank": (0.82, 0.57, 0.3, 1),
            "accent": (0.1, 0.66, 0.56, 1),
            "roof_patch": (0.78, 0.72, 0.24, 1),
        },
        3: {
            "grass": (0.36, 0.72, 0.32, 1),
            "path": (0.76, 0.54, 0.31, 1),
            "earth": (0.61, 0.4, 0.22, 1),
            "roof": (0.36, 0.68, 0.28, 1),
            "door": (0.82, 0.48, 0.14, 1),
            "trim": (0.92, 0.8, 0.48, 1),
            "plank": (0.88, 0.64, 0.36, 1),
            "accent": (0.88, 0.58, 0.16, 1),
            "roof_patch": (0.13, 0.6, 0.5, 1),
        },
        4: {
            "grass": (0.34, 0.7, 0.34, 1),
            "path": (0.8, 0.58, 0.36, 1),
            "earth": (0.64, 0.43, 0.25, 1),
            "roof": (0.4, 0.72, 0.33, 1),
            "door": (0.58, 0.2, 0.14, 1),
            "trim": (0.94, 0.68, 0.38, 1),
            "plank": (0.91, 0.69, 0.42, 1),
            "accent": (0.72, 0.18, 0.12, 1),
            "roof_patch": (0.92, 0.77, 0.22, 1),
        },
        5: {
            "grass": (0.32, 0.68, 0.36, 1),
            "path": (0.84, 0.63, 0.42, 1),
            "earth": (0.66, 0.46, 0.28, 1),
            "roof": (0.45, 0.76, 0.36, 1),
            "door": (0.12, 0.32, 0.68, 1),
            "trim": (0.96, 0.82, 0.5, 1),
            "plank": (0.95, 0.74, 0.47, 1),
            "accent": (0.12, 0.35, 0.74, 1),
            "roof_patch": (0.9, 0.86, 0.62, 1),
        },
    }
    for level, palette in level_palettes.items():
        for role, color in palette.items():
            MATS[f"{role}_l{level:02d}"] = mat(f"{role}_l{level:02d}", color)


def level_mat(role, level):
    return MATS[f"{role}_l{level:02d}"]


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


def flag(name, collection, loc, width, height, material):
    verts = [(0, 0, 0), (width, 0, height * 0.36), (0, 0, height)]
    faces = [(0, 1, 2)]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_base(collection, level):
    cube("dugout_tile_base", collection, (0, 0, -0.035), (3.6, 3.6, 0.07), level_mat("grass", level))
    cube("dugout_trampled_path", collection, (0, -1.03, 0.006), (0.86, 1.05, 0.026), level_mat("path", level))


def add_mound(collection, level, damaged=False):
    width = 1.55 + level * 0.17
    depth = 1.28 + level * 0.14
    height = 0.44 + level * 0.045
    sphere("dugout_earth_mound", collection, (0, 0.15, 0.24), (width / 2, depth / 2, height), level_mat("earth", level))
    roof = sphere("dugout_turf_roof", collection, (0, 0.18, 0.37 + level * 0.018), (width / 2.08, depth / 2.1, height * 0.54), level_mat("roof", level))
    if damaged:
        roof.rotation_euler[1] = math.radians(3)
        cube("dugout_roof_burn_mark", collection, (0.18, 0.0, 0.57 + level * 0.018), (0.46, 0.08, 0.035), MATS["damage_char"], rot=(0, 0, math.radians(-12)))
        cube("dugout_roof_split_crack", collection, (-0.18, -0.06, 0.59 + level * 0.018), (0.36, 0.035, 0.035), MATS["damage_crack"], rot=(0, 0, math.radians(19)))
    if level >= 2:
        sphere("dugout_mossy_roof_patch", collection, (0.32, -0.05, 0.52 + level * 0.018), (0.22, 0.14, 0.045), MATS["moss"], segments=12)
        sphere("dugout_colored_roof_patch", collection, (-0.34, -0.14, 0.5 + level * 0.018), (0.2, 0.12, 0.035), level_mat("roof_patch", level), segments=12)
    if level >= 4:
        sphere("dugout_sunny_roof_patch", collection, (-0.28, 0.32, 0.57 + level * 0.018), (0.28, 0.16, 0.04), level_mat("roof_patch", level), segments=12)


def add_door(collection, level, damaged=False):
    door_w = 0.36 + level * 0.035
    door_h = 0.46 + level * 0.035
    cube("dugout_door", collection, (0, -0.53, 0.28), (door_w, 0.08, door_h), MATS["damage_char"] if damaged else level_mat("door", level), rot=(0, 0, math.radians(-2 if damaged else 0)))
    cube("dugout_door_frame_top", collection, (0, -0.59, 0.54 + level * 0.03), (door_w + 0.18, 0.12, 0.08), level_mat("trim", level))
    cube("dugout_door_frame_left", collection, (-door_w / 2 - 0.07, -0.59, 0.31), (0.08, 0.12, door_h + 0.12), level_mat("trim", level))
    cube("dugout_door_frame_right", collection, (door_w / 2 + 0.07, -0.59, 0.31), (0.08, 0.12, door_h + 0.12), level_mat("trim", level))
    cube("dugout_bright_entry_arch", collection, (0, -0.635, 0.62 + level * 0.018), (door_w + 0.28, 0.045, 0.095), MATS["banner_gold"])
    cube("dugout_door_accent_plank", collection, (0, -0.625, 0.44), (door_w * 0.82, 0.032, 0.045), level_mat("accent", level))
    if level >= 3:
        cube("dugout_door_painted_crossbar", collection, (0, -0.622, 0.34), (door_w + 0.02, 0.035, 0.055), level_mat("accent", level))
    if level >= 4:
        cube("dugout_warm_window", collection, (0.48, -0.51, 0.38), (0.18, 0.055, 0.16), MATS["damage_crack"] if damaged else MATS["warm_light"])


def add_chimney(collection, level, damaged=False):
    x = -0.42 - level * 0.025
    z = 0.64 + level * 0.055
    cylinder("dugout_chimney_stack", collection, (x, 0.2, z), 0.085 + level * 0.008, 0.42 + level * 0.09, MATS["stone_cool"], vertices=9)
    cube("dugout_chimney_cap", collection, (x, 0.2, z + 0.25 + level * 0.05), (0.26, 0.22, 0.055), MATS["stone_warm"])
    if damaged:
        cube("dugout_chimney_crack", collection, (x + 0.045, 0.115, z + 0.08), (0.035, 0.03, 0.22), MATS["damage_crack"], rot=(0, 0, math.radians(11)))
    if level >= 2:
        for i in range(1 if damaged else 2):
            sphere(f"dugout_smoke_puff_{i+1}", collection, (x + i * 0.05, 0.2, z + 0.42 + i * 0.13), (0.085 + i * 0.025, 0.085 + i * 0.025, 0.055), MATS["smoke_soft"], segments=12)


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
            MATS["wood_cut" if i % 2 == 0 else "wood_bark"],
            vertices=10,
            rot=(0, math.radians(90), 0),
        )


def add_stones(collection, level):
    for i in range(3 + level):
        angle = -0.85 + i * 0.28
        x = math.sin(angle) * (0.75 + level * 0.05)
        y = -0.43 + math.cos(angle) * 0.18
        material = MATS["stone_warm" if i % 2 == 0 else "stone_cool"]
        sphere(f"dugout_entry_stone_{i+1:02d}", collection, (x, y, 0.06), (0.08, 0.06, 0.04), material, segments=10)


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
            level_mat("plank", level),
            vertices=8,
            rot=(math.radians(23 if x < 0 else -23), 0, 0),
        )
    if level >= 4:
        cube("dugout_plank_awning", collection, (0, -0.76, 0.71), (0.92, 0.54, 0.09), level_mat("plank", level))
        cube("dugout_awning_colored_edge", collection, (0, -1.03, 0.73), (0.92, 0.045, 0.07), level_mat("accent", level))
        cube("dugout_front_plank_face", collection, (0, -0.61, 0.42), (1.14, 0.055, 0.2), level_mat("plank", level))
    if level >= 5:
        cube("dugout_reinforced_facade", collection, (0, -0.64, 0.28), (1.28, 0.06, 0.28), level_mat("plank", level))
        cube("dugout_facade_shadow_gap", collection, (0, -0.675, 0.31), (1.2, 0.025, 0.045), MATS["wood_bark"])
        cube("dugout_facade_painted_band", collection, (0, -0.682, 0.43), (1.08, 0.035, 0.055), level_mat("accent", level))
        cube("dugout_stone_threshold", collection, (0, -0.81, 0.07), (0.82, 0.2, 0.08), MATS["stone_warm"])


def add_fence_and_props(collection, level, damaged=False):
    cylinder("dugout_marker_pole", collection, (-0.5, -0.18, 0.85 + level * 0.04), 0.025, 0.78 + level * 0.08, MATS["wood_cut"], vertices=8)
    if damaged:
        flag("dugout_torn_marker_flag", collection, (-0.5, -0.18, 1.18 + level * 0.085), 0.22, 0.17, MATS["damage_char"])
    else:
        flag("dugout_marker_flag", collection, (-0.5, -0.18, 1.18 + level * 0.085), 0.34, 0.24, MATS["banner_red" if level % 2 else "cloth_teal"])
    cylinder("dugout_round_door_sign", collection, (0.31, -0.66, 0.55), 0.07, 0.025, level_mat("accent", level), vertices=18, rot=(math.radians(90), 0, 0))
    if level >= 2:
        cube("dugout_blue_entry_mat", collection, (0, -0.86, 0.035), (0.52, 0.24, 0.03), MATS["water_blue"])
    if level >= 3:
        for i, x in enumerate([-0.95, -0.55, 0.55, 0.95]):
            cube(f"dugout_fence_post_{i+1:02d}", collection, (x, 0.93, 0.18), (0.07, 0.07, 0.35), level_mat("trim", level))
        cube("dugout_fence_rail", collection, (0, 0.93, 0.28), (2.0, 0.055, 0.06), MATS["damage_char"] if damaged else level_mat("trim", level), rot=(0, 0, math.radians(2 if damaged else 0)))
        cube("dugout_fence_painted_slat", collection, (0, 0.965, 0.34), (1.55, 0.035, 0.045), level_mat("accent", level))
    if level >= 4:
        cube("dugout_tool_crate", collection, (0.92, -0.8, 0.12), (0.28, 0.22, 0.18), level_mat("door", level))
        cube("dugout_tool_head", collection, (1.08, -0.77, 0.24), (0.16, 0.045, 0.05), MATS["tool_iron"])
        cylinder("dugout_rope_coil", collection, (1.12, -0.48, 0.06), 0.13, 0.045, MATS["wood_cut"], vertices=18)
    if level >= 5:
        cube("dugout_small_bench", collection, (-0.72, -0.55, 0.16), (0.48, 0.15, 0.09), level_mat("plank", level))
        cube("dugout_colored_cloth_marker", collection, (-0.46, -0.55, 0.23), (0.08, 0.16, 0.045), level_mat("accent", level))
    if damaged:
        cube("dugout_fallen_plank", collection, (0.8, -0.92, 0.08), (0.56, 0.09, 0.055), MATS["damage_char"], rot=(0, 0, math.radians(-18)))
        sphere("dugout_rubble_clump", collection, (-0.72, -0.74, 0.065), (0.14, 0.09, 0.045), MATS["stone_cool"], segments=10)


def add_construction_overlay(collection, level):
    scaffold_h = 0.62 + level * 0.12
    for i, x in enumerate([-0.82, 0.82]):
        cylinder(
            f"dugout_scaffold_post_{i+1:02d}",
            collection,
            (x, -0.58, scaffold_h / 2),
            0.035,
            scaffold_h,
            MATS["construction_plank"],
            vertices=8,
        )
    cube("dugout_scaffold_front_rail", collection, (0, -0.58, scaffold_h * 0.68), (1.78, 0.06, 0.065), MATS["construction_plank"])
    cube("dugout_scaffold_top_rail", collection, (0, -0.32, scaffold_h * 0.95), (1.5, 0.06, 0.065), MATS["construction_plank"], rot=(0, 0, math.radians(6)))
    for i in range(3):
        cube(
            f"dugout_plank_stack_{i+1:02d}",
            collection,
            (-1.08 + i * 0.07, -0.98, 0.06 + i * 0.055),
            (0.58, 0.1, 0.045),
            MATS["construction_plank"],
            rot=(0, 0, math.radians(7 - i * 3)),
        )
    cylinder("dugout_construction_rope_coil", collection, (1.05, -0.94, 0.07), 0.13, 0.045, MATS["rope"], vertices=18)
    for i in range(3):
        sphere(
            f"dugout_construction_dust_{i+1:02d}",
            collection,
            (-0.28 + i * 0.28, -0.66 + i * 0.035, 0.08),
            (0.1 + i * 0.025, 0.07, 0.035),
            MATS["dust"],
            segments=10,
        )


def add_grass_and_windleaves(collection, level):
    for i in range(5 + level * 2):
        angle = i * 2.37
        radius = 1.0 + (i % 3) * 0.18
        x = math.sin(angle) * radius
        y = math.cos(angle) * radius * 0.75 + 0.1
        cone(f"dugout_grass_tuft_{i+1:02d}", collection, (x, y, 0.11), 0.055, 0.0, 0.22, MATS["moss" if i % 2 == 0 else f"grass_l{level:02d}"], vertices=5)
        if level >= 2 and i % 5 == 0:
            flower_cycle = ["flower_yellow", "flower_lilac", "flower_red", "flower_white"]
            flower_mat = MATS[flower_cycle[(i + level) % len(flower_cycle)]]
            sphere(f"dugout_wildflower_{i+1:02d}", collection, (x + 0.035, y - 0.025, 0.22), (0.04, 0.04, 0.025), flower_mat, segments=8)
    for i, x in enumerate([-0.34, -0.17, 0.17, 0.34]):
        flower_mat = MATS[["flower_red", "flower_yellow", "flower_lilac", "flower_white"][i]]
        sphere(f"dugout_entry_flower_{i+1:02d}", collection, (x, -0.96, 0.14), (0.045, 0.045, 0.03), flower_mat, segments=8)
    if level >= 3:
        for i in range(level - 1):
            angle = i * 1.8 + 0.35
            x = math.sin(angle) * 0.95
            y = math.cos(angle) * 0.72 + 0.24
            cone(f"dugout_windleaf_{i+1:02d}", collection, (x, y, 0.18), 0.035, 0.01, 0.32, MATS["windleaf_green"], vertices=6, rot=(math.radians(8), 0, angle))


def add_state(level, state, x_offset):
    collection = bpy.data.collections.new(f"dugout_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    empty = bpy.data.objects.new(f"dugout_l{level:02d}_{state}_origin", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.35
    empty.location = (x_offset, 0, 0)
    collection.objects.link(empty)

    local = bpy.data.collections.new(f"dugout_l{level:02d}_{state}_parts")
    collection.children.link(local)

    before = set(bpy.data.objects)
    damaged = state == "damaged"
    add_base(local, level)
    add_mound(local, level, damaged)
    add_door(local, level, damaged)
    add_chimney(local, level, damaged)
    add_logs(local, level)
    add_stones(local, level)
    add_supports(local, level)
    add_fence_and_props(local, level, damaged)
    add_grass_and_windleaves(local, level)
    if state == "construction":
        add_construction_overlay(local, level)

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
        "Real City dugout models, levels 1-5, states active/construction/damaged. "
        "Source docs: docs/buildings/houses/dugout.md. "
        "Footprint: 1x1 tile. Origin empties mark tile base centers. "
        "Level progression: earth shelter -> reinforced turf dugout -> pre-wood-house half-dugout. "
        "Construction states add temporary scaffold, plank stacks, rope and dust. "
        "Damaged states add roof burns, cracks, torn marker, fallen plank, rubble and reduced smoke. "
        "Materials use level-specific earth, turf, wood, path and accent palettes for stronger map readability. "
        "Local reference direction: bright isometric readability, large entry accent, flag marker, flower clusters and compact toy-like props without copying original-game IP."
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
    for level in range(1, 6):
        for state in STATES:
            collection_name = f"dugout_l{level:02d}_{state}"
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    make_materials()
    for level in range(1, 6):
        level_x = (level - 3) * 5.4
        for index, state in enumerate(STATES):
            add_state(level, state, level_x + (index - 1) * 1.4)
    add_lighting_and_camera()
    write_asset_notes()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    export_glb()
    for path in export_state_glbs():
        print(f"Exported {path}")
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id="dugout",
            display_name="Землянка",
            category="housing",
            output_dir=OUT_DIR,
            levels=range(1, 6),
            states=STATES,
            source_blend=BLEND_PATH,
            combined_glb=GLB_PATH,
            generator="tools/assets/blender/generate_dugout_models.py",
            style_reference="Real City early housing earth-and-turf mid-poly",
        )
    )
    print(f"Saved {BLEND_PATH}")
    print(f"Exported {GLB_PATH}")


if __name__ == "__main__":
    main()
