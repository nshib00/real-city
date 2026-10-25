"""Eight Aeolian bolt throwers with five physical service states."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _beam(c, name, a, b, width, material):
    return g.beam(name, c, a, b, width, material)


def _bolt(c, mats, *, y, z, prefix):
    shaft = mat(mats, "wood_cut")
    iron = mat(mats, "metal_worn")
    _beam(c, prefix + "_shaft", (0, y - 0.45, z), (0, y + 0.24, z), 0.055, shaft)
    g.cone(prefix + "_head", c, (0, y - 0.50, z), 0.075, 0.004, 0.19, iron,
           vertices=8, rotation=(math.pi / 2, 0, 0))
    for x in (-0.09, 0.09):
        g.box(prefix + f"_fletch_{x}", c, (x, y + 0.20, z), (0.18, 0.14, 0.035),
              mat(mats, "roof_teal"), bevel=0.01, rotation=(0, 0, -0.32 if x < 0 else 0.32))


def _debris(c, mats, level, *, ruined):
    wood = mat(mats, "wood_beam")
    iron = mat(mats, "metal_worn")
    count = 5 if ruined else 3
    for i in range(count):
        x = -0.92 + i * 0.38
        g.box(f"fallen_splinter_{i}", c, (x, 0.88 - i * 0.10, 0.14),
              (0.31, 0.075, 0.07), wood, bevel=0.012, rotation=(0, 0, 0.2 * (i - 2)))
        if level >= 5 and i < 2:
            g.box(f"fallen_plate_{i}", c, (x, 0.55, 0.14), (0.25, 0.18, 0.05),
                  iron, bevel=0.012, rotation=(0, 0, i * 0.24))


def add_bolt_thrower(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 9):
        raise ValueError(f"Unsupported bolt thrower level: {level}")
    if state not in {"construction", "active", "no_crew", "damaged", "ruined"}:
        raise ValueError(f"Unsupported bolt thrower state: {state}")
    wood = mat(mats, "wood_beam")
    deck = mat(mats, "wood_pale")
    rope = mat(mats, "rope")
    iron = mat(mats, "metal_worn")
    steel = mat(mats, "dark_metal")
    stone = mat(mats, "stone_block")
    brass = mat(mats, "copper")
    armor = mat(mats, "armor")
    roof = mat(mats, "roof_teal")
    build, damaged, ruined = state == "construction", state == "damaged", state == "ruined"
    working = not (build or damaged or ruined)

    # Foundation pieces touch the common terrain, whose height is about 0.1.
    if level >= 5:
        for x in (-0.64, 0.64):
            for y in (-0.68, 0.64):
                g.box(f"stone_pier_{x}_{y}", c, (x, y, 0.20), (0.43, 0.45, 0.22), stone, bevel=0.035)
        for y in (-0.68, 0.64):
            g.box(f"stone_sill_{y}", c, (0, y, 0.28), (1.32, 0.24, 0.18), stone, bevel=0.025)
    else:
        for x in (-0.58, 0.58):
            g.box(f"timber_sleeper_{x}", c, (x, 0, 0.18), (0.19, 1.62, 0.18), wood, bevel=0.025)
    if ruined:
        for i, x in enumerate((-0.40, 0.29)):
            g.box(f"collapsed_rail_{i}", c, (x, -0.04 + i * 0.15, 0.19),
                  (0.18, 1.0, 0.18), wood, bevel=0.025, rotation=(0, 0, -0.19 + i * 0.40))
        _beam(c, "fallen_bow", (-0.66, 0.30, 0.18), (0.53, 0.49, 0.19), 0.12, wood)
        g.cylinder("fallen_winch", c, (0.72, 0.88, 0.20), 0.19, 0.16, iron, vertices=16)
        if level >= 3:
            g.box("fallen_pivot_stone", c, (-0.54, -0.55, 0.17), (0.35, 0.28, 0.15),
                  stone, bevel=0.025, rotation=(0, 0, 0.19))
        _debris(c, mats, level, ruined=True)
        return

    # Open construction and damaged versions remove much of the upper assembly.
    for i, x in enumerate((-0.42, 0.42)):
        if build and i == 1:
            continue
        if damaged and i == 0:
            g.box("snapped_left_rail", c, (-0.50, 0.48, 0.28), (0.20, 0.49, 0.18), wood,
                  bevel=0.025, rotation=(0, 0, -0.22))
            continue
        g.box(f"carriage_rail_{i}", c, (x, -0.06, 0.42), (0.19, 1.44, 0.30),
              steel if level >= 7 else wood, bevel=0.035)
        for y in (-0.54, 0.38):
            g.box(f"rail_shoe_{i}_{y}", c, (x, y, 0.28), (0.26, 0.22, 0.10), iron, bevel=0.012)
        if level >= 2:
            for y in (-0.30, 0.34):
                g.box(f"cord_wrap_{i}_{y}", c, (x, y, 0.59), (0.24, 0.07, 0.038), rope, bevel=0.008)
    g.box("rear_crossbar", c, (0, 0.45, 0.46), (1.03, 0.18, 0.21), wood, bevel=0.026)

    if build:
        g.box("loose_front_rail", c, (0.86, 0.32, 0.16), (0.17, 0.81, 0.11), deck,
              bevel=0.02, rotation=(0, 0, 0.22))
        _beam(c, "loose_bow", (-0.38, -0.87, 0.13), (0.44, -0.75, 0.13), 0.13, wood)
        g.cylinder("unmounted_winch", c, (-0.89, 0.73, 0.17), 0.17, 0.12, iron, vertices=16)
        if level >= 4:
            for x in (-0.65, 0.65):
                _beam(c, f"unfinished_canopy_post_{x}", (x, 0.56, 0.35), (x, 0.56, 0.86), 0.10, wood)
        return

    # Beam-bed and pivot are carried by the lower rails.
    g.box("bolt_channel", c, (0, -0.10, 0.69), (0.30, 1.34, 0.13),
          steel if level >= 7 else deck, bevel=0.025)
    for x in (-0.11, 0.11):
        g.box(f"channel_edge_{x}", c, (x, -0.10, 0.78), (0.045, 1.24, 0.09),
              iron if level >= 5 else wood, bevel=0.01)
    if level >= 3:
        g.cylinder("pivot_stone_bearing", c, (0, 0.07, 0.58), 0.28, 0.16,
                   stone, vertices=16)
    g.cylinder("turntable_pin", c, (0, 0.07, 0.64 if level >= 3 else 0.58), 0.24 if level >= 3 else 0.15,
               0.16, brass if level >= 3 else iron, vertices=16)
    if level >= 3:
        g.cylinder("pivot_collar", c, (0, 0.07, 0.73), 0.30, 0.065, iron, vertices=20)
        for i in range(8):
            a = i * math.tau / 8
            g.cylinder(f"pivot_rivet_{i}", c, (0.25 * math.cos(a), 0.07 + 0.25 * math.sin(a), 0.77),
                       0.027, 0.026, brass, vertices=8)

    span = 0.78 + (0.25 if level >= 6 else 0)
    if damaged:
        _beam(c, "surviving_bow_arm", (0, -0.65, 0.75), (span, -0.96, 0.81), 0.16, wood)
        _beam(c, "broken_arm_piece", (-0.87, -0.59, 0.15), (-0.35, -0.48, 0.18), 0.14, wood)
    else:
        for sign, side in ((-1, "left"), (1, "right")):
            _beam(c, f"bow_arm_{side}", (0, -0.65, 0.75), (sign * span, -0.96, 0.83),
                  0.16, steel if level >= 7 else wood)
            g.box(f"bow_cap_{side}", c, (sign * span, -0.96, 0.83), (0.18, 0.15, 0.16),
                  iron, bevel=0.025)
            if level >= 2:
                g.cylinder(f"bow_cord_collar_{side}", c, (sign * span * 0.76, -0.87, 0.82),
                           0.105, 0.065, rope, vertices=12, rotation=(0, math.pi / 2, 0))
        string_y = -0.42 if state == "active" else -0.86
        _beam(c, "bowstring_left", (-span, -0.96, 0.83), (0, string_y, 0.77),
              0.031 if level >= 2 else 0.022, rope)
        _beam(c, "bowstring_right", (span, -0.96, 0.83), (0, string_y, 0.77),
              0.031 if level >= 2 else 0.022, rope)
        if state == "active":
            _bolt(c, mats, y=-0.20, z=0.83, prefix="loaded_bolt")

    # Winch and mechanical ratchet are visible through the open rear.
    if not damaged:
        g.cylinder("tension_winch", c, (0, 0.54, 0.73), 0.18, 0.64, iron,
                   vertices=16, rotation=(0, math.pi / 2, 0))
        for x in (-0.34, 0.34):
            g.cylinder(f"winch_knob_{x}", c, (x, 0.54, 0.73), 0.07, 0.09, brass,
                       vertices=12, rotation=(0, math.pi / 2, 0))
        if level >= 3:
            for i in range(10):
                a = i * math.tau / 10
                g.box(f"ratchet_tooth_{i}", c,
                      (0.36, 0.54 + 0.20 * math.cos(a), 0.73 + 0.20 * math.sin(a)),
                      (0.06, 0.075, 0.065), brass, bevel=0.008, rotation=(a, 0, 0))
    if level >= 4 and not damaged:
        for x in (-0.56, 0.56):
            _beam(c, f"canopy_post_{x}", (x, 0.44, 0.33), (x, 0.44, 1.29), 0.095,
                  steel if level >= 7 else wood)
            _beam(c, f"canopy_frontbrace_{x}", (x, 0.44, 1.19), (x, -0.05, 1.30), 0.065, wood)
        for i in range(4):
            y = -0.14 + i * 0.22
            g.box(f"canopy_plank_{i}", c, (0, y, 1.34 + 0.035 * math.sin(i * 0.9)),
                  (1.32, 0.22, 0.08), roof if level >= 6 else deck, bevel=0.02)
    if level >= 5 and not damaged:
        for x in (-0.37, 0.37):
            g.box(f"steel_side_batten_{x}", c, (x, -0.18, 0.64), (0.065, 0.80, 0.15),
                  steel, bevel=0.014)
    if level >= 6 and not damaged:
        g.box("sight_stem", c, (0.27, -0.28, 0.89), (0.07, 0.25, 0.26), brass, bevel=0.014)
        g.cylinder("sight_ring", c, (0.27, -0.40, 1.03), 0.10, 0.045, brass,
                   vertices=16, rotation=(math.pi / 2, 0, 0))
    if level >= 7 and not damaged:
        g.cylinder("turning_drive", c, (0.68, 0.35, 0.54), 0.22, 0.11, brass,
                   vertices=16, rotation=(0, math.pi / 2, 0))
        _beam(c, "turning_handle", (0.75, 0.35, 0.54), (0.75, 0.67, 0.73), 0.052, steel)
        for x in (-0.62, 0.62):
            g.box(f"guard_plate_{x}", c, (x, 0.08, 0.60), (0.07, 0.72, 0.44),
                  armor, bevel=0.025)
    if level >= 8 and not damaged:
        g.box("covered_tension_drive", c, (0, 0.56, 0.87), (0.80, 0.49, 0.34),
              armor, bevel=0.055)
        for x in (-0.25, 0.25):
            g.box(f"drive_vent_{x}", c, (x, 0.34, 1.06), (0.10, 0.06, 0.05),
                  brass, bevel=0.009)
    if damaged:
        _debris(c, mats, level, ruined=False)
