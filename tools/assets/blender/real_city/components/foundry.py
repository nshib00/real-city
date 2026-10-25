"""Ten-stage open-vat foundry with construction and catastrophic damage states."""

from __future__ import annotations

import math

from .. import geometry as g
from ..materials import create_material
from .common import mat
from . import vat_decor


def _molten(mats):
    if "foundry_molten" not in mats:
        mats["foundry_molten"] = create_material(
            "MAT_real_city_foundry_molten_iron", (0.82, 0.09, 0.008),
            roughness=0.34, metallic=0.18, emission=(1.0, 0.12, 0.004), emission_strength=0.48)
        mats["foundry_hot_edge"] = create_material(
            "MAT_real_city_foundry_hot_edge", (1.0, 0.36, 0.025),
            roughness=0.36, emission=(1.0, 0.27, 0.012), emission_strength=0.55)
    return mats["foundry_molten"]


def _wall(c, name, *, radius, height, material, segments=32, skip=()):
    inner = radius - 0.15
    verts, faces = [], []
    for i in range(segments):
        a = math.tau * i / segments
        co, si = math.cos(a), math.sin(a)
        for r, z in ((radius, 0.29), (radius, 0.29 + height),
                     (inner, 0.29 + height), (inner, 0.36)):
            verts.append((r * co, r * si, z))
    for i in range(segments):
        if i in skip:
            continue
        a, b = i * 4, ((i + 1) % segments) * 4
        faces.extend(((a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2),
                      (a + 2, b + 2, b + 3, a + 3), (a + 3, b + 3, b, a)))
    g.mesh(name, c, verts, faces, material)


def _vat(c, m, level, state):
    radius = 0.53 + (level - 1) * 0.039
    height = 0.75 + (level - 1) * 0.082
    metal = mat(m, "steel_light" if level >= 7 else "metal_worn" if level >= 4 else "stone_shadow")
    lip = mat(m, "armor" if level >= 8 else "dark_metal")
    g.cylinder("vat_footing", c, (0, 0, 0.235), radius + 0.17, 0.22,
               mat(m, "reinforced_concrete" if level >= 8 else "brick_warm" if level >= 4 else "stone_block"), vertices=32)
    for i in range(8):
        a = math.tau * i / 8
        g.box(f"vat_footing_course_{i}", c,
              ((radius + 0.10) * math.cos(a), (radius + 0.10) * math.sin(a), 0.24),
              (0.22, 0.19, 0.13), mat(m, "stone_block" if level < 4 else "brick_light" if level < 8 else "concrete"),
              bevel=0.015, rotation=(0, 0, a))
    if state == "construction":
        # The lower shell is still being assembled; the unfinished upper half is absent.
        partial = height * 0.48
        _wall(c, "vat_lower_shell_unfinished", radius=radius, height=partial, material=metal,
              skip=tuple(range(3, 12)))
        for i in (0, 1, 2):
            a = math.tau * i / 8
            g.box(f"unmounted_vat_plate_{i}", c,
                  (0.84 * math.cos(a + 2.8), -0.80 + 0.13 * i, 0.15),
                  (0.43, 0.13, 0.10), metal, rotation=(0, 0, a))
        vat_decor.add_circumferential_stripe("uncompleted_lower_band", c, m,
                                             radius=radius + 0.018, z=0.40, arc=0.63, start=2.7)
        return radius, height
    missing = tuple(range(2, 13)) + tuple(range(25, 28)) if state == "damaged" else ()
    _wall(c, "vat_heatproof_casing", radius=radius, height=height, material=metal, skip=missing)
    if state == "damaged":
        g.cylinder("cooled_slush", c, (0, 0, 0.39), radius - 0.17, 0.06, mat(m, "damage_char"), vertices=32)
        for i in range(6):
            x = -0.84 + i * 0.29
            g.box(f"fallen_vat_wall_{i}", c, (x, -0.80 - 0.10 * (i % 2), 0.16),
                  (0.24, 0.12, 0.11), metal, rotation=(0, 0, i * 0.24))
        g.sphere("solidified_spill", c, (0.47, -0.88, 0.085),
                 (0.38, 0.28, 0.065), mat(m, "damage_char"), segments=16, ring_count=8)
        vat_decor.add_circumferential_stripe("broken_back_band", c, m,
                                             radius=radius + 0.018, z=0.29 + height * 0.37,
                                             role="copper", arc=0.32, start=2.7)
        return radius, height
    molten = _molten(m)
    g.cylinder("molten_iron_visible", c, (0, 0, 0.29 + height - 0.14),
               radius - 0.17, 0.04, molten, vertices=32)
    for i in range(5):
        a = math.tau * (i + 0.35) / 5
        g.sphere(f"molten_hot_patch_{i}", c,
                 ((radius - 0.29) * math.cos(a), (radius - 0.29) * math.sin(a), 0.29 + height - 0.109),
                 (0.10, 0.062, 0.009), mat(m, "foundry_hot_edge"), segments=12, ring_count=6)
    vat_decor.add_circumferential_stripe("vat_lip_bright", c, m,
                                         radius=radius + 0.005, z=0.29 + height - 0.04,
                                         width=0.09, role="roof_gold" if level >= 9 else "copper" if level >= 5 else "steel_light")
    for idx, frac in enumerate((0.20, 0.58) if level < 5 else (0.17, 0.48, 0.75)):
        vat_decor.add_circumferential_stripe(f"vat_belt_{idx}", c, m,
                                             radius=radius + 0.016, z=0.29 + height * frac,
                                             width=0.055 if idx == 0 else 0.035,
                                             role="copper" if level >= 5 else "dark_metal")
    vat_decor.add_radial_ribs("vat_armor_rib", c, m, radius=radius + 0.014,
                               height=height, count=8 if level < 7 else 12,
                               role="steel_light" if level >= 7 else "dark_metal")
    if level >= 4:
        vat_decor.add_heat_shield_medallions("vat_heat_badge", c, m,
                                             radius=radius + 0.06, z=0.29 + height * 0.57,
                                             count=4 if level < 8 else 6)
    if level >= 8:
        vat_decor.add_gilded_threads("vat_gilded_filament", c, m,
                                     radius=radius + 0.08, lower_z=0.40,
                                     upper_z=0.21 + height, count=6 if level == 8 else 8,
                                     strands=1 if level == 8 else 2)
    return radius, height


