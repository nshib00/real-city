"""Thirty modular decorations for the Aeolian villa.

``loc`` is a ground/roof contact point for standing details, and the centre of
the attachment for wall details. The main facade faces negative Y. All sizes
use the same scene units as the existing housing component library.
"""

from __future__ import annotations

import math

from .. import geometry
from .common import mat


def add_portico_fluted_column(name, collection, mats, loc, *, height=0.82):
    x, y, z = loc
    stone = mat(mats, "marble_white", "whitewash")
    vein = mat(mats, "marble_vein", "stone_light")
    gold = mat(mats, "gilded_gold", "roof_gold")
    geometry.box(f"{name}_plinth", collection, (x, y, z + 0.065), (0.32, 0.32, 0.13), stone, bevel=0.025)
    geometry.cylinder(f"{name}_lower_torus", collection, (x, y, z + 0.15), 0.14, 0.055, stone, vertices=20)
    geometry.cylinder(f"{name}_shaft", collection, (x, y, z + 0.16 + height / 2), 0.11, height, stone, vertices=20)
    for i in range(12):
        a = i * math.tau / 12
        geometry.beam(f"{name}_flute_{i}", collection,
                      (x + 0.108 * math.cos(a), y + 0.108 * math.sin(a), z + 0.19),
                      (x + 0.108 * math.cos(a), y + 0.108 * math.sin(a), z + 0.10 + height),
                      0.010, vein)
    for dz, radius in ((0.19, 0.121), (height + 0.09, 0.125)):
        geometry.cylinder(f"{name}_gilded_collar_{dz:.2f}", collection,
                          (x, y, z + dz), radius, 0.027, gold, vertices=20)
    for i in range(8):
        a = i * math.tau / 8
        geometry.sphere(f"{name}_capital_leaf_{i}", collection,
                        (x + 0.124 * math.cos(a), y + 0.124 * math.sin(a), z + height + 0.155),
                        (0.045, 0.027, 0.073), stone, segments=8, ring_count=4)
        geometry.sphere(f"{name}_capital_bead_{i}", collection,
                        (x + 0.155 * math.cos(a), y + 0.155 * math.sin(a), z + height + 0.222),
                        (0.018, 0.018, 0.018), gold, segments=6, ring_count=4)
    geometry.box(f"{name}_capital", collection, (x, y, z + 0.20 + height),
                 (0.35, 0.35, 0.09), stone, bevel=0.025)


def add_windleaf_pilaster(name, collection, mats, loc, *, height=0.72):
    x, y, z = loc
    geometry.box(f"{name}_shaft", collection, (x, y, z + height / 2), (0.15, 0.085, height), mat(mats, "whitewash", "stone_light"), bevel=0.012)
    geometry.box(f"{name}_foot", collection, (x, y - 0.015, z + 0.045), (0.22, 0.12, 0.09), mat(mats, "stone_block"), bevel=0.009)
    geometry.box(f"{name}_cap", collection, (x, y - 0.015, z + height - 0.04), (0.22, 0.12, 0.09), mat(mats, "stone_block"), bevel=0.009)
    geometry.sphere(f"{name}_leaf", collection, (x, y - 0.065, z + height * 0.67), (0.04, 0.012, 0.08), mat(mats, "roof_leaf"), segments=10)


def add_ceremonial_stair(name, collection, mats, loc, *, width=0.64):
    x, y, z = loc
    for i in range(3):
        geometry.box(f"{name}_step_{i}", collection,
                     (x, y + i * 0.11, z + (i + 1) * 0.035),
                     (width - i * 0.065, 0.24, (i + 1) * 0.07), mat(mats, "stone_block", "stone_light"), bevel=0.012)


