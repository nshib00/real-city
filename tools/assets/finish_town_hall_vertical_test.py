#!/usr/bin/env python3
"""Validate and index the isolated active town hall study, levels 1-15."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.assets.blender.real_city.export import make_contact_sheet  # noqa: E402


OUTPUT = ROOT / "tools/assets/staging/town_hall_vertical_test"


def main():
    report = json.loads((OUTPUT / "generation-report.json").read_text(encoding="utf-8"))
    items = sorted(report["items"], key=lambda item: item["level"])
    assert [item["level"] for item in items] == list(range(1, 16))
    heights = []
    manifest_items = []
    for item in items:
        stem = item["id"]
        png = OUTPUT / f"{stem}.png"
        blend = OUTPUT / f"{stem}.blend"
        assert png.is_file() and blend.is_file(), stem
        with Image.open(png) as image:
            assert image.size == (512, 384), (stem, image.size)
            assert image.mode == "RGBA", (stem, image.mode)
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            assert bbox and bbox[0] > 4 and bbox[1] > 4 and bbox[2] < 508 and bbox[3] < 380, (stem, bbox)
        lods = []
        for lod in ("LOD0", "LOD1", "LOD2"):
            glb = OUTPUT / f"{stem}_{lod}.glb"
            assert glb.is_file() and glb.stat().st_size > 1000, glb
            with glb.open("rb") as handle:
                assert handle.read(4) == b"glTF", glb
            lods.append(glb.name)
        lod_triangles = [lod["triangles"] for lod in item["lods"]]
        assert lod_triangles[0] > lod_triangles[1] > lod_triangles[2] > 0, (stem, lod_triangles)
        xy = item["bounds"][:2]
        assert all(abs(number) <= 1.801 for bounds in xy for number in bounds), (stem, xy)
        heights.append(item["bounds"][2][1])
        manifest_items.append({"level": item["level"], "state": "active", "png": png.name,
                               "blend": blend.name, "lods": lods, "triangles": item["triangles"],
                               "height": heights[-1], "roof_stage": item["roof_stage"]})
    assert all(next_height > height for height, next_height in zip(heights, heights[1:])), heights
    with Image.open(ROOT / "frontend/public/assets/buildings/center/town_hall/town_hall_l01_active.png") as old:
        with Image.open(OUTPUT / "town_hall_l01_active.png") as new:
            assert ImageChops.difference(old.convert("RGBA"), new.convert("RGBA")).getbbox() is None
    manifest = {"asset_id": "town_hall", "variant": "vertical_test", "runtime": False,
                "states": ["active"], "levels": list(range(1, 16)),
                "sprite": {"size": [512, 384], "anchor": [256, 292]},
                "source": report["source"], "generator": report["generator"],
                "items": manifest_items}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    make_contact_sheet([OUTPUT / item["png"] for item in manifest_items],
                       OUTPUT / "levels-contact-sheet.png", columns=5)
    print(f"validated {len(items)} active models; heights {heights[0]:.2f}–{heights[-1]:.2f}; "
          f"contact sheet: {OUTPUT / 'levels-contact-sheet.png'}")


if __name__ == "__main__":
    main()
