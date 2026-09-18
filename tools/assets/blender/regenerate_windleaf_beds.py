"""Generate runtime windleaf bed GLB/PNG assets.

This fallback generator does not require Blender. It creates valid GLB meshes
and matching isometric PNG sprites when Blender MCP/CLI is unavailable.
"""

from __future__ import annotations

import base64
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "fields" / "windleaf_bed"
LOG_PATH = Path("/tmp/real-city-windleaf-bed-generation.log")
PNG_SIZE = (512, 384)
ANCHOR = (256, 292)


MATERIALS = {
    "earth": (0.50, 0.31, 0.16, 1.0),
    "earth_dark": (0.30, 0.16, 0.08, 1.0),
    "soil": (0.36, 0.19, 0.09, 1.0),
    "soil_light": (0.57, 0.34, 0.16, 1.0),
    "grass": (0.36, 0.66, 0.22, 1.0),
    "grass_light": (0.55, 0.82, 0.30, 1.0),
    "wood": (0.66, 0.40, 0.18, 1.0),
    "wood_dark": (0.36, 0.18, 0.08, 1.0),
    "wood_cut": (0.88, 0.64, 0.34, 1.0),
    "plank": (0.82, 0.56, 0.27, 1.0),
    "plank_light": (0.96, 0.74, 0.38, 1.0),
    "flax": (0.82, 0.74, 0.50, 1.0),
    "cloth_teal": (0.10, 0.58, 0.52, 1.0),
    "leaf": (0.12, 0.54, 0.16, 1.0),
    "leaf_light": (0.42, 0.86, 0.30, 1.0),
    "leaf_deep": (0.08, 0.38, 0.16, 1.0),
    "leaf_vein": (0.78, 1.00, 0.58, 1.0),
    "super_leaf": (0.10, 0.72, 0.28, 1.0),
    "super_leaf_light": (0.45, 1.00, 0.38, 1.0),
    "super_vein": (0.86, 1.00, 0.68, 1.0),
    "stone": (0.62, 0.60, 0.48, 1.0),
    "stone_dark": (0.42, 0.40, 0.34, 1.0),
    "iron": (0.42, 0.46, 0.46, 1.0),
    "shadow": (0.09, 0.06, 0.04, 1.0),
}


@dataclass
class Mesh:
    name: str
    material: str
    positions: list[tuple[float, float, float]]
    normals: list[tuple[float, float, float]]
    indices: list[int]


def normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length == 0:
        return (0, 0, 1)
    return (v[0] / length, v[1] / length, v[2] / length)


def face_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return normalize((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))


def add_box(meshes, name, material, center, size, yaw=0.0):
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    corners = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
    ]
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    pts = []
    for x, y, z in corners:
        pts.append((cx + x * cos_y - y * sin_y, cy + x * sin_y + y * cos_y, cz + z))
    quads = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    positions, normals, indices = [], [], []
    for quad in quads:
        start = len(positions)
        a, b, c, d = [pts[i] for i in quad]
        n = face_normal(a, b, c)
        positions.extend([a, b, c, d])
        normals.extend([n] * 4)
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    meshes.append(Mesh(name, material, positions, normals, indices))


def add_stone(meshes, name, material, center, size, yaw=0.0):
    add_box(meshes, name, material, center, size, yaw)
    add_box(meshes, name + "_cap", "stone" if material == "stone_dark" else "stone_dark",
            (center[0], center[1], center[2] + size[2] * 0.54), (size[0] * 0.78, size[1] * 0.78, size[2] * 0.10), yaw + 0.18)