def _supporting_work(c, m, level, state, radius, height):
    dark = mat(m, "dark_metal")
    iron = mat(m, "steel_light" if level >= 7 else "metal_worn")
    brick = mat(m, "brick_warm" if level >= 4 else "stone_light")
    # Fuel and ore remain separate and visible around the central vessel.
    for name, x, fill in (("coal", -1.08, mat(m, "coal")), ("ore", 1.07, mat(m, "stone_shadow"))):
        g.box(f"{name}_bin_base", c, (x, 0.54, 0.15), (0.47, 0.48, 0.11), brick)
        for side in (-1, 1):
            g.box(f"{name}_bin_side_{side}", c, (x + side * 0.22, 0.54, 0.28),
                  (0.055, 0.48, 0.25), iron)
        if state == "active":
            for i in range(3):
                g.sphere(f"{name}_lump_{i}", c, (x - 0.13 + i * 0.13, 0.57, 0.26),
                         (0.085, 0.10, 0.08), fill, segments=10, ring_count=6)
    # Bellows, duct and stack grow with the plant, while damaged machinery falls.
    stack_h = 0.57 + level * 0.09
    if state == "construction":
        g.cylinder("stack_pipe_waiting", c, (-0.94, -0.73, 0.18), 0.12, 0.32, iron,
                   vertices=16, rotation=(0, math.pi / 2, 0))
        g.box("bellows_frame_incomplete", c, (-0.98, -0.36, 0.30),
              (0.43, 0.36, 0.37), mat(m, "wood_beam"))
    elif state == "damaged":
        g.cylinder("fallen_exhaust", c, (-0.95, -0.69, 0.19), 0.13, 0.63, iron,
                   vertices=16, rotation=(0, math.pi / 2, 0.19))
        g.box("crushed_bellows", c, (-1.02, -0.42, 0.17),
              (0.46, 0.38, 0.14), mat(m, "wood_dark"), rotation=(0, 0, -0.17))
    else:
        g.box("bellows_housing", c, (-1.02, -0.41, 0.32),
              (0.46, 0.40, 0.36), mat(m, "wood_beam" if level < 5 else "copper"))
        for i in range(3):
            g.box(f"bellows_fold_{i}", c, (-1.17 + i * 0.14, -0.63, 0.38),
                  (0.09, 0.045, 0.23), dark)
        g.beam("air_duct", c, (-0.82, -0.32, 0.43), (-radius + 0.03, -0.31, 0.46),
               0.10, iron)
        g.cylinder("exhaust_stack", c, (-1.05, 0.02, 0.23 + stack_h / 2),
                   0.11 if level < 6 else 0.14, stack_h, brick if level < 7 else iron,
                   vertices=18)
        g.cylinder("exhaust_cap", c, (-1.05, 0.02, 0.25 + stack_h),
                   0.16, 0.07, iron, vertices=18)
    g.box("casting_bench", c, (0.88, -0.79, 0.27),
          (0.75, 0.43, 0.22), mat(m, "elite_plank" if level >= 7 else "wood_pale"))
    if state == "active":
        for i in range(min(2 + level // 2, 6)):
            x = 0.62 + 0.25 * (i % 3)
            y = -0.87 + 0.14 * (i // 3)
            g.box(f"cast_ingot_{i}", c, (x, y, 0.41), (0.20, 0.09, 0.065), iron, bevel=0.012)
        if level >= 5:
            g.cylinder("drive_wheel", c, (-0.97, -0.21, 0.63), 0.19, 0.07,
                       mat(m, "copper"), vertices=18, rotation=(math.pi / 2, 0, 0))
        if level >= 7:
            for x in (-0.67, 0.72):
                g.box(f"hoist_post_{x}", c, (x, 0.92, 0.95), (0.10, 0.10, 1.62), iron)
            g.box("hoist_crossbeam", c, (0.02, 0.92, 1.80), (1.48, 0.12, 0.14), iron)
            g.beam("hoist_chain", c, (0.11, 0.92, 1.74), (0.11, 0.92, 1.43), 0.035, dark)
        if level >= 8:
            g.cylinder("cooling_tank", c, (1.05, 0.04, 0.34), 0.23, 0.48,
                       mat(m, "armor"), vertices=20)
    elif state == "damaged":
        for i in range(4):
            g.box(f"scattered_ingot_{i}", c,
                  (0.58 + 0.19 * i, -0.88 - 0.08 * (i % 2), 0.13),
                  (0.20, 0.09, 0.06), iron, rotation=(0, 0, 0.13 * i))
        if level >= 7:
            g.box("fallen_hoist", c, (0.28, 0.90, 0.15),
                  (1.25, 0.11, 0.13), iron, rotation=(0, 0, 0.24))


def add_foundry(collection, mats: dict, *, level: int, state: str) -> None:
    if level not in range(1, 11) or state not in {"active", "construction", "damaged"}:
        raise ValueError((level, state))
    radius, height = _vat(collection, mats, level, state)
    _supporting_work(collection, mats, level, state, radius, height)
