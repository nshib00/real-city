"""Blender MCP: prepare(), export_tile(name), finish(), validate_roundtrip()."""
import importlib.util
import json
import math
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT_DIR=ROOT/'frontend/public/assets/terrain/tiles'
TERRAIN=('grass','forest','forest_thinned','forest_sparse','water','mountain','road','oil_well','ruins')
spec=importlib.util.spec_from_file_location('terrain_geometry',Path(__file__).with_name('regenerate_early_housing.py'))
H=importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
COLLECTIONS={}
REPORT={}
SCENE=None


def palette():
    colors={'grass':(.26,.48,.08),'grass_light':(.37,.59,.13),'leaf':(.07,.29,.035),
            'leaf_light':(.19,.43,.05),'wood':(.46,.23,.075),'cut':(.72,.49,.23),
            'earth':(.30,.20,.105),'stone':(.38,.43,.43),'stone_light':(.58,.63,.59),
            'snow':(.85,.90,.82),'water':(.045,.39,.57),'foam':(.36,.78,.83),
            'oil':(.012,.018,.023),'iron':(.15,.20,.21),'copper':(.60,.23,.08),
            'ruin':(.58,.56,.40),'amber':(.95,.38,.045)}
    for role,color in colors.items():
        H.material(role,color)
        mat=H.MATS[role];mat.name='MAT_terrain_'+role
        shader=mat.node_tree.nodes.get('Principled BSDF')
        if role in ('iron','copper'):
            shader.inputs['Metallic'].default_value=.65
            shader.inputs['Roughness'].default_value=.42
        if role in ('water','oil'):
            shader.inputs['Roughness'].default_value=.24


def mesh_from_bmesh(bm,name,pos,role):
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    data=bpy.data.meshes.new(H.PREFIX+'_'+name);bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new(data.name,data);H.COL.objects.link(obj)
    obj.location=pos;data.materials.append(H.MATS[role])
    return obj


def rock(name,pos,size,role='stone',seed=0):
    bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=1)
    for v in bm.verts:
        f=1+.075*math.sin(v.co.x*13+v.co.y*9+v.co.z*11+seed)
        v.co=Vector((v.co.x*size[0]*f,v.co.y*size[1]*f,v.co.z*size[2]*f))
    return mesh_from_bmesh(bm,name,pos,role)


def cylinder(name,pos,radius,height,role):
    bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=14,
                        radius1=radius,radius2=radius,depth=height)
    return mesh_from_bmesh(bm,name,pos,role)


def base(role='grass'):
    H.box('tile_surface',(0,0,-.015),(3.6,3.6,.03),role,0)


def tuft(x,y,scale=1):
    for i in range(3):
        H.beam('grass_tuft',(x+(i-1)*.045,y,.008),
               (x+(i-1)*.085,y+.035,.13*scale+(i%2)*.04),.028,'grass_light')


def meadow():
    base()
    for x,y in ((-1.1,.7),(.9,1.15),(1.15,-.85),(-.9,-1.15)):
        tuft(x,y)
    for i in range(3):
        rock('meadow_pebble',(-1.2+i*.14,.1,.035),(.06,.07,.045),'stone_light',i)


def tree(x,y,s,index):
    H.beam('tree_trunk',(x,y,0),(x+.05*s,y,1.15*s),.15*s,'wood')
    for dx,dy,z in ((-.28,.10,.9),(.29,.08,1.02),(0,-.24,1.2)):
        H.beam('tree_branch',(x,y,.65*s),(x+dx*s,y+dy*s,z*s),.07*s,'wood')
    for j,(dx,dy,z,r) in enumerate(((-.26,.05,1.19,.49),(.26,.08,1.32,.47),(0,-.21,1.43,.50),(0,.04,1.74,.42))):
        rock('tree_canopy',(x+dx*s,y+dy*s,z*s),(r*s,r*.86*s,r*.86*s),
             'leaf_light' if (j+index)%3 else 'leaf',index+j)


def forest(density):
    base()
    positions=((-0.85,.85,.85),(.35,.90,.91),(-.85,-.45,.87),(.65,-.48,.94),(0,.12,1.06))
    survivors={3:{0,1,2,3,4},2:{0,3,4},1:{4}}[density]
    for i,(x,y,s) in enumerate(positions):
        if i in survivors:
            tree(x,y,s,i)
        else:
            cylinder('cut_stump',(x,y,.12),.16,.24,'wood')
            cylinder('stump_cut',(x,y,.245),.135,.02,'cut')
            for j in range(3):
                H.box('wood_chip',(x+.23+j*.05,y-.13,.018),(.08,.035,.025),'cut',.005,rotation=(0,0,j*.6))
        tuft(x+.25,y-.28)


