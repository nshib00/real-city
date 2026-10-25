"""Fortified, enclosed munitions works with ten visible upgrade stages."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _box(c, name, pos, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, pos, size, material, bevel=bevel, rotation=rotation)


def _shell(c, m, level, state):
    wall = mat(m, "reinforced_concrete" if level >= 5 else "brick_warm" if level >= 3 else "concrete")
    steel = mat(m, "steel_light")
    dark = mat(m, "dark_metal")
    height = 1.04 + level * 0.075
    width = 1.53 + min(level, 6) * 0.057
    depth = 1.38 + min(level, 6) * 0.045
    _box(c, "structural_floor", (0, 0.12, 0.12), (width + 0.18, depth + 0.15, 0.17), wall, 0.045)
    # The chamber grows from a plain shielded shop to a reinforced secure hall.
    for x in (-width / 2, width / 2):
        _box(c, f"load_column_{x:.2f}", (x, 0.12, 0.18 + height / 2),
             (0.15, 0.17, height), steel if level >= 3 else wall, 0.03)
    for y in (0.12 - depth / 2, 0.12 + depth / 2):
        _box(c, f"rear_or_front_corner_{y:.2f}", (-width / 2, y, 0.18 + height / 2),
             (0.15, 0.16, height), steel if level >= 5 else wall, 0.03)
    # Construction exposes the assembly cell and lacks the top half of the outer wall.
    wall_h = height * (0.43 if state == "construction" else 1.0)
    for x in (-width / 2, width / 2):
        if state == "damaged" and x > 0:
            continue
        _box(c, f"side_armor_{x:.2f}", (x, 0.12, 0.18 + wall_h / 2),
             (0.12, depth, wall_h), wall, 0.025)
    _box(c, "rear_wall", (0, 0.12 + depth / 2, 0.18 + wall_h / 2),
         (width, 0.12, wall_h), wall, 0.025)
    for x in (-width * 0.31, width * 0.31):
        if state == "damaged" and x > 0:
            continue
        _box(c, f"front_armor_{x:.2f}", (x, 0.12 - depth / 2, 0.18 + wall_h / 2),
             (width * 0.34, 0.12, wall_h), wall, 0.025)
    if state == "construction":
        for x in (-0.35, 0.29):
            _box(c, f"unmounted_roof_panel_{x}", (x, -0.99, 0.19),
                 (0.52, 0.30, 0.09), steel)
        g.beam("temporary_cross_brace", c, (-width / 2, -0.48, 0.25),
               (width / 2, -0.48, 0.18 + height), 0.065, mat(m, "wood_beam"))
        return
    if state == "damaged":
        # An open front-right breach and collapsed roof remove roughly half the shell.
        _box(c, "surviving_roof_half", (-width * 0.25, 0.12, 0.23 + height),
             (width * 0.48, depth + 0.13, 0.13), dark, 0.035)
        _box(c, "collapsed_roof_section", (0.55, -1.00, 0.19),
             (0.73, 0.43, 0.13), dark, 0.035, (0, 0, -0.23))
        for i in range(5):
            _box(c, f"broken_armor_plate_{i}", (0.30 + (i % 3) * 0.26,
                 -0.80 - (i // 3) * 0.22, 0.12 + (i % 2) * 0.045),
                 (0.23, 0.14, 0.10), wall, 0.012, (0, 0, i * 0.22))
        _box(c, "exposed_broken_roof_rib", (0.30, 0.13, 0.21 + height),
             (0.10, depth * 0.65, 0.10), steel, 0.015)
        return
    _box(c, "sealed_roof", (0, 0.12, 0.23 + height),
         (width + 0.18, depth + 0.17, 0.16), dark, 0.045)
    for x in (-width * 0.31, width * 0.31):
        _box(c, f"roof_ridge_{x:.2f}", (x, 0.12, 0.36 + height),
             (0.13, depth + 0.18, 0.13), steel, 0.025)
    # Strong top silhouette remains legible above the enclosed work cell.
    for x in (-0.43, 0.43):
        vent_h = 0.22 + (level >= 4) * 0.12 + (level >= 7) * 0.14
        _box(c, f"roof_vent_{x}", (x, 0.35, 0.34 + height + vent_h / 2),
             (0.27, 0.32, vent_h), steel, 0.025)
        _box(c, f"roof_vent_cap_{x}", (x, 0.35, 0.37 + height + vent_h),
             (0.36, 0.42, 0.075), dark, 0.02)
        for i in range(2 if level < 7 else 3):
            _box(c, f"roof_vent_louver_{x}_{i}",
                 (x, 0.17, 0.30 + height + vent_h * (0.32 + i * 0.22)),
                 (0.20, 0.023, 0.026), dark, 0.005)
    _box(c, "sliding_steel_door", (0, -0.60, 0.18 + height * 0.36),
         (0.43, 0.08, height * 0.72), dark, 0.028)
    for x in (-0.14, 0.14):
        _box(c, f"door_reinforcing_strip_{x}", (x, -0.65, 0.18 + height * 0.38),
             (0.035, 0.025, height * 0.64), steel, 0.004)
    if level >= 3:
        for z in (0.32, 0.58):
            _box(c, f"front_blast_band_{z}", (0, -0.62, z),
                 (width + 0.12, 0.055, 0.055), steel)
        for x in (-width / 2, width / 2):
            _box(c, f"armor_face_{x}", (x, -0.61, 0.18 + height * 0.54),
                 (0.18, 0.045, height * 0.62), mat(m, "armor"), 0.012)
        for x in (-0.55, 0.55):
            _box(c, f"front_warning_tile_{x}", (x, -0.647, 0.53),
                 (0.22, 0.025, 0.09), mat(m, "flower_yellow"), 0.006)
    if level >= 2:
        _box(c, "receiving_hood", (-0.45, -0.69, 0.85),
             (0.40, 0.19, 0.16), steel, 0.025)
    if level >= 4:
        _box(c, "external_drive_housing", (width / 2 + 0.15, -0.14, 0.50),
             (0.32, 0.38, 0.49), dark, 0.035)
        g.cylinder("drive_face", c, (width / 2 + 0.32, -0.14, 0.52),
                   0.17, 0.05, mat(m, "copper"), vertices=18,
                   rotation=(0, math.pi / 2, 0))
    if level >= 5:
        for x in (-0.47, 0.47):
            _box(c, f"reinforced_roof_rail_{x}", (x, 0.12, 0.46 + height),
             (0.08, depth + 0.17, 0.12), steel)
        for y in (-0.30, 0.12, 0.54):
            _box(c, f"side_armor_plate_{y}", (width / 2 + 0.075, y, 0.47 + height * 0.37),
                 (0.055, 0.29, 0.49), mat(m, "armor"), 0.012)
            _box(c, f"side_armor_rivet_{y}", (width / 2 + 0.112, y, 0.42 + height * 0.37),
                 (0.023, 0.12, 0.035), steel, 0.004)
    if level >= 8:
        for x in (-0.53, 0.53):
            _box(c, f"precision_roof_panel_{x}", (x, 0.13, 0.48 + height),
                 (0.42, 0.55, 0.055), mat(m, "glass_cyan"), 0.016)
        _box(c, "reinforced_cross_beam", (0, -0.62, 0.17 + height),
             (width + 0.23, 0.14, 0.14), steel, 0.03)
    if level >= 6:
        _box(c, "roof_service_housing", (0, -0.11, 0.40 + height),
             (0.55 + (level >= 9) * 0.20, 0.43, 0.32),
             mat(m, "armor"), 0.035)
        for i in range(2 + (level >= 9)):
            _box(c, f"service_housing_louver_{i}",
                 (-0.17 + i * 0.17, -0.34, 0.45 + height),
                 (0.08, 0.025, 0.13), dark, 0.008)
    if level >= 7:
        for x in (-0.64, 0.64):
            g.cylinder(f"extractor_roof_stack_{x}", c,
                       (x, 0.56, 0.52 + height), 0.11, 0.42,
                       dark, vertices=18)
            g.cylinder(f"extractor_stack_cap_{x}", c,
                       (x, 0.56, 0.76 + height), 0.16, 0.07,
                       steel, vertices=18)
    if level >= 8:
        for x in (-0.54, 0.54):
            _box(c, f"control_beacon_{x}", (x, -0.18, 0.42 + height),
                 (0.13, 0.13, 0.22), mat(m, "glass_cyan"), 0.025)
    if level >= 10:
        for x in (-0.66, 0.66):
            _box(c, f"master_beam_post_{x}", (x, -0.07, 0.57 + height),
                 (0.12, 0.12, 0.52), steel, 0.025)
        _box(c, "master_gantry_crown", (0, -0.07, 0.90 + height),
             (1.45, 0.17, 0.14), steel, 0.03)


def _process(c, m, level, state):
    steel = mat(m, "steel_light" if level >= 3 else "metal_worn")
    dark = mat(m, "dark_metal")
    yellow = mat(m, "flower_yellow")
    if state == "construction":
        _box(c, "mixer_unfinished_base", (-0.28, 0.15, 0.31),
             (0.63, 0.55, 0.23), steel)
        g.cylinder("loose_sealed_drum", c, (0.70, -0.98, 0.27),
                   0.18, 0.38, steel, vertices=20, rotation=(0, math.pi / 2, 0))
        return
    if state == "damaged":
        _box(c, "crushed_mixer", (-0.29, 0.14, 0.34),
             (0.62, 0.51, 0.25), dark, rotation=(0, 0, 0.16))
        g.cylinder("fallen_drum", c, (0.25, -0.90, 0.28),
                   0.18, 0.46, steel, vertices=20, rotation=(0, math.pi / 2, 0.17))
        return
    # Visible roof cell reads as a sealed mixer, not an exposed explosive heap.
    _box(c, "mixer_maintenance_pedestal", (-0.23, 0.02, 0.27),
         (0.70, 0.63, 0.16), steel)
    g.cylinder("hermetic_mixer", c, (-0.23, 0.02, 0.56),
               0.23 + min(level, 6) * 0.012, 0.48, dark, vertices=24)
    g.cylinder("mixer_seal", c, (-0.23, 0.02, 0.82),
               0.24 + min(level, 6) * 0.012, 0.06, steel, vertices=24)
    _box(c, "blast_screen", (0.19, -0.25, 0.48),
         (0.075, 0.60, 0.55), mat(m, "armor"), 0.018)
    if level >= 4:
        g.cylinder("first_drive", c, (-0.57, 0.02, 0.55),
                   0.17, 0.075, mat(m, "copper"), vertices=18,
                   rotation=(0, math.pi / 2, 0))
    if level >= 5:
        for i, y in enumerate((-0.22, 0.29)):
            g.beam(f"sealed_transfer_pipe_{i}", c, (0.01, y, 0.62),
                   (0.65, y, 0.62), 0.07, steel)
        _box(c, "mechanism_casing", (0.51, 0.05, 0.48),
             (0.35, 0.41, 0.38), dark, 0.035)
    if level >= 8:
        _box(c, "remote_control_console", (0.59, -0.39, 0.61),
             (0.27, 0.18, 0.36), dark, 0.025)
        for x in (0.52, 0.64):
            g.cylinder(f"control_dial_{x}", c, (x, -0.50, 0.66),
                       0.045, 0.022, mat(m, "glass_cyan"), vertices=12,
                       rotation=(math.pi / 2, 0, 0))
    _box(c, "hazard_identification", (-0.26, -0.59, 0.82),
         (0.24, 0.022, 0.055), yellow, 0.006)


def _yard(c, m, level, state):
    steel = mat(m, "steel_light")
    dark = mat(m, "dark_metal")
    yellow = mat(m, "flower_yellow")
    # Fuel and sulfur arrive in closed, separately marked containers.
    for name, x, role in (("fuel", -1.05, "roof_blue"),
                          ("sulfur", 1.05, "flower_yellow")):
        _box(c, f"{name}_foot", (x, 0.75, 0.13),
             (0.46, 0.42, 0.12), mat(m, "concrete"))
        if state == "construction":
            _box(c, f"{name}_unmounted_drum", (x, 0.75, 0.24),
                 (0.31, 0.30, 0.18), mat(m, role))
        elif state == "damaged":
            _box(c, f"{name}_crushed_container", (x, 0.75, 0.21),
                 (0.33, 0.27, 0.15), mat(m, role), rotation=(0, 0, 0.25))
        else:
            g.cylinder(f"{name}_sealed_tank", c, (x, 0.75, 0.34),
                       0.17, 0.36, mat(m, role), vertices=20)
            g.cylinder(f"{name}_closed_lid", c, (x, 0.75, 0.54),
                       0.19, 0.05, dark, vertices=20)
            _box(c, f"{name}_mark", (x, 0.54, 0.37),
                 (0.16, 0.018, 0.055), yellow if name == "fuel" else dark, 0.005)
    # Fabric sits in a lidded receiving box, and output is sealed in small crates.
    _box(c, "fabric_receiving_box", (-1.05, -0.39, 0.22),
         (0.41, 0.38, 0.27), mat(m, "wood_beam"))
    if state == "active":
        _box(c, "fabric_closed_lid", (-1.05, -0.39, 0.39),
             (0.45, 0.41, 0.065), steel)
    elif state == "construction":
        _box(c, "fabric_lid_waiting", (-1.05, -0.80, 0.16),
             (0.41, 0.30, 0.07), steel)
    else:
        _box(c, "fabric_broken_lid", (-1.05, -0.67, 0.17),
             (0.36, 0.28, 0.07), steel, rotation=(0, 0, -0.25))
    for i in range(2 + (level >= 5) + (level >= 8)):
        x = 0.89 + (i % 2) * 0.28
        y = -0.58 - (i // 2) * 0.27
        if state == "construction" and i > 1:
            continue
        if state == "damaged" and i % 2:
            _box(c, f"broken_output_crate_{i}", (x, y, 0.14),
                 (0.22, 0.19, 0.11), mat(m, "wood_dark"), rotation=(0, 0, 0.29))
            continue
        _box(c, f"sealed_output_crate_{i}", (x, y, 0.22),
             (0.24, 0.19, 0.24), mat(m, "wood_dark"), 0.017)
        if state == "active":
            _box(c, f"output_metal_band_{i}", (x, y, 0.26),
                 (0.25, 0.025, 0.047), steel, 0.004)
    if level >= 3:
        _box(c, "brick_fuel_divider", (-0.86, 0.22, 0.34),
             (0.17, 0.70, 0.36), mat(m, "brick_warm"))
    if level >= 5:
        _box(c, "plate_storage_rack", (1.12, 0.17, 0.28),
             (0.29, 0.41, 0.31), steel)
        if state == "active":
            for i in range(3):
                _box(c, f"shield_plate_{i}", (1.00 + i * 0.07, 0.17, 0.51),
                     (0.045, 0.31, 0.24), mat(m, "armor"))
    if level >= 7 and state == "active":
        for x in (-0.45, 0.45):
            _box(c, f"extractor_mount_{x}", (x, 0.43, 0.26),
                 (0.11, 0.11, 0.30), steel)
            g.cylinder(f"extractor_stack_{x}", c, (x, 0.43, 0.53),
                       0.10, 0.42, dark, vertices=18)
    if level >= 9 and state == "active":
        _box(c, "secure_storage_canopy", (1.06, -0.63, 0.65),
             (0.63, 0.65, 0.10), mat(m, "reinforced_concrete"), 0.03)
        for y in (-0.89, -0.35):
            _box(c, f"canopy_post_{y}", (1.30, y, 0.39),
                 (0.08, 0.08, 0.48), steel)


def add_military_factory(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    _shell(collection, mats, level, state)
    _process(collection, mats, level, state)
    _yard(collection, mats, level, state)
