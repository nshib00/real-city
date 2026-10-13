"""Blender MCP entry points: prepare(), level(1..10), finish()."""
import importlib.util
import json
import math
from pathlib import Path

import bmesh
import bpy

from real_city.migration import LegacyAssetMigration, finalize_legacy_asset_generation

spec=importlib.util.spec_from_file_location('civic_states',Path(__file__).with_name('revise_building_states.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
H=S.H
BOX=H.box


def efficient_box(name,pos,size,role,bevel=.02,rotation=(0,0,0)):
    if H.COL.get('late_model',False) and ('wall' in name or name=='window_frame'):
        bevel=0
    return BOX(name,pos,size,role,bevel,rotation)


def prism(name,points,role,thickness=.04):
    count=len(points)
    verts=points+[(x,y,z-thickness) for x,y,z in points]
    faces=[tuple(range(count)),tuple(range(count*2-1,count-1,-1))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    obj=H.mesh(name,verts,faces,role)
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    return obj


def hip_roof(cx,cy,width,depth,z,rise,leaves=False):
    corners=[(-width/2,-depth/2),(width/2,-depth/2),(width/2,depth/2),(-width/2,depth/2)]
    for side in range(4):
        left,right=corners[side],corners[(side+1)%4]
        for row in range(3):
            a,b=row/3,(row+1)/3
            def point(v,t): return (cx+v[0]*t,cy+v[1]*t,z+rise*(1-t))
            points=[(cx,cy,z+rise),point(left,b),point(right,b)] if row==0 else [point(left,a),point(left,b),point(right,b),point(right,a)]
            prism('hip_roof_shingle',points,'windleaf' if leaves else 'roof')
        H.beam('eave_trim',(cx+left[0],cy+left[1],z),(cx+right[0],cy+right[1],z),.075,'accent')
        H.beam('ridge_cap',(cx,cy,z+rise+.035),(cx+left[0],cy+left[1],z+.035),.055,'wood')
    if leaves:
        for side in (0,1):
            for t in (.40,.65,.88):
                for c in (-1,0,1):
                    x=c*width*.19*t;y=-depth*.5*t
                    def point(dx,dy):
                        px,py=x+dx,y+dy
                        pz=z+rise*(1-abs(py)/(depth/2))+.045
                        return (cx+px,cy+py,pz) if side==0 else (cx-py,cy+px,pz)
                    prism('roof_shingle_windleaf',[point(-.12,0),point(0,-.17),point(.12,0),point(0,.17)],'leaf_light',.018)


def walls(cx,cy,width,depth,bottom,height,role,name='wall_siding',courses=6):
    for i in range(courses):
        z=bottom+(i+.5)*height/courses
        for y in (cy-depth/2,cy+depth/2):
            count=3 if role in ('stone','brick') else 1
            for j in range(count):
                x=cx-width/2+(j+.5)*width/count
                H.box(name,(x,y,z),(width/count-.012,.11,height/courses-.012),role,.016 if y<cy else 0)
        for x in (cx-width/2,cx+width/2):
            count=3 if role in ('stone','brick') else 1
            for j in range(count):
                y=cy-depth/2+(j+.5)*depth/count
                H.box(name,(x,y,z),(.11,depth/count-.012,height/courses-.012),role,.016 if x>cx else 0)
    for x in (cx-width/2,cx+width/2):
        for y in (cy-depth/2,cy+depth/2):
            H.box('corner_reinforcement',(x,y,bottom+height/2),(.14,.14,height+.06),'beam' if role=='wood' else 'stone',.025)


def side_tower(x,level):
    top=1.70+(level-7)*.10
    walls(x,.17,.48,.64,.18,top-.18,'stone','side_tower_wall',5)
    hip_roof(x,.17,.65,.81,top,.40)
    H.window(x,-.20,top-.34,.19,.29)


def building(level):
    H.COL['late_model']=level>=7
    H.base()
    width=1.00+min(level,6)*.035
    depth=1.02+min(level,6)*.025
    eaves=(1.23,1.43,1.57,1.96,2.13,2.28,2.43,2.58,2.72,2.88)[level-1]
    rise=.42+level*.016
    H.COL['building_dimensions']=[width,depth,eaves,rise]
    H.COL['tower_top']=eaves+rise
    H.COL['tower_width']=width*.78
    H.box('foundation',(0,0,.10),(width+.22,depth+.22,.20),'earth' if level==1 else 'stone',.035)
    if level<=2:
        for row in range(7 if level==1 else 8):
            z=.22+row*(eaves-.24)/(6 if level==1 else 7)
            for y in (-depth/2,depth/2):
                H.log('wall_log',(-width/2-.06,y,z),(width/2+.06,y,z),.075)
            for x in (-width/2,width/2):
                H.log('wall_log',(x,-depth/2-.07,z),(x,depth/2+.07,z),.075)
    else:
        role='wood' if level<7 else ('brick' if level>=9 else 'stone')
        walls(0,0,width,depth,.2,eaves-.2,role,courses=7 if level<7 else 9)
        H.box('floor_crossbeam',(0,-depth/2-.06,1.35),(width+.18,.15,.12),'wood',.015)
    hip_roof(0,0,width+.32,depth+.32,eaves,rise,level<=3)
    H.door(-depth/2-.10,1.01)
    for i in range(3):
        H.box('entry_step',(0,-depth/2-.30-i*.16,.16-i*.04),(.85+i*.12,.25,.10),'wood' if level<5 else 'stone',.02)
    H.canopy(-depth/2-.32,1.06,.88)
    if level>=3:
        # Retain inherited leaf roofing on a lower administrative wing.
        walls(-.99,.12,.62,.97,.18,.76,'wood',name='annex_wall',courses=5)
        old=H.MATS['roof'];H.MATS['roof']=H.MATS['windleaf']
        H.roof(.81,1.14,.98,.23,cx=-.99,cy=.12,rows=2,cols=3)
        H.MATS['roof']=old
        H.window(-.99,-.43,.64,.22,.29)
        for x in (-.43,.43):
            for course in range(2):
                H.box('brick_reinforcement',(x,-depth/2-.07,.25+course*.16),(.23,.15,.15),'brick',.012)
    if level>=4:
        H.window(.05,-depth/2-.08,1.64,.32,.38)
        for x in (-.39,.39):
            H.box('mycelium_wall_infill',(x,-depth/2-.065,1.60),(.19,.08,.34),'mycelium',.022)
        H.box('bench_seat',(-.85,-1.22,.24),(.66,.25,.10),'wood',.02)
        for x in (-1.1,-.6): H.box('bench_leg',(x,-1.22,.12),(.09,.18,.24),'wood',.01)
    if level>=5:
        walls(.99,.15,.64,1.03,.18,1.0,'wood' if level<7 else 'stone',name='annex_wall',courses=5)
        H.roof(.84,1.19,1.21,.27,cx=.99,cy=.15,rows=2,cols=3)
        H.window(1.37,.13,.77,.28,.35,side=True)
        H.window(.99,-.44,.74,.23,.30)
    if level>=6:
        for x in (-1.00,0,1.0):
            H.box('stone_foundation_course',(x,-.54,.19),(.70,.22,.25),'stone',.035)
        H.window(width/2+.08,.1,1.71,.34,.40,side=True)
        H.chimney(-.96,.32,1.15,.61)
    if level>=7:
        side_tower(-1.03,level)
        for x in (-width/2,width/2):
            for row in range(5):
                H.box('stone_block_reinforcement',(x,-depth/2-.05,.34+row*.23),(.23,.24,.21),'stone',.02)
        for x in (-.9,-.45,0,.45,.9):
            H.box('plaza_paving',(x,-1.39,.025),(.41,.37,.05),'stone',.018)
    if level>=8:
        z=eaves-.32
        H.box('clock_frame',(0,-depth/2-.10,z),(.57,.15,.57),'wood',.075)
        bm=bmesh.new()
        bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=24,radius1=.25,radius2=.25,depth=.04)
        data=bpy.data.meshes.new(H.PREFIX+'_clock_face');bm.to_mesh(data);bm.free()
        clock=bpy.data.objects.new(data.name,data);H.COL.objects.link(clock)
        clock.location=(0,-depth/2-.19,z);clock.rotation_euler.x=math.pi/2
        data.materials.append(H.MATS['mycelium'])
        H.beam('clock_hand',(0,-depth/2-.225,z),(0,-depth/2-.225,z+.16),.032,'beam')
        H.beam('clock_hand',(0,-depth/2-.23,z),(.14,-depth/2-.23,z-.05),.032,'beam')
    if level>=9:
        side_tower(1.03,level)
        for x in (-.38,.38): H.window(x,-depth/2-.09,1.55,.22,.39)
    if level==10:
        H.box('premium_balcony_floor',(0,-depth/2-.29,1.29),(1.29,.55,.12),'premium',.03)
        for x in (-.57,-.28,0,.28,.57):
            H.box('balcony_post',(x,-depth/2-.54,1.51),(.06,.06,.39),'premium',.01)
        H.box('balcony_rail',(0,-depth/2-.54,1.72),(1.29,.08,.08),'premium',.016)
        for x in (-.42,.42):
            H.beam('super_mycelium_bracket',(x,-depth/2-.14,1.04),(x,-depth/2-.43,1.23),.12,'super_mycelium')
    flag_z=eaves+rise+.34
    H.beam('flag_pole',(0,0,eaves+rise),(0,0,flag_z+.16),.04,'wood')
    H.box('main_flag',(.17,0,flag_z),(.35,.035,.22),'accent',.025,rotation=(0,.07,0))
    if level>=2:
        H.box('notice_board',(.98,-1.11,.55),(.43,.09,.32),'wood',.02)
        H.box('notice_paper',(.98,-1.17,.56),(.30,.035,.20),'mycelium',.012)
        H.box('notice_post',(.98,-1.11,.28),(.08,.08,.50),'wood',.015)
    else:
        for i in range(2): H.box('blueprint_crate',(.79,-.85+i*.36,.17),(.30,.29,.30),'wood',.035)
    H.clean_meshes(H.COL)


def prepare():
    for c in list(bpy.data.collections):
        if c.name.startswith('town_hall_l'): c.name='previous_'+c.name
    scene=bpy.data.scenes.new('Real_City_Town_Halls');bpy.context.window.scene=scene
    H.palette()
    H.box=efficient_box
    for role,color in {'brick':(.56,.19,.10),'mycelium':(.73,.67,.43),
                       'premium':(.35,.17,.065),'super_mycelium':(.70,.35,.10)}.items(): H.material(role,color)
    H.setup_camera(scene)
    folder=S.ROOT/'frontend/src/assets/buildings/center/town_hall'
    folder.mkdir(parents=True,exist_ok=True)
    (S.ROOT/'frontend/public/assets/buildings/center/town_hall').mkdir(parents=True,exist_ok=True)
    S.STATE={'kind':'town_hall','count':10,'folder':'center/town_hall','model_dir':folder,'active':{},'report':{}}
    print('Town hall scene prepared')


def level(n):
    assert 1<=n<=10
    scene=bpy.context.scene
    for state in ('active','construction','damaged'):
        existing=bpy.data.collections.get(f'town_hall_l{n:02d}_{state}')
        if existing:
            for obj in list(existing.all_objects): S.remove(obj)
            for child in list(existing.children): bpy.data.collections.remove(child)
            bpy.data.collections.remove(existing)
    name=f'town_hall_l{n:02d}_active'
    active=bpy.data.collections.new(name);scene.collection.children.link(active)
    S.STATE['active'][n]=active;H.COL=active;H.PREFIX=name
    building(n)
    S.export(active,name)
    for state in ('construction','damaged'):
        name=f'town_hall_l{n:02d}_{state}'
        collection=S.clone_active(active,name,scene)
        for key in ('building_dimensions','tower_top','tower_width'): collection[key]=active[key]
        S.STATE['report'][name]=S.revise(collection,'town_hall',n,state)
        for obj in list(collection.all_objects):
            if 'clock_' in obj.name:
                S.remove(obj)
            elif 'roof_shingle_windleaf' in obj.name:
                S.clipped(obj,(-.13,0,0),(1,-.28,0),jagged=state=='damaged')
        S.export(collection,name)
    (S.STATE['model_dir']/'state-revision-report.json').write_text(json.dumps(S.STATE['report'],indent=2))
    print('Exported town hall level',n)


def finish():
    S.finish()
    previous=S.ROOT/'frontend/public/assets/buildings/state-roundtrip-validation.json'
    S.ROUNDTRIP=[e for e in json.loads(previous.read_text()) if not e['name'].startswith('town_hall_')] if previous.exists() else []
    S.validate_roundtrip('town_hall')
    result=[e for e in S.ROUNDTRIP if e['name'].startswith('town_hall_')]
    out_dir=S.ROOT/'frontend/public/assets/buildings/center/town_hall'
    (out_dir/'roundtrip-validation.json').write_text(json.dumps(result,indent=2))
    finalize_legacy_asset_generation(
        LegacyAssetMigration(
            asset_id='town_hall',
            display_name='Ратуша',
            category='center',
            output_dir=out_dir,
            levels=range(1,11),
            states=('active','construction','damaged'),
            source_blend=out_dir/'town_hall_levels.blend',
            combined_glb=out_dir/'town_hall_levels.glb',
            generator='tools/assets/blender/regenerate_town_halls.py',
            style_reference='Real City 2x2 civic chain, migrated without changing silhouette',
        )
    )


if __name__=='__main__':
    prepare()
    for n in range(1,11): level(n)
    finish()