def add_rope(meshes, name, start, end, thickness=0.045):
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    yaw = math.atan2(dy, dx)
    add_box(meshes, name, "flax", ((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2), (length, thickness, thickness), yaw)


def add_leaf(meshes, name, material, base, height, width, yaw, bend=0.0, vein=True):
    bx, by, bz = base
    dx, dy = math.cos(yaw), math.sin(yaw)
    sx, sy = -dy, dx
    mid = (bx + dx * bend, by + dy * bend, bz + height * 0.52)
    tip = (bx + dx * bend * 1.7, by + dy * bend * 1.7, bz + height)
    root = (bx, by, bz)
    left = (mid[0] + sx * width, mid[1] + sy * width, mid[2])
    right = (mid[0] - sx * width, mid[1] - sy * width, mid[2])
    back_mid = (mid[0] - dx * width * 0.18, mid[1] - dy * width * 0.18, mid[2] - 0.02)
    verts = [root, left, tip, right, back_mid]
    faces = [(0, 1, 2), (0, 2, 3), (1, 4, 2), (4, 3, 2), (0, 4, 1), (0, 3, 4)]
    positions, normals, indices = [], [], []
    for face in faces:
        start = len(positions)
        a, b, c = [verts[i] for i in face]
        n = face_normal(a, b, c)
        positions.extend([a, b, c])
        normals.extend([n] * 3)
        indices.extend([start, start + 1, start + 2])
    meshes.append(Mesh(name, material, positions, normals, indices))
    if vein:
        add_box(meshes, name + "_vein", "super_vein" if material == "super_leaf" else "leaf_vein",
                ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2, (root[2] + tip[2]) / 2),
                (0.022, 0.022, height * 0.74), yaw=math.atan2(tip[1] - root[1], tip[0] - root[0]) + math.pi / 2)


def add_soil_rows(meshes, prefix, level):
    add_box(meshes, prefix + "_tile_base", "earth", (0, 0, -0.08), (3.6, 3.6, 0.16))
    add_box(meshes, prefix + "_grass_tile", "grass", (0, 0, 0.02), (3.50, 3.50, 0.07))
    add_box(meshes, prefix + "_north_grass_highlight", "grass_light", (-0.72, 1.38, 0.075), (1.35, 0.18, 0.045), yaw=0.06)
    add_box(meshes, prefix + "_path_worn_edge", "earth", (0.75, -1.32, 0.075), (1.36, 0.28, 0.045), yaw=-0.12)
    add_box(meshes, prefix + "_soil_bed", "soil", (0, 0, 0.11), (2.38, 1.88, 0.16))
    add_box(meshes, prefix + "_soil_center_lift", "soil_light", (-0.10, -0.02, 0.205), (1.88, 1.28, 0.055))
    for y in (-0.48, 0.0, 0.48):
        add_box(meshes, prefix + "_furrow", "earth_dark", (0, y, 0.245), (1.94, 0.08, 0.042))
        add_box(meshes, prefix + "_furrow_lip", "soil_light", (-0.10, y + 0.10, 0.265), (1.72, 0.055, 0.034))
    plank = "plank" if level >= 3 else "wood"
    rail_h = 0.24 + level * 0.025
    add_box(meshes, prefix + "_front_rail", plank, (0, -1.06, 0.25), (2.60, 0.22, rail_h), yaw=0.01)
    add_box(meshes, prefix + "_back_rail", plank, (0, 1.06, 0.25), (2.60, 0.22, rail_h), yaw=-0.015)
    add_box(meshes, prefix + "_left_rail", plank, (-1.40, 0, 0.25), (0.22, 1.92, rail_h), yaw=-0.02)
    add_box(meshes, prefix + "_right_rail", plank, (1.40, 0, 0.25), (0.22, 1.92, rail_h), yaw=0.02)
    add_box(meshes, prefix + "_front_highlight", "wood_cut" if level < 3 else "plank_light", (0.0, -1.18, 0.42), (2.38, 0.045, 0.055))
    add_box(meshes, prefix + "_back_highlight", "wood_cut" if level < 3 else "plank_light", (-0.08, 1.18, 0.42), (2.20, 0.045, 0.055))
    for x in (-1.36, 1.36):
        for y in (-1.03, 1.03):
            add_box(meshes, prefix + "_corner_post", "wood_dark", (x, y, 0.44), (0.24, 0.24, 0.66 + level * 0.035), yaw=0.08 * (1 if x * y > 0 else -1))
            add_box(meshes, prefix + "_post_cap", "wood_cut", (x, y, 0.80 + level * 0.02), (0.31, 0.31, 0.08), yaw=0.18)
    for i, (x, y) in enumerate(((-1.56, -0.05), (1.56, 0.38), (-0.42, 1.34), (0.70, -1.38))):
        add_stone(meshes, f"{prefix}_field_stone_{i}", "stone", (x, y, 0.14), (0.28, 0.20, 0.13), yaw=0.35 * i)
    if level >= 2:
        for x in (-0.74, 0.74):
            add_rope(meshes, prefix + "_flax_front_tie", (x - 0.24, -1.18, 0.53), (x + 0.24, -1.18, 0.47))
            add_rope(meshes, prefix + "_flax_back_tie", (x - 0.24, 1.18, 0.51), (x + 0.24, 1.18, 0.55))
        add_box(meshes, prefix + "_plant_label_post", "wood_dark", (-1.63, -0.58, 0.56), (0.08, 0.08, 0.72), yaw=0.12)
        add_box(meshes, prefix + "_plant_label_board", "plank_light", (-1.67, -0.58, 0.86), (0.08, 0.45, 0.30), yaw=0.05)
        add_box(meshes, prefix + "_label_leaf_mark", "leaf_light", (-1.72, -0.58, 0.91), (0.045, 0.26, 0.12), yaw=0.08)
    if level >= 3:
        for x in (-0.95, 0, 0.95):
            add_box(meshes, prefix + "_plank_cap", "plank_light", (x, 0, 0.48), (0.18, 2.16, 0.09), yaw=0.01)
        for x in (-0.88, 0.88):
            add_box(meshes, prefix + "_leaf_support_post", "wood_dark", (x, 0.0, 0.72), (0.08, 0.08, 0.95), yaw=0.04)
        add_rope(meshes, prefix + "_leaf_support_rope", (-0.90, 0.02, 1.08), (0.90, 0.02, 1.04), thickness=0.050)
        add_box(meshes, prefix + "_teal_wind_ribbon", "cloth_teal", (1.55, -0.72, 0.75), (0.06, 0.46, 0.13), yaw=-0.44)


