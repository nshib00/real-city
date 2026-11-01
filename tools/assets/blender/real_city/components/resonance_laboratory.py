"""Resonance laboratory: a compact armored instrument hall and calibration ring."""

import math

from .. import geometry as g
from .common import mat


def _ring_segment(name, collection, mats, index, *, radius=0.72, center_z=1.36,
                  y=0.10, segments=16, role="steel_light"):
    """A closed beveled-looking octagonal annulus section in the XZ plane."""
    a0 = 2 * math.pi * index / segments
    a1 = 2 * math.pi * (index + 1) / segments
    vertices = []
    for a, r, yy in ((a0, radius - .075, y - .085), (a0, radius + .075, y - .085),
                     (a1, radius + .075, y - .085), (a1, radius - .075, y - .085),
                     (a0, radius - .075, y + .085), (a0, radius + .075, y + .085),
                     (a1, radius + .075, y + .085), (a1, radius - .075, y + .085)):
        vertices.append((r * math.cos(a), yy, center_z + r * math.sin(a)))
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return g.mesh(name, collection, vertices, faces, mat(mats, role))


def add_resonance_laboratory(c, m, *, level: int, state: str) -> None:
    if level != 1:
        raise ValueError("resonance_laboratory has exactly one catalog level")
    active = state == "active"
    construction = state == "construction"
    damaged = state == "damaged"
    ruined = state == "ruined"

    def box(name, pos, size, role, *, bevel=.025, rotation=(0, 0, 0)):
        return g.box(name, c, pos, size, mat(m, role), bevel=bevel, rotation=rotation)

    def cyl(name, pos, radius, depth, role, *, vertices=16, rotation=(0, 0, 0)):
        return g.cylinder(name, c, pos, radius, depth, mat(m, role),
                          vertices=vertices, rotation=rotation)

    # Fixed floor for every state; the orchestrator supplies the shared grass tile.
    box("concrete_floor", (0, 0, .105), (2.64, 2.54, .07), "reinforced_concrete")
    for x in (-1.17, 1.17):
        box(f"floor_rail_x_{x}", (x, 0, .16), (.08, 2.47, .06), "steel_light")
    for y in (-1.10, 1.10):
        box(f"floor_rail_y_{y}", (0, y, .16), (2.38, .08, .06), "steel_light")
    for i, x in enumerate((-.88, -.44, 0, .44, .88)):
        box(f"floor_plate_{i}", (x, -.77, .15), (.42, .40, .022), "armor_dark", bevel=.007)

    # Low armored rear hall. Construction and damaged models omit major wall/roof parts.
    box("hall_base", (0, .70, .27), (2.10, .84, .26), "reinforced_concrete")
    for x in (-.95, .95):
        box(f"hall_pier_{x}", (x, .68, .59 if ruined else .77),
            (.22, .79, .60 if ruined else .96), "steel_light")
    if active:
        for x in (-.67, 0, .67):
            box(f"armored_wall_{x}", (x, 1.07, .79), (.57, .11, .76), "armor")
            box(f"wall_seam_{x}", (x, 1.01, .79), (.035, .018, .70), "dark_metal", bevel=.005)
        for i, x in enumerate((-.74, -.37, 0, .37, .74)):
            box(f"roof_plate_{i}", (x, .68, 1.31), (.39, .92, .11),
                "armor" if i % 2 else "steel_light")
    elif construction:
        for x in (-.68, 0):
            box(f"partial_wall_{x}", (x, 1.07, .55), (.59, .11, .35), "reinforced_concrete")
        for x in (-.74, 0):
            box(f"loose_roof_plate_{x}", (x, -1.01, .24), (.53, .17, .09), "armor")
    elif damaged:
        for x in (-.67, .67):
            box(f"broken_wall_{x}", (x, 1.07, .60), (.57, .11, .38), "armor")
        for x in (-.74, -.37):
            box(f"surviving_roof_{x}", (x, .68, 1.31), (.39, .92, .11), "armor")
        box("fallen_roof", (.64, -.83, .24), (.69, .30, .09), "armor", rotation=(0, 0, .28))
    else:
        for x in (-.67, 0, .67):
            box(f"wall_rubble_{x}", (x, .88, .43), (.51, .22, .20), "armor_dark")
        box("collapsed_roof", (.62, .57, .47), (.87, .65, .12), "armor", rotation=(.09, -.16, .19))

    # Two load-bearing pedestals support a large, readable open calibration ring.
    for x in (-.78, .78):
        box(f"ring_foot_{x}", (x, .10, .25), (.39, .46, .22), "reinforced_concrete")
        height = .64 if ruined else .78
        box(f"ring_support_{x}", (x, .10, .36 + height / 2),
            (.18, .24, height), "dark_metal")
        cyl(f"drive_hub_{x}", (x, -.045, .82), .19, .16, "copper",
            vertices=20, rotation=(math.pi / 2, 0, 0))
        cyl(f"hub_bearing_{x}", (x, -.14, .82), .11, .06, "steel_light",
            rotation=(math.pi / 2, 0, 0))

    # The ring is incomplete during construction and visibly severed after damage.
    if active:
        indices = range(16)
    elif construction:
        indices = list(range(0, 7)) + [13, 14, 15]
    elif damaged:
        indices = list(range(0, 6)) + list(range(8, 16))
    else:
        indices = [0, 1, 2, 8, 9, 10, 13, 14]
    for i in indices:
        _ring_segment(f"calibration_ring_{i:02d}", c, m, i,
                      role="armor_dark" if ruined else "steel_light")
        if active and i % 2 == 0:
            a = 2 * math.pi * (i + .5) / 16
            cyl(f"ring_contact_{i:02d}",
                (.72 * math.cos(a), -.01, 1.36 + .72 * math.sin(a)),
                .055, .035, "copper", vertices=10,
                rotation=(math.pi / 2, 0, 0))
    if damaged or ruined:
        for i, x in enumerate((-.82, -.42, .34, .76)):
            box(f"ring_fragment_{i}", (x, -.86 + .15 * (i % 2), .23),
                (.32, .13, .09), "steel_light", rotation=(0, 0, .26 * i))

    # Central table/steel core with exact electronics and restrained star-glass.
    box("table_plinth", (0, -.21, .31), (1.03, .64, .35), "reinforced_concrete")
    box("table_armor", (0, -.21, .52), (1.18, .72, .11), "armor_dark")
    box("table_steel_bed", (0, -.21, .62), (.84, .49, .10), "steel_light")
    if active:
        cyl("armored_core", (0, -.21, .78), .21, .23, "armor", vertices=12)
        cyl("star_glass_inlay", (0, -.21, .92), .115, .06, "star_glass", vertices=12)
        for x in (-.38, .38):
            box(f"contact_panel_{x}", (x, -.55, .70), (.19, .06, .16), "glass_cyan")
            box(f"copper_contact_{x}", (x, -.59, .70), (.04, .025, .12), "copper", bevel=.004)
    elif construction:
        box("unmounted_core_shell", (.66, -.91, .26), (.40, .34, .13), "armor")
        for x in (-.28, .28):
            box(f"exposed_cable_{x}", (x, -.52, .62), (.045, .42, .04), "copper", bevel=.005)
    elif damaged:
        cyl("darkened_core", (-.13, -.20, .76), .18, .20, "armor_dark", vertices=12)
        box("broken_display", (.30, -.53, .68), (.35, .07, .17), "glass_broken", rotation=(0, 0, .14))
    else:
        box("dead_core", (-.24, -.17, .69), (.38, .32, .12), "armor_dark", rotation=(0, 0, -.23))

    # A single side cabinet keeps the ring visible in the game camera.
    box("cabinet_base", (1.02, -.22, .31), (.45, .49, .32), "reinforced_concrete")
    if active:
        box("charge_cabinet", (1.02, -.22, .77), (.47, .52, .64), "armor")
        box("cabinet_door", (1.02, -.50, .77), (.34, .045, .50), "steel_light")
        box("cabinet_lock", (1.02, -.53, .78), (.07, .02, .11), "copper", bevel=.005)
    elif damaged:
        box("torn_cabinet", (1.03, -.18, .58), (.42, .43, .33), "armor_dark")
    elif ruined:
        box("fallen_cabinet_door", (1.02, -.77, .22), (.40, .31, .05), "armor_dark", rotation=(0, 0, -.20))
