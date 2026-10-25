"""Reusable green-roof stone-house dormers, annexes, floors, porch and planting."""

from __future__ import annotations

import math

from .. import geometry
from . import landscaping, roofs
from .common import add_chimney, add_door, add_scaffold, add_window, mat


def add_round_attic_window(name, collection, mats, *, main_depth, roof_z, level, damaged=False):
    """Small round attic window in a supported dormer on the visible roof slope."""
    roof_depth = main_depth + 0.24 + (0.08 if level >= 2 else 0)
    roof_width = 1.42 + level * 0.05
    roof_width *= math.sqrt(1.10) * (1.08 if level >= 5 else 1.0)
    roof_width += 0.40
    x, y = 0.24, -roof_depth * 0.30
    surface_z = roof_z + 0.39 * (1 - x / (roof_width / 2))
    stone = mat(mats, "damage_char" if damaged else "stone_light")
    rim = mat(mats, "copper", "metal_worn")
    geometry.box(f"{name}_stone_dormer_body", collection,
                 (x, y, surface_z + 0.12), (0.30, 0.24, 0.27),
                 stone, bevel=0.014)
    roofs.add_gable_roof(f"{name}_little_green_roof", collection, mats,
                         (x, y, surface_z + 0.245), (0.37, 0.33, 0.12),
                         color_role="roof_green", damaged=damaged)
    face_y = y - 0.137
    z = surface_z + 0.135
    geometry.cylinder(f"{name}_stone_socket", collection, (x, face_y, z),
                      0.103, 0.030, mat(mats, "stone_shadow"), vertices=24,
                      rotation=(math.pi / 2, 0, 0))
    geometry.cylinder(f"{name}_copper_round_frame", collection,
                      (x, face_y - 0.020, z), 0.085, 0.023, rim,
                      vertices=32, rotation=(math.pi / 2, 0, 0))
    geometry.cylinder(f"{name}_round_glass", collection,
                      (x, face_y - 0.038, z), 0.065, 0.012,
                      mat(mats, "damage_crack" if damaged else "glass_cyan"),
                      vertices=32, rotation=(math.pi / 2, 0, 0))
    geometry.box(f"{name}_window_sill", collection,
                 (x, face_y - 0.025, surface_z + 0.028),
                 (0.24, 0.072, 0.040), stone, bevel=0.005)


def add_annex_entry_door(name, collection, mats, *, annex, damaged=False):
    """Visible side entrance to the expanded level-five stone annex."""
    x = annex["x"] + annex["width"] / 2 + 0.088
    y = annex["y"] + 0.23
    wood = mat(mats, "damage_char" if damaged else "wood_dark")
    metal = mat(mats, "metal_worn", "copper")
    geometry.box(f"{name}_door", collection, (x, y, 0.515),
                 (0.058, 0.35, 0.61), wood, bevel=0.012)
    for index in range(3):
        geometry.box(f"{name}_plank_{index}", collection,
                     (x + 0.020, y - 0.11 + index * 0.11, 0.515),
                     (0.018, 0.082, 0.58), mat(mats, "wood_beam"), bevel=0.005)
    for z in (0.37, 0.64):
        geometry.box(f"{name}_iron_band_{z}", collection,
                     (x + 0.022, y, z), (0.016, 0.30, 0.026), metal, bevel=0.004)
    geometry.box(f"{name}_handle", collection,
                 (x + 0.020, y - 0.105, 0.53),
                 (0.025, 0.040, 0.045), mat(mats, "roof_gold"), bevel=0.005)
    geometry.box(f"{name}_stone_lintel", collection,
                 (x - 0.020, y, 0.854), (0.085, 0.46, 0.065),
                 mat(mats, "stone_block"), bevel=0.009)
    geometry.box(f"{name}_stone_threshold", collection,
                 (x - 0.010, y, 0.19), (0.075, 0.46, 0.08),
                 mat(mats, "stone_block"), bevel=0.012)
    geometry.box(f"{name}_entry_step", collection,
                 (x - 0.006, y, 0.095), (0.052, 0.49, 0.10),
                 mat(mats, "stone_light"), bevel=0.012)
from .foundations import add_foundation


