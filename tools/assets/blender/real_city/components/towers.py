"""Small tower components for civic, housing and defense silhouettes."""

from __future__ import annotations

import math

from .. import geometry
from . import roofs
from .common import mat
from .walls import add_board_clad_wall, add_readable_stone_wall

TOWER_MATERIALS = {
    "wood": "wood_beam",
    "stone": "stone_light",
    "stone_block": "stone_block",
    "brick": "brick_warm",
}


def add_tower(name: str, collection, mats: dict, loc, *, material="wood", height=0.95, radius=0.24, roof=True, damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else TOWER_MATERIALS.get(material, "wood_beam")
    if material == "wood":
        geometry.cylinder(f"{name}_wood_tower_core", collection, (x, y, z + height / 2), radius, height, mat(mats, role, "wood_beam"), vertices=10)
        for index in range(6):
            angle = index * math.tau / 6
            geometry.beam(
                f"{name}_wood_tower_post_{index:02d}",
                collection,
                (x + math.cos(angle) * radius * 0.86, y + math.sin(angle) * radius * 0.86, z + 0.06),
                (x + math.cos(angle) * radius * 0.86, y + math.sin(angle) * radius * 0.86, z + height + 0.02),
                0.035,
                mat(mats, "wood_dark", "wood_beam"),
            )
    elif material == "stone":
        geometry.cylinder(f"{name}_stone_tower_core", collection, (x, y, z + height / 2), radius, height, mat(mats, role, "stone_light"), vertices=12)
        add_readable_stone_wall(f"{name}_stone_tower_front", collection, mats, (x, y - radius - 0.018, z + height * 0.48), (radius * 1.55, 0.040, height * 0.82), style="rocks", damaged=damaged)
    else:
        geometry.cylinder(f"{name}_{material}_tower_core", collection, (x, y, z + height / 2), radius, height, mat(mats, role, "stone_block"), vertices=12)
        block_role = "brick_light" if material == "brick" else "stone_block"
        for row in range(4):
            for col in range(4):
                angle = col * math.tau / 4 + (row % 2) * 0.28
                geometry.box(
                    f"{name}_{material}_tower_block_{row:02d}_{col:02d}",
                    collection,
                    (x + math.cos(angle) * radius * 0.95, y + math.sin(angle) * radius * 0.95, z + height * (0.18 + row * 0.18)),
                    (0.10, 0.035, 0.095),
                    mat(mats, block_role, role),
                    bevel=0.006,
                    rotation=(0, 0, angle),
                )
    geometry.box(f"{name}_tower_cap", collection, (x, y, z + height + 0.025), (radius * 2.15, radius * 2.15, 0.060), mat(mats, "stone_shadow", "wood_dark"), bevel=0.012)
    if roof:
        roof_role = "roof_wood_dark" if material == "wood" else "brick_warm"
        roofs.add_trapezoid_roof(f"{name}_tower_roof", collection, mats, (x, y, z + height + 0.05), (radius * 2.35, radius * 2.35, 0.24), color_role=roof_role, damaged=damaged)


def add_square_tower(name: str, collection, mats: dict, loc, *, material="stone_block", size=(0.46, 0.46, 0.98), damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else TOWER_MATERIALS.get(material, "stone_block")
    geometry.box(f"{name}_{material}_square_tower_core", collection, (x, y, z + size[2] / 2), size, mat(mats, role, "stone_light"), bevel=0.025)
    if material == "wood":
        add_board_clad_wall(f"{name}_square_tower_front", collection, mats, (x, y - size[1] / 2 - 0.020, z + size[2] / 2), (size[0] * 0.82, 0.040, size[2] * 0.76), planks=4, damaged=damaged)
    else:
        add_readable_stone_wall(f"{name}_square_tower_front", collection, mats, (x, y - size[1] / 2 - 0.018, z + size[2] / 2), (size[0] * 0.82, 0.040, size[2] * 0.72), style="blocks", damaged=damaged)
    roofs.add_trapezoid_roof(f"{name}_square_tower_roof", collection, mats, (x, y, z + size[2]), (size[0] * 1.18, size[1] * 1.18, 0.20), color_role="brick_warm" if material == "brick" else "roof_stone", damaged=damaged)


def add_stone_turret(
    name: str,
    collection,
    mats: dict,
    loc,
    *,
    height=0.82,
    radius=0.18,
    thickness="medium",
    flag=False,
    flag_role="roof_red",
    crenellations=True,
    damaged=False,
):
    x, y, z = loc
    wall_role = "damage_char" if damaged else "stone_block"
    vertices = 12 if thickness != "thick" else 14
    geometry.cylinder(f"{name}_stone_turret_core", collection, (x, y, z + height / 2), radius, height, mat(mats, wall_role, "stone_light"), vertices=vertices)
    band_count = 2 if height < 0.90 else 3
    for row in range(band_count):
        bz = z + height * (0.20 + row * 0.26)
        for index in range(6):
            angle = index * math.tau / 6 + row * 0.18
            geometry.box(
                f"{name}_turret_block_{row:02d}_{index:02d}",
                collection,
                (x + math.cos(angle) * radius * 0.95, y + math.sin(angle) * radius * 0.95, bz),
                (radius * 0.42, 0.035, height * 0.11),
                mat(mats, "stone_light", "stone_block"),
                bevel=0.005,
                rotation=(0, 0, angle),
            )
    geometry.cylinder(f"{name}_turret_cap_ring", collection, (x, y, z + height + 0.025), radius * 1.08, 0.05, mat(mats, "stone_shadow", "stone_light"), vertices=vertices)
    if crenellations:
        merlon_count = 5 if thickness == "thin" else 6 if thickness == "medium" else 8
        for index in range(merlon_count):
            angle = index * math.tau / merlon_count
            geometry.box(
                f"{name}_turret_merlon_{index:02d}",
                collection,
                (x + math.cos(angle) * radius * 0.78, y + math.sin(angle) * radius * 0.78, z + height + 0.12),
                (radius * 0.32, 0.055, 0.16),
                mat(mats, "stone_light", "stone_block"),
                bevel=0.006,
                rotation=(0, 0, angle),
            )
    if flag:
        pole_h = 0.42 + height * 0.20
        geometry.cylinder(f"{name}_turret_flag_pole", collection, (x, y, z + height + pole_h / 2), 0.015, pole_h, mat(mats, "wood_dark", "metal_worn"), vertices=8)
        geometry.flag(f"{name}_turret_flag", collection, (x + 0.02, y, z + height + pole_h * 0.72), 0.28, 0.20, mat(mats, flag_role, "roof_red"))
