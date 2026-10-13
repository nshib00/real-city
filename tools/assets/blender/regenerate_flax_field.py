"""Generate runtime flax field GLB/PNG assets.

This production fallback writes valid GLB meshes, isometric PNG sprites,
manifest, generation report and a review sheet for levels 1-3 when Blender MCP
is not available.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import regenerate_windleaf_beds as base


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "fields" / "flax_field"
LOG_PATH = Path("/tmp/real-city-flax-field-generation.log")
PNG_SIZE = base.PNG_SIZE
ANCHOR = base.ANCHOR

MATERIALS = {
    **base.MATERIALS,
    "flax_soil": (0.49, 0.29, 0.14, 1.0),
    "flax_soil_light": (0.70, 0.47, 0.25, 1.0),
    "flax_stem": (0.55, 0.78, 0.58, 1.0),
    "flax_stem_dark": (0.32, 0.57, 0.46, 1.0),
    "flax_stem_light": (0.73, 0.90, 0.73, 1.0),
    "flax_bloom": (0.56, 0.73, 0.96, 1.0),
    "flax_bloom_light": (0.76, 0.88, 1.0, 1.0),
    "dry_flax": (0.86, 0.70, 0.38, 1.0),
    "dry_flax_light": (0.96, 0.84, 0.55, 1.0),
    "quality_flax": (0.96, 0.90, 0.64, 1.0),
    "quality_blue": (0.45, 0.82, 0.98, 1.0),
    "cloth_blue": (0.34, 0.55, 0.72, 1.0),
    "marker_blue": (0.38, 0.68, 0.92, 1.0),
    "rope": (0.72, 0.56, 0.32, 1.0),
}
base.MATERIALS = MATERIALS
base.OUT_DIR = OUT_DIR
base.padded = lambda data: data + b" " * ((4 - len(data) % 4) % 4)


def add_plot(meshes, prefix, level):
    base.add_box(meshes, prefix + "_terrain_grass_tile", "grass", (0, 0, -0.015), (3.6, 3.6, 0.03))
    base.add_box(meshes, prefix + "_flax_plot", "flax_soil", (0, 0, 0.10), (2.70, 1.88, 0.14))
    base.add_box(meshes, prefix + "_raised_bed", "flax_soil_light", (-0.04, -0.02, 0.19), (2.30, 1.42, 0.06))

    for y in (-0.50, -0.18, 0.14, 0.46):
        base.add_box(meshes, prefix + "_furrow", "earth_dark", (-0.04, y, 0.25), (2.18, 0.045, 0.032))

    rail = "wood" if level == 1 else "plank"
    rail_light = "wood_cut" if level == 1 else "plank_light"
    rail_h = 0.18 + level * 0.04
    for center, size, yaw in (
        ((0, -1.05, rail_h / 2), (3.02, 0.16, rail_h), 0.01),
        ((0, 1.05, rail_h / 2), (3.02, 0.16, rail_h), -0.01),
        ((-1.50, 0, rail_h / 2), (0.16, 2.08, rail_h), -0.02),
        ((1.50, 0, rail_h / 2), (0.16, 2.08, rail_h), 0.02),
    ):
        base.add_box(meshes, prefix + "_border", rail, center, size, yaw=yaw)
    for x in (-1.42, 1.42):
        for y in (-1.02, 1.02):
            post_h = 0.44 + level * 0.08
            base.add_box(meshes, prefix + "_corner_post", "wood_dark", (x, y, post_h / 2), (0.16, 0.16, post_h), yaw=0.10)
            base.add_box(meshes, prefix + "_corner_cap", rail_light, (x, y, post_h + 0.035), (0.22, 0.22, 0.07), yaw=0.16)

    if level >= 2:
        for y in (-0.36, 0.30):
            base.add_rope(meshes, prefix + "_tie_rope", (-1.12, y, 0.55), (1.12, y, 0.55), thickness=0.034)
        add_drying_rack(meshes, prefix + "_small_rack", (0.98, -0.58, 0.30), 0.82)
    if level >= 3:
        add_drying_rack(meshes, prefix + "_large_rack", (-0.88, 0.70, 0.36), 1.08)
        base.add_box(meshes, prefix + "_sorting_tray", "plank", (0.82, 0.70, 0.36), (0.64, 0.38, 0.14), yaw=-0.18)
        base.add_box(meshes, prefix + "_tray_fiber", "dry_flax_light", (0.82, 0.70, 0.47), (0.52, 0.26, 0.04), yaw=-0.18)
        base.add_box(meshes, prefix + "_blue_marker_flag", "cloth_blue", (1.56, -0.24, 0.78), (0.055, 0.40, 0.16), yaw=-0.34)


def add_drying_rack(meshes, prefix, center, scale):
    x, y, z = center
    h = 0.68 * scale
    base.add_box(meshes, prefix + "_left_post", "wood_dark", (x - 0.24 * scale, y, z + h / 2), (0.07, 0.07, h), yaw=0.04)
    base.add_box(meshes, prefix + "_right_post", "wood_dark", (x + 0.24 * scale, y, z + h / 2), (0.07, 0.07, h), yaw=-0.04)
    base.add_box(meshes, prefix + "_top_bar", "wood", (x, y, z + h), (0.60 * scale, 0.08, 0.07), yaw=0.02)
    for index, offset in enumerate((-0.18, 0.0, 0.18)):
        base.add_box(meshes, f"{prefix}_dry_bundle_{index}", "dry_flax", (x + offset * scale, y - 0.02, z + h * 0.58), (0.09, 0.07, 0.56 * scale), yaw=0.08 * (index - 1))
        base.add_box(meshes, f"{prefix}_bundle_tie_{index}", "rope", (x + offset * scale, y - 0.02, z + h * 0.57), (0.12, 0.085, 0.035), yaw=0.08 * (index - 1))


def add_flax_bundle(meshes, prefix, center, scale=1.0, quality=False, fallen=False):
    mat = "quality_flax" if quality else "dry_flax"
    x, y, z = center
    yaw_base = -0.22 if fallen else 0.10
    for index, offset in enumerate((-0.09, 0.0, 0.09)):
        height = 0.58 * scale if not fallen else 0.12 * scale
        size = (0.055 * scale, 0.045 * scale, height)
        position = (x + offset * scale, y + 0.02 * index, z + height / 2 if not fallen else z)
        base.add_box(meshes, f"{prefix}_bundle_stem_{index}", mat, position, size, yaw=yaw_base + 0.08 * index)
    base.add_box(meshes, prefix + "_bundle_tie", "rope", (x, y, z + (0.28 * scale if not fallen else 0.02)), (0.32 * scale, 0.08 * scale, 0.045 * scale), yaw=yaw_base)


def add_marker(meshes, prefix, x, y, level, rare=False):
    base.add_box(meshes, prefix + "_post", "wood_dark", (x, y, 0.38), (0.055, 0.055, 0.68), yaw=0.06)
    base.add_box(meshes, prefix + "_board", "plank_light", (x, y, 0.78), (0.08, 0.34, 0.18), yaw=0.04)
    base.add_box(meshes, prefix + "_mark", "quality_blue" if rare else "marker_blue", (x - 0.04, y, 0.82), (0.035, 0.14 + level * 0.025, 0.052), yaw=0.04)


def add_flax_plants(meshes, prefix, level, stage, super_crop=False, damaged=False):
    rows = [-0.48, -0.16, 0.16, 0.48] if not super_crop else [-0.42, -0.14, 0.14, 0.42]
    for row_index, y in enumerate(rows):
        count = 5 + level + (1 if super_crop else 0)
        for index in range(count):
            if damaged and (index + row_index) % 4 == 0:
                continue
            x = -0.98 + index * (1.96 / max(1, count - 1))
            jitter = 0.018 * ((index + row_index) % 3 - 1)
            plant_stage = min(6, stage + (1 if super_crop else 0))
            height = (0.24 + plant_stage * 0.16 + level * 0.05) * (1.10 if super_crop else 1.0)
            stem_mat = "quality_flax" if super_crop and stage >= 5 else ("flax_stem_light" if plant_stage >= 3 else "flax_stem")
            base.add_box(meshes, f"{prefix}_stem_{row_index}_{index}", stem_mat, (x, y + jitter, 0.30 + height / 2), (0.032, 0.032, height), yaw=0.04 * ((index % 3) - 1))
            if plant_stage >= 2:
                bloom = "flax_bloom_light" if super_crop else "flax_bloom"
                base.add_box(meshes, f"{prefix}_bloom_{row_index}_{index}", bloom, (x, y + jitter, 0.34 + height), (0.095, 0.075, 0.055), yaw=0.16 * ((index % 3) - 1))
            if plant_stage >= 3:
                for side in (-1, 1):
                    angle = math.pi / 2 + side * (0.38 + 0.06 * ((index + row_index) % 2))
                    base.add_leaf(meshes, f"{prefix}_leaf_{row_index}_{index}_{side}", "flax_stem_dark", (x, y + jitter, 0.36), height * 0.62, 0.030, angle, bend=0.03)

    if stage >= 3 and not super_crop:
        add_flax_bundle(meshes, prefix + "_ready_bundle_a", (-1.04, -0.76, 0.31), 0.82)
        if level >= 2:
            add_flax_bundle(meshes, prefix + "_ready_bundle_b", (1.08, 0.76, 0.31), 0.76)
    if super_crop and stage >= 4:
        add_flax_bundle(meshes, prefix + "_quality_bundle_a", (-1.02, -0.76, 0.32), 0.88, quality=True)
    if super_crop and stage >= 5:
        base.add_box(meshes, prefix + "_quality_box", "plank", (0.08, -0.94, 0.38), (0.58, 0.28, 0.20), yaw=0.08)
        base.add_box(meshes, prefix + "_quality_lid", "quality_blue", (0.08, -0.94, 0.52), (0.46, 0.16, 0.04), yaw=0.08)


def build_meshes(level, state):
    prefix = f"flax_field_l{level:02d}_{state}"
    meshes = []
    add_plot(meshes, prefix, level)
    add_marker(meshes, prefix + "_label_a", -1.28, -0.42, level)
    if level >= 3:
        add_marker(meshes, prefix + "_label_b", 1.28, 0.38, level, rare=True)

    if state.startswith("stage"):
        add_flax_plants(meshes, prefix, level, int(state[-2:]))
    elif state == "active":
        add_flax_plants(meshes, prefix, level, 3)
    elif state.startswith("super_stage"):
        add_flax_plants(meshes, prefix, level, int(state[-2:]), super_crop=True)
    elif state == "construction":
        add_flax_plants(meshes, prefix, level, 1)
        base.add_box(meshes, prefix + "_loose_border_board", "wood", (0.66, -0.62, 0.34), (0.94, 0.12, 0.08), yaw=-0.35)
        base.add_box(meshes, prefix + "_loose_plank", "plank" if level >= 2 else "wood_cut", (0.88, -0.38, 0.42), (0.70, 0.10, 0.07), yaw=-0.16)
        base.add_rope(meshes, prefix + "_loose_rope", (-0.62, 0.58, 0.40), (-0.12, 0.86, 0.38), thickness=0.034)
    elif state == "damaged":
        add_flax_plants(meshes, prefix, level, 2, damaged=True)
        add_flax_bundle(meshes, prefix + "_fallen_bundle", (0.80, -0.76, 0.28), 0.90, fallen=True)
        base.add_box(meshes, prefix + "_broken_front_board", "wood_dark", (0.48, -1.10, 0.42), (0.94, 0.14, 0.13), yaw=0.30)
        base.add_box(meshes, prefix + "_trampled_soil", "earth_dark", (0.10, -0.02, 0.30), (0.98, 0.54, 0.055), yaw=0.16)
    elif state == "ruined":
        add_flax_plants(meshes, prefix, level, 1, damaged=True)
        for x, y, yaw in ((0.74, -1.02, 0.42), (-1.02, 0.90, -0.56), (0.28, 0.78, 0.18)):
            base.add_box(meshes, prefix + "_ruin_plank", "wood_dark", (x, y, 0.25), (0.72, 0.10, 0.08), yaw=yaw)
        base.add_box(meshes, prefix + "_dry_patch", "earth_dark", (0.05, 0.02, 0.305), (1.42, 0.90, 0.05), yaw=-0.06)
    return meshes


def draw_plot(draw, level):
    base.draw_iso_box(draw, (0, 0, 0.10), (2.70, 1.88, 0.14), MATERIALS["flax_soil"])
    base.draw_iso_box(draw, (-0.04, -0.02, 0.19), (2.30, 1.42, 0.06), MATERIALS["flax_soil_light"])
    for y in (-0.50, -0.18, 0.14, 0.46):
        base.draw_iso_box(draw, (-0.04, y, 0.25), (2.18, 0.045, 0.032), MATERIALS["earth_dark"])
    rail_mat = MATERIALS["wood" if level == 1 else "plank"]
    rail_light = MATERIALS["wood_cut" if level == 1 else "plank_light"]
    rail_h = 0.18 + level * 0.04
    for center, size, yaw in (
        ((0, -1.05, rail_h / 2), (3.02, 0.16, rail_h), 0.01),
        ((0, 1.05, rail_h / 2), (3.02, 0.16, rail_h), -0.01),
        ((-1.50, 0, rail_h / 2), (0.16, 2.08, rail_h), -0.02),
        ((1.50, 0, rail_h / 2), (0.16, 2.08, rail_h), 0.02),
    ):
        base.draw_iso_box(draw, center, size, rail_mat, yaw=yaw)
    for x in (-1.42, 1.42):
        for y in (-1.02, 1.02):
            post_h = 0.44 + level * 0.08
            base.draw_iso_box(draw, (x, y, post_h / 2), (0.16, 0.16, post_h), MATERIALS["wood_dark"])
            base.draw_iso_box(draw, (x, y, post_h + 0.035), (0.22, 0.22, 0.07), rail_light, yaw=0.16)
    if level >= 2:
        draw_drying_rack(draw, (0.98, -0.58, 0.30), 0.82)
    if level >= 3:
        draw_drying_rack(draw, (-0.88, 0.70, 0.36), 1.08)
        base.draw_iso_box(draw, (0.82, 0.70, 0.36), (0.64, 0.38, 0.14), MATERIALS["plank"], yaw=-0.18)
        base.draw_iso_box(draw, (0.82, 0.70, 0.47), (0.52, 0.26, 0.04), MATERIALS["dry_flax_light"], yaw=-0.18)
        base.draw_iso_box(draw, (1.56, -0.24, 0.78), (0.055, 0.40, 0.16), MATERIALS["cloth_blue"], yaw=-0.34)


def draw_drying_rack(draw, center, scale):
    x, y, z = center
    h = 0.68 * scale
    base.draw_iso_box(draw, (x - 0.24 * scale, y, z + h / 2), (0.07, 0.07, h), MATERIALS["wood_dark"])
    base.draw_iso_box(draw, (x + 0.24 * scale, y, z + h / 2), (0.07, 0.07, h), MATERIALS["wood_dark"])
    base.draw_iso_box(draw, (x, y, z + h), (0.60 * scale, 0.08, 0.07), MATERIALS["wood"])
    for index, offset in enumerate((-0.18, 0.0, 0.18)):
        base.draw_iso_box(draw, (x + offset * scale, y - 0.02, z + h * 0.58), (0.09, 0.07, 0.56 * scale), MATERIALS["dry_flax"], yaw=0.08 * (index - 1))


def draw_flax_bundle(draw, center, scale=1.0, quality=False, fallen=False):
    mat = MATERIALS["quality_flax" if quality else "dry_flax"]
    x, y, z = center
    for index, offset in enumerate((-0.09, 0.0, 0.09)):
        height = 0.58 * scale if not fallen else 0.12 * scale
        position = (x + offset * scale, y + 0.02 * index, z + height / 2 if not fallen else z)
        base.draw_iso_box(draw, position, (0.055 * scale, 0.045 * scale, height), mat, yaw=-0.18 + 0.08 * index)
    base.draw_iso_box(draw, (x, y, z + (0.28 * scale if not fallen else 0.02)), (0.32 * scale, 0.08 * scale, 0.045 * scale), MATERIALS["rope"], yaw=-0.10)


def draw_flax_plants(draw, level, stage, super_crop=False, damaged=False):
    rows = [-0.48, -0.16, 0.16, 0.48] if not super_crop else [-0.42, -0.14, 0.14, 0.42]
    for row_index, y in enumerate(rows):
        count = 5 + level + (1 if super_crop else 0)
        for index in range(count):
            if damaged and (index + row_index) % 4 == 0:
                continue
            x = -0.98 + index * (1.96 / max(1, count - 1))
            plant_stage = min(6, stage + (1 if super_crop else 0))
            height = (0.24 + plant_stage * 0.16 + level * 0.05) * (1.10 if super_crop else 1.0)
            root = base.iso(x, y, 0.30)
            tip = base.iso(x, y, 0.30 + height)
            color = base.material_rgba("quality_flax" if super_crop and stage >= 5 else ("flax_stem_light" if plant_stage >= 3 else "flax_stem"))
            draw.line((root[0], root[1], tip[0], tip[1]), fill=color, width=3)
            if plant_stage >= 2:
                p = base.iso(x, y, 0.36 + height)
                fill = base.material_rgba("flax_bloom_light" if super_crop else "flax_bloom")
                draw.ellipse((p[0] - 4, p[1] - 4, p[0] + 5, p[1] + 4), fill=fill)
            if plant_stage >= 3:
                for side in (-1, 1):
                    angle = math.pi / 2 + side * 0.40
                    leaf_tip = base.iso(x + math.cos(angle) * 0.08, y + math.sin(angle) * 0.08, 0.34 + height * 0.54)
                    draw.line((root[0], root[1], leaf_tip[0], leaf_tip[1]), fill=base.material_rgba("flax_stem_dark"), width=2)
    if stage >= 3 and not super_crop:
        draw_flax_bundle(draw, (-1.04, -0.76, 0.31), 0.82)
        if level >= 2:
            draw_flax_bundle(draw, (1.08, 0.76, 0.31), 0.76)
    if super_crop and stage >= 4:
        draw_flax_bundle(draw, (-1.02, -0.76, 0.32), 0.88, quality=True)
    if super_crop and stage >= 5:
        base.draw_iso_box(draw, (0.08, -0.94, 0.38), (0.58, 0.28, 0.20), MATERIALS["plank"], yaw=0.08)
        base.draw_iso_box(draw, (0.08, -0.94, 0.52), (0.46, 0.16, 0.04), MATERIALS["quality_blue"], yaw=0.08)


def draw_png(name, level, state):
    image = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((158, 260, 354, 326), fill=(0, 0, 0, 66))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(11)))
    base.paste_terrain_grass(image)
    draw = ImageDraw.Draw(image)
    draw_plot(draw, level)

    if state == "construction":
        draw_flax_plants(draw, level, 1)
        base.draw_iso_box(draw, (0.66, -0.62, 0.34), (0.94, 0.12, 0.08), MATERIALS["wood"], yaw=-0.35)
        base.draw_iso_box(draw, (0.88, -0.38, 0.42), (0.70, 0.10, 0.07), MATERIALS["plank" if level >= 2 else "wood_cut"], yaw=-0.16)
    elif state == "damaged":
        draw_flax_plants(draw, level, 2, damaged=True)
        draw_flax_bundle(draw, (0.80, -0.76, 0.28), 0.90, fallen=True)
        base.draw_iso_box(draw, (0.48, -1.10, 0.42), (0.94, 0.14, 0.13), MATERIALS["wood_dark"], yaw=0.30)
        base.draw_iso_box(draw, (0.10, -0.02, 0.30), (0.98, 0.54, 0.055), MATERIALS["earth_dark"], yaw=0.16)
    elif state == "ruined":
        draw_flax_plants(draw, level, 1, damaged=True)
        base.draw_iso_box(draw, (0.05, 0.02, 0.305), (1.42, 0.90, 0.05), MATERIALS["earth_dark"], yaw=-0.06)
        for x, y, yaw in ((0.74, -1.02, 0.42), (-1.02, 0.90, -0.56), (0.28, 0.78, 0.18)):
            base.draw_iso_box(draw, (x, y, 0.25), (0.72, 0.10, 0.08), MATERIALS["wood_dark"], yaw=yaw)
    elif state.startswith("super_stage"):
        stage = int(state[-2:])
        if stage >= 3:
            glow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            p = base.iso(0, -0.04, 0.60 + stage * 0.10)
            gd.ellipse((p[0] - 44, p[1] - 30, p[0] + 44, p[1] + 34), fill=(98, 190, 255, 38))
            image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
            draw = ImageDraw.Draw(image)
        draw_flax_plants(draw, level, stage, super_crop=True)
    elif state.startswith("stage"):
        draw_flax_plants(draw, level, int(state[-2:]))
    else:
        draw_flax_plants(draw, level, 3)

    image.save(OUT_DIR / f"{name}.png")


def asset_names():
    names = []
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    for level in (1, 2, 3):
        for state in states:
            names.append((f"flax_field_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            names.append((f"flax_field_l{level:02d}_{state}", level, state))
    return names


def validate_report(items):
    result = {"asset": "flax_field", "assets": [], "png_size": list(PNG_SIZE), "anchor": list(ANCHOR)}
    for name, level, state in items:
        glb = OUT_DIR / f"{name}.glb"
        png = OUT_DIR / f"{name}.png"
        raw = glb.read_bytes()
        with Image.open(png) as image:
            size = list(image.size)
            bbox = image.getchannel("A").getbbox()
        assert raw[:4] == b"glTF", glb
        assert size == list(PNG_SIZE), png
        assert bbox is not None, png
        result["assets"].append({
            "name": name,
            "level": level,
            "state": state,
            "triangles": sum(len(mesh.indices) // 3 for mesh in build_meshes(level, state)),
            "glb_bytes": len(raw),
            "png_bytes": png.stat().st_size,
            "bbox": list(bbox),
        })
    (OUT_DIR / "generation-report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def make_review_sheet(items):
    columns = 7
    thumb = (192, 144)
    label_h = 22
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGBA", (columns * thumb[0], rows * (thumb[1] + label_h)), (31, 43, 46, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, _level, _state) in enumerate(items):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            preview = image.resize(thumb, Image.Resampling.LANCZOS)
        x = (index % columns) * thumb[0]
        y = (index // columns) * (thumb[1] + label_h)
        sheet.alpha_composite(preview, (x, y))
        draw.text((x + 8, y + thumb[1] + 4), name.replace("flax_field_", ""), fill=(232, 245, 244, 255))
    sheet.save(OUT_DIR / "flax_field_l01_l03_review.png")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = asset_names()
    lines = []
    for name, level, state in items:
        meshes = build_meshes(level, state)
        base.write_glb(name, meshes)
        draw_png(name, level, state)
        triangles = sum(len(mesh.indices) // 3 for mesh in meshes)
        lines.append(f"{name}: meshes={len(meshes)} triangles={triangles}")
    report = validate_report(items)
    make_review_sheet(items)
    manifest = {
        "asset_id": "flax_field",
        "category": "fields",
        "display_name": "Льняное поле",
        "style": "Aeolian bright fantasy stylized mid-poly",
        "levels": [1, 2, 3],
        "states": ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined", "super_stage01", "super_stage02", "super_stage03", "super_stage04", "super_stage05", "super_stage06"],
        "sprite": {"size": list(PNG_SIZE), "anchor": list(ANCHOR)},
        "source_blend": None,
        "items": [
            {
                "id": item["name"],
                "level": item["level"],
                "state": item["state"],
                "glb": f"{item['name']}.glb",
                "png": f"{item['name']}.png",
                "anchor": list(ANCHOR),
                "triangles": item["triangles"],
                "alpha_bounds": item["bbox"],
            }
            for item in report["assets"]
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    LOG_PATH.write_text("\n".join(lines) + f"\nFLAX_FIELD_COMPLETE {len(items)}\n")
    print(f"FLAX_FIELD_COMPLETE {len(items)}")


if __name__ == "__main__":
    main()
