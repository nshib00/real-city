"""Aeolian defensive cannon: twelve upgrades and four physical states."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def add_cannon(c, mats: dict, *, level: int, state: str) -> None:
    """Keep the ground outside this function so every state has one signature."""
    active = state == "active"
    build = state == "construction"
    broken = state == "damaged"
    ruin = state == "ruined"
    wood = mat(mats, "wood_pale")
    darkwood = mat(mats, "wood_beam")
    metal = mat(mats, "dark_metal")
    iron = mat(mats, "metal_worn")
    copper = mat(mats, "copper")
    stone = mat(mats, "stone_block")
    armor = mat(mats, "armor")
    teal = mat(mats, "roof_teal")

    # A low masonry/wood bearing structure stands on the shared grass plane.
    if level >= 3:
        for x in (-0.48, 0.48):
            for y in (-0.48, 0.42):
                g.box(f"stone_foot_{x}_{y}", c, (x, y, 0.16), (0.46, 0.42, 0.18), stone, bevel=0.035)
        if level >= 6:
            for y in (-0.64, 0.62):
                g.box(f"platform_cross_{y}", c, (0, y, 0.24), (1.42, 0.22, 0.18), stone, bevel=0.025)
    else:
        for x in (-0.50, 0.50):
            g.box(f"wood_sleeper_{x}", c, (x, 0, 0.17), (0.22, 1.65, 0.22), darkwood, bevel=0.024)

    # The carriage side rails are interrupted in construction and damaged states.
    for side, x in (("left", -0.42), ("right", 0.42)):
        if build and side == "right":
            continue
        if broken and side == "left":
            g.box("broken_carriage_rail", c, (-0.67, 0.46, 0.17), (0.18, 0.56, 0.16), darkwood, bevel=0.018, rotation=(0, 0, 0.35))
            continue
        if ruin:
            g.box(f"fallen_rail_{side}", c, (x * 1.7, 0.18, 0.17), (0.20, 1.05, 0.16), darkwood, bevel=0.018, rotation=(0, 0, 0.28 if x > 0 else -0.33))
            continue
        for j in range(2 if level >= 5 else 1):
            g.box(f"carriage_{side}_{j}", c, (x + (j * 0.12 if x > 0 else -j * 0.12), 0.04, 0.43 + j * 0.08), (0.19, 1.28, 0.22), wood if level < 9 else armor, bevel=0.032)
        for y in (-0.48, 0.45):
            g.box(f"carriage_bolt_{side}_{y}", c, (x, y, 0.57), (0.23, 0.08, 0.09), iron, bevel=0.012)
        if level <= 2:
            for y in (-0.36, 0.31):
                g.box(f"rope_binding_{side}_{y}", c, (x, y, 0.58), (0.22, 0.065, 0.035), mat(mats, "rope"), bevel=0.009)
    if not ruin:
        g.box("axle", c, (0, 0.13, 0.46), (1.18, 0.15, 0.15), iron, bevel=0.014)

    # Wheels are solid, bevelled hubs with large coloured rims and visible spokes.
    if level >= 2 and not ruin:
        for side, x in (("left", -0.76), ("right", 0.76)):
            if broken and side == "left":
                continue
            if build and side == "right":
                continue
            _wheel(c, mats, f"wheel_{side}", x, 0.14, 0.42, metal_rim=level >= 2)
    if broken or ruin:
        _wheel(c, mats, "fallen_wheel", -1.03, 0.80, 0.27, metal_rim=True, fallen=True)

    # Trunnion and barrel are supported by the carriage. Construction leaves
    # the barrel on a timber trestle; ruins put it on the ground.
    if build:
        for x in (-0.25, 0.25):
            g.beam(f"trestle_leg_{x}", c, (x, -0.75, 0.11), (x, -0.72, 0.43), 0.075, darkwood)
        g.box("trestle_cross", c, (0, -0.72, 0.43), (0.65, 0.12, 0.10), darkwood, bevel=0.012)
        _barrel(c, mats, level, y=-0.72, z=0.59, length_factor=0.7, fallen=False, prefix="unmounted")
        g.box("stacked_planks", c, (0.87, 0.78, 0.18), (0.38, 0.40, 0.20), wood, bevel=0.016)
        g.cylinder("spare_rope", c, (0.90, 0.78, 0.31), 0.11, 0.045, mat(mats, "rope"), vertices=16)
        _state_upgrade_parts(c, mats, level, state)
        return
    if ruin:
        _barrel(c, mats, level, y=-0.30, z=0.29, length_factor=0.85, fallen=True, prefix="fallen")
        _debris(c, mats, level, dense=True)
        _state_upgrade_parts(c, mats, level, state)
        return

    g.cylinder("trunnion", c, (0, 0.09, 0.75), 0.12, 1.05, iron, vertices=16, rotation=(0, math.pi / 2, 0))
    _barrel(c, mats, level, y=-0.24, z=0.83, length_factor=1.0, fallen=False, prefix="mounted")
    if level >= 4 and not broken:
        _shield(c, mats, level)
    if level >= 7 and not broken:
        _gear(c, mats, "aiming_gear", 0.66, 0.48, 0.63)
    if level >= 8 and not broken:
        for x in (-0.72, 0.72):
            g.box(f"recoil_foot_{x}", c, (x, 0.64, 0.20), (0.24, 0.60, 0.19), armor, bevel=0.026)
            g.cylinder(f"recoil_piston_{x}", c, (x, 0.43, 0.42), 0.052, 0.52, copper, vertices=12, rotation=(math.pi / 2, 0, 0))
    if level >= 9 and not broken:
        for x in (-0.84, 0.84):
            g.box(f"turret_side_{x}", c, (x, 0.24, 0.69), (0.12, 0.78, 0.65), armor, bevel=0.030)
            g.box(f"turret_copper_seam_{x}", c, (x, 0.24, 0.83), (0.14, 0.70, 0.045), copper, bevel=0.009)
    if level >= 10 and not broken:
        g.box("sight_housing", c, (0.31, -0.30, 1.03), (0.20, 0.36, 0.17), armor, bevel=0.026)
        g.box("sight_lens", c, (0.31, -0.48, 1.04), (0.13, 0.035, 0.11), teal, bevel=0.015)
    if level >= 11 and not broken:
        for k in range(12):
            a = k * math.tau / 12
            g.box(f"base_ring_{k}", c, (0.86 * math.cos(a), 0.86 * math.sin(a), 0.20), (0.28, 0.20, 0.15), armor, bevel=0.020, rotation=(0, 0, a))
    if level >= 12 and not broken:
        g.box("control_module", c, (0.0, 0.85, 0.56), (0.35, 0.26, 0.22), armor, bevel=0.028)
        for x in (-0.10, 0.10):
            g.sphere(f"control_lamp_{x}", c, (x, 0.69, 0.67), (0.045, 0.035, 0.035), teal, segments=10)
    if broken:
        _debris(c, mats, level, dense=False)
        _state_upgrade_parts(c, mats, level, state)


def _barrel(c, mats, level, *, y, z, length_factor, fallen, prefix):
    metal = mat(mats, "dark_metal")
    copper = mat(mats, "copper")
    light = mat(mats, "metal_worn")
    length = (0.76 + 0.045 * level) * length_factor
    x = 0.29 if fallen else 0.0
    g.cylinder(f"{prefix}_barrel_body", c, (x, y - 0.18, z), 0.17 + 0.005 * level, length, metal, vertices=16, rotation=(math.pi / 2, 0, 0))
    for i, offset in enumerate((-0.35, 0.10, 0.39)):
        yy = y + offset * length
        g.cylinder(f"{prefix}_barrel_band_{i}", c, (x, yy, z), 0.19 + 0.005 * level, 0.055, copper if i == 0 else light, vertices=16, rotation=(math.pi / 2, 0, 0))
    g.cylinder(f"{prefix}_muzzle_ring", c, (x, y - length * 0.68, z), 0.22 + 0.004 * level, 0.075, copper, vertices=16, rotation=(math.pi / 2, 0, 0))
    g.cylinder(f"{prefix}_muzzle_dark", c, (x, y - length * 0.73, z), 0.125, 0.01, mat(mats, "coal"), vertices=16, rotation=(math.pi / 2, 0, 0))
    g.box(f"{prefix}_breech", c, (x, y + length * 0.40, z), (0.40, 0.29, 0.39), light, bevel=0.055)
    if level >= 4:
        g.cylinder(f"{prefix}_breech_lock", c, (x, y + length * 0.60, z), 0.13, 0.10, copper, vertices=12, rotation=(math.pi / 2, 0, 0))
    if level >= 10:
        g.box(f"{prefix}_barrel_cowl", c, (x, y + 0.04, z + 0.20), (0.40, 0.37, 0.08), mat(mats, "armor"), bevel=0.018)


def _wheel(c, mats, prefix, x, y, z, *, metal_rim, fallen=False):
    rot = (0, 0, 0) if fallen else (0, math.pi / 2, 0)
    g.cylinder(f"{prefix}_disc", c, (x, y, z), 0.29, 0.11, mat(mats, "wood_beam"), vertices=16, rotation=rot)
    g.cylinder(f"{prefix}_rim", c, (x + (0.06 if not fallen else 0), y, z), 0.31, 0.055, mat(mats, "metal_worn" if metal_rim else "wood_dark"), vertices=16, rotation=rot)
    g.cylinder(f"{prefix}_hub", c, (x + (0.10 if not fallen else 0), y, z), 0.085, 0.08, mat(mats, "copper"), vertices=12, rotation=rot)
    if not fallen:
        for i in range(8):
            a = i * math.tau / 8
            g.beam(f"{prefix}_spoke_{i}", c, (x + 0.14, y + 0.07 * math.cos(a), z + 0.07 * math.sin(a)), (x + 0.14, y + 0.25 * math.cos(a), z + 0.25 * math.sin(a)), 0.030, mat(mats, "wood_pale"))


def _shield(c, mats, level):
    for x in (-0.38, 0.38):
        g.beam(f"shield_support_{x}", c, (x, 0.31, 0.52), (x, 0.31, 1.02), 0.075, mat(mats, "dark_metal"))
        g.box(f"shield_panel_{x}", c, (x, 0.25, 0.91), (0.62, 0.11, 0.48), mat(mats, "metal_worn" if level < 8 else "armor"), bevel=0.035, rotation=(0, 0.12 if x < 0 else -0.12, 0))
        g.box(f"shield_edge_{x}", c, (x, 0.19, 1.16), (0.64, 0.10, 0.055), mat(mats, "copper"), bevel=0.012)
        for z in (0.76, 1.08):
            g.sphere(f"shield_rivet_{x}_{z}", c, (x, 0.17, z), (0.025, 0.016, 0.025), mat(mats, "copper"), segments=8)


def _gear(c, mats, prefix, x, y, z):
    g.cylinder(f"{prefix}_disc", c, (x, y, z), 0.19, 0.08, mat(mats, "copper"), vertices=16, rotation=(0, math.pi / 2, 0))
    for i in range(10):
        a = i * math.tau / 10
        g.box(f"{prefix}_tooth_{i}", c, (x + 0.05, y + 0.20 * math.cos(a), z + 0.20 * math.sin(a)), (0.08, 0.085, 0.055), mat(mats, "metal_worn"), bevel=0.009, rotation=(a, 0, 0))


def _debris(c, mats, level, *, dense):
    count = 8 if dense else 5
    for i in range(count):
        x = -0.86 + (i % 4) * 0.53
        y = -0.70 + (i // 4) * 1.08
        g.box(f"debris_{i}", c, (x, y, 0.16), (0.22, 0.20, 0.13), mat(mats, "stone_block" if level >= 3 and i % 2 else "wood_beam"), bevel=0.021, rotation=(0, 0, i * 0.39))


def _state_upgrade_parts(c, mats, level, state):
    """Unfinished and fallen upgrade modules retain each level's material story."""
    if level >= 4:
        if state == "construction":
            g.beam("unfinished_shield_post", c, (0.48, 0.33, 0.50), (0.48, 0.33, 1.08), 0.07, mat(mats, "metal_worn"))
        else:
            g.box("collapsed_shield_half", c, (0.84, 0.48, 0.20), (0.48, 0.12, 0.27), mat(mats, "metal_worn"), bevel=0.03, rotation=(0.22, 0.13, -0.35))
    if level >= 5:
        g.box("spare_or_broken_second_rail", c, (-0.91, 0.38, 0.17), (0.14, 0.72, 0.14), mat(mats, "wood_beam"), bevel=0.02, rotation=(0, 0, 0.32))
    if level >= 7:
        _gear(c, mats, "unmounted_or_fallen_drive", -0.81, 0.83, 0.28)
    if level >= 8:
        g.cylinder("recoil_piston_parts", c, (0.82, -0.65, 0.20), 0.06, 0.55, mat(mats, "copper"), vertices=12, rotation=(math.pi / 2, 0, 0))
    if level >= 9:
        g.box("turret_plate_parts", c, (0.99, 0.26, 0.28), (0.13, 0.50, 0.31), mat(mats, "armor"), bevel=0.03, rotation=(0, 0.17, -0.19))
    if level >= 10:
        g.box("sight_parts", c, (-0.80, -0.75, 0.22), (0.21, 0.30, 0.17), mat(mats, "armor"), bevel=0.02)
        g.box("sight_lens_parts", c, (-0.80, -0.92, 0.23), (0.13, 0.025, 0.10), mat(mats, "roof_teal"), bevel=0.01)
    if level >= 11:
        for i in range(4):
            a = i * math.tau / 12
            g.box(f"incomplete_base_ring_{i}", c, (0.86 * math.cos(a), 0.86 * math.sin(a), 0.20), (0.27, 0.20, 0.14), mat(mats, "armor"), bevel=0.02, rotation=(0, 0, a))
    if level >= 12:
        g.box("control_module_parts", c, (0.17, 0.89, 0.23), (0.36, 0.26, 0.20), mat(mats, "armor"), bevel=0.025)
        g.sphere("control_lamp_parts", c, (0.17, 0.74, 0.33), (0.045, 0.025, 0.035), mat(mats, "roof_teal"), segments=10)
