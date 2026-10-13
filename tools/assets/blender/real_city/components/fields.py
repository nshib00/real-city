"""Field and crop-bed component kit, based on windleaf bed patterns."""

from __future__ import annotations

import math

from .. import geometry
from .common import add_sign, mat

BED_STYLE_PROFILES = {
    "windleaf": {"soil": "earth_warm", "rail": "wood_pale", "post": "wood_dark", "accent": "roof_leaf", "rows": 3},
    "flax": {"soil": "soil_light", "rail": "wood_cut", "post": "wood_beam", "accent": "roof_blue", "rows": 5},
    "seed": {"soil": "earth_warm", "rail": "construction_plank", "post": "wood_dark", "accent": "flower_yellow", "rows": 4},
    "mushroom": {"soil": "soil", "rail": "stone_shadow", "post": "stone_light", "accent": "flower_lilac", "rows": 3},
    "herb": {"soil": "soil_light", "rail": "roof_leaf", "post": "wood_pale", "accent": "flower_white", "rows": 4},
    "reed": {"soil": "sand_shadow", "rail": "wood_beam", "post": "wood_dark", "accent": "glass_cyan", "rows": 3},
}


def add_leaf(name: str, collection, mats: dict, center, *, length=0.42, width=0.12, yaw=0.0, pitch=0.65, roll=0.0, material_role="roof_leaf", vein=True):
    verts = [
        (0, 0, length * 0.52),
        (-width * 0.52, 0, length * 0.08),
        (-width * 0.30, 0, -length * 0.30),
        (0, 0, -length * 0.48),
        (width * 0.30, 0, -length * 0.30),
        (width * 0.52, 0, length * 0.08),
        (0, width * 0.07, length * 0.08),
    ]
    faces = [(0, 1, 6), (1, 2, 6), (2, 3, 6), (3, 4, 6), (4, 5, 6), (5, 0, 6)]
    obj = geometry.mesh(f"{name}_leaf", collection, verts, faces, mat(mats, material_role, "roof_leaf"))
    obj.location = center
    obj.rotation_euler = (pitch, roll, yaw)
    if vein:
        x, y, z = center
        geometry.beam(f"{name}_leaf_vein", collection, (x, y + 0.01, z - length * 0.26), (x, y + 0.01, z + length * 0.34), max(0.010, width * 0.045), mat(mats, "grass_light", "roof_leaf"))
    return obj


def add_log_bed_wall(name: str, collection, mats: dict, *, level=1, width=1.96, depth=1.40):
    rows = 2 if level == 1 else 3
    radius = 0.060
    for row in range(rows):
        z = radius + row * radius * 1.75
        material = mat(mats, "wood_beam" if row % 2 else "wood_dark")
        geometry.beam(f"{name}_front_log_{row}", collection, (-width / 2, -depth / 2, z), (width / 2, -depth / 2, z), radius, material)
        geometry.beam(f"{name}_back_log_{row}", collection, (-width / 2, depth / 2, z), (width / 2, depth / 2, z), radius, material)
        geometry.beam(f"{name}_left_log_{row}", collection, (-width / 2, -depth / 2, z), (-width / 2, depth / 2, z), radius, material)
        geometry.beam(f"{name}_right_log_{row}", collection, (width / 2, -depth / 2, z), (width / 2, depth / 2, z), radius, material)
    for x in (-width / 2, width / 2):
        for y in (-depth / 2, depth / 2):
            geometry.box(f"{name}_corner_post_{x:.1f}_{y:.1f}", collection, (x, y, 0.26), (0.20, 0.20, 0.48), mat(mats, "wood_dark"), bevel=0.035)


def add_plank_bed_wall(name: str, collection, mats: dict, *, width=2.10, depth=1.62):
    for y in (-depth / 2, depth / 2):
        geometry.box(f"{name}_plank_rail_{y:.1f}", collection, (0, y, 0.13), (width, 0.16, 0.22), mat(mats, "wood_pale", "construction_plank"), bevel=0.030)
    for x in (-width / 2, width / 2):
        geometry.box(f"{name}_plank_side_rail_{x:.1f}", collection, (x, 0, 0.13), (0.16, depth, 0.22), mat(mats, "wood_pale", "construction_plank"), bevel=0.030)
    for x in (-width / 2, width / 2):
        for y in (-depth / 2, depth / 2):
            geometry.box(f"{name}_plank_corner_post_{x:.1f}_{y:.1f}", collection, (x, y, 0.30), (0.22, 0.22, 0.54), mat(mats, "wood_dark"), bevel=0.035)


