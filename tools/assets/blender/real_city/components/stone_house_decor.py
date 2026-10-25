"""Twenty optional mid-poly decorations for stone houses.

Every factory creates named geometry in the supplied collection. ``loc`` is the
centre of a wall/roof attachment, or the ground contact point for yard props.
Facades face negative Y. Dimensions are in the existing house scene units.
"""

from __future__ import annotations

import math

from .. import geometry
from .common import mat


def add_keystone_sun(name, collection, mats, loc):
    """Raised three-stone sunburst above an entrance."""
    x, y, z = loc
    for i, dx in enumerate((-0.13, 0, 0.13)):
        geometry.box(f"{name}_ray_{i}", collection, (x + dx, y, z - abs(dx) * 0.23),
                     (0.105, 0.055, 0.13), mat(mats, "stone_block", "stone_light"),
                     bevel=0.012, rotation=(0, 0, -dx * 0.65))
    geometry.sphere(f"{name}_sun", collection, (x, y - 0.037, z + 0.018),
                    (0.044, 0.015, 0.044), mat(mats, "roof_gold", "copper"), segments=10)


def add_recessed_wall_shelf(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_shadow", collection, loc, (0.30, 0.023, 0.33), mat(mats, "stone_shadow"), bevel=0.012)
    geometry.box(f"{name}_ledge", collection, (x, y - 0.055, z - 0.165),
                 (0.37, 0.13, 0.055), mat(mats, "stone_block"), bevel=0.011)
    for side in (-1, 1):
        geometry.box(f"{name}_jamb_{side}", collection, (x + side * 0.16, y - 0.026, z),
                     (0.055, 0.07, 0.36), mat(mats, "stone_light"), bevel=0.008)


def add_masonry_ribbon(name, collection, mats, loc, *, width=0.76):
    x, y, z = loc
    geometry.box(f"{name}_bed", collection, loc, (width, 0.075, 0.085), mat(mats, "stone_shadow"), bevel=0.008)
    for i in range(5):
        geometry.box(f"{name}_block_{i}", collection,
                     (x + (i - 2) * width / 5, y - 0.046, z),
                     (width / 5 - 0.009, 0.045, 0.075),
                     mat(mats, "stone_light" if i % 2 else "stone_block"), bevel=0.006)


def add_copper_wall_rosette(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_back", collection, loc, 0.118, 0.038,
                      mat(mats, "stone_block"), vertices=12, rotation=(math.pi / 2, 0, 0))
    geometry.cylinder(f"{name}_hub", collection, (x, y - 0.027, z), 0.044, 0.021,
                      mat(mats, "copper", "metal_worn"), vertices=10, rotation=(math.pi / 2, 0, 0))
    for i in range(4):
        angle = i * math.pi / 2
        geometry.beam(f"{name}_petal_{i}", collection,
                      (x + 0.038 * math.cos(angle), y - 0.032, z + 0.038 * math.sin(angle)),
                      (x + 0.091 * math.cos(angle), y - 0.032, z + 0.091 * math.sin(angle)),
                      0.026, mat(mats, "copper", "metal_worn"))


def add_window_drain_lip(name, collection, mats, loc, *, width=0.48):
    x, y, z = loc
    geometry.box(f"{name}_sill", collection, loc, (width, 0.15, 0.060), mat(mats, "stone_light"), bevel=0.010)
    geometry.box(f"{name}_drip", collection, (x, y - 0.085, z - 0.029),
                 (width * 0.93, 0.032, 0.025), mat(mats, "copper", "metal_worn"), bevel=0.004)


def add_arched_vent(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_recess", collection, loc, (0.23, 0.025, 0.16), mat(mats, "stone_shadow"), bevel=0.012)
    geometry.cylinder(f"{name}_arch", collection, (x, y - 0.021, z + 0.067), 0.115, 0.035,
                      mat(mats, "stone_block"), vertices=12, rotation=(math.pi / 2, 0, 0))
    for i in (-1, 0, 1):
        geometry.box(f"{name}_grille_{i}", collection, (x + i * 0.068, y - 0.055, z),
                     (0.018, 0.022, 0.14), mat(mats, "metal_worn"), bevel=0.003)


def add_corner_stone_bracket(name, collection, mats, loc):
    x, y, z = loc
    for i in range(3):
        geometry.box(f"{name}_course_{i}", collection, (x, y, z + i * 0.115),
                     (0.22 + (i % 2) * 0.045, 0.21, 0.105),
                     mat(mats, "stone_light" if i % 2 else "stone_block"), bevel=0.012)
    geometry.box(f"{name}_cap", collection, (x, y - 0.012, z + 0.37),
                 (0.30, 0.27, 0.075), mat(mats, "stone_block"), bevel=0.012)


def add_wall_lantern_niche(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_dark", collection, loc, (0.21, 0.030, 0.30), mat(mats, "stone_shadow"), bevel=0.008)
    geometry.box(f"{name}_light", collection, (x, y - 0.033, z),
                 (0.12, 0.035, 0.17), mat(mats, "window_warm"), bevel=0.014)
    geometry.box(f"{name}_hood", collection, (x, y - 0.055, z + 0.17),
                 (0.27, 0.17, 0.065), mat(mats, "stone_block"), bevel=0.012)
    geometry.box(f"{name}_base", collection, (x, y - 0.055, z - 0.17),
                 (0.26, 0.17, 0.05), mat(mats, "stone_block"), bevel=0.009)


def add_roof_leaf_finial(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_socket", collection, (x, y, z + 0.032), 0.075, 0.065,
                      mat(mats, "roof_green"), vertices=10)
    geometry.beam(f"{name}_stem", collection, (x, y, z + 0.06), (x, y, z + 0.32),
                  0.028, mat(mats, "copper", "metal_worn"))
    geometry.sphere(f"{name}_leaf", collection, (x + 0.057, y, z + 0.25),
                    (0.115, 0.025, 0.05), mat(mats, "roof_leaf", "roof_green"), segments=10)


def add_ridge_copper_clasp(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_crown", collection, (x, y, z + 0.035),
                 (0.22, 0.15, 0.055), mat(mats, "copper", "metal_worn"), bevel=0.009)
    for side in (-1, 1):
        geometry.box(f"{name}_wing_{side}", collection, (x + side * 0.11, y, z - 0.005),
                     (0.11, 0.13, 0.028), mat(mats, "copper", "metal_worn"),
                     bevel=0.004, rotation=(0, side * 0.40, 0))


def add_gable_tile_fan(name, collection, mats, loc):
    x, y, z = loc
    for i in range(5):
        dx = (i - 2) * 0.083
        geometry.box(f"{name}_tile_{i}", collection, (x + dx, y, z - abs(dx) * 0.75),
                     (0.09, 0.035, 0.12), mat(mats, "roof_green" if i % 2 else "roof_leaf"),
                     bevel=0.011, rotation=(0, 0, -dx * 0.60))
    geometry.box(f"{name}_tie", collection, (x, y - 0.016, z - 0.19),
                 (0.43, 0.032, 0.045), mat(mats, "copper", "metal_worn"), bevel=0.006)


def add_chimney_copper_crown(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_ring", collection, loc, (0.29, 0.24, 0.065), mat(mats, "copper"), bevel=0.009)
    for sx in (-1, 1):
        for sy in (-1, 1):
            geometry.box(f"{name}_post_{sx}_{sy}", collection,
                         (x + sx * 0.105, y + sy * 0.078, z + 0.115),
                         (0.025, 0.025, 0.18), mat(mats, "metal_worn"), bevel=0.003)
    geometry.box(f"{name}_cap", collection, (x, y, z + 0.23),
                 (0.35, 0.30, 0.055), mat(mats, "roof_green"), bevel=0.012)


def add_dormer_side_fins(name, collection, mats, loc):
    x, y, z = loc
    for side in (-1, 1):
        geometry.box(f"{name}_fin_{side}", collection, (x + side * 0.18, y, z),
                     (0.055, 0.24, 0.23), mat(mats, "stone_block"), bevel=0.008)
        geometry.box(f"{name}_cap_{side}", collection, (x + side * 0.18, y - 0.01, z + 0.13),
                     (0.085, 0.28, 0.045), mat(mats, "roof_green"), bevel=0.008)


def add_eave_chain_cup(name, collection, mats, loc, *, drop=0.38):
    x, y, z = loc
    geometry.box(f"{name}_hook", collection, (x, y, z), (0.10, 0.09, 0.04), mat(mats, "copper"), bevel=0.006)
    for i in range(3):
        geometry.cylinder(f"{name}_cup_{i}", collection,
                          (x, y, z - 0.065 - i * drop / 3), 0.043, 0.065,
                          mat(mats, "copper"), vertices=8)
        if i < 2:
            geometry.beam(f"{name}_link_{i}", collection,
                          (x, y, z - 0.10 - i * drop / 3),
                          (x, y, z - 0.03 - (i + 1) * drop / 3),
                          0.013, mat(mats, "metal_worn"))


def add_paved_stone_sun(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_centre", collection, (x, y, z + 0.018), 0.10, 0.035,
                      mat(mats, "stone_block"), vertices=12)
    for i in range(8):
        a = i * math.pi / 4
        geometry.box(f"{name}_ray_{i}", collection,
                     (x + 0.20 * math.cos(a), y + 0.20 * math.sin(a), z + 0.018),
                     (0.14, 0.085, 0.035), mat(mats, "stone_light"),
                     bevel=0.009, rotation=(0, 0, a))


def add_courtyard_moss_slab(name, collection, mats, loc):
    x, y, z = loc
    geometry.box(f"{name}_slab", collection, (x, y, z + 0.026),
                 (0.43, 0.32, 0.052), mat(mats, "stone_block"), bevel=0.014)
    for i, sx in enumerate((-1, 1)):
        geometry.box(f"{name}_moss_{i}", collection,
                     (x + sx * 0.15, y + 0.08 * sx, z + 0.055),
                     (0.10, 0.065, 0.012), mat(mats, "grass_light", "roof_leaf"), bevel=0.005)


def add_rain_barrel_stand(name, collection, mats, loc):
    x, y, z = loc
    for sx in (-1, 1):
        geometry.box(f"{name}_foot_{sx}", collection, (x + sx * 0.13, y, z + 0.035),
                     (0.07, 0.34, 0.07), mat(mats, "stone_block"), bevel=0.008)
    geometry.cylinder(f"{name}_barrel", collection, (x, y, z + 0.25), 0.15, 0.36,
                      mat(mats, "wood_dark"), vertices=12)
    for dz in (0.12, 0.37):
        geometry.cylinder(f"{name}_band_{dz}", collection, (x, y, z + dz), 0.158, 0.028,
                          mat(mats, "copper", "metal_worn"), vertices=12)
    geometry.cylinder(f"{name}_water", collection, (x, y, z + 0.432), 0.12, 0.008,
                      mat(mats, "glass_cyan"), vertices=12)


def add_stone_seed_planter(name, collection, mats, loc):
    x, y, z = loc
    geometry.cylinder(f"{name}_pedestal", collection, (x, y, z + 0.075), 0.11, 0.15,
                      mat(mats, "stone_block"), vertices=10)
    geometry.cylinder(f"{name}_bowl", collection, (x, y, z + 0.19), 0.20, 0.12,
                      mat(mats, "stone_light"), vertices=12)
    geometry.cylinder(f"{name}_soil", collection, (x, y, z + 0.255), 0.16, 0.012,
                      mat(mats, "earth_warm", "stone_shadow"), vertices=12)
    for i in range(5):
        a = i * 2 * math.pi / 5
        geometry.sphere(f"{name}_leaf_{i}", collection,
                        (x + 0.08 * math.cos(a), y + 0.08 * math.sin(a), z + 0.30),
                        (0.065, 0.045, 0.052), mat(mats, "roof_leaf", "grass_light"), segments=8)


def add_low_courtyard_gate(name, collection, mats, loc, *, width=0.72):
    x, y, z = loc
    for side in (-1, 1):
        geometry.box(f"{name}_pier_{side}", collection,
                     (x + side * width / 2, y, z + 0.23),
                     (0.17, 0.18, 0.46), mat(mats, "stone_block"), bevel=0.012)
        geometry.box(f"{name}_pier_cap_{side}", collection,
                     (x + side * width / 2, y, z + 0.49),
                     (0.22, 0.23, 0.055), mat(mats, "stone_light"), bevel=0.009)
    geometry.beam(f"{name}_lintel", collection,
                  (x - width / 2, y, z + 0.39), (x + width / 2, y, z + 0.39),
                  0.045, mat(mats, "copper", "metal_worn"))


def add_hearth_ash_bucket(name, collection, mats, loc):
    x, y, z = loc
    geometry.cone(f"{name}_pail", collection, (x, y, z + 0.13), 0.13, 0.10, 0.26,
                  mat(mats, "metal_worn"), vertices=10)
    geometry.cylinder(f"{name}_rim", collection, (x, y, z + 0.26), 0.14, 0.025,
                      mat(mats, "copper"), vertices=10)
    geometry.beam(f"{name}_handle_l", collection, (x - 0.12, y, z + 0.23),
                  (x, y, z + 0.37), 0.014, mat(mats, "metal_worn"))
    geometry.beam(f"{name}_handle_r", collection, (x, y, z + 0.37),
                  (x + 0.12, y, z + 0.23), 0.014, mat(mats, "metal_worn"))
