"""Project-wide constants for Real City Blender asset generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SPRITE_SIZE = (512, 384)
ANCHOR = (256, 292)
DEFAULT_TILE_SIZE = 3.6
GROUND_PIXEL_WIDTH = 278
ACTIVE_STATES = ("active", "construction", "damaged")
EXTENDED_BUILDING_STATES = ACTIVE_STATES


@dataclass(frozen=True)
class RenderProfile:
    """Shared camera/render contract for map sprites."""

    sprite_size: tuple[int, int] = SPRITE_SIZE
    anchor: tuple[int, int] = ANCHOR
    tile_size: float = DEFAULT_TILE_SIZE
    ground_pixel_width: int = GROUND_PIXEL_WIDTH
    camera_name: str = "real_city_isometric_camera"
    view_transform: str = "AgX"
    render_engine: str = "CYCLES"
    samples: int = 24


@dataclass(frozen=True)
class AssetOutput:
    """Runtime/source output locations for one asset family."""

    asset_id: str
    category: str
    root: Path
    use_public_glb: bool = True

    @property
    def public_dir(self) -> Path:
        return self.root / "frontend" / "public" / "assets" / "buildings" / self.category / self.asset_id

    @property
    def src_dir(self) -> Path:
        return self.root / "frontend" / "src" / "assets" / "buildings" / self.category / self.asset_id

    @property
    def runtime_dir(self) -> Path:
        return self.public_dir if self.use_public_glb else self.src_dir

    @property
    def blend_path(self) -> Path:
        return self.runtime_dir / f"{self.asset_id}_levels.blend"

    @property
    def combined_glb_path(self) -> Path:
        return self.runtime_dir / f"{self.asset_id}_levels.glb"

    @property
    def manifest_path(self) -> Path:
        return self.public_dir / "manifest.json"
