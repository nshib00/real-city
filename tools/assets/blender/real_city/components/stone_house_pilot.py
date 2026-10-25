"""Detailed masonry, green tile roof, and inherited level-six housing yard."""

from __future__ import annotations

import math

from .. import geometry
from . import landscaping, props, roofs
from .common import add_barrel, add_path, mat


def add_full_stone_cladding(name, collection, mats, *, width=1.47, depth=1.15, height=0.94, base_z=0.22):
    """Cover all four facades with staggered, nearly continuous stone courses."""
    for side in ("front", "back", "left", "right"):
        along = width if side in ("front", "back") else depth
        columns = 8 if side in ("front", "back") else 6
        rows = max(6, round(height / 0.16))
        for row in range(rows):
            offset = 0.5 if row % 2 else 0.0
            for col in range(columns + (1 if offset else 0)):
                low = max(-along / 2, -along / 2 + (col - offset) * along / columns)
                high = min(along / 2, -along / 2 + (col + 1 - offset) * along / columns)
                if high - low < 0.035:
                    continue
                position = (low + high) / 2
                z = base_z + (row + 0.5) * height / rows
                color = "stone_shadow" if (row * 3 + col) % 7 == 0 else ("stone_block" if (row + col) % 2 == 0 else "stone_light")
                if side in ("front", "back"):
                    y = (-1 if side == "front" else 1) * (depth / 2 + 0.038)
                    loc = (position, y, z)
                    size = (high - low - 0.010, 0.065, height / rows - 0.010)
                else:
                    x = (-1 if side == "left" else 1) * (width / 2 + 0.038)
                    loc = (x, position, z)
                    size = (0.065, high - low - 0.010, height / rows - 0.010)
                geometry.box(f"{name}_{side}_r{row:02d}_c{col:02d}", collection, loc, size, mat(mats, color), bevel=0.008)


def add_green_tiled_roof(name, collection, mats, *, width=1.47, depth=1.15, roof_z=1.16, level=1):
    roof_width = width + 0.30 + (0.10 if level >= 2 else 0)
    roof_depth = depth + 0.24 + (0.08 if level >= 2 else 0)
    rise = 0.39
    roofs.add_gable_roof(name, collection, mats, (0, 0, roof_z), (roof_width, roof_depth, rise), color_role="roof_green")
    pitch = math.atan2(rise, roof_width / 2)
    for side in (-1, 1):
        for slope_row in range(7):
            x = side * ((0.075 + slope_row * 0.112) if level == 1 else (slope_row + 0.5) * roof_width / 14)
            z = roof_z + rise * (1 - abs(x) / (roof_width / 2)) + 0.024
            for col in range(8):
                y = -roof_depth * 0.47 + (col + 0.5) * roof_depth * 0.94 / 8
                role = "roof_leaf" if (slope_row + 2 * col) % 9 == 0 else "roof_green"
                geometry.box(
                    f"{name}_tile_s{side:+d}_r{slope_row:02d}_c{col:02d}", collection,
                    (x, y, z), (0.145 if level == 1 else roof_width / 14 + 0.012, roof_depth * 0.94 / 8 - 0.006, 0.028),
                    mat(mats, role), bevel=0.006, rotation=(0, side * pitch, 0),
                )
    for col in range(9):
        y = -roof_depth / 2 + (col + 0.5) * roof_depth / 9
        geometry.box(f"{name}_ridge_tile_{col:02d}", collection, (0, y, roof_z + rise + 0.058),
                     (0.125, roof_depth / 9 - 0.005, 0.065), mat(mats, "roof_green"), bevel=0.014)
    for side in (-1, 1):
        geometry.box(f"{name}_eave_{side:+d}", collection,
                     (side * roof_width * 0.48, 0, roof_z + 0.038),
                     (0.060, roof_depth + 0.06, 0.065), mat(mats, "copper"), bevel=0.010)

    # The dormer is a separate built volume, not a painted roof mark.
    x, y, z = -0.28, -roof_depth * 0.36, roof_z + 0.21
    geometry.box(f"{name}_dormer_body", collection, (x, y, z), (0.38, 0.35, 0.30), mat(mats, "stone_light"), bevel=0.015)
    roofs.add_gable_roof(f"{name}_dormer", collection, mats, (x, y, z + 0.14), (0.48, 0.43, 0.16), color_role="roof_green")
    if level == 1:
        geometry.box(f"{name}_dormer_glass", collection, (x, y - 0.185, z + 0.018), (0.20, 0.025, 0.17), mat(mats, "window_warm"), bevel=0.006)
        geometry.box(f"{name}_dormer_frame", collection, (x, y - 0.205, z + 0.018), (0.245, 0.025, 0.032), mat(mats, "wood_dark"), bevel=0.004)
    geometry.box(f"{name}_dormer_sill", collection, (x, y - 0.22, z - 0.085), (0.27, 0.065, 0.045), mat(mats, "stone_block"), bevel=0.007)


