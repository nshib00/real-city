"""Scene, camera and render setup for Real City assets."""

from __future__ import annotations

import math

from .constants import RenderProfile


def _bpy():
    import bpy

    return bpy


def clear_scene(*, remove_orphans: bool = True) -> None:
    bpy = _bpy()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    if remove_orphans:
        for store in (bpy.data.materials, bpy.data.meshes, bpy.data.texts):
            for item in list(store):
                if item.users == 0:
                    store.remove(item)


def new_scene(name: str, *, make_active: bool = True):
    bpy = _bpy()
    scene = bpy.data.scenes.new(name)
    scene.unit_settings.system = "METRIC"
    if make_active and bpy.context.window:
        bpy.context.window.scene = scene
    return scene


def setup_isometric_camera(scene, profile: RenderProfile = RenderProfile()):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    data = bpy.data.cameras.new(profile.camera_name)
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    camera.location = (8, -8, math.sqrt(128) / math.sqrt(3))
    camera.rotation_euler = (-Vector(camera.location)).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = profile.sprite_size[0] * profile.tile_size * math.sqrt(2) / profile.ground_pixel_width
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = profile.sprite_size
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()

    target_y = 1 - profile.anchor[1] / profile.sprite_size[1]
    initial = world_to_camera_view(scene, camera, Vector((0, 0, 0))).y
    data.shift_y = 0.1
    delta = world_to_camera_view(scene, camera, Vector((0, 0, 0))).y - initial
    data.shift_y = (target_y - initial) * 0.1 / delta if delta else 0
    return camera


def setup_lighting(scene, *, prefix: str = "real_city"):
    import bpy
    from mathutils import Vector

    for name, pos, energy, size in (
        ("key", (-3, -5, 8), 1000, 5),
        ("fill", (5, 1, 6), 650, 5),
    ):
        light = bpy.data.lights.new(f"{prefix}_{name}", "AREA")
        light.energy = energy
        light.shape = "DISK"
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-Vector(obj.location)).to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.new(f"{prefix}_daylight")
    world.use_nodes = True
    background = next((node for node in world.node_tree.nodes if node.type == "BACKGROUND"), None)
    if background:
        background.inputs[0].default_value = (0.65, 0.75, 0.90, 1)
        background.inputs[1].default_value = 0.45
    scene.world = world


def setup_render(scene, profile: RenderProfile = RenderProfile()):
    scene.render.resolution_x, scene.render.resolution_y = profile.sprite_size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = profile.view_transform
    try:
        scene.render.engine = profile.render_engine
    except TypeError:
        pass
    if hasattr(scene, "cycles"):
        scene.cycles.samples = profile.samples
        scene.cycles.use_denoising = True


def configure_asset_scene(scene, profile: RenderProfile = RenderProfile(), *, light_prefix: str = "real_city"):
    setup_isometric_camera(scene, profile)
    setup_lighting(scene, prefix=light_prefix)
    setup_render(scene, profile)
    return scene


def write_text_note(name: str, content: str):
    bpy = _bpy()
    text = bpy.data.texts.new(name)
    text.write(content)
    return text
