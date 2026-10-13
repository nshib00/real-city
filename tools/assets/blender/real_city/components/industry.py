"""Industry component kit built from current mine/quarry/glass/lumber patterns."""

from __future__ import annotations

import math

from .. import geometry
from . import aeolian, props, roofs
from .common import add_chimney, mat


def add_work_shed(name: str, collection, mats: dict, loc=(-0.42, -0.42, 0.0), *, level=1, damaged=False, roof_role="roof_leaf"):
    x, y, z = loc
    width = 1.06 + level * 0.04
    depth = 0.78 + level * 0.025
    post_h = 0.74 + level * 0.035
    post_mat = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, "wood_dark", "wood_beam")
    for sx in (-width / 2, width / 2):
        for sy in (-depth / 2, depth / 2):
            geometry.cylinder(f"{name}_shed_post_{sx:.1f}_{sy:.1f}", collection, (x + sx, y + sy, z + post_h / 2), 0.045, post_h, post_mat, vertices=10)
    roofs.add_shed_roof(f"{name}_shed", collection, mats, (x, y, z + post_h + 0.05), (width + 0.22, depth + 0.16, 0.09), color_role=roof_role, pitch=0.08, damaged=damaged)


def add_furnace(name: str, collection, mats: dict, loc=(0.05, -0.04, 0.0), *, level=1, damaged=False, glass=False):
    x, y, z = loc
    body_role = "damage_char" if damaged else ("brick_warm" if level < 8 else "stone_light")
    geometry.box(f"{name}_furnace_foundation", collection, (x, y, z + 0.18), (1.05 + level * 0.025, 0.78 + level * 0.015, 0.22), mat(mats, "stone_shadow", "stone_light"), bevel=0.030)
    geometry.box(f"{name}_kiln_block_lower", collection, (x, y, z + 0.52), (0.92 + level * 0.018, 0.64 + level * 0.012, 0.58), mat(mats, body_role), bevel=0.055)
    geometry.cylinder(f"{name}_rounded_kiln_crown", collection, (x, y, z + 0.89), 0.42 + level * 0.010, 0.30, mat(mats, body_role), vertices=18)
    geometry.box(f"{name}_furnace_mouth", collection, (x, y - 0.34, z + 0.50), (0.36, 0.050, 0.25), mat(mats, "damage_crack", "damage_char"), bevel=0.010)
    if glass:
        add_glass_pane(f"{name}_hot_sample", collection, mats, (x + 0.52, y - 0.18, z + 0.70), star=level >= 9, broken=damaged)
    if level >= 5:
        geometry.beam(f"{name}_copper_heat_pipe_l", collection, (x - 0.52, y + 0.20, z + 0.52), (x - 0.52, y + 0.58, z + 1.06), 0.024, mat(mats, "copper", "metal_worn"))
        geometry.beam(f"{name}_copper_heat_pipe_r", collection, (x + 0.56, y + 0.20, z + 0.52), (x + 0.56, y + 0.58, z + 1.06), 0.024, mat(mats, "copper", "metal_worn"))


def add_mine_portal(name: str, collection, mats: dict, loc=(0, -0.42, 0), *, level=1, damaged=False):
    x, y, z = loc
    width = 1.24 + level * 0.035
    height = 0.92 + level * 0.030
    arch_variant = "wood" if level <= 2 else "stone" if level <= 4 else "brick" if level <= 5 else "metal" if level <= 8 else "reinforced_concrete"
    add_mine_rock_cheeks(f"{name}_rock", collection, mats, loc=(x, y + 0.04, z), width=width + 0.30, height=height + 0.18, damaged=damaged)
    add_mine_tunnel_depth(f"{name}_tunnel", collection, mats, loc=(x, y - 0.08, z + 0.08), width=width * 0.62, height=height * 0.86, depth=0.44 + level * 0.012)
    add_mine_arch(f"{name}_arch", collection, mats, loc=(x, y - 0.18, z), width=width, height=height, variant=arch_variant, damaged=damaged, reinforced=level >= 6)
    if level >= 3 and not damaged:
        add_mine_lamp_pair(f"{name}_lamps", collection, mats, loc=(x, y - 0.23, z), width=width * 0.62, height=height * 0.62)
    if level >= 5:
        add_mine_rail_segment(f"{name}_portal_rails", collection, mats, loc=(x, y - 0.54, z + 0.035), length=0.86 + level * 0.025, damaged=damaged)


