"""Paint workshop: paired pigment vats, mixer, swatches, and protected late line."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def vat(c, m, level, state, *, x, y, index):
    shell = mat(m, "steel_light" if level >= 5 else "copper")
    edge = mat(m, "roof_gold" if level >= 8 else "dark_metal")
    pigment = mat(m, ("roof_coral", "roof_blue", "roof_gold")[index % 3])
    radius = 0.33 + min(level, 7) * 0.012
    height = 0.57 + min(level, 8) * 0.035
    # Two broad hoops make the mixing vessel legible even in a small sprite.
    g.cylinder(f"vat_{index}_plinth", c, (x, y, 0.17), radius + 0.09, 0.18,
               mat(m, "reinforced_concrete" if level >= 5 else "stone_block"), vertices=20)
    if state == "construction":
        g.cylinder(f"vat_{index}_half_shell", c, (x, y, 0.30), radius, 0.18, shell, vertices=20)
        box(c, f"vat_{index}_unmounted_hoop", (x + 0.45, y - 0.27, 0.13),
            (0.47, 0.07, 0.06), edge)
        return
    if state == "damaged" and index == 1:
        g.cylinder(f"vat_{index}_broken_base", c, (x, y, 0.30), radius, 0.20, shell, vertices=20)
        box(c, f"vat_{index}_fallen_casing", (x + 0.30, y - 0.44, 0.14),
            (0.54, 0.22, 0.10), shell, rotation=(0, 0, -0.23))
        box(c, f"vat_{index}_spill", (x + 0.20, y - 0.27, 0.084),
            (0.50, 0.26, 0.012), pigment, 0.006)
        return
    g.cylinder(f"vat_{index}_shell", c, (x, y, 0.18 + height / 2), radius,
               height, shell, vertices=24)
    for z in (0.28, 0.18 + height * 0.83):
        g.cylinder(f"vat_{index}_hoop_{z:.2f}", c, (x, y, z), radius + 0.025,
                   0.055, edge, vertices=24)
    g.cylinder(f"vat_{index}_pigment", c, (x, y, 0.19 + height), radius - 0.055,
               0.025, pigment, vertices=24)
    if level >= 2 and state == "active":
        g.cylinder(f"vat_{index}_hinge", c, (x, y + 0.22, 0.22 + height),
                   0.055, 0.13, edge, vertices=12)
        box(c, f"vat_{index}_half_lid", (x, y + 0.17, 0.24 + height),
            (radius * 1.76, radius * 0.92, 0.065), shell, 0.023)
    if state == "active":
        g.cylinder(f"vat_{index}_stirrer", c, (x, y, 0.35 + height),
                   0.038, 0.37, mat(m, "dark_metal"), vertices=12)
        box(c, f"vat_{index}_paddle", (x, y, 0.18 + height),
            (radius * 1.15, 0.05, 0.05), mat(m, "wood_pale"), 0.009)


def pigment_rack(c, m, level, state):
    wood = mat(m, "steel_light" if level >= 8 else "wood_beam")
    x, y = -1.05, 0.77
    box(c, "rack_foot", (x, y, 0.14), (0.87, 0.43, 0.14), wood)
    if state == "damaged":
        box(c, "rack_fallen_post", (-1.06, 0.57, 0.13),
            (0.82, 0.08, 0.08), wood, rotation=(0, 0, 0.21))
        return
    for side in (-1, 1):
        box(c, f"rack_post_{side}", (x + side * 0.37, y + 0.13, 0.58),
            (0.075, 0.075, 0.93), wood)
    if state == "construction":
        box(c, "rack_shelf_waiting", (x, -1.18, 0.14), (0.77, 0.20, 0.07), wood)
        return
    for z in (0.50, 0.87):
        box(c, f"rack_shelf_{z}", (x, y + 0.09, z), (0.87, 0.39, 0.075), wood)
    colors = ("roof_coral", "roof_blue", "roof_gold", "roof_green", "amethyst")
    for i in range(3 + min(level // 3, 2)):
        px = x - 0.29 + i * 0.15
        g.cylinder(f"pigment_jar_{i}", c, (px, y, 0.62), 0.058, 0.15,
                   mat(m, "glass_cyan" if level >= 3 else "whitewash"), vertices=12)
        g.cylinder(f"pigment_lid_{i}", c, (px, y, 0.70), 0.065, 0.025,
                   mat(m, colors[i]), vertices=12)


def machine(c, m, level, state):
    x, y = 0.88, 0.68
    base = mat(m, "reinforced_concrete" if level >= 5 else "stone_block")
    steel = mat(m, "steel_light" if level >= 5 else "wood_beam")
    box(c, "mixer_bed", (x, y, 0.19), (0.73, 0.66, 0.20), base, 0.03)
    if state == "construction":
        box(c, "mixer_unmounted_column", (1.21, -0.77, 0.14),
            (0.12, 0.72, 0.12), steel)
        return
    if state == "damaged":
        box(c, "mixer_stump", (x + 0.26, y + 0.15, 0.42),
            (0.12, 0.12, 0.49), steel)
        box(c, "fallen_mixer_arm", (0.81, -0.73, 0.14),
            (0.77, 0.10, 0.10), steel, rotation=(0, 0, -0.21))
        return
    for px in (x - 0.28, x + 0.28):
        box(c, f"mixer_column_{px}", (px, y + 0.15, 0.64),
            (0.105, 0.10, 0.81), steel)
    box(c, "mixer_crossbeam", (x, y + 0.15, 1.06),
        (0.69, 0.16, 0.11), steel)
    g.cylinder("mixer_bowl", c, (x, y - 0.09, 0.42), 0.26, 0.25,
               mat(m, "copper"), vertices=20)
    g.cylinder("mixer_output", c, (x, y - 0.09, 0.55), 0.22, 0.018,
               mat(m, "roof_coral"), vertices=20)
    g.cylinder("mixer_spindle", c, (x, y - 0.09, 0.78), 0.045, 0.51,
               mat(m, "dark_metal"), vertices=12)
    if level >= 3:
        g.cylinder("drive_wheel", c, (x + 0.38, y + 0.16, 0.67),
                   0.19 + level * 0.007, 0.10, mat(m, "copper"), vertices=20,
                   rotation=(0, math.pi / 2, 0))
        box(c, "drive_belt", (x + 0.38, y + 0.16, 0.48),
            (0.05, 0.06, 0.42), mat(m, "rope"))
    if level >= 5:
        box(c, "mixer_guard", (x + 0.31, y - 0.09, 0.68),
            (0.08, 0.46, 0.36), mat(m, "steel_light"))


def late_enclosure(c, m, level, state):
    if level < 5:
        return
    wall = mat(m, "reinforced_concrete")
    frame = mat(m, "steel_light")
    # The back wall stops below the vessels, preserving the colored vats in iso.
    box(c, "rear_wall", (0.32, 1.31, 0.52), (1.89, 0.13, 0.75), wall, 0.025)
    if state == "construction":
        box(c, "roof_panels_waiting", (0.86, -1.01, 0.14),
            (0.74, 0.40, 0.08), frame)
        return
    if state == "damaged":
        box(c, "collapsed_hood", (0.98, 1.01, 0.16),
            (0.84, 0.31, 0.10), frame, rotation=(0, 0, -0.24))
        return
    for px in (-0.58, 1.24):
        box(c, f"hood_post_{px}", (px, 1.25, 0.85),
            (0.11, 0.11, 1.36), frame)
    box(c, "ventilation_hood", (0.34, 1.03, 1.56),
        (1.90, 0.53, 0.18), mat(m, "roof_teal"), 0.03)
    g.cylinder("exhaust", c, (0.93, 1.12, 1.78), 0.13, 0.36,
               mat(m, "steel_light"), vertices=16)
    if level >= 8:
        box(c, "reinforced_hood_lip", (0.34, 0.76, 1.49),
            (1.89, 0.07, 0.08), mat(m, "roof_gold"))
        g.cylinder("precision_gauge", c, (1.20, 0.98, 1.11), 0.10,
                   0.04, mat(m, "glass_cyan"), vertices=20,
                   rotation=(math.pi / 2, 0, 0))
        box(c, "locked_paint_store", (-1.19, -0.16, 0.49),
            (0.47, 0.53, 0.81), wall, 0.03)
        box(c, "store_lock", (-1.19, -0.44, 0.52),
            (0.10, 0.04, 0.12), mat(m, "roof_gold"))
    if level >= 9:
        g.cylinder("light_crystal_socket", c, (-0.57, 1.02, 1.72),
                   0.12, 0.09, mat(m, "steel_light"), vertices=12)
        g.cylinder("light_crystal", c, (-0.57, 1.02, 1.85),
                   0.055, 0.20, mat(m, "amethyst"), vertices=6)


def add_paint_workshop(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    floor = mat(mats, "reinforced_concrete" if level >= 5 else "stone_block")
    box(collection, "work_floor", (0.0, 0.10, 0.11),
        (2.72, 2.42, 0.07), floor, 0.02)
    if level >= 3:
        for px in (-1.22, -0.58, 0.06, 0.70, 1.23):
            box(collection, f"floor_joint_{px}", (px, -0.58, 0.155),
                (0.045, 1.04, 0.024), mat(mats, "steel_light" if level >= 8 else "brick_warm"), 0.005)
    vat(collection, mats, level, state, x=-0.35, y=-0.11, index=0)
    if level >= 2:
        vat(collection, mats, level, state, x=0.42, y=-0.18, index=1)
    if level >= 7:
        vat(collection, mats, level, state, x=0.15, y=0.73, index=2)
    pigment_rack(collection, mats, level, state)
    machine(collection, mats, level, state)
    late_enclosure(collection, mats, level, state)
    # Bottles and swatch cards are separate from the production silhouette.
    if state == "active":
        for i in range(2 + level // 2):
            px = -1.14 + (i % 3) * 0.17
            py = -0.80 - (i // 3) * 0.19
            g.cylinder(f"paint_tin_{i}", collection, (px, py, 0.20),
                       0.067, 0.19, mat(mats, "steel_light"), vertices=12)
            g.cylinder(f"paint_tin_lid_{i}", collection, (px, py, 0.31),
                       0.069, 0.022, mat(mats, ("roof_coral", "roof_blue", "roof_gold")[i % 3]), vertices=12)
        for i, role in enumerate(("roof_coral", "roof_blue", "roof_gold")):
            box(collection, f"swatch_{i}", (0.33 + i * 0.24, -1.08, 0.166),
                (0.19, 0.28, 0.020), mat(mats, role), 0.005)
    elif state == "construction":
        for i in range(3):
            box(collection, f"stored_steel_{i}", (0.77, -0.88 + i * 0.12, 0.16 + i * 0.06),
                (0.62, 0.10, 0.08), mat(mats, "steel_light"))
    else:
        for i in range(4):
            box(collection, f"debris_{i}", (-0.99 + i * 0.19, -0.93, 0.13),
                (0.17, 0.12, 0.06), mat(mats, "steel_light" if i % 2 else "stone_block"),
                rotation=(0, 0, i * 0.22))
