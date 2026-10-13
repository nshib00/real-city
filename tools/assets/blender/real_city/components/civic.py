"""Civic and center-building component factories."""

from __future__ import annotations

from .. import geometry
from . import aeolian, props, roofs
from .common import add_door, add_flag_pole, add_window, mat
from .walls import add_corner_piers, add_stone_block_wall


def add_civic_tower(name: str, collection, mats: dict, loc=(0, 0, 0), *, height=1.4, width=0.62, roof_role="roof_teal", damaged=False):
    x, y, z = loc
    body_mat = mat(mats, "damage_char", "wood_pale") if damaged else mat(mats, "wood_pale", "stone_light")
    geometry.box(f"{name}_tower_body", collection, (x, y, z + height / 2), (width, width, height), body_mat, bevel=0.035)
    add_corner_piers(f"{name}_tower", collection, mats, width, width, height, z_base=z, material_role="wood_beam")
    roofs.add_hipped_roof(f"{name}_tower", collection, mats, (x, y, z + height), (width + 0.24, width + 0.22, 0.34), color_role=roof_role, damaged=damaged)
    add_flag_pole(f"{name}_top", collection, mats, (x + width * 0.18, y - width * 0.08, z + height + 0.30), height=0.56, color_role="roof_red")


def add_notice_board(name: str, collection, mats: dict, loc=(-0.65, -0.72, 0.38)):
    props.add_tool_rack(f"{name}_plans", collection, mats, loc, tools=("plan", "ruler", "stamp"))
    props.add_crate(f"{name}_scroll_crate", collection, mats, (loc[0] + 0.34, loc[1] + 0.02, 0.15), (0.28, 0.22, 0.20))


def add_balcony(name: str, collection, mats: dict, loc, *, width=0.62, damaged=False):
    x, y, z = loc
    geometry.box(f"{name}_balcony_floor", collection, (x, y, z), (width, 0.22, 0.07), mat(mats, "damage_char", "wood_pale") if damaged else mat(mats, "wood_pale"), bevel=0.010)
    for sx in (-width * 0.42, 0, width * 0.42):
        geometry.cylinder(f"{name}_balcony_post_{sx:.1f}", collection, (x + sx, y - 0.10, z + 0.16), 0.018, 0.28, mat(mats, "wood_dark", "metal_worn"), vertices=7)
    geometry.beam(f"{name}_balcony_rail", collection, (x - width * 0.48, y - 0.10, z + 0.30), (x + width * 0.48, y - 0.10, z + 0.30), 0.026, mat(mats, "wood_dark", "metal_worn"))


def add_plaza(name: str, collection, mats: dict, *, width=1.36, depth=0.70, y=-0.92):
    geometry.box(f"{name}_plaza_base", collection, (0, y, 0.035), (width, depth, 0.055), mat(mats, "path_warm", "stone_light"), bevel=0.020)
    for index, x in enumerate((-0.42, 0.0, 0.42)):
        geometry.box(f"{name}_plaza_tile_{index}", collection, (x, y - 0.02, 0.078), (0.30, depth * 0.76, 0.018), mat(mats, "stone_light", "path_warm"), bevel=0.004)


def add_town_hall_core(name: str, collection, mats: dict, *, level=1, damaged=False):
    body_w = 1.08 + min(level, 10) * 0.06
    body_d = 0.98 + min(level, 10) * 0.035
    body_h = 0.62 + min(level, 10) * 0.055
    if level >= 7:
        add_stone_block_wall(f"{name}_body", collection, mats, (0, 0, 0.24 + body_h / 2), (body_w, body_d, body_h), rows=3, damaged=damaged)
    else:
        geometry.box(f"{name}_body", collection, (0, 0, 0.24 + body_h / 2), (body_w, body_d, body_h), mat(mats, "damage_char", "wood_pale") if damaged else mat(mats, "wood_pale"), bevel=0.035)
    roof_role = "roof_leaf" if level <= 2 else "roof_teal" if level <= 5 else "brick_warm"
    roofs.add_hipped_roof(f"{name}_main", collection, mats, (0, 0, 0.24 + body_h), (body_w + 0.22, body_d + 0.18, 0.30 + level * 0.012), color_role=roof_role, damaged=damaged)
    add_civic_tower(f"{name}_central", collection, mats, (0, 0.06, 0.24 + body_h * 0.52), height=0.92 + level * 0.055, width=0.48 + level * 0.012, roof_role=roof_role, damaged=damaged)
    add_door(f"{name}_main", collection, mats, (0, -body_d / 2 - 0.07, 0.48), reinforced=level >= 5, damaged=damaged)
    add_window(f"{name}_admin_l", collection, mats, (-body_w * 0.28, -body_d / 2 - 0.07, 0.76), damaged=damaged)
    if level >= 3:
        add_window(f"{name}_admin_r", collection, mats, (body_w * 0.28, -body_d / 2 - 0.07, 0.76), damaged=damaged)
    if level >= 8:
        aeolian.add_clock_or_city_seal(f"{name}_clock", collection, mats, (0, -body_d / 2 - 0.09, 1.26 + level * 0.03))
