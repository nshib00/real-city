"""Pack rendered Blender monster frames into Pixi spritesheets."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
TEMP = Path("/tmp/real-city-monster-frames")
OUTPUT = ROOT / "frontend/public/assets/monsters"
KINDS = (
    "roaming_melee", "resource_guardian", "ruins_guardian", "forest_stalker",
    "spore_beast", "ironback_brute", "ember_wisp", "ancient_colossus",
)
DIRECTIONS = ("se", "sw", "ne", "nw")
FRAMES = {"idle": 8, "walk": 12, "attack": 10, "hit": 5, "death": 14}
SOURCE_CELL = 160
CELL = 144
GAP = 2
REVISION = "blender-rig-v1"


def map_camera_directions(document: dict, kind: str) -> None:
    """Match Blender camera labels to the isometric map movement directions."""
    if document["meta"].get("directionMapping") == "isometric-v1":
        return
    frames = document["frames"]
    for action, count in FRAMES.items():
        for index in range(count):
            northeast = f"{kind}_{action}_ne_{index:04d}.png"
            southwest = f"{kind}_{action}_sw_{index:04d}.png"
            frames[northeast], frames[southwest] = frames[southwest], frames[northeast]
    document["meta"]["directionMapping"] = "isometric-v1"


def map_existing(kind: str) -> None:
    path = OUTPUT / kind / f"{kind}.atlas.json"
    document = json.loads(path.read_text(encoding="utf8"))
    map_camera_directions(document, kind)
    path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf8")


def pack(kind: str) -> dict[str, int | str]:
    names = [f"{kind}_{action}_{direction}_{index:04d}.png"
             for direction in DIRECTIONS for action, count in FRAMES.items() for index in range(count)]
    missing = [name for name in names if not (TEMP / kind / name).is_file()]
    if missing:
        raise FileNotFoundError(f"{kind}: {len(missing)} missing frames, first: {missing[0]}")
    columns = math.ceil(math.sqrt(len(names)))
    rows = math.ceil(len(names) / columns)
    width = columns * (CELL + GAP)
    height = rows * (CELL + GAP)
    atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    frames = {}
    for position, name in enumerate(names):
        x = position % columns * (CELL + GAP)
        y = position // columns * (CELL + GAP)
        with Image.open(TEMP / kind / name) as image:
            if image.size != (SOURCE_CELL, SOURCE_CELL):
                raise ValueError(f"{name}: unexpected size {image.size}")
            atlas.alpha_composite(image.convert("RGBA").resize((CELL, CELL), Image.Resampling.LANCZOS), (x, y))
        frames[name] = {
            "frame": {"x": x, "y": y, "w": CELL, "h": CELL},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": CELL, "h": CELL},
            "sourceSize": {"w": CELL, "h": CELL},
        }
    folder = OUTPUT / kind
    folder.mkdir(parents=True, exist_ok=True)
    atlas.save(folder / f"{kind}.webp", "WEBP", lossless=True, method=4)
    document = {
        "frames": frames,
        "meta": {
            "app": "Real City Blender monster renderer",
            "version": REVISION,
            "image": f"{kind}.webp",
            "format": "RGBA8888",
            "size": {"w": width, "h": height},
            "scale": "1",
        },
    }
    map_camera_directions(document, kind)
    (folder / f"{kind}.atlas.json").write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    manifest = {
        "kind": "monster",
        "monster_id": kind,
        "anchor": [CELL // 2, round(CELL * .9)],
        "directions": list(DIRECTIONS),
        "render": {"mode": "atlas", "size": [CELL, CELL], "preferredFormat": "webp"},
        "atlas": {"image": f"{kind}.webp", "json": f"{kind}.atlas.json", "revision": REVISION},
        "animations": {
            action: {"type": "sprite", "fps": {"idle": 6, "walk": 10, "attack": 12, "hit": 10, "death": 10}[action],
                     "frames": count, "loop": action in ("idle", "walk"),
                     "framePrefix": f"{kind}_{action}_{{direction}}_"}
            for action, count in FRAMES.items()
        },
        "glb": {"preview": f"{kind}_preview.glb"},
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return {"kind": kind, "frames": len(names), "width": width, "height": height,
            "webp_bytes": (folder / f"{kind}.webp").stat().st_size}


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    relabel = "--map-existing" in args
    for asset_id in ([arg for arg in args if arg != "--map-existing"] or KINDS):
        if asset_id not in KINDS:
            raise ValueError(asset_id)
        if relabel:
            map_existing(asset_id)
            print("mapped", asset_id)
        else:
            print(pack(asset_id))
