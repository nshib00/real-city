"""Tile factory: fired-clay kiln, shaped tile molds and progressive production line."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def _tile(c, name, x, y, z, m, angle=0):
    """Raised lip and longitudinal ridge keep a single roof tile readable."""
    box(c, name, (x, y, z), (0.19, 0.29, 0.055), m, 0.022, (0, 0, angle))
    box(c, name + "_lip", (x, y - 0.115, z + 0.034),
        (0.19, 0.055, 0.045), m, 0.012, (0, 0, angle))


def _kiln(c, m, level, state):
    brick = mat(m, "brick_warm")
    light = mat(m, "brick_light")
    stone = mat(m, "stone_block")
    concrete = mat(m, "reinforced_concrete")
    iron = mat(m, "dark_metal")
    clay = mat(m, "soil_light")
    body = concrete if level >= 8 else brick
    base = concrete if level >= 8 else stone if level >= 3 else brick
    h = 0.67 + level * 0.065
    w = 1.00 + level * 0.035
    x, y = 0.43, 0.39
    box(c, "kiln_base", (x, y, 0.18), (w + 0.18, 1.10, 0.20), base, 0.03)
    if state == "construction":
        box(c, "kiln_first_course", (x, y, 0.39), (w, 0.95, 0.24), brick, 0.025)
        box(c, "kiln_unfinished_left", (x - w * 0.33, y + 0.18, 0.59),
            (w * 0.33, 0.60, 0.35), body, 0.022)
        box(c, "kiln_loose_crown", (0.88, -0.78, 0.14), (0.54, 0.26, 0.11), brick, 0.021)
        for i in range(3):
            box(c, f"unlaid_firebrick_{i}", (0.59 + i * 0.19, -0.84, 0.11),
                (0.17, 0.21, 0.10), light, 0.015)
        return
    if state == "damaged":
        box(c, "kiln_broken_lower", (x, y, 0.28 + h * 0.24),
            (w, 0.94, h * 0.48), body, 0.03)
        box(c, "kiln_broken_rear_pier", (x - w * 0.38, y + 0.29, 0.28 + h * 0.53),
            (0.25, 0.26, h * 0.58), body, 0.027)
        box(c, "kiln_open_firebox", (x, y - 0.48, 0.49),
            (0.50, 0.05, 0.30), iron, 0.02)
        for i in range(5):
            box(c, f"fallen_kiln_brick_{i}", (0.06 + (i % 3) * 0.27,
                -0.69 - (i // 3) * 0.23, 0.11), (0.23, 0.15, 0.10),
                light if i % 2 else brick, 0.018, (0, 0, i * 0.13))
        if level >= 2:
            box(c, "fallen_chimney_segment", (1.06, 0.85, 0.15),
                (0.43, 0.26, 0.18), body, 0.025, (0, 0, 0.28))
        return
    box(c, "kiln_fired_shell", (x, y, 0.28 + h / 2), (w, 0.94, h), body, 0.06)
    box(c, "kiln_arch_cap", (x, y, 0.34 + h), (w * 0.95, 0.88, 0.20), light, 0.055)
    box(c, "kiln_mouth", (x, -0.105, 0.56), (0.47, 0.060, 0.43), iron, 0.06)
    for side in (-1, 1):
        box(c, f"firebrick_jamb_{side}", (x + side * 0.29, -0.15, 0.56),
            (0.12, 0.12, 0.51), light, 0.020)
    box(c, "firebrick_lintel", (x, -0.15, 0.84), (0.68, 0.13, 0.12), light)
    if level >= 2:
        ch = 0.40 + level * 0.08
        box(c, "kiln_chimney", (0.84, 0.66, 0.38 + h + ch / 2),
            (0.28, 0.28, ch), body, 0.025)
        box(c, "chimney_lip", (0.84, 0.66, 0.41 + h + ch),
            (0.36, 0.36, 0.10), light, 0.020)
    if level >= 3:
        for side in (-1, 1):
            box(c, f"stone_heat_buttress_{side}", (x + side * (w / 2 + 0.07),
                y, 0.55), (0.15, 0.74, 0.68), base, 0.03)
    if level >= 5:
        box(c, "iron_kiln_door", (x, -0.18, 0.57), (0.40, 0.065, 0.34), iron, 0.02)
        for z in (0.42, 0.70 + h * 0.52):
            box(c, f"kiln_iron_band_{z:.2f}", (x, y, z),
                (w + 0.035, 0.98, 0.065), mat(m, "steel_light"), 0.012)
    if level >= 8:
        box(c, "kiln_extract_duct", (0.90, 0.92, 0.60 + h),
            (0.18, 0.56, 0.18), mat(m, "steel_light"), 0.021)
        box(c, "kiln_temperature_glass", (0.48, -0.19, 0.94),
            (0.18, 0.03, 0.16), mat(m, "glass_cyan"), 0.012)
    if level >= 10:
        box(c, "kiln_copper_crest", (x, y, 0.46 + h),
            (0.63, 0.11, 0.10), mat(m, "copper"), 0.018)


def _forming(c, m, level, state):
    wood = mat(m, "wood_pale")
    beam = mat(m, "wood_beam")
    iron = mat(m, "dark_metal")
    steel = mat(m, "steel_light")
    clay = mat(m, "soil_light")
    x, y = -0.65, -0.46
    box(c, "forming_table_top", (x, y, 0.61), (1.14, 0.69, 0.12),
        steel if level >= 5 else wood, 0.026)
    for sx in (-0.46, 0.46):
        for sy in (-0.22, 0.22):
            box(c, f"forming_leg_{sx}_{sy}", (x + sx, y + sy, 0.34),
                (0.10, 0.10, 0.49), iron if level >= 5 else beam, 0.013)
    if state == "construction":
        box(c, "unmounted_mold", (-1.28, 0.35, 0.13),
            (0.37, 0.30, 0.10), wood, 0.016)
        return
    if state == "damaged":
        box(c, "broken_mold_on_floor", (-1.13, -0.91, 0.12),
            (0.39, 0.27, 0.08), iron, 0.012, (0, 0, -0.22))
        _tile(c, "fallen_raw_tile", -0.70, -0.92, 0.12, clay, 0.32)
        return
    for i in range(3):
        _tile(c, f"raw_tile_mold_{i}", x - 0.35 + i * 0.34,
              y, 0.70, clay)
        box(c, f"mold_side_{i}", (x - 0.35 + i * 0.34, y + 0.20, 0.70),
            (0.25, 0.055, 0.09), iron if level >= 3 else wood, 0.01)
    if level >= 4:
        for sx in (-0.43, 0.43):
            box(c, f"press_post_{sx}", (x + sx, y, 1.02),
                (0.09, 0.09, 0.79), steel, 0.013)
        box(c, "press_crosshead", (x, y, 1.43), (1.03, 0.20, 0.12), steel, 0.019)
        box(c, "press_platen", (x, y, 1.09), (0.83, 0.45, 0.12), iron, 0.024)
        if level >= 5:
            g.cylinder("copper_drive_wheel", c, (-0.05, y, 0.86),
                       0.22, 0.10, mat(m, "copper"), vertices=18,
                       rotation=(0, math.pi / 2, 0))
    if level >= 8:
        box(c, "closed_feed_cover", (x, y, 1.53),
            (1.15, 0.66, 0.13), mat(m, "reinforced_concrete"), 0.032)
        box(c, "feed_window", (x, y - 0.34, 1.29),
            (0.58, 0.04, 0.17), mat(m, "glass_cyan"), 0.012)


def _drying_and_output(c, m, level, state):
    wood = mat(m, "wood_pale")
    beam = mat(m, "wood_beam")
    fired = mat(m, "brick_warm")
    raw = mat(m, "soil_light")
    iron = mat(m, "dark_metal")
    count = 1 + (level >= 2) + (level >= 6)
    for row in range(count):
        x = -1.12 + row * 0.42
        y = 0.76
        if state == "damaged" and row >= count // 2:
            box(c, f"fallen_rack_{row}", (x, y, 0.12),
                (0.32, 0.58, 0.075), beam, 0.012, (0, 0, 0.24))
            _tile(c, f"fallen_tile_{row}", x, y - 0.18, 0.15, raw, 0.22)
            continue
        for sy in (-0.29, 0.29):
            box(c, f"drying_leg_{row}_{sy}", (x, y + sy, 0.40),
                (0.07, 0.07, 0.61), beam, 0.012)
        if state == "construction" and row > 0:
            continue
        box(c, f"rack_shelf_{row}", (x, y, 0.72),
            (0.36, 0.70, 0.065), wood, 0.014)
        for k in range(2):
            _tile(c, f"drying_tile_{row}_{k}", x,
                  y - 0.15 + k * 0.29, 0.79, raw)
    if state == "construction":
        box(c, "tile_bundle_unfinished", (1.13, -0.79, 0.16),
            (0.42, 0.43, 0.12), wood, 0.014)
        return
    box(c, "finished_tile_pallet", (1.18, -0.80, 0.12),
        (0.62, 0.72, 0.09), wood, 0.018)
    for i in range(3 + level // 2):
        _tile(c, f"finished_tile_{i}", 0.99 + (i % 2) * 0.26,
              -0.96 + (i // 2) * 0.18, 0.21 + (i // 4) * 0.07,
              fired, 0.12 if state == "damaged" and i % 2 else 0)
    if level >= 1:
        box(c, "coal_bin", (-1.36, 0.07, 0.20),
            (0.34, 0.48, 0.23), wood, 0.02)
        for i in range(3):
            box(c, f"coal_piece_{i}", (-1.44 + i * 0.09, 0.04, 0.35),
                (0.09, 0.15, 0.09), mat(m, "coal"), 0.013)
    if level >= 6 and state == "active":
        for sx in (-1.34, -0.46):
            box(c, f"drying_canopy_post_{sx}", (sx, 0.74, 0.68),
                (0.08, 0.08, 1.16), beam, 0.012)
        box(c, "drying_canopy", (-0.90, 0.74, 1.31),
            (1.06, 0.86, 0.12), mat(m, "roof_teal"), 0.025)
    if level >= 8 and state == "active":
        box(c, "protected_tile_store", (1.15, -0.76, 0.62),
            (0.78, 0.83, 0.12), mat(m, "reinforced_concrete"), 0.026)
        for sx in (0.85, 1.45):
            box(c, f"store_guard_post_{sx}", (sx, -0.78, 0.39),
                (0.08, 0.08, 0.53), mat(m, "steel_light"), 0.012)


def add_tile_factory(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    _kiln(collection, mats, level, state)
    _forming(collection, mats, level, state)
    _drying_and_output(collection, mats, level, state)
