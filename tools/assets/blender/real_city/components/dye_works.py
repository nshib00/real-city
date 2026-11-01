"""Кирпичная красильня: открытые ванны и ткань на сушильной раме."""

import math
from .. import geometry as g
from .common import mat


def add_dye_works(c, m, *, level=1, state="active"):
    brick, light, wood = (mat(m, key) for key in ("brick_warm", "brick_light", "wood_beam"))
    ruined = state == "ruined"
    damaged = state == "damaged"
    construction = state == "construction"
    def box(name, pos, size, material, rotation=(0, 0, 0)):
        masonry = name.startswith(("back_brick", "side_brick", "bath_"))
        return g.box(name, c, pos, size, material, bevel=0 if masonry else 0.018, rotation=rotation)
    # Individual staggered masonry rows leave genuine breaches in damaged states.
    rows = 2 if ruined else 4 if construction else 7
    for row in range(rows):
        for i in range(7):
            if damaged and row > 2 and i > 3:
                continue
            x = -1.05 + i * .30 + (.07 if row % 2 else 0)
            box(f"back_brick_{row}_{i}", (x, .93, .16 + row * .16),
                (.285, .19, .15), light if (row + i) % 4 == 0 else brick)
        for i in range(4):
            if (ruined or damaged) and row > 1 and i < 2:
                continue
            box(f"side_brick_{row}_{i}", (-1.14, .73 - i * .30, .16 + row * .16),
                (.19, .285, .15), brick)
    if not ruined:
        for x in (-1.13, .98):
            h = .6 if damaged and x > 0 else 1.48
            box(f"canopy_post_{x}", (x, .11, .08 + h / 2), (.105, .105, h), wood)
        if not damaged:
            box("front_lintel", (-.075, .11, 1.54), (2.23, .13, .14), wood)
            box("rear_lintel", (-.075, .93, 1.54), (2.23, .13, .14), wood)
            for x in (-1.1, -.55, 0, .55, .98):
                box(f"roof_rafter_{x}", (x, .52, 1.60), (.065, .95, .09), wood)
            if not construction:
                for i in range(12):
                    box(f"fabric_awning_{i}", (-1.11 + i * .19, .51, 1.67),
                        (.194, 1.02, .045), mat(m, "whitewash" if i % 3 == 0 else "roof_teal"))
                    box(f"awning_valance_{i}", (-1.11 + i * .19, .015, 1.59),
                        (.19, .04, .14), mat(m, "whitewash" if i % 3 == 0 else "roof_teal"))
        # Supported drying frame, cloth samples and hems identify dyeing rather than paint mixing.
        for x in (-.75, .85):
            h = .35 if damaged and x > 0 else 1.20
            box(f"drying_post_{x}", (x, -.82, .08 + h / 2), (.085, .085, h), wood)
        if not damaged and not construction:
            box("drying_rail", (.05, -.82, 1.28), (1.75, .09, .09), wood)
            for i, role in enumerate(("roof_coral", "roof_blue", "roof_gold")):
                x = -.56 + i * .56
                verts = [(x + dx, -.82 + .035 * math.sin(j * 1.7), z)
                         for j, z in enumerate((1.26, 1.04, .78, .54)) for dx in (-.20, .20)]
                cloth = g.mesh(f"hanging_dyed_cloth_{i}", c, verts,
                               [(j*2, j*2+1, j*2+3, j*2+2) for j in range(3)], mat(m, role))
                solid = cloth.modifiers.new("woven_thickness", "SOLIDIFY")
                solid.thickness = .018
                for dx in (-.15, .15):
                    box(f"cloth_peg_{i}_{dx}", (x + dx, -.84, 1.29), (.035, .05, .10), mat(m, "wood_pale"))
    # Open brick dye baths; lips, interiors and liquid are separate geometry.
    for index, (x, role) in enumerate(((-.57, "roof_coral"), (.46, "roof_blue"))):
        h = .18 if ruined or construction or (damaged and index == 1) else .57
        for row in range(max(1, round(h / .14))):
            z = .14 + row * .14
            for side in (-1, 1):
                box(f"bath_{index}_side_{row}_{side}", (x + side * .32, -.25, z), (.13, .64, .135), brick)
                box(f"bath_{index}_end_{row}_{side}", (x, -.25 + side * .29, z), (.52, .12, .135), light)
        if not construction and not ruined:
            box(f"bath_{index}_dye", (x, -.25, h - .025), (.50, .46, .025), mat(m, role))
            if not damaged:
                g.beam(f"bath_{index}_stirring_paddle", c, (x, -.25, h), (x + .17, -.1, h + .39), .045, wood)
    # Plant input bundles, supported on a work bench in the covered rear bay.
    if not ruined:
        for x in (-.7, .65):
            box(f"bench_leg_{x}", (x, .62, .32), (.08, .10, .48), wood)
        box("herb_workbench", (-.025, .62, .58), (1.65, .36, .08), mat(m, "wood_pale"))
        for i in range(6):
            g.sphere(f"herb_bundle_{i}", c, (-.66 + i * .14, .60, .70), (.09, .11, .10), mat(m, "grass_bright"), segments=8, ring_count=4)
    if construction or damaged or ruined:
        for i in range(8 if ruined else 5):
            box(f"loose_brick_{i}", (-.95 + i * .26, -1.13, .14), (.24, .14, .12), light, (0, 0, i * .37))
        box("unmounted_or_fallen_rail", (.67, .50 if ruined else -.99, .15), (.95, .105, .11), wood, (0, 0, -.22))
    if construction:
        for x in (-1.3, -.72):
            box(f"scaffold_post_{x}", (x, -.53, .53), (.065, .065, .90), mat(m, "wood_pale"))
        box("scaffold_platform", (-1.01, -.53, .73), (.69, .30, .07), wood)


