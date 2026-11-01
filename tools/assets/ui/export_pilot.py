"""Blender: оригинальная ресурсная миниатюра; CPU-рендер без GPU/MCP."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector

output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.render.resolution_x = scene.render.resolution_y = 64
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.world.color = (0.3, 0.3, 0.3)
material = bpy.data.materials.new('Светлый камень')
material.diffuse_color = (0.48, 0.53, 0.49, 1)
for location, scale in [((-0.35, 0, 0), (0.8, 0.65, 0.6)), ((0.5, 0.2, -0.1), (0.5, 0.45, 0.4))]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=location)
    bpy.context.object.scale = scale
    bpy.context.object.data.materials.append(material)
bpy.ops.object.light_add(type='AREA', location=(-3, -4, 6))
bpy.context.object.data.energy = 500
bpy.context.object.data.shape = 'DISK'
bpy.context.object.data.size = 4
bpy.ops.object.camera_add(location=(3, -5, 4))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.5
scene.camera = camera
scene.render.filepath = str(output / 'stone.png')
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('stone.blend')))
bpy.ops.render.render(write_still=True)
