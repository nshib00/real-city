"""Crystal greenhouse with readable glazing, copper ribs and crystal crops."""

from __future__ import annotations

import math

from .. import geometry as g
from .. import materials
from .common import mat


def _ring(radius: float, z: float):
    return [(radius * math.cos(math.pi / 8 + i * math.pi / 4),
             radius * math.sin(math.pi / 8 + i * math.pi / 4), z) for i in range(8)]


def _pane(name, c, corners, material):
    # A separate planar pane keeps the plants legible and can be dropped from damaged states.
    return g.mesh(name, c, corners, [(0, 1, 2, 3)], material)


def _stone_base(c, level, state, stone, trim, soil):
    g.box("greenhouse_stone_plinth", c, (0, 0, 0.19), (2.18, 2.18, 0.19), stone, bevel=0.065)
    g.box("greenhouse_growing_soil", c, (0, 0, 0.295), (1.78, 1.78, 0.035), soil, bevel=0.01)
    for side in (-1, 1):
        for axis in (0, 1):
            x, y = (side * 1.02, 0) if axis == 0 else (0, side * 1.02)
            size = (0.12, 1.82, 0.095) if axis == 0 else (1.82, 0.12, 0.095)
            g.box(f"stone_coping_{side}_{axis}", c, (x, y, 0.315), size, stone, bevel=0.024)
    for x in (-0.98, 0.98):
        for y in (-0.98, 0.98):
            g.box(f"stone_corner_{x}_{y}", c, (x, y, 0.34), (0.28, 0.28, 0.19), stone, bevel=0.035)
    if level >= 3:
        for side in (-1, 1):
            for axis in (0, 1):
                x, y = (side * 1.15, 0) if axis == 0 else (0, side * 1.15)
                g.box(f"buttress_{side}_{axis}", c, (x, y, 0.46),
                      (0.19, 0.45, 0.48) if axis == 0 else (0.45, 0.19, 0.48),
                      stone, bevel=0.04)
    if level == 4 and state != "ruined":
        for i in range(8):
            x = -0.70 + (i % 4) * 0.47
            y = -1.045 if i < 4 else 1.045
            g.box(f"engraved_plinth_mark_{i}", c, (x, y, 0.37),
                  (0.16, 0.023, 0.025), trim, bevel=0.005)


