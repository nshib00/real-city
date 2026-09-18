import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "resources" / "icons"
BLEND_PATH = OUT_DIR / "resource_icons.blend"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CONTACT_SHEET_PATH = OUT_DIR / "resource_icons_contact_sheet.png"
SIZE = 256
ICON_ORTHO_SCALE = 1.55
CONTACT_SHEET_ORTHO_SCALE = 16.0
STYLE_DESCRIPTION = (
    "transparent close-up bright fantasy stylized mid-poly isometric resource icons "
    "without bottom backplates, following docs/visual-style-guide.md"
)

RESOURCES = [
    {"id": "coins", "name": "Монеты", "category": "basic"},
    {"id": "population", "name": "Жители", "category": "basic"},
    {"id": "aeolian-crystal", "name": "Эолийские кристаллы", "category": "basic"},
    {"id": "wood", "name": "Древесина", "category": "raw"},
    {"id": "stone", "name": "Камень", "category": "raw"},
    {"id": "clay", "name": "Глина", "category": "raw"},
    {"id": "sand", "name": "Песок", "category": "raw"},
    {"id": "coal", "name": "Уголь", "category": "raw"},
    {"id": "iron_ore", "name": "Железная руда", "category": "raw"},
    {"id": "copper", "name": "Медь", "category": "raw"},
    {"id": "resin", "name": "Смола", "category": "raw"},
    {"id": "windleaf", "name": "Ветролист", "category": "raw"},
    {"id": "herbs", "name": "Травы", "category": "raw"},
    {"id": "mushrooms", "name": "Грибы", "category": "raw"},
    {"id": "seeds", "name": "Семена", "category": "raw"},
    {"id": "brick", "name": "Кирпич", "category": "crafted"},
    {"id": "stone_block", "name": "Каменный блок", "category": "crafted"},
    {"id": "metal", "name": "Металл", "category": "crafted"},
    {"id": "iron", "name": "Железо", "category": "crafted"},
    {"id": "steel", "name": "Сталь", "category": "crafted"},
    {"id": "glass", "name": "Стекло", "category": "crafted"},
    {"id": "planks", "name": "Доски", "category": "crafted"},
    {"id": "cement", "name": "Цемент", "category": "crafted"},
    {"id": "concrete", "name": "Бетон", "category": "crafted"},
    {"id": "fabric", "name": "Ткань", "category": "crafted"},
    {"id": "electronics", "name": "Электроника", "category": "crafted"},
    {"id": "sulfur", "name": "Сера", "category": "crafted"},
    {"id": "explosives", "name": "Взрывчатка", "category": "crafted"},
    {"id": "oil", "name": "Нефть", "category": "fuel"},
    {"id": "fuel", "name": "Бензин", "category": "fuel"},
    {"id": "super-seeds", "name": "Супер-семена", "category": "rare"},
    {"id": "super-fiber", "name": "Супер-волокно", "category": "rare"},
    {"id": "super-mushrooms", "name": "Супер-грибы", "category": "rare"},
    {"id": "elderwood-heart", "name": "Сердцевина древня", "category": "rare"},
]

CATEGORY_COLORS = {
    "basic": (0.93, 0.68, 0.25, 1),
    "raw": (0.38, 0.64, 0.36, 1),
    "crafted": (0.36, 0.58, 0.72, 1),
    "fuel": (0.76, 0.42, 0.16, 1),
    "rare": (0.62, 0.32, 0.86, 1),
}

MATS = {}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)


def set_input(node, name, value):
    if node and name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color, roughness=0.68, metallic=0.0, alpha=1.0, emission=None, emission_strength=0.0):
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


