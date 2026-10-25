"""Double the Ancient Colossus while retaining its rig and animation clips.

Run in Blender: --background --python tools/assets/blender/resize_ancient_colossus.py
The script expects the original 1x source asset and refuses to scale twice.
"""

from __future__ import annotations

import os
import sys
import json

import bpy
from mathutils import Vector


ROOT = "/home/nshib/projects/real-city"
KIND = "ancient_colossus"
SCALE = 2.0


def path(value: str) -> str:
    if sys.platform == "win32":
        return "\\\\wsl.localhost\\Debian" + value.replace("/", "\\")
    return value


folder = path(f"{ROOT}/frontend/public/assets/monsters/{KIND}")
blend_path = os.path.join(folder, f"{KIND}.blend")
bpy.ops.wm.open_mainfile(filepath=blend_path)
scene = bpy.context.scene
rigs = [obj for obj in scene.objects if obj.type == "ARMATURE"]
if len(rigs) != 1:
    raise RuntimeError(f"Expected one armature, found {len(rigs)}")
rig = rigs[0]
if any(abs(axis - 1.0) > 1e-5 for axis in rig.scale):
    raise RuntimeError(f"Expected an unscaled rig, found {tuple(rig.scale)}")

geometry = [obj for obj in scene.objects if obj.type == "MESH"]
if not geometry or any(obj.parent != rig for obj in geometry):
    raise RuntimeError("All creature meshes must be parented to the armature")

# Scaling the parent preserves meshes, bone poses and all five animation clips.
rig.scale = (SCALE,) * 3

# Keep the preview framing equivalent to the previous asset. The game's sprite
# width is scaled separately, so the visible creature becomes twice as large.
camera = scene.camera
camera.location = Vector(camera.location) * SCALE
camera.data.ortho_scale *= SCALE
for light in (obj for obj in scene.objects if obj.type == "LIGHT"):
    light.location = Vector(light.location) * SCALE
    light.data.energy *= SCALE * SCALE
    if light.data.type == "AREA":
        light.data.size *= SCALE

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)

scene.render.filepath = os.path.join(folder, f"{KIND}_preview.png")
bpy.ops.render.render(write_still=True)

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for obj in geometry:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=os.path.join(folder, f"{KIND}_preview.glb"),
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_nla_strips=False,
    export_force_sampling=True,
)
report_path = os.path.join(folder, "model-report.json")
with open(report_path, encoding="utf8") as stream:
    report = json.load(stream)
report["uniform_scale"] = SCALE
with open(report_path, "w", encoding="utf8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print("ANCIENT_COLOSSUS_RESIZED", SCALE, len(geometry), flush=True)
