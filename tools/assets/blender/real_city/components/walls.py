"""Wall, foundation and defensive detail components."""

from __future__ import annotations

import math

from .. import geometry
from .common import add_stone_courses, mat

WALL_MATERIAL_PROFILES = {
    "wood": {"body": "wood_beam", "cap": "wood_pale", "spike": "wood_dark"},
    "elite_wood": {"body": "elite_plank", "cap": "elite_plank_highlight", "spike": "wood_dark"},
    "stone": {"body": "stone_light", "cap": "stone_shadow", "spike": "stone_shadow"},
    "metal": {"body": "metal_worn", "cap": "steel_light", "spike": "metal_worn"},
    "gold": {"body": "roof_gold", "cap": "roof_gold", "spike": "roof_gold"},
    "steel": {"body": "steel_light", "cap": "metal_worn", "spike": "dark_metal"},
}

WALL_DECOR_MATERIALS = {
    "wood": "wood_pale",
    "stone": "stone_light",
    "metal": "metal_worn",
    "steel": "steel_light",
    "gold": "roof_gold",
    "elite_wood": "elite_plank_highlight",
    "white": "whitewash",
}


def add_plank_wall(name: str, collection, mats: dict, loc, size, *, planks=6, damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else "wood_pale"
    for index in range(planks):
        px = x - width / 2 + (index + 0.5) * width / planks
        geometry.box(f"{name}_plank_{index:02d}", collection, (px, y, z), (width / planks * 0.78, depth, height), mat(mats, role, "wood_pale"), bevel=0.012)
    geometry.box(f"{name}_top_beam", collection, (x, y, z + height * 0.52), (width + 0.08, depth * 1.10, 0.07), mat(mats, "wood_beam", "wood_dark"), bevel=0.010)


def add_board_clad_wall(name: str, collection, mats: dict, loc, size, *, planks=7, orientation="vertical", trim=True, damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else "wood_pale"
    if orientation == "horizontal":
        for index in range(planks):
            pz = z - height / 2 + (index + 0.5) * height / planks
            geometry.box(f"{name}_board_{index:02d}", collection, (x, y, pz), (width, depth, height / planks * 0.72), mat(mats, role, "wood_pale"), bevel=0.007)
    else:
        for index in range(planks):
            px = x - width / 2 + (index + 0.5) * width / planks
            geometry.box(f"{name}_board_{index:02d}", collection, (px, y, z), (width / planks * 0.72, depth, height), mat(mats, role, "wood_pale"), bevel=0.008)
    if trim:
        trim_mat = mat(mats, "wood_beam", "wood_dark")
        geometry.box(f"{name}_trim_top", collection, (x, y, z + height * 0.52), (width + 0.08, depth * 1.16, 0.065), trim_mat, bevel=0.007)
        geometry.box(f"{name}_trim_low", collection, (x, y, z - height * 0.48), (width + 0.05, depth * 1.12, 0.055), trim_mat, bevel=0.006)


def add_elite_board_wall(name: str, collection, mats: dict, loc, size, *, planks=7, orientation="vertical", damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else "elite_plank"
    highlight = mat(mats, "elite_plank_highlight", "wood_beam")
    add_board_clad_wall(name, collection, mats, loc, size, planks=planks, orientation=orientation, trim=True, damaged=damaged)
    for obj in collection.objects:
        if obj.name.startswith(f"{name}_board_"):
            obj.data.materials.clear()
            obj.data.materials.append(mat(mats, role, "wood_dark"))
    if orientation == "horizontal":
        for index in range(2):
            pz = z - height * 0.22 + index * height * 0.44
            geometry.box(f"{name}_elite_polished_inlay_{index:02d}", collection, (x, y - depth * 0.56, pz), (width * 0.78, depth * 0.24, 0.026), highlight, bevel=0.004)
    else:
        for index in range(3):
            px = x - width * 0.30 + index * width * 0.30
            geometry.box(f"{name}_elite_polished_inlay_{index:02d}", collection, (px, y - depth * 0.56, z), (0.030, depth * 0.24, height * 0.72), highlight, bevel=0.004)


def add_wood_house_wall_set(name: str, collection, mats: dict, *, width: float, depth: float, height: float, z_base=0.0, damaged=False):
    center_z = z_base + height / 2
    add_board_clad_wall(f"{name}_front", collection, mats, (0, -depth / 2 - 0.025, center_z), (width, 0.060, height), planks=7, damaged=damaged)
    add_board_clad_wall(f"{name}_back", collection, mats, (0, depth / 2 + 0.025, center_z), (width, 0.060, height), planks=7, orientation="horizontal", trim=False, damaged=damaged)
    add_board_clad_wall(f"{name}_left", collection, mats, (-width / 2 - 0.025, 0, center_z), (depth, 0.060, height), planks=6, orientation="horizontal", trim=False, damaged=damaged)
    for obj in [item for item in collection.objects if item.name.startswith(f"{name}_left_")]:
        obj.rotation_euler[2] = math.radians(90)
    add_board_clad_wall(f"{name}_right", collection, mats, (width / 2 + 0.025, 0, center_z), (depth, 0.060, height), planks=6, orientation="horizontal", trim=False, damaged=damaged)
    for obj in [item for item in collection.objects if item.name.startswith(f"{name}_right_")]:
        obj.rotation_euler[2] = math.radians(90)


def add_stone_block_wall(name: str, collection, mats: dict, loc, size, *, rows=3, damaged=False):
    x, y, z = loc
    width, depth, height = size
    geometry.box(f"{name}_stone_wall_core", collection, loc, size, mat(mats, "damage_char", "stone_shadow") if damaged else mat(mats, "stone_light", "stone_shadow"), bevel=0.030)
    add_stone_courses(name, collection, mats, width, depth, z - height * 0.45, rows, damaged=damaged)
    material = mat(mats, "damage_char", "stone_shadow") if damaged else mat(mats, "stone_block", "stone_light")
    for row in range(rows):
        count = 4 + row % 2
        for index in range(count):
            sy = y - depth / 2 + (index + 0.5) * depth / count
            sz = z - height * 0.36 + row * height / max(1, rows)
            geometry.box(
                f"{name}_course_side_{row:02d}_{index:02d}",
                collection,
                (x + width / 2 + 0.024, sy, sz),
                (0.055, depth / count * 0.72, height / rows * 0.42),
                material,
                bevel=0.006,
            )


def add_readable_stone_wall(name: str, collection, mats: dict, loc, size, *, style="blocks", damaged=False):
    x, y, z = loc
    width, depth, height = size
    base_role = "damage_char" if damaged else "stone_light"
    geometry.box(f"{name}_core", collection, loc, size, mat(mats, base_role, "stone_shadow"), bevel=0.030)
    if style == "rocks":
        for index in range(12):
            px = x - width * 0.42 + (index % 4) * width * 0.28
            pz = z - height * 0.32 + (index // 4) * height * 0.26
            geometry.sphere(f"{name}_rock_{index:02d}", collection, (px, y - depth * 0.55, pz), (0.11, 0.035, 0.075), mat(mats, "stone_light", "stone_shadow"), segments=8)
    else:
        rows = max(2, int(height / 0.18))
        for row in range(rows):
            cols = 4 + row % 2
            for col in range(cols):
                px = x - width / 2 + (col + 0.5) * width / cols
                pz = z - height / 2 + (row + 0.5) * height / rows
                geometry.box(f"{name}_block_{row:02d}_{col:02d}", collection, (px, y - depth * 0.56, pz), (width / cols * 0.80, depth * 0.22, height / rows * 0.76), mat(mats, "stone_block", "stone_light"), bevel=0.008)


def add_metal_plate_wall(name: str, collection, mats: dict, loc, size, *, panels=4, gold_trim=False, damaged=False):
    x, y, z = loc
    width, depth, height = size
    base = mat(mats, "damage_char", "metal_worn") if damaged else mat(mats, "metal_worn", "steel_light")
    geometry.box(f"{name}_metal_wall_core", collection, loc, size, base, bevel=0.025)
    for index in range(panels):
        px = x - width / 2 + (index + 0.5) * width / panels
        geometry.box(f"{name}_front_plate_{index:02d}", collection, (px, y - depth * 0.52, z), (width / panels * 0.70, depth * 0.18, height * 0.68), mat(mats, "steel_light", "metal_worn"), bevel=0.008)
    if gold_trim and not damaged:
        geometry.box(f"{name}_gold_trim_top", collection, (x, y - depth * 0.62, z + height * 0.42), (width * 0.82, depth * 0.12, 0.040), mat(mats, "roof_gold"), bevel=0.004)


def add_storage_wall(name: str, collection, mats: dict, loc, size, *, material_profile="stone", spikes=False, damaged=False):
    profile = WALL_MATERIAL_PROFILES.get(material_profile, WALL_MATERIAL_PROFILES["stone"])
    x, y, z = loc
    width, depth, height = size
    geometry.box(f"{name}_{material_profile}_wall", collection, loc, size, mat(mats, "damage_char", profile["body"]) if damaged else mat(mats, profile["body"]), bevel=0.030)
    geometry.box(f"{name}_{material_profile}_wall_cap", collection, (x, y, z + height * 0.54), (width + 0.12, depth + 0.05, 0.10), mat(mats, profile["cap"]), bevel=0.016)
    if material_profile in {"stone", "gold"}:
        add_stone_courses(f"{name}_{material_profile}", collection, mats, width, depth, z - height * 0.42, max(2, int(height / 0.22)), damaged=damaged)
    if spikes:
        add_wall_spikes(f"{name}_{material_profile}", collection, mats, (x, y - depth * 0.58, z + height * 0.72), count=5, width=width * 0.86, material_role=profile["spike"], damaged=damaged)


def add_wall_spikes(name: str, collection, mats: dict, loc, *, count=5, width=1.6, material_role="metal_worn", damaged=False):
    x, y, z = loc
    spike_mat = mat(mats, "damage_char", material_role) if damaged else mat(mats, material_role)
    for index in range(count):
        sx = x - width / 2 + index * width / max(1, count - 1)
        geometry.cone(f"{name}_wall_spike_{index:02d}", collection, (sx, y, z), 0.055, 0.0, 0.22, spike_mat, vertices=8, rotation=(math.radians(90), 0, 0))


def add_corner_piers(name: str, collection, mats: dict, width: float, depth: float, height: float, *, z_base=0.0, material_role="stone_light"):
    material = mat(mats, material_role, "stone_light")
    for index, (x, y) in enumerate(((-width / 2, -depth / 2), (width / 2, -depth / 2), (-width / 2, depth / 2), (width / 2, depth / 2))):
        geometry.box(f"{name}_corner_pier_{index}", collection, (x, y, z_base + height / 2), (0.20, 0.20, height), material, bevel=0.025)
        geometry.box(f"{name}_corner_pier_cap_{index}", collection, (x, y, z_base + height + 0.06), (0.28, 0.28, 0.10), material, bevel=0.018)


def _wall_decor_mat(mats: dict, material: str, damaged: bool = False):
    role = "damage_char" if damaged else WALL_DECOR_MATERIALS.get(material, "wood_pale")
    return mat(mats, role, "wood_pale")


def add_s_scroll_wall_decor(name: str, collection, mats: dict, loc, *, material="wood", width=0.72, height=0.26, depth=0.045, mirrored=False, damaged=False):
    """Add a horizontal S-like applique for walls, readable in isometric view."""

    x, y, z = loc
    decor_mat = _wall_decor_mat(mats, material, damaged)
    sign = -1 if mirrored else 1
    geometry.beam(f"{name}_scroll_mid", collection, (x - width * 0.24, y, z), (x + width * 0.24, y, z), depth * 0.80, decor_mat)
    geometry.beam(f"{name}_scroll_left_hook", collection, (x - width * 0.42, y, z + height * 0.02), (x - width * 0.20, y, z + sign * height * 0.30), depth * 0.72, decor_mat)
    geometry.beam(f"{name}_scroll_right_hook", collection, (x + width * 0.20, y, z - sign * height * 0.30), (x + width * 0.42, y, z - height * 0.02), depth * 0.72, decor_mat)
    for index, sx in enumerate((-0.42, 0.42)):
        geometry.cylinder(
            f"{name}_scroll_round_tip_{index}",
            collection,
            (x + width * sx, y, z + sign * height * (0.18 if sx < 0 else -0.18)),
            depth * 0.80,
            depth * 0.55,
            decor_mat,
            vertices=10,
            rotation=(math.radians(90), 0, 0),
        )


def add_carved_wall_pattern(name: str, collection, mats: dict, loc, *, material="wood", width=0.86, height=0.42, depth=0.035, style="vine", damaged=False):
    """Add raised carved/riveted wall ornament in wood, metal, gold or stone."""

    x, y, z = loc
    decor_mat = _wall_decor_mat(mats, material, damaged)
    geometry.box(f"{name}_pattern_top", collection, (x, y, z + height * 0.36), (width, depth, depth), decor_mat, bevel=0.005)
    geometry.box(f"{name}_pattern_bottom", collection, (x, y, z - height * 0.36), (width, depth, depth), decor_mat, bevel=0.005)
    if style == "runes":
        for index, sx in enumerate((-0.30, 0.0, 0.30)):
            geometry.box(f"{name}_rune_stroke_{index}_a", collection, (x + width * sx, y, z), (depth, depth, height * 0.42), decor_mat, bevel=0.004, rotation=(0, 0, math.radians(10 + index * 18)))
            geometry.box(f"{name}_rune_stroke_{index}_b", collection, (x + width * sx + 0.035, y, z + height * 0.05), (depth, depth, height * 0.26), decor_mat, bevel=0.004, rotation=(0, 0, math.radians(-18)))
    else:
        for index in range(5):
            px = x - width * 0.38 + index * width * 0.19
            pz = z + math.sin(index * 1.25) * height * 0.15
            geometry.beam(f"{name}_vine_{index:02d}", collection, (px, y, pz), (px + width * 0.15, y, z - math.sin(index * 1.25) * height * 0.15), depth * 0.62, decor_mat)
            if index % 2 == 0:
                geometry.sphere(f"{name}_carved_leaf_{index:02d}", collection, (px + width * 0.08, y - depth * 0.22, pz + height * 0.10), (depth * 1.2, depth * 0.45, depth * 0.8), decor_mat, segments=8)


def add_window_trim(name: str, collection, mats: dict, loc, *, width=0.62, height=0.54, depth=0.045, ornate=True, damaged=False):
    """White patterned window casing/nalichnik for wooden and stone houses."""

    x, y, z = loc
    trim_mat = mat(mats, "damage_char", "whitewash") if damaged else mat(mats, "whitewash", "wood_pale")
    geometry.box(f"{name}_left_trim", collection, (x - width / 2, y, z), (depth, depth, height), trim_mat, bevel=0.007)
    geometry.box(f"{name}_right_trim", collection, (x + width / 2, y, z), (depth, depth, height), trim_mat, bevel=0.007)
    geometry.box(f"{name}_top_trim", collection, (x, y, z + height / 2), (width + depth * 1.8, depth, depth), trim_mat, bevel=0.007)
    geometry.box(f"{name}_bottom_trim", collection, (x, y, z - height / 2), (width + depth * 1.4, depth, depth), trim_mat, bevel=0.007)
    if ornate:
        for index, sx in enumerate((-0.36, 0.0, 0.36)):
            geometry.cone(f"{name}_lace_tooth_{index:02d}", collection, (x + width * sx, y - depth * 0.10, z + height * 0.62), depth * 0.55, depth * 0.18, depth * 1.65, trim_mat, vertices=6)
        add_s_scroll_wall_decor(f"{name}_small_scroll_l", collection, mats, (x - width * 0.33, y - depth * 0.18, z), material="white", width=width * 0.30, height=height * 0.28, depth=depth * 0.62, mirrored=True, damaged=damaged)
        add_s_scroll_wall_decor(f"{name}_small_scroll_r", collection, mats, (x + width * 0.33, y - depth * 0.18, z), material="white", width=width * 0.30, height=height * 0.28, depth=depth * 0.62, damaged=damaged)


def add_wall_medallion(name: str, collection, mats: dict, loc, *, material="stone", radius=0.18, depth=0.045, symbol="wind", damaged=False):
    x, y, z = loc
    decor_mat = _wall_decor_mat(mats, material, damaged)
    geometry.cylinder(f"{name}_medallion_base", collection, (x, y, z), radius, depth, decor_mat, vertices=18, rotation=(math.radians(90), 0, 0))
    accent = mat(mats, "runic_glow" if material == "gold" else "stone_shadow", "wood_dark")
    if symbol == "cross":
        geometry.box(f"{name}_medallion_cross_v", collection, (x, y - depth * 0.58, z), (radius * 0.22, depth * 0.30, radius * 1.30), accent, bevel=0.003)
        geometry.box(f"{name}_medallion_cross_h", collection, (x, y - depth * 0.60, z), (radius * 1.28, depth * 0.28, radius * 0.20), accent, bevel=0.003)
    else:
        add_s_scroll_wall_decor(f"{name}_medallion_wind", collection, mats, (x, y - depth * 0.62, z), material=material, width=radius * 1.35, height=radius * 0.55, depth=depth * 0.42, damaged=damaged)
