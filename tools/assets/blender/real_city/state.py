"""Collection visibility and state selection helpers."""

from __future__ import annotations


def _bpy():
    import bpy

    return bpy


def state_name(asset_id: str, level: int, state: str) -> str:
    return f"{asset_id}_l{level:02d}_{state}"


def hide_all(collections) -> None:
    for collection in collections:
        collection.hide_render = True
        collection.hide_viewport = True


def show_only(name: str, *, scene=None):
    bpy = _bpy()
    scene = scene or bpy.context.scene
    selected = None
    for collection in scene.collection.children:
        visible = collection.name == name
        collection.hide_render = not visible
        collection.hide_viewport = not visible
        if visible:
            selected = collection
    bpy.context.view_layer.update()
    return selected


def select_collection_meshes(collection) -> int:
    bpy = _bpy()
    bpy.ops.object.select_all(action="DESELECT")
    count = 0
    for obj in collection.all_objects:
        if obj.type == "MESH":
            obj.select_set(True)
            count += 1
    return count


def unhide_scene_collections(scene=None) -> None:
    bpy = _bpy()
    scene = scene or bpy.context.scene
    for collection in scene.collection.children:
        collection.hide_render = False
        collection.hide_viewport = False
    bpy.context.view_layer.update()
