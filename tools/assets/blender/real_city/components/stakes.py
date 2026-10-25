"""Six compact stake-trap upgrades with distinct gameplay states."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _rail(c, name, a, b, width, material):
    g.beam(name, c, a, b, width, material)


def _stake(c, mats, name, x, y, *, level, height, state, index):
    wood = mat(mats, "wood_beam")
    cut = mat(mats, "wood_cut")
    metal = mat(mats, "metal_worn")
    if state == "ruined":
        _rail(c, name + "_fallen", (x - 0.15, y, 0.105), (x + 0.13, y + 0.12, 0.15), 0.10, wood)
        g.cone(name + "_fallen_point", c, (x + 0.19, y + 0.14, 0.15), 0.065, 0.004, 0.16, cut, vertices=8, rotation=(0, math.pi / 2, 0))
        if level >= 4:
            g.box(name + "_fallen_iron", c, (x - 0.11, y - 0.06, 0.13), (0.12, 0.045, 0.035), metal, bevel=0.009)
        return
    if state == "construction" and index % 3 == 2:
        _rail(c, name + "_loose", (x - 0.16, y, 0.11), (x + 0.16, y + 0.08, 0.13), 0.10, wood)
        return
    if state == "damaged" and index % 3 == 1:
        height *= 0.43
    if state == "empty":
        height *= 0.60
    tilt = 0.11 if state == "armed" else 0.25 if state == "triggered" else 0.03
    if state == "damaged":
        tilt = 0.28 if index % 2 else -0.15
    sx = x + (tilt if index % 2 else -tilt) * height
    tip_z = 0.105 + height
    shoulder_z = tip_z - 0.13
    _rail(c, name + "_shaft", (x, y, 0.105), (sx * 0.70 + x * 0.30, y, shoulder_z + 0.025), 0.105, wood)
    g.cone(name + "_flared_base", c, (x, y, 0.145), 0.13, 0.075, 0.105, wood, vertices=10)
    _rail(c, name + "_grain", (x - 0.025, y - 0.053, 0.18), (sx - 0.025, y - 0.053, shoulder_z - 0.01),
          0.014, cut)
    g.cone(name + "_point", c, (sx, y, shoulder_z + 0.07), 0.075, 0.002, 0.16,
           metal if level >= 4 else cut, vertices=8, rotation=(0, tilt if index % 2 else -tilt, 0))
    if level >= 4:
        g.cylinder(name + "_collar", c, (sx * 0.65 + x * 0.35, y, shoulder_z - 0.035),
                   0.081, 0.045, metal, vertices=10)
    if level >= 2 and state not in {"empty", "ruined"}:
        g.cylinder(name + "_binding", c, (x, y, 0.16), 0.069, 0.055, mat(mats, "rope"), vertices=10)


def add_stakes(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 7):
        raise ValueError(f"Unsupported stakes level: {level}")
    if state not in {"construction", "armed", "triggered", "empty", "damaged", "ruined"}:
        raise ValueError(f"Unsupported stakes state: {state}")
    wood = mat(mats, "wood_beam")
    pale = mat(mats, "wood_pale")
    rope = mat(mats, "rope")
    metal = mat(mats, "metal_worn")
    stone = mat(mats, "stone_block")
    # Functional parts stay low and concentrated at the centre of a 3.6-unit tile.
    count = 3 if level < 5 else 6
    positions = [(-0.42, -0.24), (0.0, -0.35), (0.43, -0.19)]
    if count == 6:
        positions += [(-0.48, 0.30), (0.02, 0.24), (0.50, 0.34)]
    if level >= 6:
        positions = [(x + (0.12 if i % 2 else -0.10), y) for i, (x, y) in enumerate(positions)]
    if level >= 3 and state != "ruined":
        for y in (-0.43, 0.40):
            if state == "construction" and y > 0:
                continue
            if state == "damaged" and y > 0:
                _rail(c, "broken_frame_cross", (-0.74, y, 0.105), (-0.11, y + 0.11, 0.105), 0.12, pale)
                continue
            _rail(c, f"frame_cross_{y}", (-0.74, y, 0.105), (0.74, y, 0.105), 0.12, pale)
        for x in (-0.67, 0.67):
            if state == "construction" and x > 0:
                continue
            if state == "damaged" and x < 0:
                _rail(c, "broken_frame_side", (x, -0.43, 0.105), (x - 0.09, 0.04, 0.105), 0.115, pale)
                continue
            _rail(c, f"frame_side_{x}", (x, -0.43, 0.105), (x, 0.40, 0.105), 0.115, pale)
    elif level >= 2 and state != "ruined":
        _rail(c, "cross_tie", (-0.62, -0.10, 0.14), (0.62, -0.10, 0.14), 0.085, pale)
        for x in (-0.52, 0.52):
            g.cylinder(f"rope_knot_{x}", c, (x, -0.10, 0.18), 0.075, 0.048, rope, vertices=10)
    if level >= 6:
        for x in (-0.65, 0.65):
            if state == "ruined" or state == "damaged" and x < 0:
                g.box(f"broken_stone_foot_{x}", c, (x, 0.04, 0.12), (0.25, 0.20, 0.12), stone, bevel=0.025, rotation=(0, 0, 0.30))
            else:
                g.box(f"stone_foot_{x}", c, (x, 0.0, 0.11), (0.25, 0.42, 0.12), stone, bevel=0.025)
    for i, (x, y) in enumerate(positions):
        _stake(c, mats, f"stake_{i:02d}", x, y, level=level,
               height=0.37 + level * 0.019, state=state, index=i)
    if level >= 5 and state not in {"ruined", "construction"}:
        for y in (-0.26, 0.28):
            _rail(c, f"double_row_brace_{y}", (-0.60, y, 0.19), (0.60, y, 0.19), 0.07,
                  metal if level >= 6 else pale)
    if state == "construction":
        g.box("spare_wood_bundle", c, (0.84, 0.64, 0.14), (0.43, 0.29, 0.14), pale, bevel=0.025)
        g.cylinder("rope_coil", c, (0.91, 0.64, 0.25), 0.10, 0.045, rope, vertices=12)
        if level >= 3:
            _rail(c, "unmounted_frame_piece", (0.58, 0.61, 0.105), (1.06, 0.61, 0.105), 0.10, pale)
    elif state == "triggered":
        for i in range(2):
            g.box(f"triggered_footprint_{i}", c, (-0.27 + i * 0.53, 0.56, 0.105),
                  (0.18, 0.28, 0.045), mat(mats, "soil"), bevel=0.02)
    elif state in {"damaged", "ruined"}:
        for i in range(3 if state == "ruined" else 2):
            x = -0.51 + i * 0.49
            g.box(f"splinter_{i}", c, (x, 0.61, 0.12), (0.28, 0.075, 0.055),
                  wood, bevel=0.012, rotation=(0, 0, 0.18 * i))
