"""Export, render and manifest helpers for Real City Blender assets."""

from __future__ import annotations

import json
from pathlib import Path

from .constants import ANCHOR, SPRITE_SIZE
from .geometry import collection_bounds, collection_triangle_count
from .paths import blender_path
from .state import select_collection_meshes, show_only, unhide_scene_collections


def _bpy():
    import bpy

    return bpy


def save_blend(path: str | Path) -> Path:
    bpy = _bpy()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(target))
    return target


def export_glb(path: str | Path, *, collection=None, use_selection: bool = False, export_extras: bool = True) -> Path:
    bpy = _bpy()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if collection is not None:
        use_selection = True
        select_collection_meshes(collection)
    bpy.ops.export_scene.gltf(
        filepath=blender_path(target),
        export_format="GLB",
        use_selection=use_selection,
        use_active_scene=True,
        export_extras=export_extras,
    )
    return target


def render_png(path: str | Path, *, scene=None) -> Path:
    bpy = _bpy()
    scene = scene or bpy.context.scene
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = blender_path(target)
    bpy.ops.render.render(write_still=True)
    return target


def export_state_assets(name: str, collection, output_dir: Path, *, render: bool = True, scene=None) -> dict:
    scene = scene or _bpy().context.scene
    show_only(name, scene=scene)
    glb = export_glb(output_dir / f"{name}.glb", collection=collection)
    png = render_png(output_dir / f"{name}.png", scene=scene) if render else None
    return {
        "id": name,
        "glb": str(glb),
        "png": str(png) if png else None,
        "triangles": collection_triangle_count(collection),
        "bounds": collection_bounds(collection),
    }


def export_lod_glbs(name: str, collection, output_dir: Path, lod_chain: list[dict], *, scene=None, lod_builder=None) -> list[dict]:
    """Export a per-state LOD chain.

    LOD0 is exported from the source collection. Lower LODs are exported from
    temporary mesh copies with a Decimate modifier, so the render collection is
    not mutated before PNG generation.
    """

    bpy = _bpy()
    scene = scene or bpy.context.scene
    records: list[dict] = []
    for lod in lod_chain:
        if lod.get("export") is False:
            continue
        lod_name = str(lod.get("name") or "LOD0")
        ratio = float(lod.get("ratio", 1.0))
        path = output_dir / f"{name}_{lod_name}.glb"
        if lod_name == "LOD0" or ratio >= 0.999:
            export_glb(path, collection=collection)
            triangles = collection_triangle_count(collection)
        else:
            temp = (lod_builder(lod_name) if lod_builder else
                    _copy_collection_for_lod(collection, f"{name}_{lod_name}_tmp", ratio))
            try:
                export_glb(path, collection=temp)
                triangles = collection_triangle_count(temp)
            finally:
                _remove_collection(temp)
        records.append({"name": lod_name, "ratio": ratio, "glb": str(path), "triangles": triangles})
    show_only(name, scene=scene)
    return records


def export_combined_glb(path: str | Path, *, scene=None) -> Path:
    scene = scene or _bpy().context.scene
    unhide_scene_collections(scene)
    return export_glb(path, use_selection=False)


def asset_item(name: str, level: int, state: str, directory: Path, collection) -> dict:
    return {
        "id": name,
        "level": level,
        "state": state,
        "glb": str(directory / f"{name}.glb"),
        "png": str(directory / f"{name}.png"),
        "triangles": collection_triangle_count(collection),
        "bounds": collection_bounds(collection),
    }


def write_generation_report(path: str | Path, report: dict) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def make_contact_sheet(
    image_paths: list[str | Path],
    output_path: str | Path,
    *,
    columns: int = 4,
    label_height: int = 28,
    background=(238, 240, 235, 255),
) -> Path:
    from PIL import Image, ImageDraw

    paths = [Path(path) for path in image_paths if Path(path).exists()]
    if not paths:
        raise ValueError("contact sheet requires at least one existing image")
    images = [Image.open(path).convert("RGBA") for path in paths]
    cell_w = max(image.width for image in images)
    cell_h = max(image.height for image in images) + label_height
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGBA", (cell_w * columns, cell_h * rows), background)
    draw = ImageDraw.Draw(sheet)
    for index, (path, image) in enumerate(zip(paths, images)):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        sheet.alpha_composite(image, (x + (cell_w - image.width) // 2, y))
        draw.text((x + 8, y + image.height + 6), path.stem, fill=(42, 38, 30, 255))
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    return target


def write_manifest(
    path: str | Path,
    *,
    asset_id: str,
    display_name: str,
    category: str,
    levels,
    states,
    items,
    source_blend: str | None = None,
    combined_glb: str | None = None,
    material_map: dict | None = None,
    extra: dict | None = None,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "asset_id": asset_id,
        "display_name": display_name,
        "category": category,
        "levels": list(levels),
        "states": list(states),
        "sprite": {"size": list(SPRITE_SIZE), "anchor": list(ANCHOR)},
        "source_blend": source_blend,
        "combined_glb": combined_glb,
        "material_map": material_map or {},
        "items": list(items),
    }
    if extra:
        manifest.update(extra)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _copy_collection_for_lod(collection, name: str, ratio: float):
    bpy = _bpy()
    temp = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(temp)
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        clone = obj.copy()
        clone.data = obj.data.copy()
        clone.name = f"{obj.name}_{name}"
        temp.objects.link(clone)
        # Decimating tiny closed meshes (roof wedges, five-sided stems) can
        # collapse their caps and produce invalid glTF primitives. They are
        # already cheaper than the decimator's overhead in the final LOD.
        if ratio < 0.999 and len(obj.data.polygons) > 16:
            modifier = clone.modifiers.new("real_city_lod_decimate", "DECIMATE")
            modifier.ratio = max(0.05, min(1.0, ratio))
            bpy.context.view_layer.objects.active = clone
            clone.select_set(True)
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except Exception:
                pass
            clone.select_set(False)
    bpy.context.view_layer.update()
    return temp


def _remove_collection(collection) -> None:
    bpy = _bpy()
    for obj in list(collection.objects):
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    bpy.data.collections.remove(collection)
