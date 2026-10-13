"""Render a PNG showcase of the complete Real City component library."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy
from mathutils import Vector

from tools.assets.blender.real_city import geometry, materials, scene
from tools.assets.blender.real_city.components import COMPONENT_LIBRARY_VERSION
from tools.assets.blender.real_city.components import (
    aeolian,
    civic,
    common,
    detail_kits,
    fields,
    foundations,
    housing,
    industry,
    landscaping,
    props,
    roofs,
    storage,
    towers,
    walls,
)
from tools.assets.blender.real_city.paths import blender_path

OUT_DIR = ROOT / "docs" / "assets"
PNG_PATH = OUT_DIR / "component-library-showcase.png"
REPORT_PATH = OUT_DIR / "component-library-showcase-report.json"
BLEND_PATH = OUT_DIR / "component-library-showcase.blend"


def add_label(collection, text: str, loc, material) -> None:
    font_curve = bpy.data.curves.new(f"label_{text}_curve", "FONT")
    font_curve.body = text
    font_curve.align_x = "CENTER"
    font_curve.align_y = "CENTER"
    font_curve.size = 0.18
    font_curve.extrude = 0.003
    obj = bpy.data.objects.new(f"label_{text}", font_curve)
    obj.location = loc
    obj.rotation_euler = (math.radians(60), 0, math.radians(45))
    obj.data.materials.append(material)
    collection.objects.link(obj)


def make_label_material():
    material = bpy.data.materials.new("MAT_component_showcase_label")
    material.diffuse_color = (0.08, 0.07, 0.055, 1)
    return material


def add_slot_base(name: str, collection, mats: dict, label_material, title: str) -> None:
    geometry.box(f"{name}_slot_base", collection, (0, 0, -0.035), (2.9, 2.35, 0.05), mats["path_warm"], bevel=0.035)
    geometry.box(f"{name}_slot_inner", collection, (0, 0, 0.000), (2.72, 2.17, 0.035), mats["grass_light"], bevel=0.030)
    add_label(collection, title, (0, -1.18, 0.08), label_material)


def move_collection(collection, offset) -> None:
    dx, dy, dz = offset
    for obj in collection.all_objects:
        obj.location.x += dx
        obj.location.y += dy
        obj.location.z += dz


def add_sample(scene_obj, mats: dict, label_material, title: str, builder, offset) -> dict:
    safe = title.replace(".", "_").replace("-", "_").replace(" ", "_")
    collection = bpy.data.collections.new(f"component_{safe}")
    scene_obj.collection.children.link(collection)
    add_slot_base(safe, collection, mats, label_material, title)
    builder(collection, mats)
    move_collection(collection, offset)
    return {"title": title, "object_count": len(collection.all_objects)}


def build_samples(scene_obj, mats: dict, label_material) -> list[dict]:
    samples = [
        ("housing.dugout", lambda c, m: housing.add_dugout_shell("show_dugout", c, m, level=4)),
        ("housing.wood_house", lambda c, m: housing.add_wood_house_shell("show_wood_house", c, m, level=3)),
        ("housing.stone_house", lambda c, m: housing.add_stone_house_shell("show_stone_house", c, m, level=3, rune_roof=True)),
        ("housing.yard", lambda c, m: housing.add_housing_yard("show_yard", c, m, level=5)),
        ("civic.tower", lambda c, m: civic.add_civic_tower("show_tower", c, m, height=1.25)),
        ("civic.notice", lambda c, m: civic.add_notice_board("show_notice", c, m)),
        ("civic.balcony", lambda c, m: civic.add_balcony("show_balcony", c, m, (0, -0.10, 0.55), width=0.82)),
        ("civic.plaza", lambda c, m: civic.add_plaza("show_plaza", c, m)),
        ("civic.town_hall", lambda c, m: civic.add_town_hall_core("show_town_hall", c, m, level=6)),
        ("roof.gable", lambda c, m: roofs.add_gable_roof("show_gable", c, m, (0, 0, 0.42), (1.35, 0.95, 0.38), color_role="roof_red")),
        ("roof.wood_gable", lambda c, m: roofs.add_wood_house_gable_roof("show_wood_gable", c, m, (0, 0, 0.42), (1.42, 1.00, 0.42), board_rows=5)),
        ("roof.hipped", lambda c, m: roofs.add_hipped_roof("show_hipped", c, m, (0, 0, 0.42), (1.35, 1.05, 0.36), color_role="roof_teal", armored=True)),
        ("roof.shed", lambda c, m: roofs.add_shed_roof("show_shed", c, m, (0, 0, 0.42), (1.35, 0.88, 0.11), color_role="roof_leaf")),
        ("roof.flat", lambda c, m: roofs.add_flat_roof("show_flat", c, m, (0, 0, 0.42), (1.36, 0.96, 0.16), material_role="roof_stone")),
        ("roof.trapezoid", lambda c, m: roofs.add_trapezoid_roof("show_trapezoid", c, m, (0, 0, 0.42), (1.40, 1.00, 0.34), color_role="roof_wood_plank")),
        ("roof.pyramid", lambda c, m: roofs.add_pyramid_roof("show_pyramid", c, m, (0, 0, 0.42), (1.18, 1.02, 0.44), color_role="roof_red")),
        ("roof.mansard", lambda c, m: roofs.add_mansard_roof("show_mansard", c, m, (0, 0, 0.42), (1.36, 1.02, 0.42), color_role="roof_teal")),
        ("roof.barrel", lambda c, m: roofs.add_barrel_roof("show_barrel", c, m, (0, 0, 0.42), (1.34, 1.00, 0.38), color_role="roof_wood_plank")),
        ("roof.dome", lambda c, m: roofs.add_dome_roof("show_dome", c, m, (0, 0, 0.42), radius=0.48, height=0.34, color_role="roof_gold")),
        ("roof.stepped", lambda c, m: roofs.add_stepped_roof("show_stepped", c, m, (0, 0, 0.42), (1.30, 0.98, 0.36), color_role="roof_stone")),
        ("roof.asymmetric", lambda c, m: roofs.add_asymmetric_gable_roof("show_asym", c, m, (0, 0, 0.42), (1.38, 1.00, 0.40), color_role="roof_coral")),
        ("roof.tiles", lambda c, m: roofs.add_tile_rows("show_tiles", c, m, (0, 0, 0.45), 1.35, 0.95, rows=5, color_role="roof_coral")),
        ("roof.rune_tile", lambda c, m: roofs.add_rune_tile_roof("show_rune", c, m, (0, 0, 0.42), (1.35, 0.95, 0.38))),
        ("roof.plates", lambda c, m: roofs.add_roof_plate_rows("show_plates", c, m, (0, 0, 0.42), (1.45, 1.05, 0.36), rows=5, material_role="metal_worn")),
        ("roof.spikes", lambda c, m: roofs.add_roof_spikes("show_spikes", c, m, (0, -0.28, 0.62), count=6, width=1.25, material_role="roof_gold")),
        ("foundation.wood_low", lambda c, m: foundations.add_foundation("show_foundation_wood", c, m, width=1.40, depth=0.92, height="low", thickness="thin", material="wood")),
        ("foundation.stone_high", lambda c, m: foundations.add_foundation("show_foundation_stone", c, m, width=1.40, depth=0.92, height="high", thickness="thick", material="stone_block")),
        ("foundation.metal", lambda c, m: foundations.add_foundation("show_foundation_metal", c, m, width=1.40, depth=0.92, height="medium", thickness="medium", material="metal")),
        ("foundation.round_stone", lambda c, m: foundations.add_round_foundation("show_round_foundation_stone", c, m, radius=0.62, height="medium", thickness="medium", material="stone_block")),
        ("foundation.round_metal", lambda c, m: foundations.add_round_foundation("show_round_foundation_metal", c, m, radius=0.58, height="high", thickness="thick", material="metal")),
        ("wall.plank", lambda c, m: walls.add_plank_wall("show_plank_wall", c, m, (0, -0.08, 0.48), (1.45, 0.12, 0.82), planks=8)),
        ("wall.board_clad", lambda c, m: walls.add_board_clad_wall("show_board_clad", c, m, (0, -0.08, 0.48), (1.45, 0.12, 0.82), planks=8)),
        ("wall.elite_board", lambda c, m: walls.add_elite_board_wall("show_elite_board", c, m, (0, -0.08, 0.48), (1.45, 0.12, 0.82), planks=8)),
        ("wall.stone", lambda c, m: walls.add_stone_block_wall("show_stone_wall", c, m, (0, -0.08, 0.48), (1.45, 0.18, 0.82), rows=4)),
        ("wall.readable_stone", lambda c, m: walls.add_readable_stone_wall("show_readable_stone", c, m, (0, -0.08, 0.48), (1.45, 0.18, 0.82), style="blocks")),
        ("wall.wood_set", lambda c, m: walls.add_wood_house_wall_set("show_wood_wall_set", c, m, width=1.35, depth=0.92, height=0.74)),
        ("wall.metal", lambda c, m: walls.add_metal_plate_wall("show_metal_wall", c, m, (0, -0.08, 0.48), (1.45, 0.18, 0.82), panels=5, gold_trim=True)),
        ("wall.storage", lambda c, m: walls.add_storage_wall("show_storage_wall", c, m, (0, -0.08, 0.48), (1.45, 0.18, 0.82), material_profile="gold", spikes=True)),
        ("wall.spikes", lambda c, m: walls.add_wall_spikes("show_wall_spikes", c, m, (0, -0.18, 0.52), count=7, width=1.35, material_role="metal_worn")),
        ("wall.piers", lambda c, m: walls.add_corner_piers("show_piers", c, m, 1.30, 0.95, 0.82, z_base=0.05, material_role="stone_light")),
        ("wall.scroll_gold", lambda c, m: walls.add_s_scroll_wall_decor("show_scroll_gold", c, m, (0, -0.08, 0.48), material="gold")),
        ("wall.carving", lambda c, m: walls.add_carved_wall_pattern("show_carving", c, m, (0, -0.08, 0.48), material="elite_wood", style="vine")),
        ("wall.rune_pattern", lambda c, m: walls.add_carved_wall_pattern("show_runes", c, m, (0, -0.08, 0.48), material="steel", style="runes")),
        ("wall.window_trim", lambda c, m: walls.add_window_trim("show_nalichnik", c, m, (0, -0.08, 0.50), width=0.70, height=0.56)),
        ("wall.medallion", lambda c, m: walls.add_wall_medallion("show_medallion", c, m, (0, -0.08, 0.50), material="stone", symbol="wind")),
        ("path.earth", lambda c, m: common.add_path("show_path_earth", c, m, (0, 0, 0.02), kind="earth_light")),
        ("path.pebbles", lambda c, m: common.add_path("show_path_pebbles", c, m, (0, 0, 0.02), kind="stone_pebbles")),
        ("path.blocks", lambda c, m: common.add_path("show_path_blocks", c, m, (0, 0, 0.02), kind="stone_blocks")),
        ("prop.crate", lambda c, m: props.add_crate("show_crate", c, m, (0, 0, 0.23), (0.70, 0.54, 0.42))),
        ("prop.sack", lambda c, m: props.add_sack("show_sack", c, m, (0, 0, 0.20), scale=(0.30, 0.24, 0.28))),
        ("prop.planks", lambda c, m: props.add_plank_stack("show_planks", c, m, (0, 0, 0.14), rows=4, count=5, length=0.78)),
        ("prop.logs", lambda c, m: props.add_log_stack("show_logs", c, m, (0, -0.05, 0.11), count=5, length=0.72)),
        ("prop.flowers", lambda c, m: props.add_flower_strip("show_flower_strip", c, m, (0, -0.02, 0.06), count=5)),
        ("prop.flag", lambda c, m: props.add_flag_marker("show_flag", c, m, (0, -0.04, 0.05), height=0.86, color_role="roof_teal")),
        ("prop.decor_cluster", lambda c, m: props.add_decor_cluster("show_decor_cluster", c, m, (0, -0.08, 0.06))),
        ("prop.tools", lambda c, m: props.add_tool_rack("show_tools", c, m, (0, -0.05, 0.12))),
        ("prop.workbench", lambda c, m: props.add_workbench("show_workbench", c, m, (0, -0.05, 0.10))),
        ("prop.debris", lambda c, m: props.add_scattered_debris("show_debris", c, m, count=8)),
        ("prop.scaffold", lambda c, m: props.add_construction_scaffold("show_scaffold", c, m, width=1.55, height=1.10)),
        ("prop.market", lambda c, m: props.add_market_bundle("show_market", c, m, (0, -0.08, 0.06))),
        ("land.grass", lambda c, m: [landscaping.add_grass_clump(f"show_grass_{i}", c, m, (-0.36 + i * 0.18, -0.04 + (i % 2) * 0.08, 0.04), height="high" if i % 2 else "low", blades=5) for i in range(5)]),
        ("land.flower_bed", lambda c, m: landscaping.add_flower_bed("show_flower_bed", c, m, (0, -0.04, 0.04), style="stone_ring")),
        ("land.flowers", lambda c, m: [landscaping.add_flower(f"show_flower_{i}", c, m, (-0.30 + i * 0.20, -0.02, 0.04), kind=("red", "yellow", "white", "lilac")[i]) for i in range(4)]),
        ("land.pebbles", lambda c, m: landscaping.add_pebble_cluster("show_pebbles", c, m, (0, -0.04, 0.04), count=9, radius=0.36)),
        ("field.leaf", lambda c, m: [fields.add_leaf(f"show_leaf_{i}", c, m, (0, 0, 0.45), yaw=i * math.tau / 6, length=0.56, width=0.16) for i in range(6)]),
        ("field.log_wall", lambda c, m: fields.add_log_bed_wall("show_log_bed", c, m, level=2)),
        ("field.plank_wall", lambda c, m: fields.add_plank_bed_wall("show_plank_bed", c, m)),
        ("field.soil_rows", lambda c, m: fields.add_soil_rows("show_soil", c, m, rows=4)),
        ("field.windleaf", lambda c, m: fields.add_windleaf_clusters("show_windleaf", c, m, level=3, stage=4)),
        ("field.trellis", lambda c, m: fields.add_support_trellis("show_trellis", c, m)),
        ("field.bed", lambda c, m: fields.add_field_bed("show_field_bed", c, m, level=3, stage=4, super_crop=True)),
        ("field.base_windleaf", lambda c, m: fields.add_styled_bed_base("show_base_windleaf", c, m, style="windleaf")),
        ("field.base_flax", lambda c, m: fields.add_styled_bed_base("show_base_flax", c, m, style="flax")),
        ("field.base_mushroom", lambda c, m: fields.add_styled_bed_base("show_base_mushroom", c, m, style="mushroom")),
        ("field.base_reed", lambda c, m: fields.add_styled_bed_base("show_base_reed", c, m, style="reed")),
        ("industry.shed", lambda c, m: industry.add_work_shed("show_industry_shed", c, m, level=5, roof_role="roof_rune_tile")),
        ("industry.furnace", lambda c, m: industry.add_furnace("show_furnace", c, m, level=7, glass=True)),
        ("industry.portal", lambda c, m: industry.add_mine_portal("show_portal", c, m, level=5)),
        ("mine.arch_wood", lambda c, m: industry.add_mine_arch("show_mine_arch_wood", c, m, variant="wood", width=1.38, height=1.08)),
        ("mine.arch_stone", lambda c, m: industry.add_mine_arch("show_mine_arch_stone", c, m, variant="stone", width=1.38, height=1.08)),
        ("mine.arch_brick", lambda c, m: industry.add_mine_arch("show_mine_arch_brick", c, m, variant="brick", width=1.38, height=1.08)),
        ("mine.arch_metal", lambda c, m: industry.add_mine_arch("show_mine_arch_metal", c, m, variant="metal", width=1.38, height=1.08, reinforced=True)),
        ("mine.tunnel", lambda c, m: industry.add_mine_tunnel_depth("show_mine_tunnel", c, m, width=0.86, height=0.86, depth=0.56)),
        ("mine.rocks", lambda c, m: industry.add_mine_rock_cheeks("show_mine_rocks", c, m, width=1.40, height=1.05)),
        ("mine.rails", lambda c, m: industry.add_mine_rail_segment("show_mine_rails", c, m, length=1.22)),
        ("mine.lamps", lambda c, m: industry.add_mine_lamp_pair("show_mine_lamps", c, m, width=0.92, height=0.82)),
        ("mine.ore", lambda c, m: industry.add_mine_ore_pile("show_mine_ore", c, m, kind="copper", count=7)),
        ("mine.hoist", lambda c, m: industry.add_mine_hoist("show_mine_hoist", c, m, level=6)),
        ("mine.vent_pipe", lambda c, m: industry.add_mine_vent_pipe("show_mine_vent", c, m, height=1.05)),
        ("mine.explosive_crate", lambda c, m: industry.add_mine_explosive_crate("show_mine_explosive", c, m, closed=False)),
        ("mine.detail_cluster", lambda c, m: industry.add_mine_detail_cluster("show_mine_cluster", c, m, level=6)),
        ("industry.cart", lambda c, m: industry.add_mine_cart("show_cart", c, m, loaded=True)),
        ("industry.conveyor", lambda c, m: industry.add_conveyor("show_conveyor", c, m, (0, 0, 0.46), length=1.45)),
        ("industry.crane", lambda c, m: industry.add_crane("show_crane", c, m, loc=(0.50, -0.20, 0.0), height=1.15)),
        ("industry.glass", lambda c, m: industry.add_glass_pane("show_glass", c, m, (0, -0.08, 0.48), width=0.50, height=0.62, star=True)),
        ("industry.line", lambda c, m: industry.add_resource_processing_line("show_processing", c, m, level=6, resource="glass")),
        ("storage.vault", lambda c, m: storage.add_vault_body("show_vault", c, m, level=11)),
        ("storage.roof", lambda c, m: storage.add_storage_roof("show_storage_roof", c, m, level=12, width=1.55, depth=1.05, z=0.46)),
        ("storage.coins", lambda c, m: storage.add_coin_accents("show_coins", c, m, loc=(-0.28, -0.20, 0.16), count=8)),
        ("storage.cells", lambda c, m: storage.add_safe_cells("show_cells", c, m, level=11, width=1.45, depth=0.95, z=0.40)),
        ("storage.yard", lambda c, m: storage.add_storage_yard("show_storage_yard", c, m, level=8)),
        ("tower.wood", lambda c, m: towers.add_tower("show_tower_wood", c, m, (0, -0.02, 0.04), material="wood", height=1.05)),
        ("tower.stone", lambda c, m: towers.add_tower("show_tower_stone", c, m, (0, -0.02, 0.04), material="stone", height=1.05)),
        ("tower.brick", lambda c, m: towers.add_tower("show_tower_brick", c, m, (0, -0.02, 0.04), material="brick", height=1.05)),
        ("tower.square", lambda c, m: towers.add_square_tower("show_tower_square", c, m, (0, -0.02, 0.04), material="stone_block")),
        ("tower.turret_flag", lambda c, m: towers.add_stone_turret("show_turret_flag", c, m, (0, -0.02, 0.04), height=0.88, radius=0.20, thickness="medium", flag=True)),
        ("tower.turret_thick", lambda c, m: towers.add_stone_turret("show_turret_thick", c, m, (0, -0.02, 0.04), height=1.12, radius=0.26, thickness="thick", flag=False)),
        ("aeolian.wind", lambda c, m: aeolian.add_wind_marker("show_wind", c, m, (0, 0, 0.25), scale=1.5)),
        ("aeolian.ribbon", lambda c, m: aeolian.add_ribbon("show_ribbon", c, m, (0, 0, 0.42), length=1.10, color_role="roof_teal")),
        ("aeolian.crystal", lambda c, m: aeolian.add_light_crystal("show_crystal", c, m, (0, 0, 0.42), height=0.78, radius=0.18)),
        ("aeolian.canopy", lambda c, m: aeolian.add_soft_canopy("show_canopy", c, m, (0, 0, 0.72), size=(1.25, 0.78, 0.09))),
        ("aeolian.lens", lambda c, m: aeolian.add_lens("show_lens", c, m, (0, -0.08, 0.42), radius=0.26)),
        ("aeolian.seal", lambda c, m: aeolian.add_clock_or_city_seal("show_seal", c, m, (0, -0.08, 0.42), radius=0.26)),
        ("detail.facade", lambda c, m: detail_kits.add_facade_overlay("show_facade", c, m, width=1.35, y=-0.18, z=0.58)),
        ("detail.bevels", lambda c, m: detail_kits.add_corner_bevel_blocks("show_bevels", c, m, width=1.25, depth=0.90, z=0.50, height=0.72)),
        ("detail.damage", lambda c, m: detail_kits.add_damage_kit("show_damage", c, m, y=-0.18, z=0.58, width=1.15)),
        ("detail.bake", lambda c, m: detail_kits.add_texture_bake_strips("show_bake", c, m, width=1.35, y=-0.18, z=0.56, rows=5)),
        ("detail.props", lambda c, m: detail_kits.add_readable_prop_cluster("show_detail_props", c, m, loc=(0.05, -0.25, 0.10))),
        ("common.window", lambda c, m: common.add_window("show_window", c, m, (0, -0.08, 0.50), size=(0.74, 0.07, 0.55))),
        ("common.door", lambda c, m: common.add_door("show_door", c, m, (0, -0.08, 0.48), size=(0.58, 0.09, 0.82), reinforced=True)),
        ("common.chimney", lambda c, m: common.add_chimney("show_chimney", c, m, (0, 0, 0.52), height=0.88, radius=0.14)),
        ("common.wood_chimney", lambda c, m: common.add_wood_house_chimney("show_wood_chimney", c, m, (0, 0, 0.52), level=4)),
        ("common.scaffold", lambda c, m: common.add_scaffold("show_common_scaffold", c, m, width=1.35, height=1.12)),
    ]

    cols = 9
    spacing_x = 3.6
    spacing_y = 3.15
    records = []
    rows = math.ceil(len(samples) / cols)
    for index, (title, builder) in enumerate(samples):
        row = index // cols
        col = index % cols
        offset = ((col - (cols - 1) / 2) * spacing_x, ((rows - 1) / 2 - row) * spacing_y, 0)
        records.append(add_sample(scene_obj, mats, label_material, title, builder, offset))
    return records


def configure_showcase_scene(scene_obj):
    scene_obj.render.resolution_x = 2400
    scene_obj.render.resolution_y = 2200
    scene_obj.render.resolution_percentage = 100
    scene_obj.render.film_transparent = False
    scene_obj.render.image_settings.file_format = "PNG"
    scene_obj.render.image_settings.color_mode = "RGBA"
    scene_obj.view_settings.view_transform = "AgX"
    try:
        scene_obj.render.engine = "CYCLES"
    except TypeError:
        pass
    if hasattr(scene_obj, "cycles"):
        scene_obj.cycles.samples = 32
        scene_obj.cycles.use_denoising = True

    camera_data = bpy.data.cameras.new("component_showcase_camera")
    camera = bpy.data.objects.new("component_showcase_camera", camera_data)
    scene_obj.collection.objects.link(camera)
    camera.location = (24, -34, 30)
    camera.rotation_euler = (-Vector(camera.location)).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 54.0
    camera_data.shift_y = 0.0
    scene_obj.camera = camera

    scene.setup_lighting(scene_obj, prefix="component_showcase")
    if scene_obj.world:
        background = next((node for node in scene_obj.world.node_tree.nodes if node.type == "BACKGROUND"), None)
        if background:
            background.inputs[0].default_value = (0.78, 0.82, 0.86, 1)
            background.inputs[1].default_value = 0.55


def generate() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scene.clear_scene()
    scene_obj = bpy.context.scene
    scene_obj.name = "component_library_showcase_scene"
    configure_showcase_scene(scene_obj)
    mats = materials.create_palette("MAT_component_showcase")
    label_material = make_label_material()

    records = build_samples(scene_obj, mats, label_material)
    for collection in scene_obj.collection.children:
        geometry.clean_meshes(collection)

    scene.write_text_note(
        "component_library_showcase_notes",
        f"Real City component library showcase. Version: {COMPONENT_LIBRARY_VERSION}. Samples: {len(records)}.",
    )
    bpy.ops.wm.save_as_mainfile(filepath=blender_path(BLEND_PATH))
    scene_obj.render.filepath = blender_path(PNG_PATH)
    bpy.ops.render.render(write_still=True)

    report = {
        "component_library_version": COMPONENT_LIBRARY_VERSION,
        "png": str(PurePosixPath("docs") / "assets" / PNG_PATH.name),
        "blend": str(PurePosixPath("docs") / "assets" / BLEND_PATH.name),
        "sample_count": len(records),
        "samples": records,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("COMPONENT_LIBRARY_SHOWCASE_COMPLETE", json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    generate()