def add_bed_post(name: str, collection, mats: dict, loc, *, style="plain", height=0.36, radius=0.055, material_role="wood_dark"):
    x, y, z = loc
    material = mat(mats, material_role, "wood_dark")
    if style == "round":
        geometry.cylinder(f"{name}_round_post", collection, (x, y, z + height / 2), radius, height, material, vertices=10)
    else:
        geometry.box(f"{name}_{style}_post", collection, (x, y, z + height / 2), (radius * 2.0, radius * 2.0, height), material, bevel=0.012)
    if style in {"carved", "mushroom"}:
        geometry.sphere(f"{name}_{style}_post_cap", collection, (x, y, z + height + radius * 0.45), (radius * 1.35, radius * 1.35, radius * (0.55 if style == "carved" else 0.90)), mat(mats, "wood_pale" if style == "carved" else "flower_lilac", material_role), segments=8)
    elif style == "stone":
        geometry.box(f"{name}_stone_post_cap", collection, (x, y, z + height + 0.035), (radius * 2.5, radius * 2.5, 0.07), mat(mats, "stone_light"), bevel=0.010)


def add_bed_board(name: str, collection, mats: dict, loc, size, *, style="plain", material_role="wood_pale", damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else material_role
    geometry.box(f"{name}_{style}_board", collection, loc, size, mat(mats, role, "wood_pale"), bevel=0.012)
    if style in {"slatted", "flax"}:
        count = 4 if style == "slatted" else 6
        for index in range(count):
            px = x - size[0] * 0.42 + index * size[0] * 0.84 / max(1, count - 1)
            geometry.box(f"{name}_{style}_groove_{index:02d}", collection, (px, y - size[1] * 0.54, z + size[2] * 0.18), (0.016, size[1] * 0.16, size[2] * 0.60), mat(mats, "wood_dark", role), bevel=0.002)
    elif style == "rune":
        for index, px in enumerate((-0.22, 0.0, 0.22)):
            geometry.box(f"{name}_board_rune_{index:02d}", collection, (x + size[0] * px, y - size[1] * 0.55, z + size[2] * 0.22), (size[0] * 0.09, size[1] * 0.15, size[2] * 0.16), mat(mats, "runic_glow", "amethyst"), bevel=0.002, rotation=(0, 0, index * 0.2))


def add_styled_bed_base(name: str, collection, mats: dict, *, style="windleaf", width=2.10, depth=1.62, damaged=False):
    profile = BED_STYLE_PROFILES.get(style, BED_STYLE_PROFILES["windleaf"])
    soil_role = "damage_char" if damaged else profile["soil"]
    geometry.box(f"{name}_{style}_soil_pad", collection, (0, 0, 0.070), (width * 0.76, depth * 0.74, 0.14), mat(mats, soil_role, "earth_warm"), bevel=0.055)
    row_count = profile["rows"]
    for index in range(row_count):
        y = (index - (row_count - 1) / 2) * (depth * 0.55 / max(1, row_count - 1))
        geometry.box(f"{name}_{style}_soil_row_{index:02d}", collection, (0, y, 0.17), (width * (0.56 if style != "flax" else 0.68), depth * 0.08, 0.08), mat(mats, "soil", soil_role), bevel=0.025)
    board_style = "flax" if style == "flax" else "rune" if style == "windleaf" else "slatted" if style == "seed" else "plain"
    post_style = "mushroom" if style == "mushroom" else "stone" if style in {"reed", "herb"} else "carved" if style == "windleaf" else "round"
    rail_role = profile["rail"]
    for y in (-depth / 2, depth / 2):
        add_bed_board(f"{name}_{style}_front_rail_{y:.1f}", collection, mats, (0, y, 0.18), (width, 0.14, 0.20), style=board_style, material_role=rail_role, damaged=damaged)
    for x in (-width / 2, width / 2):
        add_bed_board(f"{name}_{style}_side_rail_{x:.1f}", collection, mats, (x, 0, 0.18), (0.14, depth, 0.20), style=board_style, material_role=rail_role, damaged=damaged)
    for x in (-width / 2, width / 2):
        for y in (-depth / 2, depth / 2):
            add_bed_post(f"{name}_{style}_corner_{x:.1f}_{y:.1f}", collection, mats, (x, y, 0.02), style=post_style, height=0.42, radius=0.060, material_role=profile["post"])
    if style == "mushroom":
        for index, px in enumerate((-0.36, -0.12, 0.18, 0.42)):
            geometry.sphere(f"{name}_mushroom_cap_{index:02d}", collection, (px, -0.20 + 0.16 * (index % 2), 0.30), (0.09, 0.09, 0.050), mat(mats, "flower_lilac"), segments=8)
            geometry.cylinder(f"{name}_mushroom_stem_{index:02d}", collection, (px, -0.20 + 0.16 * (index % 2), 0.225), 0.025, 0.10, mat(mats, "whitewash"), vertices=7)
    elif style == "reed":
        for index in range(5):
            x = -0.48 + index * 0.24
            geometry.beam(f"{name}_reed_marker_{index:02d}", collection, (x, 0.25, 0.18), (x + 0.03, 0.25, 0.62), 0.020, mat(mats, "roof_leaf", "grass_bright"))
    elif style == "flax":
        for index in range(5):
            x = -0.46 + index * 0.23
            geometry.beam(f"{name}_flax_fiber_line_{index:02d}", collection, (x, -0.55, 0.30), (x, 0.55, 0.30), 0.014, mat(mats, "rope", "wood_cut"))


def add_soil_rows(name: str, collection, mats: dict, *, rows=3, width=1.34, y_step=0.38):
    geometry.box(f"{name}_warm_earth_bed", collection, (0, 0, 0.075), (1.72, 1.52, 0.16), mat(mats, "earth_warm"), bevel=0.060)
    offset = (rows - 1) / 2
    for index in range(rows):
        y = (index - offset) * y_step
        geometry.box(f"{name}_raised_soil_row_{index}", collection, (0, y, 0.185), (width, 0.23, 0.12), mat(mats, "soil", "earth_warm"), bevel=0.040)
        geometry.box(f"{name}_soil_highlight_{index}", collection, (-0.08, y - 0.035, 0.257), (0.98, 0.045, 0.018), mat(mats, "soil_light", "path_warm"), bevel=0.010)


def add_windleaf_clusters(name: str, collection, mats: dict, *, level=1, stage=3, damaged=False):
    clusters = [(-0.46, -0.32), (0.0, 0.12), (0.48, -0.18)]
    if level >= 2:
        clusters.append((-0.28, 0.42))
    if level >= 3:
        clusters.append((0.42, 0.38))
    leaves_by_stage = max(2, min(6, stage + 1))
    for ci, (cx, cy) in enumerate(clusters):
        for index in range(leaves_by_stage):
            yaw = (index - leaves_by_stage / 2) * 0.46 + ci * 0.2
            length = 0.20 + stage * 0.105 + level * 0.025
            width = 0.070 + stage * 0.028
            z = 0.32 + stage * 0.045 - (0.06 if damaged and index > 1 else 0)
            add_leaf(f"{name}_windleaf_{ci}_{index}", collection, mats, (cx, cy, z), length=length, width=width, yaw=yaw, material_role="roof_leaf" if index % 2 else "grass_light", vein=stage >= 3)
        geometry.beam(f"{name}_windleaf_stem_{ci}", collection, (cx, cy, 0.25), (cx, cy, 0.40 + stage * 0.035), 0.018 + stage * 0.004, mat(mats, "grass_bright", "roof_leaf"))


def add_support_trellis(name: str, collection, mats: dict, *, height=0.92, width=1.24):
    for x in (-width / 2, width / 2):
        for y in (-0.60, 0.60):
            geometry.beam(f"{name}_support_post_{x:.1f}_{y:.1f}", collection, (x, y, 0), (x, y, height), 0.045, mat(mats, "wood_dark"))
        geometry.beam(f"{name}_support_rope_{x:.1f}", collection, (x, -0.60, height * 0.90), (x, 0.60, height * 0.90), 0.025, mat(mats, "rope", "wood_beam"))


def add_field_bed(name: str, collection, mats: dict, *, level=1, stage=3, super_crop=False, damaged=False):
    add_soil_rows(name, collection, mats, rows=3 if not super_crop else 4)
    if level <= 2:
        add_log_bed_wall(f"{name}_log_wall", collection, mats, level=level)
    else:
        add_plank_bed_wall(f"{name}_plank_wall", collection, mats)
        add_support_trellis(f"{name}_trellis", collection, mats)
    add_windleaf_clusters(name, collection, mats, level=level, stage=stage, damaged=damaged)
    if super_crop:
        for index in range(7):
            yaw = index * math.tau / 7 + 0.14
            add_leaf(f"{name}_super_leaf_{index}", collection, mats, (0, 0, 0.76), length=0.68, width=0.18, yaw=yaw, material_role="amethyst", vein=True)
    if level >= 2:
        add_sign(f"{name}_field_sign", collection, mats, (-1.08, -0.20, 0.62), angle=-0.08)