def add_triangular_side_dormer(name, collection, mats, *, main_width, roof_z, damaged=False):
    """A gabled dormer on the visible right roof slope with a triangular side pane."""
    x, y = main_width * 0.27, 0.18
    base = roof_z + 0.17
    stone = mat(mats, "damage_char" if damaged else "stone_light")
    geometry.box(f"{name}_stone_cheek", collection, (x, y, base + 0.14),
                 (0.46, 0.48, 0.30), stone, bevel=0.017)
    roof = geometry.gable_roof(f"{name}_green_gable", collection,
                               (x, y, base + 0.27), (0.48, 0.62, 0.20),
                               mat(mats, "damage_char" if damaged else "roof_green"))
    roof.rotation_euler[2] = math.pi / 2
    geometry.beam(f"{name}_copper_ridge", collection,
                  (x - 0.34, y, base + 0.48), (x + 0.34, y, base + 0.48),
                  0.035, mat(mats, "copper"))
    for side in (-1, 1):
        for index in range(3):
            yy = y + side * (0.05 + index * 0.075)
            zz = base + 0.47 - abs(yy - y) * 0.78
            geometry.box(f"{name}_roof_tile_{side}_{index}", collection,
                         (x, yy, zz), (0.52, 0.090, 0.027),
                         mat(mats, "roof_green" if not damaged or index != 2 else "damage_char"),
                         bevel=0.006, rotation=(side * 0.39, 0, 0))
    # The two triangles stand on the +X end wall, facing the isometric camera.
    face_x = x + 0.322
    geometry.mesh(f"{name}_triangular_stone_surround", collection,
                  [(face_x, y - 0.17, base + 0.105),
                   (face_x, y + 0.17, base + 0.105),
                   (face_x, y, base + 0.355)], [(0, 1, 2)],
                  mat(mats, "stone_shadow"))
    geometry.mesh(f"{name}_triangular_glass", collection,
                  [(face_x + 0.009, y - 0.115, base + 0.133),
                   (face_x + 0.009, y + 0.115, base + 0.133),
                   (face_x + 0.009, y, base + 0.302)], [(0, 1, 2)],
                  mat(mats, "damage_crack" if damaged else "glass_cyan", "window_warm"))
    rim = mat(mats, "copper", "metal_worn")
    corners = [(face_x + 0.018, y - 0.17, base + 0.105),
               (face_x + 0.018, y + 0.17, base + 0.105),
               (face_x + 0.018, y, base + 0.355)]
    for index, (a, b) in enumerate(((0, 1), (1, 2), (2, 0))):
        geometry.beam(f"{name}_copper_frame_{index}", collection,
                      corners[a], corners[b], 0.020, rim)
    geometry.box(f"{name}_stone_sill", collection,
                 (face_x + 0.025, y, base + 0.105),
                 (0.075, 0.40, 0.055), stone, bevel=0.007)


def _stone_clad_box(name, collection, mats, *, x, y, width, depth, bottom, height, damaged=False, sides=("front", "right", "back")):
    geometry.box(f"{name}_stone_core", collection, (x, y, bottom + height / 2),
                 (width, depth, height),
                 mat(mats, "damage_char" if damaged else "stone_light"), bevel=0.025)
    rows = max(4, round(height / 0.16))
    for side in sides:
        count = 5 if side in ("front", "back") else 6
        span = width if side in ("front", "back") else depth
        for row in range(rows):
            for col in range(count):
                p = -span / 2 + (col + 0.5 + (row % 2) * 0.12) * span / count
                z = bottom + (row + 0.5) * height / rows
                role = "stone_shadow" if damaged and (row + col) % 9 == 0 else ("stone_light" if (row + col) % 2 else "stone_block")
                if side in ("front", "back"):
                    px, py = x + p, y + (-1 if side == "front" else 1) * (depth / 2 + 0.037)
                    size = (span / count - 0.012, 0.065, height / rows - 0.011)
                else:
                    px, py = x + width / 2 + 0.037, y + p
                    size = (0.065, span / count - 0.012, height / rows - 0.011)
                geometry.box(f"{name}_{side}_block_{row:02d}_{col:02d}", collection,
                             (px, py, z), size, mat(mats, role), bevel=0.007)


def _green_annex_roof(name, collection, mats, *, x, y, width, depth, roof_z, damaged=False):
    size = (width + 0.20, depth + 0.17, 0.26)
    roofs.add_gable_roof(name, collection, mats, (x, y, roof_z), size,
                         color_role="roof_green", damaged=damaged)
    for side in (-1, 1):
        for row in range(4):
            dx = side * (row + 0.5) * size[0] / 8
            z = roof_z + 0.26 * (1 - abs(dx) / (size[0] / 2)) + 0.025
            for col in range(5):
                py = y - size[1] * 0.42 + col * size[1] * 0.21
                geometry.box(f"{name}_tile_{side}_{row}_{col}", collection,
                             (x + dx, py, z), (size[0] / 8 + 0.012, size[1] * 0.20, 0.028),
                             mat(mats, "roof_green" if not damaged or (row + col) % 7 else "damage_char"),
                             bevel=0.006, rotation=(0, side * 0.47, 0))
    geometry.box(f"{name}_copper_gutter", collection,
                 (x + size[0] * 0.47, y, roof_z + 0.035),
                 (0.055, size[1] + 0.035, 0.055), mat(mats, "copper"), bevel=0.008)


