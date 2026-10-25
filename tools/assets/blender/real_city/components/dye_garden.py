"""Open, four-colour Aeolian pigment garden with craftwork and growth stages."""

from __future__ import annotations

import math

from .. import geometry as g
from .. import materials
from .common import mat


def _colors(mats):
    colors = (("crimson", (0.82, 0.025, 0.065)), ("azure", (0.025, 0.18, 0.88)),
              ("ochre", (0.98, 0.48, 0.015)), ("violet", (0.48, 0.055, 0.82)))
    for name, rgb in colors:
        key = f"_dye_{name}"
        if key not in mats:
            mats[key] = materials.create_material(f"MAT_dye_garden_{name}", rgb, roughness=0.72)
    if "_dye_gold" not in mats:
        mats["_dye_gold"] = materials.create_material("MAT_dye_garden_gold", (0.91, 0.64, 0.20), roughness=0.36)
    if "_dye_faded" not in mats:
        mats["_dye_faded"] = materials.create_material("MAT_dye_garden_faded", (0.47, 0.40, 0.36), roughness=0.90)
    return tuple(mats[f"_dye_{name}"] for name, _ in colors)


def _base(c, mats, level, state):
    stone = mat(mats, "stone_block")
    soil = mat(mats, "soil")
    gold = mats["_dye_gold"]
    g.box("dye_stone_bed", c, (0, 0, 0.205), (2.38, 2.38, 0.20), stone, bevel=0.055)
    g.box("dye_growing_soil", c, (0, 0, 0.315), (2.05, 2.05, 0.035), soil, bevel=0.01)
    for side in (-1, 1):
        for axis in (0, 1):
            x, y = (side * 1.075, 0) if axis == 0 else (0, side * 1.075)
            size = (0.14, 2.04, 0.16) if axis == 0 else (2.04, 0.14, 0.16)
            if state == "ruined" and side == 1 and axis == 1:
                for offset in (-0.63, 0.63):
                    g.box(f"broken_outer_{side}_{axis}_{offset}", c,
                          (offset, y, 0.405), (0.71, 0.14, 0.16), stone, bevel=0.025)
            elif state == "damaged" and side == -1 and axis == 0:
                for offset in (-0.65, 0.65):
                    g.box(f"cracked_outer_{side}_{axis}_{offset}", c,
                          (x, offset, 0.405), (0.14, 0.70, 0.16), stone, bevel=0.025)
            elif state == "construction" and side == 1 and axis == 0:
                g.box("unplaced_stone_rail", c, (0.80, 1.35, 0.24), (0.14, 0.80, 0.13), stone,
                      bevel=0.025, rotation=(0, 0, 0.18))
            else:
                g.box(f"outer_stone_rail_{side}_{axis}", c, (x, y, 0.405), size, stone, bevel=0.027)
    for axis in (0, 1):
        if state == "ruined" and axis == 0:
            g.box("broken_cross_left", c, (-0.53, 0, 0.385), (0.79, 0.11, 0.12), stone, bevel=0.02)
            g.box("fallen_cross_right", c, (0.52, 0.24, 0.365), (0.80, 0.11, 0.12), stone,
                  bevel=0.02, rotation=(0, 0, 0.34))
        elif state == "construction" and axis == 1:
            g.box("uninstalled_cross", c, (0.94, 0.24, 0.34), (0.12, 1.52, 0.10), stone,
                  bevel=0.02, rotation=(0, 0, 0.30))
        else:
            size = (1.99, 0.12, 0.13) if axis == 0 else (0.12, 1.99, 0.13)
            g.box(f"cross_stone_divider_{axis}", c, (0, 0, 0.39), size, stone, bevel=0.021)
    for x in (-1.08, 1.08):
        for y in (-1.08, 1.08):
            g.box(f"carved_corner_pedestal_{x}_{y}", c, (x, y, 0.42),
                  (0.27, 0.27, 0.27), stone, bevel=0.045)
            if state not in {"construction", "ruined"}:
                g.cylinder(f"gold_corner_clamp_{x}_{y}", c, (x, y, 0.58), 0.085,
                           0.035, gold, vertices=12)
                if level >= 5:
                    g.sphere(f"star_glass_corner_{x}_{y}", c, (x, y, 0.625),
                             (0.075, 0.075, 0.055), mat(mats, "star_glass"),
                             segments=8, ring_count=4)
    if level >= 3 and state not in {"construction", "ruined"}:
        for i in range(4 + level):
            x = -0.82 + i * (1.64 / (3 + level))
            g.box(f"emerald_dust_mark_{i}", c, (x, -1.145, 0.50),
                  (0.075, 0.022, 0.035), mat(mats, "roof_green"), bevel=0.005)
    if level >= 5 and state in {"active", "stage04"}:
        for i in range(4):
            g.box(f"gold_stone_scroll_{i}", c, (-0.70 + i * 0.46, 1.156, 0.50),
                  (0.23, 0.025, 0.035), gold, bevel=0.009)


