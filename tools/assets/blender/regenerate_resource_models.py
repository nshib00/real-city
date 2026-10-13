"""Resource meshes and tightly framed transparent icons; isolated Blender batch."""
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = ROOT / 'frontend/public/assets/resources/icons'
spec = importlib.util.spec_from_file_location('resource_geometry', Path(__file__).with_name('generate_resource_icons.py'))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def resource_list(output=None):
    """Use the full resource icon manifest when present, not just the old GLB subset."""
    manifest_path = Path(output or DEFAULT_OUT_DIR) / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        catalog_overrides = {
            'light_crystal': {'name': 'Светокристалл', 'category': 'rare'},
            'influence_seal': {'name': 'Печать влияния', 'category': 'rare'},
        }
        resources = []
        for item in manifest.get('resources', []):
            override = catalog_overrides.get(item['id'], {})
            resources.append({
                'id': item['id'],
                'name': override.get('name', item['name']),
                'category': override.get('category', item['category']),
            })
        if resources:
            present = {item['id'] for item in resources}
            catalog_aliases = [
                {'id': 'mechanism', 'name': 'Механизм', 'category': 'crafted'},
                {'id': 'super_mechanism', 'name': 'Супер-механизм', 'category': 'rare'},
                {'id': 'rune_tile', 'name': 'Руническая черепица', 'category': 'rare'},
            ]
            resources.extend(item for item in catalog_aliases if item['id'] not in present)
            return resources
    return G.RESOURCES


