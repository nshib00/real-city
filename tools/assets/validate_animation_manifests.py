#!/usr/bin/env python3
"""Validate runtime animation manifests exported by the Real City asset pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOTS = (
    ROOT / "frontend" / "public" / "assets" / "buildings",
    ROOT / "frontend" / "public" / "assets" / "monsters",
)
ALLOWED_ANIMATION_TYPES = {"overlay", "shared_overlay", "sprite", "skeletal"}
ALLOWED_DIRECTIONS = {"n", "ne", "e", "se", "s", "sw", "w", "nw"}
MONSTER_ACTIONS = {"idle", "walk", "attack", "hit", "death", "spawn", "roar"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Manifest files or directories. Defaults to animation-capable public asset manifests.")
    parser.add_argument("--report", help="Write JSON report to this path.")
    args = parser.parse_args()

    reports = []
    failures = 0
    for path in collect_manifest_paths(args.paths):
        errors = validate_manifest(path)
        reports.append({"manifest": str(path), "errors": errors})
        if errors:
            failures += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")

    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


def collect_manifest_paths(inputs: Iterable[str]) -> list[Path]:
    raw_inputs = list(inputs)
    if raw_inputs:
        result: list[Path] = []
        for raw in raw_inputs:
            path = Path(raw)
            if path.is_dir():
                result.extend(sorted(path.glob("**/manifest.json")))
            else:
                result.append(path)
        return sorted(dict.fromkeys(item.resolve() for item in result))

    result = []
    for root in DEFAULT_ROOTS:
        if root.exists():
            for path in sorted(root.glob("**/manifest.json")):
                data = read_json(path)
                if isinstance(data, dict) and (data.get("animations") or data.get("atlas") or data.get("monster_id")):
                    result.append(path)
    return result


def validate_manifest(path: Path) -> list[str]:
    data = read_json(path)
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    errors: list[str] = []
    kind = manifest_kind(data)
    asset_id = data.get("asset_id") or data.get("asset") or data.get("monster_id") or data.get("id")
    if not isinstance(asset_id, str) or not asset_id:
        errors.append("manifest must define asset_id, asset, monster_id or id")

    anchor = data.get("anchor") or (data.get("sprite") if isinstance(data.get("sprite"), dict) else {}).get("anchor")
    if anchor is None:
        errors.append("anchor must be defined at manifest root or sprite.anchor")
    elif not is_int_pair(anchor):
        errors.append("anchor must be [x, y]")

    atlas_frames: set[str] | None = None
    atlas = data.get("atlas")
    if atlas is not None:
        atlas_errors, atlas_frames = validate_atlas(path.parent, atlas)
        errors.extend(atlas_errors)

    animations = data.get("animations")
    if animations is not None:
        errors.extend(validate_animations(animations, kind=kind, directions=data.get("directions"), atlas_frames=atlas_frames))
    elif kind == "monster":
        errors.append("monster manifest must define animations")

    if kind == "monster":
        errors.extend(validate_monster_manifest(data))
    return errors


def validate_atlas(base: Path, value: Any) -> tuple[list[str], set[str] | None]:
    if not isinstance(value, dict):
        return ["atlas must be an object"], None
    errors: list[str] = []
    image = value.get("image")
    json_name = value.get("json")
    if not isinstance(image, str) or not image:
        errors.append("atlas.image must be a non-empty string")
    else:
        image_path = resolve_path(base, image)
        if not image_path.exists() or image_path.stat().st_size <= 0:
            errors.append(f"atlas.image is missing or empty: {image}")
    frames: set[str] | None = None
    if not isinstance(json_name, str) or not json_name:
        errors.append("atlas.json must be a non-empty string")
    else:
        atlas_path = resolve_path(base, json_name)
        if not atlas_path.exists() or atlas_path.stat().st_size <= 0:
            errors.append(f"atlas.json is missing or empty: {json_name}")
        else:
            atlas_data = read_json(atlas_path)
            frames = atlas_frame_names(atlas_data)
            if frames is None:
                errors.append(f"atlas.json has no frames object/list: {json_name}")
            elif not frames:
                errors.append(f"atlas.json contains no frames: {json_name}")
    return errors, frames


def validate_animations(value: Any, *, kind: str, directions: Any, atlas_frames: set[str] | None) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["animations must be a non-empty object"]
    errors: list[str] = []
    manifest_directions = tuple(str(direction) for direction in directions or ())
    for animation_id, animation in sorted(value.items()):
        if not isinstance(animation, dict):
            errors.append(f"animations.{animation_id} must be an object")
            continue
        errors.extend(validate_animation_entry(str(animation_id), animation, kind=kind, manifest_directions=manifest_directions, atlas_frames=atlas_frames))
    return errors


def validate_animation_entry(animation_id: str, animation: dict[str, Any], *, kind: str, manifest_directions: tuple[str, ...], atlas_frames: set[str] | None) -> list[str]:
    errors: list[str] = []
    fps = animation.get("fps")
    frame_count = animation.get("frames")
    if not isinstance(fps, (int, float)) or fps <= 0:
        errors.append(f"animations.{animation_id}.fps must be positive")
    if not isinstance(frame_count, int) or frame_count < 1:
        errors.append(f"animations.{animation_id}.frames must be a positive integer")
    if "loop" in animation and not isinstance(animation["loop"], bool):
        errors.append(f"animations.{animation_id}.loop must be boolean")
    if "anchor" in animation and not is_int_pair(animation["anchor"]):
        errors.append(f"animations.{animation_id}.anchor must be [x, y]")
    animation_type = animation.get("type")
    if animation_type is not None and animation_type not in ALLOWED_ANIMATION_TYPES:
        errors.append(f"animations.{animation_id}.type is unsupported: {animation_type}")
    if kind == "monster" and animation_id not in MONSTER_ACTIONS:
        errors.append(f"monster animation action is unsupported: {animation_id}")

    prefix = animation.get("framePrefix") or animation.get("frame_prefix")
    if animation_type == "shared_overlay" and animation.get("id") and not prefix:
        return errors
    if not isinstance(prefix, str) or not prefix:
        errors.append(f"animations.{animation_id}.framePrefix is required")
        return errors

    if atlas_frames is not None and isinstance(frame_count, int) and frame_count > 0:
        expected_prefixes = expanded_prefixes(prefix, animation.get("directions") or manifest_directions)
        for expected_prefix in expected_prefixes:
            matching = [frame for frame in atlas_frames if frame.startswith(expected_prefix)]
            if len(matching) < frame_count:
                errors.append(f"animations.{animation_id} has {len(matching)}/{frame_count} atlas frames for prefix {expected_prefix}")
    return errors


def validate_monster_manifest(data: dict[str, Any]) -> list[str]:
    directions = data.get("directions")
    if not isinstance(directions, list) or not directions:
        return ["monster directions must be a non-empty list"]
    unsupported = sorted({str(direction) for direction in directions if direction not in ALLOWED_DIRECTIONS})
    if unsupported:
        return ["monster directions contain unsupported values: " + ", ".join(unsupported)]
    return []


def expanded_prefixes(prefix: str, directions: Any) -> tuple[str, ...]:
    if "{direction}" not in prefix:
        return (prefix,)
    if not isinstance(directions, (list, tuple)) or not directions:
        return (prefix.replace("{direction}", ""),)
    return tuple(prefix.replace("{direction}", str(direction)) for direction in directions)


def atlas_frame_names(data: Any) -> set[str] | None:
    if not isinstance(data, dict):
        return None
    frames = data.get("frames")
    if isinstance(frames, dict):
        return set(str(key) for key in frames)
    if isinstance(frames, list):
        result = set()
        for item in frames:
            if isinstance(item, dict) and item.get("filename"):
                result.add(str(item["filename"]))
        return result
    return None


def manifest_kind(data: dict[str, Any]) -> str:
    if data.get("kind") == "monster" or data.get("monster_id"):
        return "monster"
    return "building"


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (base / path, ROOT / path)
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"__read_error__": str(exc)}


def is_int_pair(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) for item in value)


if __name__ == "__main__":
    raise SystemExit(main())
