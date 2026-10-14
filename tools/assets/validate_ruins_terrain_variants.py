"""Validate capturable ruins terrain variants and build a contact sheet."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_early_housing import glb_document

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend/public/assets/terrain/tiles"
VARIANT_DIR = OUT_DIR / "ruins_variants"
MANIFEST_PATH = VARIANT_DIR / "manifest.json"


def validate():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["size"] == [512, 512]
    assert manifest["anchor"] == [256, 320]
    assert manifest["footprint_pixels"] == 480
    variants = manifest["variants"]
    assert len(variants) == 12

    sheet = Image.new("RGBA", (4 * 256, 3 * 292), (37, 55, 47, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 14) if font_path.is_file() else ImageFont.load_default()
    results = []

    for index, (name, entry) in enumerate(variants.items()):
        for folder in (VARIANT_DIR, OUT_DIR):
            assert (folder / entry["png"]).is_file(), (name, folder / entry["png"])
            assert (folder / entry["glb"]).is_file(), (name, folder / entry["glb"])

        with Image.open(VARIANT_DIR / entry["png"]) as image:
            assert image.mode == "RGBA" and image.size == (512, 512), name
            alpha_box = image.getchannel("A").getbbox()
            assert alpha_box and alpha_box[0] > 0 and alpha_box[1] > 0 and alpha_box[2] < 512 and alpha_box[3] < 512, (name, alpha_box)
            assert image.getpixel((256, 320))[3] > 220, name
            assert abs(alpha_box[0] - 16) <= 3 and abs(alpha_box[2] - 496) <= 3, (name, alpha_box)
            thumb = image.resize((256, 256), Image.Resampling.LANCZOS)
            x = (index % 4) * 256
            y = (index // 4) * 292
            sheet.paste(thumb, (x, y), thumb)
            draw.text((x + 10, y + 260), entry["label"], fill=(255, 255, 255, 255), font=font)

        doc = glb_document(VARIANT_DIR / entry["glb"])
        assert len(doc["scenes"]) == 1, name
        triangles = sum(
            doc["accessors"][primitive["indices"]]["count"] // 3
            for mesh in doc["meshes"]
            for primitive in mesh["primitives"]
        )
        assert triangles == entry["triangles"] and triangles < 8000, (name, triangles, entry["triangles"])
        results.append({"terrain": name, "triangles": triangles, "alpha_bounds": alpha_box})

    roundtrip = json.loads((VARIANT_DIR / "roundtrip-validation.json").read_text())
    assert {entry["terrain"] for entry in roundtrip} == set(variants)
    assert all(entry["nonmanifold_edges"] == 0 for entry in roundtrip)
    assert (VARIANT_DIR / "ruins_variants.blend").stat().st_size > 1000

    sheet.save(VARIANT_DIR / "ruins_variants_contact_sheet.png")
    (VARIANT_DIR / "validation.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps({"validated": len(results), "models": results}, ensure_ascii=False))


if __name__ == "__main__":
    validate()