def crop_cluster(meshes, prefix, stage, level, super_crop=False):
    if super_crop:
        centers = [(0, -0.05)]
        count = min(7, stage + 2)
        base_height = 0.50 + stage * 0.21
        base_width = 0.17 + stage * 0.040
        mat = "super_leaf" if stage < 5 else "super_leaf_light"
    else:
        centers = [(-0.70, -0.42), (-0.20, 0.32), (0.36, -0.20), (0.78, 0.38 if level >= 2 else 0.18)]
        count = stage + (1 if level >= 3 else 0)
        base_height = 0.18 + stage * 0.16 + level * 0.045
        base_width = 0.060 + stage * 0.027 + level * 0.006
        mat = "leaf_light" if stage >= 3 else "leaf"
    for c_index, (cx, cy) in enumerate(centers):
        leaves = count if not super_crop else count + c_index
        for i in range(leaves):
            angle = (i / max(1, leaves)) * math.tau + c_index * 0.6
            radius = 0.10 if super_crop else 0.055
            base = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius, 0.21)
            height = base_height * (0.86 + 0.10 * ((i + c_index) % 3))
            width = base_width * (1.0 + 0.13 * (i % 2))
            add_leaf(meshes, f"{prefix}_leaf_{c_index}_{i}", mat, base, height, width, angle, bend=0.10 + stage * 0.025)
            if stage >= 3 and not super_crop and i % 2 == 0:
                add_leaf(meshes, f"{prefix}_leaf_highlight_{c_index}_{i}", "leaf_vein", (base[0], base[1], base[2] + height * 0.12), height * 0.52, width * 0.34, angle + 0.02, bend=0.08, vein=False)
        if stage >= 2 or super_crop:
            add_box(meshes, f"{prefix}_stem_{c_index}", "leaf_deep", (cx, cy, 0.32 + base_height * 0.24), (0.075, 0.075, base_height * 0.62))
    if super_crop and stage >= 4:
        for x in (-0.78, 0.78):
            add_box(meshes, prefix + "_support_post", "wood", (x, -0.02, 0.72), (0.06, 0.06, 1.0))
            add_rope(meshes, prefix + "_support_tie", (-0.82, -0.02, 1.02), (0.82, -0.02, 1.02), thickness=0.055)
    if super_crop and stage >= 3:
        add_box(meshes, prefix + "_soft_super_glow", "super_vein", (0, -0.04, 0.34 + base_height * 0.44), (0.10, 0.10, base_height * 0.88))


