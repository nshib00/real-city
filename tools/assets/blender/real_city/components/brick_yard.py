"""Ten visual stages of the Real City brick yard kiln and drying court."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def _brick_stack(c, stem, x, y, z, count, brick, light):
    for i in range(count):
        row, col = divmod(i, 3)
        g.box(f"{stem}_{i:02d}", c, (x + col * 0.15, y + (row % 2) * 0.10, z + row * 0.09),
              (0.14, 0.23, 0.09), light if i % 4 == 0 else brick, bevel=0.014)


def _kiln(c, mats, level, state):
    brick = mat(mats, "brick_warm")
    brick_light = mat(mats, "brick_light")
    clay = mat(mats, "soil_light")
    stone = mat(mats, "stone_light")
    block = mat(mats, "stone_block")
    iron = mat(mats, "dark_metal")
    steel = mat(mats, "steel_light")
    concrete = mat(mats, "reinforced_concrete")
    soot = mat(mats, "damage_crack")
    x, y = 0.20, 0.27
    width = 1.05 + min(level, 8) * 0.035
    depth = 0.86 + min(level, 8) * 0.025
    full_height = 0.70 + level * 0.055
    base_role = concrete if level >= 8 else block if level >= 3 else stone
    body_role = brick if level >= 4 else clay
    g.box("kiln_foundation", c, (x, y, 0.19), (width + 0.20, depth + 0.17, 0.25), base_role, bevel=0.035)
    if state == "construction":
        height = full_height * 0.50
        g.box("unfinished_kiln_left", c, (x - width * 0.24, y, 0.28 + height / 2), (width * 0.52, depth, height), body_role, bevel=0.035)
        g.box("unfinished_kiln_right", c, (x + width * 0.31, y + depth * 0.17, 0.28 + height * 0.36), (width * 0.30, depth * 0.62, height * 0.72), body_role, bevel=0.028)
        for side in (-1, 1):
            sx = x + side * width * 0.47
            g.beam(f"kiln_scaffold_post_{side}", c, (sx, y - depth * 0.57, 0.10), (sx, y - depth * 0.57, 1.22), 0.065, mat(mats, "wood_beam"))
        g.beam("kiln_scaffold_lintel", c, (x - width * 0.47, y - depth * 0.57, 1.22), (x + width * 0.47, y - depth * 0.57, 1.22), 0.065, mat(mats, "construction_plank"))
        if level >= 5:
            g.box("unmounted_iron_door", c, (-0.40, -1.05, 0.095), (0.35, 0.29, 0.06), iron, bevel=0.018)
        if level >= 8:
            g.box("unmounted_concrete_shield", c, (1.12, 0.52, 0.16), (0.44, 0.30, 0.19), concrete, bevel=0.026)
            g.cylinder("unmounted_feed_gear", c, (1.08, 0.08, 0.115), 0.18, 0.10, steel, vertices=16)
        _brick_stack(c, "unlaid_kiln_bricks", 0.70, -0.84, 0.11, 7 + level // 2, brick, brick_light)
        return
    if state == "damaged":
        height = full_height * 0.43
        g.box("broken_kiln_lower", c, (x, y, 0.28 + height / 2), (width, depth, height), body_role, bevel=0.035)
        g.box("broken_kiln_left_cheek", c, (x - width * 0.36, y, 0.28 + height + full_height * 0.17), (width * 0.27, depth * 0.92, full_height * 0.34), body_role, bevel=0.033)
        g.box("broken_kiln_rear_chunk", c, (x + width * 0.27, y + depth * 0.29, 0.28 + height + full_height * 0.10), (width * 0.30, depth * 0.30, full_height * 0.20), brick_light, bevel=0.026)
        g.box("exposed_firebox", c, (x, y - depth * 0.51, 0.42), (0.54, 0.07, 0.33), soot, bevel=0.012)
        for i in range(7):
            g.box(f"fallen_kiln_brick_{i}", c, (x - 0.69 + (i % 4) * 0.26, -0.68 - (i // 4) * 0.22, 0.12),
                  (0.24, 0.15, 0.11), brick_light if i % 3 == 0 else brick, bevel=0.02,
                  rotation=(0, 0, 0.17 * (i % 3 - 1)))
        if level >= 3:
            g.box("fallen_chimney", c, (0.66, 0.86, 0.155), (0.66, 0.26, 0.18), body_role, bevel=0.025, rotation=(0, 0, 0.32))
        if level >= 5:
            g.box("fallen_iron_door", c, (-0.33, -1.06, 0.10), (0.42, 0.31, 0.07), iron, bevel=0.018, rotation=(0, 0, 0.23))
        if level >= 7:
            g.box("torn_iron_hoop", c, (x + width * 0.49, y, 0.28 + height * 0.54), (0.065, depth * 0.72, 0.075), iron, bevel=0.011)
        if level >= 8:
            g.box("fallen_concrete_guard", c, (1.10, 0.52, 0.165), (0.48, 0.31, 0.20), concrete, bevel=0.026, rotation=(0, 0, -0.20))
            g.cylinder("broken_feed_gear", c, (1.10, -0.19, 0.115), 0.17, 0.10, steel, vertices=16)
        return
    g.box("kiln_firebox_body", c, (x, y, 0.28 + full_height / 2), (width, depth, full_height), body_role, bevel=0.065)
    g.box("kiln_crown", c, (x, y, 0.28 + full_height + 0.09), (width * 0.93, depth * 0.91, 0.18), brick_light if level >= 4 else clay, bevel=0.055)
    front = y - depth * 0.51
    g.box("fire_mouth_shadow", c, (x, front, 0.54), (0.44, 0.064, 0.42), soot, bevel=0.045)
    g.box("fire_mouth_lintel", c, (x, front - 0.04, 0.79), (0.55, 0.10, 0.10), brick if level >= 4 else stone, bevel=0.024)
    for side in (-1, 1):
        g.box(f"fire_mouth_pier_{side}", c, (x + side * 0.24, front - 0.04, 0.53), (0.09, 0.11, 0.40), brick if level >= 4 else clay, bevel=0.017)
    if level >= 3:
        chimney_height = 0.48 + level * 0.08
        cx, cy = x + width * 0.30, y + depth * 0.24
        g.box("kiln_chimney", c, (cx, cy, 0.28 + full_height + 0.18 + chimney_height / 2),
              (0.29, 0.29, chimney_height), brick if level >= 4 else stone, bevel=0.032)
        g.box("chimney_rim", c, (cx, cy, 0.28 + full_height + 0.18 + chimney_height), (0.36, 0.36, 0.10), brick_light, bevel=0.022)
        g.box("chimney_opening", c, (cx, cy, 0.28 + full_height + 0.245 + chimney_height), (0.20, 0.20, 0.018), soot, bevel=0.005)
    if level >= 4:
        g.box("front_heat_guard_sill", c, (x, front - 0.13, 0.135), (0.83, 0.17, 0.14), block, bevel=0.022)
        for row in range(2 + level // 4):
            z = 0.41 + row * 0.21
            for i in range(4):
                g.box(f"kiln_brick_course_{row}_{i}", c,
                      (x - width * 0.37 + i * width * 0.24, front - 0.035, z),
                      (width * 0.21, 0.075, 0.15), brick_light if (row + i) % 3 == 0 else brick, bevel=0.012)
    if level >= 5:
        g.box("iron_firebox_door", c, (x, front - 0.065, 0.53), (0.36, 0.058, 0.34), iron, bevel=0.020)
        g.cylinder("door_hinge", c, (x + 0.13, front - 0.11, 0.54), 0.035, 0.08, steel, vertices=10, rotation=(math.pi / 2, 0, 0))
    if level >= 7:
        for z in (0.43, 0.28 + full_height * 0.73):
            for side in (-1, 1):
                g.box(f"iron_kiln_hoop_{z:.2f}_{side}", c, (x + side * width * 0.51, y, z),
                      (0.055, depth * 0.93, 0.075), iron, bevel=0.010)
    if level >= 8:
        for side in (-1, 1):
            g.box(f"concrete_heat_shield_{side}", c, (x + side * (width * 0.52 + 0.07), y + depth * 0.18, 0.62),
                  (0.15, depth * 0.70, 0.65), concrete, bevel=0.025)
        g.box("extractor_duct", c, (cx + 0.17, cy + 0.23, 0.28 + full_height + 0.26 + chimney_height * 0.61),
              (0.16, 0.38, 0.16), steel, bevel=0.024)


def _drying_area(c, mats, level, state):
    wood = mat(mats, "wood_pale")
    beam = mat(mats, "wood_beam")
    clay = mat(mats, "soil_light")
    brick = mat(mats, "brick_warm")
    broken = state == "damaged"
    count = 1 if level == 1 else 2 if level < 5 else 3
    if state == "construction":
        count = max(1, count - 1)
    if broken:
        count = max(1, count - 1)
    for row in range(count):
        y = 0.75 - row * 0.48
        x = -1.12
        if broken and row == count - 1:
            g.box(f"fallen_drying_plank_{row}", c, (x, y, 0.10), (0.76, 0.27, 0.07), beam, bevel=0.015, rotation=(0, 0, 0.28))
            continue
        for sx in (-0.33, 0.33):
            g.box(f"drying_rack_leg_{row}_{sx}", c, (x + sx, y, 0.35), (0.075, 0.075, 0.57), beam, bevel=0.012)
        g.box(f"drying_rack_top_{row}", c, (x, y, 0.62), (0.78, 0.35, 0.07), wood, bevel=0.018)
        for i in range(4):
            g.box(f"wet_brick_{row}_{i}", c, (x - 0.27 + i * 0.18, y, 0.69), (0.14, 0.22, 0.08), clay if level <= 2 else brick, bevel=0.012)
    if level >= 2 and state == "active":
        for x in (-1.50, -0.73):
            for y in (-0.33, 1.08):
                g.box(f"canopy_post_{x}_{y}", c, (x, y, 0.635), (0.075, 0.075, 1.14), beam, bevel=0.012)
        g.box("drying_canopy", c, (-1.11, 0.38, 1.24), (0.95, 1.58, 0.12),
              mat(mats, "roof_wood_plank") if level < 8 else mat(mats, "roof_stone"), bevel=0.027)
        for x in (-1.42, -0.82):
            g.box(f"canopy_roof_strip_{x}", c, (x, 0.38, 1.32), (0.06, 1.57, 0.034), beam, bevel=0.008)


def _yard_props(c, mats, level, state):
    brick = mat(mats, "brick_warm")
    light = mat(mats, "brick_light")
    wood = mat(mats, "wood_pale")
    iron = mat(mats, "dark_metal")
    steel = mat(mats, "steel_light")
    coal = mat(mats, "coal")
    if state == "construction":
        _brick_stack(c, "building_materials", 0.83, -0.92, 0.11, 5 + level // 2, brick, light)
        if level >= 6:
            g.box("unlaid_cart_rail", c, (1.17, -0.22, 0.10), (0.055, 0.62, 0.07), iron, bevel=0.009)
        return
    if state == "damaged":
        _brick_stack(c, "salvage_bricks", 0.90, -0.91, 0.11, 4, brick, light)
        g.box("broken_storage_pallet", c, (1.05, 0.62, 0.105), (0.78, 0.46, 0.08), wood, bevel=0.018, rotation=(0, 0, -0.22))
        if level >= 6:
            g.box("bent_cart_rail", c, (1.23, -0.72, 0.10), (0.055, 0.55, 0.07), iron, bevel=0.009, rotation=(0, 0, 0.16))
        return
    g.box("finished_brick_pallet", c, (1.08, 0.73, 0.11), (0.83, 0.55, 0.09), wood, bevel=0.017)
    _brick_stack(c, "finished_bricks", 0.80, 0.63, 0.20, min(7 + level, 16), brick, light)
    if level >= 3:
        g.box("coal_bin", c, (-0.95, -0.79, 0.175), (0.58, 0.47, 0.22), wood, bevel=0.025)
        for i in range(5):
            g.box(f"coal_piece_{i}", c, (-1.16 + (i % 3) * 0.16, -0.88 + (i // 3) * 0.13, 0.335),
                  (0.13, 0.11, 0.10), coal, bevel=0.019)
    if level >= 4:
        g.box("cart_bed", c, (0.93, -0.90, 0.34), (0.64, 0.43, 0.14), wood, bevel=0.021)
        for sx in (-0.21, 0.21):
            g.cylinder(f"cart_wheel_{sx}", c, (0.93 + sx, -1.15, 0.195), 0.13, 0.08, iron, vertices=12, rotation=(math.pi / 2, 0, 0))
    if level >= 7:
        for side in (-1, 1):
            g.box(f"fuel_bay_iron_guard_{side}", c, (-0.95 + side * 0.31, -0.79, 0.27),
                  (0.055, 0.51, 0.30), iron, bevel=0.010)
    if level >= 5:
        for side in (-1, 1):
            g.box(f"brick_store_post_{side}", c, (1.10 + side * 0.48, 0.68, 0.605), (0.075, 0.075, 1.08), wood, bevel=0.012)
        g.box("brick_store_roof", c, (1.10, 0.68, 1.13), (1.13, 0.70, 0.10), mat(mats, "roof_wood_plank"), bevel=0.021)
    if level >= 6:
        for x in (0.57, 1.18):
            g.box(f"cart_rail_{x}", c, (x, -0.82, 0.145), (0.055, 0.82, 0.052), steel, bevel=0.009)
        g.box("sorting_table", c, (-0.55, -1.13, 0.58), (0.80, 0.37, 0.09), wood, bevel=0.017)
        for x in (-0.87, -0.23):
            g.box(f"sorting_table_leg_{x}", c, (x, -1.13, 0.3025), (0.075, 0.075, 0.475), iron, bevel=0.013)
    if level >= 8:
        g.cylinder("feed_gear", c, (1.13, -0.27, 0.54), 0.19, 0.10, steel, vertices=16, rotation=(math.pi / 2, 0, 0))
        g.cylinder("feed_hub", c, (1.13, -0.34, 0.54), 0.07, 0.12, mat(mats, "copper"), vertices=12, rotation=(math.pi / 2, 0, 0))
        g.box("conveyor_trough", c, (1.06, -0.20, 0.46), (0.50, 0.77, 0.11), iron, bevel=0.016)
    if level >= 9:
        g.box("sorted_brick_divider", c, (1.10, 0.72, 0.57), (0.07, 0.55, 0.50), mat(mats, "reinforced_concrete"), bevel=0.018)
    if level >= 10:
        g.box("protected_drive_casing", c, (1.10, -0.24, 0.78), (0.57, 0.42, 0.37), mat(mats, "reinforced_concrete"), bevel=0.036)
        g.box("drive_access_panel", c, (1.10, -0.46, 0.78), (0.36, 0.06, 0.22), steel, bevel=0.013)


def add_brick_yard(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    _kiln(collection, mats, level, state)
    _drying_area(collection, mats, level, state)
    _yard_props(collection, mats, level, state)
