"""Compact ten-stage cement milling workshop for one Real City tile."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _box(c, name, xyz, size, material, bevel=0.018, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def _sack(c, name, x, y, z, cloth, seam):
    _box(c, name, (x, y, z), (0.30, 0.21, 0.19), cloth, 0.055)
    _box(c, name + "_neck", (x, y, z + 0.107), (0.15, 0.13, 0.045), seam, 0.015)
    _box(c, name + "_tie", (x, y, z + 0.133), (0.08, 0.13, 0.02), seam, 0.005)


def _intake(c, mats, level, state):
    wood = mat(mats, "wood_beam")
    board = mat(mats, "wood_pale")
    stone = mat(mats, "stone_light")
    clay = mat(mats, "soil_light")
    steel = mat(mats, "steel_light")
    metal = mat(mats, "metal_worn")
    # Two physically separated inputs make the stone/clay recipe legible.
    for i, (y, fill) in enumerate(((0.57, stone), (-0.04, clay))):
        x = -1.12
        _box(c, f"input_{i}_floor", (x, y, 0.105), (0.69, 0.49, 0.11), board if level < 8 else mat(mats, "reinforced_concrete"), 0.02)
        for sx in (-0.32, 0.32):
            _box(c, f"input_{i}_rail_{sx}", (x + sx, y, 0.34), (0.07, 0.50, 0.42), metal if level >= 5 else wood, 0.012)
        _box(c, f"input_{i}_back", (x, y + 0.21, 0.34), (0.69, 0.07, 0.42), metal if level >= 5 else wood, 0.014)
        if state == "active":
            for k in range(3):
                g.sphere(f"input_{i}_lump_{k}", c, (x - 0.18 + k * 0.18, y - 0.02 + (k % 2) * 0.10, 0.23), (0.11, 0.10, 0.08), fill, segments=10, ring_count=6)
        elif state == "damaged":
            _box(c, f"spilled_input_{i}", (x + 0.08, y - 0.36, 0.105), (0.36, 0.15, 0.09), fill, 0.03, (0, 0, 0.2))
    if state == "active" and level >= 2:
        for y in (0.20, 0.83):
            _box(c, f"hopper_plank_{y}", (-1.11, y, 0.66), (0.80, 0.08, 0.11), board if level < 5 else metal)
        for x in (-1.45, -0.78):
            _box(c, f"hopper_post_{x}", (x, 0.51, 0.50), (0.08, 0.78, 0.80), wood if level < 5 else metal)
    if state == "active" and level >= 4:
        _box(c, "feed_chute", (-0.61, 0.24, 0.57), (0.58, 0.28, 0.12), steel, 0.02, (0, -0.16, 0))
        for side in (-1, 1):
            _box(c, f"chute_guard_{side}", (-0.61, 0.24 + side * 0.15, 0.65), (0.59, 0.05, 0.18), metal, 0.01, (0, -0.16, 0))


def _mill(c, mats, level, state):
    stone = mat(mats, "stone_block")
    brick = mat(mats, "brick_warm")
    brick_light = mat(mats, "brick_light")
    steel = mat(mats, "steel_light")
    metal = mat(mats, "dark_metal")
    wood = mat(mats, "wood_beam")
    concrete = mat(mats, "reinforced_concrete")
    material = concrete if level >= 8 else brick if level >= 4 else stone
    x, y = 0.16, 0.23
    # Fixed foundation and support remain present in every state.
    _box(c, "mill_footing", (x, y, 0.145), (1.40, 1.25, 0.19), material, 0.04)
    for side in (-1, 1):
        sx = x + side * 0.49
        _box(c, f"mill_plinth_{side}", (sx, y, 0.38), (0.23, 0.85, 0.34), material, 0.035)
    if state == "construction":
        _box(c, "unfinished_mill_wall", (x + 0.27, y + 0.37, 0.69), (0.61, 0.13, 0.69), material, 0.025)
        _box(c, "unfinished_mill_bearing", (x - 0.51, y, 0.57), (0.16, 0.34, 0.38), metal, 0.02)
        for side in (-1, 1):
            sx = x + side * 0.64
            g.beam(f"work_frame_{side}", c, (sx, y - 0.57, 0.10), (sx, y - 0.57, 1.29), 0.065, wood)
        g.beam("work_frame_top", c, (x - 0.64, y - 0.57, 1.29), (x + 0.64, y - 0.57, 1.29), 0.065, wood)
        g.cylinder("drum_waiting_installation", c, (0.72, -0.92, 0.22), 0.20, 0.41, steel if level >= 5 else stone, vertices=18, rotation=(0, math.pi / 2, 0))
        return
    if state == "damaged":
        _box(c, "broken_mill_rear_wall", (x + 0.09, y + 0.48, 0.55), (0.96, 0.16, 0.67), material, 0.035)
        _box(c, "broken_mill_left_wall", (x - 0.58, y + 0.12, 0.51), (0.16, 0.73, 0.59), material, 0.024)
        g.cylinder("fallen_drum", c, (0.68, -0.59, 0.27), 0.24, 0.58, metal, vertices=20, rotation=(0, math.pi / 2, 0.18))
        for i in range(5):
            _box(c, f"fallen_mill_masonry_{i}", (-0.37 + i * 0.20, -0.78 - (i % 2) * 0.15, 0.115), (0.23, 0.16, 0.11), brick_light if level >= 4 else stone, 0.02, (0, 0, i * 0.15))
        return
    wall_h = 0.73 + min(level, 8) * 0.055
    _box(c, "mill_rear_wall", (x, y + 0.53, 0.26 + wall_h / 2), (1.35, 0.16, wall_h), material, 0.035)
    for side in (-1, 1):
        _box(c, f"mill_side_wall_{side}", (x + side * 0.64, y + 0.08, 0.26 + wall_h / 2), (0.16, 0.95, wall_h), material, 0.03)
    if level >= 4:
        for row in range(2):
            for i in range(5):
                _box(c, f"brick_course_{row}_{i}", (x - 0.51 + i * 0.255, y - 0.56, 0.48 + row * 0.24), (0.22, 0.045, 0.17), brick_light if (i + row) % 3 == 0 else brick, 0.01)
    for side in (-1, 1):
        _box(c, f"drum_bearing_{side}", (x + side * 0.47, y - 0.15, 0.72), (0.13, 0.48, 0.33), metal if level >= 5 else wood)
    drum = steel if level >= 5 else stone
    g.cylinder("milling_drum", c, (x, y - 0.14, 0.77), 0.30, 0.81, drum, vertices=24, rotation=(0, math.pi / 2, 0))
    for side in (-1, 1):
        g.cylinder(f"drum_end_band_{side}", c, (x + side * 0.38, y - 0.14, 0.77), 0.32, 0.055, mat(mats, "copper") if level >= 5 else metal, vertices=24, rotation=(0, math.pi / 2, 0))
        g.cylinder(f"drum_axle_{side}", c, (x + side * 0.52, y - 0.14, 0.77), 0.07, 0.24, metal, vertices=12, rotation=(0, math.pi / 2, 0))
    if level >= 3:
        _box(c, "milling_shroud", (x, y - 0.11, 1.17), (1.13, 0.80, 0.13), metal if level >= 8 else wood, 0.035)
    if level >= 5:
        g.cylinder("drive_wheel", c, (0.76, 0.17, 0.70), 0.23, 0.09, metal, vertices=20, rotation=(math.pi / 2, 0, 0))
        g.cylinder("drive_hub", c, (0.76, 0.11, 0.70), 0.09, 0.12, mat(mats, "copper"), vertices=14, rotation=(math.pi / 2, 0, 0))
        _box(c, "drive_housing", (0.79, 0.38, 0.35), (0.35, 0.39, 0.35), metal, 0.035)
    if level >= 8:
        _box(c, "sealed_mill_roof", (x, y + 0.04, 1.44), (1.49, 1.18, 0.18), concrete, 0.045)
        for side in (-1, 1):
            _box(c, f"roof_steel_rib_{side}", (x + side * 0.52, y + 0.02, 1.55), (0.08, 1.15, 0.09), steel, 0.014)


def _tower_and_output(c, mats, level, state):
    steel = mat(mats, "steel_light")
    metal = mat(mats, "metal_worn")
    concrete = mat(mats, "reinforced_concrete")
    brick = mat(mats, "brick_warm")
    wood = mat(mats, "wood_beam")
    sack = mat(mats, "whitewash")
    seam = mat(mats, "rope")
    active = state == "active"
    if level >= 1:
        _box(c, "output_pallet", (1.13, -0.62, 0.115), (0.69, 0.63, 0.10), wood if level < 8 else metal)
        count = min(1 + level // 2, 5) if active else 1 if state == "construction" else 2
        for i in range(count):
            _sack(c, f"cement_sack_{i}", 0.92 + (i % 2) * 0.30, -0.80 + (i // 2) * 0.23, 0.26, sack, seam)
    if level < 4:
        return
    # The stack starts at the kiln/mill roof; ruined versions instead lie on the floor.
    _box(c, "fuel_box", (-0.92, -0.94, 0.19), (0.48, 0.34, 0.26), wood)
    if active:
        for i in range(3):
            _box(c, f"coal_piece_{i}", (-1.07 + 0.15 * i, -0.94, 0.37), (0.13, 0.10, 0.10), mat(mats, "coal"))
    if state == "construction":
        g.cylinder("uninstalled_chimney_pipe", c, (-0.65, -0.94, 0.14), 0.11, 0.45, metal, vertices=14, rotation=(0, math.pi / 2, 0))
        if level >= 6:
            for sx in (-0.19, 0.19):
                _box(c, f"silo_frame_leg_{sx}", (1.10 + sx, 0.70, 0.43), (0.07, 0.07, 0.67), metal)
            g.cylinder("half_assembled_silo", c, (1.10, 0.70, 0.88), 0.27, 0.24, steel if level < 8 else concrete, vertices=20)
        if level >= 8:
            _box(c, "unmounted_concrete_panel", (0.93, -0.28, 0.19), (0.44, 0.16, 0.16), concrete)
        if level >= 9:
            for sx in (-0.19, 0.19):
                _box(c, f"second_silo_frame_leg_{sx}", (0.56 + sx, 1.06, 0.35), (0.07, 0.07, 0.51), metal)
        if level >= 10:
            g.cylinder("uninstalled_drive_dial", c, (0.69, -0.92, 0.13), 0.13, 0.06, mat(mats, "copper"), vertices=16)
        return
    if state == "damaged":
        g.cylinder("fallen_chimney_section", c, (-0.62, -0.70, 0.17), 0.14, 0.59, brick if level < 8 else steel, vertices=16, rotation=(0, math.pi / 2, 0.16))
        if level >= 6:
            g.cylinder("ruptured_silo", c, (1.04, 0.73, 0.32), 0.26, 0.46, concrete if level >= 8 else steel, vertices=18, rotation=(0, math.pi / 2, 0.2))
        if level >= 8:
            _box(c, "collapsed_concrete_casing", (0.60, 0.39, 0.18), (0.55, 0.27, 0.20), concrete, 0.028, (0, 0, -0.22))
        if level >= 9:
            g.cylinder("second_ruptured_silo", c, (0.55, 1.03, 0.29), 0.25, 0.36, concrete, vertices=18, rotation=(0, math.pi / 2, -0.17))
        if level >= 10:
            _box(c, "wrecked_precision_drive", (0.84, 0.37, 0.22), (0.37, 0.31, 0.23), metal, 0.027, (0, 0, 0.26))
        return
    g.cylinder("exhaust_stack", c, (-0.34, 0.69, 1.38 + level * 0.055), 0.13, 0.60 + level * 0.11, brick if level < 8 else steel, vertices=16)
    g.cylinder("exhaust_rim", c, (-0.34, 0.69, 1.73 + level * 0.11), 0.17, 0.09, steel, vertices=16)
    if level >= 5:
        g.cylinder("dust_filter", c, (0.41, 0.86, 1.22), 0.18, 0.53, metal, vertices=16)
        for z in (1.03, 1.41):
            g.cylinder(f"filter_collar_{z}", c, (0.41, 0.86, z), 0.22, 0.08, steel, vertices=16)
    if level >= 6:
        n = 2 if level >= 9 else 1
        for i in range(n):
            x = 1.10 if i == 0 else 0.56
            y = 0.70 if i == 0 else 1.06
            for sx in (-0.19, 0.19):
                _box(c, f"silo_{i}_leg_{sx}", (x + sx, y, 0.44), (0.07, 0.07, 0.70), metal)
            height = 0.74 + (level - 6) * 0.07
            g.cylinder(f"silo_{i}_body", c, (x, y, 0.84 + height / 2), 0.27, height, concrete if level >= 8 else steel, vertices=20)
            g.cone(f"silo_{i}_cone", c, (x, y, 0.68), 0.27, 0.085, 0.23, steel, vertices=20)
            g.cylinder(f"silo_{i}_lid", c, (x, y, 0.88 + height), 0.30, 0.08, metal, vertices=20)
    if level >= 7:
        _box(c, "feed_pipe", (0.73, 0.67, 1.21), (0.70, 0.12, 0.12), metal)
        _box(c, "loading_ramp", (1.16, -0.29, 0.33), (0.53, 0.54, 0.12), steel, 0.014, (0.12, 0, 0))
    if level >= 9:
        _box(c, "operator_post", (-0.99, -0.91, 0.47), (0.53, 0.41, 0.69), concrete, 0.035)
        _box(c, "operator_glass", (-0.99, -1.125, 0.60), (0.40, 0.03, 0.23), mat(mats, "glass_cyan"), 0.008)
    if level >= 10:
        _box(c, "precision_drive_case", (0.68, 0.50, 1.11), (0.52, 0.40, 0.36), metal, 0.045)
        g.cylinder("precision_drive_dial", c, (0.69, 0.27, 1.14), 0.12, 0.06, mat(mats, "copper"), vertices=16, rotation=(math.pi / 2, 0, 0))


def add_cement_workshop(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    _intake(collection, mats, level, state)
    _mill(collection, mats, level, state)
    _tower_and_output(collection, mats, level, state)
