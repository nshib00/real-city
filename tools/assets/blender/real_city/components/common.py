"""Shared low-level component helpers.

The helpers accept the material dictionary returned by
``materials.create_palette()``. They intentionally use broad role fallbacks so
older generators can adopt the component kit incrementally.
"""

from __future__ import annotations

import math

from .. import geometry


def mat(mats: dict, *roles: str):
    """Return the first available material role from ``mats``."""

    for role in roles:
        if role in mats:
            return mats[role]
    if not mats:
        raise ValueError("components require at least one material")
    return next(iter(mats.values()))


def add_window(
    name: str,
    collection,
    mats: dict,
    loc,
    size=(0.34, 0.055, 0.28),
    *,
    warm: bool = True,
    frame_role: str = "wood_dark",
    shape: str = "rect",
    damaged: bool = False,
):
    x, y, z = loc
    w, d, h = size
    frame = mat(mats, "damage_char", frame_role) if damaged else mat(mats, frame_role, "wood_dark", "metal_worn")
    pane = mat(mats, "damage_crack", "damage_char") if damaged else mat(mats, "window_warm" if warm else "glass_cyan", "glass_cyan")
    if shape == "round":
        geometry.cylinder(f"{name}_window_round_frame", collection, (x, y, z), max(w, h) * 0.54, d, frame, vertices=18, rotation=(math.radians(90), 0, 0))
        geometry.cylinder(f"{name}_window_round_pane", collection, (x, y - 0.012, z), max(w, h) * 0.42, d * 0.56, pane, vertices=18, rotation=(math.radians(90), 0, 0))
        geometry.box(f"{name}_window_round_cross_v", collection, (x, y - 0.020, z), (0.028, d * 0.52, h * 0.76), frame, bevel=0.004)
        geometry.box(f"{name}_window_round_cross_h", collection, (x, y - 0.021, z), (w * 0.76, d * 0.52, 0.030), frame, bevel=0.004)
        return
    if shape == "square":
        side = max(w, h)
        w = h = side
    geometry.box(f"{name}_window_frame", collection, (x, y, z), (w + 0.08, d, h + 0.08), frame, bevel=0.01)
    geometry.box(f"{name}_window_pane", collection, (x, y - 0.012, z), (w, d * 0.62, h), pane, bevel=0.008)
    geometry.box(f"{name}_window_cross_v", collection, (x, y - 0.020, z), (0.028, d * 0.52, h + 0.03), frame, bevel=0.004)
    geometry.box(f"{name}_window_cross_h", collection, (x, y - 0.021, z), (w + 0.02, d * 0.52, 0.030), frame, bevel=0.004)


def add_door(
    name: str,
    collection,
    mats: dict,
    loc,
    size=(0.46, 0.08, 0.66),
    *,
    material_role="wood_dark",
    reinforced=False,
    planked=True,
    damaged=False,
):
    door_mat = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, material_role, "wood_dark")
    x, y, z = loc
    w, d, h = size
    geometry.box(f"{name}_door", collection, loc, size, door_mat, bevel=0.025)
    if planked and "wood" in material_role:
        for index in range(3):
            px = x - w * 0.28 + index * w * 0.28
            geometry.box(f"{name}_door_plank_{index:02d}", collection, (px, y - d * 0.50, z), (w * 0.18, d * 0.24, h * 0.92), mat(mats, "wood_beam", material_role), bevel=0.006)
    geometry.box(f"{name}_door_lintel", collection, (x, y - d * 0.12, z + h * 0.56), (w + 0.16, d * 0.65, 0.08), mat(mats, "wood_beam", "wood_dark"), bevel=0.010)
    if reinforced:
        band = mat(mats, "metal_worn", "steel_light", "wood_beam")
        geometry.box(f"{name}_door_band_v", collection, (x - w * 0.24, y - d * 0.42, z), (0.055, d * 0.45, h * 0.92), band, bevel=0.006)
        geometry.box(f"{name}_door_band_h", collection, (x, y - d * 0.43, z + h * 0.10), (w * 0.82, d * 0.44, 0.055), band, bevel=0.006)
    geometry.box(f"{name}_door_handle", collection, (x + w * 0.28, y - d * 0.56, z + h * 0.02), (0.045, d * 0.22, 0.045), mat(mats, "roof_gold", "metal_worn"), bevel=0.006)