def build_meshes(level, state):
    prefix = f"windleaf_bed_l{level:02d}_{state}"
    meshes: list[Mesh] = []
    add_soil_rows(meshes, prefix, level)
    if state.startswith("stage"):
        crop_cluster(meshes, prefix, int(state[-2:]), level)
    elif state == "active":
        crop_cluster(meshes, prefix, 4, level)
    elif state.startswith("super_stage"):
        crop_cluster(meshes, prefix, int(state[-2:]), level, super_crop=True)
    elif state == "construction":
        add_box(meshes, prefix + "_unfinished_front_rail", "wood", (-0.55, -1.08, 0.58), (1.35, 0.16, 0.18))
        add_box(meshes, prefix + "_loose_planks_a", "plank" if level >= 3 else "wood", (0.70, -0.52, 0.34), (0.92, 0.14, 0.09), yaw=-0.35)
        add_box(meshes, prefix + "_loose_planks_b", "wood_cut", (0.86, -0.36, 0.43), (0.72, 0.11, 0.07), yaw=-0.18)
        add_box(meshes, prefix + "_seed_bag", "flax", (0.82, 0.62, 0.35), (0.36, 0.25, 0.34), yaw=0.28)
        add_box(meshes, prefix + "_builder_stake", "wood_dark", (-0.48, 0.72, 0.58), (0.08, 0.08, 0.68), yaw=0.12)
        add_rope(meshes, prefix + "_loose_rope", (-0.66, 0.65, 0.42), (-0.10, 0.86, 0.40), thickness=0.040)
        crop_cluster(meshes, prefix, 1, level)
    elif state == "damaged":
        add_box(meshes, prefix + "_broken_front_rail", "shadow", (0.55, -1.08, 0.55), (0.96, 0.16, 0.18), yaw=0.26)
        add_box(meshes, prefix + "_splintered_plank", "wood_dark", (0.12, -1.16, 0.70), (0.48, 0.07, 0.09), yaw=-0.68)
        add_box(meshes, prefix + "_fallen_post", "wood_dark", (-0.86, 0.70, 0.28), (0.86, 0.13, 0.11), yaw=-0.72)
        add_box(meshes, prefix + "_trampled_soil", "earth_dark", (0.30, -0.10, 0.30), (0.92, 0.62, 0.06), yaw=0.2)
        add_box(meshes, prefix + "_torn_cloth", "cloth_teal", (1.20, -0.70, 0.36), (0.34, 0.06, 0.11), yaw=-0.58)
        crop_cluster(meshes, prefix, 2, level)
        add_leaf(meshes, prefix + "_bent_leaf", "leaf_deep", (0.52, -0.22, 0.24), 0.42, 0.09, -0.88, bend=0.34)
    return meshes


def padded(data: bytes) -> bytes:
    return data + b"\x00" * ((4 - len(data) % 4) % 4)


