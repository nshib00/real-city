"""Mid-poly detail kits for richer assets without rewriting generators."""

from __future__ import annotations

import math

from .. import geometry
from .common import add_crack, mat


def add_facade_overlay(name: str, collection, mats: dict, *, width=1.4, y=-0.62, z=0.78, material_role="wood_beam"):
    material = mat(mats, material_role, "wood_beam")
    geometry.box(f"{name}_facade_top_trim", collection, (0, y, z + 0.34), (width, 0.040, 0.055), material, bevel=0.006)
    geometry.box(f"{name}_facade_bottom_trim", collection, (0, y, z - 0.34), (width * 0.92, 0.040, 0.050), material, bevel=0.006)
    for x in (-width * 0.38, 0, width * 0.38):
        geometry.box(f"{name}_facade_vertical_trim_{x:.1f}", collection, (x, y, z), (0.055, 0.040, 0.62), material, bevel=0.006)


def add_corner_bevel_blocks(name: str, collection, mats: dict, *, width=1.4, depth=1.1, z=0.62, height=0.8, material_role="stone_light"):
    material = mat(mats, material_role, "stone_light")
    for index, (x, y) in enumerate(((-width / 2, -depth / 2), (width / 2, -depth / 2), (-width / 2, depth / 2), (width / 2, depth / 2))):
        geometry.box(f"{name}_bevel_block_{index}", collection, (x, y, z), (0.13, 0.13, height), material, bevel=0.020, rotation=(0, 0, math.radians(45)))


def add_damage_kit(name: str, collection, mats: dict, *, y=-0.68, z=0.72, width=1.2, material_role="damage_char"):
    add_crack(f"{name}_main", collection, mats, (-width * 0.26, y, z), length=0.36, angle=-0.42)
    add_crack(f"{name}_side", collection, mats, (width * 0.20, y, z - 0.10), length=0.28, angle=0.34)
    geometry.box(f"{name}_breach_shadow", collection, (width * 0.08, y - 0.010, z + 0.02), (0.36, 0.030, 0.28), mat(mats, "damage_crack"), bevel=0.0, rotation=(0, 0, -0.18))
    for index in range(4):
        geometry.box(
            f"{name}_fallen_chunk_{index}",
            collection,
            (-0.48 + index * 0.28, y - 0.26 - 0.02 * (index % 2), 0.10),
            (0.18, 0.12, 0.08),
            mat(mats, material_role, "stone_shadow"),
            bevel=0.010,
            rotation=(0, 0, index * 0.37),
        )


def add_texture_bake_strips(name: str, collection, mats: dict, *, width=1.2, y=-0.64, z=0.78, rows=3, material_role="wood_pale"):
    material = mat(mats, material_role, "wood_pale")
    for row in range(rows):
        geometry.box(
            f"{name}_bake_readable_strip_{row:02d}",
            collection,
            (0, y - 0.006 * row, z - 0.22 + row * 0.18),
            (width * (0.88 - row * 0.05), 0.022, 0.026),
            material,
            bevel=0.002,
            rotation=(0, 0, 0.01 if row % 2 else -0.01),
        )


def add_readable_prop_cluster(name: str, collection, mats: dict, *, loc=(0.82, -0.76, 0.12)):
    from . import props

    x, y, z = loc
    props.add_crate(f"{name}_readable_crate", collection, mats, (x, y, z + 0.08), (0.30, 0.24, 0.20))
    props.add_sack(f"{name}_readable_sack", collection, mats, (x - 0.28, y + 0.04, z + 0.04))
    props.add_tool_rack(f"{name}_readable_tools", collection, mats, (x + 0.28, y + 0.10, z))