def _mine_arch_roles(variant: str) -> tuple[str, str, str]:
    roles = {
        "wood": ("wood_dark", "wood_beam", "rope"),
        "elite_wood": ("elite_plank", "elite_plank_highlight", "copper"),
        "stone": ("stone_light", "stone_shadow", "moss"),
        "stone_block": ("stone_block", "stone_shadow", "metal_worn"),
        "brick": ("brick_warm", "brick_light", "metal_worn"),
        "metal": ("dark_metal", "steel_light", "copper"),
        "reinforced_concrete": ("reinforced_concrete", "armor", "steel_light"),
        "crystal_reinforced": ("stone_block", "amethyst", "steel_light"),
    }
    return roles.get(variant, roles["stone"])


def add_mine_arch(
    name: str,
    collection,
    mats: dict,
    loc=(0, -0.60, 0),
    *,
    width=1.30,
    height=1.05,
    depth=0.22,
    variant="wood",
    damaged=False,
    reinforced=False,
):
    """Add the single outside mine arch/hood that frames the adit entrance.

    The component intentionally creates only the exterior support. The dark
    tunnel behind it should be added with ``add_mine_tunnel_depth`` instead of
    a second smaller inner arch.
    """

    x, y, z = loc
    main_role, highlight_role, accent_role = _mine_arch_roles(variant)
    main = mat(mats, "damage_char", main_role) if damaged else mat(mats, main_role, "stone_light")
    highlight = mat(mats, highlight_role, main_role)
    accent = mat(mats, accent_role, "metal_worn", "rope")
    post_h = height * 0.68
    inner_w = width * 0.58
    post_x = inner_w * 0.50

    if variant in {"wood", "elite_wood"}:
        post_w = width * 0.085
        for side, sx in (("l", -post_x), ("r", post_x)):
            geometry.beam(f"{name}_{variant}_post_{side}", collection, (x + sx, y, z + 0.06), (x + sx * 0.96, y, z + post_h), post_w, main)
            geometry.box(f"{name}_{variant}_foot_{side}", collection, (x + sx, y, z + 0.045), (post_w * 1.55, depth * 1.12, 0.09), highlight, bevel=0.008)
        geometry.box(f"{name}_{variant}_top_lintel", collection, (x, y, z + post_h + height * 0.075), (width * 0.86, depth, height * 0.13), main, bevel=0.015, rotation=(0, 0, math.radians(-3 if variant == "wood" else 0)))
        geometry.box(f"{name}_{variant}_cap_plank", collection, (x, y - depth * 0.11, z + post_h + height * 0.18), (width * 0.94, depth * 0.78, height * 0.08), highlight, bevel=0.010)
        for side, sx in (("l", -post_x), ("r", post_x)):
            geometry.beam(f"{name}_{variant}_brace_{side}", collection, (x + sx, y - depth * 0.30, z + post_h * 0.64), (x + sx * 0.48, y - depth * 0.16, z + post_h + height * 0.11), post_w * 0.72, main)
        if variant == "wood":
            for side, sx in (("l", -post_x), ("r", post_x)):
                geometry.cylinder(f"{name}_rope_lashing_{side}", collection, (x + sx, y - depth * 0.52, z + post_h * 0.62), post_w * 0.72, 0.030, accent, vertices=8, rotation=(math.radians(90), 0, 0))
        else:
            for side, sx in (("l", -post_x), ("r", post_x)):
                geometry.box(f"{name}_copper_pin_{side}", collection, (x + sx, y - depth * 0.53, z + post_h * 0.72), (post_w * 0.60, 0.030, post_w * 0.60), accent, bevel=0.004)
    elif variant in {"stone", "stone_block", "brick"}:
        block_rows = 4 if variant == "stone" else 5
        block_h = post_h / block_rows
        block_w = width * (0.12 if variant == "brick" else 0.15)
        for side, sx in (("l", -post_x), ("r", post_x)):
            for row in range(block_rows):
                if damaged and (row + (0 if side == "l" else 1)) % 4 == 0:
                    continue
                geometry.box(
                    f"{name}_{variant}_pier_{side}_{row:02d}",
                    collection,
                    (x + sx + (0.012 if row % 2 else -0.010), y, z + block_h * (row + 0.5)),
                    (block_w * (0.86 if row % 2 else 1.04), depth, block_h * 0.88),
                    highlight if row % 3 == 0 else main,
                    bevel=0.012 if variant == "brick" else 0.020,
                )
        arch_blocks = 7 if variant == "brick" else 9
        radius_x = width * 0.34
        radius_z = height * 0.25
        center_z = post_h
        for index in range(arch_blocks):
            angle = math.pi - index * math.pi / (arch_blocks - 1)
            bx = x + math.cos(angle) * radius_x
            bz = z + center_z + math.sin(angle) * radius_z
            if damaged and index in {1, arch_blocks - 2}:
                continue
            geometry.box(
                f"{name}_{variant}_voussoir_{index:02d}",
                collection,
                (bx, y - depth * 0.02, bz),
                (width * (0.13 if variant == "brick" else 0.15), depth * 1.04, height * 0.105),
                highlight if index == arch_blocks // 2 else main,
                bevel=0.010 if variant == "brick" else 0.018,
                rotation=(0, -angle + math.pi / 2, 0),
            )
        if reinforced:
            geometry.box(f"{name}_{variant}_iron_tie", collection, (x, y - depth * 0.58, z + center_z + radius_z * 0.24), (width * 0.78, 0.035, height * 0.035), accent, bevel=0.005)
    else:
        post_w = width * 0.080
        for side, sx in (("l", -post_x), ("r", post_x)):
            geometry.box(f"{name}_{variant}_metal_post_{side}", collection, (x + sx, y, z + post_h * 0.50), (post_w, depth * 0.72, post_h), main, bevel=0.010)
            geometry.box(f"{name}_{variant}_base_plate_{side}", collection, (x + sx, y, z + 0.035), (post_w * 1.90, depth, 0.070), highlight, bevel=0.006)
        geometry.box(f"{name}_{variant}_top_beam", collection, (x, y, z + post_h + height * 0.10), (width * 0.86, depth * 0.72, height * 0.105), main, bevel=0.008)
        for offset in (-0.24, 0.0, 0.24):
            geometry.box(f"{name}_{variant}_rib_{offset:.2f}", collection, (x + width * offset, y - depth * 0.46, z + post_h * 0.55), (post_w * 0.68, 0.035, post_h * 0.88), highlight, bevel=0.004)
        if reinforced:
            for sx in (-post_x, post_x):
                geometry.beam(f"{name}_{variant}_diagonal_tie_{sx:.1f}", collection, (x + sx, y - depth * 0.48, z + post_h * 0.20), (x - sx * 0.32, y - depth * 0.48, z + post_h + height * 0.13), post_w * 0.46, accent)
        if variant == "crystal_reinforced":
            geometry.aeolian_crystal(f"{name}_small_depth_crystal", collection, (x, y - depth * 0.56, z + post_h + height * 0.13), width * 0.035, height * 0.18, mat(mats, "amethyst", "runic_glow"))


