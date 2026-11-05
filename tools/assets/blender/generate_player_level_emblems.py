"""Render the 15 player progression emblems at three UI sizes with Blender."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEVELS = json.loads((ROOT / "data/player/levels.json").read_text(encoding="utf-8"))
SIZES = {"small": 32, "medium": 64, "large": 128}
PREVIEW_LEVELS = (1, 8, 15)


def _dry_run(mode: str) -> None:
    levels = [entry for entry in LEVELS if mode == "full" or entry["level"] in PREVIEW_LEVELS]
    print(json.dumps({
        "asset_id": "player_level_emblems",
        "mode": mode,
        "levels": [{"level": item["level"], "title": item["title"]} for item in levels],
        "variants_per_level": list(SIZES),
        "outputs": len(levels) * (len(SIZES) if mode == "full" else 1),
        "runtime": "frontend/public/assets/player-levels/",
        "source": "tools/assets/blender/source/player_level_emblems.blend",
    }, ensure_ascii=False, indent=2))


def _labeled_contact_sheet(image_paths: list[Path], output_path: Path, levels: list[int], columns: int = 5) -> None:
    from PIL import Image, ImageDraw

    cell, label_height = 160, 24
    rows = (len(image_paths) + columns - 1) // columns
    sheet = Image.new("RGBA", (cell * columns, (cell + label_height) * rows), (235, 238, 232, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (path, level) in enumerate(zip(image_paths, levels)):
        image = Image.open(path).convert("RGBA")
        x = (index % columns) * cell
        y = (index // columns) * (cell + label_height)
        sheet.alpha_composite(image, (x + (cell - image.width) // 2, y + (cell - image.height) // 2))
        draw.text((x + 8, y + cell + 5), f"LEVEL {level:02d}", fill=(44, 48, 42, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, optimize=True)


def generate(mode: str = "full") -> dict:
    import bpy
    from PIL import Image

    from tools.assets.blender.real_city import export, geometry, materials, scene
    from tools.assets.blender.real_city.components.player_level_emblems import add_level_emblem

    if mode not in {"preview", "full"}:
        raise ValueError("mode must be preview or full")

    original_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    asset_scene = bpy.data.scenes.get("RC_Player_Level_Emblems") or bpy.data.scenes.new("RC_Player_Level_Emblems")
    if bpy.context.window:
        bpy.context.window.scene = asset_scene

    # Keep the user's existing scene intact; this scene is a self-contained icon studio.
    for obj in list(asset_scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(asset_scene.collection.children):
        asset_scene.collection.children.unlink(collection)
        bpy.data.collections.remove(collection)
    asset_scene.render.film_transparent = True
    asset_scene.render.image_settings.file_format = "PNG"
    asset_scene.render.image_settings.color_mode = "RGBA"
    asset_scene.render.resolution_percentage = 100
    engine_ids = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    asset_scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_ids else engine_ids[0]
    # Preserve the host's supported color transform. This system build exposes
    # only Standard because its OCIO 2.4 library cannot load the installed 2.5 config.
    asset_scene.render.image_settings.color_depth = "8"
    asset_scene.render.resolution_x = 512
    asset_scene.render.resolution_y = 512
    asset_scene.render.filepath = "//"
    asset_scene.render.resolution_percentage = 100

    camera_data = bpy.data.cameras.new("CAM_Player_Level_Emblems")
    camera = bpy.data.objects.new("CAM_Player_Level_Emblems", camera_data)
    asset_scene.collection.objects.link(camera)
    camera.location = (3.0, -6.4, 3.25)
    camera.rotation_euler = (math.radians(90), 0, math.radians(25))
    # Point camera at the medallion and retain a slightly elevated strategy-art view.
    from mathutils import Vector
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.45
    asset_scene.camera = camera

    key_data = bpy.data.lights.new("LGT_Emblem_Key", "AREA")
    key = bpy.data.objects.new("LGT_Emblem_Key", key_data)
    asset_scene.collection.objects.link(key)
    key.location = (-3.5, -4.5, 5.0)
    key_data.energy = 520
    key_data.shape = "DISK"
    key_data.size = 3.4
    key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat("-Z", "Y").to_euler()

    fill_data = bpy.data.lights.new("LGT_Emblem_Fill", "AREA")
    fill = bpy.data.objects.new("LGT_Emblem_Fill", fill_data)
    asset_scene.collection.objects.link(fill)
    fill.location = (3.8, -2.0, 1.2)
    fill_data.energy = 180
    fill_data.size = 2.8
    fill.rotation_euler = (Vector((0, 0, 0)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.get("WLD_Emblem_Studio") or bpy.data.worlds.new("WLD_Emblem_Studio")
    world.use_nodes = True
    background = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs[0].default_value = (0.52, 0.65, 0.72, 1)
    background.inputs[1].default_value = 0.35
    asset_scene.world = world

    mats = materials.create_palette("MAT_Player_Emblems", overrides={
        "roof_gold": (0.91, 0.62, 0.20), "copper": (0.76, 0.34, 0.13),
        "stone_block": (0.78, 0.74, 0.61), "whitewash": (0.94, 0.86, 0.68),
        "roof_coral": (0.90, 0.34, 0.23), "roof_red": (0.76, 0.19, 0.16),
        "roof_teal": (0.10, 0.56, 0.61), "roof_blue": (0.20, 0.42, 0.78),
        "roof_green": (0.23, 0.56, 0.29), "grass_bright": (0.30, 0.72, 0.32),
        "amethyst": (0.62, 0.35, 0.91), "star_glass": (0.72, 0.44, 0.98),
        "window_warm": (1.00, 0.71, 0.23), "glass_cyan": (0.30, 0.86, 0.94),
    })

    levels_to_build = [item for item in LEVELS if mode == "full" or item["level"] in PREVIEW_LEVELS]
    collections = {}
    for item in levels_to_build:
        level = int(item["level"])
        collection = geometry.create_collection(f"player_level_{level:02d}_{item['title'].replace(' ', '_').lower()}", parent=asset_scene.collection)
        add_level_emblem(collection, mats, level)
        for obj in collection.all_objects:
            obj["real_city_asset"] = "player_level_emblems"
            obj["real_city_level"] = level
            obj["real_city_title"] = item["title"]
            obj["style_profile"] = "aeolian_fantasy_midpoly"
        collections[level] = collection

    out = ROOT / ("/tmp/real-city-level-emblems-preview" if mode == "preview" else "frontend/public/assets/player-levels")
    out.mkdir(parents=True, exist_ok=True)
    preview_files = []
    records = []
    with tempfile.TemporaryDirectory(prefix="real-city-level-emblems-") as tmpdir:
        for item in levels_to_build:
            level = int(item["level"])
            collection = collections[level]
            for candidate_level, candidate in collections.items():
                candidate.hide_render = candidate_level != level
                candidate.hide_viewport = candidate_level != level
            asset_scene.render.resolution_x = asset_scene.render.resolution_y = 512
            master = Path(tmpdir) / f"level-{level:02d}.png"
            asset_scene.render.filepath = str(master)
            bpy.ops.render.render(write_still=True, scene=asset_scene.name)
            image = Image.open(master).convert("RGBA")
            alpha = image.getchannel("A")
            bounds = alpha.getbbox()
            triangle_count = geometry.collection_triangle_count(collection)
            if not bounds or triangle_count < 250:
                raise RuntimeError(f"level {level}: emblem render or geometry is empty ({triangle_count} triangles)")
            variants = {}
            sizes = SIZES if mode == "full" else {"preview": 128}
            for size_name, px in sizes.items():
                target_dir = out / f"level-{level:02d}"
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / (f"{size_name}.png" if mode == "full" else "preview.png")
                image.resize((px, px), Image.Resampling.LANCZOS).save(target, optimize=True)
                variants[size_name] = {"path": str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target), "size": [px, px]}
                if mode == "preview": preview_files.append(target)
            records.append({"level": level, "title": item["title"], "triangles": triangle_count, "alpha_bounds_512": list(bounds), "variants": variants})

    # Leave the representative mid-progression badge visible for the required live viewport review.
    for candidate_level, candidate in collections.items():
        candidate.hide_render = candidate_level != (8 if 8 in collections else next(iter(collections)))
        candidate.hide_viewport = candidate_level != (8 if 8 in collections else next(iter(collections)))

    if mode == "preview":
        _labeled_contact_sheet(preview_files, out / "player-level-emblems-preview-contact-sheet.png", [item["level"] for item in levels_to_build], columns=3)
        if bpy.context.window:
            bpy.context.window.scene = asset_scene
    else:
        source_path = ROOT / "tools/assets/blender/source/player_level_emblems.blend"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.data.libraries.write(str(source_path), {asset_scene}, fake_user=True)
        manifest_path = out / "manifest.json"
        manifest_path.write_text(json.dumps({
            "asset_id": "player_level_emblems",
            "style_profile": "aeolian_fantasy_midpoly",
            "camera": {"type": "orthographic", "view": "front_three_quarter", "transparent": True},
            "sizes": SIZES,
            "source_blend": str(source_path.relative_to(ROOT)),
            "levels": records,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        contact_sources = [out / f"level-{item['level']:02d}" / "large.png" for item in levels_to_build]
        _labeled_contact_sheet(contact_sources, out / "player-level-emblems-contact-sheet.png", [item["level"] for item in levels_to_build])
        if bpy.context.window and original_scene:
            bpy.context.window.scene = original_scene

    return {"mode": mode, "scene": asset_scene.name, "levels": records, "output": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("dry-run", "preview", "full"), default="dry-run")
    args = parser.parse_args()
    if args.mode == "dry-run":
        _dry_run(args.mode)
    else:
        print(json.dumps(generate(args.mode), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
