"""Build visual villa prototypes 2–5 from the approved enlarged level-one test.

Run ``generate()`` in Blender with this repository on sys.path. These visual
levels are deliberately separate from the single catalog level-four villa.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy

from tools.assets.blender import build_villa_l01_test as base
from tools.assets.blender import build_villa_l01_v2_test as enlarged
from tools.assets.blender.real_city import export, geometry, materials
from tools.assets.blender.real_city.components import common, roofs, villa_decor
from tools.assets.blender.real_city.components import COMPONENT_LIBRARY_VERSION


OUTPUT = base.ROOT / "frontend/public/assets/buildings/housing/villa_levels_test"
SOURCE_REL = "frontend/public/assets/buildings/housing/villa_levels_test"
LEVELS = (2, 3, 4, 5)
BODY_AREA_FACTORS = {2: 1.0, 3: 1.05, 4: 1.05 * 1.03, 5: 1.05 * 1.03 * 1.03}
BODY_WIDTH = base.HOUSE_WIDTH * enlarged.SCALE_FROM_SAVED_VERSION
BODY_DEPTH = base.HOUSE_DEPTH * enlarged.SCALE_FROM_SAVED_VERSION
BODY_CENTRE_Y = 0.13 * base.HOUSE_SCALE * enlarged.SCALE_FROM_SAVED_VERSION


def _body_scale(level):
    return math.sqrt(BODY_AREA_FACTORS[level])


def _body_footprint(level):
    return {"width": BODY_WIDTH * _body_scale(level),
            "depth": BODY_DEPTH * _body_scale(level),
            "area": BODY_WIDTH * BODY_DEPTH * BODY_AREA_FACTORS[level],
            "factor_from_level_2": BODY_AREA_FACTORS[level]}


def _scale_base_house(collection, scale):
    """Grow the original house in plan while keeping the ground and garden fixed."""
    if scale == 1:
        return
    yard_parts = ("_stairs", "_mosaic", "_flower_arc", "_west_bed", "_garden_urn_",
                  "_garden_obelisk_", "_garden_lantern", "_side_basin")
    for obj in collection.all_objects:
        if not obj.name.startswith(f"{enlarged.ASSET_NAME}_") or any(part in obj.name for part in yard_parts):
            continue
        # base.build_scene already baked transforms into mesh coordinates.
        for vertex in obj.data.vertices:
            vertex.co.x *= scale
            vertex.co.y = BODY_CENTRE_Y + (vertex.co.y - BODY_CENTRE_Y) * scale
    bpy.context.view_layer.update()


def _box(name, collection, mats, location, size, role, bevel=0.012, rotation=(0, 0, 0)):
    return geometry.box(name, collection, location, size, common.mat(mats, role),
                        bevel=bevel, rotation=rotation)


def _materials():
    mats = materials.create_palette("MAT_villa_levels_test", overrides={
        "roof_coral": (0.58, 0.19, 0.10), "roof_gold": (0.78, 0.37, 0.09),
        "marble_white": (0.96, 0.96, 0.92), "marble_ivory": (0.88, 0.90, 0.88),
        "marble_vein": (0.72, 0.76, 0.76), "gilded_gold": (0.85, 0.63, 0.25),
    })
    for role in ("marble_white", "marble_ivory"):
        materials.set_input(materials.principled_node(mats[role]), "Roughness", 0.32)
    return mats


def _remove(collection, fragments):
    for obj in list(collection.all_objects):
        if any(fragment in obj.name for fragment in fragments):
            bpy.data.objects.remove(obj, do_unlink=True)


def _level_two(collection, mats, name, body_scale):
    # The broader portico is rebuilt rather than laid over the first version.
    _remove(collection, ("_column_", "_portico_", "_portico.", "_porch_slab", "_side_basin", "_garden_lantern"))
    front = BODY_CENTRE_Y - BODY_DEPTH * body_scale / 2
    _box(f"{name}_wide_porch", collection, mats, (0, front - 0.31, 0.155),
         (1.54 * body_scale, 0.78, 0.18), "marble_white")
    for side in (-1, 1):
        column_name = f"{name}_wide_column_{side}"
        column_x, column_y = side * 0.62 * body_scale, front - 0.48
        villa_decor.add_portico_fluted_column(column_name, collection, mats,
                                               (column_x, column_y, 0.225), height=1.08)
        if body_scale > 1:
            thickness = {3: 1.18, 4: 1.22, 5: 1.26}[int(name.split('_l')[1][:2])]
            for obj in collection.all_objects:
                if obj.name.startswith(column_name + "_"):
                    obj.location.x = column_x + (obj.location.x - column_x) * thickness
                    obj.location.y = column_y + (obj.location.y - column_y) * thickness
                    obj.scale.x *= thickness
                    obj.scale.y *= thickness
            if name.startswith("villa_l05_"):
                for band, z in enumerate((0.49, 0.71, 0.93, 1.15)):
                    geometry.cylinder(f"{column_name}_fine_gold_band_{band}", collection,
                                      (column_x, column_y, z), 0.11 * thickness + 0.006,
                                      0.012, common.mat(mats, "gilded_gold"), vertices=24)
    _box(f"{name}_wide_canopy", collection, mats, (0, front - 0.29, 1.50),
         (1.64 * body_scale, 0.82, 0.11), "marble_white")
    roofs.add_gable_roof(f"{name}_wide_portico_roof", collection, mats,
                         (0, front - 0.29, 1.54), (1.72 * body_scale, 0.86, 0.22), color_role="roof_gold")
    villa_decor.add_facade_cornice(f"{name}_wide_portico_cornice", collection, mats,
                                   (0, front - 0.72, 1.55), width=1.62 * body_scale)
    # Side terrace joins the right facade and rests on four stone feet.
    _box(f"{name}_terrace_deck", collection, mats, (1.34, 0.64, 0.20),
         (0.82, 0.93, 0.12), "marble_white")
    for x in (1.05, 1.63):
        for y in (0.28, 1.0):
            _box(f"{name}_terrace_foot_{x}_{y}", collection, mats, (x, y, 0.09),
                 (0.13, 0.13, 0.18), "stone_block")
    villa_decor.add_terrace_balustrade(f"{name}_terrace_rail", collection, mats,
                                       (1.35, 1.07, 0.27), length=0.70)
    villa_decor.add_terrace_sun_table(f"{name}_table", collection, mats, (1.32, 0.65, 0.26))
    villa_decor.add_curved_lounge_chair(f"{name}_chair", collection, mats, (1.62, 0.42, 0.26))
    villa_decor.add_windleaf_pilaster(f"{name}_pilaster", collection, mats,
                                      (0.98, 0.54, 0.25), height=0.75)


def _level_three(collection, mats, name):
    # The former level-three attic is now part of the level-two silhouette.
    _box(f"{name}_attic_wall", collection, mats, (0.47, 0.68, 1.83),
         (0.77, 0.64, 0.57), "marble_ivory")
    roofs.add_gable_roof(f"{name}_attic_roof", collection, mats,
                         (0.47, 0.68, 2.12), (0.93, 0.82, 0.34), color_role="roof_coral")
    _box(f"{name}_attic_window_frame", collection, mats, (0.47, 0.335, 1.89),
         (0.37, 0.07, 0.36), "marble_white")
    _box(f"{name}_attic_window_glass", collection, mats, (0.47, 0.287, 1.89),
         (0.28, 0.03, 0.27), "glass_cyan")
    villa_decor.add_arch_window_crown(f"{name}_attic_crown", collection, mats,
                                      (0.47, 0.26, 2.12), width=0.40)
    villa_decor.add_ridge_leaf_crest(f"{name}_attic_crest", collection, mats,
                                     (0.47, 0.68, 2.47))
    # Low original garden fence with a visible gate on the side approach.
    for x in (1.13, 1.62):
        villa_decor.add_villa_gate_post(f"{name}_gate_{x}", collection, mats,
                                        (x, -1.18, 0.065))
    for y in (-1.32, -1.05):
        _box(f"{name}_garden_fence_{y}", collection, mats, (1.61, y, 0.19),
             (0.07, 0.28, 0.25), "marble_white")
    villa_decor.add_garden_lattice(f"{name}_garden_lattice", collection, mats,
                                   (-1.42, 0.62, 0.065), width=0.43)


def _tiled_roof(collection, mats, name, centre, size):
    x0, y0, z0 = centre
    width, depth, rise = size
    roofs.add_gable_roof(name, collection, mats, centre, size, color_role="roof_coral")
    pitch = math.atan2(rise, width / 2)
    for side in (-1, 1):
        for row in range(4):
            x = x0 + side * (row + 0.5) * width / 8
            z = z0 + rise * (1 - abs(x - x0) / (width / 2)) + 0.031
            for column in range(5):
                y = y0 - depth * 0.46 + (column + 0.5) * depth * 0.92 / 5
                _box(f"{name}_tile_{side}_{row}_{column}", collection, mats,
                     (x, y, z), (width / 8 + 0.012, depth * 0.92 / 5 + 0.006, 0.035),
                     "roof_gold" if (row + column) % 6 == 0 else "roof_coral",
                     bevel=0.006, rotation=(0, side * pitch, 0))
        _box(f"{name}_copper_eave_{side}", collection, mats,
             (x0 + side * width * 0.48, y0, z0 + 0.038),
             (0.055, depth + 0.02, 0.06), "copper")
    _box(f"{name}_gold_ridge", collection, mats,
         (x0, y0, z0 + rise + 0.045), (0.11, depth + 0.02, 0.072), "roof_gold")


def _replace_original_roof(collection):
    _remove(collection, ("villa_l01_active_v2_main_", "villa_l01_active_v2_tile_",
                         "villa_l01_active_v2_ridge_", "villa_l01_active_v2_copper_eave_"))


def _upper_window(collection, mats, name, x, y, z, *, width=0.38):
    common.add_window(name, collection, mats, (x, y, z),
                      (width, 0.065, 0.40), warm=False, frame_role="marble_white")
    villa_decor.add_gilded_window_surround(f"{name}_rich", collection, mats,
                                           (x, y - 0.055, z), width=width + 0.13, height=0.52)
    _box(f"{name}_sill", collection, mats, (x, y - 0.09, z - 0.25),
         (width + 0.21, 0.17, 0.055), "marble_white")


def _balcony(collection, mats, name, *, gabled, body_scale):
    # The roof columns begin on the second-floor balcony, not on the ground.
    side_wall_x = BODY_WIDTH * body_scale / 2
    x = 1.32 + (side_wall_x - BODY_WIDTH / 2)
    floor_z = 1.69
    _box(f"{name}_balcony_slab", collection, mats, (x, -0.03, floor_z),
         (0.67, 0.89, 0.12), "marble_white")
    for y in (-0.35, 0.27):
        # Cantilever braces connect the slab to the wall without ground columns.
        geometry.beam(f"{name}_balcony_brace_{y}", collection,
                      (side_wall_x - 0.04, y, 1.42), (x + 0.16, y, 1.63),
                      0.085, common.mat(mats, "marble_white"))
        villa_decor.add_portico_fluted_column(f"{name}_balcony_roof_column_{y}", collection,
                                               mats, (x + 0.16, y, 1.75), height=0.61)
    villa_decor.add_balcony_copper_rail(f"{name}_balcony_rail", collection, mats,
                                        (x, -0.47, 1.75), length=0.53)
    _box(f"{name}_balcony_door_frame", collection, mats, (side_wall_x + 0.04, -0.03, 2.10),
         (0.065, 0.40, 0.55), "marble_white")
    _box(f"{name}_balcony_door_glass", collection, mats, (side_wall_x + 0.085, -0.03, 2.10),
         (0.026, 0.32, 0.47), "glass_cyan")
    villa_decor.add_balcony_flower_box(f"{name}_balcony_flowers", collection, mats,
                                       (x + 0.16, -0.03, 1.80), width=0.36)
    if gabled:
        _tiled_roof(collection, mats, f"{name}_balcony_gable", (x, -0.03, 2.61),
                    (0.74, 0.96, 0.30))
        _box(f"{name}_balcony_gable_wall", collection, mats, (x, -0.515, 2.69),
             (0.60, 0.06, 0.18), "marble_ivory")
        common.add_window(f"{name}_balcony_gable_window", collection, mats,
                          (x, -0.56, 2.72), (0.15, 0.045, 0.14),
                          warm=False, frame_role="gilded_gold", shape="round")
    else:
        _box(f"{name}_balcony_flat_roof", collection, mats, (x, -0.03, 2.60),
             (0.78, 0.97, 0.12), "marble_white")
        for side in (-1, 1):
            _box(f"{name}_balcony_roof_gold_{side}", collection, mats,
                 (x + side * 0.35, -0.03, 2.68), (0.035, 0.99, 0.045), "gilded_gold")


def _level_rear_second_floor(collection, mats, name, body_scale):
    _replace_original_roof(collection)
    _remove(collection, (f"{name}_attic_",))
    rear_y = BODY_CENTRE_Y + (0.70 - BODY_CENTRE_Y) * body_scale
    front_roof_y = BODY_CENTRE_Y + (-0.40 - BODY_CENTRE_Y) * body_scale
    _tiled_roof(collection, mats, f"{name}_front_slope", (0, front_roof_y, 1.67),
                (2.37 * body_scale, 1.08 * body_scale, 0.59))
    _box(f"{name}_rear_upper_shell", collection, mats, (0, rear_y, 2.02),
         (2.03 * body_scale, 1.04 * body_scale, 0.90), "marble_ivory", bevel=0.034)
    _box(f"{name}_rear_upper_right_cladding", collection, mats,
         (1.03 * body_scale, rear_y, 2.03),
         (0.055, 1.05 * body_scale, 0.83), "marble_white")
    _tiled_roof(collection, mats, f"{name}_rear_upper", (0, rear_y, 2.47),
                (2.31 * body_scale, 1.22 * body_scale, 0.46))
    _upper_window(collection, mats, f"{name}_rear_upper_window",
                  -0.35 * body_scale, rear_y + 0.545 * body_scale, 2.02)
    villa_decor.add_facade_cornice(f"{name}_rear_upper_cornice", collection, mats,
                                   (0, rear_y + 0.56 * body_scale, 2.44),
                                   width=1.96 * body_scale)
    _balcony(collection, mats, name, gabled=False, body_scale=body_scale)


def _level_full_second_floor(collection, mats, name, body_scale):
    _replace_original_roof(collection)
    _remove(collection, (f"{name}_attic_",))
    upper_front = BODY_CENTRE_Y - BODY_DEPTH * body_scale / 2
    _box(f"{name}_full_upper_shell", collection, mats, (0, BODY_CENTRE_Y, 2.05),
         (BODY_WIDTH * body_scale, BODY_DEPTH * body_scale, 1.00), "marble_ivory", bevel=0.039)
    _box(f"{name}_upper_front_cladding", collection, mats, (0, upper_front - 0.02, 2.07),
         (1.97 * body_scale, 0.055, 0.91), "marble_white")
    _box(f"{name}_upper_right_cladding", collection, mats,
         (BODY_WIDTH * body_scale / 2 + 0.023, BODY_CENTRE_Y, 2.07),
         (0.055, 1.65 * body_scale, 0.91), "marble_white")
    for x in (-0.55, 0.55):
        _upper_window(collection, mats, f"{name}_front_upper_window_{x}",
                      x * body_scale, upper_front - 0.08, 2.08)
        villa_decor.add_balcony_flower_box(f"{name}_upper_flowers_{x}", collection, mats,
                                           (x * body_scale, upper_front - 0.18, 1.79), width=0.35)
    _tiled_roof(collection, mats, f"{name}_full_upper", (0, BODY_CENTRE_Y, 2.55),
                (2.38 * body_scale, 2.06 * body_scale, 0.55))
    villa_decor.add_facade_cornice(f"{name}_upper_cornice", collection, mats,
                                   (0, upper_front - 0.11, 2.53), width=2.05 * body_scale)
    _balcony(collection, mats, name, gabled=True, body_scale=body_scale)
    villa_decor.add_wind_basin(f"{name}_fountain_basin", collection, mats,
                               (-1.36, 0.15, 0.065))
    villa_decor.add_fountain_spout(f"{name}_fountain", collection, mats,
                                   (-1.36, 0.15, 0.18))
    for x, y in ((-0.97, -1.14), (0.97, -1.14)):
        villa_decor.add_courtyard_lantern(f"{name}_formal_lantern_{x}", collection, mats,
                                          (x, y, 0.065))


def _level_five(collection, mats, name):
    # A side pavilion adds occupied ground area without moving the tile or camera.
    _box(f"{name}_left_pavilion_foundation", collection, mats, (-1.18, 0.35, 0.13),
         (0.69, 1.30, 0.21), "stone_block")
    _box(f"{name}_left_pavilion_shell", collection, mats, (-1.18, 0.35, 1.36),
         (0.65, 1.26, 2.25), "marble_white", bevel=0.030)
    _tiled_roof(collection, mats, f"{name}_left_pavilion_roof", (-1.18, 0.35, 2.53),
                (0.85, 1.48, 0.48))
    for z in (0.90, 2.02):
        _upper_window(collection, mats, f"{name}_pavilion_window_{z}",
                      -1.18, -0.31, z, width=0.27)
    _box(f"{name}_pavilion_gold_course", collection, mats, (-1.18, -0.32, 1.49),
         (0.61, 0.055, 0.045), "gilded_gold")
    # Two roof crests, gilded seams and an ornamental dormer foreshadow a palace.
    for x, y in ((-0.75, 0.78), (0.75, 0.78), (0, -0.68)):
        z = 2.55 + 0.55 * (1 - abs(x) / 1.19) + 0.05
        villa_decor.add_ridge_leaf_crest(f"{name}_roof_crest_{x}_{y}", collection, mats,
                                         (x, y, z))
    for x in (-0.38, 0.38):
        _box(f"{name}_gold_roof_seam_{x}", collection, mats,
             (x, 0.13, 2.55 + 0.55 * (1 - abs(x) / 1.19) + 0.04),
             (0.028, 1.90, 0.028), "gilded_gold")
    _box(f"{name}_central_dormer_wall", collection, mats, (0, -0.58, 2.89),
         (0.45, 0.12, 0.34), "marble_white")
    common.add_window(f"{name}_central_dormer_window", collection, mats,
                      (0, -0.66, 2.91), (0.18, 0.05, 0.18),
                      warm=False, frame_role="gilded_gold", shape="round")
    _tiled_roof(collection, mats, f"{name}_central_dormer_roof", (0, -0.55, 3.06),
                (0.57, 0.40, 0.24))
    _box(f"{name}_chimney", collection, mats, (-0.81, 0.70, 2.96),
         (0.20, 0.20, 0.46), "marble_white")
    villa_decor.add_chimney_louver_crown(f"{name}_chimney_crown", collection, mats,
                                         (-0.81, 0.70, 3.19))
    villa_decor.add_copper_gutter_spout(f"{name}_downspout", collection, mats,
                                        (0.98, 0.99, 1.38), drop=1.26)
    villa_decor.add_eave_wind_chime(f"{name}_wind_chime", collection, mats,
                                    (-1.36, 0.92, 2.50), drop=0.22)


def build_scene(level):
    if level not in LEVELS:
        raise ValueError(level)
    name = f"villa_l{level:02d}_active"
    with enlarged._variant_settings():
        scene, collection = base.build_scene(architecture_scale=enlarged.SCALE_FROM_SAVED_VERSION)
    scene.name = f"villa_l{level:02d}_active_test"
    collection.name = name
    mats = _materials()
    body_scale = _body_scale(level)
    _scale_base_house(collection, body_scale)
    _level_two(collection, mats, name, body_scale)
    _level_three(collection, mats, name)
    if level == 3:
        _level_rear_second_floor(collection, mats, name, body_scale)
    elif level >= 4:
        _level_full_second_floor(collection, mats, name, body_scale)
    if level >= 5:
        _level_five(collection, mats, name)
    for obj in collection.all_objects:
        obj["real_city_visual_level"] = level
        obj["real_city_state"] = "active"
        obj["component_library_version"] = COMPONENT_LIBRARY_VERSION
        obj["real_city_body_area_factor"] = BODY_AREA_FACTORS[level]
    geometry.clean_meshes(collection)
    return scene, collection


def preview(level=3):
    scene, _ = build_scene(level)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "preview" / f"villa_l{level:02d}_active.png"
    export.render_png(path, scene=scene)
    print("VILLA_LEVEL_PREVIEW_COMPLETE", path)
    return path


def generate(levels=LEVELS):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT / "manifest.json"
    report_path = OUTPUT / "generation-report.json"
    old_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    old_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    items = {item["level"]: item for item in old_manifest.get("items", [])}
    reports = {item["level"]: item for item in old_report.get("items", [])}
    for level in levels:
        scene, collection = build_scene(level)
        name = f"villa_l{level:02d}_active"
        export.render_png(OUTPUT / f"{name}.png", scene=scene)
        lods = export.export_lod_glbs(name, collection, OUTPUT,
                                      [{"name": "LOD0", "ratio": 1.0},
                                       {"name": "LOD1", "ratio": 0.48},
                                       {"name": "LOD2", "ratio": 0.22}], scene=scene)
        bpy.context.preferences.filepaths.save_version = 0
        export.save_blend(OUTPUT / f"{name}.blend")
        item = {"id": name, "level": level, "state": "active",
                "png": f"{SOURCE_REL}/{name}.png",
                "glb": f"{SOURCE_REL}/{name}_LOD0.glb",
                "lods": [{**lod, "glb": f"{SOURCE_REL}/{name}_{lod['name']}.glb"} for lod in lods],
                "triangles": lods[0]["triangles"], "bounds": geometry.collection_bounds(collection),
                "body_footprint": _body_footprint(level)}
        items[level] = item
        reports[level] = {"level": level, "state": "active", "triangles": item["triangles"],
                          "lods": lods, "bounds": item["bounds"],
                          "body_footprint": item["body_footprint"],
                          "objects": len(collection.all_objects)}
        print("VILLA_LEVEL_COMPLETE", level, lods[0]["triangles"], flush=True)
    completed_levels = sorted(items)
    for level in completed_levels:
        items[level]["body_footprint"] = _body_footprint(level)
        reports[level]["body_footprint"] = _body_footprint(level)
    export.write_manifest(manifest_path, asset_id="villa",
                          display_name="Вилла (тестовые визуальные варианты)",
                          category="housing", levels=completed_levels, states=["active"],
                          items=[items[level] for level in completed_levels],
                          source_blend=None,
                          material_map={"stone": "мраморные стены, колонны и террасы",
                                        "glass": "фасадные окна, мансарда и балкон"},
                          extra={"prototype": True, "component_library_version": COMPONENT_LIBRARY_VERSION,
                                 "catalog_level_policy": "visual_prototype",
                                 "lod_policy": {"chain": [
                                     {"name": "LOD0", "triangle_budget": {"min": 1800, "max": 38000}},
                                     {"name": "LOD1", "triangle_budget": {"min": 850, "max": 20000}},
                                     {"name": "LOD2", "triangle_budget": {"min": 400, "max": 10000}},
                                 ]}})
    report = {"asset_id": "villa", "levels": completed_levels, "states": ["active"],
              "prototype": True, "generator": "tools/assets/blender/build_villa_levels_test.py",
              "source_variant": "frontend/public/assets/buildings/housing/villa_v2_test",
              "material_map": {"stone": "мраморные стены, колонны и террасы",
                               "glass": "фасадные окна, мансарда и балкон"},
              "component_library_version": COMPONENT_LIBRARY_VERSION,
              "items": [reports[level] for level in completed_levels]}
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        export.make_contact_sheet([OUTPUT / f"villa_l{level:02d}_active.png" for level in completed_levels],
                                  OUTPUT / "villa_levels_contact_sheet.png", columns=4)
    except ModuleNotFoundError as exc:
        if exc.name != "PIL":
            raise
        print("VILLA_CONTACT_SHEET_REQUIRES_PIL", flush=True)
    print("VILLA_LEVELS_TEST_COMPLETE", OUTPUT, flush=True)
    return report


if __name__ == "__main__":
    generate()
