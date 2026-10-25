"""Progression and physical state details for the stone-house pilot family."""

from __future__ import annotations

import math

from .. import geometry
from . import landscaping, stone_house_architecture as architecture
from .common import add_scaffold, mat
from .foundations import add_foundation


FOOTPRINT_SCALE = math.sqrt(1.10)


def dimensions(level: int) -> tuple[float, float, float]:
    size_growth = 1.08 if level >= 5 else 1.0
    height = {4: 1.64, 5: 2.03, 6: 2.20}.get(level, 0.88 + level * 0.06)
    return ((1.42 + level * 0.05) * FOOTPRINT_SCALE * size_growth,
            (1.12 + level * 0.03) * FOOTPRINT_SCALE * size_growth,
            height)


def add_progression(name, collection, mats, *, level: int, damaged: bool = False):
    """Add each requested architectural stage to the retained stone shell."""
    if level < 2:
        return
    width, depth, height = dimensions(level)
    roof_z = 0.22 + height
    architecture.add_round_attic_window(f"{name}_round_attic_window", collection, mats,
                                        main_depth=depth, roof_z=roof_z,
                                        level=level, damaged=damaged)
    architecture.add_triangular_side_dormer(f"{name}_side_dormer", collection, mats,
                                            main_width=width, roof_z=roof_z, damaged=damaged)
    annex = None
    if level >= 3:
        annex = architecture.add_right_stone_annex(f"{name}_right_annex", collection, mats,
                                                    main_width=width, level=level, damaged=damaged)
    if level >= 4:
        architecture.add_second_storey_details(f"{name}_second_storey", collection, mats,
                                                main_width=width, main_depth=depth,
                                                main_height=height, damaged=damaged)
        architecture.add_stone_entrance_porch(f"{name}_porch", collection, mats,
                                               main_depth=depth, damaged=damaged)
    if level >= 5 and annex is not None:
        architecture.add_upper_annex_storey(f"{name}_upper_annex", collection, mats,
                                             annex=annex, main_roof_z=roof_z, damaged=damaged)
        architecture.add_annex_entry_door(f"{name}_annex_entry", collection, mats,
                                          annex=annex, damaged=damaged)
    architecture.add_planted_flower_beds(f"{name}_flowers", collection, mats,
                                         level=level, damaged=damaged)


