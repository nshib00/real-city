import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "lumber_yard"
BLEND_PATH = OUT_DIR / "lumber_yard_levels.blend"
GLB_PATH = OUT_DIR / "lumber_yard_levels.glb"
REPORT_PATH = OUT_DIR / "generation-report.json"
STATE_GLB_TEMPLATE = "lumber_yard_l{level:02d}_{state}.glb"
STATE_PNG_TEMPLATE = "lumber_yard_l{level:02d}_{state}.png"
LEVELS = range(1, 14)
STATES = ("active", "construction", "damaged")
SPRITE_SIZE = (512, 384)
MATS = {}


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
    if node and name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color, roughness=0.68, metallic=0.0, alpha=1.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (color[0], color[1], color[2], alpha)
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


def make_materials():
    global MATS
    MATS = {
        "tile_grass": mat("MAT_tile_grass", (0.26, 0.48, 0.08, 1)),
        "yard_dirt": mat("MAT_yard_dirt", (0.68, 0.48, 0.27, 1)),
        "sawdust": mat("MAT_sawdust", (0.94, 0.73, 0.42, 1)),
        "stone_base": mat("MAT_stone_warm", (0.64, 0.63, 0.56, 1)),
        "stone_light": mat("MAT_stone_light", (0.78, 0.78, 0.7, 1)),
        "brick": mat("MAT_brick_muted", (0.73, 0.34, 0.22, 1)),
        "concrete": mat("MAT_concrete_light", (0.68, 0.7, 0.66, 1)),
        "wood_log": mat("MAT_wood_bark", (0.56, 0.29, 0.11, 1)),
        "wood_cut": mat("MAT_wood_cut", (0.92, 0.68, 0.36, 1)),
        "wood_pale": mat("MAT_wood_pale", (0.82, 0.56, 0.28, 1)),
        "wood_dark": mat("MAT_wood_dark", (0.32, 0.18, 0.08, 1)),
        "roof_canvas": mat("MAT_roof_canvas", (0.9, 0.82, 0.58, 1), 0.86),
        "roof_teal": mat("MAT_roof_teal", (0.08, 0.55, 0.56, 1)),
        "roof_tile": mat("MAT_roof_rune_tile", (0.52, 0.3, 0.72, 1), 0.48, 0.08),
        "metal_worn": mat("MAT_metal_worn", (0.48, 0.53, 0.54, 1), 0.42, 0.28),
        "steel": mat("MAT_steel_bright", (0.78, 0.84, 0.82, 1), 0.34, 0.45),
        "copper": mat("MAT_copper_detail", (0.92, 0.48, 0.18, 1), 0.36, 0.34),
        "gold": mat("MAT_gold_calibration", (1.0, 0.72, 0.22, 1), 0.34, 0.45),
        "fuel": mat("MAT_fuel_barrel", (0.65, 0.22, 0.12, 1), 0.52),
        "oil": mat("MAT_oil_dark", (0.04, 0.04, 0.05, 1), 0.28),
        "belt": mat("MAT_drive_belt", (0.18, 0.12, 0.08, 1)),
        "rope": mat("MAT_rope", (0.72, 0.55, 0.32, 1)),
        "premium_plank": mat("MAT_premium_plank", (1.0, 0.78, 0.42, 1), 0.34, 0.18),
        "rune": mat("MAT_rune_soft_amethyst", (0.68, 0.36, 1.0, 1), 0.28, 0, 1, emission=(0.5, 0.2, 1.0, 1), emission_strength=0.18),
        "glass": mat("MAT_bluegreen_glass", (0.48, 0.86, 0.92, 1), 0.18, 0, 0.68, emission=(0.15, 0.55, 0.72, 1), emission_strength=0.08),
        "warm_light": mat("MAT_warm_lantern", (1.0, 0.68, 0.24, 1), 0.3, emission=(1.0, 0.46, 0.12, 1), emission_strength=0.55),
        "dust": mat("MAT_dust", (0.76, 0.66, 0.5, 0.46), 0.95, alpha=0.46),
        "damage_char": mat("MAT_damage_char", (0.08, 0.06, 0.04, 1)),
        "damage_crack": mat("MAT_damage_crack", (0.03, 0.025, 0.02, 1)),
        "moss": mat("MAT_moss", (0.2, 0.48, 0.18, 1)),
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


def stylize(obj, bevel=0.025, segments=2, smooth=False):
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    del bevel, segments
    return obj


def cube(name, collection, loc, scale, material, rot=(0, 0, 0), bevel=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    stylize(obj, bevel=min(scale) * 0.08 if bevel is None else bevel)
    return link_to(collection, obj)


def cylinder(name, collection, loc, radius, depth, material, vertices=18, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    stylize(obj, bevel=radius * 0.08, smooth=True)
    return link_to(collection, obj)


def sphere(name, collection, loc, scale, material, segments=18):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=10, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    stylize(obj, bevel=0, smooth=True)
    return link_to(collection, obj)


def triangular_roof(name, collection, loc, size, material):
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
    stylize(obj, bevel=0.035, segments=2)
    return obj


def tier(level):
    if level >= 11:
        return "prestige"
    if level >= 8:
        return "advanced"
    if level >= 4:
        return "mechanized"
    return "craft"


def add_base(collection, level, damaged=False):
    cube("SM_lumber_yard_tile_base", collection, (0, 0, -0.05), (3.65, 3.65, 0.1), MATS["tile_grass"], bevel=0.012)
    yard_w = 2.45 + min(level, 8) * 0.055
    yard_d = 2.05 + min(level, 10) * 0.045
    cube("SM_lumber_yard_work_yard", collection, (0, -0.18, 0.01), (yard_w, yard_d, 0.04), MATS["yard_dirt"], bevel=0.018)
    pad_mat = MATS["concrete"] if level >= 8 else MATS["brick"] if level >= 4 else MATS["stone_base"]
    cube("SM_lumber_yard_machine_pad", collection, (-0.22, -0.34, 0.065), (1.42 + level * 0.045, 0.86 + level * 0.02, 0.1), pad_mat)
    cube("SM_lumber_yard_sawdust_lane", collection, (-0.2, -0.95, 0.09), (1.42, 0.26, 0.035), MATS["sawdust"], rot=(0, 0, math.radians(-4)), bevel=0.012)
    if damaged:
        cube("SM_lumber_yard_cracked_pad", collection, (-0.2, -0.38, 0.15), (1.0, 0.05, 0.035), MATS["damage_crack"], rot=(0, 0, math.radians(18)))


def add_logs(collection, level, damaged=False):
    log_count = min(5 + level // 2, 10)
    for index in range(log_count):
        x = -1.22 + (index % 5) * 0.24 + (0.08 if index >= 5 else 0)
        y = 0.68 + (index // 5) * 0.2 + ((index % 2) * 0.06)
        angle = -8 + (index % 5) * 5
        z = 0.22 + (index // 5) * 0.13
        mat_body = MATS["damage_char"] if damaged and index in (2, 7) else MATS["wood_log"]
        cylinder(f"SM_lumber_yard_log_{index+1:02d}", collection, (x, y, z), 0.12, 0.82, mat_body, vertices=18, rot=(0, math.radians(90), math.radians(angle)))
        cylinder(f"SM_lumber_yard_log_cut_{index+1:02d}", collection, (x - 0.4, y - 0.04, z), 0.122, 0.025, MATS["wood_cut"], vertices=18, rot=(0, math.radians(90), math.radians(angle)))
    plank_stacks = min(2 + level // 2, 7)
    for index in range(plank_stacks):
        x = -0.96 + (index % 4) * 0.42
        y = -1.2 - (index // 4) * 0.2
        mat_plank = MATS["premium_plank"] if level >= 8 and index == plank_stacks - 1 else MATS["wood_pale"]
        cube(f"SM_lumber_yard_plank_stack_{index+1:02d}", collection, (x, y, 0.18 + (index % 3) * 0.07), (0.74, 0.12, 0.1), mat_plank, rot=(0, 0, math.radians(4 - index)))


def add_shed(collection, level, state):
    construction = state == "construction"
    damaged = state == "damaged"
    width = 1.35 + min(level, 10) * 0.045
    depth = 1.0 + min(level, 8) * 0.035
    height = 0.82 + min(level, 12) * 0.035
    mat_post = MATS["metal_worn"] if level >= 8 else MATS["wood_dark"]
    mat_roof = MATS["roof_tile"] if level >= 11 else MATS["roof_teal"] if level >= 3 else MATS["roof_canvas"]
    cube("SM_lumber_yard_foundation", collection, (-0.42, -0.46, 0.14), (width + 0.18, depth + 0.08, 0.22), MATS["stone_base"])
    for idx, (x, y) in enumerate([(-1.05, -0.88), (0.2, -0.88), (-1.05, -0.1), (0.2, -0.1)]):
        post_h = height * (0.6 if construction and idx == 1 else 1.0)
        cylinder(f"SM_lumber_yard_shed_post_{idx+1}", collection, (x, y, 0.32 + post_h / 2), 0.045, post_h, mat_post, vertices=10)
    cube("SM_lumber_yard_back_beam", collection, (-0.42, -0.1, 0.98), (width, 0.1, 0.12), mat_post)
    cube("SM_lumber_yard_front_beam", collection, (-0.42, -0.88, 0.98), (width, 0.1, 0.12), mat_post)
    if not construction:
        roof = triangular_roof("SM_lumber_yard_shed_roof", collection, (-0.42, -0.42, 1.08), (width + 0.26, depth + 0.12, 0.28 + level * 0.008), mat_roof)
        if damaged:
            roof.rotation_euler[1] = math.radians(3)
            cube("SM_lumber_yard_roof_collapse", collection, (-0.08, -0.72, 1.22), (0.46, 0.34, 0.055), MATS["damage_char"], rot=(0, 0, math.radians(11)))
        cube("SM_lumber_yard_roof_ridge", collection, (-0.42, -0.42, 1.38 + level * 0.008), (0.08, depth + 0.16, 0.08), mat_post)
        if level >= 11:
            for idx, offset in enumerate((-0.34, 0.0, 0.34)):
                cube(f"SM_lumber_yard_rune_tile_{idx+1}", collection, (-0.42 + offset, -0.96, 1.22), (0.22, 0.035, 0.18), MATS["rune"], rot=(math.radians(18), 0, 0))
    else:
        cube("SM_lumber_yard_unfinished_roof_beam", collection, (-0.42, -0.52, 1.15), (width + 0.36, 0.08, 0.1), MATS["wood_pale"], rot=(0, 0, math.radians(4)))
        cube("SM_lumber_yard_canvas_partial", collection, (-0.76, -0.8, 1.18), (0.72, 0.08, 0.34), MATS["roof_canvas"], rot=(math.radians(10), 0, math.radians(-4)))
    cube("SM_lumber_yard_work_table", collection, (-0.42, -0.55, 0.42), (0.95 + level * 0.025, 0.42, 0.12), MATS["wood_pale"])


def add_saw_line(collection, level, state):
    damaged = state == "damaged"
    blade_radius = 0.24 + min(level, 9) * 0.012
    cylinder("SM_lumber_yard_saw_blade", collection, (-0.44, -0.9, 0.66), blade_radius, 0.06, MATS["steel"], vertices=36, rot=(math.radians(90), 0, 0))
    for index, angle in enumerate(range(0, 360, 45)):
        cube(f"SM_lumber_yard_saw_tooth_{index:02d}", collection, (-0.44 + math.cos(math.radians(angle)) * blade_radius, -0.94, 0.66 + math.sin(math.radians(angle)) * blade_radius), (0.07, 0.045, 0.12), MATS["steel"], rot=(0, math.radians(angle), 0), bevel=0.008)
    cylinder("SM_lumber_yard_saw_hub", collection, (-0.44, -0.96, 0.66), 0.08, 0.09, MATS["metal_worn"], vertices=18, rot=(math.radians(90), 0, 0))
    if level >= 3:
        cube("SM_lumber_yard_frame_saw_left", collection, (-0.82, -0.88, 0.75), (0.08, 0.08, 0.66), MATS["metal_worn"])
        cube("SM_lumber_yard_frame_saw_right", collection, (-0.08, -0.88, 0.75), (0.08, 0.08, 0.66), MATS["metal_worn"])
        cube("SM_lumber_yard_frame_saw_top", collection, (-0.45, -0.88, 1.08), (0.82, 0.08, 0.08), MATS["metal_worn"])
    if level >= 4:
        cube("SM_lumber_yard_motor_block", collection, (0.36, -0.86, 0.48), (0.42, 0.34, 0.34), MATS["metal_worn"])
        cylinder("SM_lumber_yard_motor_cap", collection, (0.57, -0.86, 0.48), 0.17, 0.08, MATS["copper"], vertices=18, rot=(0, math.radians(90), 0))
        cube("SM_lumber_yard_drive_belt", collection, (0.0, -0.9, 0.62), (0.82, 0.045, 0.08), MATS["belt"], rot=(0, 0, math.radians(-8)))
    if level >= 7:
        for idx, x in enumerate([-0.94, -0.48, -0.02, 0.44]):
            cylinder(f"SM_lumber_yard_feed_roller_{idx+1}", collection, (x, -0.22, 0.48), 0.07, 0.62, MATS["steel"], vertices=18, rot=(math.radians(90), 0, 0))
        cube("SM_lumber_yard_feed_rail_left", collection, (-0.24, -0.56, 0.5), (1.55, 0.06, 0.08), MATS["metal_worn"])
        cube("SM_lumber_yard_feed_rail_right", collection, (-0.24, 0.1, 0.5), (1.55, 0.06, 0.08), MATS["metal_worn"])
    if level >= 9:
        cube("SM_lumber_yard_operator_cabin", collection, (0.82, -0.48, 0.62), (0.5, 0.45, 0.6), MATS["wood_pale"])
        cube("SM_lumber_yard_operator_window", collection, (0.82, -0.72, 0.68), (0.32, 0.035, 0.22), MATS["glass"])
        cylinder("SM_lumber_yard_exhaust_stack", collection, (0.52, -0.52, 1.05), 0.06, 0.7, MATS["metal_worn"], vertices=14)
    if level >= 12:
        sphere("SM_lumber_yard_super_mechanism_core", collection, (-0.44, -0.88, 0.94), (0.16, 0.12, 0.16), MATS["rune"], segments=18)
        cube("SM_lumber_yard_gold_calibration_bar", collection, (-0.44, -1.02, 1.1), (0.58, 0.045, 0.055), MATS["gold"])
    if damaged:
        cube("SM_lumber_yard_bent_blade_mark", collection, (-0.22, -0.98, 0.84), (0.28, 0.04, 0.06), MATS["damage_crack"], rot=(0, math.radians(28), 0))
        cube("SM_lumber_yard_broken_feed_rail", collection, (0.4, -0.18, 0.52), (0.72, 0.06, 0.08), MATS["damage_char"], rot=(0, 0, math.radians(18)))


def add_fuel_and_crane(collection, level, state):
    damaged = state == "damaged"
    if level >= 4:
        for index in range(1 + min((level - 4) // 3, 2)):
            x = 1.05 + index * 0.18
            cylinder(f"SM_lumber_yard_fuel_barrel_{index+1}", collection, (x, -1.0 + index * 0.16, 0.3), 0.16, 0.5, MATS["fuel"], vertices=18)
            cube(f"SM_lumber_yard_fuel_label_{index+1}", collection, (x, -1.17 + index * 0.16, 0.32), (0.22, 0.035, 0.18), MATS["gold"])
        cube("SM_lumber_yard_oil_stain", collection, (0.76, -0.9, 0.09), (0.46, 0.28, 0.025), MATS["oil"], rot=(0, 0, math.radians(-12)), bevel=0.02)
    if level >= 5:
        post_mat = MATS["steel"] if level >= 8 else MATS["wood_dark"]
        cylinder("SM_lumber_yard_crane_post", collection, (0.96, -0.18, 0.72), 0.07, 1.36, post_mat, vertices=12)
        cube("SM_lumber_yard_crane_arm", collection, (0.54, -0.12, 1.28), (1.14, 0.09, 0.1), post_mat, rot=(0, 0, math.radians(-8)))
        cylinder("SM_lumber_yard_crane_rope", collection, (0.12, -0.12, 0.92), 0.015, 0.62, MATS["rope"], vertices=8)
        cube("SM_lumber_yard_crane_hook", collection, (0.12, -0.12, 0.56), (0.12, 0.05, 0.12), MATS["metal_worn"], rot=(0, 0, math.radians(22)))
        if damaged:
            cube("SM_lumber_yard_broken_crane_arm", collection, (1.12, 0.0, 0.74), (0.64, 0.09, 0.1), MATS["damage_char"], rot=(0, math.radians(18), math.radians(24)))


def add_premium_rack(collection, level, state):
    if level < 3:
        return
    mat_frame = MATS["gold"] if level >= 12 else MATS["copper"] if level >= 5 else MATS["wood_dark"]
    cube("SM_lumber_yard_premium_rack_back", collection, (1.05, 0.56, 0.34), (0.66, 0.08, 0.52), mat_frame)
    for idx in range(min(1 + level // 4, 4)):
        cube(f"SM_lumber_yard_premium_plank_{idx+1}", collection, (1.05, 0.48, 0.24 + idx * 0.1), (0.54, 0.08, 0.06), MATS["premium_plank"], rot=(0, 0, math.radians(2)))
    if level >= 11:
        cube("SM_lumber_yard_rune_quality_tag", collection, (0.72, 0.42, 0.62), (0.08, 0.035, 0.26), MATS["rune"], rot=(0, 0, math.radians(-6)))
    if state == "damaged":
        cube("SM_lumber_yard_broken_premium_rack", collection, (1.12, 0.46, 0.32), (0.64, 0.08, 0.08), MATS["damage_char"], rot=(0, 0, math.radians(18)))


def add_props(collection, level, state):
    damaged = state == "damaged"
    cylinder("SM_lumber_yard_water_barrel", collection, (1.18, -0.72, 0.28), 0.16, 0.44, MATS["wood_dark"], vertices=18)
    cube("SM_lumber_yard_tool_rack", collection, (1.18, 0.06, 0.42), (0.12, 0.54, 0.62), MATS["wood_dark"])
    cube("SM_lumber_yard_axe_handle", collection, (1.08, 0.02, 0.48), (0.05, 0.07, 0.52), MATS["wood_pale"], rot=(0, 0, math.radians(-18)))
    cube("SM_lumber_yard_axe_head", collection, (1.01, -0.07, 0.7), (0.15, 0.04, 0.14), MATS["metal_worn"], rot=(0, 0, math.radians(-18)))
    sphere("SM_lumber_yard_lantern", collection, (-1.2, -0.24, 0.82), (0.085, 0.085, 0.11), MATS["warm_light"], segments=14)
    for index, (x, y) in enumerate([(-1.18, 0.12), (0.44, 0.84), (1.34, 0.08)]):
        sphere(f"SM_lumber_yard_moss_patch_{index+1:02d}", collection, (x, y, 0.09), (0.16, 0.1, 0.035), MATS["moss"], segments=12)
    if level >= 6:
        cube("SM_lumber_yard_copper_gauge", collection, (0.78, -0.9, 0.72), (0.16, 0.035, 0.16), MATS["copper"], rot=(0, 0, math.radians(-8)))
    if damaged:
        sphere("SM_lumber_yard_smoke_puff", collection, (0.18, -0.72, 1.1), (0.24, 0.2, 0.16), MATS["dust"], segments=14)


def add_construction_overlay(collection, level):
    for index, x in enumerate([-1.26, -0.38, 0.48]):
        cylinder(f"SM_lumber_yard_scaffold_post_{index+1:02d}", collection, (x, -1.0, 0.62), 0.03, 1.0, MATS["wood_pale"], vertices=10)
    cube("SM_lumber_yard_scaffold_cross", collection, (-0.38, -1.0, 1.08), (1.88, 0.07, 0.07), MATS["wood_pale"])
    cube("SM_lumber_yard_scaffold_diag", collection, (-0.38, -1.0, 0.72), (1.72, 0.055, 0.055), MATS["rope"], rot=(0, math.radians(24), 0))
    for index, x in enumerate([-0.08, 0.24, 0.56]):
        cube(f"SM_lumber_yard_loose_beam_{index+1:02d}", collection, (x, 1.02, 0.18 + index * 0.08), (0.62, 0.09, 0.09), MATS["wood_pale"], rot=(0, 0, math.radians(8 - index * 4)))
    if level >= 4:
        cube("SM_lumber_yard_uninstalled_motor", collection, (0.64, 0.92, 0.26), (0.36, 0.28, 0.22), MATS["metal_worn"], rot=(0, 0, math.radians(-10)))
    sphere("SM_lumber_yard_construction_dust", collection, (0.15, -0.56, 0.32), (0.34, 0.18, 0.1), MATS["dust"], segments=14)


def add_level_state(level, state, offset):
    collection_name = f"lumber_yard_l{level:02d}_{state}"
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    before = set(bpy.data.objects)
    add_base(collection, level, state == "damaged")
    add_shed(collection, level, state)
    add_saw_line(collection, level, state)
    add_fuel_and_crane(collection, level, state)
    add_logs(collection, level, state == "damaged")
    add_premium_rack(collection, level, state)
    add_props(collection, level, state)
    if state == "construction":
        add_construction_overlay(collection, level)
    for obj in set(bpy.data.objects) - before:
        if obj.type == "MESH":
            obj.location.x += offset[0]
            obj.location.y += offset[1]
    return collection


def add_lighting_and_camera():
    import importlib.util
    spec = importlib.util.spec_from_file_location("housing_camera", Path(__file__).with_name("regenerate_early_housing.py"))
    housing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(housing)
    housing.setup_camera(bpy.context.scene)
    bpy.context.scene.camera.data.ortho_scale *= 3.65 / 3.6


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = SPRITE_SIZE[0]
    scene.render.resolution_y = SPRITE_SIZE[1]
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def write_asset_notes():
    note = bpy.data.texts.new("lumber_yard_asset_notes")
    note.write(
        "Real City lumber_yard models, levels 1-13, states active/construction/damaged. "
        "Runtime id kept as lumber_yard to match shared/catalog/buildings.ts; docs/buildings/industry/sawmill-yard.md currently also mentions sawmill_yard. "
        "Art direction: docs/visual-style-guide.md, bright fantasy stylized mid-poly, not primitive low-poly. "
        "Progression: manual timber yard -> framed saw -> fuel mechanization -> industrial feed line -> premium/rune-calibrated sawmill. "
        "Construction states are unfinished structures with missing roof/mechanism parts. Damaged states preserve the silhouette with collapsed roof marks, cracked pads, broken feed rails, smoke and char. "
        "No Gnomgrad-specific names, exact forms, UI, characters, or copyrighted assets were copied."
    )


def hide_all_model_collections():
    for collection in bpy.data.collections:
        if collection.name.startswith("lumber_yard_l"):
            collection.hide_render = True
            collection.hide_viewport = True


def prepare_collection_for_export(collection):
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in collection.all_objects:
        if obj.type == "MESH":
            obj.select_set(True)
            selected.append(obj)
    return selected


def export_glb():
    try:
        bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB")
        return True
    except Exception as exc:
        print(f"GLB export skipped: {exc}")
        return False


def export_state_glbs():
    exported = []
    for level in LEVELS:
        for state in STATES:
            collection_name = f"lumber_yard_l{level:02d}_{state}"
            collection = bpy.data.collections.get(collection_name)
            if collection is None:
                print(f"State export skipped, missing collection: {collection_name}")
                continue
            collection.hide_render = False
            collection.hide_viewport = False
            prepare_collection_for_export(collection)
            filepath = OUT_DIR / STATE_GLB_TEMPLATE.format(level=level, state=state)
            try:
                bpy.ops.export_scene.gltf(filepath=str(filepath), export_format="GLB", use_selection=True)
                exported.append(filepath)
                print(f"Exported {filepath.name}", flush=True)
            except Exception as exc:
                print(f"State GLB export skipped for {collection_name}: {exc}")
    return exported


def export_collection_glb(collection, level, state):
    prepare_collection_for_export(collection)
    filepath = OUT_DIR / STATE_GLB_TEMPLATE.format(level=level, state=state)
    bpy.ops.export_scene.gltf(filepath=str(filepath), export_format="GLB", use_selection=True)
    print(f"Exported {filepath.name}", flush=True)
    return filepath


def render_collection_png(level, state):
    path = OUT_DIR / STATE_PNG_TEMPLATE.format(level=level, state=state)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {path.name}", flush=True)
    return path


def render_state_pngs():
    rendered = []
    for level in LEVELS:
        for state in STATES:
            hide_all_model_collections()
            collection_name = f"lumber_yard_l{level:02d}_{state}"
            collection = bpy.data.collections[collection_name]
            collection.hide_render = False
            collection.hide_viewport = False
            rendered.append(render_collection_png(level, state))
    return rendered


def mesh_triangle_count(collection):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            total += sum(len(poly.vertices) - 2 for poly in mesh.polygons)
        finally:
            evaluated.to_mesh_clear()
    return total


def alpha_bounds(path):
    try:
        from PIL import Image
    except Exception:
        return None
    with Image.open(path) as image:
        return image.getchannel("A").getbbox()


def world_bounds(collection):
    points = []
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    if not points:
        return None
    return {
        "min": [round(min(getattr(p, axis) for p in points), 3) for axis in ("x", "y", "z")],
        "max": [round(max(getattr(p, axis) for p in points), 3) for axis in ("x", "y", "z")],
    }


def write_report():
    report = {}
    for level in LEVELS:
        for state in STATES:
            name = f"lumber_yard_l{level:02d}_{state}"
            collection = bpy.data.collections[name]
            png_path = OUT_DIR / f"{name}.png"
            report[name] = {
                "level": level,
                "state": state,
                "triangles": mesh_triangle_count(collection),
                "style": "bright fantasy stylized mid-poly",
                "tier": tier(level),
                "world_bounds": world_bounds(collection),
                "alpha_bounds": alpha_bounds(png_path),
            }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def report_entry(collection, level, state, png_path):
    return {
        "level": level,
        "state": state,
        "triangles": mesh_triangle_count(collection),
        "style": "bright fantasy stylized mid-poly",
        "tier": tier(level),
        "world_bounds": world_bounds(collection),
        "alpha_bounds": alpha_bounds(png_path),
    }


def write_report_data(report):
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("sawmill_pipeline", Path(__file__).with_name("regenerate_sawmills.py"))
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    pipeline.main(OUT_DIR)


if __name__ == "__main__":
    main()
