"""Render the five rig actions in four map directions from a monster .blend.

Run with Blender --background --python render_monster_frames.py -- <monster-id> [pilot].
The output PNGs are temporary inputs for pack_monster_atlases.py.
"""

from __future__ import annotations

import os
import sys
import time

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
from generate_monster_models import KINDS, destination


FRAMES = {"idle": 8, "walk": 12, "attack": 10, "hit": 5, "death": 14}
DIRECTIONS = {"se": (5, -7), "sw": (-5, -7), "ne": (5, 7), "nw": (-5, 7)}
ROOT = "/home/nshib/projects/real-city"
TEMP = "/tmp/real-city-monster-frames"


def render(kind: str, pilot: bool = False) -> None:
    assert kind in KINDS, kind
    bpy.ops.wm.open_mainfile(filepath=destination(f"{ROOT}/frontend/public/assets/monsters/{kind}/{kind}.blend"))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 160
    scene.render.resolution_y = 160
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.render.filepath = ""
    rig = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if rig is None:
        raise RuntimeError(f"{kind}: .blend contains no armature")
    print("MONSTER_RIG", kind, rig.name, flush=True)
    camera = scene.camera
    target = Vector((0, 0, 1.75 if kind == "ancient_colossus" else 1.02))
    folder = destination(f"{TEMP}/{kind}")
    os.makedirs(folder, exist_ok=True)
    started = time.perf_counter()
    rendered = 0
    for direction, (cx, cy) in DIRECTIONS.items():
        if pilot and direction != "se":
            continue
        camera.location = (cx, cy, 7 if kind == "ancient_colossus" else 6)
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        for key, count in FRAMES.items():
            if pilot and key != "walk":
                continue
            action = bpy.data.actions.get(f"AN_{kind}_{key}")
            if action is None:
                action = next((item for item in bpy.data.actions if item.name.endswith("_" + key)), None)
            if action is None:
                raise RuntimeError(f"{kind}: missing action {key}")
            rig.animation_data.action = action
            for index in range(count):
                if pilot and index >= 4:
                    break
                progress = index / count if key in ("idle", "walk") else index / max(1, count - 1)
                scene.frame_set(round(action.frame_start + progress * (action.frame_end - action.frame_start)))
                scene.render.filepath = os.path.join(folder, f"{kind}_{key}_{direction}_{index:04d}.png")
                if os.path.isfile(scene.render.filepath) and not pilot:
                    continue
                bpy.ops.render.render(write_still=True)
                rendered += 1
    print("MONSTER_FRAMES", kind, rendered, "seconds", round(time.perf_counter() - started, 2), flush=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    render(args[0], "pilot" in args[1:])