def _crop(c, mats, x, y, index, *, level, state, central=False):
    stem = mat(mats, "roof_green")
    leaf = mat(mats, "roof_leaf")
    if "_crystal_fruit" not in mats:
        mats["_crystal_fruit"] = materials.create_material(
            "MAT_crystal_fruit_violet", (0.59, 0.18, 0.94),
            roughness=0.28, emission=(0.59, 0.18, 0.94), emission_strength=0.42)
    fruit = mats["_crystal_fruit"]
    glow = mat(mats, "runic_glow")
    damaged = state in {"damaged", "ruined"}
    growth = int(state[-2:]) if state.startswith("stage") else 4
    height = (0.25 if state == "construction" else 0.35 + level * 0.085) * (0.55 if damaged else 1)
    if growth < 4:
        height *= (0.50, 0.70, 0.86)[growth - 1]
    g.cone(f"crop_{index}_stem", c, (x, y, 0.31 + height / 2), 0.043, 0.018,
           height, stem, vertices=8)
    if state == "construction" or growth == 1:
        return
    for k in range(2 if damaged or growth == 2 else 3 + level // 2):
        angle = k * math.tau / (3 + level // 2) + index * 0.63
        z = 0.42 + k * (height * 0.16)
        dx, dy = 0.15 * math.cos(angle), 0.15 * math.sin(angle)
        g.beam(f"crop_{index}_branch_{k}", c, (x, y, z),
               (x + dx, y + dy, z + 0.09), 0.025, stem)
        g.sphere(f"crop_{index}_leaf_{k}", c,
                 (x + dx, y + dy, z + 0.10), (0.095, 0.045, 0.027),
                 leaf, segments=8, ring_count=4)
        if not damaged and growth >= 3 and (k + index) % (3 if growth == 3 else 2) == 0:
            g.aeolian_crystal(f"crop_{index}_fruit_{k}", c,
                               (x + dx * 1.22, y + dy * 1.22, z + 0.035),
                               0.075 + 0.012 * level, 0.17, fruit)
    if central and level >= 4:
        if state == "ruined":
            g.aeolian_crystal("broken_aeolian_crystal", c, (x + 0.17, y, 0.38),
                               0.13, 0.20, fruit)
        else:
            g.aeolian_crystal("central_aeolian_crystal", c,
                               (x, y, 0.38 + height), 0.14, 0.40, glow)


def _mechanism(c, mats, level, state):
    stone = mat(mats, "stone_block")
    copper = mat(mats, "copper")
    dark = mat(mats, "dark_metal")
    g.box("vent_drive_base", c, (0.84, -0.78, 0.42), (0.32, 0.28, 0.24), stone, bevel=0.035)
    if state == "ruined":
        g.cylinder("fallen_vent_gear", c, (0.69, -0.85, 0.36), 0.14, 0.045,
                   copper, vertices=12, rotation=(0.5, 0.2, 0.3))
        return
    g.cylinder("vent_gear", c, (0.84, -0.78, 0.58), 0.12 + 0.02 * level, 0.06,
               copper, vertices=12)
    g.cylinder("vent_hub", c, (0.84, -0.78, 0.63), 0.055, 0.04, dark, vertices=12)
    if state == "construction":
        return
    for k in range(3 + level):
        angle = k * math.tau / (3 + level)
        x, y = 0.84 + 0.12 * math.cos(angle), -0.78 + 0.12 * math.sin(angle)
        g.box(f"vent_tooth_{k}", c, (x, y, 0.59), (0.055, 0.07, 0.05), copper,
              bevel=0.01, rotation=(0, 0, angle))
    if level >= 3 and state != "damaged":
        g.box("vent_chimney", c, (0.85, -0.78, 0.85), (0.16, 0.16, 0.44),
              copper, bevel=0.03)
        g.cylinder("vent_cap", c, (0.85, -0.78, 1.08), 0.17, 0.06,
                   dark, vertices=12)


def _glasshouse(c, mats, level, state):
    copper = mat(mats, "copper")
    stone = mat(mats, "stone_block")
    glass = materials.create_material(f"MAT_crystal_greenhouse_clear_{level}_{state}",
                                       (0.46, 0.82, 0.90), roughness=0.24, alpha=0.34)
    star = mat(mats, "star_glass")
    broken = mat(mats, "glass_broken")
    low = _ring(0.98, 0.42)
    shoulder = _ring(0.98, 0.84 + level * 0.085)
    upper = _ring(0.65 + level * 0.015, 1.18 + level * 0.15)
    crown = _ring(0.20 + level * 0.015, 1.39 + level * 0.18)
    if state == "ruined":
        for i in range(8):
            a, b = low[i], low[(i + 1) % 8]
            g.beam(f"ruined_lower_frame_{i}", c, a, b, 0.08, copper)
        for i in range(7):
            x = -0.65 + i * 0.21
            g.mesh(f"ruin_glass_shard_{i}", c,
                   [(x, -0.60 + i % 2 * 0.40, 0.38),
                    (x + 0.17, -0.55 + i % 2 * 0.40, 0.39),
                    (x + 0.09, -0.30 + i % 2 * 0.40, 0.40)],
                   [(0, 1, 2)], broken)
        for i in (0, 2, 5):
            g.beam(f"fallen_copper_rib_{i}", c,
                   (-0.8 + i * 0.28, 0.60, 0.40), (-0.45 + i * 0.28, 0.30, 0.42),
                   0.075, copper)
        return
    if state == "construction":
        for i in (0, 1, 3, 5):
            g.beam(f"unfinished_upright_{i}", c, low[i], shoulder[i], 0.075, copper)
        for i in (1, 2, 4):
            x = -0.75 + 0.51 * (i - 1)
            g.mesh(f"uninstalled_glass_panel_{i}", c,
                   [(x, 0.68, 0.42), (x + 0.42, 0.68, 0.42),
                    (x + 0.42, 1.02, 0.44), (x, 1.02, 0.44)],
                   [(0, 1, 2, 3)], glass)
            g.beam(f"panel_copper_edge_{i}", c, (x, 0.68, 0.43),
                   (x + 0.42, 0.68, 0.43), 0.03, copper)
        g.box("unfitted_star_glass_crate", c, (-0.88, -0.78, 0.40),
              (0.25, 0.29, 0.13), stone, bevel=0.025)
        return
    for i in range(8):
        j = (i + 1) % 8
        # Entire roof and two wall sections are absent from the damaged greenhouse.
        omit_wall = state == "damaged" and i in (0, 1, 2)
        omit_roof = state == "damaged" and i in (0, 1, 2, 3)
        g.beam(f"lower_ring_{i}", c, low[i], low[j], 0.065, copper)
        if not omit_wall:
            _pane(f"wall_glass_{i}", c,
                  [low[i], low[j], shoulder[j], shoulder[i]], glass)
            g.beam(f"wall_upright_{i}", c, low[i], shoulder[i], 0.075, copper)
            g.beam(f"shoulder_ring_{i}", c, shoulder[i], shoulder[j], 0.075, copper)
        if not omit_roof:
            _pane(f"roof_glass_lower_{i}", c,
                  [shoulder[i], shoulder[j], upper[j], upper[i]],
                  star if level >= 4 and i % 3 == 0 else glass)
            _pane(f"roof_glass_upper_{i}", c,
                  [upper[i], upper[j], crown[j], crown[i]],
                  star if i == 0 or level >= 3 and i % 4 == 0 else glass)
            g.beam(f"dome_rib_lower_{i}", c, shoulder[i], upper[i], 0.072, copper)
            g.beam(f"dome_rib_upper_{i}", c, upper[i], crown[i], 0.062, copper)
            g.beam(f"dome_mid_ring_{i}", c, upper[i], upper[j], 0.062, copper)
            g.beam(f"crown_ring_{i}", c, crown[i], crown[j], 0.065, copper)
    if state == "damaged":
        for i in range(5):
            x = -0.70 + i * 0.30
            g.mesh(f"fallen_glass_{i}", c,
                   [(x, -0.85, 0.41), (x + 0.25, -0.70, 0.41),
                    (x + 0.09, -0.50, 0.43)], [(0, 1, 2)], broken)
        g.beam("bent_copper_rib", c, (0.6, -0.65, 0.43),
               (0.90, -0.20, 0.48), 0.08, copper)
        return
    g.cylinder("dome_top_lens", c, (0, 0, crown[0][2] + 0.065),
               0.20 + level * 0.02, 0.10, star, vertices=12)
    if level >= 2:
        for i in (2, 6):
            x, y, z = shoulder[i]
            g.cylinder(f"side_lens_{i}", c, (x, y, z + 0.04),
                       0.13, 0.045, star, vertices=12)


def add_crystal_greenhouse(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 5):
        raise ValueError(f"Unsupported crystal greenhouse level: {level}")
    if state not in {"construction", "stage01", "stage02", "stage03", "stage04", "active", "damaged", "ruined"}:
        raise ValueError(f"Unsupported crystal greenhouse state: {state}")
    stone = mat(mats, "stone_shadow") if state == "ruined" else mat(mats, "stone_block")
    copper = mat(mats, "copper")
    _stone_base(c, level, state, stone, copper, mat(mats, "soil"))
    plant_positions = ((0, 0), (-0.43, -0.22), (0.43, 0.22),
                       (-0.35, 0.45), (0.35, -0.46))
    count = 1 if state in {"construction", "ruined", "stage01"} else min(2, level + 1) if state == "stage02" else level + 1
    for i, (x, y) in enumerate(plant_positions[:count]):
        _crop(c, mats, x, y, i, level=level, state=state, central=i == 0)
    _mechanism(c, mats, level, state)
    _glasshouse(c, mats, level, state)
    if state not in {"construction", "ruined"}:
        for i, (x, y) in enumerate(((-0.96, -0.96), (0.96, -0.96),
                                     (-0.96, 0.96), (0.96, 0.96))):
            g.aeolian_crystal(f"corner_light_crystal_{i}", c,
                               (x, y, 0.49), 0.065, 0.20,
                               mat(mats, "amethyst"))
            g.cylinder(f"corner_crystal_socket_{i}", c,
                       (x, y, 0.39), 0.09, 0.065, copper, vertices=10)
    if level >= 2 and state in {"active", "stage04"}:
        for i in range(2 + level):
            x = -0.56 + i * (1.12 / (level + 1))
            g.sphere(f"emerald_dust_marker_{i}", c,
                     (x, -0.88, 0.40), (0.035, 0.035, 0.023),
                     mat(mats, "roof_green"), segments=8, ring_count=4)
    if state.startswith("stage") or state == "active":
        maturity = int(state[-2:]) if state.startswith("stage") else 4
        for i in range(4):
            x = -0.38 + i * 0.25
            g.cylinder(f"readiness_socket_{i}", c, (x, -1.13, 0.38),
                       0.075, 0.045, copper, vertices=10)
            if i < maturity:
                g.aeolian_crystal(f"readiness_light_{i}", c,
                                   (x, -1.13, 0.49), 0.07, 0.18,
                                   mat(mats, "amethyst"))