def add_chimney(name: str, collection, mats: dict, loc, *, height=0.46, radius=0.08, damaged=False):
    role = "damage_char" if damaged else "stone_light"
    geometry.cylinder(f"{name}_chimney_stack", collection, loc, radius, height, mat(mats, role, "stone_shadow"), vertices=9)
    x, y, z = loc
    geometry.box(f"{name}_chimney_cap", collection, (x, y, z + height * 0.54), (radius * 2.8, radius * 2.4, 0.055), mat(mats, role, "stone_light"), bevel=0.008)


def add_wood_house_chimney(name: str, collection, mats: dict, loc, *, level=1, smoke=True, damaged=False):
    x, y, z = loc
    radius = 0.085 + level * 0.006
    height = 0.45 + level * 0.045
    add_chimney(name, collection, mats, loc, height=height, radius=radius, damaged=damaged)
    if smoke and not damaged:
        for index in range(2 + (1 if level >= 4 else 0)):
            geometry.sphere(
                f"{name}_smoke_{index:02d}",
                collection,
                (x + index * 0.045, y, z + height * 0.56 + 0.13 * index),
                (0.08 + index * 0.02, 0.08 + index * 0.02, 0.055),
                mat(mats, "dust"),
                segments=10,
            )


def add_path(name: str, collection, mats: dict, loc, size=(0.90, 0.86, 0.03), *, kind="earth_light"):
    role = "path_light_earth" if kind == "earth_light" else "stone_light"
    x, y, z = loc
    geometry.box(f"{name}_{kind}_base", collection, loc, size, mat(mats, role, "path_warm"), bevel=0.018)
    if kind == "stone_pebbles":
        for index in range(9):
            px = x - size[0] * 0.38 + (index % 3) * size[0] * 0.28
            py = y - size[1] * 0.30 + (index // 3) * size[1] * 0.24
            geometry.sphere(f"{name}_pebble_{index:02d}", collection, (px, py, z + size[2] * 0.80), (0.070, 0.050, 0.025), mat(mats, "stone_light", "stone_shadow"), segments=8)
    if kind == "stone_blocks":
        for index in range(6):
            px = x - size[0] * 0.30 + (index % 2) * size[0] * 0.30
            py = y - size[1] * 0.30 + (index // 2) * size[1] * 0.22
            geometry.box(f"{name}_stone_block_{index:02d}", collection, (px, py, z + size[2]), (size[0] * 0.24, size[1] * 0.16, size[2] * 1.15), mat(mats, "stone_block", "stone_light"), bevel=0.008, rotation=(0, 0, 0.06 * (index % 2)))


def add_stone_courses(name: str, collection, mats: dict, width: float, depth: float, z: float, rows: int, *, damaged=False):
    material = mat(mats, "damage_char", "stone_shadow") if damaged else mat(mats, "stone_light", "stone_shadow")
    block_h = 0.11
    for row in range(rows):
        count = 5 + row % 2
        y = -depth / 2 - 0.035
        for index in range(count):
            if damaged and (row + index) % 5 == 0:
                continue
            x = -width / 2 + (index + 0.5) * width / count
            geometry.box(
                f"{name}_course_front_{row:02d}_{index:02d}",
                collection,
                (x, y, z + row * block_h),
                (width / count * 0.82, 0.075, block_h * 0.82),
                material,
                bevel=0.010,
            )


def add_scaffold(name: str, collection, mats: dict, *, width=1.8, depth=0.2, height=1.2, y=-0.82):
    plank = mat(mats, "construction_plank", "wood_pale")
    beam = mat(mats, "wood_beam", "wood_dark")
    for x in (-width / 2, 0, width / 2):
        geometry.cylinder(f"{name}_scaffold_post_{x:.1f}", collection, (x, y, height / 2), 0.035, height, plank, vertices=7)
    for z in (height * 0.56, height * 0.88):
        geometry.beam(f"{name}_scaffold_rail_{z:.1f}", collection, (-width / 2 - 0.10, y, z), (width / 2 + 0.10, y, z), 0.045, plank)
    geometry.beam(f"{name}_scaffold_brace", collection, (-width / 2, y - depth, 0.18), (width / 2, y + depth, height), 0.040, beam)


def add_debris(name: str, collection, mats: dict, *, count=5, material_role="wood_dark", z=0.08):
    material = mat(mats, material_role, "damage_char", "wood_dark")
    for index in range(count):
        x = -0.75 + index * 0.30
        y = 0.62 + (index % 2) * 0.18
        geometry.box(
            f"{name}_debris_{index:02d}",
            collection,
            (x, y, z),
            (0.24 + 0.04 * (index % 3), 0.09, 0.075),
            material,
            bevel=0.010,
            rotation=(0.03 * (index % 2), 0.04, index * 0.42),
        )


def add_loose_planks(name: str, collection, mats: dict, loc, *, count=3, length=0.48):
    x, y, z = loc
    material = mat(mats, "construction_plank", "wood_pale")
    for index in range(count):
        geometry.box(
            f"{name}_loose_plank_{index:02d}",
            collection,
            (x + index * 0.08, y + (index % 2) * 0.04, z + index * 0.035),
            (length, 0.11, 0.055),
            material,
            bevel=0.008,
            rotation=(0, 0, -0.18 + index * 0.13),
        )


def add_barrel(name: str, collection, mats: dict, loc, *, radius=0.14, height=0.34, damaged=False):
    body = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, "wood_beam", "wood_dark")
    band = mat(mats, "metal_worn", "steel_light")
    geometry.cylinder(f"{name}_barrel_body", collection, loc, radius, height, body, vertices=14)
    x, y, z = loc
    geometry.box(f"{name}_barrel_band_low", collection, (x, y, z - height * 0.24), (radius * 2.08, 0.035, 0.040), band, bevel=0.004)
    geometry.box(f"{name}_barrel_band_high", collection, (x, y, z + height * 0.24), (radius * 2.08, 0.035, 0.040), band, bevel=0.004)


def add_rope(name: str, collection, mats: dict, start, end, *, width=0.025):
    geometry.beam(name, collection, start, end, width, mat(mats, "rope", "wood_beam"))


def add_sign(name: str, collection, mats: dict, loc, *, board_size=(0.42, 0.07, 0.24), angle=0.0):
    x, y, z = loc
    geometry.box(f"{name}_sign_post", collection, (x, y, z - 0.20), (0.07, 0.07, 0.50), mat(mats, "wood_dark", "wood_beam"), bevel=0.010)
    geometry.box(f"{name}_sign_board", collection, (x, y - 0.02, z + 0.08), board_size, mat(mats, "wood_pale", "wood_beam"), bevel=0.012, rotation=(0, 0, angle))


def add_flag_pole(name: str, collection, mats: dict, loc, *, height=0.62, flag_size=(0.34, 0.22), color_role="roof_red"):
    x, y, z = loc
    geometry.cylinder(f"{name}_flag_pole", collection, (x, y, z + height / 2), 0.018, height, mat(mats, "wood_dark", "metal_worn"), vertices=8)
    geometry.flag(f"{name}_flag_cloth", collection, (x + 0.02, y, z + height * 0.62), flag_size[0], flag_size[1], mat(mats, color_role, "roof_red"))


def add_crack(name: str, collection, mats: dict, loc, *, length=0.32, angle=0.0):
    x, y, z = loc
    geometry.box(f"{name}_crack", collection, (x, y, z), (0.035, 0.024, length), mat(mats, "damage_crack", "damage_char"), bevel=0.0, rotation=(0, 0, angle))


def circular_positions(count: int, radius: float, *, start_angle=0.0):
    for index in range(count):
        angle = start_angle + index * math.tau / count
        yield index, math.cos(angle) * radius, math.sin(angle) * radius, angle
