"""Asset spec helpers for the Real City Blender factory.

The module is intentionally Blender-free. It normalizes YAML/JSON specs into a
small contract that generators and validators can share.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import ANCHOR, SPRITE_SIZE

DEFAULT_STYLE_PROFILE = "aeolian_fantasy_midpoly"
DEFAULT_SKILL_PROFILE = {
    "base": [
        "blender-director",
        "genre-strategy-sim",
        "isometric-style",
        "fantasy-worlds",
        "stylized-style",
        "hand-painted-style",
    ],
    "asset_type": ["environment-artist"],
    "production": [
        "materials",
        "texture-workflow",
        "lookdev",
        "lod-pipeline",
        "asset-optimization",
        "export-pipeline",
    ],
    "validation": ["qa-review"],
}
DEFAULT_PNG_POLICY = {
    "sprite_size": list(SPRITE_SIZE),
    "camera_profile": "real_city_isometric",
    "transparent_background": True,
    "anchor": list(ANCHOR),
    "render_lod": "LOD0",
    "contact_sheet": {
        "enabled": True,
        "columns": 4,
        "include_states": ["active", "construction", "damaged"],
    },
    "alpha_bounds": {
        "min_opaque_pixels": 1200,
        "max_crop_margin_px": 10,
        "bottom_anchor_tolerance_px": 10,
    },
}
BASE_STATES = ("active", "construction", "damaged")
ALLOWED_RUNTIME_STATES = {
    "active",
    "construction",
    "damaged",
    "ruined",
    "upgrading",
    "armed",
    "triggered",
    "empty",
    "no_crew",
    "no_mechanic",
    "no_keeper",
    "no_fuel",
}
ALLOWED_ANIMATION_DIRECTIONS = {"n", "ne", "e", "se", "s", "sw", "w", "nw"}
ALLOWED_BUILDING_ANIMATION_TYPES = {"overlay", "shared_overlay"}


@dataclass(frozen=True)
class TriangleBudget:
    min: int
    max: int


@dataclass(frozen=True)
class LevelSpec:
    level: int
    visual_goal: str
    triangle_budget: TriangleBudget
    cost_resources: tuple[str, ...] = ()
    adds: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    category: str
    kind: str
    display_name: str
    style_profile: str
    footprint: tuple[int, int]
    states: tuple[str, ...]
    levels: tuple[LevelSpec, ...]
    material_map: dict[str, dict[str, Any]]
    level_progression: dict[str, Any]
    state_policy: dict[str, Any]
    skill_profile: dict[str, list[str]]
    lod_policy: dict[str, Any]
    png_policy: dict[str, Any]
    atlas_policy: dict[str, Any] | None
    animation_policy: dict[str, Any] | None
    output: dict[str, Any]
    references: dict[str, Any]
    raw: dict[str, Any]

    @property
    def max_level(self) -> int:
        return max(level.level for level in self.levels)

    @property
    def level_numbers(self) -> tuple[int, ...]:
        return tuple(level.level for level in self.levels)


class AssetSpecError(ValueError):
    """Raised when an asset spec cannot be loaded or normalized."""


def default_lod_policy(asset_kind: str = "building") -> dict[str, Any]:
    if asset_kind == "prop":
        budgets = ((300, 900), (150, 450), (80, 200))
    elif asset_kind in {"building", "resource_node"}:
        budgets = ((1500, 6000), (700, 3000), (300, 1300))
    else:
        budgets = ((500, 2500), (250, 1200), (120, 600))
    return {
        "chain": [
            {"name": "LOD0", "ratio": 1.0, "triangle_budget": {"min": budgets[0][0], "max": budgets[0][1]}, "export": True},
            {"name": "LOD1", "ratio": 0.45, "triangle_budget": {"min": budgets[1][0], "max": budgets[1][1]}, "export": True},
            {"name": "LOD2", "ratio": 0.22, "triangle_budget": {"min": budgets[2][0], "max": budgets[2][1]}, "export": True},
        ],
        "preserve": ["footprint", "primary silhouette", "entrance orientation", "largest readable props"],
        "exports": {
            "naming": "{asset_id}_l{level:02d}_{state}_{lod}.glb",
            "include_lod0": True,
            "include_lod1": True,
            "include_lod2": True,
        },
    }


def load_asset_spec(path: str | Path) -> AssetSpec:
    source = Path(path)
    raw = _load_mapping(source)
    return normalize_asset_spec(raw, source)


def load_asset_spec_data(path: str | Path) -> dict[str, Any]:
    return load_asset_spec(path).raw


def normalize_asset_spec(raw: dict[str, Any], source: Path | None = None) -> AssetSpec:
    data = dict(raw)
    asset_id = _required_str(data, "asset_id", source)
    category = _required_str(data, "category", source)
    kind = data.get("kind", "building")
    display_name = data.get("display_name", asset_id)
    footprint = data.get("footprint")
    if not isinstance(footprint, dict):
        raise AssetSpecError(_msg(source, "footprint must be an object with width/height"))
    width = int(footprint.get("width", 0))
    height = int(footprint.get("height", 0))
    if width < 1 or height < 1:
        raise AssetSpecError(_msg(source, "footprint width/height must be positive"))

    data.setdefault("style_profile", DEFAULT_STYLE_PROFILE)
    data.setdefault("skill_profile", DEFAULT_SKILL_PROFILE)
    data.setdefault("lod_policy", default_lod_policy(kind))
    data.setdefault("png_policy", DEFAULT_PNG_POLICY)

    states = tuple(data.get("states") or ())
    if not states:
        raise AssetSpecError(_msg(source, "states must contain at least one state"))
    levels = tuple(_normalize_level(item, source) for item in data.get("levels") or ())
    if not levels:
        raise AssetSpecError(_msg(source, "levels must contain at least one level"))

    material_map = data.get("material_map")
    if kind == "building" and not material_map:
        raise AssetSpecError(_msg(source, "building specs must define material_map"))

    errors = validate_asset_spec_dict(data)
    if errors:
        raise AssetSpecError(_msg(source, "; ".join(errors)))

    return AssetSpec(
        asset_id=asset_id,
        category=category,
        kind=kind,
        display_name=str(display_name),
        style_profile=str(data["style_profile"]),
        footprint=(width, height),
        states=states,
        levels=levels,
        material_map=dict(material_map or {}),
        level_progression=dict(data.get("level_progression") or {}),
        state_policy=dict(data.get("state_policy") or {}),
        skill_profile={key: list(value) for key, value in dict(data["skill_profile"]).items()},
        lod_policy=dict(data["lod_policy"]),
        png_policy=dict(data["png_policy"]),
        atlas_policy=dict(data["atlas_policy"]) if isinstance(data.get("atlas_policy"), dict) else None,
        animation_policy=dict(data["animation_policy"]) if isinstance(data.get("animation_policy"), dict) else None,
        output=dict(data.get("output") or {}),
        references=dict(data.get("references") or {}),
        raw=data,
    )


def validate_asset_spec_dict(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("asset_id", "category", "kind", "footprint", "levels", "states", "output", "references"):
        if key not in data:
            errors.append(f"missing required field: {key}")
    asset_id = data.get("asset_id")
    if not isinstance(asset_id, str) or not asset_id.replace("_", "a").isalnum() or not asset_id[0].isalpha():
        errors.append("asset_id must be snake_case and start with a letter")

    levels = data.get("levels")
    if not isinstance(levels, list) or not levels:
        errors.append("levels must be a non-empty list")
    else:
        level_numbers = [item.get("level") for item in levels if isinstance(item, dict)]
        if level_numbers != sorted(level_numbers):
            errors.append("levels must be sorted by level")
        if len(set(level_numbers)) != len(level_numbers):
            errors.append("levels must not contain duplicates")
        for level in levels:
            if not isinstance(level, dict):
                errors.append("each level must be an object")
                continue
            budget = level.get("triangle_budget")
            errors.extend(_validate_budget(budget, f"level {level.get('level')} triangle_budget"))

    states = data.get("states")
    if not isinstance(states, list):
        errors.append("states must be a list")
    else:
        missing_base = [state for state in BASE_STATES if state not in states]
        if data.get("kind") == "building" and missing_base:
            errors.append("building states must include: active, construction, damaged")
        invalid_states = [state for state in states if not _is_valid_state_name(state)]
        if invalid_states:
            errors.append("states contain unsupported names: " + ", ".join(str(state) for state in invalid_states))

    material_map = data.get("material_map")
    if data.get("kind") == "building" and not isinstance(material_map, dict):
        errors.append("building material_map must be an object")

    skill_profile = data.get("skill_profile")
    if not isinstance(skill_profile, dict):
        errors.append("skill_profile must be an object")
    else:
        for key in ("base", "asset_type", "production", "validation"):
            if not isinstance(skill_profile.get(key), list):
                errors.append(f"skill_profile.{key} must be a list")

    lod_policy = data.get("lod_policy")
    if not isinstance(lod_policy, dict):
        errors.append("lod_policy must be an object")
    else:
        chain = lod_policy.get("chain")
        if not isinstance(chain, list) or not chain:
            errors.append("lod_policy.chain must be a non-empty list")
        else:
            names = [item.get("name") for item in chain if isinstance(item, dict)]
            for expected in ("LOD0", "LOD1", "LOD2"):
                if expected not in names:
                    errors.append(f"lod_policy.chain must include {expected}")
            for item in chain:
                if isinstance(item, dict):
                    errors.extend(_validate_budget(item.get("triangle_budget"), f"lod_policy.{item.get('name')} triangle_budget"))

    png_policy = data.get("png_policy")
    if not isinstance(png_policy, dict):
        errors.append("png_policy must be an object")
    else:
        square_sprite = data.get("asset_id") in ("wooden_wall", "stone_wall", "concrete_wall", "modern_wall", "copper_mine", "player_level_emblems")
        expected_size = (512, 512) if square_sprite else SPRITE_SIZE
        expected_anchor = (256, 256) if data.get("asset_id") == "player_level_emblems" else (256, 320) if square_sprite else ANCHOR
        if tuple(png_policy.get("sprite_size", ())) != expected_size:
            errors.append(f"png_policy.sprite_size must be {list(expected_size)}")
        if tuple(png_policy.get("anchor", ())) != expected_anchor:
            errors.append(f"png_policy.anchor must be {list(expected_anchor)}")
        if png_policy.get("transparent_background") is not True:
            errors.append("png_policy.transparent_background must be true")

    errors.extend(_validate_atlas_policy(data.get("atlas_policy")))
    errors.extend(_validate_animation_policy(data.get("animation_policy"), data.get("kind")))
    return errors


def _normalize_level(data: dict[str, Any], source: Path | None) -> LevelSpec:
    if not isinstance(data, dict):
        raise AssetSpecError(_msg(source, "level entry must be an object"))
    budget = data.get("triangle_budget") or {}
    return LevelSpec(
        level=int(data["level"]),
        visual_goal=str(data["visual_goal"]),
        triangle_budget=TriangleBudget(min=int(budget["min"]), max=int(budget["max"])),
        cost_resources=tuple(data.get("cost_resources") or ()),
        adds=tuple(data.get("adds") or ()),
        constraints=tuple(data.get("constraints") or ()),
    )


def _validate_budget(value: Any, label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    low = value.get("min")
    high = value.get("max")
    if not isinstance(low, int) or not isinstance(high, int):
        return [f"{label}.min/max must be integers"]
    if low < 0 or high <= 0 or low > high:
        return [f"{label}.min/max range is invalid"]
    return []


def _validate_atlas_policy(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["atlas_policy must be an object"]
    errors: list[str] = []
    for key in ("enabled", "image_format", "json_naming", "image_naming", "padding_px", "max_texture_size"):
        if key not in value:
            errors.append(f"atlas_policy.{key} is required")
    if value.get("image_format") not in {"png", "webp", "avif"}:
        errors.append("atlas_policy.image_format must be png, webp or avif")
    for key in ("json_naming", "image_naming"):
        if key in value and not isinstance(value[key], str):
            errors.append(f"atlas_policy.{key} must be a string")
    for key in ("padding_px", "max_texture_size"):
        if key in value and not isinstance(value[key], int):
            errors.append(f"atlas_policy.{key} must be an integer")
    if isinstance(value.get("padding_px"), int) and value["padding_px"] < 0:
        errors.append("atlas_policy.padding_px must be non-negative")
    if isinstance(value.get("max_texture_size"), int) and value["max_texture_size"] < 512:
        errors.append("atlas_policy.max_texture_size must be at least 512")
    return errors


def _validate_animation_policy(value: Any, kind: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["animation_policy must be an object"]
    errors: list[str] = []
    if "anchor" in value and not _is_int_pair(value["anchor"]):
        errors.append("animation_policy.anchor must be [x, y]")
    if "frame_size" in value and not _is_int_pair(value["frame_size"]):
        errors.append("animation_policy.frame_size must be [width, height]")
    contact_sheet = value.get("contact_sheet")
    if contact_sheet is not None:
        if not isinstance(contact_sheet, dict):
            errors.append("animation_policy.contact_sheet must be an object")
        else:
            for key in ("enabled", "columns", "output_name"):
                if key not in contact_sheet:
                    errors.append(f"animation_policy.contact_sheet.{key} is required")
            if "columns" in contact_sheet and (not isinstance(contact_sheet["columns"], int) or contact_sheet["columns"] < 1):
                errors.append("animation_policy.contact_sheet.columns must be a positive integer")
    building_overlays = value.get("building_overlays")
    monster_actions = value.get("monster_actions")
    if kind == "monster" and not monster_actions:
        errors.append("monster animation_policy must define monster_actions")
    if kind == "building" and not building_overlays and not monster_actions:
        errors.append("animation_policy must define building_overlays or monster_actions")
    if building_overlays is not None:
        if not isinstance(building_overlays, list):
            errors.append("animation_policy.building_overlays must be a list")
        else:
            for item in building_overlays:
                errors.extend(_validate_animation_entry(item, "animation_policy.building_overlays", building=True))
    if monster_actions is not None:
        if not isinstance(monster_actions, list):
            errors.append("animation_policy.monster_actions must be a list")
        else:
            for item in monster_actions:
                errors.extend(_validate_animation_entry(item, "animation_policy.monster_actions", monster=True))
    return errors


def _validate_animation_entry(value: Any, label: str, *, building: bool = False, monster: bool = False) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} entry must be an object"]
    errors: list[str] = []
    for key in ("id", "fps", "frames", "loop", "frame_prefix"):
        if key not in value:
            errors.append(f"{label}.{key} is required")
    if not isinstance(value.get("id"), str) or not _is_snake_case(value.get("id")):
        errors.append(f"{label}.id must be snake_case")
    if not isinstance(value.get("fps"), (int, float)) or value.get("fps", 0) <= 0:
        errors.append(f"{label}.fps must be positive")
    if not isinstance(value.get("frames"), int) or value.get("frames", 0) < 1:
        errors.append(f"{label}.frames must be a positive integer")
    if "loop" in value and not isinstance(value["loop"], bool):
        errors.append(f"{label}.loop must be boolean")
    if "anchor" in value and not _is_int_pair(value["anchor"]):
        errors.append(f"{label}.anchor must be [x, y]")
    if building and value.get("type") not in ALLOWED_BUILDING_ANIMATION_TYPES:
        errors.append(f"{label}.type must be overlay or shared_overlay")
    if building and "states" in value:
        states = value["states"]
        if not isinstance(states, list) or not all(_is_valid_state_name(state) for state in states):
            errors.append(f"{label}.states contains unsupported state names")
    if monster:
        directions = value.get("directions")
        if not isinstance(directions, list) or not directions:
            errors.append(f"{label}.directions must be a non-empty list")
        elif any(direction not in ALLOWED_ANIMATION_DIRECTIONS for direction in directions):
            errors.append(f"{label}.directions contains unsupported values")
    return errors


def _is_int_pair(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) for item in value)


def _is_snake_case(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value.replace("_", "a").isalnum() and value[0].isalpha()


def _is_valid_state_name(value: Any) -> bool:
    if value in ALLOWED_RUNTIME_STATES:
        return True
    if not isinstance(value, str):
        return False
    return bool(re.match(r"^(stage|super_stage)[0-9]{2}$", value))


def _load_mapping(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        value = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise AssetSpecError("PyYAML is required to read YAML asset specs") from exc
        value = yaml.safe_load(text)
    else:
        raise AssetSpecError(f"Unsupported asset spec extension: {path.suffix}")
    if not isinstance(value, dict):
        raise AssetSpecError(_msg(path, "spec root must be an object"))
    return value


def _required_str(data: dict[str, Any], key: str, source: Path | None) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise AssetSpecError(_msg(source, f"{key} must be a non-empty string"))
    return value


def _msg(source: Path | None, message: str) -> str:
    return f"{source}: {message}" if source else message
