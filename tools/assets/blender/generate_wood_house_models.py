import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "src" / "assets" / "buildings" / "housing" / "wood_house"
BLEND_PATH = OUT_DIR / "wood_house_levels.blend"
GLB_PATH = OUT_DIR / "wood_house_levels.glb"
STATE_GLB_TEMPLATE = "wood_house_l{level:02d}_{state}.glb"
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
    rgba = (color[0], color[1], color[2], alpha)
    set_input(bsdf, "Base Color", rgba)
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
        "tile_grass": mat("tile_grass", (0.48, 0.78, 0.34)),
        "path_warm": mat("path_warm", (0.72, 0.5, 0.28)),
        "old_earth": mat("old_earth", (0.52, 0.33, 0.18)),
        "stone_foundation": mat("stone_foundation", (0.62, 0.64, 0.62)),
        "stone_block": mat("stone_block", (0.72, 0.72, 0.68)),
        "wood_cut": mat("wood_cut", (0.9, 0.66, 0.36)),
        "wood_bark": mat("wood_bark", (0.4, 0.22, 0.1)),
        "beam_dark": mat("beam_dark", (0.37, 0.21, 0.1)),
        "glass_warm": mat("glass_warm", (0.88, 0.96, 1.0), 0.28, alpha=0.72, emission=(0.9, 0.6, 0.25, 1), emission_strength=0.18),
        "window_light": mat("window_light", (1.0, 0.74, 0.32), 0.28, emission=(1.0, 0.55, 0.16, 1), emission_strength=0.65),
        "smoke_soft": mat("smoke_soft", (0.72, 0.75, 0.72), 0.95, alpha=0.58),
        "whitewash": mat("whitewash", (0.92, 0.86, 0.66)),
        "flower_red": mat("flower_red", (0.96, 0.16, 0.14)),
        "flower_yellow": mat("flower_yellow", (1.0, 0.84, 0.18)),
        "flower_white": mat("flower_white", (0.96, 0.94, 0.78)),
        "flower_lilac": mat("flower_lilac", (0.78, 0.5, 0.98)),
        "banner_red": mat("banner_red", (0.92, 0.12, 0.1)),
        "pond_blue": mat("pond_blue", (0.14, 0.64, 0.82), 0.36, alpha=0.84),
        "rope": mat("rope", (0.73, 0.57, 0.33)),
        "barrel_band": mat("barrel_band", (0.36, 0.38, 0.36), 0.55, metallic=0.08),
        "lantern_metal": mat("lantern_metal", (0.26, 0.3, 0.3), 0.48, metallic=0.15),
        "construction_plank": mat("construction_plank", (0.86, 0.62, 0.34)),
        "dust": mat("dust", (0.76, 0.67, 0.53), 0.92, alpha=0.5),
        "damage_char": mat("damage_char", (0.12, 0.1, 0.08)),
        "damage_crack": mat("damage_crack", (0.05, 0.04, 0.035)),
        "roof_hole": mat("roof_hole", (0.08, 0.06, 0.04)),
    }
    palettes = {
        1: {"wall": (0.86, 0.69, 0.42), "roof": (0.82, 0.16, 0.12), "trim": (0.96, 0.76, 0.42), "accent": (0.12, 0.58, 0.62)},
        2: {"wall": (0.88, 0.72, 0.46), "roof": (0.08, 0.58, 0.68), "trim": (0.98, 0.78, 0.44), "accent": (0.96, 0.68, 0.16)},
        3: {"wall": (0.9, 0.75, 0.5), "roof": (0.92, 0.44, 0.12), "trim": (0.98, 0.82, 0.5), "accent": (0.12, 0.64, 0.3)},
        4: {"wall": (0.92, 0.78, 0.54), "roof": (0.74, 0.14, 0.12), "trim": (0.98, 0.84, 0.54), "accent": (0.12, 0.42, 0.78)},
        5: {"wall": (0.94, 0.81, 0.58), "roof": (0.14, 0.36, 0.82), "trim": (1.0, 0.86, 0.58), "accent": (0.86, 0.14, 0.12)},
        6: {"wall": (0.96, 0.84, 0.62), "roof": (0.96, 0.66, 0.12), "trim": (1.0, 0.9, 0.66), "accent": (0.08, 0.52, 0.66)},
    }
    for level, palette in palettes.items():
        for role, color in palette.items():
            MATS[f"{role}_l{level:02d}"] = mat(f"{role}_l{level:02d}", color)


