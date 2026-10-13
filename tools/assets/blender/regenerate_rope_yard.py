"""Generate runtime rope yard GLB/PNG assets.

This production fallback writes valid GLB meshes, isometric PNG sprites,
manifest, generation report and a review sheet for levels 1-8 when Blender
MCP/CLI is not available.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import regenerate_windleaf_beds as base


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "industry" / "rope_yard"
LOG_PATH = Path("/tmp/real-city-rope-yard-generation.log")
PNG_SIZE = base.PNG_SIZE
ANCHOR = base.ANCHOR
STATES = ["active", "ready", "idle_no_input", "idle_no_workers", "construction", "damaged", "ruined"]

MATERIALS = {
    **base.MATERIALS,
    "yard_soil": (0.50, 0.33, 0.17, 1.0),
    "yard_soil_light": (0.66, 0.46, 0.25, 1.0),
    "rope": (0.72, 0.56, 0.32, 1.0),
    "rope_dark": (0.50, 0.34, 0.16, 1.0),
    "fine_rope": (0.93, 0.80, 0.52, 1.0),
    "flax_bundle": (0.86, 0.72, 0.44, 1.0),
    "windleaf": (0.36, 0.68, 0.30, 1.0),
    "cloth_band": (0.62, 0.46, 0.32, 1.0),
    "copper": (0.76, 0.42, 0.22, 1.0),
    "gold": (0.95, 0.72, 0.26, 1.0),
    "premium_wood": (0.42, 0.22, 0.10, 1.0),
    "mechanism": (0.30, 0.34, 0.34, 1.0),
}
base.MATERIALS = MATERIALS
base.OUT_DIR = OUT_DIR
base.padded = lambda data: data + b" " * ((4 - len(data) % 4) % 4)


def add_beam(meshes, name, material, start, end, thickness=0.055):
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    yaw = math.atan2(dy, dx)
    base.add_box(meshes, name, material, ((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2), (length, thickness, thickness), yaw=yaw)


def add_post(meshes, prefix, x, y, height, material="wood_dark", damaged=False):
    lean = 0.16 if damaged else 0.02
    base.add_box(meshes, prefix + "_post", material, (x, y, height / 2), (0.13, 0.13, height), yaw=lean)
    base.add_box(meshes, prefix + "_hook", "iron" if height > 0.75 else "wood", (x, y - 0.05, height + 0.05), (0.24, 0.055, 0.06), yaw=-0.15)


def add_rope_coil(meshes, prefix, center, radius=0.22, turns=4, material="rope", fallen=False):
    x, y, z = center
    for index in range(turns):
        angle = index * math.pi / max(2, turns - 1)
        dx = math.cos(angle) * radius * 0.38
        dy = math.sin(angle) * radius * 0.25
        base.add_box(
            meshes,
            f"{prefix}_coil_{index}",
            material,
            (x + dx, y + dy, z + 0.018 * index),
            (radius * 1.65, 0.055, 0.05 if not fallen else 0.035),
            yaw=angle + (0.25 if fallen else 0.0),
        )
    base.add_box(meshes, prefix + "_coil_tag", "plank_light", (x + radius * 0.55, y - radius * 0.40, z + 0.07), (0.16, 0.05, 0.04), yaw=-0.35)


def add_flax_stack(meshes, prefix, x, y, count=4, empty=False):
    if empty:
        base.add_box(meshes, prefix + "_empty_mat", "yard_soil_light", (x, y, 0.19), (0.56, 0.32, 0.035), yaw=-0.20)
        return
    for index in range(count):
        base.add_box(meshes, f"{prefix}_flax_{index}", "flax_bundle", (x + index * 0.035, y + index * 0.025, 0.28 + index * 0.035), (0.48, 0.07, 0.08), yaw=-0.24 + index * 0.10)
    base.add_box(meshes, prefix + "_tie", "rope", (x + 0.06, y + 0.04, 0.39), (0.44, 0.045, 0.04), yaw=-0.16)


def add_drum(meshes, prefix, center, level, spinning=False, broken=False):
    x, y, z = center
    mat = "mechanism" if level >= 6 else ("iron" if level >= 5 else "wood_dark")
    side = "copper" if level >= 7 else ("iron" if level >= 5 else "wood")
    yaw = 0.18 if spinning else -0.08
    base.add_box(meshes, prefix + "_drum_core", mat, (x, y, z), (0.34, 0.52, 0.34), yaw=yaw)
    base.add_box(meshes, prefix + "_drum_left", side, (x - 0.19, y, z), (0.055, 0.58, 0.38), yaw=yaw)
    base.add_box(meshes, prefix + "_drum_right", side, (x + 0.19, y, z), (0.055, 0.58, 0.38), yaw=yaw)
    if broken:
        base.add_box(meshes, prefix + "_broken_axle", "iron", (x + 0.32, y - 0.12, z - 0.14), (0.34, 0.05, 0.05), yaw=0.60)


def add_quality_rack(meshes, prefix, level):
    if level < 3:
        return
    base.add_box(meshes, prefix + "_rack_post_a", "wood_dark", (1.18, 0.72, 0.44), (0.07, 0.07, 0.72), yaw=0.05)
    base.add_box(meshes, prefix + "_rack_post_b", "wood_dark", (1.50, 0.66, 0.44), (0.07, 0.07, 0.72), yaw=-0.04)
    add_beam(meshes, prefix + "_rack_bar", "wood", (1.12, 0.70, 0.78), (1.56, 0.64, 0.78), 0.055)
    add_rope_coil(meshes, prefix + "_fine_rope", (1.34, 0.58, 0.32), 0.18, 4, material="fine_rope")
    if level >= 8:
        base.add_box(meshes, prefix + "_gold_calibrator", "gold", (1.62, 0.45, 0.55), (0.16, 0.12, 0.22), yaw=-0.18)


def add_platform(meshes, prefix, level, state):
    base.add_box(meshes, prefix + "_terrain_grass_tile", "grass", (0, 0, -0.015), (3.6, 3.6, 0.03))
    base.add_box(meshes, prefix + "_yard_soil", "yard_soil", (0, 0, 0.08), (3.25, 2.35, 0.12))
    base.add_box(meshes, prefix + "_twist_lane", "yard_soil_light", (-0.15, -0.08, 0.17), (2.62, 0.46, 0.05), yaw=0.02)

    if level >= 4:
        for x, y in ((-1.36, -1.00), (1.36, -1.00), (-1.36, 1.00), (1.36, 1.00)):
            base.add_box(meshes, prefix + "_stone_block", "stone", (x, y, 0.18), (0.34, 0.26, 0.20), yaw=0.08)
    if level >= 6:
        base.add_box(meshes, prefix + "_premium_frame_a", "premium_wood", (0, -1.04, 0.30), (2.70, 0.12, 0.16), yaw=0.01)
        base.add_box(meshes, prefix + "_premium_frame_b", "premium_wood", (0, 1.04, 0.30), (2.70, 0.12, 0.16), yaw=-0.01)
    else:
        base.add_box(meshes, prefix + "_wood_frame_a", "plank" if level >= 2 else "wood", (0, -1.04, 0.25), (2.70, 0.12, 0.12), yaw=0.01)
        base.add_box(meshes, prefix + "_wood_frame_b", "plank" if level >= 2 else "wood", (0, 1.04, 0.25), (2.70, 0.12, 0.12), yaw=-0.01)


def add_rope_line(meshes, prefix, level, state):
    empty_input = state == "idle_no_input"
    idle_workers = state == "idle_no_workers"
    damaged = state in {"damaged", "ruined"}
    post_count = 2 + min(3, level // 2)
    xs = [-1.12 + i * (2.24 / max(1, post_count - 1)) for i in range(post_count)]
    for index, x in enumerate(xs):
        material = "iron" if level >= 7 and index % 2 == 0 else ("premium_wood" if level >= 6 else "wood_dark")
        add_post(meshes, f"{prefix}_line_post_{index}", x, -0.20, 0.66 + level * 0.035, material, damaged and index % 2 == 0)

    if not empty_input and state not in {"construction", "ruined"}:
        lane_count = 1 + min(3, level // 2)
        for lane in range(lane_count):
            y = -0.33 + lane * 0.13
            z = 0.66 + level * 0.035 + lane * 0.035
            material = "fine_rope" if state == "ready" and level >= 3 and lane == lane_count - 1 else "rope"
            add_beam(meshes, f"{prefix}_twisted_line_{lane}", material, (-1.24, y, z), (1.24, y + 0.04, z + 0.02), 0.035 + level * 0.002)
    if idle_workers and state != "ruined":
        base.add_box(meshes, prefix + "_empty_work_bench", "plank", (-0.86, 0.66, 0.30), (0.60, 0.28, 0.16), yaw=0.10)


def add_level_details(meshes, prefix, level, state):
    construction = state == "construction"
    damaged = state in {"damaged", "ruined"}
    add_flax_stack(meshes, prefix + "_input_stack", -1.20, 0.58, 3 + min(3, level), empty=state == "idle_no_input")
    if level == 1:
        base.add_box(meshes, prefix + "_windleaf_bundle", "windleaf", (-1.34, -0.70, 0.30), (0.42, 0.18, 0.16), yaw=-0.18)
    if level >= 2:
        base.add_box(meshes, prefix + "_small_canopy_post_a", "wood_dark", (-0.34, 0.92, 0.52), (0.07, 0.07, 0.84), yaw=0.02)
        base.add_box(meshes, prefix + "_small_canopy_post_b", "wood_dark", (0.46, 0.90, 0.52), (0.07, 0.07, 0.84), yaw=-0.02)
        base.add_box(meshes, prefix + "_small_canopy_roof", "plank", (0.06, 0.92, 0.98), (0.98, 0.52, 0.10), yaw=-0.03)
    if level >= 5:
        for x in (-0.44, 0.44):
            base.add_box(meshes, prefix + "_cloth_band", "cloth_band", (x, -0.70, 0.52), (0.42, 0.06, 0.08), yaw=0.12)
        base.add_box(meshes, prefix + "_iron_hook_rack", "iron", (0.80, -0.74, 0.62), (0.44, 0.08, 0.11), yaw=-0.08)
    if level >= 6:
        base.add_box(meshes, prefix + "_gear_box", "mechanism", (-0.06, -0.82, 0.42), (0.38, 0.30, 0.24), yaw=0.10)
        base.add_box(meshes, prefix + "_gear_cap", "iron", (-0.06, -0.82, 0.58), (0.25, 0.20, 0.06), yaw=0.10)
    if level >= 7:
        for x in (-0.22, 0.22, 0.66):
            base.add_box(meshes, prefix + "_copper_bushing", "copper", (x, -0.42, 0.62), (0.12, 0.10, 0.10), yaw=0.20)

    drum_count = 1 + (level >= 3) + (level >= 7)
    for index in range(drum_count):
        add_drum(meshes, f"{prefix}_drum_{index}", (-0.70 + index * 0.52, -0.72, 0.42), level, spinning=state == "active", broken=damaged and index == 0)

    if state == "ready":
        for index in range(2 + level // 2):
            add_rope_coil(meshes, f"{prefix}_ready_coil_{index}", (-0.70 + index * 0.33, 0.70, 0.30), 0.18 + level * 0.008, 4, material="rope")
    else:
        add_rope_coil(meshes, prefix + "_work_coil", (0.84, 0.62, 0.30), 0.18 + level * 0.010, 4, material="rope", fallen=damaged)

    add_quality_rack(meshes, prefix + "_quality", level)

    if construction:
        base.add_box(meshes, prefix + "_loose_board_a", "plank", (0.58, -0.28, 0.30), (0.92, 0.10, 0.08), yaw=-0.38)
        base.add_box(meshes, prefix + "_loose_board_b", "wood", (0.76, -0.08, 0.38), (0.66, 0.09, 0.07), yaw=-0.16)
        add_flax_stack(meshes, prefix + "_construction_materials", -0.90, 0.84, 3, empty=False)
    if damaged:
        base.add_box(meshes, prefix + "_snapped_stand", "wood_dark", (-0.52, -0.05, 0.32), (0.70, 0.11, 0.10), yaw=0.55)
        add_beam(meshes, prefix + "_snapped_rope", "rope_dark", (-0.92, -0.25, 0.54), (-0.28, 0.02, 0.32), 0.034)
    if state == "ruined":
        for x, y, yaw in ((0.48, -0.84, 0.46), (-0.96, 0.10, -0.56), (0.98, 0.20, 0.22)):
            base.add_box(meshes, prefix + "_ruin_plank", "wood_dark", (x, y, 0.24), (0.74, 0.12, 0.09), yaw=yaw)
        base.add_box(meshes, prefix + "_scorched_lane", "earth_dark", (0.0, -0.06, 0.23), (1.72, 0.50, 0.055), yaw=-0.04)


def build_meshes(level, state):
    prefix = f"rope_yard_l{level:02d}_{state}"
    meshes = []
    add_platform(meshes, prefix, level, state)
    add_rope_line(meshes, prefix, level, state)
    add_level_details(meshes, prefix, level, state)
    return meshes


def draw_beam(draw, start, end, material="rope", width=4):
    sx, sy = base.iso(*start)
    ex, ey = base.iso(*end)
    draw.line((sx, sy, ex, ey), fill=base.material_rgba(material), width=width)


def draw_coil(draw, center, radius=18, material="rope", fallen=False):
    x, y = base.iso(*center)
    color = base.material_rgba(material)
    outline = base.material_rgba("rope_dark" if material != "fine_rope" else "rope")
    for index in range(4):
        inset = index * 3
        draw.ellipse((x - radius + inset, y - radius // 2 + inset // 2, x + radius - inset, y + radius // 2 - inset // 2), outline=outline, width=2)
    if fallen:
        draw.line((x - radius, y, x + radius, y + 4), fill=color, width=5)
    draw.rectangle((x + radius // 3, y + radius // 3, x + radius // 3 + 10, y + radius // 3 + 5), fill=base.material_rgba("plank_light"))


def draw_platform(draw, level):
    base.draw_iso_box(draw, (0, 0, 0.08), (3.25, 2.35, 0.12), MATERIALS["yard_soil"])
    base.draw_iso_box(draw, (-0.15, -0.08, 0.17), (2.62, 0.46, 0.05), MATERIALS["yard_soil_light"], yaw=0.02)
    if level >= 4:
        for x, y in ((-1.36, -1.00), (1.36, -1.00), (-1.36, 1.00), (1.36, 1.00)):
            base.draw_iso_box(draw, (x, y, 0.18), (0.34, 0.26, 0.20), MATERIALS["stone"], yaw=0.08)
    frame = "premium_wood" if level >= 6 else ("plank" if level >= 2 else "wood")
    for y in (-1.04, 1.04):
        base.draw_iso_box(draw, (0, y, 0.28), (2.70, 0.12, 0.14), MATERIALS[frame], yaw=0.01)


def draw_details(draw, level, state):
    damaged = state in {"damaged", "ruined"}
    empty_input = state == "idle_no_input"
    post_count = 2 + min(3, level // 2)
    xs = [-1.12 + i * (2.24 / max(1, post_count - 1)) for i in range(post_count)]
    for index, x in enumerate(xs):
        mat = "iron" if level >= 7 and index % 2 == 0 else ("premium_wood" if level >= 6 else "wood_dark")
        h = 0.66 + level * 0.035
        base.draw_iso_box(draw, (x, -0.20, h / 2), (0.13, 0.13, h), MATERIALS[mat], yaw=0.16 if damaged and index % 2 == 0 else 0.02)
        base.draw_iso_box(draw, (x, -0.25, h + 0.05), (0.24, 0.055, 0.06), MATERIALS["iron" if h > 0.75 else "wood"], yaw=-0.15)
    if not empty_input and state not in {"construction", "ruined"}:
        for lane in range(1 + min(3, level // 2)):
            y = -0.33 + lane * 0.13
            z = 0.66 + level * 0.035 + lane * 0.035
            draw_beam(draw, (-1.24, y, z), (1.24, y + 0.04, z + 0.02), "fine_rope" if state == "ready" and level >= 3 and lane > 1 else "rope", 4)
    if empty_input:
        base.draw_iso_box(draw, (-1.20, 0.58, 0.19), (0.56, 0.32, 0.035), MATERIALS["yard_soil_light"], yaw=-0.20)
    else:
        for index in range(3 + min(3, level)):
            base.draw_iso_box(draw, (-1.20 + index * 0.035, 0.58 + index * 0.025, 0.28 + index * 0.035), (0.48, 0.07, 0.08), MATERIALS["flax_bundle"], yaw=-0.24 + index * 0.10)
    if level == 1:
        base.draw_iso_box(draw, (-1.34, -0.70, 0.30), (0.42, 0.18, 0.16), MATERIALS["windleaf"], yaw=-0.18)
    if level >= 2:
        base.draw_iso_box(draw, (-0.34, 0.92, 0.52), (0.07, 0.07, 0.84), MATERIALS["wood_dark"])
        base.draw_iso_box(draw, (0.46, 0.90, 0.52), (0.07, 0.07, 0.84), MATERIALS["wood_dark"])
        base.draw_iso_box(draw, (0.06, 0.92, 0.98), (0.98, 0.52, 0.10), MATERIALS["plank"], yaw=-0.03)
    for index in range(1 + (level >= 3) + (level >= 7)):
        mat = "mechanism" if level >= 6 else ("iron" if level >= 5 else "wood_dark")
        base.draw_iso_box(draw, (-0.70 + index * 0.52, -0.72, 0.42), (0.34, 0.52, 0.34), MATERIALS[mat], yaw=0.18 if state == "active" else -0.08)
    if level >= 5:
        base.draw_iso_box(draw, (0.80, -0.74, 0.62), (0.44, 0.08, 0.11), MATERIALS["iron"], yaw=-0.08)
    if level >= 6:
        base.draw_iso_box(draw, (-0.06, -0.82, 0.42), (0.38, 0.30, 0.24), MATERIALS["mechanism"], yaw=0.10)
    if level >= 7:
        for x in (-0.22, 0.22, 0.66):
            base.draw_iso_box(draw, (x, -0.42, 0.62), (0.12, 0.10, 0.10), MATERIALS["copper"], yaw=0.20)
    if state == "ready":
        for index in range(2 + level // 2):
            draw_coil(draw, (-0.70 + index * 0.33, 0.70, 0.30), 15 + level, "rope")
    else:
        draw_coil(draw, (0.84, 0.62, 0.30), 16 + level, "rope", fallen=damaged)
    if level >= 3:
        draw_beam(draw, (1.12, 0.70, 0.78), (1.56, 0.64, 0.78), "wood", 5)
        draw_coil(draw, (1.34, 0.58, 0.32), 15, "fine_rope")
    if level >= 8:
        base.draw_iso_box(draw, (1.62, 0.45, 0.55), (0.16, 0.12, 0.22), MATERIALS["gold"], yaw=-0.18)
    if state == "idle_no_workers":
        base.draw_iso_box(draw, (-0.86, 0.66, 0.30), (0.60, 0.28, 0.16), MATERIALS["plank"], yaw=0.10)
    if state == "construction":
        base.draw_iso_box(draw, (0.58, -0.28, 0.30), (0.92, 0.10, 0.08), MATERIALS["plank"], yaw=-0.38)
        base.draw_iso_box(draw, (0.76, -0.08, 0.38), (0.66, 0.09, 0.07), MATERIALS["wood"], yaw=-0.16)
    if damaged:
        base.draw_iso_box(draw, (-0.52, -0.05, 0.32), (0.70, 0.11, 0.10), MATERIALS["wood_dark"], yaw=0.55)
        draw_beam(draw, (-0.92, -0.25, 0.54), (-0.28, 0.02, 0.32), "rope_dark", 4)
    if state == "ruined":
        base.draw_iso_box(draw, (0.0, -0.06, 0.23), (1.72, 0.50, 0.055), MATERIALS["earth_dark"], yaw=-0.04)
        for x, y, yaw in ((0.48, -0.84, 0.46), (-0.96, 0.10, -0.56), (0.98, 0.20, 0.22)):
            base.draw_iso_box(draw, (x, y, 0.24), (0.74, 0.12, 0.09), MATERIALS["wood_dark"], yaw=yaw)


def draw_png(name, level, state):
    image = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((146, 250, 368, 326), fill=(0, 0, 0, 70))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(11)))
    base.paste_terrain_grass(image)
    draw = ImageDraw.Draw(image)
    draw_platform(draw, level)
    draw_details(draw, level, state)
    image.save(OUT_DIR / f"{name}.png")


def asset_names():
    return [(f"rope_yard_l{level:02d}_{state}", level, state) for level in range(1, 9) for state in STATES]


def validate_report(items):
    result = {"asset": "rope_yard", "assets": [], "png_size": list(PNG_SIZE), "anchor": list(ANCHOR)}
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
        draw.text((x + 8, y + thumb[1] + 4), name.replace("rope_yard_", ""), fill=(232, 245, 244, 255))
    sheet.save(OUT_DIR / "rope_yard_l01_l08_review.png")


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
        "asset_id": "rope_yard",
        "category": "industry",
        "display_name": "Канатный двор",
        "style": "Aeolian bright fantasy stylized mid-poly open craft yard",
        "levels": list(range(1, 9)),
        "states": STATES,
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
    LOG_PATH.write_text("\n".join(lines) + f"\nROPE_YARD_COMPLETE {len(items)}\n")
    print(f"ROPE_YARD_COMPLETE {len(items)}")


if __name__ == "__main__":
    main()
