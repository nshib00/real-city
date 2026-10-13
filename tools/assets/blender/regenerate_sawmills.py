"""Rebuild all sawmills using the early-housing geometry, palette and camera."""
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation

spec=importlib.util.spec_from_file_location('sawmill_states',Path(__file__).with_name('revise_building_states.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
H=S.H
ROOT=Path(__file__).resolve().parents[3]
STATES=('active','construction','damaged')


def cylinder(name,center,radius,depth,role,axis=(0,0,1),segments=16):
    bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=segments,
                         radius1=radius,radius2=radius,depth=depth)
    mesh=bpy.data.meshes.new(H.PREFIX+'_'+name);bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(mesh.name,mesh);H.COL.objects.link(obj)
    mesh.materials.append(H.MATS[role]);obj.location=center
    obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return obj


def gear(name,x,y,z,radius,role='metal',tilt=0):
    n=48
    outline=[(radius*(1 if i%2 else .87)*math.cos(i*math.tau/n),
              radius*(1 if i%2 else .87)*math.sin(i*math.tau/n)) for i in range(n)]
    verts=[(x+px,y+thickness,z+pz) for thickness in (-.028,.028) for px,pz in outline]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=H.mesh(name,verts,faces,role)
    if tilt:
        from mathutils import Matrix
        pivot=Vector((x,y,z))
        obj.data.transform(Matrix.Translation(pivot)@Matrix.Rotation(tilt,4,'X')@Matrix.Translation(-pivot))
    return obj


def roof(width,depth,z,rise,cx,cy,state,level,label='main'):
    before=set(H.COL.objects)
    H.roof(width,depth,z,rise,cx=cx,cy=cy,rows=3,cols=6)
    bpy.context.view_layer.update()
    for obj in set(H.COL.objects)-before:
        name=obj.name
        alive=True
        # Bake positions before clipping so all state changes share housing coordinates.
        obj.data.transform(obj.matrix_world);obj.matrix_world.identity()
        if 'roof_shingle' in name:
            if level==1:
                obj.data.materials.clear();obj.data.materials.append(H.MATS['wood'])
            elif level>=11 and sum(v.co.y for v in obj.data.vertices)/len(obj.data.vertices)>cy+depth*.20:
                obj.data.materials.clear();obj.data.materials.append(H.MATS['rune_roof'])
            if state=='construction':
                alive=S.clipped(obj,(cx-width*.12,0,0),(1,0,0))
            elif state=='damaged':
                alive=S.clipped(obj,(cx-width*.12,cy,0),(1,-.45,0),jagged=True)
        elif state!='active':
            alive=S.clipped(obj,(cx+width*(.08 if state=='construction' else -.06),cy,0),
                      (1,0 if state=='construction' else -.45,0),jagged=state=='damaged')
        if alive:
            obj['assembly']=label+'_roof'
    for yy in (cy-depth*.4,cy,cy+depth*.4):
        for sign in (-1,1):
            if state=='damaged' and sign>0 and yy<cy+.1: continue
            H.beam('roof_rafter',(cx+sign*width*.45,yy,z-.05),(cx,yy,z+rise-.05),.065,'beam')


def barrel(x,y,fuel=True):
    cylinder('fuel_barrel' if fuel else 'water_barrel',(x,y,.28),.16,.40,'fuel' if fuel else 'accent')
    for z in (.13,.41):
        cylinder('barrel_band',(x,y,z),.168,.047,'metal')
    cylinder('barrel_bung',(x+.055,y,.492),.038,.025,'beam',segments=10)


def stock(level,state):
    for i in range(3+min(level//3,3)):
        row=i//3;yy=-1.23+(i%3)*.25
        H.log('raw_log',(-1.42,yy,.23+row*.19),(-.62,yy,.23+row*.19),.12)
    rows=2+min(level//3,3)
    for i in range(rows):
        for j in range(3):
            H.box('finished_planks',(.91+(j-1)*.16,-.93,.15+i*.075),(.145,.69,.062),
                  'premium' if level>=8 and i==rows-1 else 'wood',.012,
                  rotation=(0,0,.07 if state=='damaged' and i%2 else 0))
    for x in (.64,1.18):
        H.box('stack_foot',(x,-.93,.10),(.15,.84,.10),'beam')
    if level>=3:
        H.box('quality_tag',(1.15,-1.28,.23),(.12,.035,.14),'accent',.007)


def machinery(level,state,cx,cy):
    broken=state=='damaged';building=state=='construction'
    table_z=.60
    for x in (cx-.48,cx+.48):
        for y in (cy-.25,cy+.28):
            top=.36 if broken and x>cx else table_z
            H.beam('saw_table_leg',(x,y,.14),(x,y,top),.11,'beam')
    for j in range(4 if not broken else 2):
        H.box('saw_table_board',(cx,cy-.24+j*.16,table_z),(1.18,.15,.10),'wood')
    if level<3:
        H.log('workpiece_log',(cx-.64,cy+.02,.78),(cx+.54,cy+.02,.78),.12)
        if not building:
            H.box('handsaw_blade',(cx,cy-.35,.80 if not broken else .22),(.78,.035,.09),'metal',.005,rotation=(0,.14,0))
            for i in range(7):
                H.box('handsaw_tooth',(cx-.3+i*.1,cy-.35,.75 if not broken else .17),(.055,.034,.055),'metal',.004,rotation=(0,math.pi/4,0))
            H.box('handsaw_handle',(cx+.44,cy-.35,.82 if not broken else .24),(.16,.065,.13),'beam')
    else:
        for x in (cx-.4,cx+.4):
            H.beam('saw_frame_post',(x,cy-.37,.4),(x,cy-.37,.95 if broken else 1.18),.09,'metal' if level>=6 else 'beam')
        if not broken:
            H.beam('saw_frame_cross',(cx-.42,cy-.37,1.18),(cx+.42,cy-.37,1.18),.09,'metal' if level>=6 else 'beam')
        if not building:
            gear('saw_blade',cx,cy-.42,.83 if not broken else .45,.31,'metal',.5 if broken else 0)
            cylinder('blade_axle',(cx,cy-.46,.83 if not broken else .45),.074,.12,'copper',axis=(0,1,0))
        H.log('saw_log_input',(cx-.50,cy+.08,.8),(cx+.68,cy+.08,.8),.115)
    if level>=4:
        H.box('motor_plinth',(cx+.66,cy+.22,.18),(.4,.54,.22),'brick')
        if not building:
            H.box('motor_housing',(cx+.66,cy+.22,.41),(.39,.37,.28),'accent',.06)
            cylinder('motor_flywheel',(cx+.66,cy-.01,.44),.20,.09,'copper',axis=(0,1,0))
            if not broken:
                H.beam('drive_belt',(cx+.64,cy-.07,.46),(cx+.04,cy-.40,.71),.045,'char')
    if level>=7:
        for i in range(4+int(level>=10)*2):
            x=cx-.45+i*.19
            if broken and i>2: continue
            cylinder('feed_roller',(x,cy+.1,.78),.065,.50,'metal',axis=(0,1,0),segments=12)
        for yy in (cy-.14,cy+.36):
            H.beam('feed_rail',(cx-.60,yy,.70),(cx+.85,yy,.70),.07,'metal')
    if level>=12 and state=='active':
        gear('calibration_gear',cx+.63,cy-.055,.46,.13,'gold')
        cylinder('precision_core',(cx+.64,cy+.19,.60),.07,.14,'rune_roof')


def building(level,state,active=None):
    collection=bpy.data.collections.new(f'lumber_yard_l{level:02d}_{state}')
    bpy.context.scene.collection.children.link(collection)
    H.COL=collection;H.PREFIX=collection.name
    if active is None:
        H.base()
        H.box('work_yard',(0,.15,.075),(2.95,2.55,.025),'yard',.03)
        for obj in collection.objects: obj['ground']=True
    else:
        for original in active.objects:
            if original.get('ground'):
                obj=original.copy();obj.data=original.data.copy()
                obj.name=original.name.replace('_active','_'+state);collection.objects.link(obj)
    cx=-.22;cy=.18
    width=1.38+min(level,7)*.105
    depth=1.13+min(level,6)*.065
    height=1.04+min(level,8)*.06
    rise=.42+min(level,7)*.025
    construction=state=='construction';damaged=state=='damaged'
    collection['level']=level;collection['state']=state
    collection['ground_source']=f'lumber_yard_l{level:02d}_active'
    collection['construction_progress']=.52 if construction else 1
    support='metal' if level>=8 else 'beam'
    base_role='concrete' if level>=8 else 'stone' if level>=3 else 'beam'
    H.box('foundation',(cx,cy,.13),(width+.13,depth+.15,.15),base_role,.035)
    if level>=2:
        for i in range(7 if not construction else 4):
            H.box('deck_board',(cx-width*.43+i*width*.14,cy,.24),(width*.13,depth,.065),'wood',.008)
    for ix,x in enumerate((cx-width/2,cx+width/2)):
        for iy,y in enumerate((cy-depth/2,cy+depth/2)):
            top=height
            if damaged and ix==1: top=.43 if iy==0 else height*.69
            if construction and ix==1 and iy==0: top=height*.68
            H.box('post_stone_foot',(x,y,.23),(.23,.23,.20),base_role,.03)
            H.beam('frame_post',(x,y,.25),(x,y,top),.135,support)
            if level>=4:
                for z in (.33,.49):
                    H.box('brick_pier',(x,y,z),(.25,.24,.14),'brick',.016)
            if not damaged or ix==0:
                H.beam('knee_brace',(x,y,height-.36),(x+(.27 if ix==0 else -.27),y,height-.04),.08,'wood')
    for y in (cy-depth/2,cy+depth/2):
        if damaged:
            H.beam('broken_crossbeam',(cx-width/2,y,height),(cx-.12,y,height-.10),.14,'beam')
        elif not construction or y>cy:
            H.beam('crossbeam',(cx-width/2-.06,y,height),(cx+width/2+.06,y,height),.13,'wood')
    # Partial rear and side cladding leave the saw and its working aisle visible.
    if level>=2:
        for row in range(5 if not construction else 2):
            z=.32+row*.145
            H.box('rear_wall_board',(cx,cy+depth/2,z),(width,.075,.135),'wood',.014)
            if not damaged:
                H.box('side_wall_board',(cx-width/2,cy+depth*.15,z),(.075,depth*.68,.135),'wood',.014)
    roof(width+.32,depth+.30,height+.03,rise,cx,cy,state,level)
    machinery(level,state,cx,cy-.18)
    stock(level,state)
    if level>=4:
        barrel(1.38,.63)
        if level>=6: barrel(1.38,1.07)
    if level>=5:
        for x in (.98,1.56):
            H.beam('drying_rack_post',(x,.16,.12),(x,.16,1.18 if not damaged else .59),.085,'beam')
        for row in range(3 if state=='active' else 1):
            H.box('drying_rack_shelf',(1.27,.16,.35+row*.27),(.72,.37,.065),'premium' if level>=8 else 'wood')
            for j in range(3):
                H.box('drying_board',(1.27,-.01+j*.12,.41+row*.27),(.69,.09,.055),'wood',.01)
        if level>=5 and state=='active':
            H.beam('copper_cooling_pipe',(.68,.26,.36),(.68,.26,.88),.052,'copper')
    if level>=8:
        x=-1.58;y=-.77
        H.beam('hoist_mast',(x,y,.12),(x,y,1.96 if not damaged else .73),.12,'metal')
        if state=='active':
            H.beam('hoist_arm',(x-.05,y,1.91),(x+.83,y,1.91),.11,'metal')
            H.beam('hoist_brace',(x,y,1.46),(x+.56,y,1.91),.07,'copper')
            H.beam('hoist_chain',(x+.69,y,1.86),(x+.69,y,.96),.026,'metal')
            H.beam('hoist_hook',(x+.69,y,.96),(x+.57,y,.86),.045,'metal')
    if level>=9:
        bx=-.78;by=.71
        for row in range(6 if state=='active' else 3 if construction else 2):
            H.box('cabin_wall',(bx,by,.97+row*.14),(.74,.61,.13),'premium' if level>=12 else 'wood',.018)
        roof(.91,.80,1.86,.28,bx,by,state,level,'cabin')
        if state=='active': H.window(bx,by-.32,1.54,.27,.29)
        height_pipe=2.12+max(0,level-10)*.06
        pipe_top=1.08 if damaged else 1.43 if construction else height_pipe
        cylinder('extraction_pipe',(.59,.72,(.73+pipe_top)/2),.085,pipe_top-.73,'metal')
        if state=='active':
            H.box('extraction_hood',(.59,.72,height_pipe),(.32,.3,.08),'copper')
    if level>=10:
        for row in range(2 if not construction else 1):
            for i in range(3):
                H.box('sorting_planks',(-.7+i*.28,1.42,.17+row*.08),(.25,.32,.07),'premium',.012)
    if level>=11 and state=='active':
        for i in range(3):
            H.box('rune_roof_inlay',(cx-.26+i*.26,cy-depth/2-.18,height+.21+i%2*.09),(.14,.055,.045),'gold' if level>=12 else 'copper',.008)
    if level>=13:
        for x in (.8,1.56):
            H.beam('premium_guard_post',(x,.09,.1),(x,.09,1.38 if state=='active' else .73),.08,'premium')
        roof(.86,.53,1.4,.20,1.15,.10,state,level,'premium')
    if construction:
        for x in (-1.5,1.38):
            for y in (-.95,.42):
                H.beam('scaffold_post',(x,y,.1),(x,y,height+.20),.07,'wood')
            for z in (.7,height+.1):
                H.beam('scaffold_rail',(x,-.99,z),(x,.47,z),.065,'wood')
            H.beam('scaffold_brace',(x,-.9,.2),(x,.38,height),.065,'beam')
        for i in range(4):
            H.box('uninstalled_board',(-.4+i*.18,-1.13,.13),( .16,.75,.055),'wood',.012,rotation=(0,0,-.15))
    if damaged:
        for i in range(11):
            x=-.83+(i%5)*.38;y=-1.06-(i//5)*.16
            H.box('fallen_roof_plank',(x,y,.12+(i%2)*.045),(.40,.105,.065),
                  'char' if i%3==0 else 'wood',.012,rotation=(.1,.12,-.8+i*.24))
        H.beam('collapsed_support',(.44,-.88,.16),(.84,-.38,.56),.14,'char')
        for i in range(3):
            H.box('masonry_rubble',(.4+i*.18,-.82,.15),(.15,.17,.16),'brick' if level>=4 else 'stone',.035,rotation=(0,.2,.3*i))
    H.clean_meshes(collection)
    for obj in collection.objects:
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    return collection


def main(output=None,levels=range(1,14)):
    directory=Path(output or ROOT/'frontend/public/assets/buildings/industry/lumber_yard')
    directory.mkdir(parents=True,exist_ok=True)
    scene=bpy.data.scenes.new('Real_City_Sawmills_Housing_Style');bpy.context.window.scene=scene
    H.palette()
    # Match terrain/grass exactly so building bases do not drift from map tiles.
    grass=H.MATS['grass']
    grass.diffuse_color=(.26,.48,.08,1)
    shader=grass.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.26,.48,.08,1)
    for role,color in {'metal':(.30,.36,.37),'copper':(.55,.25,.075),'brick':(.47,.14,.075),
                       'concrete':(.41,.43,.38),'yard':(.34,.25,.12),'fuel':(.48,.15,.055),
                       'premium':(.76,.49,.19),'gold':(.76,.48,.08),'rune_roof':(.26,.14,.37)}.items():
        H.material(role,color)
    for role in ('metal','copper','gold'):
        bsdf=H.MATS[role].node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Metallic'].default_value=.45;bsdf.inputs['Roughness'].default_value=.43
    H.setup_camera(scene)
    scene['style_reference']='regenerate_early_housing.py: palette, base, roof, camera'
    report={};active={};collections=[]
    for level in levels:
        for state in STATES:
            collection=building(level,state,active.get(level))
            if state=='active': active[level]=collection
            for other in collections:
                other.hide_render=True;other.hide_viewport=True
            bpy.context.view_layer.update()
            for obj in scene.objects: obj.select_set(False)
            for obj in collection.objects: obj.select_set(True)
            path=directory/(collection.name+'.glb')
            bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True)
            scene.render.filepath=str(directory/(collection.name+'.png'));bpy.ops.render.render(write_still=True)
            triangles=0
            for obj in collection.objects:
                obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
                obj.select_set(False)
            report[collection.name]={'level':level,'state':state,'triangles':triangles,
                                     'bounds':[list(v) for v in S.bounds(collection.objects)],
                                     'ground_source':collection['ground_source']}
            collections.append(collection)
            (directory/'generation-report.json').write_text(json.dumps(report,indent=2))
            print('SAWMILL_DONE '+collection.name,flush=True)
    S.STATE={'kind':'lumber_yard','model_dir':directory,'active':active,'report':report}
    S.finish()
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id='lumber_yard',
            display_name='Лесопилка',
            category='industry',
            output_dir=directory,
            levels=levels,
            states=STATES,
            source_blend=directory/'lumber_yard_levels.blend',
            combined_glb=directory/'lumber_yard_levels.glb',
            generator='tools/assets/blender/regenerate_sawmills.py',
            style_reference='Real City industry sawmill/lumber yard migrated to shared report contract',
        )
    )
    qa=bpy.data.scenes.new('Sawmill_Roundtrip_QA');bpy.context.window.scene=qa
    for name,entry in report.items():
        bpy.ops.import_scene.gltf(filepath=str(directory/(name+'.glb')))
        count=0
        for obj in qa.objects:
            if obj.type!='MESH':continue
            obj.data.calc_loop_triangles();count+=len(obj.data.loop_triangles)
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
            assert all(edge.is_manifold for edge in bm.edges),(name,obj.name)
            bm.free()
        assert count==entry['triangles'],name
        bpy.data.batch_remove(ids=list(qa.objects))
    (directory/'roundtrip-validation.json').write_text(json.dumps({'models':len(report),'nonmanifold_edges':0,'triangles_matched':True},indent=2))
    print('SAWMILL_COMPLETE '+str(len(report)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.output,(1,6,13) if args.preview else range(1,14))
