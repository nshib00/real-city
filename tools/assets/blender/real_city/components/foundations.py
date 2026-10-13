"""Foundation components for reusable building bases."""

from __future__ import annotations

import math

from .. import geometry
from .common import mat

FOUNDATION_HEIGHTS = {"low": 0.14, "medium": 0.26, "high": 0.42}
FOUNDATION_THICKNESS = {"thin": 0.10, "medium": 0.20, "thick": 0.34}
FOUNDATION_MATERIALS = {
    "wood": "wood_beam",
    "stone": "stone_light",
    "brick": "brick_warm",
    "stone_block": "stone_block",
    "concrete": "concrete",
    "reinforced_concrete": "reinforced_concrete",
    "metal": "metal_worn",
}


def add_foundation(
    name: str,
    collection,
    mats: dict,
    *,
    width: float,
    depth: float,
    height: str = "low",
    thickness: str = "medium",
    material: str = "stone",
    loc=(0, 0, 0),
    damaged: bool = False,
):
    base_h = FOUNDATION_HEIGHTS.get(height, FOUNDATION_HEIGHTS["low"])
    margin = FOUNDATION_THICKNESS.get(thickness, FOUNDATION_THICKNESS["medium"])
    role = "damage_char" if damaged else FOUNDATION_MATERIALS.get(material, "stone_light")
    x, y, z = loc
    obj = geometry.box(
        f"{name}_{material}_{height}_{thickness}_foundation",
        collection,
        (x, y, z + base_h / 2),
        (width + margin, depth + margin * 0.82, base_h),
        mat(mats, role, "stone_light"),
        bevel=0.024,
    )
    trim_role = "wood_dark" if material == "wood" else "stone_shadow"
    if material in {"stone_block", "brick", "reinforced_concrete", "metal"}:
        rows = 1 if height == "low" else 2 if height == "medium" else 3
        cols = 4 if thickness == "thin" else 5 if thickness == "medium" else 6
        for row in range(rows):
            for col in range(cols):
                px = x - (width + margin * 0.45) / 2 + (col + 0.5) * (width + margin * 0.45) / cols
                pz = z + (row + 0.55) * base_h / rows
                geometry.box(
                    f"{name}_{material}_foundation_face_{row:02d}_{col:02d}",
                    collection,
                    (px, y - (depth + margin * 0.82) / 2 - 0.012, pz),
                    ((width + margin * 0.45) / cols * 0.78, 0.035, base_h / rows * 0.55),
                    mat(mats, role, "stone_light"),
                    bevel=0.006,
                )
    if material in {"reinforced_concrete", "metal"}:
        band = "metal_worn" if material == "reinforced_concrete" else "steel_light"
        geometry.box(f"{name}_foundation_front_band", collection, (x, y - (depth + margin) / 2, z + base_h * 0.68), (width + margin * 0.70, 0.038, 0.035), mat(mats, band), bevel=0.004)
    if material == "wood":
        geometry.box(f"{name}_foundation_front_beam", collection, (x, y - (depth + margin) / 2, z + base_h * 0.68), (width + margin * 0.70, 0.055, 0.055), mat(mats, trim_role), bevel=0.006)
    return obj


def add_round_foundation(
    name: str,
    collection,
    mats: dict,
    *,
    radius: float = 0.62,
    height: str = "low",
    thickness: str = "medium",
    material: str = "stone",
    loc=(0, 0, 0),
    segments: int = 18,
    damaged: bool = False,
):
    base_h = FOUNDATION_HEIGHTS.get(height, FOUNDATION_HEIGHTS["low"])
    margin = FOUNDATION_THICKNESS.get(thickness, FOUNDATION_THICKNESS["medium"])
    role = "damage_char" if damaged else FOUNDATION_MATERIALS.get(material, "stone_light")
    x, y, z = loc
    obj = geometry.cylinder(
        f"{name}_{material}_{height}_{thickness}_round_foundation",
        collection,
        (x, y, z + base_h / 2),
        radius + margin * 0.45,
        base_h,
        mat(mats, role, "stone_light"),
        vertices=segments,
    )
    if material in {"stone", "stone_block", "brick", "reinforced_concrete", "metal"}:
        block_role = "brick_light" if material == "brick" else role
        count = 10 if thickness == "thin" else 12 if thickness == "medium" else 14
        for index in range(count):
            angle = index * 6.283185307179586 / count
            px = x + math.cos(angle) * (radius + margin * 0.50)
            py = y + math.sin(angle) * (radius + margin * 0.50)
            geometry.box(
                f"{name}_{material}_round_face_{index:02d}",
                collection,
                (px, py, z + base_h * 0.56),
                (0.11, 0.035, base_h * 0.48),
                mat(mats, block_role, "stone_light"),
                bevel=0.006,
                rotation=(0, 0, angle),
            )
    if material in {"wood", "metal", "reinforced_concrete"}:
        band_role = "wood_dark" if material == "wood" else "steel_light"
        for index in range(8):
            angle = index * 6.283185307179586 / 8
            geometry.box(
                f"{name}_{material}_round_band_{index:02d}",
                collection,
                (x + math.cos(angle) * radius * 0.86, y + math.sin(angle) * radius * 0.86, z + base_h * 0.78),
                (0.22, 0.032, 0.035),
                mat(mats, band_role, role),
                bevel=0.004,
                rotation=(0, 0, angle),
            )
    return obj