def add_right_stone_annex(name, collection, mats, *, main_width, level, damaged=False):
    """Grounded right-hand annex with its own side window, green roof and flue."""
    width, depth, height = (0.86, 1.12, 0.91) if level >= 5 else (0.69, 1.00, 0.77)
    x = main_width / 2 + width / 2 - 0.13
    y = 0.06
    add_foundation(f"{name}_foundation", collection, mats, width=width, depth=depth,
                   height="low", thickness="thin", material="stone_block", loc=(x, y, 0), damaged=damaged)
    _stone_clad_box(name, collection, mats, x=x, y=y, width=width, depth=depth,
                    bottom=0.20, height=height, damaged=damaged)
    roof_z = 0.20 + height
    _green_annex_roof(f"{name}_roof", collection, mats,
                      x=x, y=y, width=width, depth=depth, roof_z=roof_z, damaged=damaged)
    side_x = x + width / 2 + (0.058 if level >= 5 else 0.088)
    geometry.box(f"{name}_side_window_stone_frame", collection,
                 (side_x, y + (-0.27 if level >= 5 else -0.12), 0.20 + height * 0.58),
                 (0.060, 0.35, 0.36), mat(mats, "stone_block"), bevel=0.011)
    geometry.box(f"{name}_side_window_warm_glass", collection,
                 (side_x + 0.033, y + (-0.27 if level >= 5 else -0.12), 0.20 + height * 0.58),
                 (0.024, 0.255, 0.26),
                 mat(mats, "damage_crack" if damaged else "window_warm"), bevel=0.006)
    for offset in (-0.11, 0.11):
        geometry.box(f"{name}_side_window_mullion_{offset}", collection,
                     (side_x + 0.05, y + (-0.27 if level >= 5 else -0.12) + offset, 0.20 + height * 0.58),
                     (0.017, 0.020, 0.28), mat(mats, "copper"), bevel=0.003)
    chimney_x = x + width * 0.15
    chimney_y = y + depth * 0.23
    add_chimney(f"{name}_chimney", collection, mats,
                (chimney_x, chimney_y, roof_z + 0.18), height=0.45, radius=0.085,
                damaged=damaged)
    return {"x": x, "y": y, "width": width, "depth": depth, "roof_z": roof_z,
            "height": height}


def add_second_storey_details(name, collection, mats, *, main_width, main_depth, main_height, damaged=False):
    """Visible floor belt and large upper windows for the full-height stone shell."""
    front = -main_depth / 2 - 0.093
    floor_z = 1.15
    roof_z = 0.22 + main_height
    upper_z = floor_z + (roof_z - floor_z) * 0.52
    stone = mat(mats, "damage_char" if damaged else "stone_block")
    geometry.box(f"{name}_second_floor_front_belt", collection,
                 (0, front + 0.015, floor_z),
                 (main_width + 0.08, 0.105, 0.11), stone, bevel=0.012)
    geometry.box(f"{name}_second_floor_right_belt", collection,
                 (main_width / 2 + 0.042, 0, floor_z),
                 (0.105, main_depth + 0.06, 0.11), stone, bevel=0.012)
    for side in (-1, 1):
        x = side * main_width * 0.285
        add_window(f"{name}_upper_window_{side}", collection, mats,
                   (x, front - 0.01, upper_z), (0.38, 0.05, 0.37),
                   frame_role="copper", damaged=damaged)
        geometry.box(f"{name}_upper_window_stone_sill_{side}", collection,
                     (x, front - 0.055, upper_z - 0.25),
                     (0.48, 0.15, 0.06), mat(mats, "stone_light"), bevel=0.008)
    geometry.box(f"{name}_right_upper_window_frame", collection,
                 (main_width / 2 + 0.095, 0.10, upper_z),
                 (0.06, 0.44, 0.41), stone, bevel=0.011)
    geometry.box(f"{name}_right_upper_window_glass", collection,
                 (main_width / 2 + 0.128, 0.10, upper_z),
                 (0.025, 0.34, 0.31), mat(mats, "damage_crack" if damaged else "window_warm"),
                 bevel=0.006)
    geometry.box(f"{name}_copper_top_cornice", collection,
                 (0, front + 0.04, roof_z - 0.06),
                 (main_width + 0.13, 0.10, 0.06), mat(mats, "copper"), bevel=0.008)


def add_stone_entrance_porch(name, collection, mats, *, main_depth, damaged=False):
    """A porch with two columns, stone steps and a green pitched canopy."""
    front = -main_depth / 2
    porch_y = front - 0.28
    geometry.box(f"{name}_landing", collection, (0, porch_y, 0.13),
                 (0.91, 0.48, 0.16), mat(mats, "stone_block"), bevel=0.018)
    for i in range(2):
        geometry.box(f"{name}_step_{i}", collection,
                     (0, porch_y - 0.32 - i * 0.11, 0.075 - i * 0.025),
                     (0.94 + i * 0.10, 0.16, 0.09), mat(mats, "stone_light"), bevel=0.012)
    for side in (-1, 1):
        geometry.box(f"{name}_stone_column_{side}", collection,
                     (side * 0.41, porch_y - 0.11, 0.66),
                     (0.11, 0.11, 1.05), mat(mats, "stone_light"), bevel=0.010)
        geometry.box(f"{name}_column_cap_{side}", collection,
                     (side * 0.41, porch_y - 0.11, 1.20),
                     (0.17, 0.17, 0.07), mat(mats, "stone_block"), bevel=0.009)
    roofs.add_gable_roof(f"{name}_canopy", collection, mats,
                         (0, porch_y - 0.04, 1.23), (1.08, 0.65, 0.18),
                         color_role="roof_green", damaged=damaged)
    geometry.box(f"{name}_copper_canopy_ridge", collection,
                 (0, porch_y - 0.04, 1.43),
                 (0.09, 0.70, 0.045), mat(mats, "copper"), bevel=0.005)