def level_mat(role, level):
    return MATS[f"{role}_l{level:02d}"]


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


def sphere(name, collection, loc, scale, material, segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return link_to(collection, obj)


def cone(name, collection, loc, radius1, radius2, depth, material, vertices=7, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def flag(name, collection, loc, width, height, material):
    verts = [(0, 0, 0), (width, 0, height * 0.35), (0, 0, height)]
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
    z = height
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (0, -y, z), (0, y, z)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_base(collection, level):
    cube("wood_house_tile_base", collection, (0, 0, -0.04), (3.6, 3.6, 0.08), MATS["tile_grass"])
    cube("wood_house_front_path", collection, (0, -1.26, 0.012), (0.9 + level * 0.04, 0.86, 0.03), MATS["path_warm"])
    cube("wood_house_old_dugout_trace", collection, (-0.62, 0.58, 0.014), (0.92, 0.42, 0.026), MATS["old_earth"])
    if level >= 3:
        cube("wood_house_blue_yard_pool", collection, (0.9, 0.72, 0.016), (0.48, 0.28, 0.028), MATS["pond_blue"])


def add_body(collection, level, damaged=False):
    width = 1.18 + level * 0.13
    depth = 1.02 + level * 0.08
    height = 0.62 + min(level, 4) * 0.08
    if level >= 5:
        height += 0.28
    foundation_h = 0.14 + min(level, 4) * 0.015
    material_suffix = "_damaged" if damaged else ""

    cube("wood_house_stone_foundation" + material_suffix, collection, (0, 0, foundation_h / 2), (width + 0.22, depth + 0.16, foundation_h), MATS["stone_foundation"])
    cube("wood_house_main_wall" + material_suffix, collection, (0, 0, foundation_h + height / 2), (width, depth, height), level_mat("wall", level))
    cube("wood_house_front_whitewash_panel" + material_suffix, collection, (0, -depth / 2 - 0.052, foundation_h + height * 0.58), (width * 0.72, 0.035, height * 0.56), MATS["whitewash"])

    for side, x in (("left", -width / 2 - 0.035), ("right", width / 2 + 0.035)):
        cube(f"wood_house_corner_beam_{side}{material_suffix}", collection, (x, 0, foundation_h + height / 2), (0.08, depth + 0.08, height + 0.05), MATS["beam_dark"])
    cube("wood_house_front_beam_top" + material_suffix, collection, (0, -depth / 2 - 0.045, foundation_h + height - 0.04), (width + 0.14, 0.07, 0.07), level_mat("trim", level))
    if level >= 2:
        for i, x in enumerate([-width * 0.32, width * 0.32]):
            cube(f"wood_house_diagonal_fascia_{i+1:02d}{material_suffix}", collection, (x, -depth / 2 - 0.062, foundation_h + height * 0.62), (0.07, 0.04, height * 0.68), level_mat("accent", level), rot=(0, 0, math.radians(22 if x < 0 else -22)))

    if level >= 3:
        cube("wood_house_upper_wall" + material_suffix, collection, (0, 0.02, foundation_h + height + 0.24), (width * 0.86, depth * 0.84, 0.42), level_mat("wall", level))
        cube("wood_house_upper_trim" + material_suffix, collection, (0, -depth * 0.44, foundation_h + height + 0.45), (width * 0.92, 0.06, 0.06), level_mat("trim", level))

    if level >= 4:
        annex_x = width / 2 + 0.33
        cube("wood_house_side_annex_wall" + material_suffix, collection, (annex_x, 0.04, foundation_h + 0.31), (0.56, depth * 0.76, 0.62), level_mat("wall", level))
        cube("wood_house_annex_beam" + material_suffix, collection, (annex_x, -depth * 0.37, foundation_h + 0.62), (0.62, 0.06, 0.07), MATS["beam_dark"])

    if level >= 6:
        for i, x in enumerate([-width * 0.34, width * 0.34]):
            cube(f"wood_house_stone_reinforcement_{i+1:02d}{material_suffix}", collection, (x, -depth / 2 - 0.07, foundation_h + 0.2), (0.24, 0.08, 0.34), MATS["stone_block"])


def add_roof(collection, level, damaged=False):
    width = 1.5 + level * 0.15
    depth = 1.28 + level * 0.1
    z = 0.92 + min(level, 4) * 0.08
    if level >= 5:
        z += 0.28
    name_suffix = "_damaged" if damaged else ""
    roof = gable_roof("wood_house_main_roof" + name_suffix, collection, (0, 0, z), (width, depth, 0.34 + level * 0.025), level_mat("roof", level))
    if damaged:
        roof.rotation_euler[1] = math.radians(2.5)
    cube("wood_house_roof_ridge" + name_suffix, collection, (0, 0, z + 0.37 + level * 0.025), (0.08, depth + 0.14, 0.075), level_mat("trim", level))
    cube("wood_house_roof_front_accent" + name_suffix, collection, (0, -depth / 2 - 0.035, z + 0.08), (width * 0.86, 0.05, 0.055), level_mat("accent", level))
    cube("wood_house_roof_light_trim" + name_suffix, collection, (0, -depth / 2 - 0.055, z + 0.16), (width * 0.66, 0.042, 0.045), level_mat("trim", level))

    if level >= 3:
        gable_roof("wood_house_dormer_roof" + name_suffix, collection, (-0.25, -depth / 2 - 0.04, z + 0.12), (0.42, 0.34, 0.18), level_mat("roof", level))
        cube("wood_house_dormer_window" + name_suffix, collection, (-0.25, -depth / 2 - 0.225, z + 0.17), (0.2, 0.04, 0.16), MATS["window_light"])
    if level >= 4:
        gable_roof("wood_house_annex_roof" + name_suffix, collection, (0.94, 0.04, 0.74), (0.76, 0.92, 0.24), level_mat("roof", level))
    if damaged:
        cube("wood_house_roof_burn_mark", collection, (0.34, -0.22, z + 0.19), (0.34, 0.28, 0.035), MATS["roof_hole"], rot=(0, 0, math.radians(12)))


def add_door_windows(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    door_mat = MATS["damage_char"] if damaged else MATS["beam_dark"]
    cube("wood_house_door" + suffix, collection, (0, -0.57, 0.42), (0.36 + level * 0.025, 0.07, 0.52), door_mat)
    cube("wood_house_door_trim_top" + suffix, collection, (0, -0.615, 0.69), (0.5 + level * 0.025, 0.055, 0.065), level_mat("trim", level))
    cube("wood_house_door_bright_arch" + suffix, collection, (0, -0.645, 0.75), (0.62 + level * 0.025, 0.04, 0.08), MATS["whitewash"])
    cube("wood_house_door_accent" + suffix, collection, (0, -0.655, 0.48), (0.28 + level * 0.02, 0.035, 0.055), level_mat("accent", level))
    for i in range(3):
        cube(f"wood_house_front_step_{i+1:02d}{suffix}", collection, (0, -0.76 - i * 0.08, 0.08 - i * 0.012), (0.56 + i * 0.12, 0.1, 0.06), MATS["stone_foundation"])

    window_positions = [(-0.46, -0.56, 0.55), (0.48, -0.56, 0.57)]
    if level >= 2:
        window_positions.append((-0.63, 0.54, 0.58))
    if level >= 5:
        window_positions.extend([(-0.34, -0.56, 1.18), (0.38, -0.56, 1.18)])
    for i, loc in enumerate(window_positions):
        material = MATS["damage_crack"] if damaged and i % 2 == 0 else MATS["window_light"]
        cube(f"wood_house_window_{i+1:02d}{suffix}", collection, loc, (0.22, 0.05, 0.2), material)
        cube(f"wood_house_window_frame_{i+1:02d}{suffix}", collection, (loc[0], loc[1] - 0.018, loc[2]), (0.29, 0.035, 0.04), level_mat("trim", level))


def add_chimney(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    x = -0.52 - level * 0.025
    z = 1.04 + min(level, 5) * 0.08
    if level >= 5:
        z += 0.22
    cylinder("wood_house_chimney_stack" + suffix, collection, (x, 0.28, z), 0.085 + level * 0.006, 0.45 + level * 0.045, MATS["stone_foundation"], vertices=9)
    cube("wood_house_chimney_cap" + suffix, collection, (x, 0.28, z + 0.26 + level * 0.022), (0.25, 0.22, 0.055), MATS["stone_block"])
    if not damaged:
        for i in range(2 + (1 if level >= 5 else 0)):
            sphere(f"wood_house_smoke_{i+1:02d}", collection, (x + i * 0.045, 0.28, z + 0.42 + i * 0.13), (0.08 + i * 0.02, 0.08 + i * 0.02, 0.055), MATS["smoke_soft"], segments=12)


def add_yard_props(collection, level, damaged=False):
    suffix = "_damaged" if damaged else ""
    pole_z = 0.78 + min(level, 4) * 0.12 + (0.28 if level >= 5 else 0)
    cylinder("wood_house_marker_pole" + suffix, collection, (-0.78, -0.08, pole_z / 2), 0.026, pole_z, MATS["wood_cut"], vertices=8)
    if not damaged:
        flag_mat = MATS["banner_red"] if level % 2 else level_mat("accent", level)
        flag("wood_house_roof_flag" + suffix, collection, (-0.78, -0.08, pole_z - 0.16), 0.36, 0.24, flag_mat)
    for i, x in enumerate([-0.48, -0.28, 0.28, 0.48]):
        flower_mat = MATS[["flower_red", "flower_yellow", "flower_lilac", "flower_white"][i]]
        sphere(f"wood_house_front_flower_{i+1:02d}{suffix}", collection, (x, -1.02, 0.13), (0.045, 0.045, 0.03), flower_mat, segments=8)
    if level >= 2:
        for i, x in enumerate([-1.08, -0.72, 0.72, 1.08]):
            cube(f"wood_house_fence_post_{i+1:02d}{suffix}", collection, (x, 1.05, 0.19), (0.07, 0.07, 0.36), level_mat("trim", level))
        cube("wood_house_fence_rail" + suffix, collection, (0, 1.05, 0.31), (2.36, 0.055, 0.06), level_mat("accent", level))
        for i in range(4):
            cylinder(f"wood_house_log_stack_{i+1:02d}{suffix}", collection, (-1.02 + (i % 2) * 0.18, -0.72 - (i // 2) * 0.08, 0.11 + (i // 2) * 0.075), 0.045, 0.36, MATS["wood_cut"], vertices=9, rot=(0, math.radians(90), 0))
    if level >= 4:
        cylinder("wood_house_barrel" + suffix, collection, (1.1, -0.58, 0.18), 0.14, 0.34, MATS["wood_bark"], vertices=14)
        cube("wood_house_barrel_band" + suffix, collection, (1.1, -0.58, 0.18), (0.31, 0.04, 0.05), MATS["barrel_band"])
    if level >= 5:
        cube("wood_house_bench" + suffix, collection, (-0.82, -0.36, 0.16), (0.48, 0.15, 0.09), level_mat("trim", level))
        cylinder("wood_house_lantern_post" + suffix, collection, (0.82, -0.98, 0.36), 0.035, 0.62, MATS["beam_dark"], vertices=8)
        cube("wood_house_lantern_glow" + suffix, collection, (0.82, -0.98, 0.72), (0.15, 0.12, 0.16), MATS["window_light"])
    if level >= 6:
        for i, y in enumerate([0.56, 0.72, 0.88]):
            sphere(f"wood_house_back_garden_bloom_{i+1:02d}{suffix}", collection, (-1.08, y, 0.14), (0.055, 0.055, 0.035), MATS[["flower_red", "flower_white", "flower_yellow"][i]], segments=8)
    if damaged:
        cube("wood_house_fallen_board", collection, (-0.62, -0.86, 0.07), (0.54, 0.09, 0.05), MATS["damage_char"], rot=(0, 0, math.radians(-18)))


def add_construction_overlay(collection, level):
    scaffold_h = 0.88 + min(level, 4) * 0.11 + (0.24 if level >= 5 else 0)
    for i, x in enumerate([-0.84, 0.84]):
        cylinder(f"wood_house_scaffold_post_{i+1:02d}", collection, (x, -0.78, scaffold_h / 2), 0.035, scaffold_h, MATS["construction_plank"], vertices=7)
    cube("wood_house_scaffold_front_rail", collection, (0, -0.78, scaffold_h * 0.72), (1.78, 0.055, 0.06), MATS["construction_plank"])
    cube("wood_house_scaffold_top_rail", collection, (0, -0.78, scaffold_h), (1.88, 0.055, 0.06), MATS["construction_plank"])
    for i in range(3):
        cube(f"wood_house_plank_stack_{i+1:02d}", collection, (-1.08, -0.58, 0.06 + i * 0.055), (0.62, 0.12, 0.045), MATS["construction_plank"])
    cylinder("wood_house_rope_coil", collection, (1.1, -0.74, 0.07), 0.12, 0.04, MATS["rope"], vertices=18)
    for i in range(3):
        sphere(f"wood_house_dust_puff_{i+1:02d}", collection, (-0.26 + i * 0.26, -0.92, 0.12 + i * 0.03), (0.12, 0.08, 0.045), MATS["dust"], segments=10)


def add_state(level, state, x_offset):
    collection = bpy.data.collections.new(f"wood_house_l{level:02d}_{state}")
    bpy.context.scene.collection.children.link(collection)
    empty = bpy.data.objects.new(f"wood_house_l{level:02d}_{state}_origin", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.35
    empty.location = (x_offset, 0, 0)
    collection.objects.link(empty)

    local = bpy.data.collections.new(f"wood_house_l{level:02d}_{state}_parts")
    collection.children.link(local)

    before = set(bpy.data.objects)
    damaged = state == "damaged"
    add_base(local, level)
    add_body(local, level, damaged)
    add_roof(local, level, damaged)
    add_door_windows(local, level, damaged)
    add_chimney(local, level, damaged)
    add_yard_props(local, level, damaged)
    if state == "construction":
        add_construction_overlay(local, level)

    for obj in set(bpy.data.objects) - before:
        if obj.type == "MESH":
            obj.location.x += x_offset


def add_lighting_and_camera():
    bpy.ops.object.light_add(type="SUN", location=(0, -7, 9))
    sun = bpy.context.object
    sun.name = "preview_sun"
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))

    bpy.ops.object.camera_add(location=(0, -13, 8.5), rotation=(math.radians(60), 0, 0))
    camera = bpy.context.object
    camera.name = "preview_isometric_camera"
    camera.data.lens = 58
    bpy.context.scene.camera = camera


def write_asset_notes():
    note = bpy.data.texts.new("wood_house_asset_notes")
    note.write(
        "Real City wood_house models, levels 1-6, states active/construction/damaged. "
        "Source docs: docs/buildings/houses/wood-house.md and shared/catalog/buildings.ts. "
        "Footprint: 1x1 tile. Origins mark tile base centers. "
        "Progression: compact wooden home -> fenced family house -> dormer -> annex -> two-tier city home -> reinforced pre-stone stage. "
        "Materials emphasize pale planks, colored roofs, warm glass, stone foundation, readable yard props. "
        "Local reference direction: bright toy-like isometric houses, high-saturation roofs, pale facade panels, large stairs, flag marker and flower beds without copying original-game IP."
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
    for level in range(1, 7):
        for state in STATES:
            collection_name = f"wood_house_l{level:02d}_{state}"
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
    for level in range(1, 7):
        x_offset = (level - 3.5) * 4.2
        for index, state in enumerate(STATES):
            add_state(level, state, x_offset + (index - 1) * 1.15)
    add_lighting_and_camera()
    write_asset_notes()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    export_glb()
    for path in export_state_glbs():
        print(f"Exported {path}")
    print(f"Saved {BLEND_PATH}")
    print(f"Exported {GLB_PATH}")


if __name__ == "__main__":
    main()
