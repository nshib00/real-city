"""Validate exported housing assets and make review contact sheets."""

import argparse
import hashlib
import json
import struct
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"dugout": 5, "wood_house": 3}
STATES = ("active", "construction", "damaged")


def glb_document(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data)
    assert (magic, version, length) == (b"glTF", 2, len(data)), path
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    assert chunk_type == 0x4E4F534A, path
    document = json.loads(data[20:20 + chunk_length])
    assert document.get("meshes"), path
    return document


def validate(backup=None):
    summary = []
    sheet = Image.new("RGB", (768, 8 * 214), "#283330")
    active_sheet = Image.new("RGB", (1024, 428), "#283330")
    row = 0
    for kind, levels in KINDS.items():
        folder = ROOT / "frontend/src/assets/buildings/housing" / kind
        report = json.loads((folder / "regeneration-report.json").read_text())
        revision = folder / "state-revision-report.json"
        if revision.exists():
            report["assets"].update(json.loads(revision.read_text()))
        assert len(report["assets"]) >= levels * 3
        assert (folder / f"{kind}_levels.blend").stat().st_size > 1000
        glb_document(folder / f"{kind}_levels.glb")
        for level in range(1, levels + 1):
            hashes = set()
            for col, state in enumerate(STATES):
                name = f"{kind}_l{level:02d}_{state}"
                doc = glb_document(folder / (name + ".glb"))
                tris = sum(doc["accessors"][primitive["indices"]]["count"] // 3
                           for mesh in doc["meshes"] for primitive in mesh["primitives"])
                assert tris == report["assets"][name]["triangles"], (name, tris)
                for node in doc["nodes"]:
                    assert node.get("translation", [0, 0, 0]) == [0, 0, 0], name
                    assert node.get("scale", [1, 1, 1]) == [1, 1, 1], name
                for mesh in doc["meshes"]:
                    for primitive in mesh["primitives"]:
                        positions = doc["accessors"][primitive["attributes"]["POSITION"]]
                        for axis in (0, 2):
                            assert positions["min"][axis] >= -1.81 and positions["max"][axis] <= 1.81, name
                path = ROOT / "frontend/public/assets/buildings/housing" / kind / (name + ".png")
                with Image.open(path) as image:
                    assert image.size == (512, 384) and image.mode == "RGBA", name
                    alpha = image.getchannel("A")
                    bounds = alpha.getbbox()
                    assert bounds and bounds[0] > 0 and bounds[1] > 0 and bounds[2] < 512 and bounds[3] < 384, (name, bounds)
                    assert sum(v > 0 for v in alpha.getdata()) > 15000, name
                    hashes.add(hashlib.sha256(image.tobytes()).hexdigest())
                    thumb = image.resize((256, 192), Image.Resampling.LANCZOS)
                    sheet.paste(thumb, (col * 256, row * 214), thumb)
                    ImageDraw.Draw(sheet).text((col * 256 + 12, row * 214 + 193), name, fill="white")
                    if state == "active":
                        x, y = (row % 4) * 256, (row // 4) * 214
                        active_sheet.paste(thumb, (x, y), thumb)
                        ImageDraw.Draw(active_sheet).text((x + 12, y + 193), name, fill="white")
                summary.append({"name": name, "triangles": tris, "alpha_bounds": bounds})
            assert len(hashes) == 3, (kind, level, "states are identical")
            row += 1
    if backup:
        checked = 0
        with tarfile.open(backup) as archive:
            for item in archive.getmembers():
                if item.isfile() and any(f"wood_house_l{level:02d}_active." in item.name for level in (4, 5, 6)):
                    assert archive.extractfile(item).read() == (ROOT / item.name).read_bytes(), item.name
                    checked += 1
        assert checked == 6, checked
    sheet.save("/tmp/real-city-housing-all-states.png")
    active_sheet.save(ROOT / "frontend/public/assets/buildings/housing/housing-levels-preview.png")
    print(json.dumps({"validated": len(summary), "preserved_files": 6 if backup else None, "assets": summary}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", type=Path)
    validate(parser.parse_args().backup)