def water():
    base('water')
    # Water reaches all four edges; banks need an adjacency-aware future kit.
    for x,y in ((-.9,-.9),(.5,.8),(-.45,.15),(.8,-.5)):
        for j in range(3):
            H.beam('flow_ripple',(x+j*.16,y+.04*math.sin(j),.009),
                   (x+(j+1)*.16,y+.04*math.sin(j+1),.009),.014,'foam')


def mountain():
    base()
    for i,(x,y,z,sx,sy,sz) in enumerate(((-.45,.15,.71,.78,.82,1.10),(.65,.3,.46,.68,.72,.75),(-.55,-.68,.24,.68,.48,.42))):
        rock('rock_mass',(x,y,z),(sx,sy,sz),'stone',i)
    for i in range(7):
        rock('talus',(-1.03+i*.30,-.98,.10),(.17,.14,.15),'stone_light',i)
    rock('pale_summit',(-.45,.15,1.55),(.27,.30,.28),'snow')
    for x,y in ((1.2,-.8),(-1.3,.8)): tuft(x,y)


def road():
    base()
    H.box('road_lane_x',(0,0,.008),(3.6,.94,.016),'earth',0)
    H.box('road_lane_y',(0,0,.009),(.94,3.6,.018),'earth',0)
    for axis in range(2):
        for side in (-1,1):
            for step in (-1.42,-1.06,-.70,.70,1.06,1.42):
                x,y=(step,side*.48) if axis==0 else (side*.48,step)
                H.box('road_edging',(x,y,.045),(.27,.12,.08) if axis==0 else (.12,.27,.08),'stone',.025)


def oil_well():
    base()
    H.box('service_pad',(0,0,.05),(2.55,2.45,.1),'stone',.035)
    rock('oil_seep',(.70,.53,.12),(.52,.47,.027),'oil')
    for y in (-.42,.42):
        for x in (-.6,.5):
            H.beam('pump_trestle',(x,y,.12),(-.1,y,1.22),.13,'iron')
        H.beam('pump_crossbrace',(-.6,y,.15),(.33,y,.69),.07,'copper')
    H.beam('walking_beam',(-1.13,0,1.42),(.83,0,1.15),.18,'copper')
    H.box('horsehead',(-1.10,0,1.27),(.29,.38,.63),'iron',.08,rotation=(0,-.18,0))
    H.beam('pump_rod',(-1.18,0,.16),(-1.18,0,1.25),.045,'iron')
    cylinder('wellhead',(-1.18,0,.20),.16,.22,'iron')
    H.box('motor',(.68,0,.36),(.54,.60,.46),'iron',.065)
    for x in (.3,.85):
        cylinder('oil_drum',(x,-.91,.33),.22,.55,'oil')
        for z in (.12,.48): cylinder('drum_band',(x,-.91,z),.228,.04,'copper')
    H.beam('outlet_pipe',(-1.1,0,.17),(-1.1,-.8,.17),.085,'iron')
    H.beam('outlet_pipe',(-1.1,-.8,.17),(.3,-.8,.17),.085,'iron')


