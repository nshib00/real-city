"""Path helpers for WSL-hosted Codex and Windows-hosted Blender."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root(start: Path | None = None) -> Path:
    """Return repository root by walking up to the nearest marker file."""

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for parent in (current, *current.parents):
        if (parent / "AGENTS.md").exists() and (parent / "frontend").exists():
            return parent
    return Path(__file__).resolve().parents[4]


def blender_path(path: str | Path) -> str:
    """Return a path Blender can write to when it runs on Windows.

    Windows Blender cannot write to Linux paths like ``/home/...`` directly,
    so it uses the WSL UNC path. Native Linux Blender keeps the original path.
    """

    value = str(Path(path))
    if sys.platform != "win32":
        return value
    if value.startswith("/mnt/"):
        drive = value[5]
        rest = value[7:].replace("/", "\\")
        return f"{drive.upper()}:\\{rest}"
    if value.startswith("/"):
        distro = os.environ.get("WSL_DISTRO_NAME", "Debian")
        return "\\\\wsl.localhost\\" + distro + value.replace("/", "\\")
    return value


def building_public_dir(asset_id: str, category: str, root: Path | None = None) -> Path:
    return (root or project_root()) / "frontend" / "public" / "assets" / "buildings" / category / asset_id


def building_src_dir(asset_id: str, category: str, root: Path | None = None) -> Path:
    return (root or project_root()) / "frontend" / "src" / "assets" / "buildings" / category / asset_id
