"""Aeolian electronics workshop: open assembly benches in a protected lab shell."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def cabinet(c, m, x, y, level, state):
    steel = mat(m, "steel_light")
    armor = mat(m, "armor" if level >= 8 else "roof_teal")
    box(c, "finished_goods_base", (x, y, 0.19), (0.57, 0.54, 0.20), steel)
    if state == "construction":
        box(c, "unmounted_cabinet_door", (x + 0.45, y - 0.26, 0.13), (0.34, 0.12, 0.08), armor)
        return
    if state == "damaged":
        box(c, "cabinet_broken_side", (x - 0.21, y, 0.40), (0.10, 0.54, 0.50), steel)
        box(c, "cabinet_fallen_door", (x + 0.26, y - 0.25, 0.13), (0.42, 0.44, 0.08), armor, rotation=(0, 0, -0.25))
        return
    box(c, "finished_goods_cabinet", (x, y, 0.63), (0.57, 0.54, 0.86), steel, 0.035)
    box(c, "cabinet_door", (x, y - 0.283, 0.62), (0.46, 0.027, 0.72), armor, 0.012)
    box(c, "cabinet_latch", (x + 0.16, y - 0.312, 0.62), (0.055, 0.03, 0.12), mat(m, "copper"), 0.008)
    if level >= 6:
        box(c, "cabinet_status", (x - 0.14, y - 0.307, 0.90), (0.10, 0.025, 0.07), mat(m, "glass_cyan"), 0.006)
    if level >= 9:
        box(c, "cabinet_armor", (x, y + 0.285, 0.63), (0.56, 0.035, 0.73), armor, 0.012)


def assembly_bench(c, m, x, y, index, level, state):
    steel = mat(m, "steel_light")
    dark = mat(m, "dark_metal")
    copper = mat(m, "copper")
    width = 1.18 if index == 0 else 0.92
    box(c, f"bench_{index}_top", (x, y, 0.55), (width, 0.64, 0.11), dark, 0.025)
    for side in (-1, 1):
        box(c, f"bench_{index}_leg_{side}", (x + side * (width / 2 - 0.10), y, 0.32),
            (0.10, 0.47, 0.39), steel, 0.01)
    if state == "construction":
        box(c, f"bench_{index}_unmounted_board", (x, y - 0.52, 0.13),
            (0.45, 0.29, 0.045), mat(m, "roof_teal"), 0.008)
        return
    if state == "damaged" and index == 1:
        box(c, "broken_bench_frame", (x + 0.22, y - 0.35, 0.15),
            (0.53, 0.12, 0.09), steel, rotation=(0, 0, -0.23))
        return
    # A broad board with copper traces and several oversized components reads in iso.
    box(c, f"pcb_{index}", (x, y, 0.645), (width * 0.62, 0.39, 0.055),
        mat(m, "roof_teal"), 0.009)
    for line in range(3):
        box(c, f"pcb_{index}_trace_{line}",
            (x - width * 0.22, y - 0.12 + line * 0.12, 0.680),
            (width * 0.36, 0.021, 0.012), copper, 0.002)
    for part in range(2 + min(level // 3, 2)):
        px = x + 0.06 + (part % 2) * 0.14
        py = y - 0.11 + (part // 2) * 0.16
        box(c, f"pcb_{index}_chip_{part}", (px, py, 0.706),
            (0.10, 0.08, 0.05), dark, 0.006)
    if level >= 3:
        box(c, f"bench_{index}_scope_post", (x - width * 0.41, y + 0.15, 0.88),
            (0.075, 0.08, 0.57), steel)
        box(c, f"bench_{index}_scope_head", (x - width * 0.33, y + 0.15, 1.14),
            (0.29, 0.24, 0.20), steel, 0.025)
        box(c, f"bench_{index}_scope_lens", (x - width * 0.33, y - 0.005, 1.14),
            (0.14, 0.04, 0.10), mat(m, "glass_cyan"), 0.01)
    if level >= 5:
        box(c, f"bench_{index}_robot_pillar", (x + width * 0.39, y + 0.19, 0.89),
            (0.10, 0.10, 0.56), steel)
        box(c, f"bench_{index}_robot_arm", (x + width * 0.25, y + 0.15, 1.13),
            (0.42, 0.09, 0.09), copper, 0.017)
        g.cylinder(f"bench_{index}_robot_tool", c,
                   (x + width * 0.09, y + 0.15, 0.92), 0.035, 0.34, dark, vertices=12)


def shell(c, m, level, state):
    steel = mat(m, "steel_light")
    wall = mat(m, "reinforced_concrete")
    armor = mat(m, "armor")
    # All three states share the exact same floor and front access strip.
    box(c, "clean_floor", (0, 0.12, 0.105), (2.75, 2.48, 0.07), wall, 0.02)
    for i in range(4):
        box(c, f"floor_seam_{i}", (-1.03 + i * 0.68, -0.42, 0.146),
            (0.026, 1.53, 0.010), steel, 0.003)
    box(c, "entry_strip", (0, -1.13, 0.15), (1.10, 0.12, 0.028),
        mat(m, "roof_teal"), 0.005)
    if state == "construction":
        for x in (-1.28, 1.28):
            box(c, f"unfinished_frame_{x}", (x, 1.04, 0.48),
                (0.12, 0.12, 0.74), steel)
        if level >= 3:
            box(c, "partial_service_wall", (-0.56, 1.22, 0.44),
                (1.14, 0.15, 0.63), wall, 0.022)
        if level >= 5:
            box(c, "vent_frame_waiting", (0.64, 1.12, 0.80),
                (0.12, 0.15, 1.39), steel)
        if level >= 7:
            box(c, "roof_spine_waiting", (-0.58, 0.84, 0.18),
                (0.83, 0.16, 0.10), armor)
        if level >= 9:
            box(c, "armored_cabinet_panel_waiting", (0.96, -0.52, 0.16),
                (0.53, 0.29, 0.08), armor)
        box(c, "stored_roof_panels", (0.91, -0.94, 0.17),
            (0.58, 0.31, 0.08), armor)
        return
    if state == "damaged":
        box(c, "surviving_rear_wall", (-0.88, 1.23, 0.60),
            (0.81, 0.16, 0.94), wall, 0.024)
        box(c, "broken_wall_slab", (0.64, 0.59, 0.16),
            (0.80, 0.30, 0.10), wall, rotation=(0, 0, -0.31))
        box(c, "fallen_roof_panel", (-0.42, -0.85, 0.19),
            (0.74, 0.45, 0.09), armor, rotation=(0, 0, 0.29))
        if level >= 4:
            box(c, "shattered_partition_frame", (-0.97, -0.21, 0.17),
                (0.67, 0.12, 0.09), steel, rotation=(0, 0, 0.27))
            box(c, "shattered_partition_glass", (-0.97, -0.41, 0.15),
                (0.38, 0.31, 0.035), mat(m, "glass_cyan"), 0.007)
        if level >= 6:
            box(c, "fallen_vent_hood", (0.79, 0.83, 0.20),
                (0.56, 0.39, 0.10), armor, rotation=(0, 0, -0.26))
        if level >= 8:
            box(c, "broken_reinforcement_stump", (1.16, 1.11, 0.45),
                (0.16, 0.19, 0.64), armor, 0.018)
        return
    # Rear silhouette stays behind the benches and leaves their boards visible.
    box(c, "rear_wall", (0, 1.23, 0.64), (2.62, 0.16, 1.03), wall, 0.027)
    for x in (-1.24, 1.24):
        box(c, f"structural_post_{x}", (x, 1.17, 0.91),
            (0.15, 0.17, 1.66), steel, 0.02)
    if level >= 2:
        box(c, "upper_service_beam", (0, 1.18, 1.75),
            (2.67, 0.21, 0.14), steel, 0.025)
        for x in (-0.77, 0.77):
            box(c, f"service_lamp_{x}", (x, 1.03, 1.57),
                (0.38, 0.09, 0.09), mat(m, "glass_cyan"), 0.01)
    if level >= 4:
        box(c, "left_glass_partition", (-1.27, 0.18, 0.89),
            (0.08, 1.71, 1.18), mat(m, "glass_cyan"), 0.015)
        for y in (-0.58, 0.38):
            box(c, f"partition_mullion_{y}", (-1.27, y, 0.89),
                (0.12, 0.06, 1.22), steel)
    if level >= 5:
        box(c, "rear_vent_hood", (0.33, 0.98, 1.63),
            (1.27, 0.39, 0.15), armor, 0.026)
        g.cylinder("vent_stack", c, (0.85, 1.13, 1.82), 0.12, 0.31,
                   steel, vertices=16)
    if level >= 7:
        box(c, "roof_spine", (0.0, 0.92, 1.95),
            (2.60, 0.38, 0.14), armor, 0.029)
        box(c, "roof_light_strip", (0, 0.69, 1.92),
            (1.60, 0.055, 0.055), mat(m, "glass_cyan"), 0.006)
    if level >= 8:
        for x in (-0.90, 0.90):
            box(c, f"reinforced_beam_{x}", (x, 1.06, 1.07),
                (0.12, 0.20, 1.35), armor)
        box(c, "precision_drive_housing", (0.56, 1.00, 1.09),
            (0.48, 0.26, 0.33), steel, 0.025)
        g.cylinder("precision_drive_core", c, (0.56, 0.84, 1.09),
                   0.12, 0.09, mat(m, "copper"), vertices=20,
                   rotation=(math.pi / 2, 0, 0))
    if level >= 10:
        box(c, "final_armor_crown", (0, 1.16, 2.06),
            (2.76, 0.28, 0.13), armor, 0.025)


def instrumentation(c, m, level, state):
    if state != "active":
        if state == "damaged":
            for i in range(4):
                box(c, f"fallen_circuit_{i}", (-0.95 + i * 0.22, -0.98, 0.17),
                    (0.18, 0.12, 0.035), mat(m, "roof_teal"), 0.004,
                    rotation=(0, 0, i * 0.14))
        return
    # Oversized circuit diagram on the rear wall gives the building its identity.
    box(c, "diagnostic_screen_frame", (-0.30, 1.106, 0.92),
        (1.12, 0.075, 0.64), mat(m, "dark_metal"), 0.022)
    box(c, "diagnostic_screen", (-0.30, 1.052, 0.92),
        (0.94, 0.023, 0.49), mat(m, "roof_teal"), 0.009)
    for j in range(3):
        box(c, f"screen_trace_{j}", (-0.62 + j * 0.25, 1.027, 0.90),
            (0.045, 0.010, 0.25 + j * 0.05), mat(m, "copper"), 0.003)
    for j in range(2):
        box(c, f"screen_readout_{j}", (0.02 + j * 0.17, 1.023, 1.06),
            (0.10, 0.009, 0.065), mat(m, "glass_cyan"), 0.005)
    box(c, "copper_bus_rail", (0.74, 1.07, 0.82),
        (0.10, 0.04, 0.66), mat(m, "copper"), 0.009)
    for j in range(3):
        box(c, f"bus_node_{j}", (0.74, 1.036, 0.59 + j * 0.22),
            (0.15, 0.025, 0.08), mat(m, "glass_cyan"), 0.006)
    if level >= 6:
        for i in range(2):
            box(c, f"secondary_indicator_{i}", (0.14 + i * 0.14, 1.06, 1.16),
                (0.08, 0.03, 0.08), mat(m, "roof_gold"), 0.005)
    if level >= 9:
        g.cylinder("light_crystal_socket", c, (-0.89, 1.08, 1.85),
                   0.10, 0.09, mat(m, "steel_light"), vertices=12)
        g.cone("light_crystal", c, (-0.89, 1.08, 2.03),
               0.065, 0.027, 0.32, mat(m, "amethyst"), vertices=6)


def add_electronics_workshop(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    shell(collection, mats, level, state)
    assembly_bench(collection, mats, -0.29, -0.20, 0, level, state)
    if level >= 2:
        assembly_bench(collection, mats, 0.80, 0.39, 1, level, state)
    cabinet(collection, mats, -0.94, 0.68, level, state)
    instrumentation(collection, mats, level, state)
    if state == "active":
        # Clear input/output flow: copper and glass crates at the left front,
        # sealed product trays at the right front.
        for i in range(2 + level // 3):
            x = -1.04 + (i % 2) * 0.24
            y = -0.80 - (i // 2) * 0.24
            box(collection, f"input_crate_{i}", (x, y, 0.23),
                (0.22, 0.21, 0.20), mat(mats, "copper" if i % 2 else "glass_cyan"), 0.016)
        for i in range(1 + level // 4):
            box(collection, f"output_tray_{i}", (0.76 + i * 0.19, -0.88, 0.19),
                (0.16, 0.33, 0.07), mat(mats, "steel_light"), 0.01)
    elif state == "construction":
        for i in range(3):
            box(collection, f"stored_beam_{i}", (0.63, -0.98 + i * 0.11, 0.16 + i * 0.05),
                (0.64, 0.09, 0.07), mat(mats, "steel_light"))
    else:
        for i in range(5):
            box(collection, f"lab_debris_{i}", (0.29 + (i % 3) * 0.21,
                -0.77 - (i // 3) * 0.19, 0.14), (0.17, 0.12, 0.07),
                mat(mats, "steel_light" if i % 2 else "reinforced_concrete"),
                rotation=(0, 0, i * 0.17))