def add_upper_annex_storey(name, collection, mats, *, annex, main_roof_z, damaged=False):
    """L5 upper volume over the inner half of the enlarged annex, joined to the house."""
    width = annex["width"] * 0.62
    depth = annex["depth"] * 0.84
    x = annex["x"] - annex["width"] * 0.22
    y = annex["y"]
    bottom = annex["roof_z"] - 0.10
    height = main_roof_z - bottom - 0.07
    _stone_clad_box(name, collection, mats, x=x, y=y, width=width, depth=depth,
                    bottom=bottom, height=height, damaged=damaged,
                    sides=("front", "right", "back"))
    _green_annex_roof(f"{name}_roof", collection, mats, x=x, y=y,
                      width=width, depth=depth, roof_z=bottom + height,
                      damaged=damaged)
    front = y - depth / 2 - 0.085
    add_window(f"{name}_front_upper_window", collection, mats,
               (x, front, bottom + height * 0.55), (0.27, 0.04, 0.32),
               frame_role="copper", damaged=damaged)
    geometry.box(f"{name}_side_upper_window", collection,
                 (x + width / 2 + 0.084, y + 0.07, bottom + height * 0.56),
                 (0.035, 0.25, 0.32),
                 mat(mats, "damage_crack" if damaged else "window_warm"), bevel=0.006)
    geometry.box(f"{name}_joining_stone_course", collection,
                 (x - width / 2 - 0.07, front + 0.06, bottom + height * 0.50),
                 (0.17, 0.13, height * 0.83), mat(mats, "stone_block"), bevel=0.010)


def add_planted_flower_beds(name, collection, mats, *, level, damaged=False):
    """Planted stone beds that increase in number from levels three to five."""
    if level < 3:
        return
    positions = [(-1.33, -1.25), (-0.86, -1.34)]
    if level >= 4:
        positions.append((0.83, -1.36))
    if level >= 5:
        positions.append((1.36, -1.34))
    for index, (x, y) in enumerate(positions):
        landscaping.add_flower_bed(f"{name}_planted_bed_{index}", collection, mats,
                                   (x, y, 0.048), style="stone_ring")
        if damaged and index == len(positions) - 1:
            geometry.box(f"{name}_broken_flower_marker", collection,
                         (x + 0.09, y - 0.10, 0.11),
                         (0.22, 0.055, 0.06), mat(mats, "stone_shadow"),
                         bevel=0.006, rotation=(0, 0, 0.21))