def _plant(c, mats, x, y, name, pigment, *, growth, level, crushed=False, faded=False, base_z=0.335):
    leaf = mat(mats, "roof_leaf") if not faded else mats["_dye_faded"]
    stem = mat(mats, "roof_green") if not faded else mats["_dye_faded"]
    height = (0.16, 0.25, 0.35, 0.43)[growth - 1] + level * 0.028
    if crushed:
        height *= 0.45
    g.cone(f"{name}_stem", c, (x, y, base_z + height / 2), 0.034, 0.011,
           height, stem, vertices=8)
    if growth >= 2:
        for j in (-1, 1):
            g.sphere(f"{name}_leaf_{j}", c,
                     (x + j * 0.075, y, base_z + 0.03 + height * 0.55),
                     (0.10, 0.052, 0.031), leaf, segments=8, ring_count=4)
    if growth >= 2 and not faded:
        radius = 0.063 if growth == 2 else 0.103 + level * 0.006
        g.sphere(f"{name}_flower", c, (x, y, base_z + 0.01 + height),
                 (radius, radius, radius * 0.62), pigment, segments=8, ring_count=4)
        if growth >= 3:
            g.sphere(f"{name}_heart", c, (x, y, base_z + 0.012 + height + radius * 0.35),
                     (radius * 0.33, radius * 0.33, radius * 0.19),
                     mats["_dye_gold"], segments=8, ring_count=4)


def _beds(c, mats, level, state, pigments):
    if state == "construction":
        return
    growth = int(state[-2:]) if state.startswith("stage") else 4
    for q, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        # A few organized rows read as colour blocks from the fixed game camera.
        count = 4 + level if growth >= 3 else 3 + level // 2
        if state == "ruined":
            count = 2
        for i in range(count):
            row, col = divmod(i, 3)
            x = sx * (0.24 + col * 0.21)
            y = sy * (0.26 + row * 0.20)
            if state == "damaged" and (i + q) % 2 == 0:
                continue
            _plant(c, mats, x, y, f"pigment_{q}_{i}", pigments[q],
                   growth=growth if state != "ruined" else 1, level=level,
                   crushed=state == "damaged" and i % 2 == 0,
                   faded=state == "ruined")


def _bowl(c, name, x, y, z, rim, pigment, *, tipped=False):
    g.cylinder(f"{name}_stone_foot", c, (x, y, z + 0.035), 0.13, 0.07,
               rim, vertices=12)
    g.cone(f"{name}_carved_bowl", c, (x, y, z + 0.13), 0.13, 0.18,
           0.13, rim, vertices=12, rotation=(0.32 if tipped else 0, 0, 0))
    g.cylinder(f"{name}_pigment", c, (x, y, z + 0.205), 0.145, 0.014,
               pigment, vertices=12, rotation=(0.32 if tipped else 0, 0, 0))