def write_glb(name, meshes):
    material_index = {key: index for index, key in enumerate(MATERIALS)}
    buffer = bytearray()
    accessors = []
    buffer_views = []
    gltf_meshes = []
    nodes = []

    def add_accessor(raw, component_type, type_name, count, mins=None, maxs=None):
        offset = len(buffer)
        buffer.extend(raw)
        while len(buffer) % 4:
            buffer.append(0)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(raw)})
        accessor = {"bufferView": len(buffer_views) - 1, "componentType": component_type, "count": count, "type": type_name}
        if mins is not None:
            accessor["min"] = mins
            accessor["max"] = maxs
        accessors.append(accessor)
        return len(accessors) - 1

    for mesh in meshes:
        pos_raw = b"".join(struct.pack("<3f", *p) for p in mesh.positions)
        nrm_raw = b"".join(struct.pack("<3f", *n) for n in mesh.normals)
        idx_raw = b"".join(struct.pack("<H", i) for i in mesh.indices)
        mins = [min(p[i] for p in mesh.positions) for i in range(3)]
        maxs = [max(p[i] for p in mesh.positions) for i in range(3)]
        pos_i = add_accessor(pos_raw, 5126, "VEC3", len(mesh.positions), mins, maxs)
        nrm_i = add_accessor(nrm_raw, 5126, "VEC3", len(mesh.normals))
        idx_i = add_accessor(idx_raw, 5123, "SCALAR", len(mesh.indices))
        gltf_meshes.append({
            "name": mesh.name,
            "primitives": [{
                "attributes": {"POSITION": pos_i, "NORMAL": nrm_i},
                "indices": idx_i,
                "material": material_index[mesh.material],
            }],
        })
        nodes.append({"name": mesh.name, "mesh": len(gltf_meshes) - 1})

    doc = {
        "asset": {"version": "2.0", "generator": "Real City windleaf bed generator"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": gltf_meshes,
        "materials": [
            {
                "name": "MAT_windleaf_bed_" + key,
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color),
                    "roughnessFactor": 0.78,
                    "metallicFactor": 0.0,
                },
            }
            for key, color in MATERIALS.items()
        ],
        "buffers": [{"byteLength": len(buffer)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    json_bytes = padded(json.dumps(doc, separators=(",", ":")).encode("utf-8"))
    bin_bytes = padded(bytes(buffer))
    glb = bytearray()
    glb.extend(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)))
    glb.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    glb.extend(json_bytes)
    glb.extend(struct.pack("<I4s", len(bin_bytes), b"BIN\x00"))
    glb.extend(bin_bytes)
    (OUT_DIR / f"{name}.glb").write_bytes(glb)


def iso(x, y, z, scale=64):
    return (ANCHOR[0] + (x - y) * scale, ANCHOR[1] + (x + y) * scale * 0.46 - z * scale)


def draw_iso_box(draw, center, size, fill, outline=None, yaw=0.0):
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    pts = []
    for x, y, z in [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]:
        pts.append(iso(cx + x * cos_y - y * sin_y, cy + x * sin_y + y * cos_y, cz + z))
    top = [pts[i] for i in (4, 5, 6, 7)]
    left = [pts[i] for i in (0, 3, 7, 4)]
    right = [pts[i] for i in (1, 2, 6, 5)]
    base = tuple(int(v * 255) for v in fill[:3]) + (255,)
    darker = tuple(max(0, int(v * 185)) for v in base[:3]) + (255,)
    side = tuple(max(0, int(v * 210)) for v in base[:3]) + (255,)
    draw.polygon(left, fill=darker)
    draw.polygon(right, fill=side)
    draw.polygon(top, fill=base)
    if outline:
        draw.line(top + [top[0]], fill=outline, width=2)


def material_rgba(name, alpha=255):
    color = MATERIALS[name]
    return tuple(int(v * 255) for v in color[:3]) + (alpha,)


def draw_leaf_shape(draw, root, tip, width, angle, fill, vein=None, vein_width=2):
    left = (tip[0] - math.sin(angle) * width, tip[1] + math.cos(angle) * width * 0.58)
    right = (tip[0] + math.sin(angle) * width, tip[1] - math.cos(angle) * width * 0.58)
    shoulder = ((root[0] + tip[0]) / 2 - math.sin(angle) * width * 0.35, (root[1] + tip[1]) / 2 + math.cos(angle) * width * 0.20)
    draw.polygon([root, shoulder, left, tip, right], fill=fill)
    draw.line([root, tip], fill=(22, 88, 30, 130), width=vein_width + 1)
    if vein:
        draw.line([root, tip], fill=vein, width=vein_width)
        for offset in (-0.35, 0.35):
            mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2)
            side = (mid[0] + math.sin(angle + offset) * width * 0.45, mid[1] - math.cos(angle + offset) * width * 0.28)
            draw.line([mid, side], fill=vein, width=max(1, vein_width - 1))