def build_lod(level, state, lod_name, mats):
    """Авторские LOD: цельная кладка сохраняет стены без щелей decimate."""
    from .. import ground
    c = g.create_collection(f"dye_works_l{level:02d}_{state}_{lod_name}_tmp")
    ground.add_ground_tile(c, mats, prefix=f"dye_works_l{level:02d}", include_path=True)
    fine = lod_name == "LOD1"
    ruined, damaged, construction = (state == x for x in ("ruined", "damaged", "construction"))
    def b(name, pos, size, role):
        return g.box(name, c, pos, size, mat(mats, role), bevel=.012 if fine else 0)
    h = .32 if ruined else .64 if construction else 1.12
    b("back_left", (-.57, .93, .08+h/2), (1.44, .19, h), "brick_warm")
    rh = .48 if damaged else h
    b("back_right", (.58, .93, .08+rh/2), (.87, .19, rh), "brick_light")
    b("side_wall", (-1.14, .28, .08+h/2), (.19, 1.10, h), "brick_warm")
    if not ruined:
        for x in (-1.13, .98):
            ph = .6 if damaged and x > 0 else 1.48
            b(f"post{x}", (x, .11, .08+ph/2), (.105,.105,ph), "wood_beam")
        if not damaged:
            for y in (.11,.93): b(f"lintel{y}",(-.075,y,1.54),(2.23,.13,.14),"wood_beam")
            if construction:
                for x in (-1.1,0,.98): b(f"rafter{x}",(x,.52,1.60),(.065,.95,.09),"wood_beam")
            else:
                b("awning",(-.065,.51,1.67),(2.28,1.02,.045),"roof_teal")
                for x in (-1.11,-.54,.03,.60): b(f"stripe{x}",(x,.51,1.695),(.19,1.02,.012),"whitewash")
        for x in (-.75,.85):
            ph=.35 if damaged and x>0 else 1.20
            b(f"dry_post{x}",(x,-.82,.08+ph/2),(.085,.085,ph),"wood_beam")
        if not damaged and not construction:
            b("dry_rail",(.05,-.82,1.28),(1.75,.09,.09),"wood_beam")
            for i,role in enumerate(("roof_coral","roof_blue","roof_gold")):
                b(f"cloth{i}",(-.56+i*.56,-.82,.90),(.40,.025,.72),role)
        for x in (-.7,.65): b(f"bench_leg{x}",(x,.62,.32),(.08,.10,.48),"wood_beam")
        b("bench",(-.025,.62,.58),(1.65,.36,.08),"wood_pale")
        b("herbs",(-.32,.60,.69),(.78,.22,.14),"grass_bright")
    for i,x in enumerate((-.57,.46)):
        bh=.18 if ruined or construction or (damaged and i==1) else .57
        for side in (-1,1):
            b(f"bath_side{i}_{side}",(x+side*.32,-.25,.08+bh/2),(.13,.64,bh),"brick_warm")
            b(f"bath_end{i}_{side}",(x,-.25+side*.29,.08+bh/2),(.52,.12,bh),"brick_light")
        if not ruined and not construction:
            b(f"liquid{i}",(x,-.25,bh-.025),(.50,.46,.025),"roof_coral" if i==0 else "roof_blue")
    if state != "active":
        for i in range(5): b(f"debris{i}",(-.95+i*.32,-1.13,.14),(.24,.14,.12),"brick_light")
        b("fallen_rail",(.67,-.99,.15),(.95,.105,.11),"wood_beam")
    return c