def _craftwork(c, mats, level, state, pigments):
    stone = mat(mats, "stone_block")
    gold = mats["_dye_gold"]
    wood = mat(mats, "elite_plank")
    growth = int(state[-2:]) if state.startswith("stage") else 4
    if state == "ruined":
        for i in range(4):
            g.box(f"torn_fabric_{i}", c, (-1.20 + i * 0.33, -1.34, 0.25),
                  (0.25, 0.12, 0.025), mats["_dye_faded"], bevel=0.005,
                  rotation=(0, 0, -0.13 * i))
        if level >= 2:
            g.box("splintered_premium_sorting_rail", c, (0.76, 1.24, 0.25),
                  (0.10, 0.53, 0.08), wood, bevel=0.01, rotation=(0, 0, 0.35))
        if level >= 4:
            g.cylinder("fallen_pigment_feed_gear", c, (1.18, 0.32, 0.25),
                       0.13, 0.06, gold, vertices=12)
        if level >= 5:
            for i in range(2):
                g.mesh(f"broken_star_glass_{i}", c,
                       [(0.81 + i * 0.28, -0.72, 0.23),
                        (0.95 + i * 0.28, -0.68, 0.23),
                        (0.86 + i * 0.28, -0.54, 0.26)],
                       [(0, 1, 2)], mat(mats, "star_glass"))
        return
    if state == "construction":
        for i in range(3):
            g.cylinder(f"rolled_unfitted_fabric_{i}", c,
                       (-0.67 + 0.30 * i, -1.28, 0.28), 0.055, 0.29,
                       pigments[i], vertices=10, rotation=(0, math.pi / 2, 0))
        g.box("loose_premium_wood", c, (0.68, -1.28, 0.245),
              (0.50, 0.10, 0.055), wood, bevel=0.015)
        if level >= 2:
            for i in range(min(level - 1, 3)):
                g.box(f"uninstalled_premium_rail_{i}", c,
                      (0.84, 0.93 - i * 0.21, 0.25),
                      (0.10, 0.62, 0.055), wood, bevel=0.012)
        if level >= 3:
            _bowl(c, "uninstalled_pigment_bowl", -1.30, 0.43, 0.17,
                  stone, pigments[0])
        if level >= 4:
            g.cylinder("uninstalled_mechanism_gear", c, (1.28, 0.38, 0.24),
                       0.14, 0.07, gold, vertices=12)
        if level >= 5:
            g.box("star_glass_installation_crate", c, (1.28, -0.44, 0.28),
                  (0.26, 0.25, 0.14), wood, bevel=0.012)
            g.sphere("star_glass_uninstalled", c, (1.28, -0.44, 0.39),
                     (0.075, 0.075, 0.06), mat(mats, "star_glass"),
                     segments=8, ring_count=4)
        return
    for i in range(2 + (level >= 3) + (level >= 5)):
        x = -0.86 + i * 0.43
        if state == "damaged" and i % 2 == 0:
            g.box(f"fallen_sample_{i}", c, (x, -1.29, 0.25),
                  (0.24, 0.20, 0.018), pigments[i % 4], bevel=0.003,
                  rotation=(0, 0, 0.2))
            continue
        g.box(f"carved_sample_post_{i}", c, (x, -1.20, 0.53),
              (0.085, 0.085, 0.52), stone, bevel=0.017)
        g.box(f"gold_sample_clip_{i}", c, (x, -1.20, 0.815),
              (0.15, 0.08, 0.035), gold, bevel=0.008)
        g.box(f"fabric_swatches_{i}", c, (x, -1.22, 0.675),
              (0.21, 0.025, 0.23), pigments[i % 4], bevel=0.004)
    if level >= 2:
        g.box("premium_sorting_rail", c, (0.78, 1.23, 0.62),
              (0.10, 0.85, 0.09), wood, bevel=0.018)
        for y in (0.87, 1.57):
            g.box(f"sorting_rail_leg_{y}", c, (0.78, y, 0.42),
                  (0.10, 0.10, 0.42), wood, bevel=0.012)
    if growth == 4 or state == "damaged":
        for i in range(min(level, 3)):
            _bowl(c, f"pigment_tray_{i}", -1.29 + i * 0.30, 0.42, 0.22,
                  stone, pigments[i], tipped=state == "damaged" and i == 1)
    # The centre is a stone planter, physically rooted in the cross junction.
    _bowl(c, "central_rare_flower_chalice", 0, 0, 0.44, stone, gold)
    if growth >= 2 and state != "damaged":
        count = 1 + level // 2 if growth >= 3 else 1
        for i in range(count):
            angle = i * math.tau / max(count, 1)
            _plant(c, mats, 0.065 * math.cos(angle), 0.065 * math.sin(angle),
                   f"rare_flower_{i}", pigments[3], growth=growth, level=level,
                   base_z=0.65)
    if level >= 4 and state != "damaged":
        g.box("mechanism_stone_plinth", c, (1.27, 0.32, 0.30),
              (0.29, 0.40, 0.16), stone, bevel=0.025)
        g.cylinder("pigment_feed_gear", c, (1.27, 0.32, 0.44), 0.13,
                   0.07, gold, vertices=12)
        g.cylinder("mechanism_hub", c, (1.27, 0.32, 0.495), 0.048,
                   0.04, mat(mats, "copper"), vertices=12)
        for i in range(6):
            angle = math.tau * i / 6
            g.box(f"mechanism_tooth_{i}", c,
                  (1.27 + 0.13 * math.cos(angle), 0.32 + 0.13 * math.sin(angle), 0.45),
                  (0.06, 0.06, 0.06), gold, bevel=0.008, rotation=(0, 0, angle))
    if state == "damaged":
        for i, (x, y) in enumerate(((0.55, 0.30), (-0.48, -0.52), (0.55, -0.52))):
            g.cylinder(f"spilled_pigment_{i}", c, (x, y, 0.345),
                       0.16 + 0.04 * i, 0.01, pigments[i], vertices=12)
        for i in range(4):
            g.box(f"fallen_stone_and_rail_{i}", c, (0.64 + i * 0.13, -0.46, 0.25),
                  (0.22, 0.12, 0.08), stone if i % 2 else wood,
                  bevel=0.01, rotation=(0, 0, 0.22 * i))


def add_dye_garden(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 7):
        raise ValueError(f"Unsupported dye garden level: {level}")
    if state not in {"construction", "stage01", "stage02", "stage03", "stage04", "active", "damaged", "ruined"}:
        raise ValueError(f"Unsupported dye garden state: {state}")
    pigments = _colors(mats)
    _base(c, mats, level, state)
    _beds(c, mats, level, state, pigments)
    _craftwork(c, mats, level, state, pigments)
