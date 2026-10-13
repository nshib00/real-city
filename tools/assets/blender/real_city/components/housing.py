"""Parametric component groups for housing assets."""

from __future__ import annotations

from .. import geometry
from . import foundations, landscaping, props, roofs
from .common import add_chimney, add_door, add_path, add_window, add_wood_house_chimney, mat
from .walls import add_corner_piers, add_plank_wall, add_readable_stone_wall, add_stone_block_wall, add_wood_house_wall_set


def add_dugout_shell(name: str, collection, mats: dict, *, level=1, damaged=False):
    mound_mat = mat(mats, "damage_char", "earth_warm") if damaged else mat(mats, "earth_warm")
    geometry.sphere(f"{name}_earth_mound", collection, (0, 0, 0.34), (0.82 + level * 0.06, 0.66 + level * 0.04, 0.32 + level * 0.025), mound_mat, segments=16)
    geometry.box(f"{name}_entry_frame_top", collection, (0, -0.64, 0.58), (0.54, 0.055, 0.08), mat(mats, "wood_beam", "wood_dark"), bevel=0.010)
    geometry.box(f"{name}_entry_step", collection, (0, -0.80, 0.10), (0.58, 0.22, 0.060), mat(mats, "stone_light", "earth_warm"), bevel=0.012)
    add_path(f"{name}_earth_path", collection, mats, (0, -1.04, 0.020), (0.70, 0.42, 0.030), kind="earth_light")
    if level >= 3:
        for index, x in enumerate((-0.42, -0.14, 0.16, 0.42)):
            geometry.box(f"{name}_windleaf_roof_patch_{index}", collection, (x, -0.08 + index * 0.035, 0.68 + index * 0.012), (0.34, 0.18, 0.040), mat(mats, "roof_leaf"), bevel=0.018, rotation=(0.14, 0.02, -0.20 + index * 0.14))
    add_door(f"{name}_entry", collection, mats, (0, -0.62, 0.32), (0.42, 0.075, 0.42), material_role="wood_dark", reinforced=level >= 4, damaged=damaged)
    add_chimney(f"{name}_rough", collection, mats, (0.42, 0.18, 0.76), height=0.34 + level * 0.04, damaged=damaged)


def add_wood_house_shell(name: str, collection, mats: dict, *, level=1, damaged=False):
    width = 1.18 + min(level, 6) * 0.13
    depth = 1.02 + min(level, 6) * 0.08
    height = 0.62 + min(level, 4) * 0.08
    foundation_h = 0.14 + min(level, 4) * 0.015
    if level >= 5:
        height += 0.28
    foundations.add_foundation(
        f"{name}_spec",
        collection,
        mats,
        width=width,
        depth=depth,
        height="low" if level <= 2 else "medium",
        thickness="medium",
        material="stone" if level < 6 else "stone_block",
        loc=(0, 0, 0),
        damaged=damaged,
    )
    geometry.box(f"{name}_body_core", collection, (0, 0, foundation_h + height / 2), (width * 0.96, depth * 0.96, height * 0.96), mat(mats, "damage_char", "wood_pale") if damaged else mat(mats, "wood_pale"), bevel=0.016)
    add_wood_house_wall_set(f"{name}_plank_walls", collection, mats, width=width, depth=depth, height=height, z_base=foundation_h, damaged=damaged)
    geometry.box(f"{name}_front_whitewash_panel", collection, (0, -depth / 2 - 0.062, foundation_h + height * 0.48), (width * 0.54, 0.030, height * 0.28), mat(mats, "whitewash", "wood_pale"), bevel=0.010)
    add_corner_piers(f"{name}_wood", collection, mats, width, depth, height, z_base=foundation_h, material_role="wood_beam")
    roof_role = ("roof_red", "roof_teal", "roof_coral", "roof_red", "roof_blue", "roof_gold")[min(level, 6) - 1]
    roof_z = foundation_h + height
    roofs.add_wood_house_gable_roof(f"{name}_main", collection, mats, (0, 0, roof_z), (width + 0.30, depth + 0.26, 0.34 + level * 0.025), color_role=roof_role, damaged=damaged)
    add_door(f"{name}_front", collection, mats, (0, -depth / 2 - 0.070, foundation_h + 0.28), (0.42 + level * 0.025, 0.050, 0.56), material_role="wood_dark", reinforced=level >= 4, planked=True, damaged=damaged)
    geometry.box(f"{name}_door_arch", collection, (0, -depth / 2 - 0.086, foundation_h + 0.64), (0.66 + level * 0.025, 0.030, 0.08), mat(mats, "whitewash", "wood_pale"), bevel=0.008)
    for index in range(3):
        geometry.box(f"{name}_front_step_{index:02d}", collection, (0, -depth / 2 - 0.22 - index * 0.08, 0.08 - index * 0.012), (0.56 + index * 0.12, 0.10, 0.060), mat(mats, "stone_light", "stone_block"), bevel=0.010)
    add_window(f"{name}_window_l", collection, mats, (-width * 0.36, -depth / 2 - 0.074, foundation_h + height * 0.62), (0.30, 0.034, 0.28), frame_role="wood_beam", shape="rect", damaged=damaged)
    add_window(f"{name}_window_r", collection, mats, (width * 0.36, -depth / 2 - 0.074, foundation_h + height * 0.63), (0.28, 0.034, 0.26), frame_role="wood_beam", shape="square", damaged=damaged)
    side_x = width / 2 + 0.046
    side_z = foundation_h + height * 0.58
    frame = mat(mats, "wood_beam", "wood_dark")
    pane = mat(mats, "window_warm", "glass_cyan")
    geometry.box(f"{name}_side_window_frame", collection, (side_x, 0.18, side_z), (0.034, 0.34, 0.30), frame, bevel=0.008)
    geometry.box(f"{name}_side_window_pane", collection, (side_x + 0.010, 0.18, side_z), (0.020, 0.25, 0.22), pane, bevel=0.006)
    geometry.box(f"{name}_side_window_cross_v", collection, (side_x + 0.018, 0.18, side_z), (0.018, 0.030, 0.25), frame, bevel=0.003)
    geometry.box(f"{name}_side_window_cross_h", collection, (side_x + 0.019, 0.18, side_z), (0.018, 0.28, 0.030), frame, bevel=0.003)
    add_wood_house_chimney(f"{name}_chimney", collection, mats, (-width * 0.40, depth * 0.24, roof_z + 0.12), level=level, smoke=True, damaged=damaged)


