"""Machine-readable component registry for orchestrators and docs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentEntry:
    module: str
    function: str
    tags: tuple[str, ...]
    source_reference: str
    version: str = "2026.10.phase3.v5"


COMPONENTS: tuple[ComponentEntry, ...] = (
    ComponentEntry("housing", "add_dugout_shell", ("housing", "early", "earth", "windleaf"), "docs/buildings/houses/dugout.md"),
    ComponentEntry("housing", "add_wood_house_shell", ("housing", "wood", "roof", "yard"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("housing", "add_stone_house_shell", ("housing", "stone", "rune_tile_roof"), "docs/buildings/houses/stone-house.md"),
    ComponentEntry("common", "add_door", ("door", "wood", "stone", "metal", "reinforced"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("common", "add_window", ("window", "glass", "wood_frame", "metal_frame", "rect", "square", "round"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("common", "add_wood_house_chimney", ("chimney", "wood_house", "smoke"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("common", "add_path", ("path", "earth_light", "stone_pebbles", "stone_blocks"), "docs/art/visual-style-guide.md"),
    ComponentEntry("foundations", "add_foundation", ("foundation", "wood", "stone", "brick", "stone_block", "concrete", "reinforced_concrete", "metal", "low", "medium", "high", "thin", "thick"), "docs/art/visual-style-guide.md"),
    ComponentEntry("foundations", "add_round_foundation", ("foundation", "round", "wood", "stone", "brick", "stone_block", "concrete", "metal"), "docs/art/visual-style-guide.md"),
    ComponentEntry("civic", "add_town_hall_core", ("center", "tower", "civic", "flag"), "docs/buildings/center/town-hall.md"),
    ComponentEntry("industry", "add_furnace", ("industry", "kiln", "glass", "brick"), "tools/assets/blender/generate_glass_workshop_models.py"),
    ComponentEntry("industry", "add_mine_portal", ("industry", "mine", "portal", "ore", "tunnel_depth"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_arch", ("industry", "mine", "arch", "wood", "stone", "brick", "metal", "reinforced_concrete"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_tunnel_depth", ("industry", "mine", "adit", "dark_depth", "tunnel"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_rock_cheeks", ("industry", "mine", "rock_mass", "stone_cheeks"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_rail_segment", ("industry", "mine", "rails", "track"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_lamp_pair", ("industry", "mine", "lamp", "depth_light"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_ore_pile", ("industry", "mine", "ore", "coal", "stone"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_hoist", ("industry", "mine", "hoist", "winch", "mechanism"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_vent_pipe", ("industry", "mine", "ventilation", "pipe"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_explosive_crate", ("industry", "mine", "explosives", "crate"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_mine_detail_cluster", ("industry", "mine", "rails", "cart", "ore", "hoist", "props"), "docs/buildings/industry/mine.md"),
    ComponentEntry("industry", "add_conveyor", ("industry", "quarry", "sand", "sorting"), "tools/assets/blender/generate_sand_quarry_models.py"),
    ComponentEntry("industry", "add_crane", ("industry", "wood", "lumber", "crane"), "tools/assets/blender/generate_lumber_yard_models.py"),
    ComponentEntry("fields", "add_field_bed", ("fields", "windleaf", "soil", "trellis"), "tools/assets/blender/regenerate_windleaf_beds_blender.py"),
    ComponentEntry("fields", "add_styled_bed_base", ("fields", "bed_base", "windleaf", "flax", "seed", "mushroom", "herb", "reed"), "docs/buildings/fields/fields-and-beds.md"),
    ComponentEntry("fields", "add_bed_post", ("fields", "bed_post", "wood", "stone", "carved", "mushroom"), "docs/buildings/fields/fields-and-beds.md"),
    ComponentEntry("fields", "add_bed_board", ("fields", "bed_board", "plank", "slatted", "rune", "flax"), "docs/buildings/fields/fields-and-beds.md"),
    ComponentEntry("storage", "add_vault_body", ("storage", "vault", "wood", "stone", "metal", "gold"), "tools/assets/blender/generate_coin_storage_models.py"),
    ComponentEntry("storage", "add_storage_roof", ("storage", "roof", "spikes", "gold"), "tools/assets/blender/generate_coin_storage_models.py"),
    ComponentEntry("roofs", "add_rune_tile_roof", ("roof", "rune_tile", "colored"), "docs/game-design/resources-list.md"),
    ComponentEntry("roofs", "add_wood_house_gable_roof", ("roof", "wood_house", "gable", "wood_planks"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("roofs", "add_flat_roof", ("roof", "flat", "wood", "stone", "metal"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_trapezoid_roof", ("roof", "trapezoid", "hipped", "wood"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_pyramid_roof", ("roof", "pyramid", "tower", "stone"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_mansard_roof", ("roof", "mansard", "late_building"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_barrel_roof", ("roof", "barrel", "wood", "industry"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_dome_roof", ("roof", "dome", "gold", "civic"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_stepped_roof", ("roof", "stepped", "stone", "storage"), "docs/art/visual-style-guide.md"),
    ComponentEntry("roofs", "add_asymmetric_gable_roof", ("roof", "asymmetric", "gable", "house"), "docs/art/visual-style-guide.md"),
    ComponentEntry("walls", "add_storage_wall", ("wall", "spikes", "wood", "stone", "metal", "gold"), "tools/assets/blender/generate_coin_storage_models.py"),
    ComponentEntry("walls", "add_board_clad_wall", ("wall", "wood", "planks", "boards"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("walls", "add_elite_board_wall", ("wall", "elite_planks", "polished", "late_building"), "docs/art/visual-style-guide.md"),
    ComponentEntry("walls", "add_readable_stone_wall", ("wall", "stone", "rocks", "blocks"), "docs/buildings/houses/stone-house.md"),
    ComponentEntry("walls", "add_wood_house_wall_set", ("wall", "wood_house", "plank_set"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("walls", "add_s_scroll_wall_decor", ("wall_decor", "scroll", "wood", "stone", "metal", "gold", "elite_wood"), "docs/art/visual-style-guide.md"),
    ComponentEntry("walls", "add_carved_wall_pattern", ("wall_decor", "carving", "ornament", "runes", "wood", "gold", "steel"), "docs/art/visual-style-guide.md"),
    ComponentEntry("walls", "add_window_trim", ("wall_decor", "window_trim", "nalichnik", "white", "ornate"), "docs/buildings/houses/wood-house.md"),
    ComponentEntry("walls", "add_wall_medallion", ("wall_decor", "medallion", "aeolian", "stone", "gold"), "docs/art/visual-style-guide.md"),
    ComponentEntry("props", "add_market_bundle", ("props", "crate", "barrel", "sack"), "existing generator props"),
    ComponentEntry("props", "add_log_stack", ("props", "wood", "logs"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("props", "add_flower_strip", ("props", "flowers", "yard"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("props", "add_flag_marker", ("props", "flag", "yard"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("props", "add_decor_cluster", ("props", "crate", "barrel", "logs", "yard"), "tools/assets/blender/generate_wood_house_models.py"),
    ComponentEntry("landscaping", "add_grass_clump", ("landscaping", "grass", "low", "high"), "docs/art/visual-style-guide.md"),
    ComponentEntry("landscaping", "add_flower_bed", ("landscaping", "flower_bed", "round", "box", "stone_ring", "strip"), "docs/art/visual-style-guide.md"),
    ComponentEntry("landscaping", "add_flower", ("landscaping", "flower", "red", "yellow", "white", "lilac"), "docs/art/visual-style-guide.md"),
    ComponentEntry("landscaping", "add_pebble_cluster", ("landscaping", "pebbles", "ground_decor"), "docs/art/visual-style-guide.md"),
    ComponentEntry("towers", "add_tower", ("tower", "wood", "stone", "stone_block", "brick", "round"), "docs/art/visual-style-guide.md"),
    ComponentEntry("towers", "add_square_tower", ("tower", "wood", "stone_block", "brick", "square"), "docs/art/visual-style-guide.md"),
    ComponentEntry("towers", "add_stone_turret", ("tower", "turret", "stone", "flag", "crenellation"), "docs/art/visual-style-guide.md"),
    ComponentEntry("aeolian", "add_light_crystal", ("aeolian", "crystal", "accent"), "docs/art/visual-style-guide.md"),
    ComponentEntry("detail_kits", "add_damage_kit", ("detail", "damage", "midpoly"), "tools/assets/blender/revise_building_states.py"),
)


def by_tag(tag: str) -> tuple[ComponentEntry, ...]:
    return tuple(entry for entry in COMPONENTS if tag in entry.tags)


def names() -> tuple[str, ...]:
    return tuple(f"{entry.module}.{entry.function}" for entry in COMPONENTS)
