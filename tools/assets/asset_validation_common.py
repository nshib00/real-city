#!/usr/bin/env python3
"""Shared helpers for lightweight Real City asset quality gates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_BUILDINGS = ROOT / "frontend" / "public" / "assets" / "buildings"
SRC_BUILDINGS = ROOT / "frontend" / "src" / "assets" / "buildings"
DEFAULT_BUILDING_ROOTS = (PUBLIC_BUILDINGS, SRC_BUILDINGS)


@dataclass(frozen=True)
class AssetManifest:
    path: Path
    directory: Path
    data: dict[str, Any]

    @property
    def asset_id(self) -> str:
        return str(self.data.get("asset_id") or self.data.get("asset") or self.data.get("family") or self.data.get("id") or self.directory.name)

    @property
    def category(self) -> str:
        if self.data.get("category"):
            return str(self.data["category"])
        try:
            relative = self.directory.relative_to(PUBLIC_BUILDINGS)
        except ValueError:
            try:
                relative = self.directory.relative_to(SRC_BUILDINGS)
            except ValueError:
                return ""
        return relative.parts[0] if relative.parts else ""

    @property
    def levels(self) -> tuple[int, ...]:
        explicit = tuple(int(value) for value in self.data.get("levels") or ())
        if explicit:
            return explicit
        return tuple(sorted({int(item["level"]) for item in self.items if item.get("level") is not None}))

    @property
    def states(self) -> tuple[str, ...]:
        explicit = tuple(str(value) for value in self.data.get("states") or ())
        if explicit:
            return explicit
        return tuple(sorted({str(item["state"]) for item in self.items if item.get("state")}))

    @property
    def items(self) -> tuple[dict[str, Any], ...]:
        raw = self.data.get("items")
        if raw is None:
            raw = self.data.get("assets")
        if raw is None:
            files = self.data.get("files")
            if isinstance(files, list) and files and all(isinstance(item, dict) for item in files):
                raw = files
        if isinstance(raw, dict):
            result = []
            for key, value in raw.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("id", key)
                    result.append(_normalize_item_paths(item))
            return tuple(result)
        if isinstance(raw, list) and raw and all(isinstance(item, dict) for item in raw):
            return tuple(_normalize_item_paths(dict(item)) for item in raw)

        files = self.data.get("files") or []
        models = self.data.get("models") or []
        model_by_stem = {Path(str(model)).stem: str(model) for model in models}
        result = []
        for value in files:
            if not isinstance(value, str):
                continue
            parsed = parse_level_state(Path(value).stem)
            item: dict[str, Any] = {"id": Path(value).stem, "png": value}
            if parsed:
                item["level"], item["state"] = parsed
            model = model_by_stem.get(Path(value).stem)
            if model:
                item["glb"] = model
            result.append(item)
        return tuple(result)


def collect_manifest_paths(inputs: Iterable[str] | None = None) -> list[Path]:
    raw_inputs = list(inputs or ())
    if raw_inputs:
        result: list[Path] = []
        for raw in raw_inputs:
            path = Path(raw)
            if path.is_dir():
                result.extend(sorted(path.glob("**/manifest.json")))
            else:
                result.append(path)
        return sorted(dict.fromkeys(path.resolve() for path in result))

    paths: list[Path] = []
    for root in DEFAULT_BUILDING_ROOTS:
        if root.exists():
            paths.extend(sorted(root.glob("**/manifest.json")))
    return paths


def load_manifests(inputs: Iterable[str] | None = None) -> list[AssetManifest]:
    manifests: list[AssetManifest] = []
    for path in collect_manifest_paths(inputs):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"manifest root must be an object: {path}")
        manifests.append(AssetManifest(path=path, directory=path.parent, data=data))
    return manifests


def resolve_asset_path(base: Path, value: str | Path | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (ROOT / path, base / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def item_id(asset_id: str, level: int, state: str) -> str:
    return f"{asset_id}_l{level:02d}_{state}"


def existing_items_by_key(manifest: AssetManifest) -> dict[tuple[int, str], dict[str, Any]]:
    result: dict[tuple[int, str], dict[str, Any]] = {}
    for item in manifest.items:
        level = item.get("level")
        state = item.get("state")
        if level is None or not state:
            parsed = parse_level_state(str(item.get("id") or ""))
            if parsed:
                level, state = parsed
        if level is None or not state:
            continue
        result[(int(level), str(state))] = item
    return result


def parse_level_state(name: str) -> tuple[int, str] | None:
    marker = "_l"
    if marker not in name:
        return None
    tail = name.rsplit(marker, 1)[-1]
    if len(tail) < 4 or not tail[:2].isdigit() or tail[2] != "_":
        return None
    return int(tail[:2]), tail[3:]


def _normalize_item_paths(item: dict[str, Any]) -> dict[str, Any]:
    if "png" not in item and "sprite" in item:
        item["png"] = item["sprite"]
    if "glb" not in item and "model" in item:
        item["glb"] = item["model"]
    if item.get("level") is None or not item.get("state"):
        parsed = parse_level_state(str(item.get("id") or ""))
        if parsed:
            item.setdefault("level", parsed[0])
            item.setdefault("state", parsed[1])
    if item.get("level") is None and item.get("state") and item.get("shape"):
        item["level"] = 1
    return item
