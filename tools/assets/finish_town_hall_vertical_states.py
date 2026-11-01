#!/usr/bin/env python3
"""Validate and install the 1-15 town hall study, preserving the old family archive."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/assets"))

from validate_building_ground import ground_signature, sprite_alignment  # noqa: E402
from blender.real_city.export import make_contact_sheet  # noqa: E402

STAGING = ROOT / "tools/assets/staging/town_hall_vertical_test"
RUNTIME = ROOT / "frontend/public/assets/buildings/center/town_hall"
BACKUP = ROOT / "tools/assets/backups/town_hall_before_vertical_2026-10-26.tar.gz"


def main() -> None:
    assert BACKUP.is_file() and BACKUP.stat().st_size > 1_000_000, "Old town halls must be backed up first"
    active = json.loads((STAGING / "generation-report.json").read_text(encoding="utf-8"))["items"]
    states = json.loads((STAGING / "states-generation-report.json").read_text(encoding="utf-8"))["items"]
    by_id = {item["id"]: item for item in active + states}
    expected = [f"town_hall_l{level:02d}_{state}"
                for level in range(1, 16) for state in ("active", "construction", "damaged")]
    assert set(by_id) == set(expected), (len(by_id), len(expected))
    items = []
    for level in range(1, 16):
        active_name = f"town_hall_l{level:02d}_active"
        active_ground = ground_signature(STAGING / f"{active_name}_LOD0.glb")
        for state in ("active", "construction", "damaged"):
            name = f"town_hall_l{level:02d}_{state}"
            record = by_id[name]
            assert record["triangles"] > 1000, name
            assert all(abs(value) <= 1.801 for axis in record["bounds"][:2] for value in axis), name
            png = STAGING / f"{name}.png"
            blend = STAGING / f"{name}.blend"
            assert blend.is_file() and blend.stat().st_size > 1000, blend
            with Image.open(png) as image:
                assert image.size == (512, 384) and image.mode == "RGBA", name
                box = image.getchannel("A").getbbox()
                assert box and box[0] > 0 and box[1] > 0 and box[2] < 512 and box[3] < 384, (name, box)
            lods = []
            counts = []
            for lod in ("LOD0", "LOD1", "LOD2"):
                glb = STAGING / f"{name}_{lod}.glb"
                assert glb.is_file() and glb.stat().st_size > 1000, glb
                with glb.open("rb") as handle:
                    assert handle.read(4) == b"glTF", glb
                value = next(entry for entry in record["lods"] if entry["name"] == lod)
                counts.append(value["triangles"])
                lods.append({"name": lod, "ratio": value["ratio"],
                             "glb": str((RUNTIME / glb.name).relative_to(ROOT)),
                             "triangles": value["triangles"]})
            assert counts[0] > counts[1] > counts[2] > 0, (name, counts)
            if state != "active":
                assert record["structural_edits"] > 15, name
                assert ground_signature(STAGING / f"{name}_LOD0.glb") == active_ground, name
                assert sprite_alignment(STAGING / f"{active_name}.png", png), name
            for source in (png, blend, *(STAGING / f"{name}_{lod}.glb" for lod in ("LOD0", "LOD1", "LOD2"))):
                shutil.copy2(source, RUNTIME / source.name)
            items.append({"id": name, "level": level, "state": state,
                          "png": str((RUNTIME / png.name).relative_to(ROOT)),
                          "glb": lods[0]["glb"], "blend": str((RUNTIME / blend.name).relative_to(ROOT)),
                          "lods": lods, "triangles": record["triangles"], "bounds": record["bounds"]})
    manifest = {
        "asset_id": "town_hall", "display_name": "Ратуша", "category": "center",
        "levels": list(range(1, 16)), "states": ["active", "construction", "damaged"],
        "sprite": {"size": [512, 384], "anchor": [256, 292]},
        "runtime_levels": list(range(1, 16)), "playable_levels": list(range(1, 11)),
        "source_blends": [item["blend"] for item in items],
        "material_map": {"wood": "walls and beams", "stone": "foundation and masonry",
                         "brick": "late facade", "windleaf": "early roof"},
        "lod_policy": {"chain": [{"name": "LOD0"}, {"name": "LOD1"}, {"name": "LOD2"}]},
        "generator": "tools/assets/blender/build_town_hall_vertical_states.py",
        "backup": str(BACKUP.relative_to(ROOT)),
        "items": items,
    }
    (RUNTIME / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    make_contact_sheet([RUNTIME / f"{name}.png" for name in expected],
                       RUNTIME / "vertical-state-review.png", columns=3)
    print(f"Installed {len(items)} town hall variants; backup {BACKUP}")


if __name__ == "__main__":
    main()
