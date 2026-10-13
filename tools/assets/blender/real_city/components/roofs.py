"""Roof component kit for fantasy mid-poly buildings."""

from __future__ import annotations

import math

from .. import geometry
from .common import mat

ROOF_COLOR_ROLES = (
    "roof_wood_plank",
    "roof_wood_dark",
    "roof_leaf",
    "roof_teal",
    "roof_red",
    "roof_gold",
    "roof_blue",
    "roof_green",
    "roof_coral",
    "roof_rune_tile",
    "brick_warm",
    "stone_light",
)


def add_gable_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_red", trim=True, damaged=False):
    material = mat(mats, "damage_char", color_role) if damaged else mat(mats, color_role, "roof_red")
    roof = geometry.gable_roof(f"{name}_gable_roof", collection, loc, size, material)
    if trim:
        x, y, z = loc
        width, depth, height = size
        trim_mat = mat(mats, "wood_pale", "wood_beam")
        geometry.box(f"{name}_roof_ridge", collection, (x, y, z + height + 0.035), (0.07, depth + 0.14, 0.07), trim_mat, bevel=0.006)
        geometry.box(f"{name}_roof_front_trim", collection, (x, y - depth / 2 - 0.035, z + height * 0.26), (width * 0.86, 0.045, 0.050), trim_mat, bevel=0.005)
    return roof


def add_wood_house_gable_roof(
    name: str,
    collection,
    mats: dict,
    loc,
    size,
    *,
    color_role="roof_wood_plank",
    accent_role="wood_beam",
    board_rows=4,
    damaged=False,
):
    x, y, z = loc
    width, depth, height = size
    roof = add_gable_roof(name, collection, mats, loc, size, color_role=color_role, trim=True, damaged=damaged)
    geometry.box(f"{name}_front_accent", collection, (x, y - depth / 2 - 0.035, z + height * 0.24), (width * 0.86, 0.050, 0.055), mat(mats, accent_role, "wood_pale"), bevel=0.006)
    geometry.box(f"{name}_light_trim", collection, (x, y - depth / 2 - 0.055, z + height * 0.47), (width * 0.66, 0.042, 0.045), mat(mats, "wood_cut", "wood_pale"), bevel=0.005)
    add_roof_board_rows(f"{name}_boards", collection, mats, (x, y, z + height * 0.23), width * 0.88, depth * 0.90, rows=board_rows, material_role=color_role, damaged=damaged)
    return roof


def add_roof_board_rows(name: str, collection, mats: dict, loc, width: float, depth: float, *, rows=4, material_role="roof_wood_plank", damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else material_role
    for row in range(rows):
        offset_y = y - depth / 2 + (row + 0.5) * depth / rows
        row_width = width * (0.94 - row * 0.025)
        geometry.box(
            f"{name}_roof_board_{row:02d}",
            collection,
            (x, offset_y, z + row * 0.014),
            (row_width, depth / rows * 0.38, 0.040),
            mat(mats, role, "roof_wood_plank"),
            bevel=0.005,
            rotation=(0, 0, 0.010 if row % 2 else -0.010),
        )


def add_flat_roof(name: str, collection, mats: dict, loc, size, *, material_role="roof_wood_dark", parapet=True, damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else material_role
    geometry.box(f"{name}_flat_roof_deck", collection, loc, size, mat(mats, role, "roof_wood_dark"), bevel=0.020)
    if parapet:
        trim = mat(mats, "wood_beam", "stone_shadow")
        geometry.box(f"{name}_flat_roof_front_parapet", collection, (x, y - depth / 2, z + height * 0.78), (width + 0.08, 0.060, height * 0.54), trim, bevel=0.008)
        geometry.box(f"{name}_flat_roof_back_parapet", collection, (x, y + depth / 2, z + height * 0.78), (width + 0.08, 0.060, height * 0.54), trim, bevel=0.008)


def add_trapezoid_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_wood_plank", top_scale=0.56, damaged=False):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    top_x = x * top_scale
    top_y = y * top_scale
    verts = [
        (-x, -y, 0),
        (x, -y, 0),
        (x, y, 0),
        (-x, y, 0),
        (-top_x, -top_y, height),
        (top_x, -top_y, height),
        (top_x, top_y, height),
        (-top_x, top_y, height),
    ]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)]
    role = "damage_char" if damaged else color_role
    roof = geometry.mesh(f"{name}_trapezoid_roof", collection, verts, faces, mat(mats, role, "roof_wood_plank"))
    roof.location = loc
    add_roof_board_rows(f"{name}_trap_boards", collection, mats, (loc[0], loc[1], loc[2] + height * 0.42), width * 0.72, depth * 0.72, rows=3, material_role=color_role, damaged=damaged)
    return roof


