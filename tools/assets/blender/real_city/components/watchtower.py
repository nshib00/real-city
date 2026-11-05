"""Six-level observation and signaling tower for the Real City defense catalog."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def add_watchtower(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 7) or state not in {"construction", "active", "damaged", "ruined"}:
        raise ValueError(f"Unsupported watchtower variant: {level}/{state}")
    if state == "ruined":
        _add_watchtower_ruined(c, mats, level)
        return
    if level > 1:
        _add_upgraded_watchtower(c, mats, level, state)
        return

    building = state == "construction"
    broken = state == "damaged"
    stone = mat(mats, "stone_block")
    stone_light = mat(mats, "stone_light")
    wood = mat(mats, "wood_beam")
    dark = mat(mats, "wood_dark")
    planks = mat(mats, "wood_pale")
    roof = mat(mats, "roof_teal")
    iron = mat(mats, "metal_worn")
    brass = mat(mats, "copper")
    glow = mat(mats, "window_warm")

    # The tiled ground is created by the orchestrator, identically for all states.
    # Stone course and four footings carry the wood uprights.
    for row, z in enumerate((0.18, 0.34)):
        for side, y in enumerate((-0.62, 0.62)):
            for i in range(5):
                x = -0.75 + i * 0.375 + (0.10 if row else 0)
                if x > 0.78:
                    continue
                g.box(f"plinth_{row}_{side}_{i}", c, (x, y, z),
                      (0.37, 0.22, 0.17), stone_light if (i + row) % 3 == 0 else stone,
                      bevel=0.025)
        for x in (-0.73, 0.73):
            g.box(f"plinth_return_{row}_{x}", c, (x, 0, z),
                  (0.21, 1.10, 0.17), stone, bevel=0.02)
    for x in (-0.58, 0.58):
        for y in (-0.52, 0.52):
            g.box(f"stone_foot_{x}_{y}", c, (x, y, 0.48),
                  (0.37, 0.37, 0.15), stone_light, bevel=0.035)

    # Open air under the deck makes this an observation tower, not a solid turret.
    for x in (-0.58, 0.58):
        for y in (-0.52, 0.52):
            if building and x > 0 and y < 0:
                continue
            top = 1.25 if building and x > 0 else 2.10
            g.box(f"upright_{x}_{y}", c, (x, y, (0.55 + top) / 2),
                  (0.19, 0.19, top - 0.55), wood, bevel=0.035)
            g.box(f"iron_shoe_{x}_{y}", c, (x, y, 0.66),
                  (0.225, 0.225, 0.15), iron, bevel=0.02)
            if not building or x < 0:
                for by in (-0.08, 0.13):
                    g.box(f"shoe_rivet_{x}_{y}_{by}", c, (x, y + by, 0.68),
                          (0.035, 0.025, 0.035), brass, bevel=0.006)

    # Bracing terminates at existing posts and transverse beams.
    for x in (-0.58, 0.58):
        if building and x > 0:
            continue
        for sign in (-1, 1):
            g.beam(f"side_brace_{x}_{sign}", c,
                   (x, sign * 0.52, 0.72), (x, -sign * 0.10, 1.56), 0.085, dark)
    for y in (-0.52, 0.52):
        if building and y < 0:
            continue
        g.beam(f"rear_brace_{y}", c, (-0.58, y, 0.78), (0.32, y, 1.72), 0.09, dark)

    if building:
        g.box("temporary_crossbar", c, (-0.58, 0, 1.77),
              (0.20, 1.22, 0.14), planks, bevel=0.018)
        for i in range(4):
            g.box(f"unmounted_deck_board_{i}", c,
                  (0.95, -0.48 + i * 0.22, 0.18 + i * 0.025),
                  (0.72, 0.17, 0.06), planks, bevel=0.012)
        for i in range(3):
            g.box(f"iron_parts_{i}", c, (-1.02 + 0.13 * i, 0.78, 0.15),
                  (0.09, 0.15, 0.07), iron, bevel=0.012)
        return

    for y in (-0.52, 0.52):
        g.box(f"deck_bearer_{y}", c, (0, y, 2.04),
              (1.50, 0.18, 0.18), dark, bevel=0.025)
    for i in range(9):
        if broken and i in (0, 1, 2, 3):
            continue
        x = -0.72 + i * 0.18
        g.box(f"deck_board_{i}", c, (x, 0, 2.17),
              (0.165, 1.45, 0.10), planks, bevel=0.015)
        if i % 2 == 0:
            for y in (-0.57, 0.57):
                g.cylinder(f"deck_nail_{i}_{y}", c, (x, y, 2.235),
                           0.019, 0.016, iron, vertices=8)

    # Ladder inclines against the near face; every rung meets the side rails.
    if not broken:
        for x in (-0.18, 0.18):
            g.beam(f"ladder_rail_{x}", c, (x, -1.12, 0.13),
                   (x, -0.75, 2.18), 0.07, wood)
        for i in range(8):
            z = 0.35 + i * 0.24
            y = -1.08 + (z - 0.13) * 0.18
            g.box(f"ladder_rung_{i}", c, (0, y, z),
                  (0.43, 0.09, 0.07), planks, bevel=0.014)
    else:
        for x in (-0.18, 0.18):
            g.beam(f"broken_ladder_rail_{x}", c,
                   (x, -1.12, 0.13), (x, -0.97, 0.94), 0.07, wood)
        for i in range(3):
            g.box(f"broken_ladder_rung_{i}", c,
                  (0, -1.08 + i * 0.04, 0.35 + i * 0.24),
                  (0.43, 0.09, 0.07), planks, bevel=0.012)

    if broken:
        _fallen_parts(c, mats)
        return

    # Narrow guard rails leave the front opening for the ladder.
    for x in (-0.69, 0.69):
        for y in (-0.60, 0.60):
            if x < 0 and y < 0:
                continue
            g.box(f"parapet_post_{x}_{y}", c, (x, y, 2.42),
                  (0.11, 0.11, 0.53), wood, bevel=0.02)
    for y in (-0.60, 0.60):
        g.box(f"parapet_long_{y}", c, (0, y, 2.63),
              (1.49, 0.10, 0.11), dark, bevel=0.018)
    g.box("parapet_right", c, (0.69, 0, 2.63),
          (0.10, 1.28, 0.11), dark, bevel=0.018)
    g.box("parapet_left_rear", c, (-0.69, 0.31, 2.63),
          (0.10, 0.68, 0.11), dark, bevel=0.018)

    # Light roof over the rear half keeps the deck visibly usable for lookout.
    for x in (-0.60, 0.60):
        g.box(f"canopy_post_{x}", c, (x, 0.52, 2.91),
              (0.105, 0.105, 0.95), wood, bevel=0.02)
    for y in (0.06, 0.93):
        g.box(f"canopy_crossbar_{y}", c, (0, y, 3.35),
              (1.45, 0.11, 0.12), dark, bevel=0.02)
    for i in range(7):
        x = -0.64 + i * 0.21
        g.box(f"canopy_board_{i}", c, (x, 0.50, 3.44),
              (0.20, 1.09, 0.08), roof, bevel=0.015,
              rotation=(0.08, 0, 0))
    g.box("canopy_front_trim", c, (0, -0.02, 3.41),
          (1.55, 0.10, 0.12), planks, bevel=0.018)

    # Lantern is signaling equipment. No weapon mount or firing elements.
    _lantern(c, iron, brass, glow, (0.57, 0.50, 3.56), fallen=False)


def _lantern(c, iron, brass, glow, loc, *, fallen: bool) -> None:
    x, y, z = loc
    g.box("lantern_base" if not fallen else "fallen_lantern_base", c,
          (x, y, z), (0.27, 0.24, 0.08), iron, bevel=0.025)
    g.box("lantern_glass" if not fallen else "fallen_lantern_glass", c,
          (x, y, z + 0.15), (0.19, 0.17, 0.25), glow, bevel=0.028)
    for sx in (-0.115, 0.115):
        for sy in (-0.10, 0.10):
            g.box(f"lantern_bar_{sx}_{sy}_{fallen}", c,
                  (x + sx, y + sy, z + 0.14), (0.025, 0.025, 0.29), iron,
                  bevel=0.006)
    g.box("lantern_cap" if not fallen else "fallen_lantern_cap", c,
          (x, y, z + 0.30), (0.29, 0.26, 0.07), brass, bevel=0.024)


def _fallen_parts(c, mats: dict) -> None:
    wood = mat(mats, "wood_beam")
    planks = mat(mats, "wood_pale")
    roof = mat(mats, "roof_teal")
    iron = mat(mats, "metal_worn")
    brass = mat(mats, "copper")
    glow = mat(mats, "window_warm")
    for i in range(4):
        g.box(f"fallen_deck_{i}", c,
              (-1.05 + 0.24 * i, 0.81, 0.14), (0.14, 0.67, 0.07),
              planks, bevel=0.012, rotation=(0, 0, 0.18 * i))
    for i in range(3):
        g.box(f"fallen_canopy_{i}", c,
              (0.35 + 0.22 * i, 1.01, 0.15), (0.18, 0.58, 0.07),
              roof, bevel=0.012, rotation=(0, 0, -0.15 * i))
    g.beam("broken_parapet", c, (-0.83, -0.78, 0.16),
           (-0.28, -0.92, 0.21), 0.09, wood)
    _lantern(c, iron, brass, glow, (1.05, -0.30, 0.16), fallen=True)


def _add_upgraded_watchtower(c, mats: dict, level: int, state: str) -> None:
    """Keep the one-tile open lookout while accumulating distinct signal equipment."""
    construction = state == "construction"
    damaged = state == "damaged"
    stone = mat(mats, "stone_block" if level >= 3 else "stone_light")
    stone_trim = mat(mats, "stone_light")
    wood = mat(mats, "wood_beam")
    plank = mat(mats, "wood_pale")
    dark = mat(mats, "wood_dark")
    iron = mat(mats, "metal_worn")
    copper = mat(mats, "copper")
    glass = mat(mats, "glass_cyan", "window_warm")
    glow = mat(mats, "window_warm")
    roof = mat(mats, "roof_teal")

    deck_z = 2.25 + (level - 2) * 0.24
    # Ground is supplied by the orchestrator and is identical in every state.
    for row in range(2 + (level >= 4)):
        for side in (-1, 1):
            for i in range(4):
                x = -0.66 + 0.44 * i + (0.08 if row % 2 else 0)
                g.box(f"stone_course_{row}_{side}_{i}", c,
                      (x, side * 0.61, 0.17 + row * 0.16),
                      (0.42, 0.21, 0.17), stone_trim if (i + row) % 4 == 0 else stone, bevel=0.024)
        for x in (-0.72, 0.72):
            g.box(f"stone_return_{row}_{x}", c, (x, 0, 0.17 + row * 0.16),
                  (0.20, 1.16, 0.17), stone, bevel=0.02)
    footing_top = 0.57 if level >= 4 else 0.42
    for x in (-0.61, 0.61):
        for y in (-0.54, 0.54):
            g.box(f"foot_{x}_{y}", c, (x, y, footing_top),
                  (0.37, 0.37, 0.17), stone_trim, bevel=0.025)
            if construction and x > 0 and y < 0:
                continue
            post_top = deck_z - 0.11
            if construction and x > 0:
                post_top = footing_top + 0.95
            if damaged and x < 0 and y < 0:
                post_top = footing_top + 1.0
            g.box(f"post_{x}_{y}", c,
                  (x, y, (footing_top + post_top) / 2),
                  (0.20, 0.20, post_top - footing_top), wood if level <= 3 else stone,
                  bevel=0.03)
            g.box(f"post_clamp_{x}_{y}", c, (x, y, footing_top + 0.13),
                  (0.24, 0.24, 0.14), iron, bevel=0.02)
            if not construction and not (damaged and x < 0 and y < 0):
                g.beam(f"brace_{x}_{y}", c, (x, y, footing_top + 0.35),
                       (x - math.copysign(0.31, x), y, deck_z - 0.20), 0.085, dark if level <= 3 else copper)

    if construction:
        # A half-built frame with a staging beam and loose boards, rather than a finished tower with scaffolds.
        g.box("temporary_crossbar", c, (-0.61, 0, deck_z - 0.34),
              (0.16, 1.28, 0.14), plank, bevel=0.02)
        for i in range(5):
            g.box(f"staged_board_{i}", c, (0.88, -0.55 + i * 0.20, 0.16 + i * 0.017),
                  (0.72, 0.15, 0.065), plank, bevel=0.012)
        if level >= 3:
            g.box("unmounted_instrument_case", c, (-0.89, 0.83, 0.20),
                  (0.38, 0.30, 0.25), copper, bevel=0.035)
        if level >= 5:
            g.cylinder("unmounted_relay_drum", c, (0.88, 0.58, 0.25),
                       0.23, 0.30, copper, vertices=12)
        return

    # The damaged deck has a broad missing quadrant; the other boards still touch their bearers.
    for y in (-0.54, 0.54):
        g.box(f"deck_bearer_{y}", c, (0, y, deck_z - 0.13),
              (1.66, 0.19, 0.18), dark if level <= 3 else iron, bevel=0.02)
    for i in range(9):
        if damaged and i < 4:
            continue
        x = -0.72 + i * 0.18
        g.box(f"deck_board_{i}", c, (x, 0, deck_z),
              (0.17, 1.50, 0.09), plank, bevel=0.012)

    if damaged:
        for i in range(4):
            g.box(f"fallen_deck_{i}", c, (-1.04 + i * 0.20, 0.83, 0.16),
                  (0.15, 0.65, 0.06), plank, bevel=0.012, rotation=(0, 0, i * 0.11))
        g.beam("fallen_rail", c, (0.18, -0.95, 0.16), (0.95, -0.83, 0.19), 0.09, dark)
        _fallen_signal(c, level, mats)
        return

    # A balcony and clear front opening make the platform an observation post.
    for x in (-0.76, 0.76):
        for y in (-0.66, 0.66):
            if x < 0 and y < 0:
                continue
            g.box(f"rail_post_{x}_{y}", c, (x, y, deck_z + 0.28),
                  (0.10, 0.10, 0.55), wood if level <= 3 else iron, bevel=0.017)
    for y in (-0.66, 0.66):
        g.box(f"balcony_rail_{y}", c, (0, y, deck_z + 0.52),
              (1.61, 0.10, 0.10), dark if level <= 3 else copper, bevel=0.015)
    g.box("balcony_side_rail", c, (0.76, 0, deck_z + 0.52),
          (0.10, 1.38, 0.10), dark if level <= 3 else copper, bevel=0.015)
    g.box("balcony_rear_rail", c, (-0.76, 0.36, deck_z + 0.52),
          (0.10, 0.67, 0.10), dark if level <= 3 else copper, bevel=0.015)
    for x in (-0.18, 0.18):
        g.beam(f"ladder_rail_{x}", c, (x, -1.10, 0.13),
               (x, -0.75, deck_z + 0.02), 0.065, wood)
    for i in range(9 + (level >= 4)):
        z = 0.34 + i * (deck_z - 0.30) / (9 + (level >= 4))
        y = -1.10 + (z - 0.13) * 0.35 / (deck_z - 0.11)
        g.box(f"ladder_rung_{i}", c, (0, y, z),
              (0.42, 0.08, 0.065), plank, bevel=0.012)

    # Rear canopy is deliberately narrow so the observation deck remains open.
    canopy_top = deck_z + 1.12
    for x in (-0.65, 0.65):
        g.box(f"canopy_post_{x}", c, (x, 0.54, deck_z + 0.60),
              (0.11, 0.11, 1.12), wood if level <= 3 else stone, bevel=0.018)
    for y in (0.08, 0.94):
        g.box(f"canopy_bearer_{y}", c, (0, y, canopy_top),
              (1.51, 0.12, 0.12), dark, bevel=0.015)
    for i in range(6 if level >= 5 else 7):
        g.box(f"canopy_board_{i}", c, (-0.63 + i * 0.21, 0.51, canopy_top + 0.07),
              (0.20, 1.08, 0.07), roof, bevel=0.012)
    _signal_equipment(c, mats, level, deck_z, canopy_top)


def _signal_equipment(c, mats: dict, level: int, deck_z: float, canopy_top: float) -> None:
    iron = mat(mats, "metal_worn")
    copper = mat(mats, "copper")
    glass = mat(mats, "glass_cyan", "window_warm")
    glow = mat(mats, "window_warm")
    dark = mat(mats, "wood_dark")
    _lantern(c, iron, copper, glow, (0.56, 0.55, canopy_top + 0.15), fallen=False)
    if 2 <= level <= 4:
        g.cylinder("pennant_pole", c, (-0.58, 0.58, canopy_top + 0.44),
                   0.028, 0.82, iron, vertices=8)
        g.flag("wind_pennant", c, (-0.54, 0.58, canopy_top + 0.63),
               0.35, 0.22, mat(mats, "roof_teal"))
    if 3 <= level <= 4:
        # A broad, short roof-mounted viewing lens reads as optics, not a weapon barrel.
        g.cylinder("telescope_pivot", c, (-0.42, 0.19, canopy_top + 0.18),
                   0.17, 0.23, iron, vertices=12)
        g.beam("telescope_tube", c, (-0.42, 0.19, canopy_top + 0.29),
               (-0.42, -0.18, canopy_top + 0.41), 0.23, copper)
        g.cylinder("telescope_lens", c, (-0.42, -0.20, canopy_top + 0.42),
                   0.25, 0.05, glass, vertices=12, rotation=(math.radians(70), 0, 0))
    if level == 4:
        g.box("signal_lantern_guard", c, (0.56, 0.55, canopy_top + 0.36),
              (0.49, 0.40, 0.43), glass, bevel=0.045)
        g.cylinder("bell", c, (-0.56, -0.03, canopy_top - 0.20),
                   0.25, 0.31, copper, vertices=12)
        g.box("bell_hanger", c, (-0.56, -0.03, canopy_top - 0.02),
              (0.09, 0.08, 0.20), iron, bevel=0.01)
        for side in (-1, 1):
            g.box(f"reflector_{side}", c, (side * 0.83, 0.53, canopy_top + 0.31),
                  (0.10, 0.58, 0.72), copper, bevel=0.025, rotation=(0, 0, side * 0.35))
    if level >= 5:
        relay_x = 0 if level == 5 else -0.45
        relay_z = canopy_top + 0.31 if level == 5 else deck_z + 0.22
        drum_radius = 0.36 if level == 5 else 0.27
        drum_height = 0.50 if level == 5 else 0.30
        g.cylinder("relay_drum", c, (relay_x, 0.43, relay_z),
                   drum_radius, drum_height, copper, vertices=12)
        g.box("relay_drum_cover", c, (relay_x, 0.43, relay_z + drum_height / 2 + 0.04),
              (0.45 if level == 5 else 0.34, 0.45 if level == 5 else 0.34, 0.10), iron, bevel=0.025)
        g.box("relay_indicator", c, (relay_x, 0.22, relay_z + 0.03),
              (0.18, 0.035, 0.08), glass, bevel=0.01)
        for side in (-1, 1):
            g.beam(f"protected_copper_line_{side}", c,
                   (side * 0.42, 0.53, canopy_top + 0.07),
                   (side * 0.20, 0.43, canopy_top + 0.33), 0.045, copper)
            g.beam(f"signal_arm_{side}", c,
                   (side * 0.69, 0.55, canopy_top + 0.19),
                   (side * (1.12 if level == 5 else 0.96), 0.55, canopy_top + 0.57), 0.07, dark)
    if level >= 6:
        # One restrained crystal inside a protected beacon crown.
        crystal = mat(mats, "amethyst")
        g.cylinder("beacon_crown", c, (0, 0.42, canopy_top + 0.43),
                   0.31, 0.10, copper, vertices=12)
        g.cylinder("single_aeolian_crystal", c, (0, 0.42, canopy_top + 0.70),
                   0.12, 0.42, crystal, vertices=6)
        g.cylinder("beacon_cap", c, (0, 0.42, canopy_top + 0.97),
                   0.25, 0.08, iron, vertices=12)
        for sx in (-0.21, 0.21):
            g.box(f"beacon_guard_{sx}", c, (sx, 0.42, canopy_top + 0.69),
                  (0.035, 0.035, 0.47), iron, bevel=0.008)
        for side in (-1, 1):
            g.box(f"directional_reflector_{side}", c,
                  (side * 0.39, 0.42, canopy_top + 0.67),
                  (0.08, 0.32, 0.40), copper, bevel=0.025, rotation=(0, 0, side * 0.25))


def _fallen_signal(c, level: int, mats: dict) -> None:
    copper = mat(mats, "copper")
    iron = mat(mats, "metal_worn")
    glass = mat(mats, "glass_cyan", "window_warm")
    g.box("fallen_signal_case", c, (0.86, 0.70, 0.18),
          (0.39, 0.32, 0.23), copper, bevel=0.025, rotation=(0, 0, -0.24))
    if level >= 3:
        g.cylinder("fallen_lens", c, (-0.96, -0.56, 0.17),
                   0.16, 0.06, glass, vertices=12)
    if level >= 4:
        g.cylinder("fallen_bell", c, (0.70, -0.77, 0.19),
                   0.19, 0.18, copper, vertices=12)
    if level >= 5:
        g.cylinder("fallen_relay", c, (-0.72, 0.78, 0.24),
                   0.23, 0.27, iron, vertices=12)
    if level >= 6:
        g.cylinder("fallen_beacon_crown", c, (0.95, 0.32, 0.18),
                   0.27, 0.10, copper, vertices=12)


def _add_watchtower_ruined(c, mats: dict, level: int) -> None:
    """A collapsed low remnant, distinct from the standing damaged lookout."""
    stone = mat(mats, "stone_block" if level >= 3 else "stone_light")
    stone_light = mat(mats, "stone_light")
    wood = mat(mats, "wood_beam")
    plank = mat(mats, "wood_pale")
    iron = mat(mats, "metal_worn")
    copper = mat(mats, "copper")
    roof = mat(mats, "roof_teal")
    for row in range(2 + (level >= 4)):
        for side in (-1, 1):
            for i in range(4):
                if row == 2 and i in (1, 2):
                    continue
                g.box(f"ruin_stone_course_{row}_{side}_{i}", c,
                      (-0.66 + i * 0.44, side * 0.61, 0.17 + row * 0.16),
                      (0.42, 0.21, 0.17), stone_light if (i + row) % 4 == 0 else stone,
                      bevel=0.024)
        for x in (-0.72, 0.72):
            if row == 2 and x < 0:
                continue
            g.box(f"ruin_stone_return_{row}_{x}", c,
                  (x, 0, 0.17 + row * 0.16), (0.20, 1.16, 0.17), stone, bevel=0.02)
    for x, y, h in ((-0.58, 0.52, 0.72), (0.58, 0.52, 1.15), (0.58, -0.52, 0.55)):
        g.box(f"snapped_upright_{x}_{y}", c, (x, y, 0.46 + h / 2),
              (0.20, 0.20, h), wood if level <= 3 else stone, bevel=0.025)
        g.box(f"foot_remnant_{x}_{y}", c, (x, y, 0.46),
              (0.36, 0.36, 0.16), stone_light, bevel=0.02)
    for i in range(5):
        g.box(f"collapsed_deck_{i}", c,
              (-0.90 + i * 0.36, 0.78 - (i % 2) * 0.22, 0.17 + i * 0.015),
              (0.29, 0.61, 0.075), plank, bevel=0.012, rotation=(0, 0, i * 0.13))
    for i in range(4):
        g.box(f"collapsed_roof_{i}", c,
              (0.70 - i * 0.30, -0.78 + (i % 2) * 0.10, 0.19 + i * 0.012),
              (0.26, 0.51, 0.075), roof, bevel=0.012, rotation=(0, 0, -i * 0.16))
    g.beam("fallen_ladder", c, (-0.97, -0.42, 0.18),
           (-0.55, -0.97, 0.18), 0.10, wood)
    for i in range(3):
        g.box(f"fallen_stone_{i}", c, (0.90 - i * 0.24, 0.94, 0.16),
              (0.21, 0.19, 0.12), stone, bevel=0.02)
    g.box("broken_lantern", c, (-0.97, 0.22, 0.18),
          (0.27, 0.22, 0.18), iron, bevel=0.02)
    if level >= 3:
        g.cylinder("fallen_optic", c, (-0.83, -0.76, 0.16),
                   0.17, 0.06, mat(mats, "glass_cyan"), vertices=12)
    if level >= 4:
        g.cylinder("fallen_bell", c, (0.94, -0.17, 0.19),
                   0.18, 0.18, copper, vertices=12)
    if level >= 5:
        g.cylinder("crushed_relay", c, (0.54, 0.63, 0.29),
                   0.22, 0.20, copper, vertices=12)
    if level >= 6:
        g.cylinder("broken_beacon_crown", c, (0.32, -0.80, 0.21),
                   0.25, 0.08, iron, vertices=12)
