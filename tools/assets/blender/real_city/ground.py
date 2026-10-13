"""Shared flat ground tile helpers."""

from __future__ import annotations

import math

from . import geometry
from .constants import DEFAULT_TILE_SIZE


def add_ground_tile(
    collection,
    materials: dict,
    *,
    prefix: str,
    tile_size: float = DEFAULT_TILE_SIZE,
    z: float = 0.0,
    include_path: bool = True,
):
    """Add the standard flat Real City building ground.

    Object names intentionally include ``earth_tile``, ``grass_tile`` and
    ``path_stone`` so existing ground-signature validators can identify them.
    """

    earth = materials.get("earth_warm") or materials["earth"]
    grass = materials.get("grass_bright") or materials.get("grass") or earth
    stone = materials.get("stone_light") or materials.get("path_warm") or earth
    geometry.box(f"{prefix}_earth_tile", collection, (0, 0, z - 0.075), (tile_size, tile_size, 0.15), earth, bevel=0.07)
    geometry.box(f"{prefix}_grass_tile", collection, (0, 0, z + 0.015), (tile_size - 0.02, tile_size - 0.02, 0.10), grass, bevel=0.06)
    if include_path:
        for i in range(3):
            geometry.box(
                f"{prefix}_path_stone_{i+1:02d}",
                collection,
                (0.05 * math.sin(i), -1.12 - 0.23 * i, z + 0.08),
                (0.48, 0.21, 0.07),
                stone,
                bevel=0.04,
                rotation=(0, 0, 0.09 * (i - 1)),
            )
