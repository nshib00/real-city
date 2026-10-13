#!/usr/bin/env python3
"""Create contact sheets for Real City animation frame batches."""

from __future__ import annotations

import argparse
from pathlib import Path

from blender.real_city.export import make_contact_sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Frame files or directories with rendered animation PNG frames.")
    parser.add_argument("--pattern", default="*.png", help="Glob pattern used when a path is a directory.")
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--output-name", default="animation-contact-sheet.png")
    args = parser.parse_args()

    failures = 0
    for path in [Path(raw) for raw in args.paths]:
        frames = collect_frames(path, args.pattern)
        if not frames:
            failures += 1
            print(f"FAIL {path}: no animation frames matched {args.pattern}")
            continue
        output_dir = path if path.is_dir() else path.parent
        output = output_dir / args.output_name
        make_contact_sheet(frames, output, columns=args.columns)
        print(f"PASS {output} ({len(frames)} frames)")
    return 1 if failures else 0


def collect_frames(path: Path, pattern: str) -> list[Path]:
    if path.is_dir():
        return sorted(item for item in path.glob(pattern) if item.is_file())
    if path.is_file():
        return [path]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