def draw_bed_base(draw, level):
    draw_iso_box(draw, (0, 0, -0.08), (3.6, 3.6, 0.16), MATERIALS["earth"], (226, 255, 190, 100))
    draw_iso_box(draw, (0, 0, 0.02), (3.50, 3.50, 0.07), MATERIALS["grass"], (222, 255, 183, 90))
    draw_iso_box(draw, (-0.72, 1.38, 0.075), (1.35, 0.18, 0.045), MATERIALS["grass_light"])
    draw_iso_box(draw, (0.75, -1.32, 0.075), (1.36, 0.28, 0.045), MATERIALS["earth"])
    draw_iso_box(draw, (0, 0, 0.11), (2.38, 1.88, 0.16), MATERIALS["soil"])
    draw_iso_box(draw, (-0.10, -0.02, 0.205), (1.88, 1.28, 0.055), MATERIALS["soil_light"])
    for y in (-0.48, 0.0, 0.48):
        draw_iso_box(draw, (0, y, 0.245), (1.94, 0.08, 0.042), MATERIALS["earth_dark"])
        draw_iso_box(draw, (-0.10, y + 0.10, 0.265), (1.72, 0.055, 0.034), MATERIALS["soil_light"])
    rail_mat = MATERIALS["plank" if level >= 3 else "wood"]
    rail_h = 0.24 + level * 0.025
    for center, size, yaw in (
        ((0, -1.06, 0.25), (2.60, 0.22, rail_h), 0.01),
        ((0, 1.06, 0.25), (2.60, 0.22, rail_h), -0.015),
        ((-1.40, 0, 0.25), (0.22, 1.92, rail_h), -0.02),
        ((1.40, 0, 0.25), (0.22, 1.92, rail_h), 0.02),
    ):
        draw_iso_box(draw, center, size, rail_mat, yaw=yaw)
    highlight = MATERIALS["plank_light" if level >= 3 else "wood_cut"]
    draw_iso_box(draw, (0.0, -1.18, 0.42), (2.38, 0.045, 0.055), highlight)
    draw_iso_box(draw, (-0.08, 1.18, 0.42), (2.20, 0.045, 0.055), highlight)
    for x in (-1.36, 1.36):
        for y in (-1.03, 1.03):
            draw_iso_box(draw, (x, y, 0.44), (0.24, 0.24, 0.66 + level * 0.035), MATERIALS["wood_dark"])
            draw_iso_box(draw, (x, y, 0.80 + level * 0.02), (0.31, 0.31, 0.08), MATERIALS["wood_cut"], yaw=0.18)
    for i, (x, y) in enumerate(((-1.56, -0.05), (1.56, 0.38), (-0.42, 1.34), (0.70, -1.38))):
        draw_iso_box(draw, (x, y, 0.14), (0.28, 0.20, 0.13), MATERIALS["stone"], yaw=0.35 * i)
    if level >= 2:
        for x in (-0.74, 0.74):
            draw_iso_box(draw, (x, -1.18, 0.50), (0.52, 0.045, 0.045), MATERIALS["flax"], yaw=-0.12)
            draw_iso_box(draw, (x, 1.18, 0.53), (0.52, 0.045, 0.045), MATERIALS["flax"], yaw=0.12)
        draw_iso_box(draw, (-1.63, -0.58, 0.56), (0.08, 0.08, 0.72), MATERIALS["wood_dark"], yaw=0.12)
        draw_iso_box(draw, (-1.67, -0.58, 0.86), (0.08, 0.45, 0.30), MATERIALS["plank_light"], yaw=0.05)
        mark = iso(-1.74, -0.58, 0.94)
        draw.ellipse((mark[0] - 5, mark[1] - 4, mark[0] + 7, mark[1] + 5), fill=material_rgba("leaf_light"))
    if level >= 3:
        for x in (-0.95, 0, 0.95):
            draw_iso_box(draw, (x, 0, 0.48), (0.18, 2.16, 0.09), MATERIALS["plank_light"])
        for x in (-0.88, 0.88):
            draw_iso_box(draw, (x, 0.0, 0.72), (0.08, 0.08, 0.95), MATERIALS["wood_dark"])
        draw_iso_box(draw, (0, 0.02, 1.06), (1.82, 0.045, 0.045), MATERIALS["flax"])
        draw_iso_box(draw, (1.55, -0.72, 0.75), (0.06, 0.46, 0.13), MATERIALS["cloth_teal"], yaw=-0.44)


