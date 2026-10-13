"""Validation helpers usable before and during Blender roundtrip checks."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from .paths import project_root


def glb_header(path: str | Path) -> dict:
    target = Path(path)
    raw = target.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise ValueError(f"Not a GLB file: {target}")
    version, total_length = struct.unpack_from("<II", raw, 4)
    json_length, json_type = struct.unpack_from("<II", raw, 12)
    if version != 2:
        raise ValueError(f"Unsupported GLB version {version}: {target}")
    if total_length != len(raw):
        raise ValueError(f"GLB length mismatch: {target}")
    if json_type != 0x4E4F534A:
        raise ValueError(f"Missing JSON chunk: {target}")
    doc = json.loads(raw[20 : 20 + json_length])
    return {
        "path": str(target),
        "version": version,
        "length": total_length,
        "meshes": len(doc.get("meshes", [])),
        "materials": len(doc.get("materials", [])),
        "nodes": len(doc.get("nodes", [])),
    }


def validate_manifest_files(manifest_path: str | Path) -> list[dict]:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = project_root(manifest_path)
    results = []
    for item in manifest.get("items", []):
        checks = {}
        for key in ("glb", "png"):
            value = item.get(key)
            if not value:
                checks[key] = False
                continue
            path = Path(value)
            if not path.is_absolute():
                path = root / value
            checks[key] = path.exists() and path.stat().st_size > 0
        results.append({"id": item.get("id"), **checks})
    return results


def roundtrip_import_glb(path: str | Path, *, collection_name: str | None = None) -> dict:
    """Import a GLB in Blender and return a small structural report.

    This function intentionally imports lazily so the module remains usable in
    normal Python quality gates. Call it only from Blender-enabled scripts.
    """

    import bpy

    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(target)

    before_objects = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(target))
    imported = [obj for obj in bpy.data.objects if obj not in before_objects]
    meshes = [obj for obj in imported if obj.type == "MESH"]

    collection = None
    if collection_name:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        for obj in imported:
            for current in list(obj.users_collection):
                current.objects.unlink(obj)
            collection.objects.link(obj)

    triangles = 0
    for obj in meshes:
        mesh = obj.data
        triangles += sum(len(poly.vertices) - 2 for poly in mesh.polygons)

    return {
        "path": str(target),
        "objects": len(imported),
        "meshes": len(meshes),
        "triangles": triangles,
        "materials": len({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}),
        "collection": collection.name if collection else None,
    }


def validate_glb_roundtrip(paths: list[str | Path]) -> list[dict]:
    results = []
    for index, path in enumerate(paths, start=1):
        result = roundtrip_import_glb(path, collection_name=f"roundtrip_{index:03d}")
        result["ok"] = result["meshes"] > 0 and result["triangles"] > 0
        results.append(result)
    return results
