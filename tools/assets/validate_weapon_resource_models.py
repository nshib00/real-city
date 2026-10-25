"""Validate nine Blender weapon resources and produce full-size/small-icon review sheets."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from validate_building_ground import read_glb
from validate_resource_models import catalog
from validate_town_halls import validate_topology

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "frontend/public/assets/resources/icons"


def validate():
    weapons = {item["id"]: item for item in catalog() if item["category"] == "weapons"}
    if len(weapons) != 9:
        raise AssertionError(f"Expected nine weapon resources, found {len(weapons)}")
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    entries = {item["id"]: item for item in manifest["resources"]}
    if not weapons.keys() <= entries.keys():
        raise AssertionError(f"Manifest misses: {sorted(weapons.keys() - entries.keys())}")
    report = json.loads((OUTPUT / "weapon-generation-report.json").read_text(encoding="utf-8"))
    built = {item["id"]: item for item in report}
    if built.keys() != weapons.keys():
        raise AssertionError(f"Generation report IDs: {sorted(built)}")
    if (OUTPUT / "weapon_resources.blend").stat().st_size < 1000:
        raise AssertionError("Editable Blender source is missing")

    full = Image.new("RGB", (3 * 256, 3 * 290), "#233b34")
    full_draw = ImageDraw.Draw(full)
    small = Image.new("RGB", (3 * 256, 3 * 124), "#233b34")
    small_draw = ImageDraw.Draw(small)
    results = []
    for index, (rid, item) in enumerate(weapons.items()):
        entry = entries[rid]
        if (entry["name"], entry["category"], entry["file"], entry["model"]) != (
            item["name"], "weapons", rid + ".png", rid + ".glb"
        ):
            raise AssertionError(f"Catalog/manifest mismatch: {rid}")
        glb_path = OUTPUT / entry["model"]
        image_path = OUTPUT / entry["file"]
        doc, _ = read_glb(glb_path)
        validate_topology(glb_path, doc)
        triangles = sum(doc["accessors"][primitive["indices"]]["count"] // 3
                        for mesh in doc["meshes"] for primitive in mesh["primitives"])
        if not 300 <= triangles <= 6000 or triangles != entry["triangles"] or triangles != built[rid]["triangles"]:
            raise AssertionError(f"Triangle count/budget mismatch: {rid} ({triangles})")
        if len(doc["scenes"]) != 1 or not doc.get("materials"):
            raise AssertionError(f"Missing GLB scene/materials: {rid}")
        for node in doc["nodes"]:
            if node.get("translation", [0, 0, 0]) != [0, 0, 0] or node.get("scale", [1, 1, 1]) != [1, 1, 1]:
                raise AssertionError(f"Unapplied transform: {rid}")
        with Image.open(image_path) as source:
            if source.mode != "RGBA" or source.size != (256, 256):
                raise AssertionError(f"PNG format: {rid}")
            bbox = source.getchannel("A").getbbox()
            if not bbox or min(bbox[:2]) < 10 or max(bbox[2:]) > 246:
                raise AssertionError(f"Bad alpha bounds: {rid} {bbox}")
            if max(bbox[2] - bbox[0], bbox[3] - bbox[1]) < 190:
                raise AssertionError(f"Icon too small: {rid} {bbox}")
            if source.getpixel((0, 0))[3] != 0:
                raise AssertionError(f"Background is not transparent: {rid}")
            icon = source.copy()
        x, y = (index % 3) * 256, (index // 3) * 290
        full.paste(icon, (x, y), icon)
        full_draw.text((x + 8, y + 256), rid, fill="white")
        x, y = (index % 3) * 256, (index // 3) * 124
        for size, offset in ((24, 14), (32, 72), (48, 140)):
            thumb = icon.resize((size, size), Image.Resampling.LANCZOS)
            small.paste(thumb, (x + offset, y + 8), thumb)
        small_draw.text((x + 8, y + 75), rid, fill="white")
        results.append({"id": rid, "triangles": triangles, "alpha_bounds": bbox,
                        "glb_bytes": glb_path.stat().st_size})
    full.save(OUTPUT / "weapon_icons_contact_sheet.png")
    small.save(OUTPUT / "weapon_icons_small_review.png")
    (OUTPUT / "weapon-validation-report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    runtime_check = """
import { readFileSync } from 'node:fs'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
for (const id of JSON.parse(process.argv[1])) {
  const file = readFileSync(`public/assets/resources/icons/${id}.glb`)
  const data = file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength)
  const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(data, '', resolve, reject))
  let meshes = 0
  gltf.scene.traverse((object) => { if (object.isMesh) meshes++ })
  if (meshes === 0) throw new Error(`${id}: empty GLB`)
}
"""
    subprocess.run(["node", "--input-type=module", "-e", runtime_check, json.dumps(list(weapons))],
                   cwd=ROOT / "frontend", check=True, capture_output=True, text=True)
    print(json.dumps({"weapons": len(results), "max_triangles": max(item["triangles"] for item in results),
                      "glb_bytes": sum(item["glb_bytes"] for item in results)}, ensure_ascii=False))


if __name__ == "__main__":
    validate()
