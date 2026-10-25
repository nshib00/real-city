"""Reed paper workshop: vat, screw press, drying frames and upgrade machinery."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def _reed_bundle(c, m, stem, x, y, state):
    wood = mat(m, "wood_pale")
    green = mat(m, "roof_leaf")
    rope = mat(m, "rope")
    for i in range(5):
        dx = (i - 2) * 0.055
        h = 0.47 + (i % 3) * 0.06
        if state == "damaged":
            box(c, f"{stem}_fallen_reed_{i}", (x + dx, y, 0.13),
                (0.045, h, 0.045), green, 0.008, (0, 0, 0.20))
        else:
            g.beam(f"{stem}_reed_{i}", c, (x + dx, y, 0.10),
                   (x + dx + 0.035, y + 0.025, 0.10 + h), 0.035, green)
    if state != "damaged":
        box(c, f"{stem}_tie", (x, y, 0.29), (0.34, 0.11, 0.038), rope, 0.006)
    box(c, f"{stem}_pallet", (x, y, 0.09), (0.40, 0.32, 0.08), wood)


def _vat(c, m, level, state):
    rim = mat(m, "steel_light" if level >= 5 else "wood_beam")
    wood = mat(m, "wood_pale")
    liquid = mat(m, "glass_cyan")
    # Open vat with a visible pale pulp surface and slotted strainer.
    x, y = -0.58, 0.10
    w = 0.72 + min(level, 7) * 0.025
    d = 0.65 + min(level, 7) * 0.025
    box(c, "vat_foot", (x, y, 0.16), (w + 0.10, d + 0.10, 0.18),
        mat(m, "stone_block" if level >= 3 else "wood_beam"), 0.025)
    if state == "construction":
        box(c, "vat_unmounted_wall", (x - w * 0.35, y, 0.28), (0.09, d, 0.18), rim)
        box(c, "vat_unmounted_rail", (x + 0.28, -0.84, 0.13), (0.10, 0.54, 0.08), rim)
        return
    box(c, "pulp_surface", (x, y, 0.40), (w - 0.08, d - 0.08, 0.055),
        mat(m, "whitewash") if state == "active" else liquid, 0.018)
    for side in (-1, 1):
        if state == "damaged" and side > 0:
            box(c, "fallen_vat_side", (x + 0.34, y - 0.43, 0.12),
                (0.09, 0.58, 0.09), rim, rotation=(0, 0, -0.22))
        else:
            box(c, f"vat_side_{side}", (x + side * w / 2, y, 0.36),
                (0.095, d, 0.31), rim)
        box(c, f"vat_end_{side}", (x, y + side * d / 2, 0.36),
            (w, 0.095, 0.31), rim)
    if state == "active":
        for i in range(4):
            box(c, f"strainer_slatted_frame_{i}", (x - 0.25 + i * 0.16, y, 0.49),
                (0.035, d - 0.10, 0.035), wood, 0.006)


def _press(c, m, level, state):
    frame = mat(m, "wood_beam" if level < 5 else "steel_light")
    plate = mat(m, "wood_pale" if level < 5 else "metal_worn")
    dark = mat(m, "dark_metal")
    h = 1.10 + level * 0.060
    x, y = 0.30, 0.27
    box(c, "press_plinth", (x, y, 0.17), (0.85, 0.75, 0.17),
        mat(m, "stone_block" if level >= 3 else "wood_beam"), 0.035)
    box(c, "press_lower_platen", (x, y, 0.30), (0.68, 0.58, 0.10), plate)
    if state == "damaged":
        box(c, "broken_press_left_stanchion", (x - 0.34, y, 0.53),
            (0.09, 0.10, 0.54), frame)
        box(c, "fallen_upper_platen", (x + 0.50, -0.45, 0.12),
            (0.65, 0.48, 0.10), plate, rotation=(0, 0, -0.25))
        g.cylinder("broken_screw_on_ground", c, (x + 0.24, -0.79, 0.13),
                   0.06, 0.43, dark, vertices=16, rotation=(math.pi / 2, 0, 0.3))
        return
    for side in (-1, 1):
        box(c, f"press_upright_{side}", (x + side * 0.35, y, 0.34 + h / 2),
            (0.11, 0.12, h), frame, 0.018)
    if state == "construction":
        box(c, "upper_crossbar_waiting", (0.70, -0.79, 0.14),
            (0.81, 0.13, 0.12), frame)
        return
    box(c, "press_crossbar", (x, y, 0.37 + h), (0.84, 0.16, 0.14), frame, 0.026)
    box(c, "press_moving_platen", (x, y, 0.69), (0.69, 0.57, 0.10), plate, 0.020)
    g.cylinder("press_screw", c, (x, y, 0.95 + h * 0.26),
               0.072, 0.46 + h * 0.48, dark, vertices=20)
    g.beam("screw_cross_handle", c, (x - 0.27, y, 0.78 + h * 0.49),
           (x + 0.27, y, 0.78 + h * 0.49), 0.055, frame)
    if level >= 4:
        g.cylinder("drive_wheel", c, (0.78, y, 0.70), 0.24, 0.09,
                   mat(m, "copper"), vertices=20, rotation=(0, math.pi / 2, 0))
        for i in range(4):
            angle = i * math.pi / 2
            g.beam(f"drive_spoke_{i}", c, (0.84, y, 0.70),
                   (0.84, y + math.sin(angle) * 0.19, 0.70 + math.cos(angle) * 0.19),
                   0.025, dark)


def _drying(c, m, level, state):
    wood = mat(m, "wood_pale")
    beam = mat(m, "wood_beam")
    paper = mat(m, "whitewash")
    frame_count = 1 + (level >= 2) + (level >= 6) + (level >= 9)
    for i in range(frame_count):
        y = -0.86 + i * 0.32
        x = -0.70
        if state == "damaged" and i >= frame_count // 2:
            box(c, f"fallen_drying_frame_{i}", (x, y, 0.13),
                (0.69, 0.06, 0.08), beam, rotation=(0, 0, 0.19))
            box(c, f"wet_sheet_debris_{i}", (x, y - 0.08, 0.13),
                (0.43, 0.22, 0.015), paper, 0.003)
            continue
        for side in (-1, 1):
            box(c, f"drying_post_{i}_{side}", (x + side * 0.31, y, 0.48),
                (0.06, 0.06, 0.76), beam, 0.010)
        if state == "construction" and i > 0:
            continue
        box(c, f"drying_top_{i}", (x, y, 0.87), (0.70, 0.07, 0.07), beam)
        box(c, f"suspended_paper_sheet_{i}", (x, y, 0.64),
            (0.50, 0.02, 0.36), paper, 0.004)
        box(c, f"drying_sheet_lower_weight_{i}", (x, y, 0.45),
            (0.52, 0.04, 0.035), wood, 0.006)
    if state == "active" and level >= 2:
        # Rain canopy sits on four posts, leaving the press and paper sheets readable.
        for x in (-1.17, -0.19):
            for y in (-1.04, 0.54):
                box(c, f"canopy_post_{x}_{y}", (x, y, 0.69),
                    (0.07, 0.07, 1.18), beam)
        roof = mat(m, "roof_teal" if level >= 8 else "roof_wood_plank")
        box(c, "drying_canopy", (-0.68, -0.25, 1.34),
            (1.12, 1.72, 0.12), roof, 0.030)
        for x in (-1.10, -0.26):
            box(c, f"canopy_trim_{x}", (x, -0.25, 1.42),
                (0.055, 1.69, 0.055), beam, 0.008)


def _late(c, m, level, state):
    if level < 3:
        return
    wall = mat(m, "reinforced_concrete" if level >= 8 else "brick_warm" if level >= 5 else "stone_block")
    steel = mat(m, "steel_light")
    h = 0.48 + level * 0.045
    if state == "active":
        box(c, "rear_workshop_wall", (0.37, 0.91, 0.12 + h / 2),
            (1.40, 0.16, h), wall, 0.025)
        box(c, "side_workshop_wall", (1.04, 0.40, 0.12 + h / 2),
            (0.14, 1.12, h), wall, 0.023)
        box(c, "machine_roof", (0.44, 0.45, 0.19 + h),
            (1.44, 1.15, 0.11), mat(m, "roof_teal" if level >= 8 else "roof_wood_plank"), 0.025)
    elif state == "construction":
        box(c, "unfinished_rear_wall", (0.37, 0.91, 0.12 + h * 0.22),
            (1.40, 0.16, h * 0.44), wall, 0.022)
        box(c, "unmounted_roof_panel", (1.03, -0.80, 0.15),
            (0.43, 0.35, 0.10), steel, 0.022)
    else:
        box(c, "surviving_rear_wall", (-0.08, 0.91, 0.12 + h * 0.32),
            (0.52, 0.16, h * 0.64), wall, 0.022)
        box(c, "fallen_machine_roof", (0.75, -0.70, 0.14),
            (0.70, 0.44, 0.10), wall, 0.022, (0, 0, 0.18))
    if level >= 4:
        box(c, "pump_mount", (1.05, 0.10, 0.19), (0.43, 0.45, 0.19), wall)
        if state == "active":
            g.cylinder("water_pump", c, (1.05, 0.10, 0.47), 0.15, 0.40,
                       steel, vertices=20)
            g.beam("water_pipe", c, (1.05, 0.11, 0.63),
                   (0.70, 0.11, 0.63), 0.055, steel)
        elif state == "damaged":
            g.cylinder("fallen_pump", c, (1.19, -0.67, 0.16), 0.13, 0.32,
                       steel, vertices=16, rotation=(math.pi / 2, 0, 0))
    if level >= 5 and state == "active":
        box(c, "mechanism_guard", (0.84, 0.30, 0.60),
            (0.22, 0.42, 0.34), mat(m, "metal_worn"), 0.023)
        if level >= 7:
            g.cylinder("exhaust_pipe", c, (0.93, 0.73, 0.82 + h * 0.30),
                       0.10, 0.48, steel, vertices=16)
    if level >= 8 and state == "active":
        for x in (0.12, 0.56):
            box(c, f"glass_control_pane_{x}", (x, 0.82, 0.58),
                (0.30, 0.035, 0.27), mat(m, "glass_cyan"), 0.012)
        box(c, "protected_paper_store", (1.03, -0.85, 0.36),
            (0.57, 0.42, 0.49), wall, 0.028)
        box(c, "store_window", (1.03, -1.067, 0.45),
            (0.38, 0.025, 0.24), mat(m, "glass_cyan"), 0.009)
    if level >= 10 and state == "active":
        for x in (0.12, 0.72):
            box(c, f"roof_precision_rib_{x}", (x, 0.43, 0.29 + h),
                (0.075, 1.02, 0.12), steel, 0.012)
        box(c, "master_roof_crest", (0.43, 0.43, 0.39 + h),
            (0.73, 0.12, 0.12), mat(m, "copper"), 0.018)


def _output(c, m, level, state):
    if state == "construction":
        box(c, "unassembled_output_crate", (0.84, -0.86, 0.13),
            (0.50, 0.36, 0.09), mat(m, "wood_pale"))
        return
    count = 1 + level // 3
    for i in range(count):
        x = 0.48 + (i % 2) * 0.33
        y = -0.88 + (i // 2) * 0.25
        if state == "damaged" and i % 2:
            box(c, f"scattered_paper_{i}", (x, y, 0.11),
                (0.27, 0.23, 0.025), mat(m, "whitewash"), 0.004, (0, 0, 0.27))
        else:
            box(c, f"paper_stack_{i}", (x, y, 0.16),
                (0.26, 0.22, 0.13), mat(m, "whitewash"), 0.011)
            box(c, f"paper_press_board_{i}", (x, y, 0.24),
                (0.28, 0.24, 0.035), mat(m, "wood_pale"), 0.006)
    if level >= 6 and state == "active":
        box(c, "output_cart_bed", (1.16, -0.44, 0.31),
            (0.40, 0.55, 0.09), mat(m, "wood_beam"))
        for y in (-0.66, -0.23):
            g.cylinder(f"output_cart_wheel_{y}", c, (1.38, y, 0.20),
                       0.13, 0.07, mat(m, "dark_metal"), vertices=12,
                       rotation=(0, math.pi / 2, 0))


def add_paper_workshop(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    _reed_bundle(collection, mats, "reed_input", -1.25, 0.45, state)
    if level >= 2:
        _reed_bundle(collection, mats, "reed_reserve", -1.25, 0.86, state)
    _vat(collection, mats, level, state)
    _press(collection, mats, level, state)
    _drying(collection, mats, level, state)
    _late(collection, mats, level, state)
    _output(collection, mats, level, state)