def add_level_six_house(name, collection, mats, *, state="active"):
    """One masonry body and one broad trapezoidal roof replacing the L5 annex."""
    from . import stone_house_variants
    from .common import add_barrel

    main_w, depth, height = stone_house_variants.dimensions(6)
    annex_w = 0.78
    right = main_w / 2 + annex_w - 0.13
    left = -main_w / 2
    width, cx = right - left, (right + left) / 2
    roof_z = 0.22 + height
    floor_z = 0.22 + height / 2
    front = -depth / 2 - 0.078
    construction = state == "construction"
    damaged = state == "damaged"
    stone = mat(mats, "stone_block")
    pale = mat(mats, "stone_light")
    copper = mat(mats, "copper")
    wood = mat(mats, "wood_beam")
    foundation = add_foundation(f"{name}_unified_foundation", collection, mats,
                                width=width, depth=depth, height="medium",
                                thickness="thin", material="stone_block", loc=(cx, 0, 0))
    # The masonry courses span the old join continuously; no former annex wall remains.
    if construction:
        geometry.box(f"{name}_lower_masonry", collection, (cx, 0, 0.22 + height / 4),
                     (width, depth, height / 2), pale, bevel=0.020)
        for x, remaining in ((left + 0.11, 0.76), (0.01, 0.55), (right - 0.11, 0.42)):
            geometry.box(f"{name}_unfinished_upper_pier_{x:.2f}", collection,
                         (x, front + 0.07, floor_z + remaining / 2),
                         (0.17, 0.18, remaining), stone, bevel=0.012)
    elif damaged:
        # Separate masses leave an actual missing upper-right corner and a front breach.
        geometry.box(f"{name}_lower_surviving_body", collection,
                     (cx, 0, 0.22 + height / 4),
                     (width, depth, height / 2), pale, bevel=0.022)
        geometry.box(f"{name}_upper_left_survivor", collection,
                     (left + 0.53, 0, floor_z + 0.41), (1.06, depth, 0.82),
                     pale, bevel=0.018)
        geometry.box(f"{name}_upper_rear_survivor", collection,
                     (cx + 0.48, depth * 0.33, floor_z + 0.39),
                     (width * 0.55, depth * 0.34, 0.78), pale, bevel=0.016)
        for index, x in enumerate((left + 0.14, -0.18)):
            geometry.box(f"{name}_surviving_roof_pier_{index}", collection,
                         (x, depth * 0.32, floor_z + height / 4),
                         (0.16, 0.16, height / 2), stone, bevel=0.012)
            geometry.beam(f"{name}_surviving_rafter_{index}", collection,
                          (x, depth * 0.32, roof_z),
                          (0.11, depth * 0.32, roof_z + 0.72),
                          0.044, wood)
    else:
        for storey in (0, 1):
            geometry.box(f"{name}_storey_{storey}_stone_core", collection,
                         (cx, 0, 0.22 + (storey + 0.5) * height / 2),
                         (width, depth, height / 2), pale, bevel=0.020)
    rows = 14
    cols = 13
    for side in ("front", "back", "right", "left"):
        ncols = cols if side in ("front", "back") else 7
        span = width if side in ("front", "back") else depth
        for row in range(rows):
            z = 0.22 + (row + 0.5) * height / rows
            for col in range(ncols):
                p = -span / 2 + (col + 0.5) * span / ncols
                x = cx + p if side in ("front", "back") else (right if side == "right" else left)
                y = (-depth / 2 if side == "front" else depth / 2) if side in ("front", "back") else p
                if construction and (z > floor_z and (side == "right" or x > 0.05 or row % 3 == 1)):
                    continue
                if damaged and z > floor_z and ((side == "front" and x > 0.20) or
                                                (side == "right" and y < 0.20) or
                                                (side == "back" and x > 0.90)):
                    continue
                role = "stone_shadow" if (row * 3 + col) % 11 == 0 else ("stone_block" if (row + col) % 2 else "stone_light")
                if side in ("front", "back"):
                    loc, size = (x, y + (-0.038 if side == "front" else 0.038), z), (span / ncols - 0.010, 0.060, height / rows - 0.010)
                else:
                    loc, size = (x + (0.038 if side == "right" else -0.038), y, z), (0.060, span / ncols - 0.010, height / rows - 0.010)
                geometry.box(f"{name}_course_{side}_{row:02d}_{col:02d}", collection,
                             loc, size, mat(mats, role), bevel=0.006)
    # Continuous plinth, floor belt and cornice make both former volumes one facade.
    for z, thick, role in ((0.29, 0.09, "stone_shadow"),
                           (floor_z, 0.13, "stone_block"), (roof_z - 0.06, 0.08, "copper")):
        if construction and z > floor_z:
            continue
        if damaged and z > floor_z:
            length = width * 0.55
            center = left + length / 2
        else:
            length, center = width + 0.06, cx
        geometry.box(f"{name}_continuous_front_band_{z}", collection,
                     (center, front - 0.01, z), (length, 0.10, thick),
                     mat(mats, role), bevel=0.010)
    if not construction:
        add_door(f"{name}_main_entry", collection, mats, (0, front - 0.01, 0.54),
                 (0.44, 0.05, 0.64), material_role="wood_dark",
                 reinforced=True, damaged=damaged)
        side_annex = {"x": right - annex_w / 2, "y": 0.06, "width": annex_w}
        add_annex_entry_door(f"{name}_side_entry", collection, mats,
                             annex=side_annex, damaged=damaged)
        # A shallow tiled hood shelters the side entrance without crossing the tile edge.
        door_y = side_annex["y"] + 0.23
        hood_x = right + 0.106
        geometry.box(f"{name}_side_entry_canopy", collection,
                     (hood_x, door_y, 0.94), (0.125, 0.53, 0.055),
                     mat(mats, "damage_char" if damaged else "roof_green"),
                     bevel=0.008, rotation=(0, -0.16, 0))
        geometry.box(f"{name}_side_entry_canopy_copper_edge", collection,
                     (right + 0.156, door_y, 0.931), (0.025, 0.55, 0.028),
                     copper, bevel=0.004)
        for offset in (-0.19, 0.19):
            geometry.beam(f"{name}_side_entry_canopy_bracket_{offset}", collection,
                          (right + 0.04, door_y + offset, 0.855),
                          (right + 0.135, door_y + offset, 0.925), 0.025, stone)
        for x in (-0.58, 0.58, 1.28):
            for z in (0.88, floor_z + height / 4):
                if damaged and x > 0.5 and z > 1:
                    continue
                add_window(f"{name}_front_window_{x}_{z}", collection, mats,
                           (x, front - 0.025, z), (0.27, 0.05, 0.31),
                           frame_role="copper", damaged=damaged)
                geometry.box(f"{name}_window_sill_{x}_{z}", collection,
                             (x, front - 0.09, z - 0.21), (0.36, 0.12, 0.055),
                             stone, bevel=0.008)
        for z, positions in ((0.95, (-0.26,)),
                             (floor_z + height / 4, (-0.29, 0.29))):
            for window_y in positions:
                if damaged and z > 1.2 and window_y > 0:
                    continue
                geometry.box(f"{name}_side_window_frame_{z}_{window_y}", collection,
                             (right + 0.067, window_y, z), (0.055, 0.29, 0.36),
                             stone, bevel=0.009)
                geometry.box(f"{name}_side_window_glass_{z}_{window_y}", collection,
                             (right + 0.099, window_y, z), (0.024, 0.22, 0.27),
                             mat(mats, "window_warm" if not damaged else "damage_crack"),
                             bevel=0.005)
        add_stone_entrance_porch(f"{name}_porch", collection, mats,
                                 main_depth=depth, damaged=damaged)
    else:
        add_scaffold(f"{name}_scaffold", collection, mats,
                     width=1.44, depth=0.23, height=roof_z + 0.40, y=front - 0.25)
        for x in (left + 0.10, 0.11, 0.61):
            for y in (-depth * 0.32, depth * 0.32):
                geometry.beam(f"{name}_third_floor_support_{x:.2f}_{y:.2f}", collection,
                              (x, y, floor_z), (x, y, roof_z + 0.02),
                              0.060, wood)
        for y in (-depth * 0.32, depth * 0.32):
            geometry.beam(f"{name}_third_floor_crossbeam_{y:.2f}", collection,
                          (left + 0.10, y, roof_z + 0.02),
                          (0.61, y, roof_z + 0.02), 0.052, wood)
        for idx in range(9):
            geometry.box(f"{name}_stone_stock_{idx}", collection,
                         (-0.86 + idx * 0.14, -1.20, 0.10 + (idx % 2) * 0.06),
                         (0.16, 0.14, 0.12), stone, bevel=0.009)
    _add_level_six_roof(name, collection, mats, left=left, right=right,
                        depth=depth, roof_z=roof_z, state=state)
    if construction:
        geometry.box(f"{name}_second_chimney_courses", collection,
                     (1.12, 0.60, 0.085), (0.19, 0.19, 0.17),
                     stone, bevel=0.013)
    else:
        for index, x in enumerate((-0.56, 1.12)):
            if damaged:
                chimney_h = 0.20 if index else 0.29
            else:
                chimney_h = 0.53
            chimney_y = 0.62 if damaged and index == 1 else 0.31
            if x < 0.11:
                roof_rise = 0.72 * (x - (left - 0.12)) / (0.11 - (left - 0.12))
            else:
                roof_rise = 0.72 * ((right + 0.12) - x) / ((right + 0.12) - 0.61)
            bottom = roof_z + roof_rise - 0.04
            geometry.box(f"{name}_stone_chimney_{index}", collection,
                         (x, chimney_y, bottom + chimney_h / 2),
                         (0.20, 0.20, chimney_h), pale, bevel=0.016)
            for row in range(3 if not damaged else 1):
                geometry.box(f"{name}_chimney_course_{index}_{row}", collection,
                             (x, chimney_y - 0.115, bottom + (row + 0.5) * chimney_h / 3),
                             (0.21, 0.038, chimney_h / 3 - 0.012), stone,
                             bevel=0.005)
            geometry.box(f"{name}_chimney_crown_{index}", collection,
                         (x, chimney_y, bottom + chimney_h + 0.02),
                         (0.29, 0.28, 0.07), stone, bevel=0.012,
                         rotation=(0, 0.12 if damaged else 0, 0))
    # Extra level-six planting stays away from both entrances.
    for index, (x, y) in enumerate(((1.43, -1.16), (1.40, -0.60),
                                    (-1.49, -1.13), (-0.68, -1.44))):
        landscaping.add_flower_bed(f"{name}_new_flower_bed_{index}", collection,
                                   mats, (x, y, 0.048), style="stone_ring")
    for index, (x, y) in enumerate(((1.47, 0.54), (-1.48, -0.42))):
        geometry.box(f"{name}_stone_planter_{index}", collection,
                     (x, y, 0.075), (0.24, 0.23, 0.13), stone, bevel=0.015)
        landscaping.add_flower_bed(f"{name}_planter_blooms_{index}", collection,
                                   mats, (x, y, 0.14), style="stone_ring")
    if damaged:
        for index, (x, y) in enumerate(((0.98, -0.99), (1.24, -0.83),
                                        (1.49, -0.98), (0.34, -1.18))):
            geometry.box(f"{name}_fallen_masonry_{index}", collection,
                         (x, y, 0.08), (0.18, 0.13, 0.11),
                         mat(mats, "stone_shadow"), bevel=0.010,
                         rotation=(0, 0, index * 0.23))


