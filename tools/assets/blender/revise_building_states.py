"""Blender MCP entry points: prepare(kind), export_level(level), finish()."""

import importlib.util
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("housing_geometry", Path(__file__).with_name("regenerate_early_housing.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
FAMILIES = {
    "dugout": ("housing/dugout", 5, False),
    "wood_house": ("housing/wood_house", 6, False),
    "town_hall": ("center/town_hall", 10, False),
    "lumber_yard": ("industry/lumber_yard", 1, True),
}
STATE = {}
ROUNDTRIP = []


def bounds(objects):
    coords = [obj.matrix_world @ Vector(c) for obj in objects if obj.type == "MESH" for c in obj.bound_box]
    return Vector([min(v[i] for v in coords) for i in range(3)]), Vector([max(v[i] for v in coords) for i in range(3)])


def normalized(objects):
    bpy.context.view_layer.update()
    ground = [obj for obj in objects if obj.type == 'MESH' and ('earth_tile' in obj.name or 'tile_base' in obj.name)]
    if not ground:
        raise ValueError('Cannot normalize a building without its active ground tile')
    low, high = bounds(ground)
    offset = Vector(((low.x+high.x)/2, (low.y+high.y)/2, 0))
    for obj in objects:
        if obj.type != "MESH":
            continue
        transform = Matrix.Translation(-offset) @ obj.matrix_world
        obj.parent = None
        obj.data = obj.data.copy()
        obj.data.transform(transform)
        obj.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()


def remove(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def clipped(obj, plane_point, plane_normal, jagged=False):
    """Retain the negative half-space, cap the new boundary and recalc normals."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                          plane_co=plane_point, plane_no=plane_normal, dist=0.00001,
                          clear_outer=True, clear_inner=False)
    boundary = [edge for edge in bm.edges if edge.is_boundary]
    if boundary:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    if not bm.faces:
        bm.free()
        remove(obj)
        return False
    if jagged:
        normal=Vector(plane_normal).normalized(); point=Vector(plane_point)
        for vertex in bm.verts:
            if abs((vertex.co-point).dot(normal)) < 0.025:
                noise=math.sin(vertex.co.x*31+vertex.co.y*43+vertex.co.z*29)
                vertex.co += normal*(0.07*noise)
                vertex.co.z += 0.045*noise
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return True


def solid_role(name):
    return any(token in name for token in ("main_body", "main_wall", "upper_wall", "annex_wall", "side_annex", "open_frame_")) and "roof" not in name


def roof_role(name):
    return any(token in name for token in ("roof_shingle", "main_roof", "annex_roof", "shed_roof", "tower_roof", "roof_left", "roof_right", "gable_roof")) and not any(token in name for token in ("ridge", "beam", "support", "trim", "hole", "patch"))


def wall_role(name):
    return any(token in name for token in ("wall", "siding", "facade", "gable", "panel", "retaining", "dormer_body", "central_tower", "second_tier", "side_tower", "open_frame")) and not roof_role(name)


def set_material(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.material_index = 0


def shell_walls(collection):
    for obj in list(collection.all_objects):
        if obj.type != "MESH" or not solid_role(obj.name):
            continue
        low, high = bounds([obj])
        size = high-low
        if min(size.x, size.y) < 0.3:
            continue
        material = obj.data.materials[0]
        name = obj.name
        remove(obj)
        for axis in (0, 1):
            for side in (-1, 1):
                center = (low+high)/2
                center[axis] += side*(size[axis]/2-0.045)
                dims = size.copy()
                dims[axis] = 0.09
                wall = H.box(name+"_shell", center, dims, "wood")
                set_material(wall, material)


def frame(width, depth, eaves, rise, damaged):
    for y in (-depth/2, 0, depth/2):
        for side in (-1, 1):
            if damaged and side > 0 and y <= 0:
                endpoint = (width*0.13, y, eaves+rise*0.42)
            else:
                endpoint = (0, y, eaves+rise)
            H.beam("exposed_rafter", (side*width/2, y, eaves), endpoint, 0.075, "beam" if damaged else "wood")
    for x in (-width/2, width/2):
        for y in (-depth/2, depth/2):
            if not (damaged and x > 0 and y < 0):
                H.beam("exposed_frame_post", (x,y,0.15), (x,y,eaves), 0.085, "beam" if damaged else "wood")


def rubble(width, depth, level):
    for i in range(18):
        angle = -1.1 + i*0.20
        x = width*(-0.35+0.17*(i%6))
        y = -depth*0.50 - 0.38 - 0.14*(i%3)
        H.box("fallen_masonry" if i%3==0 else "splintered_plank",
              (x,y,0.12+0.06*(i%3)),
              (0.18,0.17,0.13) if i%3==0 else (0.34+0.07*(i%2),0.09,0.07),
              "stone" if i%3==0 else ("char" if i%2 else "wood"),
              rotation=(0.15*(i%2),0.12*(i%3),angle))


def revise(collection, kind, level, state):
    H.COL = collection
    H.PREFIX = f"{kind}_l{level:02d}_{state}"
    shell_walls(collection)
    H.clean_meshes(collection)
    objects = list(collection.all_objects)
    low, high = bounds(objects)
    tile = max(high.x-low.x,high.y-low.y)
    damaged = state == "damaged"
    if kind == "dugout":
        width, depth, eaves, rise = 1.72+level*0.11, 1.42+level*0.06, 0.57+level*0.05, 0.27
    elif kind == "wood_house":
        if level <= 3:
            width,depth,eaves,rise = 1.48+0.13*level,1.27+0.08*level,1.29+0.12*level,0.62+0.05*level
        else:
            width,depth,eaves,rise = 1.18+level*0.13,1.02+level*0.08,1.3+0.1*level,0.50
    elif kind == "town_hall":
        width,depth,eaves,rise = 1.55+min(level,7)*0.18,1.3+min(level,6)*0.13,0.8+min(level,8)*0.106,0.38+level*0.025
    else:
        width,depth,eaves,rise = 1.32,0.96,1.08,0.42
    if 'building_dimensions' in collection:
        width,depth,eaves,rise = collection['building_dimensions']
    missing = 0
    for index,obj in enumerate(objects):
        if obj.type != "MESH" or obj.name not in bpy.data.objects:
            continue
        name = obj.name.lower()
        lo,hi = bounds([obj]); center=(lo+hi)/2
        if any(token in name for token in ("smoke", "dust", "flower", "main_flag", "flag_pole", "weather_vane", "amethyst", "clock_hand", "lantern", "window_light", "pool", "pond", "banner")):
            remove(obj); missing+=1; continue
        if "tile" in name or "foundation" in name or "path" in name or "plaza" in name or "work_yard" in name or "stone_pad" in name:
            continue
        if any(token in name for token in ("window_glass", "glass", "front_door", "door_plank", "shutter")) or ("window" in name and "frame" not in name and "sill" not in name and "recess" not in name):
            if not damaged or index%3!=0:
                remove(obj); missing+=1
            else:
                set_material(obj,H.MATS["char"])
            continue
        if any(token in name for token in ("canopy_board", "canopy_roof", "porch_roof", "awning")):
            if not damaged or index%3!=0:
                remove(obj); missing+=1
            continue
        if kind=="dugout" and any(token in name for token in ("earth_mound", "turf_cap", "windleaf_roof")):
            if clipped(obj,(-0.18,0,0),(1,-0.38,0),jagged=damaged):
                if damaged and "earth_mound" in name:
                    for vertex in obj.data.vertices:
                        if vertex.co.x > -0.4 and vertex.co.z > 0.35:
                            vertex.co.z *= 0.70
                if "turf_cap" in name and damaged:
                    obj.data.materials.append(H.MATS["earth"])
                    for face in obj.data.polygons:
                        if face.center.x > -0.5: face.material_index=len(obj.data.materials)-1
            missing+=1
            continue
        if roof_role(name):
            if "tower_roof" in name:
                remove(obj)
            else:
                threshold = -width*(0.05 if damaged else 0.18) - (0.45 if kind=='lumber_yard' else 0)
                clipped(obj,(threshold,0,0),(1,-0.28 if damaged else 0,0),jagged=damaged)
            missing+=1
            continue
        if wall_role(name):
            if damaged:
                # A diagonal loss region removes the front-right corner across all layers.
                retained=clipped(obj,(width*0.08-(0.45 if kind=='lumber_yard' else 0),0,0),(1,-0.48,0.12),jagged=True)
                if retained and center.x > -0.15:
                    set_material(obj,H.MATS["char"])
            else:
                height=eaves*(0.50 if center.x > 0 else 0.76)
                clipped(obj,(0,0,height),(0,0,1))
            missing+=1
            continue
        if any(token in name for token in ("corner", "curved_bargeboard", "eave_trim", "ridge", "chimney", "door_lintel", "door_header", "window_frame", "window_sill", "window_recess", "door_recess", "door_jamb", "canopy_bracket", "porch_post", "brick_pier", "reinforcement")):
            if damaged:
                if "chimney" in name:
                    clipped(obj,(0,0,eaves+0.25),(0,0,1),jagged=True)
                elif center.x > 0.15 and center.y < depth*0.35:
                    remove(obj)
            elif hi.z > eaves*0.78 and ("window" in name or "chimney" in name or "door" in name):
                remove(obj)
            continue
        if "crane" in name:
            if "post" in name:
                clipped(obj,(0,0,0.58 if damaged else 0.74),(0,0,1))
            elif damaged:
                obj.data.transform(Matrix.Translation((0,0,0.14-center.z)) @ Matrix.Rotation(0.55,4,'Y'))
            else:
                remove(obj)
        if damaged and kind=='lumber_yard' and 'saw_' in name:
            pivot=Vector((-0.45,-0.9,0.66))
            obj.data.transform(Matrix.Translation(pivot+Vector((0,0,-0.16))) @ Matrix.Rotation(0.25,4,'X') @ Matrix.Translation(-pivot))
        if not damaged and any(token in name for token in ("bench", "barrel", "notice", "archive", "balcony", "fence", "tool_rack")):
            remove(obj)
    frame(width,depth,eaves,rise,damaged)
    if kind == "town_hall":
        tower_width=collection.get('tower_width',0.55+min(level,7)*0.035)
        tower_top=collection.get('tower_top',1.52+level*0.13)
        if damaged:
            H.beam("broken_tower_spine",(-tower_width/2,0.13,eaves*0.65),
                   (-tower_width/2-0.09,0.13,tower_top*0.86),0.10,"beam")
            H.box("surviving_tower_course",(-tower_width*0.15,-0.04,eaves+0.12),
                  (tower_width*0.64,tower_width,0.17),"stone")
        else:
            for x in (-tower_width/2,tower_width/2):
                for y in (-tower_width/2-0.04,tower_width/2-0.04):
                    H.beam("tower_frame_upright",(x,y,eaves*0.65),(x,y,tower_top),0.075,"wood")
            for z in (eaves+0.18,tower_top-0.07):
                for y in (-tower_width/2-0.04,tower_width/2-0.04):
                    H.beam("tower_frame_crossbeam",(-tower_width/2,y,z),(tower_width/2,y,z),0.075,"wood")
            H.beam("tower_scaffold_brace",(-tower_width/2,-tower_width/2-0.06,eaves),
                   (tower_width/2,-tower_width/2-0.06,tower_top-0.12),0.06,"beam")
    if kind == "lumber_yard":
        newparts=[obj for obj in collection.all_objects if "exposed_" in obj.name]
        for obj in newparts: obj.location += Vector((-0.45,-0.48,0))
    if damaged:
        rubble(width,depth,level)
        H.beam("collapsed_roof_beam", (width*0.2,-depth*0.25,0.16), (width*0.48,depth*0.2,eaves*0.45),0.12,"char")
    else:
        overlay=bpy.data.collections.new(H.PREFIX+"_overlay")
        collection.children.link(overlay)
        H.COL=overlay
        scaffold_width=min(tile*0.40,width/2+0.35)
        for x in (-scaffold_width,scaffold_width):
            for y in (-depth*0.63,depth*0.50):
                H.beam("scaffold_post",(x,y,0.09),(x,y,eaves+0.25),0.08,"wood")
            for z in (eaves*0.5,eaves+0.12):
                H.beam("scaffold_rail",(x,-depth*0.67,z),(x,depth*0.56,z),0.075,"wood")
            H.beam("scaffold_brace",(x,-depth*0.60,0.15),(x,depth*0.47,eaves+0.1),0.065,"beam")
        for i in range(4):
            H.box("ordered_plank_stack",(width*0.20,-depth*0.68,0.13+i*0.07),(0.68,0.18,0.065),"wood")
        for i in range(4):
            H.box("masonry_delivery",(-width*0.3,-depth*0.69,0.14+(i//2)*0.15),(0.17,0.17,0.14),"stone")
    H.clean_meshes(collection)
    assert missing > 4,(kind,level,state,"no structural change")
    return {"structural_edits":missing,"progress":0.55 if not damaged else None}


def clone_active(active,name,scene):
    collection=bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    for source in active.all_objects:
        if source.type!='MESH': continue
        obj=source.copy(); obj.data=source.data.copy(); obj.parent=None
        obj.name=source.name.replace('_active','_'+name.rsplit('_',1)[1])
        collection.objects.link(obj)
    return collection


def prepare(kind):
    global STATE
    folder,count,public=FAMILIES[kind]
    model_dir=ROOT/('frontend/public/assets/buildings' if public else 'frontend/src/assets/buildings')/folder
    source=model_dir/(kind+'_levels.blend')
    # Existing asset scenes have already been backed up, and are replaced by this revision.
    oldcollections=[c for c in bpy.data.collections if c.name.startswith(kind+'_l')]
    for collection in oldcollections:
        for obj in list(collection.objects): remove(obj)
    for collection in oldcollections:
        bpy.data.collections.remove(collection)
    scene=bpy.data.scenes.new('revised_'+kind)
    bpy.context.window.scene=scene
    H.palette()
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        dst.collections=[f'{kind}_l{level:02d}_active' for level in range(1,count+1)]
        assert all(name in src.collections for name in dst.collections),(kind,src.collections)
    active_collections={}
    for level,collection in enumerate(dst.collections,1):
        scene.collection.children.link(collection)
        collection.hide_viewport=False; collection.hide_render=False
        for child in collection.children:
            child.hide_viewport=False; child.hide_render=False
        if kind=='dugout' and level>=2:
            for obj in list(collection.all_objects): remove(obj)
            H.COL=collection; H.PREFIX=collection.name
            H.dugout(level,False)
        normalized(list(collection.all_objects))
        active_collections[level]=collection
    H.setup_camera(scene)
    tile=max(bounds(active_collections[1].all_objects)[1]-bounds(active_collections[1].all_objects)[0])
    scene.camera.data.ortho_scale *= tile/3.6
    scene['state_revision']='structural-v2'
    STATE={'kind':kind,'count':count,'folder':folder,'model_dir':model_dir,'active':active_collections,'report':{}}
    print('Prepared '+kind+', levels '+str(count))


def select_only(collection):
    for obj in bpy.context.scene.objects: obj.select_set(False)
    for root in bpy.context.scene.collection.children:
        root.hide_viewport=root!=collection; root.hide_render=root!=collection
    for child in collection.children:
        child.hide_viewport=False; child.hide_render=False
    bpy.context.view_layer.update()
    for obj in collection.all_objects:
        if obj.type=='MESH': obj.select_set(True)


def export(collection,name):
    select_only(collection)
    bpy.ops.export_scene.gltf(filepath=str(STATE['model_dir']/(name+'.glb')),export_format='GLB',
                              use_selection=True,use_active_scene=True,export_extras=True)
    bpy.context.scene.render.filepath=str(ROOT/'frontend/public/assets/buildings'/STATE['folder']/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    tris=0
    for obj in collection.all_objects:
        if obj.type=='MESH':
            obj.data.calc_loop_triangles(); tris+=len(obj.data.loop_triangles)
    STATE['report'].setdefault(name,{}).update({'triangles':tris,'bounds':[list(v) for v in bounds(collection.all_objects)]})


def export_level(level):
    kind=STATE['kind']; active=STATE['active'][level]
    if kind=='dugout' and level>=2:
        export(active,active.name)
    for state in ('construction','damaged'):
        name=f'{kind}_l{level:02d}_{state}'
        collection=clone_active(active,name,bpy.context.scene)
        STATE['report'][name]=revise(collection,kind,level,state)
        export(collection,name)
    print('Updated '+kind+' level '+str(level))


def finish():
    scene=bpy.context.scene
    kind=STATE['kind']
    for root in scene.collection.children:
        root.hide_viewport=False;root.hide_render=False
    bpy.context.view_layer.update()
    for obj in scene.objects: obj.select_set(False)
    saved=[]
    for collection in scene.collection.children:
        if not collection.name.startswith(kind+'_l'): continue
        level=int(collection.name.split('_l')[1][:2]); state=collection.name.rsplit('_',1)[1]
        tile=max(bounds(collection.all_objects)[1]-bounds(collection.all_objects)[0])
        delta=Vector(((level-1)*(tile+0.6),H.STATES.index(state)*(tile+0.6),0))
        for obj in collection.all_objects:
            if obj.type=='MESH':
                saved.append((obj,obj.location.copy()));obj.location+=delta;obj.select_set(True)
    try:
        bpy.context.view_layer.update()
        bpy.ops.export_scene.gltf(filepath=str(STATE['model_dir']/(kind+'_levels.glb')),
                                  export_format='GLB',use_selection=True,use_active_scene=True)
    finally:
        for obj,location in saved: obj.location=location
    select_only(STATE['active'][1])
    bpy.data.libraries.write(str(STATE['model_dir']/(kind+'_levels.blend')),{scene},fake_user=True)
    (STATE['model_dir']/'state-revision-report.json').write_text(json.dumps(STATE['report'],indent=2))
    print('Saved '+kind+' source, gallery and report')


def validate_roundtrip(kind):
    folder,count,public=FAMILIES[kind]
    model_dir=ROOT/('frontend/public/assets/buildings' if public else 'frontend/src/assets/buildings')/folder
    report=json.loads((model_dir/'state-revision-report.json').read_text())
    previous=bpy.context.scene
    qa=bpy.data.scenes.new('state_roundtrip_validation')
    bpy.context.window.scene=qa
    results=[]
    try:
        for name,expected in report.items():
            bpy.ops.import_scene.gltf(filepath=str(model_dir/(name+'.glb')))
            tris=0;nonmanifold=0;flag_boundaries=0
            for obj in list(qa.objects):
                if obj.type=='MESH':
                    obj.data.calc_loop_triangles();tris+=len(obj.data.loop_triangles)
                    bm=bmesh.new();bm.from_mesh(obj.data)
                    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001)
                    for edge in bm.edges:
                        if edge.is_manifold:
                            continue
                        # Legacy cloth flags are intentionally single-sided surfaces.
                        if 'flag' in obj.name.lower() and edge.is_boundary:
                            flag_boundaries+=1
                        else:
                            nonmanifold+=1
                    bm.free()
            bpy.data.batch_remove(ids=list(qa.objects))
            assert tris==expected['triangles'],(name,tris,expected['triangles'])
            assert nonmanifold==0,(name,nonmanifold)
            results.append({'name':name,'triangles':tris,'nonmanifold_edges':nonmanifold,
                            'intentional_flag_boundary_edges':flag_boundaries})
    finally:
        bpy.context.window.scene=previous
        bpy.data.scenes.remove(qa)
    ROUNDTRIP.extend(results)
    (ROOT/'frontend/public/assets/buildings/state-roundtrip-validation.json').write_text(json.dumps(ROUNDTRIP,indent=2))
    print('Validated roundtrip '+kind+': '+str(len(results)))