def add_construction(name, collection, mats, *, level: int):
    width, depth, height = dimensions(level)
    add_foundation(f"{name}_foundation", collection, mats, width=width, depth=depth,
                   height="medium", thickness="medium", material="stone_block")
    # Low masonry has a door gap; the upper courses and roof are visibly absent.
    half_wall = height * 0.56
    for side in (-1, 1):
        section_w = (width - 0.56) / 2
        geometry.box(f"{name}_front_wall_{side}", collection,
                     (side * (0.28 + section_w / 2), -depth / 2, 0.22 + half_wall / 2),
                     (section_w, 0.14, half_wall), mat(mats, "stone_block"), bevel=0.016)
        for row in range(3):
            for col in range(3):
                geometry.box(f"{name}_front_course_{side}_{row}_{col}", collection,
                             (side * (0.28 + (col + 0.5) * section_w / 3),
                              -depth / 2 - 0.085, 0.22 + (row + 0.5) * half_wall / 3),
                             (section_w / 3 - 0.014, 0.045, half_wall / 3 - 0.014),
                             mat(mats, "stone_light" if (row + col) % 2 else "stone_block"), bevel=0.006)
    for side in (-1, 1):
        geometry.box(f"{name}_side_wall_{side}", collection,
                     (side * width / 2, 0, 0.22 + half_wall / 2),
                     (0.14, depth, half_wall), mat(mats, "stone_light"), bevel=0.015)
    geometry.box(f"{name}_rear_wall", collection,
                 (0, depth / 2, 0.22 + half_wall * 0.40),
                 (width, 0.14, half_wall * 0.80), mat(mats, "stone_block"), bevel=0.014)
    for side in (-1, 1):
        geometry.beam(f"{name}_roof_rafter_{side}", collection,
                      (side * (width + 0.40) * 0.50, -depth * 0.43, 0.22 + height),
                      (0, -depth * 0.43, 0.22 + height + 0.39),
                      0.065, mat(mats, "wood_beam"))
    geometry.beam(f"{name}_ridge_beam", collection,
                  (0, -depth * 0.46, 0.22 + height + 0.39),
                  (0, depth * 0.46, 0.22 + height + 0.39),
                  0.065, mat(mats, "wood_beam"))
    add_scaffold(f"{name}_scaffold", collection, mats,
                 width=min(1.42, width * 0.88), depth=0.22,
                 height=0.22 + height + 0.38, y=-depth / 2 - 0.27)
    for index in range(3 + level):
        x = -0.37 + index * 0.16
        geometry.box(f"{name}_stock_stone_{index}", collection,
                     (x, -1.15, 0.10 + (index % 2) * 0.08),
                     (0.18, 0.15, 0.13), mat(mats, "stone_block"), bevel=0.012)
    for index in range(2):
        geometry.box(f"{name}_stacked_tile_{index}", collection,
                     (0.91, -0.91 + index * 0.14, 0.10 + index * 0.05),
                     (0.34, 0.13, 0.045), mat(mats, "roof_green"), bevel=0.006)
    if level >= 2:
        geometry.box(f"{name}_carved_lintel_stock", collection,
                     (-1.05, -0.65, 0.12), (0.48, 0.16, 0.12),
                     mat(mats, "stone_light"), bevel=0.012)
    if level >= 3:
        annex_w, annex_d, annex_h = (0.86, 1.12, 0.91) if level >= 5 else (0.69, 1.00, 0.77)
        annex_x = width / 2 + annex_w / 2 - 0.13
        annex_y = 0.06
        add_foundation(f"{name}_annex_foundation", collection, mats,
                       width=annex_w, depth=annex_d, height="low", thickness="thin",
                       material="stone_block", loc=(annex_x, annex_y, 0))
        for side in (-1, 1):
            geometry.box(f"{name}_annex_partial_side_{side}", collection,
                         (annex_x + side * annex_w * 0.42, annex_y, 0.20 + annex_h * 0.27),
                         (0.13, annex_d * 0.90, annex_h * 0.54),
                         mat(mats, "stone_block"), bevel=0.012)
        geometry.beam(f"{name}_annex_roof_guide", collection,
                      (annex_x, annex_y - annex_d * 0.53, 0.20 + annex_h + 0.24),
                      (annex_x, annex_y + annex_d * 0.53, 0.20 + annex_h + 0.24),
                      0.045, mat(mats, "wood_beam"))
    if level >= 4:
        for side in (-1, 1):
            geometry.box(f"{name}_partial_corner_pier_{side}", collection,
                         (side * (width / 2 - 0.04), -depth / 2 - 0.04,
                          0.22 + min(1.16, height) * 0.50),
                         (0.19, 0.19, min(1.16, height)),
                         mat(mats, "stone_block"), bevel=0.014)
        for side in (-1, 1):
            geometry.beam(f"{name}_upper_storey_post_{side}", collection,
                          (side * width * 0.44, depth * 0.36, 1.10),
                          (side * width * 0.44, depth * 0.36, 0.22 + height),
                          0.065, mat(mats, "wood_beam"))
        geometry.box(f"{name}_porch_footing", collection,
                     (0, -depth / 2 - 0.29, 0.13), (0.91, 0.49, 0.16),
                     mat(mats, "stone_block"), bevel=0.014)
        geometry.box(f"{name}_copper_gutter_stock", collection,
                     (1.15, 0.55, 0.11), (0.60, 0.075, 0.06),
                     mat(mats, "copper"), bevel=0.008)
    if level >= 5:
        upper_x = annex_x - annex_w * 0.22
        for side in (-1, 1):
            geometry.beam(f"{name}_upper_annex_post_{side}", collection,
                          (upper_x + side * annex_w * 0.27, annex_y - annex_d * 0.34,
                           0.20 + annex_h),
                          (upper_x + side * annex_w * 0.27, annex_y - annex_d * 0.34,
                           0.22 + height - 0.08),
                          0.055, mat(mats, "wood_beam"))


def add_damage(name, collection, mats, *, level: int):
    width, depth, height = dimensions(level)
    roof_z = 0.22 + height
    dark = mat(mats, "damage_char", "stone_shadow")
    # A large blackened patch and snapped timbers replace one missing tile field.
    for row in range(3):
        for col in range(3):
            x = 0.29 + row * 0.12
            y = -0.42 + col * 0.15
            z = roof_z + 0.39 * (1 - x / ((width + 0.40) / 2)) + 0.040
            geometry.box(f"{name}_burnt_roof_{row}_{col}", collection,
                         (x, y, z), (0.15, 0.15, 0.042), dark,
                         bevel=0.006, rotation=(0, -0.40, (row + col) * 0.045))
    for i in range(3):
        geometry.beam(f"{name}_broken_rafter_{i}", collection,
                      (0.44 + i * 0.12, -0.50 + i * 0.16, roof_z + 0.22),
                      (0.51 + i * 0.12, -0.55 + i * 0.16, roof_z + 0.36),
                      0.034, mat(mats, "wood_dark"))
    # Loose masonry and cracks make the failure visible even at map scale.
    for i in range(5):
        geometry.box(f"{name}_fallen_masonry_{i}", collection,
                     (width * 0.52 + (i % 2) * 0.09, -depth * 0.52 - 0.16 - (i // 2) * 0.11,
                      0.10 + (i % 2) * 0.03),
                     (0.14, 0.11, 0.09), mat(mats, "stone_shadow"),
                     bevel=0.008, rotation=(0, 0, i * 0.18))
    for i in range(3):
        geometry.box(f"{name}_facade_crack_{i}", collection,
                     (width * 0.27 + i * 0.05, -depth / 2 - 0.088,
                      0.22 + height * (0.32 + i * 0.13)),
                     (0.022, 0.025, 0.22), dark,
                     bevel=0.003, rotation=(0, 0, 0.22 - i * 0.18))
    landscaping.add_pebble_cluster(f"{name}_fallen_shards", collection, mats,
                                    (0.91, -0.91, 0.08), count=7)
