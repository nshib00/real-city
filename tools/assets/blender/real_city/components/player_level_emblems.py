"""Stylized city-growth emblems used for the 15 player progression levels."""

from __future__ import annotations

import math

from .. import geometry


def _coin(name, collection, mats, level):
    palette = ("roof_coral", "roof_red", "roof_gold", "roof_teal", "roof_blue", "roof_green")
    enamel = mats[palette[min((level - 1) // 3, len(palette) - 1)]]
    geometry.cylinder(f"{name}_brass_rim", collection, (0, 0, 0), 1.0, 0.20, mats["roof_gold"], vertices=48, rotation=(math.pi / 2, 0, 0))
    geometry.cylinder(f"{name}_enamel_face", collection, (0, -0.115, 0), 0.86, 0.12, enamel, vertices=48, rotation=(math.pi / 2, 0, 0))
    for index in range(12):
        angle = math.tau * index / 12
        geometry.sphere(f"{name}_rim_stud_{index:02d}", collection,
                        (math.sin(angle) * 0.92, -0.20, math.cos(angle) * 0.92),
                        (0.035, 0.026, 0.035), mats["copper"], segments=10, ring_count=6)


def _house(name, collection, mats, x, z, scale=1.0, roof="roof_red"):
    width, height = 0.24 * scale, 0.26 * scale
    bottom = z - height / 2
    geometry.box(f"{name}_stone_base", collection, (x, -0.235, bottom + 0.035 * scale),
                 (width * 1.05, 0.12, 0.07 * scale), mats["stone_light"], bevel=0.025 * scale)
    geometry.box(f"{name}_walls", collection, (x, -0.245, bottom + height * 0.48),
                 (width, 0.13, height * 0.78), mats["whitewash"], bevel=0.025 * scale)
    geometry.gable_roof(f"{name}_roof", collection, (x, -0.255, bottom + height * 0.72),
                        (width * 1.3, 0.18, 0.15 * scale), mats[roof])
    geometry.box(f"{name}_door", collection, (x, -0.322, bottom + 0.055 * scale),
                 (0.055 * scale, 0.018, 0.11 * scale), mats["wood_dark"], bevel=0.006)


def _tower(name, collection, mats, x, z, scale=1.0, roof="roof_teal"):
    width, height = 0.18 * scale, 0.40 * scale
    geometry.box(f"{name}_stone_foot", collection, (x, -0.245, z - height * 0.43),
                 (width * 1.3, 0.15, 0.10 * scale), mats["stone_block"], bevel=0.025)
    geometry.box(f"{name}_shaft", collection, (x, -0.245, z),
                 (width, 0.14, height * 0.84), mats["brick_warm"], bevel=0.018)
    geometry.cone(f"{name}_roof", collection, (x, -0.245, z + height * 0.48),
                  width * 0.82, 0.02, height * 0.30, mats[roof], vertices=8)
    geometry.box(f"{name}_window", collection, (x, -0.324, z + 0.02 * scale),
                 (0.045 * scale, 0.018, 0.075 * scale), mats["window_warm"], bevel=0.006)


def add_level_emblem(collection, mats, level: int, name: str | None = None):
    """Build one readable, layered emblem; levels depict city growth, never professions."""
    name = name or f"player_level_{level:02d}"
    _coin(name, collection, mats, level)

    # Warm crystal spark: the first sign of a future settlement.
    if level == 1:
        geometry.aeolian_crystal(f"{name}_spark", collection, (0, -0.35, 0.03), 0.20, 0.48, mats["window_warm"])
        geometry.sphere(f"{name}_spark_core", collection, (0, -0.38, -0.06), (0.105, 0.06, 0.12), mats["roof_gold"], segments=16, ring_count=8)
    elif level == 2:
        for i, (x, z) in enumerate(((-0.22, -0.18), (0.22, -0.18), (-0.22, 0.16), (0.22, 0.16))):
            geometry.sphere(f"{name}_hearth_stone_{i}", collection, (x, -0.31, z), (0.10, 0.065, 0.075), mats["stone_block"], segments=12, ring_count=8)
        geometry.aeolian_crystal(f"{name}_hearth_flame", collection, (0, -0.39, 0.04), 0.13, 0.35, mats["window_warm"])
    elif level == 3:
        for i, x in enumerate((-0.34, 0, 0.34)):
            _house(f"{name}_roof_{i}", collection, mats, x, -0.02, 0.76 + 0.08 * (i == 1), "roof_red" if i != 1 else "roof_coral")
    elif level == 4:
        geometry.beam(f"{name}_road", collection, (-0.44, -0.30, -0.23), (0.42, -0.30, 0.15), 0.11, mats["path_light_earth"])
        _house(f"{name}_house_west", collection, mats, -0.28, 0.28, 0.74)
        _house(f"{name}_house_east", collection, mats, 0.32, -0.19, 0.78, "roof_teal")
    elif level == 5:
        geometry.box(f"{name}_courtyard", collection, (0, -0.30, -0.05), (0.30, 0.10, 0.24), mats["path_warm"], bevel=0.04)
        for i, (x, z) in enumerate(((-0.36, 0.29), (0.36, 0.29), (-0.36, -0.31), (0.36, -0.31))):
            _house(f"{name}_quarter_{i}", collection, mats, x, z, 0.60, ("roof_red", "roof_teal", "roof_green", "roof_coral")[i])
    elif level == 6:
        geometry.cylinder(f"{name}_plaza_fountain", collection, (0, -0.36, 0.02), 0.20, 0.10, mats["glass_cyan"], vertices=24, rotation=(math.pi / 2, 0, 0))
        geometry.cylinder(f"{name}_fountain_lip", collection, (0, -0.39, 0.02), 0.27, 0.05, mats["stone_block"], vertices=24, rotation=(math.pi / 2, 0, 0))
        for i, x in enumerate((-0.48, 0.48)):
            _house(f"{name}_plaza_house_{i}", collection, mats, x, -0.20 if i else 0.24, 0.56)
        geometry.aeolian_crystal(f"{name}_plaza_spring", collection, (0, -0.43, 0.15), 0.07, 0.18, mats["glass_cyan"])
    elif level == 7:
        for i, (x, z) in enumerate(((-0.40, 0.30), (0, 0.32), (0.40, 0.30), (-0.34, -0.25), (0.34, -0.25))):
            _house(f"{name}_district_{i}", collection, mats, x, z, 0.56, ("roof_red", "roof_teal", "roof_coral", "roof_green", "roof_blue")[i])
        geometry.beam(f"{name}_district_lane", collection, (-0.50, -0.31, -0.04), (0.50, -0.31, -0.04), 0.08, mats["path_light_earth"])
    elif level == 8:
        for i, (x, z, s) in enumerate(((-0.42, -0.23, .72), (-.22, .24, .68), (.40, -.18, .76), (.23, .26, .70))):
            _house(f"{name}_city_house_{i}", collection, mats, x, z, s, ("roof_red", "roof_teal", "roof_green", "roof_coral")[i])
        _tower(f"{name}_city_center", collection, mats, 0, -0.01, .84)
    elif level == 9:
        for i, (x, z, s) in enumerate(((-.47,-.31,.62),(-.31,.18,.72),(.40,-.29,.66),(.44,.22,.68),(-.10,-.36,.62))):
            _house(f"{name}_wide_city_{i}", collection, mats, x, z, s, ("roof_red", "roof_teal", "roof_green", "roof_coral", "roof_blue")[i])
        _tower(f"{name}_high_tower", collection, mats, 0, .08, 1.18, "roof_gold")
    elif level == 10:
        geometry.beam(f"{name}_belt_road_n", collection, (-.50, -.31, .50), (.50, -.31, .50), .075, mats["path_light_earth"])
        geometry.beam(f"{name}_belt_road_s", collection, (-.50, -.31, -.50), (.50, -.31, -.50), .075, mats["path_light_earth"])
        geometry.beam(f"{name}_belt_road_w", collection, (-.50, -.31, -.50), (-.50, -.31, .50), .075, mats["path_light_earth"])
        geometry.beam(f"{name}_belt_road_e", collection, (.50, -.31, -.50), (.50, -.31, .50), .075, mats["path_light_earth"])
        for i, (x, z) in enumerate(((-.34,-.23),(.34,-.23),(-.34,.24),(.34,.24))):
            _house(f"{name}_belt_house_{i}", collection, mats, x, z, .64, ("roof_red", "roof_teal", "roof_green", "roof_coral")[i])
        _tower(f"{name}_belt_gate", collection, mats, 0, 0, .80)
    elif level == 11:
        for i, (x,z) in enumerate(((-.40,-.26),(.35,-.25),(-.28,.23),(.34,.25))):
            _house(f"{name}_garden_home_{i}", collection, mats, x, z, .59, ("roof_teal", "roof_green", "roof_red", "roof_coral")[i])
        for i, (x,z) in enumerate(((-.48,.43),(.48,.43),(-.48,-.45),(.48,-.45))):
            geometry.sphere(f"{name}_canopy_{i}", collection, (x,-.30,z), (.15,.11,.17), mats["grass_bright"], segments=14, ring_count=8)
            geometry.cylinder(f"{name}_tree_trunk_{i}", collection, (x,-.27,z-.17), .035,.16,mats["wood_dark"],vertices=8)
    elif level == 12:
        for i, (x,z) in enumerate(((-.42,-.25),(.40,-.22),(-.37,.28),(.38,.29))):
            _house(f"{name}_crystal_city_{i}", collection, mats, x, z, .57, ("roof_teal", "roof_red", "roof_green", "roof_coral")[i])
        geometry.aeolian_crystal(f"{name}_heart_crystal", collection, (0,-.38,.04), .20,.63,mats["amethyst"])
        geometry.aeolian_crystal(f"{name}_crystal_shard_left", collection, (-.19,-.36,-.12), .09,.30,mats["star_glass"])
        geometry.aeolian_crystal(f"{name}_crystal_shard_right", collection, (.19,-.36,-.12), .09,.30,mats["star_glass"])
    elif level == 13:
        for i, (x,z,s) in enumerate(((-.46,-.25,.56),(-.29,.22,.72),(.35,-.28,.61),(.44,.24,.64))):
            _house(f"{name}_horizon_home_{i}", collection, mats, x,z,s,("roof_red","roof_teal","roof_green","roof_coral")[i])
        for i,x in enumerate((-.08,.10)):
            _tower(f"{name}_horizon_spire_{i}", collection,mats,x,.12,1.12 + i*.18,"roof_gold" if i else "roof_teal")
        geometry.sphere(f"{name}_horizon_sun", collection, (0,-.30,.61), (.23,.08,.12), mats["window_warm"], segments=20, ring_count=10)
    elif level == 14:
        for i,(x,z) in enumerate(((-.46,-.27),(.45,-.27),(-.38,.25),(.38,.24))):
            _house(f"{name}_aolia_home_{i}",collection,mats,x,z,.59,("roof_red","roof_teal","roof_green","roof_coral")[i])
        _tower(f"{name}_aolia_center",collection,mats,0,-.02,1.28,"roof_gold")
        geometry.aeolian_crystal(f"{name}_heart_of_aolia",collection,(0,-.42,.27),.10,.32,mats["amethyst"])
        for i,x in enumerate((-.18,.18)):
            geometry.sphere(f"{name}_heart_glow_{i}",collection,(x,-.41,.04),(.08,.05,.10),mats["glass_cyan"],segments=14,ring_count=8)
    else:
        for i,(x,z,s) in enumerate(((-.52,-.26,.58),(-.34,.23,.68),(.34,-.26,.64),(.51,.22,.61),(-.03,-.36,.56),(.02,.34,.62))):
            _house(f"{name}_eternal_city_{i}",collection,mats,x,z,s,("roof_red","roof_teal","roof_green","roof_coral","roof_blue","roof_gold")[i])
        _tower(f"{name}_eternal_spire",collection,mats,0,.06,1.32,"roof_gold")
        for i in range(2):
            # Beveled arc curves frame the city without obscuring its skyline.
            import bpy
            curve = bpy.data.curves.new(f"{name}_wind_arc_{i}_curve", "CURVE")
            curve.dimensions = "3D"
            curve.bevel_depth = .018
            curve.bevel_resolution = 3
            spline = curve.splines.new("POLY")
            pts = []
            for step in range(25):
                angle = math.radians(28 + step * 124 / 24)
                pts.append((math.cos(angle) * (.72 + i*.10), -.22, math.sin(angle) * (.72 + i*.10) + .02))
            spline.points.add(len(pts)-1)
            for p, co in zip(spline.points, pts): p.co = (*co, 1)
            obj = bpy.data.objects.new(f"{name}_wind_arc_{i}", curve)
            collection.objects.link(obj)
            curve.materials.append(mats["roof_gold"] if i == 0 else mats["glass_cyan"])

    return collection