def sphere(name, collection, loc, scale, material, segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=min(segments, 16), ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    G.apply_transform(obj)
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return G.link_to(collection, obj)


def leaf(name, collection, loc, scale, material, rot=(0, 0, 0)):
    # A broad folded blade, not a flat diamond or a crystal-like spike.
    verts = [(0,-.72,0),(-.31,-.3,.015),(-.42,.18,0),(-.23,.5,0),(0,.72,0),
             (.23,.5,0),(.42,.18,0),(.31,-.3,.015),(0,0,.11)]
    faces = [(i,(i+1)%8,8) for i in range(8)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    obj = bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.location, obj.scale, obj.rotation_euler = loc, scale, rot
    mesh.materials.append(material)
    mod = obj.modifiers.new('leaf_thickness','SOLIDIFY')
    mod.thickness = .025
    return obj


def shard(name, collection, loc, height, material, rot=(0,0,0), radius=.15):
    verts = [(radius*math.cos(i*math.tau/6),radius*math.sin(i*math.tau/6),z)
             for z in (-height/2,height*.26) for i in range(6)]
    verts.append((0,0,height/2))
    faces = [tuple(reversed(range(6)))]
    faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    faces += [(i+6,(i+1)%6+6,12) for i in range(6)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    obj = bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.location,obj.rotation_euler = loc,rot
    mesh.materials.append(material)
    return obj


def faceted_crystal(name, collection, loc, height, radius, material, core_material, glow_material, rot=(0, 0, 0)):
    verts = []
    levels = [
        (0.0, radius * .72, .18),
        (height * .16, radius * 1.08, 0.0),
        (height * .68, radius * .92, .11),
        (height * .88, radius * .58, -.05),
    ]
    for z, r, phase in levels:
        for i in range(6):
            a = i * math.tau / 6 + phase
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    tip = len(verts)
    verts.append((0, 0, height))
    faces = [tuple(reversed(range(6)))]
    for ring in range(len(levels) - 1):
        base = ring * 6
        nxt = (ring + 1) * 6
        for i in range(6):
            faces.append((base + i, base + (i + 1) % 6, nxt + (i + 1) % 6, nxt + i))
    top = (len(levels) - 1) * 6
    for i in range(6):
        faces.append((top + i, top + (i + 1) % 6, tip))
    mesh = bpy.data.meshes.new(f'{name}_mesh')
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    inner_h = height * .58
    inner_z = loc[2] + height * .18
    inner = shard(f'{name}_inner_lumen', collection, (loc[0] + radius * .1, loc[1] - radius * .08, inner_z), inner_h, core_material, (rot[0], rot[1] + .08, rot[2] + .18), radius * .28)
    glow = G.cube(f'{name}_vertical_glow', collection, (loc[0] - radius * .16, loc[1] - radius * .22, loc[2] + height * .48), (radius * .12, radius * .05, height * .46), glow_material, (rot[0] + .08, rot[1] - .12, rot[2] + .28))
    rim = G.cube(f'{name}_edge_flash', collection, (loc[0] + radius * .28, loc[1] - radius * .2, loc[2] + height * .58), (radius * .09, radius * .035, height * .48), glow_material, (rot[0] - .04, rot[1] + .18, rot[2] - .18))
    return obj


def crystal(collection):
    crystal_mat = G.MATS.get('amethyst_shell', G.MATS['amethyst'])
    core_mat = G.MATS.get('amethyst_core', G.MATS['amethyst'])
    glow_mat = G.MATS.get('amethyst_inner_light', G.MATS['rune'])
    for i, (x, y, h, tilt, radius) in enumerate((
        (-.3, -.02, .82, -18, .15),
        (-.04, .08, 1.28, 2, .19),
        (.24, .02, 1.08, 16, .17),
        (.42, -.12, .62, 28, .1),
    )):
        faceted_crystal(f'amethyst_faceted_prism_{i}', collection, (x, y, 0), h, radius, crystal_mat, core_mat, glow_mat, (0, math.radians(tilt), math.radians(4 * i - 6)))
    for i, (x, y, h, r, angle) in enumerate(((-.34, -.27, .24, .07, -.4), (-.08, -.3, .34, .08, .18), (.22, -.28, .26, .06, .46), (.42, -.22, .22, .055, -.12))):
        shard(f'amethyst_base_splinter_{i}', collection, (x, y, h / 2), h, glow_mat if i % 2 else crystal_mat, (0, math.radians(58), angle), r)


def windleaf(collection):
    for i,angle in enumerate((-.55,0,.55)):
        leaf(f'windleaf_blade_{i}',collection,(i*.08-.08,0,.2+i*.08),(.63,.78,.65),
             G.MATS['leaf'] if i!=1 else G.MATS['leaf_light'],(.25,0,angle))
        G.cube(f'windleaf_rib_{i}',collection,(i*.08-.08,0,.28+i*.08),(.024,.75,.024),G.MATS['leaf_dark'],(.25,0,angle))
    # Keep the harvested leaf clean: no board or tie crossing through the blades.
    G.cylinder('windleaf_base_stem', collection, (-.04, -.38, .16), .028, .48, G.MATS['leaf_dark'], vertices=10, rot=(math.radians(74), 0, math.radians(-8)))


def steel(collection):
    for i in range(2):
        x,y,z = i*.12-.08,i*.29-.17,.1+i*.07
        for height in (z,z+.27):
            G.cube(f'steel_flange_{i}_{height}',collection,(x,y,height),(.92,.22,.06),G.MATS['steel'])
        G.cube(f'steel_web_{i}',collection,(x,y,z+.135),(.92,.05,.24),G.MATS['steel'])


def metal(collection):
    for i in range(3):
        G.cube(f'scrap_plate_{i}',collection,(i*.14-.16,0,.07+i*.085),(.65,.52,.075),
               G.MATS['metal'],(0,0,i*.24-.2))
    G.cylinder('scrap_cog_hub',collection,(.3,-.24,.28),.15,.09,G.MATS['iron'],vertices=16)
    for i in range(8):
        a=i*math.tau/8
        G.cube(f'cog_tooth_{i}',collection,(.3+.16*math.cos(a),-.24+.16*math.sin(a),.28),
               (.09,.07,.07),G.MATS['iron'],(0,0,a))


def glass(collection):
    for i in range(3):
        G.cube(f'glass_sheet_{i}',collection,(i*.15-.15,i*.075,.42+i*.02),(.51,.045,.78),
               G.MATS['glass'],(0,-.18,0))
        G.cube(f'glass_edge_{i}',collection,(i*.15-.38,i*.075-.03,.43+i*.02),(.028,.022,.67),
               G.MATS['rune'],(0,-.18,0))


def fiber(collection):
    for i in range(7):
        G.cylinder(f'super_fiber_strand_{i}',collection,((i%3)*.11-.11,(i//3)*.12-.1,.38),
                   .045,.73+(i%2)*.15,G.MATS['fabric_light'],vertices=10,rot=(0,(i-3)*.065,0))
    for z in (.19,.5):
        G.cube(f'fiber_tie_{z}',collection,(0,.03,z),(.34,.31,.065),G.MATS['gold'])


def reed(collection):
    for i, x in enumerate((-.28, -.12, .05, .2, .34)):
        h = .72 + (i % 2) * .14
        G.cylinder(f'reed_stalk_{i}', collection, (x, .04 * i - .1, h / 2), .035, h, G.MATS['leaf_dark'], vertices=10, rot=(.08 * (i - 2), 0, .05 * i))
        G.cylinder(f'reed_head_{i}', collection, (x + .04, .04 * i - .1, h + .08), .055, .22, G.MATS['wood'], vertices=12, rot=(.08 * (i - 2), 0, .05 * i))
        leaf(f'reed_leaf_{i}', collection, (x + .05, .04 * i - .18, .36 + .05 * (i % 2)), (.16, .28, .16), G.MATS['leaf'], (.75, 0, .45 - i * .12))


def flax(collection):
    for i, x in enumerate((-.26, -.1, .07, .23)):
        G.cylinder(f'flax_stem_{i}', collection, (x, .02 * i, .34), .025, .68, G.MATS['leaf_dark'], vertices=8, rot=(.05 * (i - 1), 0, -.08 * i))
        sphere(f'flax_bloom_{i}', collection, (x, .02 * i, .72), (.09, .08, .045), G.MATS['glass'], 12)
    G.cube('flax_twine_wrap', collection, (0, -.12, .22), (.48, .08, .07), G.MATS['rope'] if 'rope' in G.MATS else G.MATS['sand'], (0, 0, -.18))


def oil_plants(collection):
    for i, angle in enumerate((-.55, -.2, .2, .55)):
        leaf(f'oil_leaf_{i}', collection, (0, .02 * i, .25 + .03 * i), (.36, .5, .34), G.MATS['leaf'], (.65, 0, angle))
    for i, (x, y) in enumerate(((-.2, -.05), (.05, .06), (.26, -.09))):
        sphere(f'oil_seed_pod_{i}', collection, (x, y, .58), (.13, .1, .12), G.MATS['fuel_light'], 14)


def sugar_cane(collection):
    for i, x in enumerate((-.2, 0, .2)):
        G.cylinder(f'cane_stalk_{i}', collection, (x, 0, .42), .055, .84, G.MATS['leaf_dark'], vertices=10, rot=(.05 * (i - 1), 0, .05 * i))
        for z in (.22, .42, .62):
            G.cylinder(f'cane_node_{i}_{z}', collection, (x, 0, z), .06, .035, G.MATS['sand_light'], vertices=10, rot=(math.pi / 2, 0, 0))
        leaf(f'cane_leaf_{i}', collection, (x + .05, -.06, .78), (.18, .34, .18), G.MATS['leaf_light'], (.75, 0, .35 + i * .24))


def rare_flowers(collection):
    for i, (x, y, color) in enumerate(((-.28, -.05, 'fabric_light'), (-.04, .08, 'amethyst'), (.22, -.07, 'rune'))):
        G.cylinder(f'flower_stem_{i}', collection, (x, y, .28), .022, .54, G.MATS['leaf_dark'], vertices=8, rot=(.08 * i, 0, -.04 * i))
        for p in range(6):
            a = p * math.tau / 6
            sphere(f'flower_petal_{i}_{p}', collection, (x + math.cos(a) * .08, y + math.sin(a) * .055, .58), (.05, .032, .025), G.MATS[color], 8)
        sphere(f'flower_core_{i}', collection, (x, y, .59), (.04, .035, .025), G.MATS['gold'], 8)


def crystal_fruit(collection):
    G.cylinder('fruit_branch', collection, (0, 0, .34), .045, .86, G.MATS['bark'], vertices=10, rot=(0, math.pi / 2, -.22))
    for i, (x, y, z) in enumerate(((-.25, -.08, .42), (0, .08, .52), (.26, -.04, .44))):
        sphere(f'crystal_fruit_{i}', collection, (x, y, z), (.13, .11, .15), G.MATS['amethyst'], 14)
        leaf(f'fruit_leaf_{i}', collection, (x + .05, y + .06, z + .08), (.13, .18, .13), G.MATS['leaf_light'], (.7, 0, .45 * i))


def sap(collection):
    resin(collection)
    G.cylinder('sap_spile', collection, (.28, -.18, .32), .035, .36, G.MATS['metal'], vertices=10, rot=(0, math.pi / 2, -.25))


def premium_planks(collection):
    G.build_planks(collection)
    for i, y in enumerate((-.24, 0, .24)):
        G.cube(f'premium_plank_inlay_{i}', collection, (-.02, y - .04, .34 + i * .035), (.7, .025, .02), G.MATS['gold'], (0, 0, -.16))
    sphere('premium_sap_gem', collection, (.36, .26, .48), (.055, .045, .045), G.MATS['resin'], 10)


def rope(collection):
    for i, r in enumerate((.34, .25, .16)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=.035, major_segments=34, minor_segments=8, location=(0, 0, .13 + i * .07), rotation=(0, 0, .12 * i))
        obj = bpy.context.object
        obj.name = f'rope_coil_{i}'
        obj.data.materials.append(G.MATS['sand'])
        G.link_to(collection, obj)
    G.cube('rope_end_tag', collection, (.32, -.18, .25), (.22, .06, .045), G.MATS['wood_cut'], (0, 0, -.4))


def copper_parts(collection):
    metal(collection)
    for i, a in enumerate((0, math.tau / 3, math.tau * 2 / 3)):
        G.cylinder(f'copper_coil_{i}', collection, (-.26 + .08 * i, .2 - .04 * i, .34), .065, .26, G.MATS['copper'], vertices=14, rot=(math.pi / 2, 0, a))


def tools(collection):
    G.cylinder('hammer_handle', collection, (-.1, -.02, .32), .035, .82, G.MATS['wood'], vertices=10, rot=(0, math.pi / 2, -.55))
    G.cube('hammer_head', collection, (.22, -.22, .5), (.36, .16, .14), G.MATS['steel'], (0, 0, -.55))
    G.cylinder('pick_handle', collection, (.05, .18, .28), .03, .76, G.MATS['wood_dark'], vertices=10, rot=(0, math.pi / 2, .45))
    G.cube('pick_head', collection, (-.22, .42, .45), (.5, .08, .1), G.MATS['iron'], (0, 0, .45))


def paper(collection):
    for i, (x, y, z) in enumerate(((-.08, -.08, .14), (.04, .02, .2), (.13, .12, .26))):
        G.cube(f'paper_sheet_{i}', collection, (x, y, z), (.62, .42, .025), G.MATS['mortar'], (0, 0, -.18 + .1 * i))
        G.cube(f'paper_line_{i}', collection, (x - .07, y - .14, z + .02), (.34, .018, .012), G.MATS['wood'], (0, 0, -.18 + .1 * i))
    G.cylinder('paper_scroll', collection, (-.32, .18, .34), .075, .48, G.MATS['mortar'], vertices=18, rot=(0, math.pi / 2, .25))


def paints(collection):
    for i, (x, mat_name) in enumerate(((-.24, 'fabric_light'), (0, 'rune'), (.24, 'fuel_light'))):
        G.cylinder(f'paint_pot_{i}', collection, (x, 0, .22), .13, .28, G.MATS['metal'], vertices=16)
        sphere(f'paint_blob_{i}', collection, (x, -.02, .39), (.12, .1, .04), G.MATS[mat_name], 12)
        G.cube(f'paint_brush_{i}', collection, (x + .08, -.18, .43), (.035, .34, .035), G.MATS['wood_cut'], (0, 0, .35))


def reinforced_concrete(collection):
    G.build_concrete(collection)
    for i, y in enumerate((-.18, .02, .22)):
        G.cylinder(f'rebar_visible_{i}', collection, (.26, y, .58), .024, .44, G.MATS['steel'], vertices=10, rot=(0, math.pi / 2, -.18))


def mechanisms(collection, super_variant=False):
    gear_mat = G.MATS['gold'] if super_variant else G.MATS['copper']
    for gi, (x, y, r) in enumerate(((-.18, .02, .18), (.18, -.06, .22))):
        G.cylinder(f'gear_core_{gi}', collection, (x, y, .32 + .05 * gi), r, .09, gear_mat, vertices=20)
        G.cylinder(f'gear_hole_{gi}', collection, (x, y, .38 + .05 * gi), r * .42, .095, G.MATS['metal'], vertices=16)
        for t in range(10):
            a = t * math.tau / 10
            G.cube(f'gear_tooth_{gi}_{t}', collection, (x + math.cos(a) * (r + .04), y + math.sin(a) * (r + .04), .36 + .05 * gi), (.08, .045, .06), gear_mat, (0, 0, a))
    if super_variant:
        shard('super_mechanism_crystal', collection, (.02, .2, .55), .42, G.MATS['amethyst'], (0, .18, 0), .08)


def lenses(collection):
    for i, (x, y, s) in enumerate(((-.18, .02, 1), (.2, -.06, .82))):
        G.cylinder(f'lens_frame_{i}', collection, (x, y, .32), .2 * s, .055, G.MATS['gold'], vertices=28)
        sphere(f'lens_glass_{i}', collection, (x, y, .35), (.17 * s, .17 * s, .035), G.MATS['glass'], 18)
    G.cube('lens_handle', collection, (.03, -.24, .22), (.08, .52, .06), G.MATS['wood_dark'], (0, 0, -.4))


def reinforced_beams(collection):
    for i, y in enumerate((-.18, .16)):
        G.cube(f'beam_wood_{i}', collection, (0, y, .23 + i * .08), (.88, .16, .14), G.MATS['wood_cut'], (0, 0, -.12))
        for x in (-.34, .34):
            G.cube(f'beam_cap_{i}_{x}', collection, (x, y, .32 + i * .08), (.08, .19, .19), G.MATS['steel'], (0, 0, -.12))


def armor_plates(collection):
    for i, (x, y) in enumerate(((-.2, -.08), (.06, .03), (.27, -.12))):
        G.cube(f'armor_plate_{i}', collection, (x, y, .24 + .07 * i), (.48, .34, .07), G.MATS['steel'], (0, .18, -.18 + .14 * i))
        G.cylinder(f'armor_rivet_{i}_a', collection, (x - .16, y - .1, .31 + .07 * i), .03, .025, G.MATS['gold'], vertices=10)
        G.cylinder(f'armor_rivet_{i}_b', collection, (x + .16, y - .1, .31 + .07 * i), .03, .025, G.MATS['gold'], vertices=10)


def dust_pile(collection, mat_name, accent='rune'):
    sphere('dust_mound', collection, (0, 0, .12), (.46, .32, .16), G.MATS[mat_name], 14)
    for i in range(7):
        a = i * math.tau / 7
        sphere(f'dust_spark_{i}', collection, (.32 * math.cos(a), .22 * math.sin(a), .18 + .04 * (i % 2)), (.04, .032, .025), G.MATS[accent], 8)
    G.cube('dust_scoop_spoon', collection, (.28, .18, .28), (.34, .11, .04), G.MATS['wood_cut'], (0, 0, .35))


def star_glass(collection):
    glass(collection)
    for i, (x, y, z) in enumerate(((-.18, -.03, .52), (.04, .04, .6), (.2, .1, .48))):
        sphere(f'star_glint_{i}', collection, (x, y, z), (.035, .025, .035), G.MATS['rune'], 8)


def stone_heart(collection):
    rocks(collection, 'stone')
    sphere('stone_heart_core', collection, (.04, -.03, .45), (.22, .18, .2), G.MATS['stone_dark'], 14)
    shard('stone_heart_rune', collection, (.05, -.08, .58), .28, G.MATS['rune'], (0, .12, 0), .055)


def aeolian_alloy(collection):
    for i, mat_name in enumerate(('steel', 'amethyst', 'copper')):
        G.cube(f'alloy_ingot_{i}', collection, ((i - 1) * .2, .04 * i, .24 + .06 * i), (.52, .22, .14), G.MATS[mat_name], (0, 0, -.18 + .12 * i))
    G.cube('alloy_wind_inlay', collection, (0, -.16, .48), (.58, .03, .025), G.MATS['rune'], (0, 0, -.08))


def printing_plate(collection):
    G.cube('printing_plate_base', collection, (0, 0, .22), (.72, .52, .1), G.MATS['copper'], (0, 0, .08))
    for i, x in enumerate((-.22, 0, .22)):
        G.cube(f'printing_glyph_bar_{i}', collection, (x, -.05, .31), (.05, .32, .035), G.MATS['gold_dark'], (0, 0, .08))
    G.cylinder('printing_coin_stamp', collection, (.22, .16, .34), .09, .035, G.MATS['gold'], vertices=18)


def runic_tile(collection):
    for i, (x, y) in enumerate(((-.18, -.1), (.18, -.06), (0, .18))):
        G.cube(f'runic_tile_{i}', collection, (x, y, .2 + .03 * i), (.34, .3, .08), G.MATS['stone'], (0, 0, .22 * i))
        G.cube(f'runic_mark_{i}', collection, (x, y - .06, .27 + .03 * i), (.19, .025, .02), G.MATS['rune'], (0, 0, .22 * i))


def influence_seal(collection):
    G.cylinder('seal_disc', collection, (0, 0, .28), .36, .12, G.MATS['fabric'], vertices=32)
    G.cylinder('seal_inner', collection, (0, 0, .36), .23, .045, G.MATS['gold'], vertices=28)
    G.cube('seal_ribbon_left', collection, (-.16, -.3, .18), (.14, .42, .05), G.MATS['fabric_light'], (0, 0, .25))
    G.cube('seal_ribbon_right', collection, (.16, -.3, .18), (.14, .42, .05), G.MATS['fabric_light'], (0, 0, -.25))


def monster_trophy(collection):
    for i, x in enumerate((-.14, .14)):
        shard(f'trophy_claw_{i}', collection, (x, 0, .36), .62, G.MATS['mortar'], (0, .32 * (-1 if i else 1), .14 * (-1 if i else 1)), .07)
    G.cube('trophy_binding', collection, (0, -.08, .16), (.42, .12, .08), G.MATS['wood_dark'], (0, 0, -.08))
    sphere('trophy_red_mark', collection, (.02, -.19, .28), (.06, .04, .04), G.MATS['fabric'], 8)


def relic_fragment(collection):
    for i, (x, y, r) in enumerate(((-.22, -.03, .18), (.04, .08, -.05), (.25, -.1, .23))):
        G.cube(f'relic_stone_{i}', collection, (x, y, .24 + .04 * i), (.36, .28, .1), G.MATS['stone_light'], (0, .08, r))
        G.cube(f'relic_glyph_{i}', collection, (x, y - .08, .31 + .04 * i), (.17, .022, .018), G.MATS['amethyst'], (0, 0, r))


def festival_token(collection):
    G.cylinder('festival_token_coin', collection, (0, 0, .28), .34, .11, G.MATS['gold'], vertices=32)
    for i, (a, mat_name) in enumerate(((0, 'fabric_light'), (math.tau / 3, 'rune'), (math.tau * 2 / 3, 'leaf_light'))):
        G.cube(f'token_ribbon_{i}', collection, (.2 * math.cos(a), .2 * math.sin(a), .38), (.24, .045, .028), G.MATS[mat_name], (0, 0, a))
    sphere('token_center_glint', collection, (0, 0, .41), (.06, .05, .025), G.MATS['rune'], 8)


def sand(collection):
    sphere('sand_heap',collection,(0,0,.12),(.55,.42,.19),G.MATS['sand'])
    for i in range(8):
        a=i*math.tau/8
        sphere(f'sand_grain_{i}',collection,(.4*math.cos(a),.31*math.sin(a),.14),(.045,.04,.035),G.MATS['sand_light'],12)
    G.cube('sand_scoop',collection,(.25,.18,.31),(.32,.22,.055),G.MATS['wood_cut'],(.3,.2,.3))


def rocks(collection, material):
    for i,(x,y,z,s) in enumerate(((-.28,-.13,.2,.31),(.16,.1,.3,.42),(.37,-.2,.13,.23))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=s,location=(x,y,z))
        obj=bpy.context.object
        obj.name=f'{material}_chunk_{i}'
        obj.scale=(1,.83,.8)
        obj.data.materials.append(G.MATS[material])
        G.link_to(collection,obj)
        if material=='iron_ore':
            for j in range(3):
                G.cube(f'ore_seam_{i}_{j}',collection,(x+(j-1)*.1,y-.16,z+.12),(.08,.055,.12),G.MATS['iron'],(0,.3,.2))


def oil(collection):
    G.cylinder('oil_barrel',collection,(0,0,.34),.31,.65,G.MATS['oil'],vertices=24)
    for z in (.09,.54):
        G.cylinder(f'barrel_hoop_{z}',collection,(0,0,z),.324,.07,G.MATS['iron'],vertices=24)
    G.cylinder('oil_bung',collection,(.14,-.05,.69),.06,.035,G.MATS['metal'],vertices=12)
    sphere('oil_drop',collection,(.4,-.22,.09),(.13,.1,.065),G.MATS['oil'])


def resin(collection):
    G.cube('resin_bark',collection,(0,.12,.055),(.75,.4,.09),G.MATS['bark'],(0,0,.15))
    for i,(x,y,s) in enumerate(((-.25,-.1,.2),(.08,.1,.27),(.33,-.15,.16))):
        sphere(f'amber_resin_{i}',collection,(x,y,s*.75),(s,s*.78,s*.8),G.MATS['resin'])
        sphere(f'resin_glint_{i}',collection,(x-.045,y-.09,s*1.35),(.025,.018,.045),G.MATS['wood_highlight'],12)


def wood(collection):
    angle=.2
    axis=Vector((math.cos(angle),math.sin(angle),0))
    for i,y in enumerate((-.22,.06,.34)):
        center=Vector((0,y,.17+i*.02))
        rot=(0,math.pi/2,angle)
        G.cylinder(f'log_bark_{i}',collection,center,.15,1.04,G.MATS['bark'],vertices=18,rot=rot)
        for side in (-1,1):
            end=center+axis*(.525*side)
            G.cylinder(f'log_cut_{i}_{side}',collection,end,.148,.018,G.MATS['wood_cut'],vertices=18,rot=rot)
            G.cylinder(f'log_ring_{i}_{side}',collection,end+axis*(.012*side),.086,.009,G.MATS['wood'],vertices=18,rot=rot)
    G.cube('timber_binding',collection,(0,.05,.36),(.075,.83,.05),G.MATS['fabric'],(0,0,angle))
    leaf('timber_sprout',collection,(.38,.32,.34),(.2,.27,.2),G.MATS['leaf'],(.3,.2,-.3))


def explosives(collection):
    G.cylinder('powder_keg',collection,(0,0,.3),.3,.58,G.MATS['wood_dark'],vertices=20)
    for z in (.1,.48):
        G.cylinder(f'keg_hoop_{z}',collection,(0,0,z),.31,.065,G.MATS['iron'],vertices=20)
    points=[Vector((0,0,.59)),Vector((.05,0,.8)),Vector((.24,0,.84))]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        obj=G.cylinder(f'curved_fuse_{i}',collection,(a+b)/2,.026,(b-a).length,G.MATS['sand'],vertices=10)
        obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    sphere('fuse_ember',collection,points[-1],(.045,.045,.045),G.MATS['fuel_light'],12)


def configure_geometry():
    G.sphere=sphere
    G.add_leaf=leaf
    G.add_shard=shard
    G.make_materials()
    G.MATS['rope'] = G.mat('rope', (.72, .55, .32, 1), .68)
    G.MATS['amethyst_shell'] = G.mat('amethyst_shell', (.42, .05, .82, 1), .14, 0, .82, emission=(.28, .04, .82, 1), emission_strength=.12)
    G.MATS['amethyst_core'] = G.mat('amethyst_core', (.08, .01, .22, 1), .28, 0, .96, emission=(.2, .01, .48, 1), emission_strength=.14)
    G.MATS['amethyst_inner_light'] = G.mat('amethyst_inner_light', (.72, .38, 1, 1), .12, 0, .86, emission=(.75, .16, 1, 1), emission_strength=.9)
    for key,material in G.MATS.items():
        shader=material.node_tree.nodes.get('Principled BSDF')
        color=shader.inputs['Base Color'].default_value
        # The art palette is authored in display sRGB; Principled expects linear RGB.
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in color[:3]]
        shader.inputs['Base Color'].default_value=(*linear,color[3])
        material.diffuse_color=(*linear,color[3])
    # Opaque tinted surfaces keep liquid and rare-resource silhouettes readable at 24px.
    for key in ('amethyst','resin','oil'):
        shader=G.MATS[key].node_tree.nodes.get('Principled BSDF')
        shader.inputs['Alpha'].default_value=1
    G.MATS['amethyst'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.06
    G.BUILDERS.update({'aeolian-crystal':crystal,'windleaf':windleaf,'super-fiber':fiber,
                       'metal':metal,'steel':steel,'glass':glass,'sand':sand,'oil':oil,
                       'resin':resin,'wood':wood,'explosives':explosives})
    G.BUILDERS.update({
        'flax': flax,
        'reed': reed,
        'fiber': fiber,
        'dyes': paints,
        'oil_plants': oil_plants,
        'sugar_cane': sugar_cane,
        'rare_flowers': rare_flowers,
        'crystal_fruit': crystal_fruit,
        'sap': sap,
        'premium_planks': premium_planks,
        'rope': rope,
        'iron_ingot': lambda c: G.build_ingots(c, 'iron'),
        'gold_ingot': lambda c: G.build_ingots(c, 'gold'),
        'reinforced_concrete': reinforced_concrete,
        'copper_parts': copper_parts,
        'tools': tools,
        'paper': paper,
        'paints': paints,
        'vegetable_oil': lambda c: G.build_flask(c, G.MATS['fuel_light']),
        'mechanisms': mechanisms,
        'super-mechanisms': lambda c: mechanisms(c, True),
        'mechanism': mechanisms,
        'super_mechanism': lambda c: mechanisms(c, True),
        'lenses': lenses,
        'reinforced_beams': reinforced_beams,
        'armor_plates': armor_plates,
        'light_crystal': lambda c: crystal(c),
        'amber_essence': lambda c: G.build_flask(c, G.MATS['resin']),
        'emerald_dust': lambda c: dust_pile(c, 'leaf_light', 'rune'),
        'blue_salt': lambda c: dust_pile(c, 'glass', 'rune'),
        'star_glass': star_glass,
        'stone_heart': stone_heart,
        'aeolian_alloy': aeolian_alloy,
        'printing_plate': printing_plate,
        'runic_tile': runic_tile,
        'rune_tile': runic_tile,
        'silent_powder': lambda c: dust_pile(c, 'powder', 'amethyst'),
        'memory_shard': lambda c: build_memory_shards(c),
        'super-windleaf': lambda c: windleaf(c),
        'influence_seal': influence_seal,
        'monster_trophy': monster_trophy,
        'relic_fragment': relic_fragment,
                       'festival_token': festival_token,
    })
    for key in ('stone','coal','iron_ore'):
        G.BUILDERS[key]=lambda c,k=key:rocks(c,k)


def primary_material_name(obj):
    if obj.data.materials:
        return obj.data.materials[0].name.lower()
    return ''


def high_detail_profile(obj):
    """Return bevel/displacement settings for high-detail resource icon meshes."""
    mat = primary_material_name(obj)
    name = obj.name.lower()
    dims = [abs(v) for v in obj.dimensions if abs(v) > 1e-5]
    shortest = min(dims) if dims else 0.05
    organic = any(key in mat or key in name for key in (
        'wood', 'bark', 'leaf', 'mushroom', 'resin', 'sand', 'stone', 'clay',
        'coal', 'ore', 'cement', 'concrete', 'fabric', 'rope', 'powder',
        'flower', 'reed', 'flax', 'cane', 'fiber', 'trophy', 'relic'
    ))
    hard_surface = any(key in mat or key in name for key in (
        'metal', 'iron', 'steel', 'gold', 'copper', 'glass', 'amethyst',
        'rune', 'mechanism', 'lens', 'plate', 'coin', 'ingot'
    ))
    bevel = max(0.006, min(0.035, shortest * (0.22 if hard_surface else 0.16)))
    segments = 5 if hard_surface else 4
    strength = 0.0
    if organic:
        strength = max(0.003, min(0.018, shortest * 0.06))
    if 'glass' in mat or 'amethyst' in mat or 'rune' in mat:
        strength = 0.0
    return bevel, segments, strength


def apply_named_modifier(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)


def high_detail_mesh_pass(collection, rid):
    """Upgrade generated resource props from simple mid-poly forms to final high-detail meshes."""
    for obj in list(collection.objects):
        if obj.type != 'MESH':
            continue
        preserve_facets = 'faceted_prism' in obj.name or 'base_splinter' in obj.name or 'inner_lumen' in obj.name
        bevel_width, bevel_segments, displace_strength = high_detail_profile(obj)
        if preserve_facets:
            bevel_width = min(bevel_width, 0.008)
            bevel_segments = 1
            displace_strength = 0.0
        if displace_strength:
            texture = bpy.data.textures.new(f'{rid}_{obj.name}_handpaint_noise', type='VORONOI')
            texture.noise_scale = 0.72
            texture.intensity = 0.18
            texture.contrast = 0.28
            displace = obj.modifiers.new(f'{obj.name}_subtle_surface_relief', 'DISPLACE')
            displace.strength = displace_strength
            displace.texture = texture
            apply_named_modifier(obj, displace)
        bevel = obj.modifiers.new(f'{obj.name}_high_detail_bevel', 'BEVEL')
        bevel.width = bevel_width
        bevel.segments = bevel_segments
        bevel.profile = 0.42
        bevel.affect = 'EDGES'
        apply_named_modifier(obj, bevel)
        try:
            normals = obj.modifiers.new(f'{obj.name}_weighted_normals', 'WEIGHTED_NORMAL')
            normals.keep_sharp = True
            apply_named_modifier(obj, normals)
        except Exception:
            pass
        for poly in obj.data.polygons:
            poly.use_smooth = not preserve_facets


def add_aeolian_detail_motifs(collection, rid):
    """Add small readable craft details so icons do not look like primitive silhouettes."""
    detail_mat = G.MATS.get('gold') or G.MATS.get('rune')
    rune_mat = G.MATS.get('rune') or detail_mat
    if rid in {'coins', 'festival_token', 'influence_seal'}:
        for i, radius in enumerate((0.18, 0.24)):
            bpy.ops.mesh.primitive_torus_add(
                major_radius=radius,
                minor_radius=0.008,
                major_segments=48,
                minor_segments=8,
                location=(-0.03, -0.08, 0.42 + i * 0.02),
                rotation=(0.42, 0.0, -0.28),
            )
            obj = bpy.context.object
            obj.name = f'{rid}_raised_wind_ring_{i}'
            obj.data.materials.append(detail_mat)
            G.link_to(collection, obj)
    if rid in {'aeolian-crystal', 'light_crystal', 'memory_shard', 'relic_fragment', 'star_glass'}:
        for i, (x, y, z) in enumerate(((-0.13, -0.11, 0.42), (0.12, 0.03, 0.58), (0.28, -0.05, 0.5))):
            G.cube(f'{rid}_facet_glint_{i}', collection, (x, y, z), (0.02, 0.014, 0.22), rune_mat, (0.12, -0.18, 0.34 + i * 0.18))
    if rid in {'wood', 'planks', 'premium_planks', 'elderwood-heart'}:
        for i, y in enumerate((-0.24, -0.04, 0.16, 0.34)):
            G.cube(f'{rid}_carved_growth_line_{i}', collection, (-0.04, y, 0.43 + i * 0.01), (0.5, 0.014, 0.012), G.MATS['wood_highlight'], (0, 0, -0.16))
    if rid in {'mechanism', 'mechanisms', 'super_mechanism', 'super-mechanisms', 'electronics'}:
        for i, angle in enumerate((0, math.tau / 3, math.tau * 2 / 3)):
            G.cylinder(f'{rid}_pinion_pin_{i}', collection, (0.18 * math.cos(angle), 0.18 * math.sin(angle), 0.52), 0.025, 0.08, G.MATS['copper'], vertices=16)
    if rid in {'fabric', 'rope', 'super-fiber', 'flax', 'reed'}:
        for i, x in enumerate((-0.18, 0.0, 0.18)):
            G.cube(f'{rid}_woven_thread_{i}', collection, (x, -0.18, 0.46 + i * 0.02), (0.035, 0.46, 0.018), G.MATS['fabric_light'], (0, 0, 0.16))
    if rid in {'stone_block', 'concrete', 'reinforced_concrete'}:
        for i, (x, y, z, rot) in enumerate(((-0.22, -0.22, 0.47, -0.08), (0.08, -0.23, 0.52, 0.13), (0.24, -0.18, 0.37, -0.22))):
            G.cube(f'{rid}_chiseled_face_line_{i}', collection, (x, y, z), (0.22, 0.018, 0.018), G.MATS['stone_light'], (0, 0, rot))
        for i, (x, y, z) in enumerate(((-0.28, 0.22, 0.53), (0.3, 0.16, 0.42), (0.02, 0.28, 0.55))):
            sphere(f'{rid}_aggregate_chip_{i}', collection, (x, y, z), (0.045, 0.035, 0.026), G.MATS['stone_dark'], 10)
    if rid == 'cement':
        for i, (x, y, z) in enumerate(((-0.18, -0.2, 0.39), (0.08, -0.23, 0.31), (0.22, -0.12, 0.44))):
            G.cube(f'cement_fold_shadow_{i}', collection, (x, y, z), (0.2, 0.018, 0.016), G.MATS['stone'], (0, 0, -0.2 + i * 0.16))
        for i, x in enumerate((-0.18, 0.0, 0.18)):
            sphere(f'cement_powder_lump_{i}', collection, (x, 0.24, 0.13), (0.06, 0.045, 0.025), G.MATS['cement'], 10)
    if rid == 'fuel':
        G.cube('fuel_embossed_label_frame', collection, (-0.02, -0.225, 0.36), (0.38, 0.018, 0.24), G.MATS['gold'], (0, 0, -0.08))
        for i, z in enumerate((0.3, 0.38, 0.46)):
            G.cube(f'fuel_label_line_{i}', collection, (-0.03, -0.242, z), (0.23 - i * 0.04, 0.014, 0.012), G.MATS['fuel_light'], (0, 0, -0.08))
    if rid == 'oil_plants':
        for i, (x, y, z) in enumerate(((-0.24, -0.16, 0.48), (0.16, 0.08, 0.58), (0.28, -0.18, 0.5))):
            sphere(f'oil_plant_gloss_seed_{i}', collection, (x, y, z), (0.055, 0.045, 0.045), G.MATS['oil'], 10)


def build_memory_shards(collection):
    for i, (x, y, h, tilt) in enumerate(((-.22, -.05, .58, -.22), (.04, .06, .78, .05), (.25, -.02, .5, .24))):
        shard(f'memory_shard_{i}', collection, (x, y, h / 2), h, G.MATS['rune'], (0, tilt, .1 * i), .09)
    G.cube('memory_tablet_piece', collection, (0, -.24, .14), (.54, .18, .07), G.MATS['stone_dark'], (0, 0, -.12))


def bake(collection):
    bpy.context.view_layer.update()
    for obj in list(collection.objects):
        bpy.context.view_layer.objects.active=obj
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.data.transform(obj.matrix_world)
        obj.matrix_world=Matrix.Identity(4)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free()
    points=[v.co.copy() for obj in collection.objects for v in obj.data.vertices]
    lo=Vector([min(v[i] for v in points) for i in range(3)])
    hi=Vector([max(v[i] for v in points) for i in range(3)])
    offset=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    transform=Matrix.Translation(-offset)
    for obj in collection.objects:
        obj.data.transform(transform)
    bpy.context.view_layer.update()


def camera(scene, collection):
    points=[obj.matrix_world@v.co for obj in collection.objects for v in obj.data.vertices]
    cam=scene.camera
    rotation=cam.rotation_euler.to_matrix()
    right,up=rotation@Vector((1,0,0)),rotation@Vector((0,1,0))
    xs=[v.dot(right) for v in points];ys=[v.dot(up) for v in points]
    center=right*((min(xs)+max(xs))/2)+up*((min(ys)+max(ys))/2)
    cam.location=center+rotation@Vector((0,0,6))
    cam.data.ortho_scale=max(max(xs)-min(xs),max(ys)-min(ys))/.82


def main(output=None):
    output=Path(output or ROOT/'frontend/public/assets/resources/icons')
    output.mkdir(parents=True,exist_ok=True)
    G.RESOURCES = resource_list(output)
    scene=bpy.data.scenes.new('Real_City_Resource_Models')
    bpy.context.window.scene=scene
    configure_geometry()
    G.setup_camera()
    scene.camera.rotation_euler=Vector((-5,7,-5.5)).to_track_quat('-Z','Y').to_euler()
    for obj in scene.objects:
        if obj.type=='LIGHT':
            obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.world=bpy.data.worlds.new('resource_daylight')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.8,1,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
    scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='AgX'
    report=[];collections=[]
    for resource in G.RESOURCES:
        collection=G.build_icon(resource)
        rid=resource['id']
        add_aeolian_detail_motifs(collection, rid)
        high_detail_mesh_pass(collection, rid)
        bake(collection)
        camera(scene,collection)
        for obj in scene.objects: obj.select_set(False)
        triangles=0
        for obj in collection.objects:
            obj.name='resource_'+resource['id']+'_'+obj.name
            obj.select_set(True)
            obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
        bpy.ops.export_scene.gltf(filepath=str(output/(rid+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True)
        scene.render.filepath=str(output/(rid+'.png'))
        bpy.ops.render.render(write_still=True)
        report.append({**resource,'file':rid+'.png','model':rid+'.glb','triangles':triangles,
                       'ortho_scale':scene.camera.data.ortho_scale,'camera_location':list(scene.camera.location)})
        for obj in collection.objects: obj.select_set(False)
        collection.hide_render=True;collection.hide_viewport=True
        collections.append(collection)
        (output/'manifest.json').write_text(json.dumps({'style':G.STYLE_DESCRIPTION,'size':256,'resources':report},ensure_ascii=False,indent=2))
        print('RESOURCE_DONE '+rid,flush=True)
    collections[0].hide_render=False;collections[0].hide_viewport=False
    camera(scene,collections[0])
    bpy.data.libraries.write(str(output/'resource_icons.blend'),{scene},fake_user=True)
    # Reimport every exported model in an empty scene, not the user's open scene.
    qa=bpy.data.scenes.new('Resource_Export_QA');bpy.context.window.scene=qa
    for entry in report:
        bpy.ops.import_scene.gltf(filepath=str(output/entry['model']))
        triangles=0
        for obj in qa.objects:
            if obj.type!='MESH': continue
            obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
            assert all(e.is_manifold for e in bm.edges),(entry['id'],obj.name,'nonmanifold')
            bm.free()
        assert triangles==entry['triangles'],entry['id']
        bpy.data.batch_remove(ids=list(qa.objects))
    (output/'roundtrip-validation.json').write_text(json.dumps({'models':len(report),'nonmanifold_edges':0,'triangles_matched':True},indent=2))
    print('RESOURCE_COMPLETE '+str(len(report)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.output)
