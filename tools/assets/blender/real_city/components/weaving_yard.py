"""Open Aeolian weaving yard with visible warp, cloth and progressive drive."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, pos, size, material, bevel=0.014, rotation=(0, 0, 0)):
    return g.box(name, c, pos, size, material, bevel=bevel, rotation=rotation)


def roll(c, name, pos, length, radius, fabric, end):
    g.cylinder(name, c, pos, radius, length, fabric, vertices=20,
               rotation=(0, math.pi / 2, 0))
    for side in (-1, 1):
        g.cylinder(f"{name}_end_{side}", c,
                   (pos[0] + side * length * 0.48, pos[1], pos[2]),
                   radius * 0.65, 0.018, end, vertices=16,
                   rotation=(0, math.pi / 2, 0))


def loom(c, m, level, state, *, x=-0.35, y=-0.22, scale=1.0, suffix="main"):
    wood = mat(m, "wood_beam")
    pale = mat(m, "wood_pale")
    metal = mat(m, "steel_light" if level >= 7 else "copper" if level >= 5 else "wood_dark")
    thread = mat(m, "whitewash")
    cloth = mat(m, "roof_teal" if level >= 4 else "whitewash")
    width = (1.27 + min(level, 7) * 0.035) * scale
    h = (1.26 + min(level, 8) * 0.045) * scale
    for side in (-1, 1):
        px = x + side * width / 2
        if state == "damaged" and side == 1:
            box(c, f"{suffix}_fallen_post", (x + 0.70, y - 0.72, 0.14),
                (0.78, 0.10, 0.11), wood, rotation=(0, 0, -0.33))
            continue
        box(c, f"{suffix}_post_{side}", (px, y, 0.12 + h / 2),
            (0.12, 0.13, h), metal if level >= 8 else wood, 0.019)
        box(c, f"{suffix}_foot_{side}", (px, y, 0.15),
            (0.23, 0.72, 0.10), wood)
    for z in (0.48, 0.94):
        box(c, f"{suffix}_cross_{z}", (x, y, z * scale + 0.12),
            (width + 0.11, 0.12, 0.12), wood, 0.02)
    if state == "construction":
        box(c, f"{suffix}_unmounted_beam", (x - 0.15, -0.94, 0.12),
            (width * 0.78, 0.14, 0.12), pale)
        return
    if state == "damaged":
        box(c, f"{suffix}_broken_top", (x - width * 0.24, y, h + 0.07),
            (width * 0.52, 0.13, 0.12), wood)
        box(c, f"{suffix}_torn_cloth", (x - 0.24, y - 0.11, 0.64),
            (width * 0.40, 0.045, 0.45), cloth, rotation=(0, 0, -0.12))
        return
    box(c, f"{suffix}_top_rail", (x, y, h + 0.09),
        (width + 0.13, 0.15, 0.13), metal if level >= 8 else wood, 0.02)
    for i in range(9):
        tx = x - width * 0.40 + i * width * 0.10
        box(c, f"{suffix}_warp_{i}", (tx, y - 0.045, 0.82),
            (0.016, 0.019, 0.66), thread, 0.004)
    box(c, f"{suffix}_woven_panel", (x, y - 0.077, 0.53),
        (width * 0.79, 0.045, 0.46), cloth, 0.018)
    box(c, f"{suffix}_cloth_hem", (x, y - 0.109, 0.30),
        (width * 0.79, 0.045, 0.055), mat(m, "copper"), 0.008)
    box(c, f"{suffix}_shuttle", (x + width * 0.18, y - 0.17, 0.69),
        (0.32, 0.09, 0.075), pale, 0.025, (0, 0, 0.15))
    for side in (-1, 1):
        box(c, f"{suffix}_pedal_{side}", (x + side * 0.20, y - 0.54, 0.17),
            (0.18, 0.51, 0.055), pale, 0.012)
    if level >= 5:
        g.cylinder(f"{suffix}_drive_wheel", c,
                   (x + width / 2 + 0.13, y + 0.11, 0.89),
                   0.23 + level * 0.007, 0.09, metal, vertices=20,
                   rotation=(0, math.pi / 2, 0))
        box(c, f"{suffix}_belt", (x + width / 2 + 0.13, y + 0.11, 0.59),
            (0.055, 0.045, 0.42), mat(m, "rope"), 0.012)
    if level >= 8:
        box(c, f"{suffix}_guard", (x + width / 2 + 0.17, y - 0.10, 0.54),
            (0.09, 0.49, 0.34), mat(m, "steel_light"), 0.026)


def canopy(c, m, level, state):
    if level < 2:
        return
    height = 1.61 + min(level, 8) * 0.045
    for x in (-1.23, 0.78):
        if state == "damaged" and x > 0:
            continue
        box(c, f"canopy_post_{x}", (x, 0.72, 0.12 + height / 2),
            (0.11, 0.11, height), mat(m, "steel_light" if level >= 8 else "wood_beam"), 0.019)
    box(c, "canopy_back_beam", (-0.23, 0.72, height + 0.09),
        (2.14, 0.14, 0.15), mat(m, "wood_beam"), 0.021)
    if state == "construction":
        box(c, "canopy_roof_pile", (0.86, 1.02, 0.12),
            (0.88, 0.23, 0.09), mat(m, "wood_pale"))
        return
    if state == "damaged":
        box(c, "fallen_canopy", (0.80, 0.87, 0.18),
            (0.96, 0.56, 0.09), mat(m, "roof_teal"), rotation=(0, 0, -0.22))
        return
    box(c, "woven_sunshade", (-0.23, 0.70, height + 0.14),
        (2.18, 0.79, 0.085), mat(m, "roof_teal"), 0.022,
        rotation=(0.16, 0, 0))
    for x in (-0.96, -0.24, 0.48):
        box(c, f"sunshade_stripe_{x}", (x, 0.70, height + 0.19),
            (0.13, 0.79, 0.025), mat(m, "whitewash"), 0.007,
            rotation=(0.16, 0, 0))
    if level >= 9:
        box(c, "canopy_reinforcement", (-0.23, 1.02, height + 0.15),
            (2.20, 0.09, 0.10), mat(m, "steel_light"), 0.012)


def output_and_details(c, m, level, state):
    pale = mat(m, "wood_pale")
    fiber = mat(m, "whitewash")
    rope = mat(m, "rope")
    box(c, "flax_input_crate", (-1.23, -0.61, 0.22),
        (0.44, 0.48, 0.28), pale, 0.022)
    for i in range(4 + min(level, 5)):
        box(c, f"flax_bundle_{i}", (-1.35 + (i % 3) * 0.13,
            -0.63 + (i // 3) * 0.11, 0.41),
            (0.055, 0.24, 0.13), fiber, 0.009,
            rotation=(0, 0, i * 0.15))
    if state == "construction":
        box(c, "stacked_planks", (0.97, -0.88, 0.14),
            (0.74, 0.30, 0.12), pale)
        return
    for i in range(2 + level // 2):
        roll(c, f"finished_fabric_{i}",
             (0.92, -0.78 + (i // 3) * 0.20, 0.20 + (i % 3) * 0.14),
             0.48, 0.105, mat(m, "roof_teal" if i % 2 else "whitewash"),
             mat(m, "roof_gold" if level >= 9 else "rope"))
    if level >= 2:
        for i in range(2 + level // 3):
            g.cylinder(f"rope_coil_{i}", c,
                       (-1.18 + (i % 2) * 0.13, 0.05 + (i // 2) * 0.13, 0.11),
                       0.10, 0.065, rope, vertices=16)
    if level >= 4:
        g.cylinder("dye_vat", c, (1.20, 0.48, 0.29), 0.29, 0.38,
                   mat(m, "copper" if level >= 5 else "stone_block"), vertices=20)
        g.cylinder("dye_surface", c, (1.20, 0.48, 0.49), 0.24, 0.018,
                   mat(m, "roof_blue"), vertices=20)
    if level >= 7 and state == "active":
        box(c, "fabric_store_roof", (0.98, 1.10, 1.03),
            (0.77, 0.55, 0.10), mat(m, "reinforced_concrete" if level >= 8 else "wood_pale"), 0.025)
        for x in (0.69, 1.27):
            box(c, f"store_post_{x}", (x, 1.11, 0.57),
                (0.07, 0.08, 0.89), mat(m, "steel_light"), 0.012)
    if level >= 9 and state == "active":
        box(c, "calibration_badge", (0.16, -0.36, 1.33),
            (0.17, 0.045, 0.14), mat(m, "roof_gold"), 0.02)
    if level >= 10 and state == "active":
        box(c, "light_crystal_housing", (-1.21, 0.72, 1.31),
            (0.17, 0.14, 0.15), mat(m, "copper"), 0.022)
        g.cylinder("light_crystal", c, (-1.21, 0.72, 1.45),
                   0.055, 0.15, mat(m, "amethyst"), vertices=6)


def add_weaving_yard(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    if level >= 4:
        box(collection, "stone_work_area", (-0.35, -0.13, 0.105),
            (1.55, 1.13, 0.07),
            mat(mats, "reinforced_concrete" if level >= 8 else "stone_block"), 0.025)
    if level >= 5:
        for side in (-1, 1):
            box(collection, f"brick_work_area_edge_{side}",
                (-0.35 + side * 0.70, -0.13, 0.15),
                (0.14, 1.13, 0.075), mat(mats, "brick_warm"), 0.016)
    loom(collection, mats, level, state)
    if level >= 7 and state == "active":
        loom(collection, mats, level, state, x=-0.67, y=0.74, scale=0.49,
             suffix="secondary")
    canopy(collection, mats, level, state)
    output_and_details(collection, mats, level, state)
