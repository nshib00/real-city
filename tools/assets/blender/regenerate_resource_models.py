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
spec = importlib.util.spec_from_file_location('resource_geometry', Path(__file__).with_name('generate_resource_icons.py'))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


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


def crystal(collection):
    for i,(x,y,h,tilt) in enumerate(((-.25,0,.72,-18),(0,.12,1.15,0),(.27,0,.86,17))):
        shard(f'amethyst_prism_{i}',collection,(x,y,h/2),h,G.MATS['amethyst'],(0,math.radians(tilt),0),.14)


def windleaf(collection):
    for i,angle in enumerate((-.55,0,.55)):
        leaf(f'windleaf_blade_{i}',collection,(i*.08-.08,0,.2+i*.08),(.63,.78,.65),
             G.MATS['leaf'] if i!=1 else G.MATS['leaf_light'],(.25,0,angle))
        G.cube(f'windleaf_rib_{i}',collection,(i*.08-.08,0,.28+i*.08),(.024,.75,.024),G.MATS['leaf_dark'],(.25,0,angle))
    G.cube('harvest_binding',collection,(0,-.45,.18),(.29,.075,.065),G.MATS['wood_cut'])


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


def sand(collection):
    sphere('sand_heap',collection,(0,0,.12),(.55,.42,.19),G.MATS['sand'])
    for i in range(8):
        a=i*math.tau/8
        sphere(f'sand_grain_{i}',collection,(.4*math.cos(a),.31*math.sin(a),.14),(.045,.04,.035),G.MATS['sand_light'],12)
    G.cube('sand_scoop',collection,(.25,.18,.31),(.32,.22,.055),G.MATS['wood_cut'],(.3,.2,.3))


def rocks(collection, material):
    for i,(x,y,z,s) in enumerate(((-.28,-.13,.2,.31),(.16,.1,.3,.42),(.37,-.2,.13,.23))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=s,location=(x,y,z))
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
    for key in ('stone','coal','iron_ore'):
        G.BUILDERS[key]=lambda c,k=key:rocks(c,k)


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
        bake(collection)
        camera(scene,collection)
        for obj in scene.objects: obj.select_set(False)
        triangles=0
        for obj in collection.objects:
            obj.name='resource_'+resource['id']+'_'+obj.name
            obj.select_set(True)
            obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
        rid=resource['id']
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
