"""Low, passable resin trap with four material upgrades and six clear states."""

from __future__ import annotations

from .. import geometry as g
from .common import mat


STATES = {"construction", "armed", "triggered", "empty", "damaged", "ruined"}


def _plank(c, name, x, y, z, sx, sy, material, *, angle=0.0):
    g.box(name, c, (x, y, z), (sx, sy, 0.09), material, bevel=0.022, rotation=(0, 0, angle))


def _channel(c, mats, *, level, state, index, cy, width):
    wood = mat(mats, "wood_pale")
    dark = mat(mats, "wood_dark")
    metal = mat(mats, "steel_light" if level >= 4 else "metal_worn")
    resin = mat(mats, "resin_amber")
    resin_edge = mat(mats, "resin_highlight")
    stone = mat(mats, "stone_block")
    half = width / 2
    if state == "ruined":
        for side in (-1, 1):
            _plank(c, f"ruin_channel_{index}_side_{side}", side * (half + 0.10), cy + side * 0.13,
                   0.115, 0.64, 0.14, wood, angle=side * 0.28)
        g.box(f"ruin_resin_remnant_{index}", c, (0.0, cy, 0.107), (0.44, width * 0.48, 0.025),
              resin, bevel=0.012)
        return

    # Flat basin at terrain level: a monster remains visible when crossing it.
    g.box(f"channel_{index}_plank_floor", c, (0, cy, 0.113), (1.42, width, 0.09), dark, bevel=0.035)
    if state != "empty":
        fill = 0.40 if state == "construction" else 0.58 if state == "damaged" else 0.92
        g.box(f"channel_{index}_resin", c, (-0.12 if state == "construction" else 0, cy, 0.164),
              (1.29 * fill, width * 0.77, 0.018), resin, bevel=0.009)
        if state in {"armed", "triggered"}:
            for i in range(3):
                g.box(f"channel_{index}_resin_sheen_{i}", c,
                      (-0.37 + i * 0.34, cy - 0.045 + i * 0.025, 0.176),
                      (0.14, 0.023, 0.009), resin_edge, bevel=0.004)
    else:
        for x in (-0.44, 0.0, 0.44):
            g.box(f"empty_basin_slit_{index}_{x}", c, (x, cy, 0.166),
                  (0.10, width * 0.54, 0.012), mat(mats, "damage_char"), bevel=0.003)

    for side in (-1, 1):
        if state == "construction" and side == 1:
            _plank(c, f"unmounted_rail_{index}_{side}", 0.94, cy + side * 0.22, 0.115,
                   0.55, 0.12, wood, angle=0.25)
            continue
        if state == "damaged" and side == 1:
            _plank(c, f"broken_rail_{index}_{side}", -0.36, cy + side * half, 0.155,
                   0.64, 0.11, wood, angle=0.22)
            _plank(c, f"fallen_rail_{index}_{side}", 0.86, cy + side * 0.29, 0.115,
                   0.50, 0.11, wood, angle=-0.30)
            continue
        for section in (-1, 0, 1):
            _plank(c, f"channel_{index}_rail_{side}_{section}", section * 0.47, cy + side * half,
                   0.18, 0.49, 0.13, stone if level >= 3 else wood)
            if level >= 3:
                g.box(f"channel_{index}_iron_cap_{side}_{section}", c,
                      (section * 0.47, cy + side * half, 0.24), (0.33, 0.075, 0.035), metal, bevel=0.008)
    for x in (-0.70, 0.70):
        if state == "construction" and x > 0:
            continue
        _plank(c, f"channel_{index}_end_{x}", x, cy, 0.18, 0.13, width + 0.17,
               stone if level >= 3 else wood)


def _shutter(c, mats, *, level, state, index, cy, width):
    if state in {"ruined", "construction"}:
        return
    wood = mat(mats, "wood_pale")
    iron = mat(mats, "steel_light" if level >= 4 else "metal_worn")
    for side in (-1, 1):
        if state == "damaged" and side == 1:
            _plank(c, f"torn_shutter_{index}_{side}", 0.84, cy + side * 0.24,
                   0.115, 0.42, 0.25, wood, angle=-0.52)
            continue
        angle = side * (0.68 if state == "triggered" else 0.44 if state == "armed" else 0.06)
        shutter_y = cy + side * (width * 0.55)
        shutter_z = 0.28 if state in {"armed", "triggered"} else 0.195
        g.box(f"shutter_{index}_{side}", c, (0.0, shutter_y, shutter_z),
              (1.05, 0.23, 0.07), wood, bevel=0.023, rotation=(angle, 0, 0))
        for x in (-0.42, 0.42):
            g.cylinder(f"hinge_{index}_{side}_{x}", c, (x, cy + side * (width * 0.63), 0.215),
                       0.055, 0.09, iron, vertices=12)
        if level >= 2 and state != "empty":
            g.beam(f"shutter_lift_{index}_{side}", c,
                   (0.49, cy + side * (width * 0.69), 0.20),
                   (0.49, shutter_y, shutter_z + 0.025), 0.045, iron)
        for x in (-0.30, 0.30):
            g.cylinder(f"shutter_rivet_{index}_{side}_{x}", c,
                       (x, shutter_y, shutter_z + 0.046), 0.025, 0.017, iron, vertices=8)


