"""Validate massive mountain detail staging assets and build a contact sheet."""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_early_housing import glb_document


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend/public/assets/terrain/tiles/mountain_detail_staging"
MANIFEST_PATH = OUT_DIR / "manifest_massive.json"
CONTACT_SHEET_PATH = OUT_DIR / "mountain_detail_massive_contact_sheet.png"
VALIDATION_PATH = OUT_DIR / "validation_massive.json"

MOUNTAINS = {
    "mountain_detail_ridge_massive",
    "mountain_detail_spire_massive",
    "mountain_detail_snowcap_massive",
}
MINE_ASSETS = {
    f"mine_l{level:02d}_{state}_mountain_detail"
    for level in range(1, 13)
    for state in ("active", "construction", "damaged")
    if not (level == 1 and state == "active")
}
EXPECTED = MOUNTAINS | MINE_ASSETS


def validate():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["size"] == [512, 512]
    assert manifest["anchor"] == [256, 320]
    assert manifest["footprint_pixels"] == 480
    assets = manifest["assets"]
    assert set(assets) == EXPECTED

    columns = 6
    rows = math.ceil(len(assets) / columns)
    sheet = Image.new("RGBA", (columns * 220, rows * 252), (37, 55, 47, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 11) if font_path.is_file() else ImageFont.load_default()
    results = []

    ordered = list(manifest["assets"].keys())
    for index, name in enumerate(ordered):
        entry = assets[name]
        png_path = OUT_DIR / entry["png"]
        glb_path = OUT_DIR / entry["glb"]
        assert png_path.is_file(), png_path
        assert glb_path.is_file(), glb_path

        with Image.open(png_path) as image:
            assert image.mode == "RGBA" and image.size == (512, 512), name
            alpha_box = image.getchannel("A").getbbox()
            assert alpha_box and alpha_box[0] >= 0 and alpha_box[1] >= 0 and alpha_box[2] <= 512 and alpha_box[3] <= 512, (name, alpha_box)
            assert image.getpixel((256, 320))[3] > 220, name
            thumb = image.resize((220, 220), Image.Resampling.LANCZOS)
            x = (index % columns) * 220
            y = (index // columns) * 252
            sheet.alpha_composite(thumb, (x, y))
            draw.text((x + 5, y + 224), name, fill=(255, 255, 255, 255), font=font)

        doc = glb_document(glb_path)
        assert len(doc["scenes"]) == 1, name
        triangles = sum(
            doc["accessors"][primitive["indices"]]["count"] // 3
            for mesh in doc["meshes"]
            for primitive in mesh["primitives"]
        )
        assert triangles == entry["triangles"], (name, triangles, entry["triangles"])
        assert 1200 <= triangles <= 12000, (name, triangles)
        results.append({"asset": name, "triangles": triangles, "alpha_bounds": alpha_box})

    roundtrip = json.loads((OUT_DIR / "roundtrip-validation-massive.json").read_text(encoding="utf-8"))
    assert {entry["asset"] for entry in roundtrip} == EXPECTED
    assert all(entry["loose_vertices"] == 0 for entry in roundtrip)
    assert (OUT_DIR / manifest["source"]).stat().st_size > 1000

    sheet.save(CONTACT_SHEET_PATH)
    VALIDATION_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"validated": len(results), "triangles_min": min(r["triangles"] for r in results), "triangles_max": max(r["triangles"] for r in results)}, ensure_ascii=False))


if __name__ == "__main__":
    validate()
