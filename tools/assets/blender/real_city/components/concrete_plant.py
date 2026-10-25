"""Ten-stage concrete batching plant on the shared one-tile ground."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def box(c, name, pos, size, material, bevel=0.02, rotation=(0, 0, 0)):
    return g.box(name, c, pos, size, material, bevel=bevel, rotation=rotation)


def pipe(c, name, a, b, radius, material):
    return g.beam(name, c, a, b, radius * 2, material)


def bins(c, m, level, state):
    rim = mat(m, "steel_light" if level >= 5 else "wood_beam")
    pale = mat(m, "concrete" if level >= 8 else "stone_light")
    fills = (mat(m, "whitewash"), mat(m, "dust"), mat(m, "stone_shadow"))
    # Three physically separate recipe inputs: cement, sand and aggregate.
    for i, x in enumerate((-0.98, -0.11, 0.76)):
        box(c, f"input_{i}_bed", (x, 0.90, 0.13), (0.72, 0.74, 0.14), pale)
        for side in (-1, 1):
            if state == "construction" and i == 2 and side == 1:
                continue
            if state == "damaged" and (i + side) % 3 == 0:
                continue
            h = 0.25 if state == "damaged" and i == 1 else 0.47
            box(c, f"input_{i}_side_{side}", (x + side * 0.34, 0.90, 0.125 + h / 2), (0.07, 0.74, h), rim)
        if not (state == "damaged" and i == 1):
            h = 0.23 if state == "construction" and i == 2 else 0.47
            box(c, f"input_{i}_back", (x, 1.25, 0.125 + h / 2), (0.73, 0.07, h), rim)
        if state == "active":
            for k in range(3):
                g.sphere(f"input_{i}_fill_{k}", c, (x - 0.19 + k * 0.18, 0.94, 0.29), (0.14, 0.18, 0.13), fills[i], segments=12, ring_count=6)
        elif state == "damaged":
            g.sphere(f"spill_{i}", c, (x, 0.48, 0.13), (0.23, 0.16, 0.09), fills[i], segments=12, ring_count=6)
            box(c, f"fallen_input_panel_{i}", (x, 0.50, 0.15), (0.46, 0.10, 0.12), rim, rotation=(0, 0, i * 0.16 - 0.16))
    if state == "active" and level >= 3:
        for i, x in enumerate((-0.98, -0.11, 0.76)):
            box(c, f"feed_chute_{i}", (x, 0.49, 0.46), (0.39, 0.38, 0.10), rim, rotation=(0.20, 0, 0))
            for side in (-1, 1):
                box(c, f"feed_lip_{i}_{side}", (x + side * 0.17, 0.49, 0.53), (0.05, 0.37, 0.12), rim, rotation=(0.20, 0, 0))
    if level >= 6 and state == "active":
        box(c, "enclosed_feed_canopy", (-0.11, 0.88, 0.83), (2.56, 0.78, 0.12), mat(m, "reinforced_concrete") if level >= 8 else rim, 0.035)


def mixer(c, m, level, state):
    base = mat(m, "reinforced_concrete" if level >= 8 else "stone_block" if level >= 3 else "wood_pale")
    steel = mat(m, "steel_light" if level >= 5 else "metal_worn")
    dark = mat(m, "dark_metal")
    copper = mat(m, "copper")
    box(c, "batching_pad", (0.10, -0.28, 0.14), (1.60, 1.25, 0.18), base, 0.04)
    if level <= 2:
        for i in range(5):
            box(c, f"brick_pad_facing_{i}", (-0.51 + i * 0.30, -0.92, 0.15), (0.27, 0.06, 0.14), mat(m, "brick_warm"), 0.012)
    for x in (-0.51, 0.71):
        box(c, f"mixer_pedestal_{x}", (x, -0.18, 0.35), (0.20, 0.45, 0.32), base)
    if state == "construction":
        for x in (-0.56, 0.72):
            pipe(c, f"bare_frame_{x}", (x, -0.22, 0.25), (x, -0.22, 1.23), 0.055, steel)
        pipe(c, "bare_crossmember", (-0.56, -0.22, 1.23), (0.72, -0.22, 1.23), 0.055, steel)
        g.cylinder("unmounted_drum", c, (0.57, -1.01, 0.30), 0.24, 0.49, steel, vertices=20, rotation=(0, math.pi / 2, 0))
        box(c, "stacked_casing_panels", (-0.57, -0.86, 0.17), (0.56, 0.19, 0.13), base)
        return
    if state == "damaged":
        box(c, "broken_mixer_wall", (0.57, 0.16, 0.51), (0.15, 0.57, 0.60), base)
        g.cylinder("fallen_mixer_drum", c, (0.05, -0.86, 0.32), 0.25, 0.65, steel, vertices=20, rotation=(0, math.pi / 2, 0.12))
        for i in range(4):
            box(c, f"casing_rubble_{i}", (-0.55 + i * 0.28, -0.70 - (i % 2) * 0.16, 0.13), (0.22, 0.18, 0.12), base, rotation=(0, 0, i * 0.13))
        return
    for x in (-0.56, 0.72):
        box(c, f"mixer_bearing_{x}", (x, -0.22, 0.66), (0.14, 0.49, 0.59), steel, 0.03)
    g.cylinder("mixing_drum", c, (0.08, -0.22, 0.84), 0.39 + level * 0.012, 1.15, steel, vertices=28, rotation=(0, math.pi / 2, 0))
    for x in (-0.45, 0.61):
        g.cylinder(f"drum_band_{x}", c, (x, -0.22, 0.84), 0.43 + level * 0.012, 0.075, dark, vertices=28, rotation=(0, math.pi / 2, 0))
    g.cylinder("drum_mouth", c, (0.69, -0.22, 0.84), 0.26, 0.075, mat(m, "whitewash"), vertices=24, rotation=(0, math.pi / 2, 0))
    if level >= 4:
        box(c, "drive_housing", (-0.75, -0.29, 0.51), (0.43, 0.50, 0.48), dark, 0.045)
        g.cylinder("drive_wheel", c, (-0.77, -0.56, 0.64), 0.19, 0.09, copper if level >= 5 else steel, vertices=18, rotation=(math.pi / 2, 0, 0))
    if level >= 6:
        box(c, "mixer_guard_roof", (0.03, -0.19, 1.46), (1.66, 1.06, 0.15), base if level >= 8 else steel, 0.04)
        for x in (-0.69, 0.73):
            box(c, f"guard_post_{x}", (x, 0.26, 0.93), (0.08, 0.08, 0.90), steel)
    if level >= 10:
        box(c, "precision_control", (-0.80, -0.65, 0.79), (0.32, 0.18, 0.34), dark)
        g.cylinder("precision_dial", c, (-0.80, -0.76, 0.81), 0.105, 0.04, mat(m, "glass_cyan"), vertices=16, rotation=(math.pi / 2, 0, 0))


def utilities(c, m, level, state):
    steel = mat(m, "steel_light")
    concrete = mat(m, "reinforced_concrete")
    copper = mat(m, "copper")
    yellow = mat(m, "flower_yellow")
    # Water stays visible in every stage and is connected only on completed plants.
    g.cylinder("water_tank", c, (-1.14, -0.60, 0.38), 0.22, 0.55, mat(m, "roof_blue"), vertices=20)
    g.cylinder("water_rim", c, (-1.14, -0.60, 0.67), 0.25, 0.06, steel, vertices=20)
    if level >= 3:
        box(c, "water_glass_gauge", (-1.14, -0.83, 0.40), (0.08, 0.025, 0.36), mat(m, "glass_cyan"), 0.006)
    if state == "active":
        pipe(c, "water_riser", (-1.14, -0.60, 0.68), (-1.14, -0.16, 0.68), 0.045, copper)
        pipe(c, "water_feed", (-1.14, -0.16, 0.68), (-0.44, -0.16, 0.68), 0.045, copper)
    if level >= 4:
        box(c, "fuel_reservoir", (-1.07, -1.12, 0.28), (0.49, 0.27, 0.38), mat(m, "dark_metal"))
        if state == "active":
            g.cylinder("fuel_cap", c, (-1.07, -1.12, 0.50), 0.09, 0.06, yellow, vertices=12)
    if level >= 5:
        if state == "active":
            for i, x in enumerate((1.10,) if level < 9 else (0.94, 1.30)):
                height = 0.75 + 0.095 * (level - 5)
                for dx in (-0.17, 0.17):
                    box(c, f"silo_{i}_leg_{dx}", (x + dx, 0.48, 0.47), (0.07, 0.07, 0.70), steel)
                g.cylinder(f"silo_{i}_body", c, (x, 0.48, 0.83 + height / 2), 0.25, height, concrete if level >= 8 else steel, vertices=22)
                g.cone(f"silo_{i}_hopper", c, (x, 0.48, 0.68), 0.25, 0.08, 0.24, steel, vertices=22)
                g.cylinder(f"silo_{i}_lid", c, (x, 0.48, 0.86 + height), 0.28, 0.08, mat(m, "dark_metal"), vertices=22)
                if level >= 7:
                    box(c, f"silo_{i}_hazard", (x, 0.19, 1.21), (0.26, 0.025, 0.08), yellow, 0.005)
        elif state == "construction":
            for dx in (-0.17, 0.17):
                box(c, f"silo_frame_{dx}", (1.10 + dx, 0.48, 0.45), (0.07, 0.07, 0.67), steel)
            g.cylinder("silo_section_waiting", c, (1.09, -0.96, 0.20), 0.23, 0.25, steel, vertices=20)
        else:
            g.cylinder("ruptured_silo", c, (1.04, -0.85, 0.29), 0.25, 0.46, concrete if level >= 8 else steel, vertices=20, rotation=(0, math.pi / 2, 0.16))
    if level >= 8:
        if state == "active":
            for x in (-0.69, 0.68):
                box(c, f"gantry_post_{x}", (x, -0.05, 1.02), (0.10, 0.10, 1.77), steel)
            box(c, "gantry_beam", (0, -0.05, 1.94), (1.52, 0.13, 0.15), steel)
            pipe(c, "crane_drop", (0.28, -0.05, 1.88), (0.28, -0.05, 1.58), 0.025, mat(m, "dark_metal"))
            g.cylinder("crane_hook", c, (0.28, -0.05, 1.54), 0.07, 0.08, yellow, vertices=12)
        elif state == "construction":
            box(c, "gantry_first_post", (-0.69, -0.05, 0.91), (0.10, 0.10, 1.55), steel)
            box(c, "gantry_beam_waiting", (0.45, -1.05, 0.19), (1.16, 0.14, 0.13), steel)
        else:
            box(c, "collapsed_gantry", (0.40, -1.00, 0.18), (1.31, 0.14, 0.13), steel, rotation=(0, 0, -0.15))


def output(c, m, level, state):
    base = mat(m, "concrete" if level >= 8 else "wood_pale")
    steel = mat(m, "steel_light")
    box(c, "loading_bed", (1.09, -0.72, 0.14), (0.61, 0.88, 0.15), base)
    if state == "construction":
        for i in range(2):
            box(c, f"wet_form_unmounted_{i}", (0.91 + 0.26 * i, -0.80, 0.25), (0.22, 0.29, 0.08), steel)
        return
    if state == "damaged":
        for i in range(3):
            box(c, f"broken_block_{i}", (0.82 + 0.20 * i, -0.82 - (i % 2) * 0.20, 0.25), (0.21, 0.17, 0.13), mat(m, "concrete"), rotation=(0, 0, i * 0.18))
        return
    for i in range(min(2 + level // 2, 6)):
        box(c, f"cast_block_{i}", (0.86 + (i % 2) * 0.27, -0.92 + (i // 2) * 0.24, 0.27), (0.22, 0.18, 0.12), mat(m, "concrete"), 0.015)
    if level >= 6:
        for y in (-1.04, -0.55):
            box(c, f"rail_{y}", (1.13, y, 0.24), (0.48, 0.05, 0.06), steel)
        box(c, "loading_cart", (1.13, -0.77, 0.38), (0.41, 0.32, 0.18), steel)


def add_concrete_plant(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    bins(collection, mats, level, state)
    mixer(collection, mats, level, state)
    utilities(collection, mats, level, state)
    output(collection, mats, level, state)
