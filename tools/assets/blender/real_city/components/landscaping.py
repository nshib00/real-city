"""Ground decoration components around buildings."""

from __future__ import annotations

import math

from .. import geometry
from .common import mat


def add_grass_clump(name: str, collection, mats: dict, loc, *, height="low", blades=5):
    x, y, z = loc
    blade_h = 0.10 if height == "low" else 0.20
    blade_w = 0.018 if height == "low" else 0.026
    for index in range(blades):
        angle = index * math.tau / max(1, blades)
        bx = x + math.cos(angle) * 0.035
        by = y + math.sin(angle) * 0.035
        geometry.box(
            f"{name}_{height}_grass_{index:02d}",
            collection,
            (bx, by, z + blade_h / 2),
            (blade_w, 0.010, blade_h),
            mat(mats, "grass_light", "grass_bright"),
            bevel=0.002,
            rotation=(0.0, 0.0, angle + 0.18),
        )


def add_flower(name: str, collection, mats: dict, loc, *, kind="red"):
    roles = {
        "red": "flower_red",
        "yellow": "flower_yellow",
        "white": "flower_white",
        "lilac": "flower_lilac",
    }
    x, y, z = loc
    geometry.cylinder(f"{name}_{kind}_stem", collection, (x, y, z + 0.055), 0.007, 0.11, mat(mats, "grass_bright"), vertices=5)
    geometry.sphere(f"{name}_{kind}_bloom", collection, (x, y, z + 0.13), (0.034, 0.034, 0.026), mat(mats, roles.get(kind, "flower_red"), "roof_red"), segments=8)


def add_flower_bed(name: str, collection, mats: dict, loc, *, style="round"):
    x, y, z = loc
    if style == "round":
        geometry.cylinder(f"{name}_round_bed_soil", collection, (x, y, z + 0.018), 0.22, 0.036, mat(mats, "soil", "earth_warm"), vertices=16)
        positions = [(0, 0), (-0.08, 0.04), (0.08, 0.04), (0, -0.08)]
    elif style == "box":
        geometry.box(f"{name}_box_bed_frame", collection, (x, y, z + 0.040), (0.46, 0.24, 0.080), mat(mats, "wood_beam", "wood_dark"), bevel=0.010)
        geometry.box(f"{name}_box_bed_soil", collection, (x, y, z + 0.090), (0.38, 0.16, 0.030), mat(mats, "soil"), bevel=0.006)
        positions = [(-0.13, 0), (0, 0.02), (0.13, -0.01)]
    elif style == "stone_ring":
        geometry.cylinder(f"{name}_ring_soil", collection, (x, y, z + 0.020), 0.20, 0.040, mat(mats, "soil_light", "soil"), vertices=14)
        for index in range(8):
            angle = index * math.tau / 8
            geometry.sphere(f"{name}_ring_stone_{index:02d}", collection, (x + math.cos(angle) * 0.22, y + math.sin(angle) * 0.22, z + 0.045), (0.045, 0.035, 0.025), mat(mats, "stone_light"), segments=8)
        positions = [(-0.06, 0.04), (0.07, 0.04), (0, -0.07)]
    else:
        geometry.box(f"{name}_strip_soil", collection, (x, y, z + 0.018), (0.56, 0.12, 0.036), mat(mats, "soil", "earth_warm"), bevel=0.012)
        positions = [(-0.20, 0), (-0.07, 0.01), (0.07, -0.01), (0.20, 0)]
    kinds = ("red", "yellow", "white", "lilac")
    for index, (px, py) in enumerate(positions):
        add_flower(f"{name}_flower_{index:02d}", collection, mats, (x + px, y + py, z + 0.05), kind=kinds[index % len(kinds)])


def add_pebble_cluster(name: str, collection, mats: dict, loc, *, count=7, radius=0.22):
    x, y, z = loc
    for index in range(count):
        angle = index * 2.399963
        dist = radius * (0.25 + 0.75 * ((index * 37) % 100) / 100)
        geometry.sphere(
            f"{name}_pebble_{index:02d}",
            collection,
            (x + math.cos(angle) * dist, y + math.sin(angle) * dist, z + 0.018),
            (0.040 + 0.008 * (index % 3), 0.030, 0.018),
            mat(mats, "stone_light", "stone_shadow"),
            segments=8,
        )