def add_stone_house_shell(name: str, collection, mats: dict, *, level=1, damaged=False, rune_roof=False):
    width = 1.42 + level * 0.05
    depth = 1.12 + level * 0.03
    height = 0.88 + level * 0.06
    foundation_h = 0.22
    foundations.add_foundation(f"{name}_spec", collection, mats, width=width, depth=depth, height="medium", thickness="medium", material="stone_block", loc=(0, 0, 0), damaged=damaged)
    add_stone_block_wall(f"{name}_stone_body", collection, mats, (0, 0, foundation_h + height / 2), (width, depth, height), rows=3 + level // 2, damaged=damaged)
    roof_loc = (0, 0, foundation_h + height)
    if rune_roof:
        roofs.add_rune_tile_roof(f"{name}_rune", collection, mats, roof_loc, (width + 0.24, depth + 0.18, 0.36), damaged=damaged)
    else:
        roofs.add_gable_roof(f"{name}_stone", collection, mats, roof_loc, (width + 0.24, depth + 0.18, 0.36), color_role="brick_warm", damaged=damaged)
    add_door(f"{name}_stone", collection, mats, (0, -depth / 2 - 0.060, foundation_h + 0.32), (0.44, 0.050, 0.64), material_role="wood_dark", reinforced=True, damaged=damaged)
    add_window(f"{name}_stone_l", collection, mats, (-width * 0.28, -depth / 2 - 0.060, foundation_h + 0.66), (0.28, 0.034, 0.28), frame_role="metal_worn", damaged=damaged)
    add_window(f"{name}_stone_r", collection, mats, (width * 0.28, -depth / 2 - 0.060, foundation_h + 0.66), (0.28, 0.034, 0.28), frame_role="metal_worn", damaged=damaged)
    add_chimney(f"{name}_stone_chimney", collection, mats, (-width * 0.34, depth * 0.20, foundation_h + height + 0.14), height=0.42, damaged=damaged)


def add_housing_yard(name: str, collection, mats: dict, *, level=1, damaged=False):
    add_path(f"{name}_front_path", collection, mats, (0, -1.26, 0.012), (0.90 + level * 0.04, 0.86, 0.030), kind="earth_light")
    props.add_log_stack(f"{name}_log_stack", collection, mats, (-1.02, -0.72, 0.11), count=4)
    props.add_decor_cluster(f"{name}_decor", collection, mats, (1.08, -0.56, 0.02), damaged=damaged)
    props.add_flower_strip(f"{name}_flowers", collection, mats, (0, -1.02, 0.13), count=4)
    landscaping.add_grass_clump(f"{name}_grass_l", collection, mats, (-1.26, 0.58, 0.08), height="low", blades=5)
    landscaping.add_grass_clump(f"{name}_grass_h", collection, mats, (1.20, 0.62, 0.08), height="high", blades=6)
    landscaping.add_pebble_cluster(f"{name}_pebbles", collection, mats, (-0.92, 0.88, 0.08), count=6)
    props.add_flag_marker(f"{name}_flag", collection, mats, (-0.78, -0.08, 0.02), height=0.78 + min(level, 4) * 0.12, color_role="roof_red")
    if level >= 4:
        props.add_tool_rack(f"{name}_tool_rack", collection, mats, (-1.02, 0.42, 0.10))
