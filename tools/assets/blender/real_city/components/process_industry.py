"""Distinct compact process-industry kits for the shared isometric building tile."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, xyz, size, material, bevel=0.02, rotation=(0, 0, 0)):
    return g.box(name, c, xyz, size, material, bevel=bevel, rotation=rotation)


def cyl(c, name, xyz, radius, depth, material, vertices=20, rotation=(0, 0, 0)):
    return g.cylinder(name, c, xyz, radius, depth, material, vertices=vertices, rotation=rotation)


def floor(c, m, level, *, industrial=False):
    role = "reinforced_concrete" if level >= 8 else "brick_warm" if industrial and level >= 3 else "stone_block" if level >= 3 else "wood_beam"
    box(c, "work_floor", (0, 0, 0.12), (2.72, 2.50, 0.08), mat(m, role), 0.025)
    if level >= 3:
        for i in range(4):
            box(c, f"floor_course_{i}", (-0.90 + i * 0.59, -1.01, 0.17),
                (0.48, 0.12, 0.045), mat(m, "steel_light" if level >= 8 else "stone_light"), 0.008)


def barrel(c, m, name, x, y, *, role="wood_beam", state="active", h=0.55):
    if state == "construction":
        cyl(c, f"{name}_half", (x, y, 0.24), 0.23, 0.20, mat(m, role))
        return
    if state == "damaged":
        cyl(c, f"{name}_overturned", (x, y, 0.19), 0.23, 0.46,
            mat(m, role), rotation=(math.pi / 2, 0, -0.22))
        return
    cyl(c, f"{name}_body", (x, y, 0.16 + h / 2), 0.23, h, mat(m, role))
    for z in (0.23, 0.16 + h * 0.83):
        cyl(c, f"{name}_hoop_{z:.2f}", (x, y, z), 0.244, 0.045, mat(m, "steel_light"), 20)
    cyl(c, f"{name}_lid", (x, y, 0.18 + h), 0.21, 0.035,
        mat(m, "roof_gold" if role == "copper" else "wood_pale"), 20)


def _drive(c, m, name, x, y, z, level, state):
    if level < 3 or state == "construction":
        return
    if state == "damaged":
        cyl(c, f"{name}_fallen_wheel", (x, y - 0.46, 0.15), 0.20, 0.08,
            mat(m, "copper"), rotation=(math.pi / 2, 0, 0))
        return
    cyl(c, f"{name}_wheel", (x, y, z), 0.18 + level * 0.009, 0.08,
        mat(m, "copper"), rotation=(0, math.pi / 2, 0))
    for i in range(4):
        theta = math.pi * i / 2
        g.beam(f"{name}_spoke_{i}", c, (x + 0.05, y, z),
               (x + 0.05, y + math.sin(theta) * 0.16, z + math.cos(theta) * 0.16),
               0.025, mat(m, "dark_metal"))


def upgrade_details(c, m, level, state, kind):
    """Incremental, subject-specific machinery outside the main working core."""
    if state != "active":
        return
    if kind == "oil_press":
        if level >= 2:
            box(c, "seed_sorting_table", (-1.02, 0.89, 0.42), (0.51, 0.39, 0.10), mat(m, "wood_pale"))
            for x in (-1.21, -0.83):
                box(c, f"seed_table_leg_{x}", (x, 0.89, 0.27), (0.07, 0.07, 0.27), mat(m, "wood_beam"))
        if level >= 3:
            box(c, "brick_press_rail", (-0.08, 0.76, 0.31), (1.12, 0.12, 0.19), mat(m, "brick_warm"))
        if level >= 4:
            box(c, "wide_filter_rack", (0.67, -0.60, 0.50), (0.74, 0.11, 0.40), mat(m, "wood_beam"))
            for x in (0.36, 0.98):
                box(c, f"filter_rack_leg_{x}", (x, -0.60, 0.28), (0.07, 0.07, 0.29), mat(m, "wood_beam"))
        if level >= 6:
            barrel(c, m, "second_oil_output", 1.10, 0.72, role="copper")
        if level >= 7:
            box(c, "seed_feed_chute", (-0.68, -0.12, 0.83), (0.19, 0.55, 0.17), mat(m, "steel_light"))
        if level >= 9:
            cyl(c, "pressure_gauge", (0.46, 0.20, 1.26), 0.09, 0.04, mat(m, "glass_cyan"), 18,
                (math.pi / 2, 0, 0))
        if level >= 10:
            box(c, "master_press_lintel", (-0.08, 0.53, 1.54), (1.27, 0.16, 0.14), mat(m, "steel_light"))
    elif kind == "oil_refinery":
        if level >= 2:
            box(c, "column_feed_table", (-0.99, 0.72, 0.42), (0.44, 0.38, 0.11), mat(m, "brick_warm"))
            box(c, "column_feed_pier", (-0.99, 0.72, 0.27), (0.31, 0.28, 0.27), mat(m, "brick_warm"))
        if level >= 3:
            for y in (-0.31, -0.03, 0.11):
                box(c, f"cooling_coil_support_{y}", (0.72, y, 0.54), (0.08, 0.08, 0.32), mat(m, "steel_light"))
            for i in range(3):
                g.beam(f"cooling_coil_{i}", c, (0.48, -0.31 + i * 0.14, 0.70),
                       (1.02, -0.31 + i * 0.14, 0.70), 0.035, mat(m, "copper"))
        if level >= 4:
            cyl(c, "secondary_riser_foot", (0.58, 0.53, 0.24), 0.17, 0.19, mat(m, "stone_block"), 16)
            cyl(c, "secondary_riser", (0.58, 0.53, 0.90), 0.10, 1.19, mat(m, "steel_light"), 16)
        if level >= 5:
            box(c, "pump_casing", (1.01, -0.13, 0.34), (0.39, 0.37, 0.32), mat(m, "steel_light"))
        if level >= 6:
            barrel(c, m, "reserve_fuel_tank", 1.09, 1.04, role="copper", h=0.43)
        if level >= 7:
            g.beam("overhead_transfer", c, (-0.18, 0.30, 1.67), (0.89, 0.72, 1.67), 0.055,
                   mat(m, "copper"))
        if level >= 9:
            cyl(c, "column_gauge", (-0.10, -0.08, 1.07), 0.10, 0.04,
                mat(m, "glass_cyan"), 18, (math.pi / 2, 0, 0))
        if level >= 10:
            box(c, "master_pipe_lintel", (0.43, 0.83, 1.79), (1.37, 0.13, 0.13), mat(m, "reinforced_concrete"))
    elif kind == "resin_kiln":
        if level >= 2:
            box(c, "wood_storage_shelf", (-1.05, 0.02, 0.53), (0.53, 0.30, 0.09), mat(m, "wood_pale"))
            for x in (-1.26, -0.85):
                box(c, f"wood_shelf_leg_{x}", (x, 0.02, 0.33), (0.07, 0.07, 0.36), mat(m, "wood_beam"))
        if level >= 3:
            box(c, "brick_flue_base", (0.67, 0.71, 0.39), (0.48, 0.43, 0.36), mat(m, "brick_warm"))
            box(c, "brick_flue_foot", (0.67, 0.71, 0.22), (0.50, 0.45, 0.15), mat(m, "stone_block"))
        if level >= 4:
            barrel(c, m, "resin_trial_barrel", 0.64, -0.98, role="wood_dark", h=0.36)
        if level >= 5:
            box(c, "hot_retort_guard", (-0.13, -0.20, 0.71), (0.81, 0.08, 0.70), mat(m, "steel_light"))
        if level >= 6:
            g.beam("second_condenser", c, (0.80, 0.20, 1.26), (1.19, 0.21, 0.87), 0.060,
                   mat(m, "copper"))
        if level >= 7:
            cyl(c, "kiln_stack", (-0.13, 0.75, 1.17), 0.11, 0.80, mat(m, "steel_light"), 16)
        if level >= 9:
            cyl(c, "retort_gauge", (0.09, -0.09, 1.09), 0.09, 0.04,
                mat(m, "glass_cyan"), 18, (math.pi / 2, 0, 0))
        if level >= 10:
            box(c, "sealed_cooler_lintel", (0.85, 0.40, 1.45), (0.70, 0.14, 0.12), mat(m, "steel_light"))
    elif kind == "steelworks":
        if level >= 2:
            box(c, "charge_platform", (-1.06, 0.27, 0.42), (0.43, 0.42, 0.12), mat(m, "brick_warm"))
            box(c, "charge_platform_pier", (-1.06, 0.27, 0.27), (0.32, 0.30, 0.27), mat(m, "brick_warm"))
        if level >= 3:
            box(c, "mechanical_feed", (-0.91, 0.32, 0.71), (0.51, 0.18, 0.24), mat(m, "steel_light"))
            box(c, "mechanical_feed_stanchion", (-0.91, 0.32, 0.58), (0.13, 0.15, 0.15), mat(m, "steel_light"))
        if level >= 4:
            for x in (0.54, 1.07):
                box(c, f"rail_{x}", (x, -0.80, 0.17), (0.07, 0.82, 0.06), mat(m, "dark_metal"))
        if level >= 5:
            box(c, "armor_backstop", (0.74, 0.83, 0.63), (0.72, 0.16, 0.73), mat(m, "steel_light"))
            box(c, "armor_backstop_foot", (0.74, 0.83, 0.21), (0.77, 0.20, 0.12), mat(m, "steel_light"))
        if level >= 6:
            cyl(c, "second_ladle", (1.03, 0.72, 0.45), 0.19, 0.24, mat(m, "dark_metal"))
            cyl(c, "second_ladle_pedestal", (1.03, 0.72, 0.25), 0.21, 0.22, mat(m, "stone_block"))
        if level >= 7:
            box(c, "beam_press", (0.80, -0.53, 0.92), (0.11, 0.62, 1.19), mat(m, "steel_light"))
            box(c, "beam_press_foot", (0.80, -0.53, 0.22), (0.28, 0.65, 0.15), mat(m, "steel_light"))
        if level >= 9:
            box(c, "heat_hood", (-0.15, 0.80, 1.86), (1.20, 0.44, 0.17), mat(m, "reinforced_concrete"))
            for x in (-0.67, 0.37):
                box(c, f"heat_hood_post_{x}", (x, 0.84, 1.03), (0.09, 0.09, 1.60), mat(m, "steel_light"))
        if level >= 10:
            cyl(c, "second_exhaust", (0.32, 0.88, 1.98), 0.12, 0.34, mat(m, "steel_light"), 16)
    elif kind == "sulfur_spring":
        if level >= 2:
            box(c, "warning_post", (-0.91, 0.92, 0.52), (0.08, 0.08, 0.79), mat(m, "wood_beam"))
        if level >= 3:
            cyl(c, "gas_gauge", (0.96, 0.50, 0.77), 0.09, 0.04,
                mat(m, "glass_cyan"), 18, (math.pi / 2, 0, 0))
        if level >= 4:
            g.beam("second_duct", c, (-0.42, 0.48, 1.26), (-0.82, 0.80, 0.66), 0.055,
                   mat(m, "copper"))
            box(c, "second_duct_pier", (-0.82, 0.80, 0.41), (0.10, 0.10, 0.50), mat(m, "stone_block"))
        if level >= 5:
            box(c, "armored_pump_guard", (1.10, 0.57, 0.45), (0.22, 0.50, 0.50), mat(m, "steel_light"))
            box(c, "armored_pump_foot", (1.10, 0.57, 0.20), (0.27, 0.54, 0.13), mat(m, "steel_light"))
        if level >= 6:
            g.beam("sealed_return_pipe", c, (0.84, 0.26, 0.61), (1.14, -0.28, 0.61), 0.057,
                   mat(m, "steel_light"))
        if level >= 7:
            cyl(c, "reserve_pump", (0.86, -0.18, 0.39), 0.15, 0.33, mat(m, "dark_metal"))
            cyl(c, "reserve_pump_foot", (0.86, -0.18, 0.21), 0.18, 0.13, mat(m, "stone_block"), 16)
        if level >= 8:
            box(c, "alloy_hood_lip", (0, -0.17, 1.30), (1.29, 0.08, 0.09), mat(m, "steel_light"))
        if level >= 9:
            cyl(c, "crystal_control", (-0.52, 0.27, 1.49), 0.055, 0.21, mat(m, "amethyst"), 6)
        if level >= 10:
            box(c, "sealed_control_lintel", (0.50, 1.02, 1.42), (1.26, 0.15, 0.13),
                mat(m, "reinforced_concrete"))
            for x in (-0.02, 1.02):
                box(c, f"control_lintel_post_{x}", (x, 1.02, 0.78), (0.09, 0.09, 1.18), mat(m, "steel_light"))


def add_oil_press(c, m, *, level: int, state: str):
    floor(c, m, level)
    upgrade_details(c, m, level, state, "oil_press")
    frame = mat(m, "steel_light" if level >= 5 else "wood_beam")
    box(c, "press_pedestal", (-0.08, 0.14, 0.25), (1.06, 0.92, 0.17), mat(m, "stone_block"), 0.04)
    cyl(c, "seed_basket", (-1.03, 0.45, 0.31), 0.28, 0.34, mat(m, "wood_pale"))
    if state != "construction":
        for i in range(5):
            cyl(c, f"seed_cluster_{i}", (-1.17 + i * 0.07, 0.43, 0.51),
                0.055, 0.06, mat(m, "roof_gold"), 10)
    barrel(c, m, "oil_output", 1.01, -0.61, role="copper" if level >= 5 else "wood_beam", state=state)
    if state == "damaged":
        box(c, "broken_press_post", (-0.55, 0.33, 0.50), (0.14, 0.14, 0.50), frame)
        box(c, "fallen_press_beam", (0.27, -0.84, 0.17), (1.12, 0.15, 0.15), frame,
            rotation=(0, 0, -0.28))
        cyl(c, "split_screw", (0.59, -0.76, 0.15), 0.06, 0.61,
            mat(m, "dark_metal"), 14, (math.pi / 2, 0, 0.20))
        return
    for x in (-0.54, 0.40):
        box(c, f"press_post_{x}", (x, 0.34, 0.77), (0.15, 0.15, 1.20), frame, 0.018)
    if state == "construction":
        box(c, "unmounted_upper_beam", (0.27, -0.86, 0.17), (1.10, 0.15, 0.14), frame)
        return
    box(c, "press_upper_beam", (-0.07, 0.34, 1.36), (1.16, 0.20, 0.17), frame, 0.03)
    box(c, "press_plate", (-0.07, 0.13, 0.64), (0.76, 0.64, 0.12),
        mat(m, "steel_light" if level >= 5 else "wood_pale"), 0.03)
    cyl(c, "press_screw", (-0.07, 0.13, 1.00), 0.075, 0.67,
        mat(m, "dark_metal"), 18)
    box(c, "oil_gutter", (0.54, -0.18, 0.28), (0.61, 0.11, 0.09), mat(m, "copper"))
    box(c, "filter_cloth", (0.53, -0.28, 0.34), (0.50, 0.32, 0.025), mat(m, "whitewash"), 0.006)
    _drive(c, m, "press_drive", 0.53, 0.35, 0.80, level, state)
    if level >= 5:
        box(c, "guard_panel", (0.55, 0.14, 0.65), (0.09, 0.67, 0.50), mat(m, "steel_light"))
    if level >= 8:
        box(c, "sealed_oil_cabinet", (1.14, 0.71, 0.45), (0.35, 0.41, 0.65), mat(m, "reinforced_concrete"))


def add_oil_refinery(c, m, *, level: int, state: str):
    floor(c, m, level, industrial=True)
    upgrade_details(c, m, level, state, "oil_refinery")
    shell = mat(m, "steel_light" if level >= 5 else "brick_warm")
    # The distillation column is the visual anchor; raw oil and fuel stay separate.
    h = 1.28 + level * 0.065
    cyl(c, "column_foot", (-0.18, 0.30, 0.22), 0.48, 0.22, mat(m, "stone_block"))
    if state == "construction":
        cyl(c, "column_lower_stage", (-0.18, 0.30, 0.59), 0.37, 0.52, shell)
        box(c, "column_panels_waiting", (0.45, -0.94, 0.16), (0.84, 0.29, 0.10), shell)
    elif state == "damaged":
        cyl(c, "column_split_stump", (-0.18, 0.30, 0.60), 0.37, 0.53, shell)
        cyl(c, "fallen_column_top", (0.35, -0.68, 0.20), 0.31, 0.64,
            shell, rotation=(math.pi / 2, 0, 0.25))
    else:
        cyl(c, "distillation_column", (-0.18, 0.30, 0.20 + h / 2), 0.36, h, shell, 24)
        for z in (0.45, 0.86, 1.24):
            cyl(c, f"column_band_{z}", (-0.18, 0.30, z), 0.385, 0.07,
                mat(m, "dark_metal"), 24)
        cyl(c, "column_cap", (-0.18, 0.30, 0.22 + h), 0.40, 0.13,
            mat(m, "copper"), 24)
        g.beam("vapour_pipe", c, (0.13, 0.30, 1.35), (0.82, 0.30, 1.35),
               0.09, mat(m, "copper"))
        g.beam("condenser_drop", c, (0.82, 0.30, 1.35), (0.82, 0.30, 0.73),
               0.09, mat(m, "copper"))
    barrel(c, m, "raw_oil", -1.04, -0.46, role="dark_metal", state=state)
    barrel(c, m, "fuel_tank", 0.96, 0.55, role="copper", state=state, h=0.64)
    if state == "active":
        box(c, "cooler_bed", (0.76, -0.46, 0.34), (0.70, 0.48, 0.31), mat(m, "glass_cyan"), 0.025)
        for i in range(3 + level // 3):
            box(c, f"fuel_can_{i}", (0.65 + (i % 2) * 0.19, -1.00 + (i // 2) * 0.19, 0.25),
                (0.15, 0.13, 0.24), mat(m, "roof_gold"), 0.015)
        _drive(c, m, "pump_drive", 1.20, -0.02, 0.57, level, state)
        if level >= 8:
            box(c, "reinforced_pipe_frame", (0.86, 0.13, 0.92),
                (0.14, 1.16, 1.27), mat(m, "steel_light"))


def add_resin_kiln(c, m, *, level: int, state: str):
    floor(c, m, level, industrial=True)
    upgrade_details(c, m, level, state, "resin_kiln")
    shell = mat(m, "steel_light" if level >= 5 else "brick_warm")
    h = 0.91 + level * 0.055
    cyl(c, "kiln_stone_foot", (-0.16, 0.28, 0.25), 0.56, 0.26, mat(m, "stone_block"))
    if state == "construction":
        cyl(c, "kiln_lower_drum", (-0.16, 0.28, 0.57), 0.43, 0.47, shell)
        box(c, "flue_bricks_waiting", (0.67, -0.96, 0.16), (0.55, 0.26, 0.13), shell)
    elif state == "damaged":
        cyl(c, "kiln_broken_base", (-0.16, 0.28, 0.58), 0.43, 0.48, shell)
        box(c, "fallen_kiln_shell", (0.44, -0.53, 0.18), (0.64, 0.33, 0.12), shell,
            rotation=(0, 0, -0.18))
    else:
        cyl(c, "sealed_retort", (-0.16, 0.28, 0.25 + h / 2), 0.43, h, shell, 24)
        for z in (0.40, 0.25 + h * 0.78):
            cyl(c, f"retort_hoop_{z:.2f}", (-0.16, 0.28, z), 0.455, 0.06,
                mat(m, "dark_metal"), 24)
        cyl(c, "retort_lid", (-0.16, 0.28, 0.28 + h), 0.44, 0.09,
            mat(m, "wood_dark"), 24)
        g.beam("resin_vapour_pipe", c, (0.18, 0.28, 1.18), (0.82, 0.28, 1.18),
               0.075, mat(m, "copper"))
        g.beam("cooling_drop", c, (0.82, 0.28, 1.18), (0.82, 0.28, 0.62),
               0.075, mat(m, "copper"))
    for i in range(3 + level // 4):
        box(c, f"dry_log_{i}", (-1.13 + i * 0.16, -0.49, 0.24),
            (0.13, 0.56, 0.14), mat(m, "wood_beam"), 0.025)
    box(c, "coal_bin", (-1.06, 0.67, 0.28), (0.44, 0.47, 0.33), mat(m, "wood_pale"))
    if state == "active":
        box(c, "coal_charge", (-1.06, 0.67, 0.47), (0.33, 0.35, 0.045), mat(m, "coal"))
    barrel(c, m, "resin_barrel", 1.04, -0.55, role="wood_dark", state=state)
    if level >= 5 and state == "active":
        box(c, "cooling_shroud", (0.84, 0.27, 0.58), (0.43, 0.53, 0.47),
            mat(m, "steel_light"))
        _drive(c, m, "draft_drive", 1.20, 0.36, 0.86, level, state)
    if level >= 8 and state == "active":
        box(c, "sealed_resin_store", (1.10, 0.97, 0.44),
            (0.38, 0.36, 0.64), mat(m, "reinforced_concrete"))


def add_steelworks(c, m, *, level: int, state: str):
    floor(c, m, level, industrial=True)
    upgrade_details(c, m, level, state, "steelworks")
    steel = mat(m, "steel_light")
    brick = mat(m, "brick_warm")
    h = 1.17 + level * 0.07
    box(c, "furnace_plinth", (-0.15, 0.29, 0.25), (1.20, 1.02, 0.24), mat(m, "stone_block"), 0.04)
    if state == "construction":
        cyl(c, "furnace_lower_course", (-0.15, 0.29, 0.67), 0.47, 0.59, brick, 24)
        box(c, "upper_shell_waiting", (0.61, -0.89, 0.17), (0.70, 0.34, 0.11), steel)
    elif state == "damaged":
        cyl(c, "furnace_breached_stump", (-0.15, 0.29, 0.65), 0.47, 0.55, brick, 24)
        box(c, "fallen_furnace_wall", (0.66, -0.57, 0.18), (0.73, 0.37, 0.12), brick,
            rotation=(0, 0, -0.22))
    else:
        cyl(c, "blast_furnace", (-0.15, 0.29, 0.25 + h / 2), 0.47, h, brick, 28)
        for z in (0.48, 0.98, 1.45):
            cyl(c, f"furnace_band_{z}", (-0.15, 0.29, z), 0.49, 0.07, steel, 28)
        cyl(c, "furnace_mouth", (-0.15, 0.29, 0.28 + h), 0.44, 0.08,
            mat(m, "dark_metal"), 28)
        cyl(c, "hot_core", (-0.15, 0.29, 0.33 + h), 0.33, 0.025,
            mat(m, "roof_coral"), 24)
        box(c, "heat_shield", (-0.16, -0.39, 0.72), (1.08, 0.10, 0.78), steel)
    for i in range(3):
        box(c, f"input_ingot_{i}", (-1.15, -0.82 + i * 0.19, 0.22),
            (0.44, 0.13, 0.09), steel)
    box(c, "coal_feed", (-1.07, 0.78, 0.31), (0.39, 0.40, 0.33), mat(m, "coal"))
    if state == "active":
        cyl(c, "casting_ladle", (0.81, -0.25, 0.42), 0.29, 0.32,
            mat(m, "dark_metal"), 20)
        cyl(c, "ladle_glow", (0.81, -0.25, 0.59), 0.23, 0.025,
            mat(m, "roof_coral"), 20)
        box(c, "rail_cart", (0.82, -0.91, 0.28), (0.71, 0.42, 0.22), steel)
        for x in (0.56, 1.08):
            cyl(c, f"cart_wheel_{x}", (x, -0.91, 0.18), 0.11, 0.07,
                mat(m, "dark_metal"), 14, (math.pi / 2, 0, 0))
        _drive(c, m, "air_blast", 1.19, 0.65, 0.64, level, state)
        if level >= 8:
            for x in (-0.64, 0.34):
                box(c, f"reinforced_shield_{x}", (x, 0.95, 0.91),
                    (0.13, 0.20, 1.35), mat(m, "reinforced_concrete"))


def add_sulfur_spring(c, m, *, level: int, state: str):
    floor(c, m, level)
    upgrade_details(c, m, level, state, "sulfur_spring")
    frame = mat(m, "steel_light" if level >= 5 else "stone_block")
    # A natural split and mineral crust remain visible beneath the collector.
    for i in range(4):
        box(c, f"mineral_crust_{i}", (-0.75 + i * 0.31, 0.14 + (i % 2) * 0.17, 0.18),
            (0.35, 0.21, 0.07), mat(m, "flower_yellow"), 0.025,
            rotation=(0, 0, 0.32 if i % 2 else -0.23))
    box(c, "spring_fissure", (-0.10, 0.22, 0.22),
        (0.96, 0.13, 0.055), mat(m, "stone_shadow"), 0.012,
        rotation=(0, 0, 0.28))
    for x in (-0.58, 0.58):
        box(c, f"collector_foot_{x}", (x, 0.25, 0.31), (0.16, 0.83, 0.26), frame)
    if state == "construction":
        box(c, "unmounted_collector", (0.55, -0.85, 0.18), (0.83, 0.34, 0.12), frame)
    elif state == "damaged":
        box(c, "collector_left_remnant", (-0.43, 0.26, 0.63),
            (0.14, 0.13, 0.62), frame)
        box(c, "fallen_gas_canopy", (0.47, -0.61, 0.18),
            (0.88, 0.39, 0.13), frame, rotation=(0, 0, -0.28))
    else:
        for x in (-0.55, 0.55):
            box(c, f"collector_post_{x}", (x, 0.26, 0.83),
                (0.13, 0.13, 1.03), frame)
        box(c, "gas_collector_hood", (0, 0.26, 1.34),
            (1.27, 0.85, 0.18), mat(m, "roof_teal"), 0.035)
        g.beam("gas_pipe", c, (0.50, 0.45, 1.30), (0.97, 0.67, 1.02),
               0.085, mat(m, "copper"))
        g.beam("pump_drop", c, (0.97, 0.67, 1.02), (0.97, 0.67, 0.55),
               0.085, mat(m, "copper"))
        _drive(c, m, "pump_drive", 1.19, 0.72, 0.62, level, state)
    barrel(c, m, "remote_fuel", -1.11, -0.72, role="dark_metal", state=state)
    for i in range(2 + level // 3):
        box(c, f"sealed_sulfur_case_{i}", (0.52 + (i % 2) * 0.31,
            -0.83 + (i // 2) * 0.33, 0.28), (0.27, 0.26, 0.24),
            mat(m, "stone_light"), 0.025)
        if state == "active":
            box(c, f"sulfur_mark_{i}", (0.52 + (i % 2) * 0.31,
                -0.97 + (i // 2) * 0.33, 0.31), (0.12, 0.02, 0.09),
                mat(m, "flower_yellow"), 0.005)
    if level >= 8 and state == "active":
        box(c, "sealed_control_bank", (1.10, 1.02, 0.44),
            (0.40, 0.38, 0.63), mat(m, "reinforced_concrete"))
