"""Validate mountain detail staging assets and build a contact sheet."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_early_housing import glb_document


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend/public/assets/terrain/tiles/mountain_detail_staging"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CONTACT_SHEET_PATH = OUT_DIR / "mountain_detail_contact_sheet.png"
VALIDATION_PATH = OUT_DIR / "validation.json"


def validate():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["size"] == [512, 512]
    assert manifest["anchor"] == [256, 320]
    assert manifest["footprint_pixels"] == 480
    assets = manifest["assets"]
    assert set(assets) == {
        "mountain_detail_ridge",
        "mountain_detail_spire",
        "mountain_detail_snowcap",
        "mine_l01_active_mountain_detail",
    }

    sheet = Image.new("RGBA", (2 * 256, 2 * 292), (37, 55, 47, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 13) if font_path.is_file() else ImageFont.load_default()
    results = []

    for index, (name, entry) in enumerate(assets.items()):
        png_path = OUT_DIR / entry["png"]
        glb_path = OUT_DIR / entry["glb"]
        assert png_path.is_file(), png_path
        assert glb_path.is_file(), glb_path

        with Image.open(png_path) as image:
            assert image.mode == "RGBA" and image.size == (512, 512), name
            alpha_box = image.getchannel("A").getbbox()
            assert alpha_box and alpha_box[0] > 0 and alpha_box[1] > 0 and alpha_box[2] < 512 and alpha_box[3] < 512, (name, alpha_box)
            assert image.getpixel((256, 320))[3] > 220, name
            thumb = image.resize((256, 256), Image.Resampling.LANCZOS)
            x = (index % 2) * 256
            y = (index // 2) * 292
            sheet.alpha_composite(thumb, (x, y))
            draw.text((x + 8, y + 260), name, fill=(255, 255, 255, 255), font=font)

        doc = glb_document(glb_path)
        assert len(doc["scenes"]) == 1, name
        triangles = sum(
            doc["accessors"][primitive["indices"]]["count"] // 3
            for mesh in doc["meshes"]
            for primitive in mesh["primitives"]
        )
        assert triangles == entry["triangles"], (name, triangles, entry["triangles"])
        assert triangles < 8000, (name, triangles)
        results.append({"asset": name, "triangles": triangles, "alpha_bounds": alpha_box})

    roundtrip = json.loads((OUT_DIR / "roundtrip-validation.json").read_text(encoding="utf-8"))
    assert {entry["asset"] for entry in roundtrip} == set(assets)
    assert all(entry["loose_vertices"] == 0 for entry in roundtrip)
    assert (OUT_DIR / manifest["source"]).stat().st_size > 1000

    sheet.save(CONTACT_SHEET_PATH)
    VALIDATION_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"validated": len(results), "models": results}, ensure_ascii=False))


if __name__ == "__main__":
    validate()