def draw_crop(draw, level, stage, super_crop=False, damaged=False):
    centers = [(0, -0.05)] if super_crop else [(-0.70, -0.42), (-0.20, 0.32), (0.36, -0.20), (0.78, 0.38 if level >= 2 else 0.18)]
    for c, (cx, cy) in enumerate(centers):
        leaves = min(7, stage + 2) if super_crop else max(2, stage + (1 if level >= 3 else 0))
        height = (0.50 + stage * 0.21) if super_crop else (0.18 + stage * 0.16 + level * 0.045)
        width = (18 + stage * 5) if super_crop else (8 + stage * 3 + level)
        leaf_color = material_rgba("super_leaf_light" if super_crop and stage >= 5 else ("super_leaf" if super_crop else ("leaf_light" if stage >= 3 else "leaf")))
        vein = material_rgba("super_vein" if super_crop else "leaf_vein", 235)
        for i in range(leaves):
            angle = (i / leaves) * math.tau + c * 0.58
            if damaged and i == leaves - 1:
                angle -= 0.85
            root = iso(cx + math.cos(angle) * 0.05, cy + math.sin(angle) * 0.05, 0.30)
            tip = iso(cx + math.cos(angle) * (0.13 if super_crop else 0.09), cy + math.sin(angle) * (0.13 if super_crop else 0.09), 0.30 + height * (0.85 + 0.08 * (i % 3)))
            draw_leaf_shape(draw, root, tip, width * (1.0 + 0.12 * (i % 2)), angle, leaf_color, vein if stage >= 2 or super_crop else None, 3 if super_crop else 2)
        if stage >= 2 or super_crop:
            stem = iso(cx, cy, 0.36 + height * 0.28)
            draw.ellipse((stem[0] - 5, stem[1] - 4, stem[0] + 5, stem[1] + 5), fill=material_rgba("leaf_deep"))
    if super_crop and stage >= 4:
        for x in (-0.78, 0.78):
            draw_iso_box(draw, (x, -0.02, 0.72), (0.06, 0.06, 1.0), MATERIALS["wood"])
        draw_iso_box(draw, (0, -0.02, 1.02), (1.62, 0.05, 0.05), MATERIALS["flax"])
    if super_crop and stage >= 3:
        glow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        p = iso(0, -0.04, 1.0)
        gd.ellipse((p[0] - 42, p[1] - 32, p[0] + 42, p[1] + 36), fill=(90, 255, 116, 42))
        return glow.filter(ImageFilter.GaussianBlur(9))
    return None


def draw_png(name, level, state):
    image = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", PNG_SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((118, 270, 398, 358), fill=(0, 0, 0, 82))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(11)))
    draw = ImageDraw.Draw(image)
    draw_bed_base(draw, level)
    if state == "construction":
        rail_mat = MATERIALS["plank" if level >= 3 else "wood"]
        draw_iso_box(draw, (-0.55, -1.08, 0.58), (1.35, 0.16, 0.18), MATERIALS["wood"])
        draw_iso_box(draw, (0.70, -0.52, 0.34), (0.92, 0.14, 0.09), rail_mat, yaw=-0.35)
        draw_iso_box(draw, (0.86, -0.36, 0.43), (0.72, 0.11, 0.07), MATERIALS["wood_cut"], yaw=-0.18)
        draw_iso_box(draw, (0.82, 0.62, 0.35), (0.36, 0.25, 0.34), MATERIALS["flax"], yaw=0.28)
        draw_iso_box(draw, (-0.48, 0.72, 0.58), (0.08, 0.08, 0.68), MATERIALS["wood_dark"], yaw=0.12)
        crop_stage = 1
        super_crop = False
    elif state == "damaged":
        draw_iso_box(draw, (0.55, -1.08, 0.55), (0.96, 0.16, 0.18), MATERIALS["shadow"], yaw=0.26)
        draw_iso_box(draw, (0.12, -1.16, 0.70), (0.48, 0.07, 0.09), MATERIALS["wood_dark"], yaw=-0.68)
        draw_iso_box(draw, (-0.86, 0.70, 0.28), (0.86, 0.13, 0.11), MATERIALS["wood_dark"], yaw=-0.72)
        draw_iso_box(draw, (0.30, -0.10, 0.30), (0.92, 0.62, 0.06), MATERIALS["earth_dark"], yaw=0.2)
        draw_iso_box(draw, (1.20, -0.70, 0.36), (0.34, 0.06, 0.11), MATERIALS["cloth_teal"], yaw=-0.58)
        crop_stage = 2
        super_crop = False
    elif state == "active":
        crop_stage = 4
        super_crop = False
    elif state.startswith("super_stage"):
        crop_stage = int(state[-2:])
        super_crop = True
    else:
        crop_stage = int(state[-2:])
        super_crop = False
    glow = draw_crop(draw, level, crop_stage, super_crop, damaged=state == "damaged")
    if glow is not None:
        image.alpha_composite(glow)
        draw = ImageDraw.Draw(image)
        draw_crop(draw, level, crop_stage, super_crop, damaged=False)
    if state == "damaged":
        draw.line([(184, 286), (235, 272), (214, 260), (264, 248), (286, 260)], fill=(43, 30, 20, 220), width=5)
    image.save(OUT_DIR / f"{name}.png")