def add_hipped_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_teal", cap=0.34, armored=False, damaged=False):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    top_x = max(0.18, x * cap)
    top_y = max(0.16, y * cap)
    verts = [
        (-x, -y, 0),
        (x, -y, 0),
        (x, y, 0),
        (-x, y, 0),
        (-top_x, -top_y, height),
        (top_x, -top_y, height),
        (top_x, top_y, height),
        (-top_x, top_y, height),
    ]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)]
    material = mat(mats, "damage_char", color_role) if damaged else mat(mats, color_role, "roof_teal")
    roof = geometry.mesh(f"{name}_hipped_roof", collection, verts, faces, material)
    roof.location = loc
    if armored:
        add_roof_plate_rows(name, collection, mats, loc, size, rows=3, material_role="metal_worn" if not damaged else "damage_char")
    return roof


def add_shed_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_leaf", pitch=0.10, damaged=False):
    material = mat(mats, "damage_char", color_role) if damaged else mat(mats, color_role, "roof_leaf")
    obj = geometry.box(f"{name}_shed_roof", collection, loc, size, material, bevel=0.018, rotation=(pitch, 0, 0))
    return obj


def add_tile_rows(name: str, collection, mats: dict, loc, width: float, depth: float, *, rows=4, color_role="roof_red", damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else color_role
    for row in range(rows):
        offset_y = y - depth / 2 + (row + 0.5) * depth / rows
        row_width = width * (0.92 - row * 0.018)
        geometry.box(
            f"{name}_tile_row_{row:02d}",
            collection,
            (x, offset_y, z + row * 0.012),
            (row_width, depth / rows * 0.42, 0.045),
            mat(mats, role, "roof_red"),
            bevel=0.004,
            rotation=(0, 0, 0.012 if row % 2 else -0.012),
        )


def add_rune_tile_roof(name: str, collection, mats: dict, loc, size, *, rune_rows=4, damaged=False):
    add_gable_roof(name, collection, mats, loc, size, color_role="roof_rune_tile", trim=True, damaged=damaged)
    x, y, z = loc
    width, depth, height = size
    add_tile_rows(f"{name}_rune", collection, mats, (x, y, z + height * 0.28), width * 0.88, depth * 0.88, rows=rune_rows, color_role="roof_rune_tile", damaged=damaged)
    rune_mat = mat(mats, "runic_glow", "amethyst")
    for index, offset in enumerate((-0.32, 0.0, 0.32)):
        geometry.box(f"{name}_rune_tile_glyph_{index}", collection, (x + offset, y - depth * 0.50, z + height * 0.36), (0.12, 0.020, 0.030), rune_mat, bevel=0.003, rotation=(0, 0, math.radians(8 * index)))


def add_roof_plate_rows(name: str, collection, mats: dict, loc, size, *, rows=4, material_role="metal_worn"):
    x, y, z = loc
    width, depth, height = size
    for index in range(rows):
        row_y = y - depth * 0.34 + index * depth * 0.22
        geometry.box(
            f"{name}_roof_plate_{index:02d}",
            collection,
            (x, row_y, z + height * (0.55 + index * 0.018)),
            (width * (0.82 - index * 0.035), 0.15, 0.055),
            mat(mats, material_role, "metal_worn"),
            bevel=0.008,
        )


def add_roof_spikes(name: str, collection, mats: dict, loc, *, count=5, width=1.6, material_role="metal_worn", damaged=False):
    x, y, z = loc
    spike_mat = mat(mats, "damage_char", material_role) if damaged else mat(mats, material_role, "metal_worn")
    for index in range(count):
        sx = x - width / 2 + index * width / max(1, count - 1)
        geometry.cone(f"{name}_roof_spike_{index:02d}", collection, (sx, y, z), 0.045, 0.0, 0.18, spike_mat, vertices=8, rotation=(math.radians(90), 0, 0))


def add_pyramid_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_red", damaged=False):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (0, 0, height)]
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)]
    role = "damage_char" if damaged else color_role
    obj = geometry.mesh(f"{name}_pyramid_roof", collection, verts, faces, mat(mats, role, "roof_red"))
    obj.location = loc
    return obj


