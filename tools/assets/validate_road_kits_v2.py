"""Check complete road-kit exports and their shared open-port contract."""

import json
from collections import Counter
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "frontend/public/assets/buildings/roads"
KITS = ("ground_road", "common_road", "paved_road")
SHAPES = {
    "single": "", "end_n": "n", "end_e": "e", "end_s": "s", "end_w": "w",
    "straight_ns": "ns", "straight_ew": "ew", "corner_ne": "ne", "corner_es": "es",
    "corner_sw": "sw", "corner_wn": "wn", "t_nes": "nes", "t_esw": "esw",
    "t_swn": "swn", "t_wne": "wne", "cross": "nesw",
}
STATES = ("active", "construction", "damaged", "ruined")


def glb_surface_bounds(path):
    data = path.read_bytes()
    assert data[:4] == b"glTF" and len(data) == struct.unpack_from("<I", data, 8)[0], path
    json_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    node = next(node for node in document["nodes"] if node["name"].startswith("SM_road_connected_surface"))
    mesh = document["meshes"][node["mesh"]]
    accessor = document["accessors"][mesh["primitives"][0]["attributes"]["POSITION"]]
    view = document["bufferViews"][accessor["bufferView"]]
    start = 20 + json_length + 8 + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", 12)
    positions = [tuple(round(v, 3) for v in struct.unpack_from("<3f", data, start + i * stride))
                 for i in range(accessor["count"])]
    return accessor["min"], accessor["max"], Counter(positions)


def validate(root):
    total = 0
    for kit in KITS:
        directory = root / kit
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        assert set(manifest["shapes"]) == set(SHAPES)
        assert set(manifest["states"]) == set(STATES)
        assert manifest["size"] == [512, 512] and manifest["anchor"] == [256, 320]
        assert manifest["footprint"] == 3.6
        assert manifest["port"] == {"width": 3.6, "height": 0.055}
        assert len(manifest["assets"]) == 64
        sheet = Image.new("RGB", (16 * 128, 4 * 160), (47, 52, 48))
        draw = ImageDraw.Draw(sheet)
        for col, (shape, dirs) in enumerate(SHAPES.items()):
            for row, state in enumerate(STATES):
                name = f"{kit}_{shape}_{state}"
                entry = manifest["assets"][name]
                assert entry["shape"] == shape and entry["state"] == state
                assert 0 < entry["triangles"] < 4500, name
                image = Image.open(directory / entry["png"]).convert("RGBA")
                assert image.size == (512, 512), name
                assert image.getchannel("A").getbbox(), name
                low, high, positions = glb_surface_bounds(directory / entry["glb"])
                # The closed eight-corner box spans the *entire* tile for every mask.
                # glTF duplicates corners for each face normal (24 exported vertices).
                # Thus any adjacent pair, including the four inner corners of a 2x2,
                # meets with no uncovered terrain between their surfaces.
                assert len(positions) == 8 and set(positions.values()) == {3}, (name, positions)
                expected_corners = {(x, y, z) for x in (-1.8, 1.8)
                                    for y in (0.028, 0.055) for z in (-1.8, 1.8)}
                assert set(positions) == expected_corners, (name, positions)
                assert abs(low[0] + 1.8) < 0.005 and abs(high[0] - 1.8) < 0.005, name
                assert abs(low[2] + 1.8) < 0.005 and abs(high[2] - 1.8) < 0.005, name
                assert abs(high[1] - 0.055) < 0.005, (name, high[1])
                thumb = image.resize((128, 128), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (col * 128, row * 160), thumb)
                draw.text((col * 128 + 2, row * 160 + 132), f"{shape} {state[:3]}", fill=(240, 240, 220))
                total += 1
        sheet.save(directory / "road_v2_contact_sheet.png")
        print("VALID", kit, len(manifest["assets"]))
    assert total == 64 * len(KITS)
    print("ROAD_KITS_OK", total)


if __name__ == "__main__":
    validate(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
