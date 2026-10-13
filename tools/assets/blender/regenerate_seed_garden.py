"""Generate runtime seed garden GLB/PNG assets.

This production fallback mirrors the field runtime contract when Blender MCP is
not available: it writes valid GLB meshes, isometric PNG sprites, manifest,
generation report and a review sheet for levels 1-3.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import regenerate_windleaf_beds as base


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "fields" / "seed_garden"
LOG_PATH = Path("/tmp/real-city-seed-garden-generation.log")
PNG_SIZE = base.PNG_SIZE
ANCHOR = base.ANCHOR

MATERIALS = {
    **base.MATERIALS,
    "seed_soil": (0.48, 0.27, 0.12, 1.0),
    "seed_soil_light": (0.70, 0.44, 0.20, 1.0),
    "sprout": (0.34, 0.72, 0.23, 1.0),
    "sprout_light": (0.62, 0.92, 0.34, 1.0),
    "seed_pod": (0.83, 0.67, 0.34, 1.0),
    "seed_pod_light": (0.96, 0.82, 0.45, 1.0),
    "seed_gold": (1.00, 0.80, 0.24, 1.0),
    "seed_super": (0.72, 1.00, 0.38, 1.0),
    "bag": (0.78, 0.66, 0.45, 1.0),
    "bag_dark": (0.48, 0.36, 0.20, 1.0),
    "tray": (0.72, 0.45, 0.20, 1.0),
    "tray_light": (0.92, 0.66, 0.35, 1.0),
    "marker_green": (0.58, 0.86, 0.34, 1.0),
}
base.MATERIALS = MATERIALS
base.OUT_DIR = OUT_DIR
base.padded = lambda data: data + b" " * ((4 - len(data) % 4) % 4)


def add_seed_rows(meshes, prefix, level):
    base.add_box(meshes, prefix + "_terrain_grass_tile", "grass", (0, 0, -0.015), (3.6, 3.6, 0.03))
    base.add_box(meshes, prefix + "_seed_plot", "seed_soil", (0, 0, 0.10), (2.52, 1.92, 0.14))
    base.add_box(meshes, prefix + "_raised_soil", "seed_soil_light", (-0.08, -0.02, 0.19), (2.12, 1.50, 0.05))
    for y in (-0.54, -0.18, 0.18, 0.54):
        base.add_box(meshes, prefix + "_seed_furrow", "earth_dark", (-0.04, y, 0.24), (2.05, 0.055, 0.035))
        base.add_box(meshes, prefix + "_seed_ridge", "seed_soil_light", (-0.04, y + 0.08, 0.265), (1.86, 0.045, 0.030))

    rail_mat = "wood" if level == 1 else "plank"
    rail_light = "wood_cut" if level == 1 else "plank_light"
    rail_h = 0.22 + level * 0.035
    base.add_box(meshes, prefix + "_front_board", rail_mat, (0, -1.08, rail_h / 2), (2.98, 0.18, rail_h), yaw=0.01)
    base.add_box(meshes, prefix + "_back_board", rail_mat, (0, 1.08, rail_h / 2), (2.98, 0.18, rail_h), yaw=-0.01)
    base.add_box(meshes, prefix + "_left_board", rail_mat, (-1.46, 0, rail_h / 2), (0.18, 2.24, rail_h), yaw=-0.02)
    base.add_box(meshes, prefix + "_right_board", rail_mat, (1.46, 0, rail_h / 2), (0.18, 2.24, rail_h), yaw=0.02)
    for x in (-0.78, 0.0, 0.78):
        base.add_box(meshes, prefix + "_front_cap", rail_light, (x, -1.20, rail_h + 0.035), (0.62, 0.055, 0.055))
        base.add_box(meshes, prefix + "_back_cap", rail_light, (x, 1.20, rail_h + 0.035), (0.62, 0.055, 0.055))

    for x in (-1.42, 1.42):
        for y in (-1.03, 1.03):
            post_h = 0.48 + level * 0.08
            base.add_box(meshes, prefix + "_corner_stake", "wood_dark", (x, y, post_h / 2), (0.18, 0.18, post_h), yaw=0.10)
            base.add_box(meshes, prefix + "_stake_cap", rail_light, (x, y, post_h + 0.035), (0.24, 0.24, 0.07), yaw=0.18)

    if level >= 2:
        for y in (-0.36, 0.36):
            base.add_rope(meshes, prefix + "_sorting_rope", (-1.12, y, 0.48), (1.12, y, 0.48), thickness=0.040)
        base.add_box(meshes, prefix + "_drying_tray", "tray", (0.96, -0.48, 0.36), (0.62, 0.34, 0.12), yaw=-0.18)
        base.add_box(meshes, prefix + "_tray_seed_layer", "seed_pod", (0.96, -0.48, 0.45), (0.52, 0.24, 0.035), yaw=-0.18)
    if level >= 3:
        for x in (-0.86, 0.86):
            base.add_box(meshes, prefix + "_rope_post", "wood_dark", (x, 0.02, 0.55), (0.075, 0.075, 1.10))
        base.add_rope(meshes, prefix + "_rare_row_rope", (-0.92, 0.02, 1.08), (0.92, 0.02, 1.08), thickness=0.050)
        base.add_box(meshes, prefix + "_rare_marker_flag", "cloth_teal", (1.56, -0.70, 0.76), (0.055, 0.42, 0.16), yaw=-0.38)
        base.add_box(meshes, prefix + "_large_sorting_table", "plank", (-0.90, 0.82, 0.34), (0.68, 0.42, 0.16), yaw=0.22)
        base.add_box(meshes, prefix + "_table_seed_layer", "seed_pod_light", (-0.90, 0.82, 0.45), (0.54, 0.30, 0.035), yaw=0.22)


def add_seed_bag(meshes, prefix, center, scale=1.0, torn=False):
    mat = "bag_dark" if torn else "bag"
    base.add_box(meshes, prefix + "_seed_bag_body", mat, center, (0.30 * scale, 0.24 * scale, 0.34 * scale), yaw=0.25)
    base.add_box(meshes, prefix + "_seed_bag_neck", "flax", (center[0], center[1], center[2] + 0.22 * scale), (0.18 * scale, 0.12 * scale, 0.10 * scale), yaw=0.30)
    if torn:
        base.add_box(meshes, prefix + "_spilled_seeds", "seed_pod", (center[0] + 0.20, center[1] - 0.08, 0.26), (0.38, 0.16, 0.035), yaw=-0.25)


def add_label(meshes, prefix, x, y, level, rare=False):
    base.add_box(meshes, prefix + "_label_post", "wood_dark", (x, y, 0.36), (0.055, 0.055, 0.64), yaw=0.08)
    base.add_box(meshes, prefix + "_label_board", "plank_light", (x, y, 0.76), (0.08, 0.34, 0.18), yaw=0.04)
    base.add_box(meshes, prefix + "_label_mark", "seed_super" if rare else "marker_green", (x - 0.04, y, 0.80), (0.035, 0.16 + level * 0.02, 0.055), yaw=0.06)


def add_seed_plants(meshes, prefix, level, stage, super_crop=False, damaged=False):
    rows = [-0.54, -0.18, 0.18, 0.54]
    if super_crop:
        rows = [-0.42, 0.0, 0.42]
    for row_index, y in enumerate(rows):
        count = 4 + level + (1 if super_crop else 0)
        for index in range(count):
            x = -0.88 + index * (1.76 / max(1, count - 1))
            if damaged and (index + row_index) % 4 == 0:
                continue
            jitter = 0.025 * ((index + row_index) % 3 - 1)
            plant_stage = stage if not super_crop else min(6, stage + 1)
            height = (0.13 + plant_stage * 0.12 + level * 0.035) * (1.35 if super_crop else 1.0)
            width = (0.035 + plant_stage * 0.010) * (1.45 if super_crop else 1.0)
            stem_mat = "seed_super" if super_crop else "sprout"
            base.add_box(meshes, f"{prefix}_sprout_stem_{row_index}_{index}", "leaf_deep", (x, y + jitter, 0.28 + height * 0.25), (0.035, 0.035, height * 0.58))
            for side in (-1, 1):
                angle = math.pi / 2 + side * (0.55 + 0.08 * ((index + row_index) % 2))
                base.add_leaf(meshes, f"{prefix}_sprout_leaf_{row_index}_{index}_{side}", stem_mat, (x, y + jitter, 0.29), height * 0.78, width, angle, bend=0.05)
            if plant_stage >= 2:
                pod_mat = "seed_super" if super_crop else "seed_pod"
                base.add_box(meshes, f"{prefix}_seed_pod_{row_index}_{index}", pod_mat, (x, y + jitter, 0.38 + height * 0.58), (0.10, 0.075, 0.075), yaw=0.15 * ((index % 3) - 1))
            if plant_stage >= 3:
                pod_mat = "seed_gold" if super_crop and stage >= 5 else "seed_pod_light"
                base.add_box(meshes, f"{prefix}_open_pod_{row_index}_{index}", pod_mat, (x + 0.025, y + jitter, 0.43 + height * 0.70), (0.12, 0.035, 0.040), yaw=0.25)

    if super_crop and stage >= 3:
        for x in (-0.82, 0.82):
            support_h = 0.78 + stage * 0.12
            base.add_box(meshes, prefix + "_super_support_post", "wood", (x, 0.0, support_h / 2), (0.06, 0.06, support_h))
        base.add_rope(meshes, prefix + "_super_support_rope", (-0.86, 0.0, 0.90 + stage * 0.10), (0.86, 0.0, 0.90 + stage * 0.10), thickness=0.045)
    if super_crop and stage >= 5:
        base.add_box(meshes, prefix + "_protected_seed_box", "tray", (-0.04, -0.92, 0.38), (0.58, 0.28, 0.20), yaw=0.08)
        base.add_box(meshes, prefix + "_protected_seed_glow", "seed_super", (-0.04, -0.92, 0.52), (0.44, 0.16, 0.04), yaw=0.08)


def build_meshes(level, state):
    prefix = f"seed_garden_l{level:02d}_{state}"
    meshes = []
    add_seed_rows(meshes, prefix, level)
    add_seed_bag(meshes, prefix + "_bag_a", (-1.00, -0.70, 0.33), 1.0)
    if level >= 2:
        add_seed_bag(meshes, prefix + "_bag_b", (1.08, 0.70, 0.31), 0.85)
    add_label(meshes, prefix + "_label_a", -1.28, -0.30, level)
    if level >= 3:
        add_label(meshes, prefix + "_label_b", 1.28, 0.20, level, rare=True)

    if state.startswith("stage"):
        add_seed_plants(meshes, prefix, level, int(state[-2:]))
    elif state == "active":
        add_seed_plants(meshes, prefix, level, 3)
    elif state.startswith("super_stage"):
        add_seed_plants(meshes, prefix, level, int(state[-2:]), super_crop=True)
    elif state == "construction":
        add_seed_plants(meshes, prefix, level, 1)
        base.add_box(meshes, prefix + "_missing_back_gap", "seed_soil", (0.62, 1.08, 0.17), (0.78, 0.20, 0.14), yaw=0.04)
        base.add_box(meshes, prefix + "_loose_board_a", "wood", (0.62, -0.58, 0.35), (0.92, 0.12, 0.08), yaw=-0.36)
        base.add_box(meshes, prefix + "_loose_board_b", "plank" if level >= 2 else "wood_cut", (0.82, -0.38, 0.43), (0.72, 0.10, 0.07), yaw=-0.18)
        base.add_rope(meshes, prefix + "_loose_rope", (-0.62, 0.58, 0.40), (-0.12, 0.86, 0.38), thickness=0.038)
    elif state == "damaged":
        add_seed_plants(meshes, prefix, level, 2, damaged=True)
        add_seed_bag(meshes, prefix + "_torn_bag", (0.88, -0.78, 0.29), 0.85, torn=True)
        base.add_box(meshes, prefix + "_broken_front_board", "wood_dark", (0.55, -1.12, 0.48), (0.92, 0.14, 0.13), yaw=0.28)
        base.add_box(meshes, prefix + "_fallen_stake", "wood_dark", (-0.92, 0.72, 0.27), (0.82, 0.11, 0.09), yaw=-0.74)
        base.add_box(meshes, prefix + "_trampled_soil", "earth_dark", (0.16, -0.02, 0.30), (0.94, 0.56, 0.055), yaw=0.18)
    elif state == "ruined":
        add_seed_plants(meshes, prefix, level, 1, damaged=True)
        add_seed_bag(meshes, prefix + "_empty_torn_bag", (-0.68, -0.72, 0.25), 0.75, torn=True)
        for x, y, yaw in ((0.72, -1.05, 0.42), (-1.08, 0.94, -0.58), (0.36, 0.78, 0.18)):
            base.add_box(meshes, prefix + "_ruin_plank", "wood_dark", (x, y, 0.26), (0.72, 0.10, 0.08), yaw=yaw)
        base.add_box(meshes, prefix + "_dry_patch", "earth_dark", (0.08, 0.02, 0.305), (1.40, 0.92, 0.05), yaw=-0.06)
    return meshes


def draw_seed_base(draw, level):
    base.draw_iso_box(draw, (0, 0, 0.10), (2.52, 1.92, 0.14), MATERIALS["seed_soil"])
    base.draw_iso_box(draw, (-0.08, -0.02, 0.19), (2.12, 1.50, 0.05), MATERIALS["seed_soil_light"])
    for y in (-0.54, -0.18, 0.18, 0.54):
        base.draw_iso_box(draw, (-0.04, y, 0.24), (2.05, 0.055, 0.035), MATERIALS["earth_dark"])
        base.draw_iso_box(draw, (-0.04, y + 0.08, 0.265), (1.86, 0.045, 0.030), MATERIALS["seed_soil_light"])
    rail_mat = MATERIALS["wood" if level == 1 else "plank"]
    rail_light = MATERIALS["wood_cut" if level == 1 else "plank_light"]
    rail_h = 0.22 + level * 0.035
    for center, size, yaw in (
        ((0, -1.08, rail_h / 2), (2.98, 0.18, rail_h), 0.01),
        ((0, 1.08, rail_h / 2), (2.98, 0.18, rail_h), -0.01),
        ((-1.46, 0, rail_h / 2), (0.18, 2.24, rail_h), -0.02),
        ((1.46, 0, rail_h / 2), (0.18, 2.24, rail_h), 0.02),
    ):
        base.draw_iso_box(draw, center, size, rail_mat, yaw=yaw)
    for x in (-0.78, 0.0, 0.78):
        base.draw_iso_box(draw, (x, -1.20, rail_h + 0.035), (0.62, 0.055, 0.055), rail_light)
        base.draw_iso_box(draw, (x, 1.20, rail_h + 0.035), (0.62, 0.055, 0.055), rail_light)
    for x in (-1.42, 1.42):
        for y in (-1.03, 1.03):
            post_h = 0.48 + level * 0.08
            base.draw_iso_box(draw, (x, y, post_h / 2), (0.18, 0.18, post_h), MATERIALS["wood_dark"])
            base.draw_iso_box(draw, (x, y, post_h + 0.035), (0.24, 0.24, 0.07), rail_light, yaw=0.18)
    if level >= 2:
        base.draw_iso_box(draw, (0.96, -0.48, 0.36), (0.62, 0.34, 0.12), MATERIALS["tray"], yaw=-0.18)
        base.draw_iso_box(draw, (0.96, -0.48, 0.45), (0.52, 0.24, 0.035), MATERIALS["seed_pod"], yaw=-0.18)
    if level >= 3:
        base.draw_iso_box(draw, (-0.90, 0.82, 0.34), (0.68, 0.42, 0.16), MATERIALS["plank"], yaw=0.22)
        base.draw_iso_box(draw, (-0.90, 0.82, 0.45), (0.54, 0.30, 0.035), MATERIALS["seed_pod_light"], yaw=0.22)
        base.draw_iso_box(draw, (1.56, -0.70, 0.76), (0.055, 0.42, 0.16), MATERIALS["cloth_teal"], yaw=-0.38)


def draw_seed_bag(draw, center, scale=1.0, torn=False):
    base.draw_iso_box(draw, center, (0.30 * scale, 0.24 * scale, 0.34 * scale), MATERIALS["bag_dark" if torn else "bag"], yaw=0.25)
    base.draw_iso_box(draw, (center[0], center[1], center[2] + 0.22 * scale), (0.18 * scale, 0.12 * scale, 0.10 * scale), MATERIALS["flax"], yaw=0.30)
    if torn:
        base.draw_iso_box(draw, (center[0] + 0.20, center[1] - 0.08, 0.26), (0.38, 0.16, 0.035), MATERIALS["seed_pod"], yaw=-0.25)


def draw_seed_plants(draw, level, stage, super_crop=False, damaged=False):
    rows = [-0.54, -0.18, 0.18, 0.54] if not super_crop else [-0.42, 0.0, 0.42]
    for row_index, y in enumerate(rows):
        count = 4 + level + (1 if super_crop else 0)
        for index in range(count):
            if damaged and (index + row_index) % 4 == 0:
                continue
            x = -0.88 + index * (1.76 / max(1, count - 1))
            plant_stage = stage if not super_crop else min(6, stage + 1)
            height = (0.13 + plant_stage * 0.12 + level * 0.035) * (1.35 if super_crop else 1.0)
            width = (7 + plant_stage * 2 + level) * (1.35 if super_crop else 1.0)
            root = base.iso(x, y, 0.30)
            for side in (-1, 1):
                angle = math.pi / 2 + side * (0.55 + 0.08 * ((index + row_index) % 2))
                tip = base.iso(x + math.cos(angle) * 0.10, y + math.sin(angle) * 0.10, 0.30 + height)
                color = base.material_rgba("seed_super" if super_crop else ("sprout_light" if plant_stage >= 3 else "sprout"))
                vein = base.material_rgba("seed_pod_light" if plant_stage >= 2 else "leaf_vein", 230)
                base.draw_leaf_shape(draw, root, tip, width, angle, color, vein, 2)
            if plant_stage >= 2:
                p = base.iso(x, y, 0.45 + height * 0.40)
                fill = base.material_rgba("seed_gold" if super_crop and stage >= 5 else "seed_pod")
                draw.ellipse((p[0] - 4, p[1] - 5, p[0] + 5, p[1] + 4), fill=fill)
    if super_crop and stage >= 5:
        base.draw_iso_box(draw, (-0.04, -0.92, 0.38), (0.58, 0.28, 0.20), MATERIALS["tray"], yaw=0.08)
        base.draw_iso_box(draw, (-0.04, -0.92, 0.52), (0.44, 0.16, 0.04), MATERIALS["seed_super"], yaw=0.08)


def draw_png(name, level, state):
    image = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((158, 260, 354, 326), fill=(0, 0, 0, 66))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(11)))
    base.paste_terrain_grass(image)
    draw = ImageDraw.Draw(image)
    draw_seed_base(draw, level)
    draw_seed_bag(draw, (-1.00, -0.70, 0.33), 1.0)
    if level >= 2:
        draw_seed_bag(draw, (1.08, 0.70, 0.31), 0.85)

    if state == "construction":
        draw_seed_plants(draw, level, 1)
        base.draw_iso_box(draw, (0.62, -0.58, 0.35), (0.92, 0.12, 0.08), MATERIALS["wood"], yaw=-0.36)
        base.draw_iso_box(draw, (0.82, -0.38, 0.43), (0.72, 0.10, 0.07), MATERIALS["plank" if level >= 2 else "wood_cut"], yaw=-0.18)
    elif state == "damaged":
        draw_seed_plants(draw, level, 2, damaged=True)
        draw_seed_bag(draw, (0.88, -0.78, 0.29), 0.85, torn=True)
        base.draw_iso_box(draw, (0.55, -1.12, 0.48), (0.92, 0.14, 0.13), MATERIALS["wood_dark"], yaw=0.28)
        base.draw_iso_box(draw, (-0.92, 0.72, 0.27), (0.82, 0.11, 0.09), MATERIALS["wood_dark"], yaw=-0.74)
        base.draw_iso_box(draw, (0.16, -0.02, 0.30), (0.94, 0.56, 0.055), MATERIALS["earth_dark"], yaw=0.18)
    elif state == "ruined":
        draw_seed_plants(draw, level, 1, damaged=True)
        draw_seed_bag(draw, (-0.68, -0.72, 0.25), 0.75, torn=True)
        base.draw_iso_box(draw, (0.08, 0.02, 0.305), (1.40, 0.92, 0.05), MATERIALS["earth_dark"], yaw=-0.06)
        for x, y, yaw in ((0.72, -1.05, 0.42), (-1.08, 0.94, -0.58), (0.36, 0.78, 0.18)):
            base.draw_iso_box(draw, (x, y, 0.26), (0.72, 0.10, 0.08), MATERIALS["wood_dark"], yaw=yaw)
    elif state.startswith("super_stage"):
        stage = int(state[-2:])
        if stage >= 3:
            glow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            p = base.iso(0, -0.04, 0.62 + stage * 0.12)
            gd.ellipse((p[0] - 42, p[1] - 30, p[0] + 42, p[1] + 34), fill=(160, 255, 86, 42))
            image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
            draw = ImageDraw.Draw(image)
        draw_seed_plants(draw, level, stage, super_crop=True)
    elif state.startswith("stage"):
        draw_seed_plants(draw, level, int(state[-2:]))
    else:
        draw_seed_plants(draw, level, 3)

    image.save(OUT_DIR / f"{name}.png")


def asset_names():
    names = []
    states = ["stage01", "stage02", "stage03", "active", "construction", "damaged", "ruined"]
    for level in (1, 2, 3):
        for state in states:
            names.append((f"seed_garden_l{level:02d}_{state}", level, state))
        for stage in range(1, 7):
            state = f"super_stage{stage:02d}"
            names.append((f"seed_garden_l{level:02d}_{state}", level, state))
    return names


def validate_report(items):
    result = {"asset": "seed_garden", "assets": [], "png_size": list(PNG_SIZE), "anchor": list(ANCHOR)}
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
    sheet = Image.new("RGBA", (columns * thumb[0], rows * (thumb[1] + label_h)), (32, 45, 41, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, _level, _state) in enumerate(items):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            preview = image.resize(thumb, Image.Resampling.LANCZOS)
        x = (index % columns) * thumb[0]
        y = (index // columns) * (thumb[1] + label_h)
        sheet.alpha_composite(preview, (x, y))
        draw.text((x + 8, y + thumb[1] + 4), name.replace("seed_garden_", ""), fill=(235, 246, 230, 255))
    sheet.save(OUT_DIR / "seed_garden_l01_l03_review.png")


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
        "asset_id": "seed_garden",
        "category": "fields",
        "display_name": "Семенной огород",
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
    LOG_PATH.write_text("\n".join(lines) + f"\nSEED_GARDEN_COMPLETE {len(items)}\n")
    print(f"SEED_GARDEN_COMPLETE {len(items)}")


if __name__ == "__main__":
    main()