def add_mine_tunnel_depth(name: str, collection, mats: dict, loc=(0, -0.70, 0.08), *, width=0.78, height=0.78, depth=0.48):
    """Add visible adit depth behind the exterior arch without creating another arch."""

    x, y, z = loc
    shadow = mat(mats, "damage_crack", "coal")
    side = mat(mats, "stone_shadow", "stone_light")
    floor = mat(mats, "soil", "earth_warm")
    geometry.box(f"{name}_deep_back_shadow", collection, (x, y - depth * 0.56, z + height * 0.42), (width * 0.54, 0.040, height * 0.66), shadow, bevel=0.006)
    geometry.box(f"{name}_mid_shadow", collection, (x, y - depth * 0.30, z + height * 0.38), (width * 0.70, 0.045, height * 0.76), shadow, bevel=0.008)
    geometry.box(f"{name}_floor_plane", collection, (x, y - depth * 0.18, z + height * 0.05), (width * 0.76, depth * 0.76, 0.055), floor, bevel=0.010, rotation=(0.08, 0, 0))
    geometry.beam(f"{name}_left_wall_plane", collection, (x - width * 0.36, y + depth * 0.08, z + 0.12), (x - width * 0.24, y - depth * 0.58, z + height * 0.62), 0.055, side)
    geometry.beam(f"{name}_right_wall_plane", collection, (x + width * 0.36, y + depth * 0.08, z + 0.12), (x + width * 0.24, y - depth * 0.58, z + height * 0.62), 0.055, side)