def asset_names():
    names = []
    for level in (1, 2, 3):
        for stage in range(1, 5):
            names.append((f"windleaf_bed_l{level:02d}_stage{stage:02d}", level, f"stage{stage:02d}"))
        names.append((f"windleaf_bed_l{level:02d}_active", level, "active"))
        names.append((f"windleaf_bed_l{level:02d}_construction", level, "construction"))
        names.append((f"windleaf_bed_l{level:02d}_damaged", level, "damaged"))
    for stage in range(1, 7):
        names.append((f"windleaf_bed_l03_super_stage{stage:02d}", 3, f"super_stage{stage:02d}"))
    return names


def validate_report(items):
    result = {"assets": [], "png_size": list(PNG_SIZE), "anchor": list(ANCHOR)}
    for name, level, state in items:
        glb = OUT_DIR / f"{name}.glb"
        png = OUT_DIR / f"{name}.png"
        raw = glb.read_bytes()
        with Image.open(png) as image:
            size = list(image.size)
            bbox = image.getchannel("A").getbbox()
        assert raw[:4] == b"glTF", glb
        assert size == list(PNG_SIZE), png
        assert bbox is not None, png
        result["assets"].append({"name": name, "level": level, "state": state, "glb_bytes": len(raw), "png_bytes": png.stat().st_size, "bbox": list(bbox)})
    expected = len(items)
    assert len(result["assets"]) == expected
    (OUT_DIR / "generation-report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def make_review_sheet(items):
    columns = 7
    thumb = (192, 144)
    label_h = 22
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGBA", (columns * thumb[0], rows * (thumb[1] + label_h)), (32, 45, 41, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, _level, _state) in enumerate(items):
        with Image.open(OUT_DIR / f"{name}.png") as image:
            preview = image.resize(thumb, Image.Resampling.LANCZOS)
        x = (index % columns) * thumb[0]
        y = (index // columns) * (thumb[1] + label_h)
        sheet.alpha_composite(preview, (x, y))
        draw.text((x + 8, y + thumb[1] + 4), name.replace("windleaf_bed_", ""), fill=(235, 246, 230, 255))
    sheet.save(OUT_DIR / "windleaf_bed_l01_l03_review.png")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    items = asset_names()
    for name, level, state in items:
        meshes = build_meshes(level, state)
        write_glb(name, meshes)
        draw_png(name, level, state)
        triangles = sum(len(mesh.indices) // 3 for mesh in meshes)
        lines.append(f"{name}: meshes={len(meshes)} triangles={triangles}")
    report = validate_report(items)
    make_review_sheet(items)
    manifest = {
        "asset": "windleaf_bed",
        "display_name": "Грядка ветролиста",
        "style": "Aeolian bright fantasy stylized mid-poly",
        "scope": "levels 1-3, stages, construction, damaged, level 3 super stages",
        "png_size": list(PNG_SIZE),
        "anchor": list(ANCHOR),
        "files": [item["name"] for item in report["assets"]],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    LOG_PATH.write_text("\n".join(lines) + f"\nWINDLEAF_BED_COMPLETE {len(items)}\n")
    print(f"WINDLEAF_BED_COMPLETE {len(items)}")


if __name__ == "__main__":
    main()