def _add_level_six_roof(name, collection, mats, *, left, right, depth, roof_z, state):
    """High tiled trapezoid around a green third floor with inset side lights."""
    eave_l, eave_r = left - 0.12, right + 0.12
    crest_l, crest_r = 0.11, 0.61
    rise = 0.72
    roof_depth = depth + 0.27
    damaged, construction = state == "damaged", state == "construction"
    green = mat(mats, "roof_leaf")
    wall_y = depth / 2 + 0.055
    # The central part of the third floor is a real supported volume. Its
    # pitched flanks form continuous green facade faces under the roof tiles.
    if construction:
        geometry.box(f"{name}_unfinished_green_third_floor", collection,
                     ((crest_l + crest_r) / 2, depth * 0.20, roof_z + rise * 0.26),
                     (crest_r - crest_l, depth * 0.55, rise * 0.52),
                     green, bevel=0.012)
    elif damaged:
        geometry.box(f"{name}_broken_green_third_floor", collection,
                     (crest_l + 0.11, depth * 0.18, roof_z + rise * 0.25),
                     (0.22, depth * 0.60, rise * 0.50), green, bevel=0.010)
    else:
        geometry.box(f"{name}_green_third_floor_core", collection,
                     ((crest_l + crest_r) / 2, 0, roof_z + rise / 2),
                     (crest_r - crest_l, depth, rise), green, bevel=0.014)
    for face, y in (("front", -wall_y), ("back", wall_y)):
        verts = [(eave_l, y, roof_z), (crest_l, y, roof_z),
                 (crest_r, y, roof_z), (eave_r, y, roof_z),
                 (crest_l, y, roof_z + rise), (crest_r, y, roof_z + rise)]
        if construction:
            faces = [(0, 1, 4)]
        elif damaged:
            faces = [(0, 1, 4), (1, 2, 5, 4)] if face == "back" else [(0, 1, 4), (1, 2, 5, 4)]
        else:
            faces = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5)]
        geometry.mesh(f"{name}_green_third_floor_{face}_wall", collection,
                      verts, faces if face == "front" else [tuple(reversed(f)) for f in faces],
                      green)
    # Right triangles follow the two opposing roof pitches. Their vertical
    # legs face the square central window; all three panes stay in the wall.
    front_y = -wall_y - 0.005
    for index, x in enumerate((-0.36, 1.02)):
        if construction and index == 1:
            continue
        base_z, top_z, half_w = roof_z + 0.10, roof_z + 0.37, 0.14
        high_x = x + half_w if index == 0 else x - half_w
        surround = [(x - half_w - 0.022, front_y, base_z - 0.02),
                    (x + half_w + 0.022, front_y, base_z - 0.02),
                    (high_x, front_y, top_z + 0.02)]
        glazing = [(x - half_w, front_y - 0.008, base_z),
                   (x + half_w, front_y - 0.008, base_z),
                   (high_x, front_y - 0.008, top_z)]
        geometry.mesh(f"{name}_inset_triangle_frame_{index}", collection,
                      surround, [(0, 1, 2)], mat(mats, "stone_shadow"))
        if not construction:
            geometry.mesh(f"{name}_inset_triangle_glass_{index}", collection,
                          glazing, [(0, 1, 2)],
                          mat(mats, "damage_crack" if damaged else "glass_cyan"))
            for edge, (start, end) in enumerate(((0, 1), (1, 2), (2, 0))):
                geometry.beam(f"{name}_triangle_copper_edge_{index}_{edge}",
                              collection, glazing[start], glazing[end], 0.015,
                              mat(mats, "copper"))
    if not construction:
        square_x, square_z = (crest_l + crest_r) / 2, roof_z + rise * 0.55
        geometry.box(f"{name}_third_floor_square_window_recess", collection,
                     (square_x, front_y - 0.001, square_z), (0.34, 0.025, 0.34),
                     mat(mats, "stone_shadow"), bevel=0.010)
        geometry.box(f"{name}_third_floor_square_window_glass", collection,
                     (square_x, front_y - 0.020, square_z), (0.29, 0.018, 0.29),
                     mat(mats, "damage_crack" if damaged else "glass_cyan"),
                     bevel=0.006)
        for offset in (-0.16, 0.16):
            geometry.box(f"{name}_square_window_vertical_frame_{offset}", collection,
                         (square_x + offset, front_y - 0.034, square_z),
                         (0.024, 0.035, 0.35), mat(mats, "copper"), bevel=0.004)
            geometry.box(f"{name}_square_window_horizontal_frame_{offset}", collection,
                         (square_x, front_y - 0.034, square_z + offset),
                         (0.35, 0.035, 0.024), mat(mats, "copper"), bevel=0.004)
        geometry.box(f"{name}_square_window_mullion", collection,
                     (square_x, front_y - 0.045, square_z), (0.018, 0.024, 0.30),
                     mat(mats, "copper"), bevel=0.003)
    # Roof decking and tiles use the same grid so missing fields are physical holes.
    segments = ((eave_l, crest_l, 7), (crest_l, crest_r, 3), (crest_r, eave_r, 7))
    for section, (start, end, count) in enumerate(segments):
        slope = 0 if section == 1 else (rise / (crest_l - eave_l) if section == 0 else -rise / (eave_r - crest_r))
        for row in range(count):
            x = start + (row + 0.5) * (end - start) / count
            z = roof_z + (rise if section == 1 else
                          (x - eave_l) * slope if section == 0 else
                          rise + (x - crest_r) * slope)
            for col in range(9):
                if construction and (section == 2 or (section == 1 and col >= 3) or col >= 5):
                    continue
                if damaged and ((section == 2 and 1 <= col <= 6) or
                                (section == 1 and col >= 4) or
                                (section == 0 and 2 <= row <= 5 and col <= 3)):
                    continue
                y = -roof_depth / 2 + (col + 0.5) * roof_depth / 9
                sw = (end - start) / count
                geometry.box(f"{name}_trapezoid_tile_{section}_{row}_{col}", collection,
                             (x, y, z + 0.027), (sw + 0.018, roof_depth / 9 + 0.008, 0.046),
                             mat(mats, "roof_leaf" if (row + col) % 11 == 0 else "roof_green"),
                             bevel=0.007, rotation=(0, -math.atan(slope), 0))
    for x in (eave_l + 0.04, crest_l, crest_r, eave_r - 0.04):
        for y in (-roof_depth * 0.43, roof_depth * 0.43):
            geometry.beam(f"{name}_roof_rafter_{x:.2f}_{y:.2f}", collection,
                          (x, y, roof_z + (rise if crest_l <= x <= crest_r else 0.02)),
                          (x, -y, roof_z + (rise if crest_l <= x <= crest_r else 0.02)),
                          0.038, mat(mats, "wood_beam"))
    if not construction:
        for x in (eave_l + 0.04, eave_r - 0.04):
            geometry.box(f"{name}_copper_gutter_{x:.2f}", collection,
                         (x, 0, roof_z + 0.035),
                         (0.055, roof_depth + 0.04, 0.05),
                         mat(mats, "copper"), bevel=0.007)
        for col in range(7):
            y = -roof_depth * 0.43 + col * roof_depth * 0.143
            if damaged and col in (3, 4):
                continue
            geometry.box(f"{name}_crest_tile_{col}", collection,
                         ((crest_l + crest_r) / 2, y, roof_z + rise + 0.065),
                         (crest_r - crest_l + 0.05, roof_depth / 7, 0.066),
                         mat(mats, "roof_green"), bevel=0.013)
    if not construction:
        geometry.box(f"{name}_ridge_copper_clasp", collection,
                     ((crest_l + crest_r) / 2, roof_depth * 0.28, roof_z + rise + 0.11),
                     (0.42, 0.10, 0.045), mat(mats, "copper"), bevel=0.008)
        _add_level_six_roof_dormer(name, collection, mats, roof_z=roof_z,
                                   eave_l=eave_l, crest_l=crest_l, rise=rise,
                                   damaged=damaged)
        from . import stone_house_decor as decor
        for index, y in enumerate((-0.46, 0.46)):
            decor.add_ridge_copper_clasp(f"{name}_extra_ridge_clasp_{index}",
                                         collection, mats,
                                         ((crest_l + crest_r) / 2, y,
                                          roof_z + rise + 0.11))
        if not damaged:
            decor.add_roof_leaf_finial(f"{name}_roof_leaf_finial", collection,
                                       mats, ((crest_l + crest_r) / 2, 0.61,
                                              roof_z + rise + 0.12))
        for index, (x, y) in enumerate(((-0.84, 0.28), (0.88, 0.28))):
            slope_height = (x - eave_l) * rise / (crest_l - eave_l) if x < crest_l else rise * (1 - (x - crest_r) / (eave_r - crest_r))
            geometry.box(f"{name}_roof_copper_ornament_{index}", collection,
                         (x, y, roof_z + slope_height + 0.065),
                         (0.13, 0.18, 0.035), mat(mats, "copper"),
                         bevel=0.006)


