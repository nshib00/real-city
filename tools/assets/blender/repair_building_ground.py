"""Repair the audited lumber-yard ground without regenerating building geometry.

Run in a separate factory-startup Blender, with --output pointing to staging.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'frontend/public/assets/buildings/industry/lumber_yard'


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('yard', Path(__file__).with_name('generate_lumber_yard_models.py'))
    yard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(yard)
    bpy.data.batch_remove(ids=list(bpy.context.scene.objects))
    scene = bpy.context.scene
    scene.name = 'Lumber_Yard_Ground_Revision'
    yard.add_lighting_and_camera()
    yard.setup_render()
    collections = []
    report = {}
    for level in range(1, 14):
        for state in ('active', 'construction', 'damaged'):
            name = f'lumber_yard_l{level:02d}_{state}'
            bpy.ops.import_scene.gltf(filepath=str(SOURCE / (name + '.glb')))
            objects = list(bpy.context.selected_objects)
            collection = bpy.data.collections.new(name)
            collection['ground_source'] = f'lumber_yard_l{level:02d}_active'
            scene.collection.children.link(collection)
            for obj in objects:
                for old in list(obj.users_collection):
                    old.objects.unlink(obj)
                collection.objects.link(obj)
            removed = [obj for obj in objects if 'scorched_ground' in obj.name]
            if state == 'damaged':
                assert len(removed) == 1, name
                bpy.data.batch_remove(ids=removed)
                bpy.ops.export_scene.gltf(filepath=str(output / (name + '.glb')), export_format='GLB',
                                          use_selection=True, use_active_scene=True)
            scene.render.filepath = str(output / (name + '.png'))
            bpy.ops.render.render(write_still=True)
            report[name] = yard.report_entry(collection, level, state, output / (name + '.png'))
            report[name]['ground_source'] = collection['ground_source']
            report[name]['removed_ground_overlays'] = len(removed)
            collection.hide_render = True
            collection.hide_viewport = True
            collections.append(collection)
            (output / 'ground-repair-report.json').write_text(json.dumps(report, indent=2))
            print('GROUND_REPAIR ' + name, flush=True)
    # One editable source contains all 39 states; gallery offsets are export-only.
    saved = []
    for i, collection in enumerate(collections):
        collection.hide_viewport = False
        delta = Vector(((i // 3) * 4.3, (i % 3) * 4.3, 0))
        for obj in collection.all_objects:
            saved.append((obj, obj.location.copy()))
            obj.location += delta
            obj.select_set(True)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(output / 'lumber_yard_levels.glb'), export_format='GLB',
                              use_selection=True, use_active_scene=True)
    for obj, location in saved:
        obj.location = location
    for collection in collections:
        collection.hide_render = collection != collections[0]
        collection.hide_viewport = collection != collections[0]
    bpy.data.libraries.write(str(output / 'lumber_yard_levels.blend'), {scene}, fake_user=True)
    (output / 'complete.json').write_text(json.dumps({'rendered': len(report), 'repaired_ground': 13}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    main(args.output)
