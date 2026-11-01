"""Осадный двор: открытый пресс и бронированная сборочная камера."""

import math

from .. import geometry as g
from .common import mat


def add_siege_yard(c, m, *, level: int, state: str) -> None:
    building = state in {"active", "damaged"}
    damaged = state == "damaged"
    ruined = state == "ruined"
    construction = state == "construction"

    def box(name, pos, size, role, *, bevel=0.022, rotation=(0, 0, 0)):
        return g.box(name, c, pos, size, mat(m, role), bevel=bevel, rotation=rotation)

    def cylinder(name, pos, radius, depth, role, *, vertices=16, rotation=(0, 0, 0)):
        return g.cylinder(name, c, pos, radius, depth, mat(m, role), vertices=vertices, rotation=rotation)

    # Shared rigid floor: ground.add_ground_tile is handled by the orchestrator.
    box("concrete_work_slab", (0, 0, 0.105), (2.64, 2.50, 0.075), "reinforced_concrete")
    for x in (-1.14, 1.14):
        box(f"slab_steel_edge_{x}", (x, 0, 0.15), (0.075, 2.40, 0.07), "steel_light")
    for y in (-1.08, 1.08):
        box(f"slab_steel_edge_{y}", (0, y, 0.15), (2.36, 0.075, 0.07), "steel_light")
    for x in (-0.91, -0.35, 0.35, 0.91):
        box(f"floor_plate_{x}", (x, -0.76, 0.157), (0.43, 0.43, 0.018), "armor_dark", bevel=0.008)

    # The press is the identifying shape at every level, including damage and ruins.
    for x in (-0.61, 0.61):
        box(f"press_foot_{x}", (x, -0.08, 0.24), (0.29, 0.62, 0.19), "steel_light")
    box("press_bed", (0, -0.08, 0.37), (1.60, 0.84, 0.20), "armor_dark")
    box("press_work_plate", (0, -0.08, 0.49), (1.27, 0.56, 0.045), "steel_light")
    post_height = 0.45 if ruined else 0.75 if construction else 1.07
    for x in (-0.63, 0.63):
        if damaged and x > 0:
            post_height_here = 0.56
        else:
            post_height_here = post_height
        box(f"press_upright_{x}", (x, -0.08, 0.51 + post_height_here / 2),
            (0.19, 0.20, post_height_here), "dark_metal")
        for z in (0.63, 0.87) if post_height_here > 0.75 else (0.64,):
            box(f"upright_rivet_{x}_{z}", (x, -0.195, z), (0.07, 0.024, 0.07), "copper", bevel=0.006)
    if building and not damaged:
        box("press_crosshead", (0, -0.08, 1.64), (1.61, 0.31, 0.22), "steel_light")
        cylinder("hydraulic_ram", (0, -0.08, 1.29), 0.20, 0.60, "copper", vertices=20)
        box("ram_shoe", (0, -0.08, 0.99), (0.83, 0.54, 0.14), "armor")
    elif damaged:
        box("bent_press_crosshead", (-0.20, -0.08, 1.40), (1.26, 0.31, 0.19),
            "steel_light", rotation=(0, 0.16, -0.15))
        cylinder("jammed_hydraulic_ram", (-0.18, -0.08, 1.05), 0.18, 0.45,
                 "copper", rotation=(0, 0.27, 0))
    elif ruined:
        box("fallen_press_crosshead", (0.36, -0.68, 0.29), (1.45, 0.29, 0.20),
            "dark_metal", rotation=(0, 0, 0.36))
        cylinder("fallen_ram", (-0.31, -0.80, 0.25), 0.15, 0.52, "copper",
                 rotation=(0, math.pi / 2, 0.4))
    else:
        box("unmounted_crosshead", (0.89, -0.79, 0.28), (0.79, 0.23, 0.16), "steel_light")

    # Framed canopy: progressively less of the actual structure remains.
    canopy_posts = [(-1.07, 0.62), (1.07, 0.62), (-1.07, -0.55), (1.07, -0.55)]
    for i, (x, y) in enumerate(canopy_posts):
        height = 0.44 if ruined else 0.77 if construction and i > 1 else 1.62
        if damaged and i == 3:
            height = 0.49
        box(f"canopy_post_{i}", (x, y, 0.17 + height / 2), (0.13, 0.13, height), "dark_metal")
        box(f"post_armor_foot_{i}", (x, y, 0.37), (0.22, 0.22, 0.20), "armor")
    if not ruined:
        box("canopy_rear_beam", (0, 0.62, 1.80), (2.29, 0.17, 0.18), "steel_light")
        if not construction and not damaged:
            box("canopy_front_beam", (0, -0.55, 1.80), (2.29, 0.17, 0.18), "steel_light")
        for i, x in enumerate((-1.0, -0.50, 0, 0.50, 1.0)):
            if (construction and i > 1) or (damaged and i > 2):
                continue
            box(f"canopy_rafter_{i}", (x, 0.04, 1.87), (0.10, 1.36, 0.10), "steel_light")
        if building:
            for i, x in enumerate((-0.86, -0.43, 0, 0.43, 0.86)):
                if damaged and i > 1:
                    continue
                box(f"armor_roof_panel_{i}", (x, 0.04, 1.94), (0.43, 1.31, 0.055),
                    "armor" if i % 2 else "armor_dark", bevel=0.012)
    if damaged or ruined:
        for i in range(5 if damaged else 9):
            x = -0.94 + (i % 5) * 0.44
            y = -1.04 + (i // 5) * 0.31
            box(f"fallen_armor_{i}", (x, y, 0.23), (0.31, 0.21, 0.06),
                "armor_dark", rotation=(0, 0, 0.17 * i))

    # Level 1 is open; level 2 encloses the right assembly chamber.
    if level == 2:
        box("chamber_foundation", (0.84, 0.72, 0.28), (0.74, 0.83, 0.23), "reinforced_concrete")
        if not ruined:
            wall_h = 0.54 if construction else 0.72 if damaged else 1.08
            for j, y in enumerate((0.33, 1.07)):
                if damaged and j == 0:
                    continue
                box(f"chamber_wall_{j}", (0.83, y, 0.40 + wall_h / 2),
                    (0.82, 0.12, wall_h), "armor_dark")
            box("chamber_side_wall", (1.20, 0.70, 0.40 + wall_h / 2),
                (0.12, 0.70, wall_h), "armor")
            if building and not damaged:
                box("chamber_roof", (0.84, 0.70, 1.57), (0.95, 0.97, 0.10), "armor")
                for x in (0.57, 1.11):
                    box(f"chamber_roof_rib_{x}", (x, 0.70, 1.64),
                        (0.08, 0.99, 0.10), "steel_light")
                box("chamber_hatch", (0.76, 0.28, 0.98), (0.38, 0.055, 0.57), "steel_light")
        if ruined:
            box("fallen_chamber_roof", (0.84, 0.79, 0.45), (0.91, 0.76, 0.10),
                "armor", rotation=(0.13, -0.17, 0.15))

    # Munition shapes are unarmed, stationary shells; construction has no finished charge.
    if state == "active":
        for x in (-0.84, -0.47):
            box(f"mine_cradle_{x}", (x, 0.82, 0.34), (0.28, 0.37, 0.18), "wood_beam")
            cylinder(f"mine_shell_{x}", (x, 0.82, 0.57), 0.16, 0.31,
                     "armor_dark", vertices=16)
            cylinder(f"mine_cap_{x}", (x, 0.82, 0.74), 0.10, 0.05, "copper")
        if level == 2:
            box("breach_shell_cradle", (0.84, -0.86, 0.32), (0.52, 0.38, 0.20), "wood_beam")
            cylinder("breach_shell", (0.84, -0.86, 0.54), 0.21, 0.32,
                     "armor", vertices=20)
            cylinder("breach_shell_collar", (0.84, -0.86, 0.72), 0.16, 0.055, "copper")
    if construction:
        for i in range(3):
            box(f"loose_steel_beam_{i}", (-0.85 + i * 0.24, 0.88, 0.25 + i * 0.07),
                (0.66, 0.10, 0.11), "steel_light")
    if damaged or ruined:
        for i in range(3):
            cylinder(f"empty_shell_{i}", (-0.86 + i * 0.35, 0.89, 0.23),
                     0.14, 0.23, "armor_dark", rotation=(math.pi / 2, 0, 0.19 * i))