def add_mansard_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_teal", damaged=False):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    mid_x = x * 0.82
    mid_y = y * 0.82
    top_x = x * 0.42
    top_y = y * 0.42
    verts = [
        (-x, -y, 0),
        (x, -y, 0),
        (x, y, 0),
        (-x, y, 0),
        (-mid_x, -mid_y, height * 0.54),
        (mid_x, -mid_y, height * 0.54),
        (mid_x, mid_y, height * 0.54),
        (-mid_x, mid_y, height * 0.54),
        (-top_x, -top_y, height),
        (top_x, -top_y, height),
        (top_x, top_y, height),
        (-top_x, top_y, height),
    ]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11), (8, 9, 10, 11), (0, 3, 2, 1)]
    role = "damage_char" if damaged else color_role
    obj = geometry.mesh(f"{name}_mansard_roof", collection, verts, faces, mat(mats, role, "roof_teal"))
    obj.location = loc
    add_roof_plate_rows(f"{name}_mansard", collection, mats, loc, size, rows=3, material_role=role)
    return obj


def add_barrel_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_wood_plank", ribs=5, damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else color_role
    for index in range(ribs):
        px = x - width / 2 + (index + 0.5) * width / ribs
        geometry.cylinder(
            f"{name}_barrel_segment_{index:02d}",
            collection,
            (px, y, z + height * 0.36),
            depth * 0.24,
            width / ribs * 0.72,
            mat(mats, role, "roof_wood_plank"),
            vertices=12,
            rotation=(0, math.radians(90), 0),
        )
    geometry.box(f"{name}_barrel_front_trim", collection, (x, y - depth * 0.27, z + height * 0.34), (width * 0.95, 0.045, height * 0.16), mat(mats, "wood_beam", "wood_dark"), bevel=0.006)


def add_dome_roof(name: str, collection, mats: dict, loc, *, radius=0.48, height=0.30, color_role="roof_gold", damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else color_role
    geometry.sphere(f"{name}_dome_cap", collection, (x, y, z + height * 0.55), (radius, radius, height), mat(mats, role, "roof_gold"), segments=18)
    geometry.cylinder(f"{name}_dome_ring", collection, (x, y, z + height * 0.06), radius * 1.02, height * 0.16, mat(mats, "stone_shadow", "wood_dark"), vertices=18)
    geometry.cone(f"{name}_dome_finial", collection, (x, y, z + height * 1.16), radius * 0.10, 0.0, height * 0.34, mat(mats, "roof_gold", role), vertices=8)


def add_stepped_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_stone", steps=3, damaged=False):
    x, y, z = loc
    width, depth, height = size
    role = "damage_char" if damaged else color_role
    for index in range(steps):
        scale = 1.0 - index * 0.18
        geometry.box(
            f"{name}_stepped_layer_{index:02d}",
            collection,
            (x, y, z + height * (index + 0.5) / steps),
            (width * scale, depth * scale, height / steps * 0.82),
            mat(mats, role, "roof_stone"),
            bevel=0.014,
        )


def add_asymmetric_gable_roof(name: str, collection, mats: dict, loc, size, *, color_role="roof_coral", damaged=False):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    ridge_x = -width * 0.16
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (ridge_x, -y, height), (ridge_x, y, height)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    role = "damage_char" if damaged else color_role
    obj = geometry.mesh(f"{name}_asym_gable_roof", collection, verts, faces, mat(mats, role, "roof_coral"))
    obj.location = loc
    add_tile_rows(f"{name}_asym_tiles", collection, mats, (loc[0], loc[1], loc[2] + height * 0.20), width * 0.88, depth * 0.88, rows=4, color_role=role, damaged=damaged)
    return obj