def add_mine_rock_cheeks(name: str, collection, mats: dict, loc=(0, -0.42, 0), *, width=1.58, height=1.18, damaged=False):
    """Compact hard-rock mass around the entrance, sized for a 1x1 mine."""

    x, y, z = loc
    rock = mat(mats, "damage_char", "stone_shadow") if damaged else mat(mats, "stone_shadow", "stone_light")
    light = mat(mats, "stone_light", "stone_block")
    chunks = (
        (-0.42, 0.00, 0.48, 0.34, 0.36, 0.82, -0.10),
        (0.42, 0.02, 0.48, 0.34, 0.36, 0.82, 0.12),
        (-0.20, 0.08, 0.92, 0.46, 0.34, 0.36, 0.04),
        (0.22, 0.08, 0.92, 0.48, 0.34, 0.34, -0.04),
        (-0.58, 0.18, 0.22, 0.28, 0.30, 0.34, 0.18),
        (0.58, 0.18, 0.22, 0.28, 0.30, 0.34, -0.16),
    )
    for index, (ox, oy, oz, sx, sy, sz, rz) in enumerate(chunks):
        if damaged and index == 2:
            continue
        geometry.box(
            f"{name}_hard_rock_chunk_{index:02d}",
            collection,
            (x + ox * width, y + oy, z + oz * height),
            (sx * width, sy, sz * height),
            light if index % 3 == 0 and not damaged else rock,
            bevel=0.040,
            rotation=(0, 0, rz),
        )
    for index in range(5):
        geometry.box(
            f"{name}_fallen_stone_{index:02d}",
            collection,
            (x - width * 0.42 + index * width * 0.21, y - 0.46 - 0.03 * (index % 2), z + 0.055),
            (0.16 + 0.03 * (index % 2), 0.11, 0.075),
            rock,
            bevel=0.014,
            rotation=(0, 0, index * 0.47),
        )


def add_mine_rail_segment(name: str, collection, mats: dict, loc=(0, -0.85, 0.04), *, length=1.05, gauge=0.38, damaged=False):
    x, y, z = loc
    rail = mat(mats, "damage_char", "metal_worn") if damaged else mat(mats, "metal_worn", "steel_light")
    sleeper = mat(mats, "wood_dark", "wood_beam")
    for sx in (-gauge / 2, gauge / 2):
        geometry.box(f"{name}_rail_{sx:.1f}", collection, (x + sx, y, z + 0.035), (0.035, length, 0.045), rail, bevel=0.004, rotation=(0.03 if damaged else 0, 0, 0.02 if sx > 0 and damaged else 0))
    for index in range(4):
        oy = y - length * 0.40 + index * length * 0.26
        geometry.box(f"{name}_sleeper_{index:02d}", collection, (x, oy, z), (gauge + 0.24, 0.060, 0.050), sleeper, bevel=0.006, rotation=(0, 0, 0.04 * (index % 2)))


