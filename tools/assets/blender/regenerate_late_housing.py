"""Run prepare(), level(4..6), finish() through Blender MCP."""

import importlib.util
import json
from pathlib import Path

import bpy

spec = importlib.util.spec_from_file_location('late_housing_states', Path(__file__).with_name('revise_building_states.py'))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
H = S.H


def fit_tile(collection):
    for obj in collection.all_objects:
        if obj.type != 'MESH' or 'tile' in obj.name:
            continue
        for vertex in obj.data.vertices:
            if vertex.co.x > 1.1:
                vertex.co.x = 1.1+(vertex.co.x-1.1)*0.75
        obj.data.update()


def prepare():
    S.prepare('wood_house')
    folder = S.STATE['model_dir']
    S.STATE['report'] = json.loads((folder/'state-revision-report.json').read_text())
    with bpy.data.libraries.load(str(folder/'wood_house_levels.blend'), link=False) as (src, dst):
        dst.collections = [f'wood_house_l{n:02d}_{state}' for n in (1,2,3) for state in ('construction','damaged')]
    for collection in dst.collections:
        bpy.context.scene.collection.children.link(collection)
    for n in (4,5,6):
        collection = S.STATE['active'][n]
        for obj in list(collection.all_objects):
            S.remove(obj)
        H.COL=collection; H.PREFIX=collection.name
        H.wood_house(n,False)
        H.clean_meshes(collection)
        fit_tile(collection)
        collection['building_dimensions']=[1.48+0.13*n,1.27+0.08*n,1.29+0.12*n+(0.48 if n>=5 else 0),0.62+0.05*n]
    print('Prepared wooden house levels 4-6; preserved levels 1-3')


def level(n):
    assert n in (4,5,6)
    active=S.STATE['active'][n]
    S.export(active,active.name)
    for state in ('construction','damaged'):
        name=f'wood_house_l{n:02d}_{state}'
        collection=S.clone_active(active,name,bpy.context.scene)
        collection['building_dimensions']=list(active['building_dimensions'])
        S.STATE['report'][name]=S.revise(collection,'wood_house',n,state)
        S.export(collection,name)
    print('Exported three states:',n)


def finish():
    S.finish()
    previous=S.ROOT/'frontend/public/assets/buildings/state-roundtrip-validation.json'
    S.ROUNDTRIP=[entry for entry in json.loads(previous.read_text()) if not entry['name'].startswith('wood_house_')] if previous.exists() else []
    S.validate_roundtrip('wood_house')
