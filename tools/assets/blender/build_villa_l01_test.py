"""Build the level-one active villa visual prototype in an isolated test folder.

Run from Windows Blender with access to the WSL project UNC path, or call
``generate()`` through Blender MCP. This is a visual prototype, not game data.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy

from tools.assets.blender.real_city import export, geometry, ground, materials, scene
from tools.assets.blender.real_city import components
from tools.assets.blender.real_city.components import common, foundations, landscaping, roofs, villa_decor
from tools.assets.blender.real_city.constants import RenderProfile
from tools.assets.blender.real_city.constants import DEFAULT_TILE_SIZE


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "frontend" / "public" / "assets" / "buildings" / "housing" / "villa_test"
ASSET_NAME = "villa_l01_active"
SOURCE_REL = "frontend/public/assets/buildings/housing/villa_test"
ORIGINAL_WIDTH = 1.72
ORIGINAL_DEPTH = 1.48
FOOTPRINT_AREA_MULTIPLIER = 1.20
HOUSE_SCALE = math.sqrt(FOOTPRINT_AREA_MULTIPLIER)
HOUSE_WIDTH = ORIGINAL_WIDTH * HOUSE_SCALE
HOUSE_DEPTH = ORIGINAL_DEPTH * HOUSE_SCALE
FOOTPRINT_PERCENT_BEFORE = ORIGINAL_WIDTH * ORIGINAL_DEPTH / DEFAULT_TILE_SIZE**2 * 100
FOOTPRINT_PERCENT_AFTER = HOUSE_WIDTH * HOUSE_DEPTH / DEFAULT_TILE_SIZE**2 * 100


def _box(name, collection, mats, loc, size, role, *, bevel=0.012, rotation=(0, 0, 0)):
    return geometry.box(name, collection, loc, size, common.mat(mats, role), bevel=bevel, rotation=rotation)


def _add_shell(collection, mats):
    """A pale stone home: real stone mass and glazing, not decorative stand-ins."""
    name = ASSET_NAME
    width, depth, centre_y = HOUSE_WIDTH, HOUSE_DEPTH, 0.13 * HOUSE_SCALE
    front_y = centre_y - depth / 2
    foundations.add_foundation(f"{name}_base", collection, mats, width=width, depth=depth,
                               height="low", thickness="medium", material="stone_block",
                               loc=(0, centre_y, 0.085))
    # Pale polished marble and narrow veins read as a richer material than stone.
    _box(f"{name}_marble_core", collection, mats, (0, centre_y, 0.80 * HOUSE_SCALE),
         (width, depth, 1.18 * HOUSE_SCALE), "marble_ivory", bevel=0.040)
    _box(f"{name}_front_marble_cladding", collection, mats, (0, front_y - 0.018, 0.86 * HOUSE_SCALE),
         (width - 0.12, 0.045, 0.99 * HOUSE_SCALE), "marble_white", bevel=0.018)
    _box(f"{name}_right_marble_cladding", collection, mats, (width / 2 + 0.018, centre_y, 0.86 * HOUSE_SCALE),
         (0.045, depth - 0.10, 0.99 * HOUSE_SCALE), "marble_white", bevel=0.018)
    for z in (0.30, 1.44):
        _box(f"{name}_front_gilded_course_{z}", collection, mats,
             (0, front_y - 0.058, z), (width - 0.10, 0.028, 0.025),
             "gilded_gold", bevel=0.004)
        _box(f"{name}_side_gilded_course_{z}", collection, mats,
             (width / 2 + 0.058, centre_y, z),
             (0.028, depth - 0.10, 0.025), "gilded_gold", bevel=0.004)
    for y in (centre_y - 0.48, centre_y + 0.47):
        villa_decor.add_marble_wall_inlay(f"{name}_right_veined_panel_{y:.2f}",
                                          collection, mats,
                                          (width / 2 + 0.046, y, 1.04),
                                          width=0.29, height=0.37, side=True)
    for side in (-1, 1):
        for row in range(7):
            _box(f"{name}_front_quoin_{side}_{row}", collection, mats,
                 (side * (width / 2 - 0.035), front_y - 0.065,
                  (0.29 + row * 0.145) * HOUSE_SCALE),
                 (0.18, 0.095, 0.12 * HOUSE_SCALE),
                 "marble_ivory" if row % 2 else "marble_white", bevel=0.009)
        # Clear blue glass is a structural part of the villa facade.
        window_x = side * width * 0.345
        window_z = 0.90 * HOUSE_SCALE
        common.add_window(f"{name}_front_window_{side}", collection, mats,
                          (window_x, front_y - 0.062, window_z),
                          (0.35, 0.055, 0.47), warm=False, frame_role="marble_white")
        villa_decor.add_gilded_window_surround(f"{name}_rich_front_window_{side}",
                                                collection, mats,
                                                (window_x, front_y - 0.115, window_z),
                                                width=0.35, height=0.47)
        _box(f"{name}_sill_{side}", collection, mats,
             (window_x, front_y - 0.105, window_z - 0.29),
             (0.48, 0.16, 0.060), "marble_white", bevel=0.009)
        villa_decor.add_balcony_flower_box(f"{name}_front_flower_box_{side}",
                                            collection, mats,
                                            (window_x, front_y - 0.18,
                                             window_z - 0.42), width=0.40)
    # A window on the visible +X side adds depth in the fixed isometric view.
    side_x = width / 2 + 0.055
    side_window_z = 0.90 * HOUSE_SCALE
    _box(f"{name}_side_window_frame", collection, mats, (side_x, 0.19, side_window_z),
         (0.055, 0.54, 0.55), "marble_white", bevel=0.009)
    _box(f"{name}_side_window_glass", collection, mats,
         (side_x + 0.034, 0.19, side_window_z),
         (0.023, 0.44, 0.45), "glass_cyan", bevel=0.005)
    _box(f"{name}_side_window_mullion", collection, mats,
         (side_x + 0.052, 0.19, side_window_z),
         (0.018, 0.025, 0.47), "marble_white", bevel=0.003)
    villa_decor.add_gilded_window_surround(f"{name}_rich_side_window", collection,
                                            mats, (side_x + 0.058, 0.19, side_window_z),
                                            width=0.44, height=0.45, side=True)
    _box(f"{name}_side_window_sill", collection, mats,
         (side_x + 0.015, 0.19, side_window_z - 0.32),
         (0.15, 0.64, 0.060), "marble_white", bevel=0.008)
    common.add_door(f"{name}_entry", collection, mats,
                    (0, front_y - 0.065, 0.66 * HOUSE_SCALE),
                    (0.55, 0.10, 0.88), material_role="elite_plank", planked=False)
    villa_decor.add_gilded_entry_portal(f"{name}_grand_entry", collection, mats,
                                         (0, front_y - 0.115, 0.66 * HOUSE_SCALE),
                                         width=0.55, height=0.88)
    villa_decor.add_door_wind_medallion(f"{name}_door_medallion", collection,
                                        mats, (0, front_y - 0.135, 0.84))
    for side in (-1, 1):
        _box(f"{name}_door_gold_inlay_{side}", collection, mats,
             (side * 0.16, front_y - 0.125, 0.71),
             (0.018, 0.018, 0.51), "gilded_gold", bevel=0.003)
    villa_decor.add_transom_sunburst(f"{name}_transom", collection, mats,
                                     (0, front_y - 0.19, 1.30))
    villa_decor.add_facade_cornice(f"{name}_cornice", collection, mats,
                                   (0, front_y - 0.015, 1.50), width=width)
    return width, depth, centre_y, front_y


def _add_roof(collection, mats, width, depth, centre_y):
    name = ASSET_NAME
    roof_width, roof_depth, roof_z, rise = ((ORIGINAL_WIDTH + 0.25) * HOUSE_SCALE,
                                            (ORIGINAL_DEPTH + 0.24) * HOUSE_SCALE,
                                            1.39 * HOUSE_SCALE, 0.49 * HOUSE_SCALE)
    roofs.add_gable_roof(f"{name}_main", collection, mats, (0, centre_y, roof_z),
                         (roof_width, roof_depth, rise), color_role="roof_coral")
    pitch = math.atan2(rise, roof_width / 2)
    tile_rows, tile_columns = 4, 6
    for side in (-1, 1):
        for row in range(tile_rows):
            x = side * (row + 0.5) * roof_width / (tile_rows * 2)
            z = roof_z + rise * (1 - abs(x) / (roof_width / 2)) + 0.031
            for column in range(tile_columns):
                y = centre_y - roof_depth * 0.46 + (column + 0.5) * roof_depth * 0.92 / tile_columns
                role = "roof_gold" if (row + column) % 5 == 0 else "roof_coral"
                _box(f"{name}_tile_{side:+d}_{row:02d}_{column:02d}", collection, mats,
                     (x, y, z), (roof_width / (tile_rows * 2) + 0.015, roof_depth * 0.92 / tile_columns + 0.006, 0.035),
                     role, bevel=0.007, rotation=(0, side * pitch, 0))
    for column in range(9):
        y = centre_y - roof_depth / 2 + (column + 0.5) * roof_depth / 9
        _box(f"{name}_ridge_{column:02d}", collection, mats,
             (0, y, roof_z + rise + 0.047), (0.11, roof_depth / 9 + 0.006, 0.075),
             "roof_gold", bevel=0.013)
    for side in (-1, 1):
        _box(f"{name}_copper_eave_{side}", collection, mats,
             (side * roof_width * 0.48, centre_y, roof_z + 0.038),
             (0.057, roof_depth + 0.03, 0.065), "copper", bevel=0.008)


def _add_entrance(collection, mats, front_y):
    name = ASSET_NAME
    # Porch and columns have deliberate contact with the grass, stone platform and canopy.
    _box(f"{name}_porch_slab", collection, mats,
         (0, front_y - 0.29, 0.155), (1.28, 0.72, 0.18), "marble_white", bevel=0.018)
    villa_decor.add_ceremonial_stair(f"{name}_stairs", collection, mats,
                                     (0, front_y - 0.81, 0.065), width=0.88)
    for side in (-1, 1):
        villa_decor.add_portico_fluted_column(f"{name}_column_{side}", collection, mats,
                                               (side * 0.47, front_y - 0.49, 0.225), height=1.08)
    canopy_y = front_y - 0.29
    _box(f"{name}_portico_ceiling", collection, mats,
         (0, canopy_y, 1.50), (1.29, 0.76, 0.11), "marble_white", bevel=0.016)
    roofs.add_gable_roof(f"{name}_portico", collection, mats,
                         (0, canopy_y, 1.54), (1.36, 0.81, 0.20), color_role="roof_gold")
    _box(f"{name}_portico_front_fascia", collection, mats,
         (0, canopy_y - 0.42, 1.55), (1.30, 0.09, 0.11), "marble_white", bevel=0.010)
    for side in (-1, 1):
        _box(f"{name}_portico_fascia_inlay_{side}", collection, mats,
             (side * 0.40, canopy_y - 0.473, 1.55),
             (0.31, 0.016, 0.025), "gilded_gold", bevel=0.003)
    _box(f"{name}_portico_fascia_sun", collection, mats,
         (0, canopy_y - 0.477, 1.55), (0.10, 0.021, 0.065),
         "gilded_gold", bevel=0.008)


def _add_yard(collection, mats):
    name = ASSET_NAME
    # The richer forecourt keeps a clear central approach to the door.
    villa_decor.add_courtyard_sun_mosaic(f"{name}_mosaic", collection, mats,
                                          (0, -1.50, 0.105))
    villa_decor.add_arc_flower_bed(f"{name}_flower_arc", collection, mats,
                                   (1.25, -0.68, 0.065))
    landscaping.add_flower_bed(f"{name}_west_bed", collection, mats,
                                (-1.25, -0.70, 0.065), style="round")
    for side in (-1, 1):
        villa_decor.add_gilded_urn(f"{name}_garden_urn_{side}", collection, mats,
                                    (side * 1.23, -1.18, 0.065))
        villa_decor.add_garden_sun_obelisk(f"{name}_garden_obelisk_{side}",
                                            collection, mats,
                                            (side * 1.45, 0.78, 0.065))
    villa_decor.add_courtyard_lantern(f"{name}_garden_lantern", collection,
                                       mats, (1.55, -0.18, 0.065))
    villa_decor.add_wind_basin(f"{name}_side_basin", collection, mats,
                               (1.42, 0.22, 0.065))


def build_scene(*, architecture_scale=1.0):
    scene.clear_scene()
    asset_scene = bpy.context.scene
    asset_scene.name = "villa_l01_active_test"
    profile = RenderProfile(samples=24)
    scene.configure_asset_scene(asset_scene, profile, light_prefix="villa_l01_test")
    mats = materials.create_palette("MAT_villa_l01_test", overrides={
        "roof_coral": (0.58, 0.19, 0.10),
        "roof_gold": (0.78, 0.37, 0.09),
        "marble_white": (0.96, 0.96, 0.92),
        "marble_ivory": (0.88, 0.90, 0.88),
        "marble_vein": (0.72, 0.76, 0.76),
        "gilded_gold": (0.85, 0.63, 0.25),
    })
    for role in ("marble_white", "marble_ivory"):
        materials.set_input(materials.principled_node(mats[role]), "Roughness", 0.32)
    materials.set_input(materials.principled_node(mats["gilded_gold"]), "Metallic", 0.45)
    collection = geometry.create_collection(ASSET_NAME)
    ground.add_ground_tile(collection, mats, prefix="villa", include_path=True)
    ground_objects = set(collection.all_objects)
    dimensions = _add_shell(collection, mats)
    _add_roof(collection, mats, *dimensions[:3])
    _add_entrance(collection, mats, dimensions[3])
    if architecture_scale != 1.0:
        for obj in collection.all_objects:
            if obj in ground_objects:
                continue
            obj.location *= architecture_scale
            obj.scale *= architecture_scale
        bpy.context.view_layer.update()
    _add_yard(collection, mats)
    for obj in collection.all_objects:
        obj["real_city_asset"] = "villa"
        obj["real_city_visual_level"] = 1
        obj["real_city_state"] = "active"
        obj["component_library_version"] = components.COMPONENT_LIBRARY_VERSION
    geometry.clean_meshes(collection)
    return asset_scene, collection


def preview(*, architecture_scale=1.0):
    asset_scene, collection = build_scene(architecture_scale=architecture_scale)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "preview" / f"{ASSET_NAME}.png"
    export.render_png(target, scene=asset_scene)
    print("VILLA_L01_ACTIVE_PREVIEW_COMPLETE", str(target), len(collection.all_objects))
    return target


def generate(*, architecture_scale=1.0):
    asset_scene, collection = build_scene(architecture_scale=architecture_scale)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    export.render_png(OUTPUT / f"{ASSET_NAME}.png", scene=asset_scene)
    lods = export.export_lod_glbs(ASSET_NAME, collection, OUTPUT,
                                 [{"name": "LOD0", "ratio": 1.0},
                                  {"name": "LOD1", "ratio": 0.48},
                                  {"name": "LOD2", "ratio": 0.22}], scene=asset_scene)
    bpy.context.preferences.filepaths.save_version = 0
    export.save_blend(OUTPUT / f"{ASSET_NAME}.blend")
    item = {
        "id": ASSET_NAME, "level": 1, "state": "active",
        "png": f"{SOURCE_REL}/{ASSET_NAME}.png",
        "glb": f"{SOURCE_REL}/{ASSET_NAME}_LOD0.glb",
        "lods": [{**lod, "glb": f"{SOURCE_REL}/{ASSET_NAME}_{lod['name']}.glb"} for lod in lods],
        "triangles": lods[0]["triangles"],
        "bounds": geometry.collection_bounds(collection),
    }
    export.write_manifest(OUTPUT / "manifest.json", asset_id="villa", display_name="Вилла (тест)",
                          category="housing", levels=[1], states=["active"], items=[item],
                          source_blend=f"{SOURCE_REL}/{ASSET_NAME}.blend",
                          material_map={"marble": "корпус, облицовка, колонны и портик",
                                        "glass": "увеличенные фасадные и боковое окна, фрамуга",
                                        "gold": "обрамления, колонны, дверь, вазоны и мозаика"},
                          extra={"prototype": True,
                                 "component_library_version": components.COMPONENT_LIBRARY_VERSION,
                                 "lod_policy": {"chain": [
                                     {"name": "LOD0", "triangle_budget": {"min": 1800, "max": 16000}},
                                     {"name": "LOD1", "triangle_budget": {"min": 850, "max": 8000}},
                                     {"name": "LOD2", "triangle_budget": {"min": 400, "max": 4100}},
                                 ]}})
    report = {
        "asset_id": "villa", "visual_level": 1, "state": "active", "prototype": True,
        "component_library_version": components.COMPONENT_LIBRARY_VERSION,
        "generator": "tools/assets/blender/build_villa_l01_test.py",
        "object_count": len(collection.all_objects), "triangles": lods[0]["triangles"],
        "lods": [{"name": lod["name"], "triangles": lod["triangles"]} for lod in lods],
        "bounds": item["bounds"], "sprite": {"size": [512, 384], "anchor": [256, 292]},
        "material_map": {"stone": "мраморные стены и колонны",
                         "glass": "увеличенные окна и фрамуга",
                         "gold": "обрамления, дверной декор, капители и двор"},
        "footprint": {"tile_size": DEFAULT_TILE_SIZE,
                      "original_body": [ORIGINAL_WIDTH, ORIGINAL_DEPTH],
                      "body": [HOUSE_WIDTH * architecture_scale, HOUSE_DEPTH * architecture_scale],
                      "area_multiplier": FOOTPRINT_AREA_MULTIPLIER * architecture_scale**2,
                      "multiplier_from_saved_version": architecture_scale**2,
                      "cell_percent_before": FOOTPRINT_PERCENT_BEFORE,
                      "cell_percent_after": FOOTPRINT_PERCENT_AFTER * architecture_scale**2},
        "components": ["ground.add_ground_tile", "foundations.add_foundation",
                       "common.add_door", "common.add_window", "roofs.add_gable_roof",
                       "villa_decor.add_portico_fluted_column", "villa_decor.add_ceremonial_stair",
                       "villa_decor.add_transom_sunburst", "villa_decor.add_facade_cornice",
                       "villa_decor.add_marble_wall_inlay",
                       "villa_decor.add_gilded_window_surround",
                       "villa_decor.add_gilded_entry_portal",
                       "villa_decor.add_gilded_urn",
                       "villa_decor.add_courtyard_sun_mosaic",
                       "villa_decor.add_garden_sun_obelisk",
                       "villa_decor.add_arc_flower_bed",
                       "villa_decor.add_courtyard_lantern",
                       "landscaping.add_flower_bed"],
    }
    (OUTPUT / "generation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VILLA_L01_ACTIVE_TEST_COMPLETE", json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    generate()
