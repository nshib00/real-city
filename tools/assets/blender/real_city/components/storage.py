"""Storage/vault component kit including roofs, walls and spikes."""

from __future__ import annotations

import math

from .. import geometry
from . import props, roofs
from .common import add_door, add_window, mat
from .walls import add_corner_piers, add_metal_plate_wall, add_storage_wall

STORAGE_MATERIAL_BY_TIER = {
    1: "wood",
    2: "stone",
    3: "metal",
    4: "gold",
}


def storage_tier(level: int) -> int:
    if level <= 2:
        return 1
    if level <= 6:
        return 2
    if level <= 10:
        return 3
    return 4


def add_vault_body(name: str, collection, mats: dict, *, level=1, damaged=False):
    tier = storage_tier(level)
    profile = STORAGE_MATERIAL_BY_TIER[tier]
    width = 1.42 + min(level, 12) * 0.055
    depth = 1.02 + min(level, 12) * 0.030
    height = 0.72 + min(level, 12) * 0.055
    geometry.box(f"{name}_vault_foundation", collection, (0, 0, 0.16), (width + 0.34, depth + 0.28, 0.28), mat(mats, "stone_shadow", "stone_light"), bevel=0.040)
    if profile == "metal":
        add_metal_plate_wall(f"{name}_vault", collection, mats, (0, 0, 0.32 + height / 2), (width, depth, height), panels=4, gold_trim=level >= 10, damaged=damaged)
    else:
        add_storage_wall(f"{name}_vault", collection, mats, (0, 0, 0.32 + height / 2), (width, depth, height), material_profile=profile, spikes=level >= 11, damaged=damaged)
    add_corner_piers(f"{name}_vault", collection, mats, width + 0.08, depth + 0.08, height + 0.10, z_base=0.32, material_role="dark_metal" if tier >= 3 else "stone_light")
    add_door(f"{name}_safe", collection, mats, (0, -depth / 2 - 0.065, 0.56 + height * 0.24), (0.56, 0.075, height * 0.64), material_role="metal_worn" if tier >= 2 else "wood_dark", reinforced=True, damaged=damaged)
    if level >= 4:
        add_window(f"{name}_cashier", collection, mats, (-width * 0.30, -depth / 2 - 0.068, 0.76 + height * 0.18), warm=False, damaged=damaged)


def add_storage_roof(name: str, collection, mats: dict, *, level=1, width=1.8, depth=1.2, z=1.26, damaged=False):
    tier = storage_tier(level)
    if tier == 1:
        roofs.add_gable_roof(f"{name}_wood", collection, mats, (0, 0, z), (width, depth, 0.34), color_role="roof_teal", damaged=damaged)
    elif tier == 2:
        roofs.add_hipped_roof(f"{name}_stone", collection, mats, (0, 0, z), (width, depth, 0.36), color_role="roof_stone", cap=0.36, damaged=damaged)
    elif tier == 3:
        roofs.add_gable_roof(f"{name}_metal", collection, mats, (0, 0, z), (width, depth, 0.36), color_role="roof_stone", damaged=damaged)
        roofs.add_roof_plate_rows(f"{name}_metal", collection, mats, (0, 0, z), (width, depth, 0.36), rows=4, material_role="metal_worn")
        roofs.add_roof_spikes(f"{name}_metal", collection, mats, (0, -depth / 2 - 0.08, z + 0.30), count=4, width=width * 0.78, material_role="metal_worn", damaged=damaged)
    else:
        roofs.add_gable_roof(f"{name}_gold", collection, mats, (0, 0, z), (width, depth, 0.40), color_role="roof_gold", damaged=damaged)
        roofs.add_roof_plate_rows(f"{name}_gold", collection, mats, (0, 0, z), (width, depth, 0.40), rows=5, material_role="roof_gold")
        roofs.add_roof_spikes(f"{name}_gold", collection, mats, (0, -depth / 2 - 0.08, z + 0.34), count=5, width=width * 0.82, material_role="roof_gold", damaged=damaged)


def add_coin_accents(name: str, collection, mats: dict, loc=(0.82, -0.82, 0.13), *, count=3, damaged=False):
    x, y, z = loc
    coin_mat = mat(mats, "dust", "roof_gold") if damaged else mat(mats, "roof_gold")
    for index in range(count):
        geometry.cylinder(f"{name}_coin_{index:02d}", collection, (x + index * 0.045, y - index * 0.018, z + index * 0.012), 0.065, 0.018, coin_mat, vertices=18, rotation=(math.radians(90), 0, 0))


def add_safe_cells(name: str, collection, mats: dict, *, level=7, width=1.8, depth=1.2, z=0.78, damaged=False):
    cols = 3 if level < 10 else 4
    rows = 2 if level < 11 else 3
    for row in range(rows):
        for col in range(cols):
            if damaged and (row + col) % 4 == 0:
                continue
            x = -0.36 + (col - (cols - 1) / 2) * 0.24
            geometry.box(f"{name}_safe_cell_{row}_{col}", collection, (x, -depth / 2 - 0.082, z + row * 0.18), (0.17, 0.035, 0.12), mat(mats, "metal_worn", "steel_light"), bevel=0.010)
            geometry.cylinder(f"{name}_safe_knob_{row}_{col}", collection, (x + 0.048, -depth / 2 - 0.112, z + row * 0.18), 0.015, 0.012, mat(mats, "roof_gold"), vertices=10, rotation=(math.radians(90), 0, 0))


def add_storage_yard(name: str, collection, mats: dict, *, level=1, damaged=False):
    props.add_sack(f"{name}_money_bag", collection, mats, (-0.72, -0.78, 0.16), material_role="dust")
    props.add_crate(f"{name}_sealed_crate", collection, mats, (0.78, 0.58, 0.16), (0.32, 0.28, 0.22), damaged=damaged)
    add_coin_accents(name, collection, mats, count=2 + min(level, 5), damaged=damaged)