def _add_level_six_roof_dormer(name, collection, mats, *, roof_z, eave_l,
                               crest_l, rise, damaged):
    """A small gabled attic window carried by the visible left roof slope."""
    x, y = -0.63, -0.14
    roof_surface = roof_z + (x - eave_l) * rise / (crest_l - eave_l)
    base_z = roof_surface + 0.015
    stone = mat(mats, "damage_char" if damaged else "stone_light")
    copper = mat(mats, "copper")
    geometry.box(f"{name}_attic_dormer_stone_body", collection,
                 (x, y, base_z + 0.14), (0.38, 0.38, 0.29), stone, bevel=0.014)
    roofs.add_gable_roof(f"{name}_attic_dormer_green_roof", collection, mats,
                         (x, y, base_z + 0.27), (0.46, 0.49, 0.19),
                         color_role="roof_green", damaged=damaged)
    face_y = y - 0.207
    corners = ((x - 0.105, face_y, base_z + 0.09),
               (x + 0.105, face_y, base_z + 0.09),
               (x, face_y, base_z + 0.285))
    geometry.mesh(f"{name}_attic_dormer_triangle_recess", collection,
                  corners, [(0, 1, 2)], mat(mats, "stone_shadow"))
    glass = tuple((vx, vy - 0.012, vz) for vx, vy, vz in
                  ((x - 0.077, face_y, base_z + 0.11),
                   (x + 0.077, face_y, base_z + 0.11),
                   (x, face_y, base_z + 0.25)))
    geometry.mesh(f"{name}_attic_dormer_triangle_glass", collection, glass,
                  [(0, 1, 2)],
                  mat(mats, "damage_crack" if damaged else "glass_cyan"))
    for edge, (start, end) in enumerate(((0, 1), (1, 2), (2, 0))):
        geometry.beam(f"{name}_attic_dormer_copper_frame_{edge}", collection,
                      corners[start], corners[end], 0.018, copper)
    for index in range(3):
        geometry.box(f"{name}_attic_dormer_roof_tile_{index}", collection,
                     (x, y - 0.15 + index * 0.15, base_z + 0.447),
                     (0.10, 0.14, 0.023),
                     mat(mats, "damage_char" if damaged and index == 2 else "roof_leaf"),
                     bevel=0.004)
