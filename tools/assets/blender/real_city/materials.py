"""Material helpers and the shared Real City palette."""

from __future__ import annotations

REAL_CITY_PALETTE = {
    "earth_warm": (0.55, 0.36, 0.18),
    "grass_bright": (0.30, 0.62, 0.16),
    "grass_light": (0.48, 0.78, 0.30),
    "path_warm": (0.72, 0.52, 0.30),
    "path_light_earth": (0.78, 0.58, 0.35),
    "wood_pale": (0.82, 0.56, 0.27),
    "wood_dark": (0.34, 0.18, 0.08),
    "wood_beam": (0.58, 0.32, 0.13),
    "wood_cut": (0.90, 0.66, 0.36),
    "elite_plank": (0.46, 0.24, 0.10),
    "elite_plank_highlight": (0.72, 0.45, 0.22),
    "whitewash": (0.92, 0.86, 0.66),
    "stone_light": (0.66, 0.64, 0.56),
    "stone_shadow": (0.42, 0.42, 0.37),
    "stone_block": (0.72, 0.72, 0.68),
    "brick_warm": (0.62, 0.25, 0.14),
    "brick_light": (0.76, 0.35, 0.20),
    "reinforced_concrete": (0.55, 0.58, 0.55),
    "roof_wood_plank": (0.78, 0.44, 0.20),
    "roof_wood_dark": (0.48, 0.25, 0.10),
    "roof_leaf": (0.30, 0.62, 0.24),
    "roof_teal": (0.08, 0.52, 0.56),
    "roof_red": (0.72, 0.16, 0.10),
    "roof_gold": (0.86, 0.55, 0.16),
    "roof_blue": (0.14, 0.36, 0.82),
    "roof_green": (0.27, 0.58, 0.35),
    "roof_coral": (0.84, 0.43, 0.31),
    "roof_stone": (0.58, 0.60, 0.56),
    "roof_rune_tile": (0.42, 0.34, 0.68),
    "metal_worn": (0.45, 0.47, 0.44),
    "steel_light": (0.62, 0.66, 0.62),
    "dark_metal": (0.22, 0.24, 0.24),
    "armor": (0.52, 0.56, 0.54),
    "armor_dark": (0.34, 0.37, 0.36),
    "copper": (0.82, 0.44, 0.20),
    "coal": (0.12, 0.12, 0.11),
    "concrete": (0.68, 0.70, 0.66),
    "glass_cyan": (0.46, 0.82, 0.90),
    "glass_edge": (0.22, 0.62, 0.70),
    "glass_broken": (0.58, 0.90, 0.95),
    "star_glass": (0.55, 0.31, 0.94),
    "window_warm": (1.00, 0.66, 0.24),
    "flower_red": (0.96, 0.16, 0.14),
    "flower_yellow": (1.00, 0.84, 0.18),
    "flower_white": (0.96, 0.94, 0.78),
    "flower_lilac": (0.78, 0.50, 0.98),
    "amethyst": (0.56, 0.32, 0.86),
    "runic_glow": (0.64, 0.40, 0.94),
    "construction_plank": (0.86, 0.62, 0.34),
    "rope": (0.70, 0.50, 0.26),
    "dust": (0.76, 0.67, 0.53),
    "soil": (0.44, 0.27, 0.13),
    "soil_light": (0.66, 0.43, 0.21),
    "sand_shadow": (0.58, 0.44, 0.25),
    "damage_char": (0.08, 0.06, 0.045),
    "damage_crack": (0.035, 0.030, 0.026),
}


def _bpy():
    import bpy

    return bpy


def principled_node(material):
    """Find a Principled BSDF node by node type, not localized name."""

    if not material.use_nodes:
        material.use_nodes = True
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def set_input(node, name: str, value) -> None:
    if node and name in node.inputs:
        node.inputs[name].default_value = value


def create_material(
    name: str,
    color,
    *,
    roughness: float = 0.78,
    metallic: float = 0.0,
    alpha: float = 1.0,
    emission=None,
    emission_strength: float = 0.0,
):
    bpy = _bpy()
    material = bpy.data.materials.new(name)
    material.diffuse_color = (color[0], color[1], color[2], alpha)
    material.use_nodes = True
    if alpha < 1:
        material.blend_method = "BLEND"
        material.show_transparent_back = True
    node = principled_node(material)
    set_input(node, "Base Color", (color[0], color[1], color[2], alpha))
    set_input(node, "Alpha", alpha)
    set_input(node, "Roughness", roughness)
    set_input(node, "Metallic", metallic)
    if emission is not None:
        set_input(node, "Emission Color", (emission[0], emission[1], emission[2], 1))
        set_input(node, "Emission Strength", emission_strength)
    return material


def create_palette(prefix: str = "MAT_real_city", overrides: dict[str, tuple[float, float, float]] | None = None):
    palette = dict(REAL_CITY_PALETTE)
    if overrides:
        palette.update(overrides)
    materials = {}
    for role, color in palette.items():
        kwargs = {}
        if role in {"glass_cyan", "glass_broken", "star_glass", "amethyst", "runic_glow"}:
            kwargs["alpha"] = 0.68
            kwargs["roughness"] = 0.24
        if role in {"metal_worn", "steel_light", "dark_metal", "armor", "armor_dark", "roof_gold"}:
            kwargs["metallic"] = 0.16 if role != "roof_gold" else 0.28
            kwargs["roughness"] = 0.48
        if role == "window_warm":
            kwargs["emission"] = color
            kwargs["emission_strength"] = 0.35
            kwargs["roughness"] = 0.30
        if role in {"star_glass", "runic_glow"}:
            kwargs["emission"] = color
            kwargs["emission_strength"] = 0.28
        materials[role] = create_material(f"{prefix}_{role}", color, **kwargs)
    return materials