def ruins():
    base()
    for row in range(3):
        for col in range(4):
            if (row,col)==(0,3): continue
            H.box('ancient_paving',(-.95+col*.57,-.72+row*.62,.07),(.53,.57,.14),'ruin',.035)
    for x,count in ((-.85,5),(.65,4)):
        for row in range(count):
            H.box('broken_arch_pier',(x,.35,.25+row*.28),(.38,.40,.26),'ruin',.045)
    for i in range(7):
        if i in (1,2): continue
        angle=math.pi*i/6
        H.box('arch_voussoir',(-.1+.75*math.cos(angle),.35,1.35+.52*math.sin(angle)),
              (.30,.43,.28),'ruin',.035,rotation=(0,angle-math.pi/2,0))
    for i in range(5):
        H.box('fallen_masonry',(.60+(i%2)*.35,-.60+(i//2)*.30,.14),(.29,.24,.22),'ruin',.04,rotation=(0,.12*i,.5*i))
    cylinder('old_beacon_base',(-.65,-.68,.26),.28,.36,'stone')
    H.box('amber_archive_marker',(-.65,-.70,.53),(.13,.13,.26),'amber',.028)
    for i,(x,y) in enumerate(((-.9,.55),(.65,.5),(-.8,-.5))):
        rock('moss',(x,y,.16),(.24,.17,.10),'leaf',i)
    for x,y in ((-1.3,.8),(1.25,-1.1)): tuft(x,y,1.5)


def prepare():
    global SCENE
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    SCENE=bpy.data.scenes.new('Real_City_Terrain');bpy.context.window.scene=SCENE
    palette();H.setup_camera(SCENE)
    SCENE.render.resolution_x=512;SCENE.render.resolution_y=512
    SCENE.camera.data.ortho_scale=3.6*math.sqrt(2)*512/480
    SCENE.camera.data.shift_y=0
    bpy.context.view_layer.update()
    initial=world_to_camera_view(SCENE,SCENE.camera,Vector((0,0,0))).y
    SCENE.camera.data.shift_y=.1
    delta=world_to_camera_view(SCENE,SCENE.camera,Vector((0,0,0))).y-initial
    SCENE.camera.data.shift_y=((1-320/512)-initial)*.1/delta
    builders={'grass':meadow,'forest':lambda:forest(3),'forest_thinned':lambda:forest(2),
              'forest_sparse':lambda:forest(1),'water':water,'mountain':mountain,'road':road,
              'oil_well':oil_well,'ruins':ruins}
    for name,builder in builders.items():
        c=bpy.data.collections.new('terrain_tile_'+name);SCENE.collection.children.link(c)
        COLLECTIONS[name]=c;H.COL=c;H.PREFIX='SM_terrain_'+name
        builder();H.clean_meshes(c)
    print('Prepared nine terrain models in a separate scene')


def show(name):
    bpy.context.window.scene=SCENE
    for key,c in COLLECTIONS.items():
        c.hide_render=key!=name;c.hide_viewport=key!=name
    bpy.context.view_layer.update()
    for obj in SCENE.objects: obj.select_set(False)
    for obj in COLLECTIONS[name].all_objects: obj.select_set(True)


def export_tile(name):
    show(name);tris=0
    for obj in COLLECTIONS[name].all_objects:
        obj.data.calc_loop_triangles();tris+=len(obj.data.loop_triangles)
        bm=bmesh.new();bm.from_mesh(obj.data)
        assert all(e.is_manifold for e in bm.edges),obj.name
        bm.free()
        assert all(abs(v.co.x)<=1.801 and abs(v.co.y)<=1.801 for v in obj.data.vertices),obj.name
    assert tris<8000,(name,tris)
    bpy.ops.export_scene.gltf(filepath=str(OUT_DIR/(name+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True)
    SCENE.render.filepath=str(OUT_DIR/(name+'.png'));bpy.ops.render.render(write_still=True)
    REPORT[name]={'triangles':tris,'objects':len(COLLECTIONS[name].all_objects),'png':name+'.png','glb':name+'.glb'}
    print('Exported',name,tris)


def finish():
    show('forest')
    bpy.data.libraries.write(str(OUT_DIR/'terrain_tiles.blend'),{SCENE},fake_user=True)
    manifest={'style':'Aeolian bright fantasy stylized mid-poly','size':[512,512],
              'footprint':3.6,'footprint_pixels':480,'anchor':[256,320],
              'camera_elevation':30,'tiles':REPORT}
    (OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Saved terrain source and manifest')


def validate_roundtrip():
    previous=bpy.context.scene;qa=bpy.data.scenes.new('terrain_export_qa');bpy.context.window.scene=qa
    results=[]
    try:
        for name in TERRAIN:
            bpy.ops.import_scene.gltf(filepath=str(OUT_DIR/(name+'.glb')))
            triangles=0
            for obj in list(qa.objects):
                if obj.type=='MESH':
                    obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
                    bm=bmesh.new();bm.from_mesh(obj.data)
                    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
                    assert all(e.is_manifold for e in bm.edges),(name,obj.name)
                    bm.free()
                bpy.data.objects.remove(obj,do_unlink=True)
            assert triangles==REPORT[name]['triangles'],name
            results.append({'terrain':name,'triangles':triangles,'nonmanifold_edges':0})
    finally:
        bpy.context.window.scene=previous;bpy.data.scenes.remove(qa)
    (OUT_DIR/'roundtrip-validation.json').write_text(json.dumps(results,indent=2))
    print('Roundtrip validated',len(results))


if __name__=='__main__':
    prepare()
    for name in TERRAIN: export_tile(name)
    finish();validate_roundtrip()
