"""Steampunk mechanical workshop with a lathe, flywheels and copper steam pipes."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def gear(c, m, name, x, y, z, radius, teeth=10):
    metal = mat(m, "copper")
    g.cylinder(name + "_wheel", c, (x, y, z), radius, 0.11, metal,
               vertices=24, rotation=(math.pi / 2, 0, 0))
    g.cylinder(name + "_hub", c, (x, y - 0.075, z), radius * 0.23, 0.16,
               mat(m, "dark_metal"), vertices=16, rotation=(math.pi / 2, 0, 0))
    for i in range(teeth):
        angle = 2 * math.pi * i / teeth
        box(c, f"{name}_tooth_{i}",
            (x + radius * math.sin(angle), y, z + radius * math.cos(angle)),
            (0.12, 0.15, 0.10), metal, 0.014, (0, angle, 0))


def floor(c, m):
    # Identical permanent floor for active, construction and damaged.
    box(c, "brick_workshop_floor", (0, 0.08, 0.105), (2.76, 2.48, 0.07), mat(m, "brick_warm"), 0.012)
    for i in range(5):
        box(c, f"workshop_floor_joint_{i}", (-1.08 + i * 0.54, 0.0, 0.146),
            (0.020, 2.25, 0.010), mat(m, "brick_light"), 0.002)
    for i in range(3):
        box(c, f"plank_walkway_{i}", (0.63 + i * 0.17, -0.58, 0.163),
            (0.15, 1.08, 0.035), mat(m, "wood_pale"), 0.008)


def shell(c, m, level, state):
    brick, beam = mat(m, "brick_warm"), mat(m, "wood_beam")
    steel, copper = mat(m, "steel_light"), mat(m, "copper")
    if state == "construction":
        box(c, "rear_wall_half", (-0.72, 1.23, 0.49), (1.20, 0.16, 0.71), brick)
        for x in (-1.26, 1.26):
            box(c, f"unfinished_post_{x}", (x, 1.13, 0.73), (0.13, 0.15, 1.25), beam)
        if level >= 4:
            box(c, "unmounted_drive_frame", (0.64, 0.99, 0.47), (0.16, 0.16, 0.72), steel)
        if level >= 7:
            box(c, "unmounted_roof_beam", (0.20, -1.03, 0.21), (1.36, 0.14, 0.12), steel)
        if level >= 2:
            box(c, "unmounted_flywheel_plate", (-0.78, -0.87, 0.19), (0.37, 0.31, 0.07), copper)
        if level >= 8:
            box(c, "precision_gantry_waiting", (-0.30, -1.02, 0.29), (0.90, 0.12, 0.12), mat(m, "armor"))
        return
    if state == "damaged":
        box(c, "surviving_brick_pier", (-0.98, 1.20, 0.65), (0.60, 0.17, 1.02), brick)
        box(c, "surviving_left_post", (-1.26, 1.11, 0.80), (0.13, 0.16, 1.36), beam)
        box(c, "fallen_wall_block", (0.75, 0.64, 0.20), (0.62, 0.40, 0.13), brick,
            rotation=(0, 0, 0.26))
        box(c, "fallen_roof_iron", (-0.48, -0.91, 0.20), (0.71, 0.38, 0.10), steel,
            rotation=(0, 0, -0.28))
        if level >= 5:
            box(c, "broken_pipe_on_floor", (0.87, 0.78, 0.19), (0.67, 0.09, 0.09), copper,
                rotation=(0, 0, 0.25))
        if level >= 2:
            g.cylinder("fallen_flywheel", c, (-0.78, -0.82, 0.20), 0.25, 0.08,
                       copper, vertices=16)
        if level >= 8:
            box(c, "fallen_gantry_chunk", (0.53, -0.97, 0.23), (0.61, 0.16, 0.10), mat(m, "armor"),
                rotation=(0, 0, -0.28))
        return
    box(c, "full_rear_brick_wall", (0, 1.23, 0.73), (2.61, 0.17, 1.19), brick, 0.025)
    for x in (-1.26, 1.26):
        box(c, f"full_structural_post_{x}", (x, 1.13, 0.90), (0.14, 0.17, 1.62), beam)
    box(c, "upper_timber_lintel", (0, 1.11, 1.70), (2.69, 0.20, 0.15), beam)
    # Large exposed gear crowns the machine, never concealed by the roof.
    if level >= 3:
        box(c, "steam_pipe_riser", (1.04, 1.01, 0.91), (0.11, 0.11, 1.36), copper)
        box(c, "steam_pipe_elbow", (0.80, 1.02, 1.55), (0.59, 0.11, 0.11), copper)
        g.cylinder("pressure_valve", c, (0.55, 0.94, 1.57), 0.12, 0.09,
                   mat(m, "roof_gold"), vertices=12, rotation=(math.pi / 2, 0, 0))
    if level >= 5:
        box(c, "iron_exhaust_post", (-0.99, 1.03, 1.80), (0.23, 0.20, 1.33), steel)
        box(c, "exhaust_cowl", (-0.99, 1.03, 2.45), (0.40, 0.39, 0.19), mat(m, "armor"))
        box(c, "protected_drive_hood", (0.60, 0.95, 1.81), (0.80, 0.42, 0.12), mat(m, "roof_teal"))
    if level >= 7:
        box(c, "reinforced_roof_lintel", (0, 1.13, 1.89), (2.75, 0.26, 0.16), steel)
        for x in (-0.71, 0.12, 0.82):
            box(c, f"roof_rivet_{x}", (x, 0.976, 1.89), (0.08, 0.035, 0.08), copper, 0.008)
    if level >= 8:
        box(c, "precision_gantry", (0.12, 0.84, 2.12), (2.12, 0.19, 0.13), mat(m, "armor"))
        for x in (-0.88, 0.92):
            box(c, f"gantry_support_{x}", (x, 0.95, 1.84), (0.12, 0.18, 0.55), steel)
    if level >= 10:
        box(c, "final_copper_crown", (0.12, 0.84, 2.24), (2.22, 0.10, 0.07), copper, 0.012)


def lathe(c, m, level, state):
    steel, dark, copper = mat(m, "steel_light"), mat(m, "dark_metal"), mat(m, "copper")
    box(c, "lathe_base", (-0.26, -0.06, 0.28), (1.37, 0.68, 0.22), dark, 0.028)
    for x in (-0.79, 0.27):
        box(c, f"lathe_foot_{x}", (x, -0.06, 0.19), (0.13, 0.53, 0.17), steel)
    if state == "construction":
        box(c, "lathe_unmounted_rail", (-0.20, -0.05, 0.46), (0.90, 0.08, 0.09), steel)
        return
    if state == "damaged":
        box(c, "lathe_broken_stock", (-0.70, -0.05, 0.51), (0.35, 0.37, 0.37), steel)
        box(c, "lathe_fallen_rail", (0.37, -0.78, 0.18), (0.71, 0.10, 0.08), copper,
            rotation=(0, 0, 0.23))
        return
    box(c, "lathe_rail_front", (-0.22, -0.31, 0.47), (1.18, 0.09, 0.10), steel)
    box(c, "lathe_rail_rear", (-0.22, 0.18, 0.47), (1.18, 0.09, 0.10), steel)
    box(c, "lathe_headstock", (-0.72, -0.06, 0.68), (0.37, 0.44, 0.42), dark, 0.032)
    g.cylinder("lathe_chuck", c, (-0.48, -0.06, 0.69), 0.16, 0.12, copper,
               vertices=16, rotation=(0, math.pi / 2, 0))
    g.cylinder("lathe_workpiece", c, (-0.15, -0.06, 0.69), 0.065, 0.52, steel,
               vertices=12, rotation=(0, math.pi / 2, 0))
    box(c, "tailstock", (0.28, -0.05, 0.60), (0.18, 0.34, 0.29), steel)
    box(c, "tool_carriage", (0.04, -0.24, 0.64), (0.28, 0.18, 0.18), copper)
    if level >= 4:
        box(c, "feed_drive_base", (0.43, -0.02, 0.28), (0.32, 0.41, 0.23), dark)
        g.cylinder("feed_drive_pulley", c, (0.43, -0.29, 0.48), 0.19, 0.08, copper,
                   vertices=16, rotation=(math.pi / 2, 0, 0))
    if level >= 6:
        box(c, "lathe_guard", (-0.24, 0.27, 0.66), (0.82, 0.06, 0.29), mat(m, "roof_teal"))
    if level >= 9:
        box(c, "precision_tool_head", (0.10, -0.20, 0.92), (0.24, 0.19, 0.13), mat(m, "armor"))


def detail(c, m, level, state):
    wood, copper, steel = mat(m, "wood_pale"), mat(m, "copper"), mat(m, "steel_light")
    box(c, "vise_bench_top", (0.76, 0.42, 0.60), (0.84, 0.49, 0.10), wood)
    for x in (0.46, 1.05):
        box(c, f"vise_bench_leg_{x}", (x, 0.42, 0.36), (0.10, 0.36, 0.42), mat(m, "wood_beam"))
    if state == "construction":
        for i in range(3):
            box(c, f"stored_copper_pipe_{i}", (0.46, -0.94 + i * 0.13, 0.17),
                (0.80, 0.07, 0.07), copper)
        return
    if state == "damaged":
        box(c, "vise_broken_jaw", (0.82, 0.40, 0.68), (0.19, 0.15, 0.12), steel)
        for i in range(4):
            box(c, f"scattered_part_{i}", (-0.89 + i * 0.23, -0.97, 0.18),
                (0.13, 0.10, 0.07), copper if i % 2 else steel, 0.009)
        return
    box(c, "vise_fixed_jaw", (0.65, 0.42, 0.70), (0.12, 0.28, 0.14), steel)
    box(c, "vise_moveable_jaw", (0.88, 0.42, 0.70), (0.12, 0.28, 0.14), steel)
    box(c, "vise_screw", (1.04, 0.42, 0.67), (0.24, 0.055, 0.055), copper)
    for i in range(2 + level // 3):
        box(c, f"copper_blank_{i}", (0.62 + (i % 3) * 0.17,
            0.47 + (i // 3) * 0.11, 0.71), (0.10, 0.08, 0.11), copper, 0.008)
    gear(c, m, "wall_flywheel", -0.83, 1.00, 1.02, 0.22 if level == 1 else 0.33)
    if level >= 2:
        gear(c, m, "secondary_handwheel", -0.18, 1.00, 0.89, 0.14, 8)
    if level >= 4:
        gear(c, m, "small_drive_gear", -0.18, 1.00, 0.97, 0.19, 8)
    if level >= 5:
        box(c, "steam_gauge_face", (0.55, 0.966, 1.48), (0.19, 0.03, 0.19), mat(m, "whitewash"))
        box(c, "steam_gauge_needle", (0.56, 0.944, 1.48), (0.10, 0.017, 0.018), mat(m, "dark_metal"))
    if level >= 6:
        box(c, "sorted_parts_shelf", (-1.03, 0.52, 0.54), (0.45, 0.27, 0.09), wood)
        for i in range(3):
            box(c, f"parts_bin_{i}", (-1.18 + i * 0.15, 0.53, 0.65),
                (0.12, 0.20, 0.12), steel, 0.012)
    if level >= 8:
        box(c, "precision_console", (-0.98, 0.48, 0.94), (0.38, 0.25, 0.15), mat(m, "armor"))
        for i in range(3):
            box(c, f"console_readout_{i}", (-1.08 + i * 0.10, 0.32, 0.96),
                (0.06, 0.03, 0.07), mat(m, "glass_cyan"), 0.005)
    if level >= 9:
        box(c, "super_mechanism_cradle", (0.94, -0.83, 0.28), (0.44, 0.32, 0.20), steel)
        gear(c, m, "precision_product", 0.94, -0.99, 0.51, 0.16, 8)
    if level >= 10:
        box(c, "finished_parts_crate", (0.96, -0.76, 0.29), (0.41, 0.33, 0.22), mat(m, "armor"))


def add_mechanical_workshop(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    floor(collection, mats)
    shell(collection, mats, level, state)
    lathe(collection, mats, level, state)
    detail(collection, mats, level, state)
