"""General prop kit for readable mid-poly map assets."""

from __future__ import annotations

import math

from .. import geometry
from .common import add_barrel, add_loose_planks, add_rope, mat


def add_crate(name: str, collection, mats: dict, loc, size=(0.34, 0.28, 0.24), *, empty=False, damaged=False):
    body = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, "wood_pale", "wood_beam")
    geometry.box(f"{name}_crate_body", collection, loc, size, body, bevel=0.018)
    x, y, z = loc
    w, d, h = size
    if not empty:
        geometry.box(f"{name}_crate_lid", collection, (x, y, z + h * 0.55), (w * 1.05, d * 1.04, 0.045), mat(mats, "wood_beam", "wood_dark"), bevel=0.006)
    for sx in (-0.36, 0.36):
        geometry.box(f"{name}_crate_band_{sx}", collection, (x + sx * w, y - d * 0.52, z), (0.035, 0.030, h * 1.05), mat(mats, "wood_dark", "wood_beam"), bevel=0.004)


def add_sack(name: str, collection, mats: dict, loc, scale=(0.16, 0.13, 0.15), *, material_role="dust"):
    geometry.sphere(f"{name}_sack_body", collection, loc, scale, mat(mats, material_role, "dust"), segments=12)
    x, y, z = loc
    geometry.cylinder(f"{name}_sack_tie", collection, (x, y, z + scale[2] * 1.05), 0.030, 0.040, mat(mats, "rope", "wood_dark"), vertices=8)


def add_plank_stack(name: str, collection, mats: dict, loc, *, rows=3, count=4, length=0.62):
    x, y, z = loc
    for row in range(rows):
        for index in range(count):
            geometry.box(
                f"{name}_plank_{row:02d}_{index:02d}",
                collection,
                (x + (index - (count - 1) / 2) * 0.07, y, z + row * 0.055),
                (length, 0.055, 0.045),
                mat(mats, "wood_pale", "construction_plank"),
                bevel=0.005,
                rotation=(0, 0, -0.04 + index * 0.025),
            )


def add_tool_rack(name: str, collection, mats: dict, loc, *, tools=("hammer", "saw", "shovel")):
    x, y, z = loc
    geometry.box(f"{name}_rack_back", collection, (x, y, z + 0.22), (0.48, 0.055, 0.12), mat(mats, "wood_beam", "wood_dark"), bevel=0.008)
    for index, tool in enumerate(tools):
        tx = x - 0.18 + index * 0.18
        geometry.beam(f"{name}_{tool}_handle", collection, (tx, y - 0.02, z), (tx + 0.04, y - 0.02, z + 0.42), 0.018, mat(mats, "wood_dark"))
        geometry.box(f"{name}_{tool}_head", collection, (tx + 0.05, y - 0.035, z + 0.42), (0.10, 0.030, 0.055), mat(mats, "metal_worn", "steel_light"), bevel=0.004)


def add_workbench(name: str, collection, mats: dict, loc, size=(0.62, 0.36, 0.09)):
    x, y, z = loc
    geometry.box(f"{name}_bench_top", collection, (x, y, z + 0.32), size, mat(mats, "wood_pale", "wood_beam"), bevel=0.012)
    for sx in (-0.42, 0.42):
        for sy in (-0.32, 0.32):
            geometry.beam(f"{name}_bench_leg_{sx}_{sy}", collection, (x + sx * size[0], y + sy * size[1], z + 0.05), (x + sx * size[0], y + sy * size[1], z + 0.32), 0.030, mat(mats, "wood_dark"))
    geometry.box(f"{name}_tool_strip", collection, (x, y - size[1] * 0.40, z + 0.39), (size[0] * 0.72, 0.026, 0.026), mat(mats, "metal_worn", "steel_light"), bevel=0.003)


def add_scattered_debris(name: str, collection, mats: dict, loc=(0, 0, 0.08), *, count=6, roles=("wood_dark", "stone_shadow", "damage_char")):
    x, y, z = loc
    for index in range(count):
        role = roles[index % len(roles)]
        geometry.box(
            f"{name}_scattered_debris_{index:02d}",
            collection,
            (x - 0.55 + index * 0.20, y + (index % 3 - 1) * 0.16, z),
            (0.16 + 0.03 * (index % 2), 0.10, 0.08),
            mat(mats, role),
            bevel=0.010,
            rotation=(0.05 * (index % 2), 0.04, index * 0.47),
        )


def add_construction_scaffold(name: str, collection, mats: dict, *, width=1.8, y=-0.85, height=1.25):
    from .common import add_scaffold

    add_scaffold(name, collection, mats, width=width, height=height, y=y)
    add_loose_planks(f"{name}_materials", collection, mats, (-0.55, y - 0.18, 0.16), count=4)


def add_market_bundle(name: str, collection, mats: dict, loc):
    x, y, z = loc
    add_crate(f"{name}_crate", collection, mats, (x, y, z + 0.14), (0.34, 0.28, 0.24))
    add_sack(f"{name}_sack", collection, mats, (x + 0.32, y + 0.02, z + 0.12))
    add_barrel(f"{name}_barrel", collection, mats, (x - 0.32, y + 0.02, z + 0.18))
    add_rope(f"{name}_bundle_rope", collection, mats, (x - 0.18, y - 0.18, z + 0.30), (x + 0.18, y - 0.16, z + 0.31), width=0.018)


def add_log_stack(name: str, collection, mats: dict, loc, *, count=4, radius=0.045, length=0.36):
    x, y, z = loc
    for index in range(count):
        lx = x + (index % 2) * radius * 3.8
        ly = y - (index // 2) * radius * 2.2
        lz = z + (index // 2) * radius * 1.7
        geometry.cylinder(f"{name}_log_{index:02d}", collection, (lx, ly, lz), radius, length, mat(mats, "wood_cut", "wood_pale"), vertices=9, rotation=(0, math.radians(90), 0))
        geometry.cylinder(f"{name}_log_bark_{index:02d}", collection, (lx, ly, lz), radius * 1.05, 0.018, mat(mats, "wood_dark"), vertices=9, rotation=(0, math.radians(90), 0))


def add_flower_strip(name: str, collection, mats: dict, loc, *, count=4):
    x, y, z = loc
    roles = ("flower_red", "flower_yellow", "flower_lilac", "flower_white")
    for index in range(count):
        geometry.sphere(
            f"{name}_flower_{index:02d}",
            collection,
            (x - (count - 1) * 0.10 + index * 0.20, y, z),
            (0.045, 0.045, 0.030),
            mat(mats, roles[index % len(roles)], "roof_red"),
            segments=8,
        )


def add_flag_marker(name: str, collection, mats: dict, loc, *, height=0.78, color_role="roof_red"):
    from .common import add_flag_pole

    add_flag_pole(name, collection, mats, loc, height=height, flag_size=(0.36, 0.24), color_role=color_role)


def add_decor_cluster(name: str, collection, mats: dict, loc, *, damaged=False):
    x, y, z = loc
    add_crate(f"{name}_crate", collection, mats, (x, y, z + 0.14), (0.30, 0.25, 0.22), damaged=damaged)
    add_barrel(f"{name}_barrel", collection, mats, (x + 0.34, y + 0.02, z + 0.18), radius=0.13, height=0.32, damaged=damaged)
    add_log_stack(f"{name}_logs", collection, mats, (x - 0.46, y - 0.02, z + 0.10), count=4)
