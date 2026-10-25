"""Aeolian guardian enclosure: five levels, five visually distinct states."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


NESTS = ((-0.55, 0.68), (0.55, 0.68), (-0.55, 0.0),
         (0.55, 0.0), (-0.55, -0.66), (0.55, -0.66))


def _nest(c, stem, x, y, wood, straw, earth, gold, *, broken=False):
    g.cylinder(f"{stem}_stone_bed", c, (x, y, 0.19), 0.30, 0.12,
               earth, vertices=12)
    if broken:
        for i in range(5):
            angle = 0.30 + i * 0.95
            px, py = x + 0.24 * math.cos(angle), y + 0.24 * math.sin(angle)
            g.box(f"{stem}_broken_wattle_{i}", c, (px, py, 0.23),
                  (0.20, 0.045, 0.055), wood, bevel=0.009,
                  rotation=(0, 0, angle + 0.33))
        return
    g.cylinder(f"{stem}_straw_cushion", c, (x, y, 0.27), 0.24, 0.075,
               straw, vertices=14)
    g.cylinder(f"{stem}_inner_soil", c, (x, y, 0.32), 0.14, 0.025,
               earth, vertices=14)
    for i in range(10):
        angle = i * math.tau / 10
        px, py = x + 0.255 * math.cos(angle), y + 0.255 * math.sin(angle)
        g.box(f"{stem}_woven_rim_{i}", c, (px, py, 0.31),
              (0.19, 0.047, 0.055), wood, bevel=0.01,
              rotation=(0, 0, angle + math.pi / 2))
    g.cylinder(f"{stem}_core_medallion", c, (x, y, 0.347),
               0.052, 0.02, gold, vertices=10)


def _fence(c, level, state, wood, stone, beam):
    ruined = state == "ruined"
    damaged = state == "damaged"
    build = state == "construction"
    for side in (-1, 1):
        for y in (-1.06, -0.35, 0.36, 1.06):
            if ruined and y in (-0.35, 0.36):
                continue
            if damaged and side == 1 and y >= 0.36:
                continue
            if build and y == 0.36:
                continue
            height = 0.49 if ruined else (0.80 if level >= 3 else 0.68)
            g.box(f"fence_post_{side}_{y}", c,
                  (side * 1.14, y, 0.16 + height / 2),
                  (0.13, 0.13, height), stone if level >= 3 else wood,
                  bevel=0.025)
            g.box(f"post_cap_{side}_{y}", c,
                  (side * 1.14, y, 0.17 + height),
                  (0.19, 0.19, 0.07), beam if level >= 3 else wood,
                  bevel=0.018)
        for segment, y in enumerate((-0.70, 0.0, 0.71)):
            if ruined and segment != 0:
                continue
            if damaged and side == 1 and segment >= 1:
                continue
            if build and segment == 1:
                continue
            for z in (0.44, 0.67 if level >= 3 else 0.58):
                g.box(f"side_wattle_{side}_{segment}_{z}", c,
                      (side * 1.14, y, z), (0.07, 0.76, 0.065),
                      beam if level >= 3 and z > 0.5 else wood, bevel=0.012)
            for k in range(4):
                g.box(f"side_woven_stave_{side}_{segment}_{k}", c,
                      (side * 1.14, y - 0.27 + k * 0.18, 0.50),
                      (0.045, 0.045, 0.34), wood, bevel=0.007)
    for y in (-1.06, 1.06):
        for side in (-1, 1):
            if y < 0 and side == 1:  # readable entry gap
                continue
            if ruined and y > 0:
                continue
            if damaged and y > 0 and side > 0:
                continue
            if build and side > 0:
                continue
            g.box(f"end_sill_{y}_{side}", c,
                  (side * 0.58, y, 0.35), (1.14, 0.11, 0.16),
                  stone if level >= 3 else wood, bevel=0.025)
            if not ruined:
                g.box(f"end_rail_{y}_{side}", c,
                      (side * 0.58, y, 0.64), (1.14, 0.075, 0.075),
                      beam if level >= 3 else wood, bevel=0.014)
                for k in range(5):
                    g.box(f"end_stave_{y}_{side}_{k}", c,
                          (side * 0.58 - 0.40 + k * 0.20, y, 0.50),
                          (0.045, 0.045, 0.32), wood, bevel=0.009)
    if level >= 5 and not ruined:
        for y in (-0.34, 0.35):
            if damaged and y > 0:
                continue
            g.box(f"section_divider_{y}", c, (0, y, 0.33),
                  (1.05, 0.07, 0.30), beam, bevel=0.015)


def _canopy(c, stem, x, y, wood, beam, cloth, *, state, tall=False):
    if state == "ruined":
        g.box(f"{stem}_fallen_roof", c, (x, y, 0.19),
              (0.76, 0.56, 0.07), cloth, bevel=0.019,
              rotation=(0, 0, 0.17))
        return
    if state == "damaged":
        g.box(f"{stem}_broken_pole", c, (x - 0.28, y + 0.15, 0.27),
              (0.10, 0.53, 0.10), beam, bevel=0.017,
              rotation=(0, 0, 0.15))
        g.box(f"{stem}_fallen_cloth", c, (x + 0.11, y, 0.20),
              (0.58, 0.51, 0.06), cloth, bevel=0.012,
              rotation=(0, 0, -0.12))
        return
    top = 1.20 if tall else 1.06
    for side in (-1, 1):
        if state == "construction" and side > 0:
            continue
        px = x + side * 0.39
        g.box(f"{stem}_post_{side}", c, (px, y + 0.14, 0.16 + top / 2),
              (0.11, 0.11, top), wood, bevel=0.02)
        g.box(f"{stem}_stone_foot_{side}", c, (px, y + 0.14, 0.19),
              (0.19, 0.19, 0.12), beam, bevel=0.02)
    if state == "construction":
        g.box(f"{stem}_cloth_roll", c, (x + 0.1, y + 0.14, 0.22),
              (0.50, 0.18, 0.12), cloth, bevel=0.04)
        return
    g.box(f"{stem}_lintel", c, (x, y + 0.14, top + 0.15),
          (0.88, 0.10, 0.10), beam, bevel=0.018)
    g.box(f"{stem}_awning", c, (x, y + 0.06, top + 0.16),
          (0.94, 0.67, 0.07), cloth, bevel=0.027,
          rotation=(0.10, 0, 0))
    for side in (-1, 1):
        g.box(f"{stem}_cloth_trim_{side}", c,
              (x + side * 0.40, y - 0.26, top + 0.10),
              (0.055, 0.10, 0.17), beam, bevel=0.012)


def _healing_station(c, mats, *, state):
    wood = mat(mats, "elite_plank")
    stone = mat(mats, "stone_block")
    leaf = mat(mats, "roof_leaf")
    cloth = mat(mats, "roof_teal")
    if state == "ruined":
        g.box("healing_fallen_table", c, (0.10, -1.00, 0.22),
              (0.55, 0.28, 0.08), wood, bevel=0.018)
        return
    g.box("healing_stone_base", c, (0.35, -0.96, 0.20),
          (0.58, 0.31, 0.14), stone, bevel=0.025)
    if state == "construction":
        return
    if state == "damaged":
        g.box("healing_broken_table", c, (0.28, -0.96, 0.29),
              (0.49, 0.27, 0.07), wood, bevel=0.02,
              rotation=(0, 0, 0.12))
        return
    g.box("healing_table", c, (0.35, -0.96, 0.43),
          (0.59, 0.32, 0.10), wood, bevel=0.025)
    for side in (-1, 1):
        g.cylinder(f"healing_tray_{side}", c,
                   (0.35 + side * 0.17, -0.96, 0.51),
                   0.11, 0.07, stone, vertices=12)
        if state != "no_keeper":
            for i in range(3):
                g.sphere(f"healing_herb_{side}_{i}", c,
                         (0.30 + side * 0.17 + i * 0.04, -0.96, 0.56),
                         (0.045, 0.065, 0.035), leaf, segments=8)
    g.box("healing_canopy", c, (0.34, -0.96, 0.89),
          (0.73, 0.41, 0.07), cloth, bevel=0.019)
    for side in (-1, 1):
        g.box(f"healing_roof_pole_{side}", c,
              (0.34 + side * 0.30, -0.96, 0.58),
              (0.07, 0.07, 0.60), wood, bevel=0.012)


def add_guardian_enclosure(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 6):
        raise ValueError(f"Unsupported guardian enclosure level: {level}")
    if state not in {"construction", "active", "no_keeper", "damaged", "ruined"}:
        raise ValueError(f"Unsupported guardian enclosure state: {state}")

    wood = mat(mats, "elite_plank_highlight")
    dark = mat(mats, "elite_plank")
    stone = mat(mats, "stone_block")
    concrete = mat(mats, "reinforced_concrete")
    beam = mat(mats, "metal_worn") if level >= 3 else dark
    straw = mat(mats, "wood_cut")
    earth = mat(mats, "soil_light")
    leaf = mat(mats, "roof_leaf")
    gold = mat(mats, "roof_gold")
    cloth = mat(mats, "roof_green")

    # The standard ground is supplied by the orchestrator and identical in all states.
    for x in (-1.12, 1.12):
        for y in (-1.06, 1.06):
            g.box(f"foundation_block_{x}_{y}", c, (x, y, 0.17),
                  (0.33, 0.33, 0.13), stone if level >= 3 else concrete,
                  bevel=0.027)
    for y in (-1.06, 1.06):
        g.box(f"foundation_sill_{y}", c, (0, y, 0.15),
              (2.20, 0.17, 0.11), stone if level >= 3 else concrete,
              bevel=0.018)
    for x in (-1.12, 1.12):
        g.box(f"foundation_sill_{x}", c, (x, 0, 0.15),
              (0.17, 2.06, 0.11), stone if level >= 3 else concrete,
              bevel=0.018)

    # Premium boards are structural floorboards, never merely a pile beside the building.
    for i in range(9):
        g.box(f"yard_floor_plank_{i}", c, (-0.94 + i * 0.235, 0.0, 0.145),
              (0.19, 1.85, 0.055), wood if i % 3 else dark,
              bevel=0.014)

    count = level + 1
    visible_count = max(1, count - 2) if state == "construction" else count
    for i, (x, y) in enumerate(NESTS[:visible_count]):
        _nest(c, f"guardian_nest_{i+1}", x, y, dark, straw, earth, gold,
              broken=(state == "ruined" or state == "damaged" and i % 2 == 1))

    _fence(c, level, state, dark, stone, beam)
    canopy_count = min(level + 1, 4)
    for i in range(canopy_count):
        x, y = NESTS[i]
        canopy_state = state
        if state == "damaged":
            canopy_state = "active" if i == 0 else "ruined"
        _canopy(c, f"guardian_shelter_{i+1}", x, y, wood, beam,
                cloth, state=canopy_state, tall=level >= 4)

    if level >= 4:
        _healing_station(c, mats, state=state)
    if state not in {"ruined", "construction"}:
        for side in (-1, 1):
            g.box(f"feeding_trough_{side}", c,
                  (side * 0.72, -0.97, 0.25), (0.36, 0.20, 0.13),
                  stone, bevel=0.025)
            if state != "no_keeper" and state != "damaged":
                for k in range(3):
                    g.sphere(f"feeding_herbs_{side}_{k}", c,
                             (side * 0.72 - 0.10 + k * 0.09, -0.97, 0.35),
                             (0.063, 0.054, 0.05), leaf, segments=8)
    if state == "no_keeper":
        g.box("keeper_absent_sign_post", c, (-0.14, -1.20, 0.47),
              (0.07, 0.07, 0.58), dark, bevel=0.012)
        g.box("keeper_absent_sign", c, (-0.14, -1.23, 0.76),
              (0.43, 0.07, 0.33), mat(mats, "roof_coral"), bevel=0.018)
        g.box("keeper_absent_emblem", c, (-0.14, -1.28, 0.76),
              (0.12, 0.02, 0.21), gold, bevel=0.008)
    if level >= 5 and state in {"active", "no_keeper"}:
        for side in (-1, 1):
            g.box(f"crystal_pedestal_{side}", c,
                  (side * 0.83, -1.20, 0.28), (0.22, 0.22, 0.24),
                  stone, bevel=0.025)
            g.cylinder(f"crystal_{side}", c,
                       (side * 0.83, -1.20, 0.60), 0.075, 0.38,
                       mat(mats, "amethyst"), vertices=6)
            g.cone(f"crystal_tip_{side}", c,
                   (side * 0.83, -1.20, 0.85), 0.075, 0, 0.14,
                   mat(mats, "amethyst"), vertices=6)
    if state == "construction":
        for i in range(4):
            g.box(f"loose_premium_board_{i}", c,
                  (0.32 + i * 0.10, -1.26, 0.17 + i * 0.035),
                  (0.54, 0.08, 0.05), wood, bevel=0.01)
    if state in {"damaged", "ruined"}:
        for i in range(5 if state == "ruined" else 3):
            g.box(f"fallen_fence_rail_{i}", c,
                  (-0.72 + 0.37 * i, -1.18 + 0.08 * (i % 2), 0.20),
                  (0.43, 0.08, 0.075), dark, bevel=0.01,
                  rotation=(0, 0, 0.14 * (i - 2)))
