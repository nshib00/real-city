"""Geometry helpers for Real City Blender generators."""

from __future__ import annotations

import math
from math import radians


def _bpy():
    import bpy

    return bpy


def _bmesh():
    import bmesh

    return bmesh


def _vector():
    from mathutils import Vector

    return Vector


def create_collection(name: str, parent=None):
    bpy = _bpy()
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def link_to(collection, obj):
    for item in list(obj.users_collection):
        item.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def apply_transform(obj, *, location: bool = False, rotation: bool = False, scale: bool = True):
    bpy = _bpy()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
    obj.select_set(False)
    return obj


def mesh(name: str, collection, verts, faces, material):
    bpy = _bpy()
    data = bpy.data.meshes.new(f"{name}_mesh")
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def box(name: str, collection, loc, size, material, *, bevel: float = 0.02, rotation=(0, 0, 0)):
    bmesh = _bmesh()
    bpy = _bpy()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vertex in bm.verts:
        for axis in range(3):
            vertex.co[axis] *= size[axis]
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.24), segments=1, affect="EDGES")
    data = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = rotation
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def cylinder(name: str, collection, loc, radius: float, depth: float, material, *, vertices: int = 12, rotation=(0, 0, 0)):
    bpy = _bpy()
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def sphere(name: str, collection, loc, scale, material, *, segments: int = 16, ring_count: int = 8):
    bpy = _bpy()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=ring_count, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    obj.data.materials.append(material)
    return link_to(collection, obj)


def cone(
    name: str,
    collection,
    loc,
    radius1: float,
    radius2: float,
    depth: float,
    material,
    *,
    vertices: int = 6,
    rotation=(0, 0, 0),
):
    bpy = _bpy()
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=loc,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return link_to(collection, obj)


def beam(name: str, collection, a, b, width: float, material):
    Vector = _vector()
    delta = Vector(b) - Vector(a)
    obj = box(name, collection, (Vector(a) + Vector(b)) / 2, (width, width, delta.length), material)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def flag(name: str, collection, loc, width: float, height: float, material):
    verts = [(0, 0, 0), (width, 0, height * 0.34), (0, 0, height)]
    obj = mesh(name, collection, verts, [(0, 1, 2)], material)
    obj.location = loc
    return obj


def gable_roof(name: str, collection, loc, size, material):
    width, depth, height = size
    x = width / 2
    y = depth / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (0, -y, height), (0, y, height)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    obj = mesh(name, collection, verts, faces, material)
    obj.location = loc
    return obj


def aeolian_crystal(name: str, collection, loc, radius: float, height: float, material):
    obj = cone(name, collection, loc, radius, radius * 0.18, height, material, vertices=6, rotation=(0, 0, radians(30)))
    return obj


def clean_meshes(collection):
    bpy = _bpy()
    bpy.context.view_layer.update()
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        obj.data.transform(obj.matrix_world)
        obj.matrix_world.identity()
        obj.data.calc_loop_triangles()
    bpy.context.view_layer.update()


def collection_triangle_count(collection) -> int:
    total = 0
    for obj in collection.all_objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            total += len(obj.data.loop_triangles)
    return total


def collection_bounds(collection):
    Vector = _vector()
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in collection.all_objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not points:
        return None
    return [[min(point[i] for point in points), max(point[i] for point in points)] for i in range(3)]