def add_resin_snare(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 5) or state not in STATES:
        raise ValueError(f"Unsupported resin snare variant: {level}/{state}")
    wood = mat(mats, "wood_pale")
    dark = mat(mats, "wood_dark")
    iron = mat(mats, "metal_worn")
    steel = mat(mats, "steel_light")
    stone = mat(mats, "stone_block")
    resin = mat(mats, "resin_amber")
    channels = [(0.0, 0.70)] if level < 4 else [(-0.38, 0.46), (0.38, 0.46)]

    if level >= 3 and state != "ruined":
        for x in (-0.82, 0.82):
            for y in (-0.64, 0.64):
                if state == "construction" and x > 0 and y > 0:
                    continue
                g.box(f"stone_foot_{x}_{y}", c, (x, y, 0.135), (0.24, 0.24, 0.14), stone, bevel=0.028)
        if state != "damaged":
            for y in (-0.65, 0.65):
                g.box(f"iron_outer_rail_{y}", c, (0, y, 0.205), (1.57, 0.075, 0.06),
                      steel if level == 4 else iron, bevel=0.014)
        else:
            g.box("broken_iron_rail", c, (-0.41, -0.65, 0.205), (0.70, 0.075, 0.06), iron, bevel=0.014)
    for index, (cy, width) in enumerate(channels):
        _channel(c, mats, level=level, state=state, index=index, cy=cy, width=width)
        _shutter(c, mats, level=level, state=state, index=index, cy=cy, width=width)
    if level >= 2 and state not in {"ruined", "construction"}:
        for side in (-1, 1):
            g.cylinder(f"lever_pivot_{side}", c, (side * 0.78, -0.13, 0.19),
                       0.07, 0.08, iron, vertices=12)
            g.beam(f"lever_arm_{side}", c, (side * 0.78, -0.13, 0.21),
                   (side * 0.91, -0.13, 0.31 if state != "empty" else 0.22), 0.048, iron)
    if level == 4 and state not in {"ruined", "construction"}:
        for x in (-0.70, 0.70):
            g.box(f"steel_cross_brace_{x}", c, (x, 0, 0.22), (0.10, 1.22, 0.065), steel, bevel=0.015)
        g.box("dual_channel_divider", c, (0, 0, 0.19), (1.48, 0.11, 0.15), stone, bevel=0.018)
    if state == "construction":
        for i in range(3):
            _plank(c, f"spare_plank_{i}", 0.85, -0.56 + i * 0.12, 0.12,
                   0.47, 0.08, wood, angle=0.13)
        g.cylinder("resin_installation_pot", c, (-0.91, 0.68, 0.18), 0.15, 0.20, iron, vertices=12)
        g.cylinder("resin_installation_surface", c, (-0.91, 0.68, 0.287), 0.125, 0.015, resin, vertices=12)
    elif state == "triggered":
        for i in range(4):
            g.box(f"resin_splash_{i}", c, (-0.49 + i * 0.32, 0.68 + 0.035 * (i % 2), 0.094),
                  (0.13, 0.10, 0.018), resin, bevel=0.009, rotation=(0, 0, 0.18 * i))
    elif state == "empty":
        g.box("empty_indicator_back", c, (-0.92, 0.68, 0.19), (0.25, 0.13, 0.18), iron, bevel=0.024)
        g.box("empty_indicator_slot", c, (-0.92, 0.60, 0.19), (0.12, 0.015, 0.07), dark, bevel=0.006)
    elif state in {"damaged", "ruined"}:
        for i in range(4 if state == "damaged" else 8):
            x = -0.70 + (i % 4) * 0.40
            y = 0.57 + (i // 4) * 0.16
            _plank(c, f"fallen_fragment_{i}", x, y, 0.115, 0.25, 0.08,
                   stone if level >= 3 and i % 3 == 0 else wood, angle=0.18 * (i - 2))
        if state == "damaged":
            g.box("escaped_resin", c, (0.62, 0.49, 0.096), (0.27, 0.21, 0.021), resin, bevel=0.01)
