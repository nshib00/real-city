"""Shared Blender asset API for Real City generators.

The package is intentionally importable outside Blender. Modules import
``bpy`` lazily inside functions so smoke checks can run with normal Python.
"""

from .constants import (
    ACTIVE_STATES,
    ANCHOR,
    DEFAULT_TILE_SIZE,
    GROUND_PIXEL_WIDTH,
    SPRITE_SIZE,
    AssetOutput,
    RenderProfile,
)
from .paths import blender_path, building_public_dir, building_src_dir, project_root
from .spec import AssetSpec, AssetSpecError, LevelSpec, TriangleBudget, load_asset_spec

__all__ = [
    "ACTIVE_STATES",
    "ANCHOR",
    "AssetSpec",
    "AssetSpecError",
    "AssetOutput",
    "DEFAULT_TILE_SIZE",
    "GROUND_PIXEL_WIDTH",
    "LevelSpec",
    "RenderProfile",
    "SPRITE_SIZE",
    "TriangleBudget",
    "blender_path",
    "building_public_dir",
    "building_src_dir",
    "load_asset_spec",
    "project_root",
]