def add_mine_lamp_pair(name: str, collection, mats: dict, loc=(0, -0.78, 0), *, width=0.70, height=0.66, damaged=False):
    x, y, z = loc
    for side, sx in (("l", -width * 0.50), ("r", width * 0.50)):
        post = mat(mats, "damage_char", "metal_worn") if damaged else mat(mats, "metal_worn", "dark_metal")
        geometry.beam(f"{name}_lamp_bracket_{side}", collection, (x + sx, y, z + height * 0.70), (x + sx * 0.88, y - 0.10, z + height * 0.84), 0.018, post)
        geometry.cylinder(f"{name}_lamp_body_{side}", collection, (x + sx * 0.84, y - 0.11, z + height * 0.62), 0.045, 0.090, post, vertices=8)
        if not damaged:
            geometry.sphere(f"{name}_lamp_glow_{side}", collection, (x + sx * 0.84, y - 0.13, z + height * 0.60), (0.040, 0.040, 0.050), mat(mats, "window_warm"), segments=8)


def add_mine_ore_pile(name: str, collection, mats: dict, loc=(0.66, -0.76, 0.08), *, kind="stone", count=6, damaged=False):
    x, y, z = loc
    role = "coal" if kind == "coal" else "copper" if kind == "copper" else "stone_shadow"
    material = mat(mats, "damage_char", role) if damaged else mat(mats, role, "stone_shadow")
    for index in range(count):
        geometry.box(
            f"{name}_{kind}_chunk_{index:02d}",
            collection,
            (x + (index % 3 - 1) * 0.11, y + (index // 3) * 0.10, z + 0.035 * (index % 2)),
            (0.13 + 0.02 * (index % 2), 0.10, 0.08),
            material,
            bevel=0.018,
            rotation=(0.03, 0.02, index * 0.54),
        )


def add_mine_hoist(name: str, collection, mats: dict, loc=(0.72, -0.36, 0.0), *, level=1, damaged=False):
    x, y, z = loc
    frame = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, "wood_dark" if level < 7 else "metal_worn", "wood_beam")
    metal = mat(mats, "metal_worn", "steel_light")
    height = 0.82 + level * 0.035
    geometry.beam(f"{name}_hoist_left_leg", collection, (x - 0.22, y, z + 0.06), (x - 0.08, y, z + height), 0.045, frame)
    geometry.beam(f"{name}_hoist_right_leg", collection, (x + 0.22, y, z + 0.06), (x + 0.08, y, z + height), 0.045, frame)
    geometry.box(f"{name}_hoist_top", collection, (x, y, z + height), (0.62, 0.08, 0.070), frame, bevel=0.008)
    geometry.cylinder(f"{name}_hoist_winch", collection, (x, y - 0.055, z + height * 0.68), 0.105, 0.16, metal, vertices=12, rotation=(math.radians(90), 0, 0))
    geometry.cylinder(f"{name}_hoist_rope", collection, (x, y - 0.075, z + height * 0.43), 0.012, height * 0.46, mat(mats, "rope", "wood_dark"), vertices=8)
    geometry.box(f"{name}_hoist_bucket", collection, (x, y - 0.075, z + height * 0.18), (0.20, 0.16, 0.14), mat(mats, "metal_worn", "wood_dark"), bevel=0.012)


def add_mine_vent_pipe(name: str, collection, mats: dict, loc=(-0.78, -0.36, 0.10), *, height=0.90, damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else "metal_worn"
    geometry.cylinder(f"{name}_vent_vertical", collection, (x, y, z + height * 0.50), 0.055, height, mat(mats, role, "metal_worn"), vertices=12)
    geometry.cylinder(f"{name}_vent_elbow", collection, (x + 0.12, y, z + height * 0.92), 0.050, 0.26, mat(mats, role, "metal_worn"), vertices=12, rotation=(0, math.radians(90), 0))
    geometry.box(f"{name}_vent_cap", collection, (x + 0.26, y, z + height * 0.92), (0.08, 0.12, 0.10), mat(mats, role, "metal_worn"), bevel=0.010)


def add_mine_explosive_crate(name: str, collection, mats: dict, loc=(-0.66, -0.78, 0.14), *, closed=True, damaged=False):
    x, y, z = loc
    wood = mat(mats, "damage_char", "wood_dark") if damaged else mat(mats, "wood_dark", "wood_beam")
    accent = mat(mats, "roof_red", "brick_warm")
    geometry.box(f"{name}_blast_crate_body", collection, (x, y, z), (0.34, 0.26, 0.22), wood, bevel=0.012)
    if closed:
        geometry.box(f"{name}_blast_crate_lid", collection, (x, y, z + 0.13), (0.37, 0.28, 0.045), wood, bevel=0.006)
    geometry.box(f"{name}_blast_warning_band", collection, (x, y - 0.135, z + 0.03), (0.24, 0.020, 0.045), accent, bevel=0.002)


def add_mine_detail_cluster(name: str, collection, mats: dict, loc=(0, -0.70, 0), *, level=1, damaged=False):
    """Readable mine props around the portal: rails, cart, ore, tools and late machinery."""

    x, y, z = loc
    add_mine_rail_segment(f"{name}_rails", collection, mats, (x, y, z + 0.035), length=1.0 + level * 0.035, damaged=damaged)
    add_mine_cart(f"{name}_cart", collection, mats, (x + 0.48, y + 0.02, z + 0.25), loaded=not damaged, damaged=damaged)
    add_mine_ore_pile(f"{name}_ore", collection, mats, (x - 0.62, y + 0.02, z + 0.08), kind="coal" if level >= 3 else "stone", count=5 + min(level, 4), damaged=damaged)
    props.add_tool_rack(f"{name}_tools", collection, mats, (x - 0.84, y + 0.30, z + 0.02), tools=("pick", "shovel", "hammer"))
    if level >= 6:
        add_mine_hoist(f"{name}_hoist", collection, mats, (x + 0.78, y + 0.34, z), level=level, damaged=damaged)
        add_mine_explosive_crate(f"{name}_charges", collection, mats, (x - 0.72, y - 0.20, z + 0.14), damaged=damaged)
    if level >= 8:
        add_mine_vent_pipe(f"{name}_vent", collection, mats, (x - 0.88, y + 0.16, z + 0.06), height=0.88 + level * 0.025, damaged=damaged)


def add_mine_cart(name: str, collection, mats: dict, loc=(0.65, -0.72, 0.24), *, loaded=True, damaged=False):
    role = "damage_char" if damaged else "metal_worn"
    geometry.box(f"{name}_cart_bin", collection, loc, (0.52, 0.34, 0.22), mat(mats, role, "metal_worn"), bevel=0.030, rotation=(0.0 if not damaged else 0.20, 0.0, -0.06))
    x, y, z = loc
    if loaded:
        geometry.box(f"{name}_cart_load", collection, (x, y, z + 0.17), (0.42, 0.24, 0.08), mat(mats, "coal", "stone_shadow"), bevel=0.020, rotation=(0, 0, -0.06))
    for sx in (-0.18, 0.18):
        for sy in (-0.13, 0.13):
            geometry.cylinder(f"{name}_cart_wheel_{sx}_{sy}", collection, (x + sx, y + sy, z - 0.13), 0.055, 0.030, mat(mats, "metal_worn"), vertices=12, rotation=(math.radians(90), 0, 0))


def add_conveyor(name: str, collection, mats: dict, loc, *, length=1.4, angle=-0.35, belt_role="sand_shadow", damaged=False):
    x, y, z = loc
    frame = mat(mats, "damage_char", "steel_light") if damaged else mat(mats, "steel_light", "metal_worn")
    belt = mat(mats, belt_role, "earth_warm")
    geometry.box(f"{name}_conveyor_belt", collection, (x, y, z), (length, 0.28, 0.065), belt, bevel=0.012, rotation=(-0.10, 0, angle))
    geometry.box(f"{name}_conveyor_frame", collection, (x, y, z + 0.05), (length + 0.12, 0.36, 0.045), frame, bevel=0.010, rotation=(-0.10, 0, angle))
    for offset in (-length * 0.38, length * 0.38):
        geometry.beam(f"{name}_conveyor_leg_{offset:.1f}", collection, (x + offset, y - 0.13, z - 0.28), (x + offset * 0.96, y - 0.10, z), 0.035, frame)


def add_crane(name: str, collection, mats: dict, loc=(0.96, -0.18, 0.0), *, height=1.36, damaged=False):
    x, y, z = loc
    role = "damage_char" if damaged else "wood_beam"
    geometry.cylinder(f"{name}_crane_post", collection, (x, y, z + height / 2), 0.07, height, mat(mats, role), vertices=12)
    geometry.box(f"{name}_crane_arm", collection, (x - 0.42, y + 0.04, z + height * 0.92), (1.14, 0.09, 0.10), mat(mats, role), bevel=0.012, rotation=(0, 0, math.radians(-8)))
    geometry.cylinder(f"{name}_crane_rope", collection, (x - 0.84, y + 0.05, z + height * 0.62), 0.015, 0.54, mat(mats, "rope", "wood_dark"), vertices=8)
    geometry.box(f"{name}_crane_hook", collection, (x - 0.84, y + 0.05, z + height * 0.36), (0.12, 0.05, 0.12), mat(mats, "metal_worn"), bevel=0.006, rotation=(0, 0, math.radians(22)))


def add_glass_pane(name: str, collection, mats: dict, loc, *, width=0.22, height=0.26, star=False, broken=False, angle=0.0):
    x, y, z = loc
    pane_role = "glass_broken" if broken else ("star_glass" if star else "glass_cyan")
    geometry.box(f"{name}_pane", collection, loc, (width, 0.035, height), mat(mats, pane_role, "glass_cyan"), bevel=0.004, rotation=(0, 0, angle))
    geometry.box(f"{name}_edge_top", collection, (x, y - 0.004, z + height * 0.52), (width + 0.060, 0.045, 0.026), mat(mats, "glass_edge", "glass_cyan"), bevel=0.003, rotation=(0, 0, angle))
    if broken:
        geometry.beam(f"{name}_crack_a", collection, (x - width * 0.30, y - 0.036, z + height * 0.16), (x + width * 0.28, y - 0.036, z - height * 0.18), 0.009, mat(mats, "glass_edge", "glass_cyan"))


def add_resource_processing_line(name: str, collection, mats: dict, *, level=1, damaged=False, resource="wood"):
    add_work_shed(f"{name}_shed", collection, mats, level=level, damaged=damaged, roof_role="roof_leaf" if resource == "wood" else "roof_rune_tile" if resource == "rune_tile" else "roof_teal")
    if resource == "wood":
        props.add_plank_stack(f"{name}_planks", collection, mats, (-0.78, -0.10, 0.10), rows=3, count=4)
        add_crane(f"{name}_crane", collection, mats, damaged=damaged)
    elif resource in {"sand", "stone"}:
        add_conveyor(f"{name}_conveyor", collection, mats, (0.22, 0.42, 0.70), damaged=damaged, belt_role="earth_warm")
    elif resource == "glass":
        add_furnace(f"{name}_furnace", collection, mats, level=level, damaged=damaged, glass=True)
        aeolian.add_lens(f"{name}_lens", collection, mats, (0.72, -0.46, 0.56))
    else:
        props.add_workbench(f"{name}_bench", collection, mats, (0.45, -0.45, 0.12))
        add_chimney(f"{name}_utility", collection, mats, (-0.52, 0.30, 0.76), damaged=damaged)
