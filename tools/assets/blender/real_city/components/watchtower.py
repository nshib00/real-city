"""One-level observation tower for the Real City defense catalog."""

from __future__ import annotations

from .. import geometry as g
from .common import mat


def add_watchtower(c, mats: dict, *, level: int, state: str) -> None:
    if level != 1 or state not in {"construction", "active", "damaged"}:
        raise ValueError(f"Unsupported watchtower variant: {level}/{state}")

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