def add_transom_sunburst(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_frame", collection, loc, (0.40, 0.07, 0.19), mat(mats, "stone_block"), bevel=0.015)
    geometry.box(f"{name}_glass", collection, (x, y - 0.042, z), (0.33, 0.025, 0.12), mat(mats, "glass_cyan"), bevel=0.009)
    for i in range(5):
        dx = (i - 2) * 0.065
        geometry.beam(f"{name}_ray_{i}", collection, (x, y - 0.063, z - 0.055),
                      (x + dx, y - 0.063, z + 0.052), 0.012, mat(mats, "copper", "roof_gold"))


def add_door_wind_medallion(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_disc", collection, loc, 0.095, 0.026, mat(mats, "copper", "roof_gold"), vertices=12, rotation=(math.pi / 2, 0, 0))
    for i in range(4):
        a = i * math.pi / 2
        geometry.sphere(f"{name}_petal_{i}", collection,
                        (x + 0.046 * math.cos(a), y - 0.018, z + 0.046 * math.sin(a)),
                        (0.030, 0.013, 0.018), mat(mats, "roof_gold", "copper"),
                        segments=6, ring_count=4)


def add_facade_cornice(name, collection, mats, loc, *, width=0.85):
    x, y, z = loc
    for i, (depth, height) in enumerate(((0.13, 0.065), (0.18, 0.052), (0.12, 0.036))):
        geometry.box(f"{name}_course_{i}", collection, (x, y - depth * 0.19, z + i * 0.045),
                     (width, depth, height), mat(mats, "stone_block" if i != 1 else "whitewash"), bevel=0.008)


def add_arch_window_crown(name, collection, mats, loc, *, width=0.46):
    x, y, z = loc
    stone = mat(mats, "stone_block", "stone_light")
    for i in range(5):
        dx = (i - 2) * width / 5
        geometry.box(f"{name}_voussoir_{i}", collection,
                     (x + dx, y, z - abs(dx) * 0.28), (width / 5 + 0.008, 0.085, 0.075),
                     stone, bevel=0.006, rotation=(0, 0, -dx * 0.32))
    geometry.box(f"{name}_key", collection, (x, y - 0.014, z + 0.035), (0.065, 0.105, 0.12), mat(mats, "whitewash"), bevel=0.008)


def add_glass_shutter_pair(name, collection, mats, loc, *, opening_width=0.38, height=0.42):
    x, y, z = loc
    for side in (-1, 1):
        px = x + side * (opening_width / 2 + 0.075)
        geometry.box(f"{name}_shutter_{side}", collection, (px, y, z), (0.13, 0.055, height), mat(mats, "roof_teal", "roof_green"), bevel=0.010)
        geometry.box(f"{name}_slat_{side}", collection, (px, y - 0.032, z), (0.095, 0.018, 0.035), mat(mats, "whitewash"), bevel=0.004)


def add_copper_gutter_spout(name, collection, mats, loc, *, drop=0.36):
    x, y, z = loc
    metal = mat(mats, "copper", "metal_worn")
    geometry.box(f"{name}_socket", collection, loc, (0.12, 0.13, 0.07), metal, bevel=0.008)
    geometry.beam(f"{name}_pipe", collection, (x, y, z - 0.025), (x, y, z - drop), 0.041, metal)
    geometry.box(f"{name}_outlet", collection, (x, y - 0.07, z - drop), (0.09, 0.16, 0.045), metal, bevel=0.007)


def add_balcony_flower_box(name, collection, mats, loc, *, width=0.50):
    x, y, z = loc
    geometry.box(f"{name}_box", collection, (x, y, z + 0.06), (width, 0.17, 0.12), mat(mats, "stone_block"), bevel=0.012)
    geometry.box(f"{name}_soil", collection, (x, y, z + 0.125), (width * 0.88, 0.12, 0.014), mat(mats, "soil"), bevel=0.002)
    for i in range(5):
        px = x + (i - 2) * width * 0.17
        geometry.sphere(f"{name}_leaf_{i}", collection, (px, y, z + 0.17), (0.055, 0.052, 0.055), mat(mats, "roof_leaf"), segments=6, ring_count=4)
        geometry.sphere(f"{name}_bloom_{i}", collection, (px, y - 0.025, z + 0.19), (0.027, 0.027, 0.022), mat(mats, "flower_lilac" if i % 2 else "flower_white"), segments=6, ring_count=4)


def add_roof_scallop_tile(name, collection, mats, loc, *, width=0.17):
    x, y, z = loc
    geometry.box(f"{name}_tile", collection, (x, y, z + 0.014), (width, 0.25, 0.03), mat(mats, "roof_gold", "roof_coral"), bevel=0.014)
    geometry.cylinder(f"{name}_lip", collection, (x, y - 0.105, z + 0.024), width * 0.47, 0.018,
                      mat(mats, "roof_coral", "roof_gold"), vertices=12)


def add_ridge_leaf_crest(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_socket", collection, (x, y, z + 0.025), (0.16, 0.14, 0.05), mat(mats, "roof_coral", "roof_gold"), bevel=0.009)
    geometry.beam(f"{name}_stem", collection, (x, y, z + 0.05), (x, y, z + 0.26), 0.029, mat(mats, "copper"))
    for side in (-1, 1):
        geometry.sphere(f"{name}_leaf_{side}", collection, (x + side * 0.06, y, z + 0.18), (0.095, 0.022, 0.043), mat(mats, "roof_green"), segments=10)


def add_dormer_copper_cap(name, collection, mats, loc, *, width=0.48):
    x, y, z = loc
    geometry.box(f"{name}_cap", collection, (x, y, z + 0.027), (width, 0.22, 0.055), mat(mats, "roof_coral", "roof_gold"), bevel=0.014)
    for side in (-1, 1):
        geometry.box(f"{name}_tip_{side}", collection, (x + side * width * 0.45, y - 0.012, z + 0.057),
                     (0.06, 0.19, 0.055), mat(mats, "copper"), bevel=0.008)


def add_chimney_louver_crown(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_base", collection, (x, y, z + 0.035), (0.25, 0.22, 0.07), mat(mats, "stone_block"), bevel=0.009)
    for side in (-1, 1):
        geometry.box(f"{name}_louver_{side}", collection, (x + side * 0.07, y - 0.01, z + 0.13), (0.045, 0.18, 0.13), mat(mats, "copper"), bevel=0.006)
    geometry.box(f"{name}_hood", collection, (x, y, z + 0.215), (0.31, 0.27, 0.055), mat(mats, "roof_coral", "roof_gold"), bevel=0.011)


def add_eave_wind_chime(name, collection, mats, loc, *, drop=0.30):
    x, y, z = loc
    geometry.box(f"{name}_hook", collection, loc, (0.12, 0.09, 0.04), mat(mats, "copper"), bevel=0.005)
    for i, dx in enumerate((-0.055, 0, 0.055)):
        geometry.beam(f"{name}_cord_{i}", collection, (x + dx, y, z), (x + dx, y, z - drop + i * 0.045), 0.011, mat(mats, "rope"))
        geometry.cylinder(f"{name}_bell_{i}", collection, (x + dx, y, z - drop + i * 0.045), 0.021, 0.06, mat(mats, "copper"), vertices=8)


def add_terrace_balustrade(name, collection, mats, loc, *, length=0.70):
    x, y, z = loc
    stone = mat(mats, "stone_block", "whitewash")
    geometry.box(f"{name}_sill", collection, (x, y, z + 0.045), (length, 0.13, 0.09), stone, bevel=0.010)
    for i in range(5):
        geometry.cylinder(f"{name}_baluster_{i}", collection,
                          (x + (i - 2) * length * 0.20, y, z + 0.24), 0.032, 0.32, mat(mats, "whitewash"), vertices=8)
    geometry.box(f"{name}_rail", collection, (x, y, z + 0.42), (length, 0.15, 0.065), stone, bevel=0.010)


def add_terrace_sun_table(name, collection, mats, loc):
    x, y, z = loc
    wood = mat(mats, "elite_plank", "wood_beam")
    geometry.cylinder(f"{name}_foot", collection, (x, y, z + 0.035), 0.115, 0.07, wood, vertices=10)
    geometry.cylinder(f"{name}_post", collection, (x, y, z + 0.23), 0.027, 0.34, mat(mats, "copper"), vertices=8)
    geometry.cylinder(f"{name}_top", collection, (x, y, z + 0.42), 0.19, 0.055, wood, vertices=12)
    geometry.cylinder(f"{name}_inlay", collection, (x, y, z + 0.452), 0.055, 0.006, mat(mats, "roof_gold"), vertices=12)


def add_curved_lounge_chair(name, collection, mats, loc):
    x, y, z = loc
    wood = mat(mats, "elite_plank", "wood_beam")
    for side in (-1, 1):
        geometry.beam(f"{name}_leg_{side}", collection, (x + side * 0.12, y, z + 0.02), (x + side * 0.12, y, z + 0.30), 0.032, wood)
    geometry.box(f"{name}_seat", collection, (x, y, z + 0.31), (0.33, 0.28, 0.055), mat(mats, "whitewash"), bevel=0.012)
    geometry.box(f"{name}_back", collection, (x, y + 0.12, z + 0.48), (0.33, 0.05, 0.34), wood, bevel=0.012, rotation=(0.20, 0, 0))


def add_awning_tieback(name, collection, mats, loc, *, drop=0.32):
    x, y, z = loc
    geometry.box(f"{name}_hook", collection, loc, (0.075, 0.07, 0.075), mat(mats, "copper"), bevel=0.007)
    geometry.beam(f"{name}_cord", collection, (x, y, z - 0.03), (x, y, z - drop), 0.018, mat(mats, "rope"))
    geometry.sphere(f"{name}_tassel", collection, (x, y, z - drop - 0.035), (0.032, 0.032, 0.065), mat(mats, "roof_coral", "roof_gold"), segments=8)


def add_balcony_copper_rail(name, collection, mats, loc, *, length=0.65):
    x, y, z = loc
    for side in (-1, 1):
        geometry.box(f"{name}_pier_{side}", collection, (x + side * length / 2, y, z + 0.20), (0.09, 0.10, 0.40), mat(mats, "stone_block"), bevel=0.008)
    for i in range(5):
        geometry.beam(f"{name}_bar_{i}", collection, (x + (i - 2) * length * 0.17, y, z + 0.08),
                      (x + (i - 2) * length * 0.17, y, z + 0.40), 0.019, mat(mats, "copper"))
    geometry.box(f"{name}_handrail", collection, (x, y, z + 0.42), (length + 0.08, 0.07, 0.045), mat(mats, "copper"), bevel=0.006)


def add_topiary_spiral(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_pot", collection, (x, y, z + 0.09), 0.13, 0.18, mat(mats, "stone_block"), vertices=10)
    geometry.beam(f"{name}_stem", collection, (x, y, z + 0.17), (x, y, z + 0.59), 0.035, mat(mats, "wood_beam"))
    for i in range(3):
        geometry.sphere(f"{name}_crown_{i}", collection, (x + (i - 1) * 0.055, y, z + 0.32 + i * 0.13),
                        (0.14 - i * 0.016, 0.13 - i * 0.012, 0.09), mat(mats, "roof_leaf" if i % 2 else "roof_green"), segments=10)


def add_arc_flower_bed(name, collection, mats, loc):
    x, y, z = loc
    for i in range(7):
        a = math.pi * i / 6
        px, py = x + 0.24 * math.cos(a), y - 0.18 * math.sin(a)
        geometry.box(f"{name}_curb_{i}", collection, (px, py, z + 0.035), (0.10, 0.085, 0.07), mat(mats, "stone_block"), bevel=0.008, rotation=(0, 0, a))
        geometry.sphere(f"{name}_flower_{i}", collection, (px * 0.72 + x * 0.28, py + 0.055, z + 0.12),
                        (0.045, 0.045, 0.05), mat(mats, "flower_red" if i % 2 else "flower_yellow"), segments=6, ring_count=4)


def add_orchard_sapling(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_soil", collection, (x, y, z + 0.014), 0.16, 0.028, mat(mats, "soil"), vertices=10)
    geometry.beam(f"{name}_trunk", collection, (x, y, z + 0.02), (x, y, z + 0.52), 0.042, mat(mats, "wood_beam"))
    for side in (-1, 1):
        geometry.sphere(f"{name}_crown_{side}", collection, (x + side * 0.10, y, z + 0.48), (0.17, 0.16, 0.15), mat(mats, "roof_leaf"), segments=10)
        geometry.sphere(f"{name}_fruit_{side}", collection, (x + side * 0.17, y - 0.08, z + 0.42), (0.031, 0.031, 0.031), mat(mats, "roof_coral"), segments=8)


def add_garden_lattice(name, collection, mats, loc, *, width=0.48):
    x, y, z = loc
    wood = mat(mats, "elite_plank", "wood_beam")
    for side in (-1, 1):
        geometry.beam(f"{name}_post_{side}", collection, (x + side * width / 2, y, z), (x + side * width / 2, y, z + 0.64), 0.04, wood)
    for i in range(4):
        geometry.beam(f"{name}_cross_{i}", collection, (x - width / 2, y, z + 0.10 + i * 0.15),
                      (x + width / 2, y, z + 0.10 + i * 0.15), 0.024, wood)
    geometry.sphere(f"{name}_vine", collection, (x, y, z + 0.52), (width * 0.42, 0.065, 0.10), mat(mats, "roof_leaf"), segments=10)


def add_villa_gate_post(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_base", collection, (x, y, z + 0.055), (0.20, 0.20, 0.11), mat(mats, "stone_block"), bevel=0.012)
    geometry.box(f"{name}_pier", collection, (x, y, z + 0.31), (0.15, 0.15, 0.48), mat(mats, "whitewash"), bevel=0.010)
    geometry.box(f"{name}_cap", collection, (x, y, z + 0.57), (0.23, 0.23, 0.07), mat(mats, "stone_block"), bevel=0.011)
    geometry.sphere(f"{name}_finial", collection, (x, y, z + 0.64), (0.06, 0.06, 0.06), mat(mats, "roof_gold"), segments=10)


def add_petal_paving(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_centre", collection, (x, y, z + 0.013), 0.06, 0.026, mat(mats, "roof_gold"), vertices=10)
    for i in range(6):
        a = i * math.tau / 6
        geometry.sphere(f"{name}_petal_{i}", collection,
                        (x + 0.12 * math.cos(a), y + 0.12 * math.sin(a), z + 0.013),
                        (0.09, 0.045, 0.026), mat(mats, "stone_block"), segments=8)


def add_wind_basin(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_foot", collection, (x, y, z + 0.035), 0.18, 0.07, mat(mats, "stone_block"), vertices=12)
    geometry.cylinder(f"{name}_bowl", collection, (x, y, z + 0.11), 0.25, 0.09, mat(mats, "stone_light"), vertices=16)
    geometry.cylinder(f"{name}_water", collection, (x, y, z + 0.16), 0.20, 0.008, mat(mats, "glass_cyan"), vertices=16)
    geometry.sphere(f"{name}_island", collection, (x, y, z + 0.18), (0.045, 0.045, 0.023), mat(mats, "whitewash"), segments=8)


def add_fountain_spout(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_plinth", collection, (x, y, z + 0.08), (0.17, 0.16, 0.16), mat(mats, "stone_block"), bevel=0.012)
    geometry.cylinder(f"{name}_spout", collection, (x, y - 0.055, z + 0.19), 0.037, 0.14, mat(mats, "copper"), vertices=10, rotation=(math.pi / 2, 0, 0))
    geometry.sphere(f"{name}_drop", collection, (x, y - 0.14, z + 0.16), (0.026, 0.026, 0.045), mat(mats, "glass_cyan"), segments=8)


def add_pool_mosaic_edge(name, collection, mats, loc, *, length=0.60):
    x, y, z = loc
    geometry.box(f"{name}_bed", collection, (x, y, z + 0.034), (length, 0.15, 0.068), mat(mats, "stone_block"), bevel=0.010)
    for i in range(6):
        geometry.box(f"{name}_inlay_{i}", collection, (x + (i - 2.5) * length / 6, y - 0.012, z + 0.072),
                     (length / 6 - 0.012, 0.065, 0.007), mat(mats, "glass_cyan" if i % 2 else "roof_teal"), bevel=0.001)


def add_courtyard_lantern(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_foot", collection, (x, y, z + 0.035), (0.15, 0.15, 0.07), mat(mats, "stone_block"), bevel=0.008)
    geometry.beam(f"{name}_post", collection, (x, y, z + 0.07), (x, y, z + 0.45), 0.035, mat(mats, "copper"))
    geometry.box(f"{name}_glass", collection, (x, y, z + 0.54), (0.13, 0.13, 0.17), mat(mats, "window_warm"), bevel=0.012)
    geometry.box(f"{name}_hood", collection, (x, y, z + 0.65), (0.19, 0.19, 0.055), mat(mats, "roof_coral"), bevel=0.009)


def add_marble_wall_inlay(name, collection, mats, loc, *, width=0.45, height=0.65, side=False):
    """Light polished wall slab crossed by restrained grey marble veins."""
    x, y, z = loc
    geometry.box(f"{name}_slab", collection, loc,
                 (0.025, width, height) if side else (width, 0.025, height),
                 mat(mats, "marble_ivory", "whitewash"), bevel=0.009)
    vein = mat(mats, "marble_vein", "stone_light")
    for index, (a, b) in enumerate((((-.38, -.39), (-.12, -.06)),
                                     ((-.12, -.06), (.15, .18)),
                                     ((.15, .18), (.30, .42)))):
        start = (x + 0.018, y + a[0] * width, z + a[1] * height) if side else (x + a[0] * width, y - 0.018, z + a[1] * height)
        end = (x + 0.018, y + b[0] * width, z + b[1] * height) if side else (x + b[0] * width, y - 0.018, z + b[1] * height)
        geometry.beam(f"{name}_vein_{index}", collection, start, end, 0.006, vein)


def add_gilded_window_surround(name, collection, mats, loc, *, width, height, side=False):
    """Raised white marble architrave, gold glazing line and carved keystone."""
    x, y, z = loc
    marble = mat(mats, "marble_white", "whitewash")
    gold = mat(mats, "gilded_gold", "roof_gold")
    for sign in (-1, 1):
        if side:
            geometry.box(f"{name}_jamb_{sign}", collection,
                         (x, y + sign * (width / 2 + 0.055), z),
                         (0.055, 0.075, height + 0.15), marble, bevel=0.010)
            geometry.box(f"{name}_gold_edge_{sign}", collection,
                         (x + 0.035, y + sign * (width / 2 + 0.014), z),
                         (0.014, 0.014, height), gold, bevel=0.003)
        else:
            geometry.box(f"{name}_jamb_{sign}", collection,
                         (x + sign * (width / 2 + 0.055), y, z),
                         (0.075, 0.055, height + 0.15), marble, bevel=0.010)
            geometry.box(f"{name}_gold_edge_{sign}", collection,
                         (x + sign * (width / 2 + 0.014), y - 0.035, z),
                         (0.014, 0.014, height), gold, bevel=0.003)
    if side:
        for sign in (-1, 1):
            geometry.box(f"{name}_horizontal_{sign}", collection,
                         (x, y, z + sign * (height / 2 + 0.058)),
                         (0.07, width + 0.20, 0.085), marble, bevel=0.010)
        geometry.sphere(f"{name}_keystone", collection,
                        (x + 0.052, y, z + height / 2 + 0.095),
                        (0.024, 0.055, 0.042), gold, segments=8)
    else:
        for sign in (-1, 1):
            geometry.box(f"{name}_horizontal_{sign}", collection,
                         (x, y, z + sign * (height / 2 + 0.058)),
                         (width + 0.20, 0.07, 0.085), marble, bevel=0.010)
        geometry.sphere(f"{name}_keystone", collection,
                        (x, y - 0.055, z + height / 2 + 0.095),
                        (0.055, 0.024, 0.042), gold, segments=8)


def add_gilded_entry_portal(name, collection, mats, loc, *, width=0.59, height=0.90):
    x, y, z = loc
    marble = mat(mats, "marble_white", "whitewash")
    gold = mat(mats, "gilded_gold", "roof_gold")
    for sign in (-1, 1):
        px = x + sign * (width / 2 + 0.065)
        geometry.box(f"{name}_marble_jamb_{sign}", collection, (px, y, z),
                     (0.10, 0.10, height + 0.18), marble, bevel=0.014)
        geometry.box(f"{name}_gilt_jamb_{sign}", collection,
                     (x + sign * (width / 2 + 0.01), y - 0.06, z),
                     (0.018, 0.025, height), gold, bevel=0.003)
        geometry.sphere(f"{name}_leaf_{sign}", collection,
                        (px, y - 0.067, z + height / 2 - 0.04),
                        (0.045, 0.017, 0.10), gold, segments=10)
    geometry.box(f"{name}_marble_lintel", collection,
                 (x, y, z + height / 2 + 0.11),
                 (width + 0.30, 0.14, 0.13), marble, bevel=0.016)
    geometry.box(f"{name}_gold_lintel", collection,
                 (x, y - 0.081, z + height / 2 + 0.14),
                 (width + 0.15, 0.020, 0.022), gold, bevel=0.004)
    geometry.sphere(f"{name}_sun_gem", collection,
                    (x, y - 0.095, z + height / 2 + 0.14),
                    (0.055, 0.020, 0.055), mat(mats, "glass_cyan"), segments=12)


def add_gilded_urn(name, collection, mats, loc):
    x, y, z = loc
    marble = mat(mats, "marble_white", "whitewash")
    gold = mat(mats, "gilded_gold", "roof_gold")
    geometry.box(f"{name}_foot", collection, (x, y, z + 0.038),
                 (0.24, 0.24, 0.075), marble, bevel=0.015)
    geometry.cylinder(f"{name}_bowl", collection, (x, y, z + 0.20),
                      0.105, 0.25, marble, vertices=16)
    geometry.cylinder(f"{name}_gold_rim", collection, (x, y, z + 0.33),
                      0.13, 0.035, gold, vertices=16)
    for index in range(5):
        a = index * math.tau / 5
        geometry.sphere(f"{name}_leaf_{index}", collection,
                        (x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), z + 0.39),
                        (0.055, 0.055, 0.085), mat(mats, "roof_leaf"), segments=6, ring_count=4)
        geometry.sphere(f"{name}_flower_{index}", collection,
                        (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), z + 0.46),
                        (0.030, 0.030, 0.028),
                        mat(mats, "flower_lilac" if index % 2 else "flower_white"), segments=6, ring_count=4)


def add_courtyard_sun_mosaic(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_marble_disc", collection, (x, y, z + 0.008),
                      0.27, 0.025, mat(mats, "marble_white", "whitewash"), vertices=16)
    geometry.cylinder(f"{name}_gold_centre", collection, (x, y, z + 0.023),
                      0.065, 0.008, mat(mats, "gilded_gold", "roof_gold"), vertices=12)
    for index in range(8):
        a = index * math.tau / 8
        geometry.box(f"{name}_ray_{index}", collection,
                     (x + 0.16 * math.cos(a), y + 0.16 * math.sin(a), z + 0.023),
                     (0.13, 0.026, 0.007), mat(mats, "gilded_gold", "roof_gold"),
                     bevel=0.002, rotation=(0, 0, a))


def add_garden_sun_obelisk(name, collection, mats, loc):
    x, y, z = loc
    marble = mat(mats, "marble_white", "whitewash")
    geometry.box(f"{name}_plinth", collection, (x, y, z + 0.055),
                 (0.25, 0.25, 0.11), marble, bevel=0.018)
    geometry.box(f"{name}_shaft", collection, (x, y, z + 0.28),
                 (0.13, 0.13, 0.37), marble, bevel=0.013)
    geometry.cone(f"{name}_spire", collection, (x, y, z + 0.54),
                  0.11, 0.015, 0.23, marble, vertices=8)
    geometry.sphere(f"{name}_sun", collection, (x, y - 0.071, z + 0.31),
                    (0.050, 0.012, 0.050), mat(mats, "gilded_gold", "roof_gold"), segments=8)
