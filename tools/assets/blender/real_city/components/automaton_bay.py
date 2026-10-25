"""Five levels of an Aeolian automaton workshop and six service states."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _frame(c, stem: str, x: float, y: float, steel, copper, *, complete: bool):
    """A bolted assembly gantry with a visible empty cradle."""
    for side in (-1, 1):
        px = x + side * 0.27
        g.box(f"{stem}_foot_{side}", c, (px, y, 0.30), (0.24, 0.27, 0.16), steel, bevel=0.025)
        g.box(f"{stem}_post_{side}", c, (px, y, 0.78 if complete else 0.56),
              (0.105, 0.105, 0.84 if complete else 0.40), steel, bevel=0.015)
        g.cylinder(f"{stem}_pivot_{side}", c, (px, y - 0.08, 0.80 if complete else 0.52),
                   0.08, 0.06, copper, vertices=12, rotation=(math.pi / 2, 0, 0))
    g.box(f"{stem}_cradle", c, (x, y, 0.40), (0.46, 0.27, 0.10), copper, bevel=0.022)
    if complete:
        g.box(f"{stem}_lintel", c, (x, y, 1.23), (0.68, 0.12, 0.12), steel, bevel=0.021)
        g.box(f"{stem}_suspended_tool", c, (x, y, 1.09), (0.12, 0.16, 0.23), copper, bevel=0.020)
        g.cylinder(f"{stem}_top_bearing", c, (x, y, 1.33), 0.12, 0.08, copper, vertices=16)


def _debris(c, steel, copper, stone, *, ruined: bool):
    count = 6 if ruined else 4
    for i in range(count):
        x = -0.84 + (i % 3) * 0.68
        y = 0.73 - (i // 3) * 0.35
        g.box(f"fallen_frame_segment_{i}", c, (x, y, 0.20),
              (0.42, 0.10, 0.10), steel, bevel=0.015,
              rotation=(0, 0, 0.18 * (i % 3 - 1)))
        g.cylinder(f"fallen_copper_joint_{i}", c, (x + 0.12, y, 0.18),
                   0.09, 0.08, copper, vertices=12)
    for i in range(3 if ruined else 2):
        g.box(f"fallen_masonry_{i}", c, (-0.67 + i * 0.54, -0.84, 0.20),
              (0.28, 0.25, 0.13), stone, bevel=0.024)


def add_automaton_bay(c, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 6):
        raise ValueError(f"Unsupported automaton bay level: {level}")
    if state not in {"construction", "active", "no_mechanic", "no_fuel", "damaged", "ruined"}:
        raise ValueError(f"Unsupported automaton bay state: {state}")

    stone = mat(mats, "reinforced_concrete")
    steel = mat(mats, "steel_light")
    dark = mat(mats, "dark_metal")
    copper = mat(mats, "copper")
    armor = mat(mats, "armor")
    light = mat(mats, "glass_cyan")
    off = mat(mats, "stone_shadow")
    char = mat(mats, "damage_char")
    build = state == "construction"
    damaged = state == "damaged"
    ruined = state == "ruined"

    # The common ground tile comes from the orchestrator. Stone plinth is equipment.
    for x in (-0.80, 0.80):
        for y in (-0.75, 0.75):
            g.box(f"concrete_corner_{x}_{y}", c, (x, y, 0.20),
                  (0.38, 0.38, 0.15), stone, bevel=0.027)
    for y in (-0.75, 0.75):
        g.box(f"low_concrete_sill_{y}", c, (0, y, 0.20),
              (1.65, 0.19, 0.15), stone, bevel=0.025)
    for x in (-0.80, 0.80):
        g.box(f"low_concrete_sill_x_{x}", c, (x, 0, 0.20),
              (0.19, 1.52, 0.15), stone, bevel=0.025)
    if ruined:
        g.box("collapsed_bench_top", c, (-0.08, -0.22, 0.25),
              (0.90, 0.36, 0.10), dark, bevel=0.025, rotation=(0, 0, 0.17))
        _debris(c, steel, copper, stone, ruined=True)
        if level >= 3:
            g.cylinder("fallen_test_wheel", c, (0.72, 0.10, 0.23),
                       0.22, 0.10, copper, vertices=16)
        if level >= 5:
            for i in range(3):
                g.box(f"fallen_roof_panel_{i}", c, (-0.62 + 0.61 * i, 0.42, 0.22),
                      (0.48, 0.31, 0.08), armor, bevel=0.02,
                      rotation=(0, 0, 0.14 * (i - 1)))
        return

    # Workbench legs physically carry the top; construction is visibly incomplete.
    for x in (-0.56, 0.56):
        for y in (-0.35, 0.15):
            if build and x > 0 and y > 0:
                continue
            g.box(f"bench_leg_{x}_{y}", c, (x, y, 0.42),
                  (0.105, 0.105, 0.36), dark, bevel=0.017)
    g.box("bench_top", c, (-0.12 if build else 0, -0.10, 0.63 if not damaged else 0.40),
          (0.90 if build else 1.24, 0.67, 0.10), dark, bevel=0.033,
          rotation=(0, 0, 0 if not damaged else 0.12))
    if damaged:
        _debris(c, steel, copper, stone, ruined=False)
        g.box("broken_workbench_tool", c, (-0.24, -0.10, 0.50),
              (0.38, 0.16, 0.10), steel, bevel=0.015)
        if level >= 5:
            g.box("remaining_roof_post", c, (-0.95, 0.75, 0.66),
                  (0.13, 0.13, 0.92), armor, bevel=0.02)
            g.box("fallen_roof_plate", c, (0.64, 0.53, 0.26),
                  (0.58, 0.44, 0.08), armor, bevel=0.02,
                  rotation=(0, 0, -0.2))
        return

    if not build:
        for i, x in enumerate((-0.37, 0.02, 0.41)):
            g.box(f"bench_steel_vise_{i}", c, (x, -0.08, 0.71),
                  (0.20, 0.15, 0.07), steel, bevel=0.015)
            g.cylinder(f"bench_copper_gear_{i}", c, (x, 0.12, 0.73),
                       0.10, 0.05, copper, vertices=12)
        g.box("workbench_toolbox", c, (-0.47, -0.36, 0.80),
              (0.28, 0.18, 0.25), armor, bevel=0.026)
        g.box("workbench_toolbox_lid", c, (-0.47, -0.36, 0.94),
              (0.33, 0.22, 0.06), steel, bevel=0.015)
    else:
        g.box("uninstalled_bench_plate", c, (0.70, -0.48, 0.20),
              (0.54, 0.30, 0.09), steel, bevel=0.02)
        g.box("uninstalled_lintel", c, (-0.76, 0.54, 0.19),
              (0.60, 0.10, 0.09), steel, bevel=0.016)

    # The first visible assembly station is always present; the second is L2.
    _frame(c, "primary_gantry", -0.45, 0.52, steel, copper, complete=not build)
    if level >= 2:
        _frame(c, "secondary_gantry", 0.44, 0.52, armor, copper,
               complete=not build)

    if level >= 3:
        # Wheel test stand is a separate, fully supported upgrade.
        g.box("test_stand_pedestal", c, (0.80, -0.58, 0.39),
              (0.37, 0.32, 0.53), stone, bevel=0.035)
        g.cylinder("test_stand_axle", c, (0.80, -0.68, 0.72),
                   0.075, 0.17, steel, vertices=12,
                   rotation=(math.pi / 2, 0, 0))
        if not build:
            g.cylinder("test_wheel", c, (0.80, -0.82, 0.72),
                       0.24, 0.09, copper, vertices=20,
                       rotation=(math.pi / 2, 0, 0))
            g.cylinder("test_wheel_hub", c, (0.80, -0.87, 0.72),
                       0.085, 0.11, dark, vertices=12,
                       rotation=(math.pi / 2, 0, 0))

    if level >= 4:
        # A repair arm anchored to the reinforced rear corner.
        g.box("manipulator_base", c, (0.88, 0.69, 0.40),
              (0.33, 0.33, 0.33), stone, bevel=0.035)
        g.cylinder("manipulator_turntable", c, (0.88, 0.69, 0.60),
                   0.18, 0.11, copper, vertices=16)
        g.beam("manipulator_lower_link", c, (0.88, 0.69, 0.66),
               (0.99, 0.69, 1.18 if not build else 0.91), 0.13, armor)
        if not build:
            g.cylinder("manipulator_elbow", c, (0.99, 0.69, 1.18),
                       0.14, 0.13, copper, vertices=16)
            g.beam("manipulator_upper_link", c, (0.99, 0.69, 1.18),
                   (0.58, 0.47, 1.43), 0.11, armor)
            for side in (-1, 1):
                g.beam(f"manipulator_gripper_{side}", c,
                       (0.58, 0.47, 1.43), (0.51 + side * 0.10, 0.32, 1.29),
                       0.055, steel)

    if level < 5:
        # Narrow side canopy shelters the workstation without hiding the gantries.
        for y in (-0.75, 0.75):
            g.box(f"canopy_post_{y}", c, (-0.80, y, 0.77 if not build else 0.55),
                  (0.10, 0.10, 1.14 if not build else 0.70), steel, bevel=0.015)
        if not build:
            g.box("workstation_canopy", c, (-0.80, 0, 1.38),
                  (0.53, 1.66, 0.09), armor, bevel=0.023)
            for y in (-0.54, 0.54):
                g.box(f"canopy_copper_trim_{y}", c, (-0.80, y, 1.43),
                      (0.48, 0.045, 0.025), copper, bevel=0.006)
        else:
            g.box("uninstalled_canopy_panel", c, (0.72, 0.62, 0.20),
                  (0.47, 0.40, 0.08), armor, bevel=0.018)

    if level >= 5:
        # Closed upper workshop cover; construction leaves most roof panels off.
        for x in (-0.93, 0.93):
            for y in (-0.83, 0.83):
                if build and x > 0:
                    continue
                g.box(f"roof_support_{x}_{y}", c, (x, y, 0.94),
                      (0.14, 0.14, 1.30), armor, bevel=0.022)
        if not build:
            for x in (-0.55, 0, 0.55):
                g.box(f"roof_panel_{x}", c, (x, 0, 1.64),
                      (0.61, 1.74, 0.10), armor, bevel=0.025)
                g.box(f"roof_copper_seam_{x}", c, (x + 0.26, 0, 1.70),
                      (0.045, 1.68, 0.03), copper, bevel=0.007)
            g.box("front_header", c, (0, -0.85, 1.51),
                  (1.98, 0.13, 0.16), steel, bevel=0.024)
            g.cylinder("beacon_socket", c, (0, 0, 1.75),
                       0.18, 0.12, copper, vertices=20)
            g.cylinder("beacon_lens", c, (0, 0, 1.86),
                       0.13, 0.13, light if state == "active" else off,
                       vertices=20)
        else:
            g.box("roof_panel_on_ground", c, (0.72, -0.60, 0.20),
                  (0.62, 0.38, 0.09), armor, bevel=0.021)

    if build:
        return

    # Service status is readable at map distance and preserves complete geometry.
    indicator = light if state == "active" else off if state == "no_fuel" else copper
    g.box("front_control_housing", c, (0, -0.85, 0.47),
          (0.40, 0.13, 0.31), dark, bevel=0.028)
    g.box(f"front_indicator_{state}", c, (0, -0.925, 0.48),
          (0.23, 0.03, 0.15), indicator, bevel=0.008)
    g.box("fuel_canister", c, (0.61, -0.67, 0.37),
          (0.25, 0.22, 0.31), copper, bevel=0.036)
    g.box("fuel_cap", c, (0.61, -0.67, 0.54),
          (0.16, 0.13, 0.06), steel, bevel=0.012)
    if state == "no_fuel":
        g.box("empty_fuel_marker", c, (0.61, -0.797, 0.37),
              (0.16, 0.025, 0.20), char, bevel=0.006)
    else:
        g.box("fuel_level_marker", c, (0.61, -0.797, 0.37),
              (0.15, 0.025, 0.19), light, bevel=0.006)
    if state == "no_mechanic":
        g.box("parked_tool_rack", c, (-0.75, -0.59, 0.63),
              (0.13, 0.13, 0.74), steel, bevel=0.013)
        g.box("vacant_maintenance_sign", c, (-0.75, -0.64, 1.01),
              (0.34, 0.09, 0.26), copper, bevel=0.018)
        g.beam("parked_wrench", c, (-0.76, -0.67, 0.58),
               (-0.76, -0.67, 0.81), 0.06, dark)