def add_level_six_wood_yard(name, collection, mats, *, level=1):
    """Rebuild every exterior decoration of wood_house level 6 around the stone shell."""
    add_path(f"{name}_front_path", collection, mats, (0, -1.26, 0.012), (1.14, 0.86, 0.030), kind="earth_light")
    geometry.box(f"{name}_old_house_trace", collection, (-0.62, 0.58, 0.014), (0.92, 0.42, 0.026), mat(mats, "earth_warm"), bevel=0.006)
    geometry.box(f"{name}_blue_yard_pool", collection, (0.90, 0.72, 0.018), (0.48, 0.28, 0.030), mat(mats, "glass_cyan"), bevel=0.012)
    props.add_flag_marker(f"{name}_marker", collection, mats, (-0.88, -0.08, 0.02), height=1.54, color_role="roof_teal")
    props.add_flower_strip(f"{name}_front_flowers", collection, mats, (0, -1.02, 0.13), count=4)
    for i, x in enumerate((-1.08, -0.72, 0.72, 1.08)):
        geometry.box(f"{name}_fence_post_{i:02d}", collection, (x, 1.05, 0.19),
                     (0.075, 0.075, 0.38), mat(mats, "wood_pale"), bevel=0.008)
    geometry.box(f"{name}_fence_rail", collection, (0, 1.05, 0.31),
                 (2.34, 0.065, 0.07), mat(mats, "roof_teal"), bevel=0.007)
    props.add_log_stack(f"{name}_log_stack", collection, mats, (-1.02, -0.72, 0.11), count=4)
    barrel_loc = ((1.50, 0.88, 0.18) if level >= 5 else
                  (1.48, -0.84, 0.18) if level >= 3 else (1.10, -0.58, 0.18))
    add_barrel(f"{name}_barrel", collection, mats, barrel_loc, radius=0.14, height=0.34)
    geometry.box(f"{name}_bench_seat", collection, (-1.08, -0.37, 0.19),
                 (0.46, 0.17, 0.07), mat(mats, "wood_pale"), bevel=0.010)
    for i, x in enumerate((-1.24, -0.92)):
        geometry.box(f"{name}_bench_leg_{i}", collection, (x, -0.37, 0.085),
                     (0.055, 0.12, 0.17), mat(mats, "wood_beam"), bevel=0.006)
    geometry.cylinder(f"{name}_lantern_post", collection, (0.82, -0.98, 0.35),
                      0.035, 0.70, mat(mats, "wood_dark"), vertices=8)
    geometry.box(f"{name}_lantern_glow", collection, (0.82, -0.98, 0.76),
                 (0.16, 0.13, 0.16), mat(mats, "window_warm"), bevel=0.012)
    for i, y in enumerate((0.56, 0.72, 0.88)):
        landscaping.add_flower_bed(f"{name}_rear_bloom_{i}", collection, mats,
                                   (-1.12, y, 0.06), style="stone_ring")
    landscaping.add_grass_clump(f"{name}_grass_l", collection, mats, (-1.32, 0.58, 0.08), height="low", blades=5)
    grass_r = (1.50, 1.20, 0.08) if level >= 5 else ((1.58, 0.60, 0.08) if level >= 3 else (1.22, 0.60, 0.08))
    landscaping.add_grass_clump(f"{name}_grass_r", collection, mats, grass_r, height="high", blades=6)
    landscaping.add_pebble_cluster(f"{name}_pebbles", collection, mats, (-0.92, 0.90, 0.08), count=6)
    landscaping.add_flower_bed(f"{name}_front_bed", collection, mats, (-1.12, -0.48, 0.06), style="stone_ring")