def make_materials():
    global MATS
    MATS = {
        "rim_basic": mat("rim_basic", CATEGORY_COLORS["basic"], 0.38, 0.28),
        "rim_raw": mat("rim_raw", CATEGORY_COLORS["raw"], 0.5),
        "rim_crafted": mat("rim_crafted", CATEGORY_COLORS["crafted"], 0.46, 0.1),
        "rim_fuel": mat("rim_fuel", CATEGORY_COLORS["fuel"], 0.44),
        "rim_rare": mat("rim_rare", CATEGORY_COLORS["rare"], 0.34, 0.05, emission=(0.42, 0.18, 0.78, 1), emission_strength=0.12),
        "backplate": mat("backplate", (0.16, 0.2, 0.17, 1), 0.82),
        "shadow": mat("shadow", (0.05, 0.06, 0.05, 1), 0.9),
        "gold": mat("gold", (1.0, 0.72, 0.22, 1), 0.32, 0.45),
        "gold_dark": mat("gold_dark", (0.72, 0.42, 0.08, 1), 0.46, 0.35),
        "skin": mat("skin", (0.86, 0.58, 0.38, 1)),
        "cloth": mat("cloth", (0.18, 0.58, 0.55, 1)),
        "wood": mat("wood", (0.62, 0.34, 0.14, 1)),
        "wood_dark": mat("wood_dark", (0.32, 0.15, 0.06, 1)),
        "wood_cut": mat("wood_cut", (0.93, 0.68, 0.36, 1)),
        "wood_highlight": mat("wood_highlight", (1.0, 0.78, 0.42, 1)),
        "bark": mat("bark", (0.36, 0.18, 0.08, 1)),
        "stone": mat("stone", (0.58, 0.62, 0.62, 1)),
        "stone_light": mat("stone_light", (0.78, 0.82, 0.78, 1)),
        "stone_dark": mat("stone_dark", (0.32, 0.36, 0.38, 1)),
        "clay": mat("clay", (0.72, 0.34, 0.2, 1)),
        "clay_light": mat("clay_light", (0.94, 0.5, 0.3, 1)),
        "sand": mat("sand", (0.9, 0.76, 0.46, 1)),
        "sand_light": mat("sand_light", (1.0, 0.9, 0.58, 1)),
        "coal": mat("coal", (0.08, 0.09, 0.1, 1), 0.82),
        "coal_light": mat("coal_light", (0.2, 0.23, 0.26, 1), 0.72),
        "iron_ore": mat("iron_ore", (0.72, 0.36, 0.26, 1), 0.54, 0.12),
        "ore_glow": mat("ore_glow", (1.0, 0.55, 0.28, 1), 0.36, 0.1, emission=(0.8, 0.22, 0.06, 1), emission_strength=0.1),
        "copper": mat("copper", (0.95, 0.48, 0.18, 1), 0.38, 0.35),
        "copper_light": mat("copper_light", (1.0, 0.68, 0.32, 1), 0.32, 0.4),
        "resin": mat("resin", (0.95, 0.52, 0.12, 1), 0.22, 0, 0.88, emission=(0.85, 0.32, 0.04, 1), emission_strength=0.18),
        "leaf": mat("leaf", (0.25, 0.78, 0.3, 1)),
        "leaf_light": mat("leaf_light", (0.52, 0.94, 0.42, 1)),
        "leaf_dark": mat("leaf_dark", (0.1, 0.42, 0.18, 1)),
        "mushroom_cap": mat("mushroom_cap", (0.86, 0.22, 0.18, 1)),
        "mushroom_spot": mat("mushroom_spot", (0.96, 0.88, 0.68, 1)),
        "brick": mat("brick", (0.76, 0.34, 0.22, 1)),
        "mortar": mat("mortar", (0.86, 0.72, 0.56, 1)),
        "metal": mat("metal", (0.62, 0.68, 0.68, 1), 0.34, 0.46),
        "iron": mat("iron", (0.42, 0.48, 0.5, 1), 0.38, 0.5),
        "steel": mat("steel", (0.82, 0.9, 0.92, 1), 0.28, 0.58),
        "glass": mat("glass", (0.52, 0.86, 1.0, 1), 0.18, 0, 0.62, emission=(0.28, 0.6, 0.92, 1), emission_strength=0.1),
        "cement": mat("cement", (0.76, 0.72, 0.62, 1)),
        "fabric": mat("fabric", (0.78, 0.22, 0.52, 1)),
        "fabric_light": mat("fabric_light", (1.0, 0.42, 0.72, 1)),
        "rune": mat("rune", (0.16, 0.92, 1.0, 1), 0.25, 0, 1, emission=(0.08, 0.7, 1.0, 1), emission_strength=0.65),
        "sulfur": mat("sulfur", (0.95, 0.88, 0.18, 1), 0.42, 0, 1, emission=(0.75, 0.58, 0.08, 1), emission_strength=0.08),
        "powder": mat("powder", (0.18, 0.16, 0.14, 1)),
        "oil": mat("oil", (0.04, 0.04, 0.06, 1), 0.28, 0, 0.92),
        "fuel": mat("fuel", (0.95, 0.42, 0.12, 1), 0.34),
        "fuel_light": mat("fuel_light", (1.0, 0.72, 0.22, 1), 0.28, 0, 1, emission=(1.0, 0.45, 0.08, 1), emission_strength=0.12),
        "amethyst": mat("amethyst", (0.62, 0.32, 0.9, 1), 0.25, 0, 0.82, emission=(0.5, 0.2, 1, 1), emission_strength=0.28),
        "elderwood": mat("elderwood", (0.48, 0.2, 0.08, 1), 0.62),
        "heart_glow": mat("heart_glow", (1.0, 0.58, 0.18, 1), 0.28, 0, 0.88, emission=(1.0, 0.38, 0.08, 1), emission_strength=0.4),
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


def stylize_mesh(obj, bevel=0.025, segments=2, smooth=True):
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    if bevel > 0:
        mod = obj.modifiers.new(f"{obj.name}_soft_bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.affect = "EDGES"
        mod.profile = 0.5
    try:
        normal = obj.modifiers.new(f"{obj.name}_weighted_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
    except Exception:
        pass
    return obj


def cube(name, collection, loc, scale, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    stylize_mesh(obj, bevel=min(scale) * 0.08, segments=2, smooth=False)
    return link_to(collection, obj)


def cylinder(name, collection, loc, radius, depth, material, vertices=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    stylize_mesh(obj, bevel=radius * 0.08, segments=2, smooth=True)
    return link_to(collection, obj)


def sphere(name, collection, loc, scale, material, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=12, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    stylize_mesh(obj, bevel=0, smooth=True)
    return link_to(collection, obj)


def cone(name, collection, loc, radius1, radius2, depth, material, vertices=6, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    stylize_mesh(obj, bevel=radius1 * 0.035, segments=1, smooth=False)
    return link_to(collection, obj)


def add_leaf(name, collection, loc, scale, material, rot=(0, 0, 0)):
    verts = [(0, 0.72, 0), (0.42, 0, 0), (0, -0.72, 0), (-0.42, 0, 0)]
    faces = [(0, 1, 2, 3)]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    solid = obj.modifiers.new(f"{name}_leaf_thickness", "SOLIDIFY")
    solid.thickness = 0.018
    bevel = obj.modifiers.new(f"{name}_leaf_soft_edge", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 1
    collection.objects.link(obj)
    return obj


def add_shard(name, collection, loc, height, material, rot=(0, 0, 0), radius=0.24):
    return cone(name, collection, loc, radius, 0.04, height, material, vertices=6, rot=rot)


def add_highlight(name, collection, loc, scale, material, rot=(0, 0, 0)):
    return cube(name, collection, loc, scale, material, rot)


def add_backplate(collection, resource):
    category = resource["category"]
    cylinder("icon_shadow", collection, (0.08, -0.08, -0.12), 1.18, 0.1, MATS["shadow"], vertices=48)
    cylinder("icon_backplate", collection, (0, 0, -0.08), 1.14, 0.12, MATS["backplate"], vertices=48)
    cylinder("icon_category_rim", collection, (0, 0, 0.0), 1.2, 0.08, MATS[f"rim_{category}"], vertices=48)


def build_coins(collection):
    for i, (x, y) in enumerate([(-0.3, 0.0), (0.08, 0.1), (0.32, -0.14), (-0.02, -0.2)]):
        cylinder(f"coin_{i}", collection, (x, y, 0.18 + i * 0.07), 0.32, 0.12, MATS["gold"], vertices=32)
        cylinder(f"coin_face_{i}", collection, (x, y, 0.255 + i * 0.07), 0.23, 0.025, MATS["gold_dark"], vertices=32)
        add_highlight(f"coin_glint_{i}", collection, (x - 0.04, y - 0.1, 0.28 + i * 0.07), (0.2, 0.035, 0.018), MATS["wood_highlight"], rot=(0, 0, math.radians(18)))


def build_population(collection):
    for i, (x, y, s) in enumerate([(-0.32, -0.02, 0.86), (0.28, -0.02, 0.76), (0.0, 0.16, 1.0)]):
        sphere(f"villager_head_{i}", collection, (x, y, 0.52 * s), (0.16 * s, 0.16 * s, 0.18 * s), MATS["skin"])
        cube(f"villager_body_{i}", collection, (x, y, 0.2 * s), (0.26 * s, 0.18 * s, 0.36 * s), MATS["cloth"])
        cube(f"villager_sash_{i}", collection, (x, y - 0.095 * s, 0.27 * s), (0.28 * s, 0.035 * s, 0.065 * s), MATS["fabric_light"], rot=(0, 0, math.radians(-6)))
        cylinder(f"villager_cap_{i}", collection, (x, y, 0.68 * s), 0.13 * s, 0.055 * s, MATS["wood"], vertices=18)


def build_crystal(collection, material="amethyst"):
    for i, (x, y, h, r) in enumerate([(-0.3, -0.08, 0.75, -12), (0, 0.05, 1.05, 0), (0.32, -0.02, 0.82, 14)]):
        add_shard(f"crystal_{i}", collection, (x, y, 0.38), h, MATS[material], rot=(0, math.radians(r), 0), radius=0.22)
        add_highlight(f"crystal_edge_{i}", collection, (x - 0.035, y - 0.045, 0.58), (0.035, 0.025, h * 0.42), MATS["rune"] if material == "amethyst" else MATS[material], rot=(0, math.radians(r), math.radians(8)))


def build_wood(collection):
    for i, y in enumerate([-0.22, 0.08, 0.36]):
        cylinder(f"log_{i}", collection, (0, y, 0.28 + i * 0.02), 0.16, 1.05, MATS["bark"], vertices=18, rot=(0, math.radians(90), math.radians(12)))
        cylinder(f"log_cut_{i}", collection, (-0.52, y, 0.28 + i * 0.02), 0.162, 0.025, MATS["wood_cut"], vertices=18, rot=(0, math.radians(90), math.radians(12)))
        cylinder(f"log_ring_{i}", collection, (-0.545, y, 0.28 + i * 0.02), 0.09, 0.027, MATS["wood_highlight"], vertices=18, rot=(0, math.radians(90), math.radians(12)))
    cube("log_binding", collection, (0.04, 0.08, 0.5), (0.08, 0.72, 0.08), MATS["fabric"], rot=(0, 0, math.radians(12)))
    add_leaf("log_sprout", collection, (0.45, 0.34, 0.5), (0.18, 0.18, 0.18), MATS["leaf_light"], rot=(math.radians(70), 0, math.radians(34)))


def build_rocks(collection, material="stone"):
    light = {
        "stone": "stone_light",
        "clay": "clay_light",
        "sand": "sand_light",
        "coal": "coal_light",
        "iron_ore": "ore_glow",
    }.get(material, material)
    for i, (x, y, sx, sy, sz) in enumerate([(-0.32, 0, 0.38, 0.28, 0.26), (0.18, 0.12, 0.48, 0.32, 0.34), (0.36, -0.24, 0.3, 0.22, 0.2)]):
        sphere(f"rock_{i}", collection, (x, y, 0.22), (sx, sy, sz), MATS[material], segments=12)
        add_highlight(f"rock_facet_{i}", collection, (x - sx * 0.18, y - sy * 0.22, 0.32), (sx * 0.42, 0.025, 0.035), MATS[light], rot=(0, 0, math.radians(-14 + i * 9)))


def build_ingots(collection, material):
    light = "copper_light" if material == "copper" else "stone_light"
    for i, (x, y) in enumerate([(-0.28, -0.04), (0.16, 0.08), (0.34, -0.2)]):
        cube(f"ingot_{i}", collection, (x, y, 0.24 + i * 0.04), (0.62, 0.28, 0.16), MATS[material], rot=(0, 0, math.radians(-12 + i * 9)))
        add_highlight(f"ingot_bevel_glint_{i}", collection, (x - 0.04, y - 0.11, 0.34 + i * 0.04), (0.36, 0.035, 0.018), MATS[light], rot=(0, 0, math.radians(-12 + i * 9)))


def build_leaf_cluster(collection, material="leaf", glow=False):
    for i, angle in enumerate([-42, 0, 42]):
        add_leaf(f"leaf_{i}", collection, (0, -0.02, 0.34 + i * 0.03), (0.62, 0.62, 0.62), MATS[material], rot=(math.radians(70), 0, math.radians(angle)))
        cylinder(f"leaf_vein_{i}", collection, (math.sin(math.radians(angle)) * 0.05, -0.02, 0.36 + i * 0.03), 0.012, 0.56, MATS["leaf_light"], vertices=8, rot=(math.radians(70), 0, math.radians(angle)))
    cube("leaf_stem", collection, (0, -0.16, 0.22), (0.08, 0.66, 0.08), MATS["leaf_dark"], rot=(0, 0, math.radians(-10)))
    if glow:
        sphere("leaf_glow_seed", collection, (0.12, 0.18, 0.54), (0.1, 0.1, 0.1), MATS["rune"])
        add_highlight("wind_ribbon", collection, (-0.16, 0.18, 0.58), (0.44, 0.035, 0.025), MATS["rune"], rot=(0, 0, math.radians(-28)))


def build_mushrooms(collection, super_variant=False):
    cap_mat = MATS["amethyst"] if super_variant else MATS["mushroom_cap"]
    for i, (x, y, s) in enumerate([(-0.25, -0.05, 0.85), (0.2, 0.08, 1.05), (0.43, -0.18, 0.65)]):
        cylinder(f"mushroom_stem_{i}", collection, (x, y, 0.2 * s), 0.08 * s, 0.34 * s, MATS["mushroom_spot"], vertices=12)
        sphere(f"mushroom_cap_{i}", collection, (x, y, 0.42 * s), (0.22 * s, 0.18 * s, 0.12 * s), cap_mat)
        sphere(f"mushroom_spot_{i}", collection, (x - 0.04, y - 0.02, 0.5 * s), (0.035 * s, 0.02 * s, 0.018 * s), MATS["mushroom_spot"])


def build_seed_cluster(collection, super_variant=False):
    seed_mat = MATS["rune"] if super_variant else MATS["sand"]
    for i, angle in enumerate(range(0, 360, 60)):
        x = math.cos(math.radians(angle)) * 0.28
        y = math.sin(math.radians(angle)) * 0.18
        sphere(f"seed_{i}", collection, (x, y, 0.26), (0.11, 0.07, 0.06), seed_mat, segments=12)
    sphere("seed_center", collection, (0, 0, 0.32), (0.13, 0.09, 0.08), seed_mat, segments=12)


def build_bricks(collection):
    for row, y in enumerate([-0.18, 0.08]):
        for col, x in enumerate([-0.32, 0.18]):
            cube(f"brick_{row}_{col}", collection, (x + row * 0.1, y, 0.22 + row * 0.16), (0.44, 0.26, 0.16), MATS["brick"])
            cube(f"mortar_{row}_{col}", collection, (x + row * 0.1, y - 0.145, 0.31 + row * 0.16), (0.46, 0.03, 0.035), MATS["mortar"])
            add_highlight(f"brick_edge_{row}_{col}", collection, (x + row * 0.1 - 0.08, y - 0.08, 0.315 + row * 0.16), (0.2, 0.025, 0.018), MATS["clay_light"], rot=(0, 0, math.radians(2)))


def build_planks(collection):
    for i, y in enumerate([-0.22, 0.0, 0.22]):
        cube(f"plank_{i}", collection, (0, y, 0.22 + i * 0.035), (0.88, 0.16, 0.12), MATS["wood_cut"], rot=(0, 0, math.radians(-9)))
        add_highlight(f"plank_grain_{i}", collection, (-0.04, y - 0.045, 0.295 + i * 0.035), (0.58, 0.02, 0.016), MATS["wood_highlight"], rot=(0, 0, math.radians(-9)))
    cube("plank_tie", collection, (0.12, 0, 0.38), (0.08, 0.64, 0.06), MATS["fabric"], rot=(0, 0, math.radians(-9)))


def build_sack(collection, material="cement"):
    sphere("sack_body", collection, (0, 0, 0.28), (0.46, 0.34, 0.34), MATS[material], segments=16)
    cylinder("sack_tie", collection, (0, 0.03, 0.6), 0.16, 0.09, MATS["wood"], vertices=12)
    add_highlight("sack_fold", collection, (-0.12, -0.21, 0.34), (0.32, 0.026, 0.018), MATS["stone_light"], rot=(0, 0, math.radians(12)))


def build_flask(collection, liquid_material):
    cylinder("flask_neck", collection, (0, 0.05, 0.62), 0.12, 0.36, MATS["glass"], vertices=18)
    sphere("flask_body", collection, (0, -0.04, 0.28), (0.36, 0.32, 0.28), MATS["glass"], segments=18)
    sphere("flask_liquid", collection, (0, -0.04, 0.18), (0.31, 0.28, 0.15), liquid_material, segments=18)
    cylinder("flask_cork", collection, (0, 0.05, 0.84), 0.13, 0.1, MATS["wood_dark"], vertices=18)
    add_highlight("flask_glint", collection, (-0.12, -0.25, 0.46), (0.055, 0.025, 0.26), MATS["rune"], rot=(0, 0, math.radians(-18)))


def build_electronics(collection):
    cube("rune_plate", collection, (0, 0, 0.24), (0.7, 0.52, 0.12), MATS["metal"], rot=(0, 0, math.radians(6)))
    cube("rune_plate_frame", collection, (0, 0, 0.34), (0.8, 0.08, 0.07), MATS["steel"], rot=(0, 0, math.radians(6)))
    for i, x in enumerate([-0.22, 0, 0.22]):
        cube(f"rune_line_{i}", collection, (x, -0.02, 0.33), (0.05, 0.48, 0.025), MATS["rune"])
    sphere("rune_core", collection, (0, 0, 0.44), (0.13, 0.13, 0.08), MATS["rune"])
    cylinder("small_lens", collection, (0.32, 0.18, 0.4), 0.085, 0.06, MATS["glass"], vertices=18)


def build_explosives(collection):
    cylinder("powder_keg", collection, (0, 0, 0.28), 0.34, 0.56, MATS["powder"], vertices=18)
    cube("powder_band_top", collection, (0, 0, 0.52), (0.66, 0.08, 0.08), MATS["metal"])
    cube("powder_band_bottom", collection, (0, 0, 0.18), (0.66, 0.08, 0.08), MATS["metal"])
    cylinder("fuse", collection, (0.28, 0.08, 0.66), 0.025, 0.38, MATS["sulfur"], vertices=8, rot=(math.radians(35), 0, math.radians(25)))
    sphere("fuse_spark", collection, (0.38, 0.18, 0.78), (0.055, 0.055, 0.055), MATS["fuel_light"], segments=12)


def build_fuel_can(collection):
    cube("fuel_can", collection, (0, 0, 0.32), (0.58, 0.42, 0.55), MATS["fuel"], rot=(0, 0, math.radians(-5)))
    add_highlight("fuel_can_label", collection, (-0.02, -0.22, 0.35), (0.3, 0.035, 0.18), MATS["fuel_light"], rot=(0, 0, math.radians(-5)))
    cylinder("fuel_cap", collection, (0.24, 0.05, 0.68), 0.09, 0.12, MATS["metal"], vertices=12)
    cylinder("fuel_handle", collection, (-0.16, 0.0, 0.68), 0.16, 0.08, MATS["metal"], vertices=18)


def build_elderwood_heart(collection):
    cylinder("heart_branch", collection, (0, 0, 0.26), 0.24, 0.58, MATS["elderwood"], vertices=16, rot=(0, math.radians(90), math.radians(-12)))
    sphere("heart_core", collection, (0.02, 0, 0.38), (0.23, 0.2, 0.18), MATS["heart_glow"], segments=18)
    for i, angle in enumerate([70, 120, 250]):
        add_leaf(f"heart_leaf_{i}", collection, (math.cos(math.radians(angle)) * 0.28, math.sin(math.radians(angle)) * 0.2, 0.52), (0.22, 0.22, 0.22), MATS["leaf"], rot=(math.radians(75), 0, math.radians(angle)))
    add_highlight("heart_wind_mark", collection, (-0.13, -0.1, 0.58), (0.32, 0.026, 0.022), MATS["fuel_light"], rot=(0, 0, math.radians(-24)))


def build_stone_block(collection):
    cube("stone_block", collection, (0, 0, 0.28), (0.7, 0.54, 0.42), MATS["stone"], rot=(0, 0, math.radians(6)))
    add_highlight("stone_block_face", collection, (-0.08, -0.22, 0.36), (0.38, 0.035, 0.12), MATS["stone_light"], rot=(0, 0, math.radians(6)))
    cube("stone_block_chip", collection, (0.26, 0.18, 0.52), (0.18, 0.1, 0.08), MATS["stone_dark"], rot=(0, 0, math.radians(14)))


def build_concrete(collection):
    cube("concrete_block", collection, (0, 0, 0.3), (0.72, 0.54, 0.44), MATS["stone_dark"], rot=(0, 0, math.radians(-7)))
    add_highlight("concrete_edge", collection, (-0.08, -0.22, 0.4), (0.42, 0.035, 0.12), MATS["stone"], rot=(0, 0, math.radians(-7)))
    cube("concrete_rebar", collection, (0.24, 0.2, 0.58), (0.38, 0.035, 0.035), MATS["iron"], rot=(0, 0, math.radians(-18)))


def build_fabric(collection):
    cylinder("fabric_roll", collection, (0, 0, 0.32), 0.28, 0.78, MATS["fabric"], vertices=24, rot=(0, math.radians(90), math.radians(-10)))
    cylinder("fabric_inner", collection, (-0.39, -0.07, 0.32), 0.17, 0.035, MATS["fabric_light"], vertices=24, rot=(0, math.radians(90), math.radians(-10)))
    add_highlight("fabric_fold", collection, (0.06, -0.26, 0.44), (0.58, 0.025, 0.035), MATS["fabric_light"], rot=(0, 0, math.radians(-10)))


BUILDERS = {
    "coins": build_coins,
    "population": build_population,
    "aeolian-crystal": lambda c: build_crystal(c, "amethyst"),
    "wood": build_wood,
    "stone": lambda c: build_rocks(c, "stone"),
    "clay": lambda c: build_rocks(c, "clay"),
    "sand": lambda c: build_rocks(c, "sand"),
    "coal": lambda c: build_rocks(c, "coal"),
    "iron_ore": lambda c: build_rocks(c, "iron_ore"),
    "copper": lambda c: build_ingots(c, "copper"),
    "resin": lambda c: build_flask(c, MATS["resin"]),
    "windleaf": lambda c: build_leaf_cluster(c, "leaf", True),
    "herbs": lambda c: build_leaf_cluster(c),
    "mushrooms": build_mushrooms,
    "seeds": build_seed_cluster,
    "brick": build_bricks,
    "stone_block": build_stone_block,
    "metal": lambda c: build_ingots(c, "metal"),
    "iron": lambda c: build_ingots(c, "iron"),
    "steel": lambda c: build_ingots(c, "steel"),
    "glass": lambda c: build_crystal(c, "glass"),
    "planks": build_planks,
    "cement": lambda c: build_sack(c, "cement"),
    "concrete": build_concrete,
    "fabric": build_fabric,
    "electronics": build_electronics,
    "sulfur": lambda c: build_crystal(c, "sulfur"),
    "explosives": build_explosives,
    "oil": lambda c: build_flask(c, MATS["oil"]),
    "fuel": build_fuel_can,
    "super-seeds": lambda c: build_seed_cluster(c, True),
    "super-fiber": lambda c: build_leaf_cluster(c, "leaf", True),
    "super-mushrooms": lambda c: build_mushrooms(c, True),
    "elderwood-heart": build_elderwood_heart,
}


def setup_camera():
    bpy.ops.object.light_add(type="AREA", location=(-2.8, -3.2, 5.0))
    key = bpy.context.object
    key.name = "resource_icon_key_light"
    key.data.energy = 460
    key.data.size = 4.0
    bpy.ops.object.light_add(type="POINT", location=(2.4, 1.6, 2.2))
    fill = bpy.context.object
    fill.name = "resource_icon_warm_fill"
    fill.data.energy = 90
    bpy.ops.object.camera_add(location=(0, -4.8, 3.25), rotation=(math.radians(58), 0, 0))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ICON_ORTHO_SCALE
    bpy.context.scene.camera = camera


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 80
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def build_icon(resource):
    collection = bpy.data.collections.new(f"resource_icon_{resource['id']}")
    bpy.context.scene.collection.children.link(collection)
    BUILDERS[resource["id"]](collection)
    return collection


def hide_all_icon_collections():
    for collection in bpy.data.collections:
        if collection.name.startswith("resource_icon_"):
            collection.hide_render = True
            collection.hide_viewport = True


def render_icon(resource):
    hide_all_icon_collections()
    collection = bpy.data.collections[f"resource_icon_{resource['id']}"]
    collection.hide_render = False
    collection.hide_viewport = False
    bpy.context.scene.camera.data.ortho_scale = ICON_ORTHO_SCALE
    bpy.context.scene.camera.location = (0, -4.8, 3.25)
    bpy.context.scene.camera.rotation_euler = (math.radians(58), 0, 0)
    bpy.context.scene.render.resolution_x = SIZE
    bpy.context.scene.render.resolution_y = SIZE
    bpy.context.scene.render.filepath = str(OUT_DIR / f"{resource['id']}.png")
    bpy.ops.render.render(write_still=True)


def render_contact_sheet():
    hide_all_icon_collections()
    for index, resource in enumerate(RESOURCES):
        source = bpy.data.collections[f"resource_icon_{resource['id']}"]
        row = index // 6
        col = index % 6
        offset_x = (col - 2.5) * 2.75
        offset_y = (2.5 - row) * 2.75
        source.hide_render = False
        source.hide_viewport = False
        for obj in source.objects:
            obj.location.x += offset_x
            obj.location.y += offset_y
    bpy.context.scene.camera.location = (0, -13.0, 10.8)
    bpy.context.scene.camera.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.scene.camera.data.ortho_scale = CONTACT_SHEET_ORTHO_SCALE
    bpy.context.scene.render.resolution_x = 1536
    bpy.context.scene.render.resolution_y = 1536
    bpy.context.scene.render.filepath = str(CONTACT_SHEET_PATH)
    bpy.ops.render.render(write_still=True)


def write_manifest():
    manifest = {
        "style": STYLE_DESCRIPTION,
        "size": SIZE,
        "resources": [{"id": item["id"], "name": item["name"], "category": item["category"], "file": f"{item['id']}.png"} for item in RESOURCES],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("resource_pipeline", Path(__file__).with_name("regenerate_resource_models.py"))
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    pipeline.main(OUT_DIR)


if __name__ == "__main__":
    main()
