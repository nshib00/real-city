"""Aeolian fantasy accent components."""

from __future__ import annotations

import math

from .. import geometry
from .common import mat


def add_wind_marker(name: str, collection, mats: dict, loc, *, scale=1.0, damaged=False):
    x, y, z = loc
    pole = mat(mats, "damage_char", "metal_worn") if damaged else mat(mats, "metal_worn", "steel_light")
    geometry.cylinder(f"{name}_wind_marker_pole", collection, (x, y, z + 0.16 * scale), 0.018 * scale, 0.32 * scale, pole, vertices=8)
    geometry.box(f"{name}_wind_marker_banner", collection, (x + 0.08 * scale, y, z + 0.30 * scale), (0.18 * scale, 0.018 * scale, 0.08 * scale), mat(mats, "roof_coral", "roof_red"), bevel=0.006)


def add_ribbon(name: str, collection, mats: dict, loc, *, length=0.58, color_role="roof_teal", angle=0.18):
    x, y, z = loc
    geometry.box(f"{name}_aeolian_ribbon", collection, (x, y, z), (length, 0.035, 0.14), mat(mats, color_role, "roof_teal"), bevel=0.014, rotation=(0.04, 0, angle))


def add_light_crystal(name: str, collection, mats: dict, loc, *, height=0.34, radius=0.10, socket=True):
    crystal = geometry.aeolian_crystal(f"{name}_light_crystal", collection, loc, radius, height, mat(mats, "amethyst"))
    if socket:
        x, y, z = loc
        geometry.box(f"{name}_crystal_socket", collection, (x, y, z - height * 0.42), (radius * 3.0, radius * 2.2, 0.08), mat(mats, "metal_worn", "stone_shadow"), bevel=0.010)
    return crystal


def add_soft_canopy(name: str, collection, mats: dict, loc, size=(1.0, 0.7, 0.08), *, color_role="roof_teal", damaged=False):
    x, y, z = loc
    material = mat(mats, "damage_char", color_role) if damaged else mat(mats, color_role, "roof_teal")
    geometry.box(f"{name}_soft_canopy_panel", collection, loc, size, material, bevel=0.016, rotation=(0.10, 0.03, -0.06))
    for sx in (-size[0] * 0.46, size[0] * 0.46):
        geometry.beam(f"{name}_canopy_support_{sx:.1f}", collection, (x + sx, y - size[1] * 0.42, z - 0.52), (x + sx, y - size[1] * 0.42, z), 0.035, mat(mats, "wood_dark", "metal_worn"))


def add_lens(name: str, collection, mats: dict, loc, *, radius=0.12):
    x, y, z = loc
    geometry.cylinder(f"{name}_lens_frame", collection, (x, y, z), radius, 0.035, mat(mats, "copper", "metal_worn"), vertices=18, rotation=(math.radians(90), 0, 0))
    geometry.cylinder(f"{name}_lens_glass", collection, (x, y - 0.022, z), radius * 0.72, 0.022, mat(mats, "glass_cyan"), vertices=18, rotation=(math.radians(90), 0, 0))


def add_clock_or_city_seal(name: str, collection, mats: dict, loc, *, radius=0.13):
    x, y, z = loc
    geometry.cylinder(f"{name}_seal_base", collection, (x, y, z), radius, 0.034, mat(mats, "roof_gold", "metal_worn"), vertices=20, rotation=(math.radians(90), 0, 0))
    geometry.beam(f"{name}_seal_hand_a", collection, (x, y - 0.026, z), (x + radius * 0.45, y - 0.026, z + radius * 0.14), 0.010, mat(mats, "wood_dark", "metal_worn"))
    geometry.beam(f"{name}_seal_hand_b", collection, (x, y - 0.028, z), (x - radius * 0.12, y - 0.028, z + radius * 0.50), 0.010, mat(mats, "wood_dark", "metal_worn"))
