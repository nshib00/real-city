#!/usr/bin/env python3
import json
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
GLB_OUT_DIR = ROOT / "frontend" / "src" / "assets" / "buildings" / "housing" / "wood_house"
PNG_OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "housing" / "wood_house"
STATES = ("active", "construction", "damaged")
LEVELS = (1, 2, 3)
SPRITE_SIZE = (512, 384)


MATERIALS = [
    ("grass_bright", (0.34, 0.72, 0.28, 1.0)),
    ("path_warm", (0.72, 0.50, 0.28, 1.0)),
    ("stone_path", (0.56, 0.55, 0.48, 1.0)),
    ("wood_wall_pale", (0.88, 0.69, 0.39, 1.0)),
    ("wood_wall_shadow", (0.64, 0.43, 0.23, 1.0)),
    ("roof_cyan", (0.10, 0.78, 0.86, 1.0)),
    ("roof_shadow", (0.07, 0.48, 0.52, 1.0)),
    ("roof_trim_light", (0.88, 0.96, 0.88, 1.0)),
    ("fence_white", (0.88, 0.90, 0.84, 1.0)),
    ("beam_dark", (0.35, 0.20, 0.10, 1.0)),
    ("stone_light", (0.62, 0.62, 0.56, 1.0)),
    ("window_blue", (0.56, 0.84, 0.96, 1.0)),
    ("window_light", (1.00, 0.78, 0.34, 1.0)),
    ("door_warm", (0.56, 0.35, 0.18, 1.0)),
    ("flower_red", (0.94, 0.16, 0.12, 1.0)),
    ("flower_yellow", (1.00, 0.84, 0.14, 1.0)),
    ("leaf_green", (0.14, 0.55, 0.18, 1.0)),
    ("tool_metal", (0.48, 0.50, 0.46, 1.0)),
    ("construction_plank", (0.86, 0.59, 0.30, 1.0)),
    ("dust", (0.76, 0.68, 0.54, 0.62)),
    ("damage_char", (0.10, 0.08, 0.06, 1.0)),
    ("damage_crack", (0.03, 0.025, 0.02, 1.0)),
    ("brick_chimney", (0.66, 0.42, 0.32, 1.0)),
    ("watering_can", (0.94, 0.84, 0.18, 1.0)),
]

MAT = {name: index for index, (name, _) in enumerate(MATERIALS)}


def rot_z(point, angle):
    x, y, z = point
    c = math.cos(angle)
    s = math.sin(angle)
    return (x * c - y * s, x * s + y * c, z)


def normal(a, b, c):
    ux, uy, uz = (b[i] - a[i] for i in range(3))
    vx, vy, vz = (c[i] - a[i] for i in range(3))
    nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    return (nx / length, ny / length, nz / length)


class MeshBuilder:
    def __init__(self):
        self.parts = []

    def add_triangle(self, material, verts):
        n = normal(verts[0], verts[1], verts[2])
        self.parts.extend((material, vertex, n) for vertex in verts)

    def add_face(self, material, verts):
        if len(verts) == 3:
            self.add_triangle(material, verts)
            return
        self.add_triangle(material, [verts[0], verts[1], verts[2]])
        self.add_triangle(material, [verts[0], verts[2], verts[3]])

    def add_polyhedron(self, material, verts, faces):
        for face in faces:
            self.add_face(material, [verts[i] for i in face])

    def box(self, material, loc, size, rz=0.0):
        lx, ly, lz = loc
        sx, sy, sz = (v / 2 for v in size)
        base = [
            (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
            (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
        ]
        verts = []
        for p in base:
            rx, ry, rzv = rot_z(p, rz)
            verts.append((rx + lx, ry + ly, rzv + lz))
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add_polyhedron(material, verts, faces)

    def gable_roof(self, material, loc, size):
        lx, ly, lz = loc
        width, depth, height = size
        x = width / 2
        y = depth / 2
        verts = [
            (-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0),
            (0, -y, height), (0, y, height),
        ]
        verts = [(vx + lx, vy + ly, vz + lz) for vx, vy, vz in verts]
        faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
        self.add_polyhedron(material, verts, faces)

    def cylinder(self, material, loc, radius, depth, segments=10):
        lx, ly, lz = loc
        bottom_z = lz - depth / 2
        top_z = lz + depth / 2
        bottom_center = (lx, ly, bottom_z)
        top_center = (lx, ly, top_z)
        for i in range(segments):
            a0 = math.tau * i / segments
            a1 = math.tau * (i + 1) / segments
            p0 = (lx + math.cos(a0) * radius, ly + math.sin(a0) * radius, bottom_z)
            p1 = (lx + math.cos(a1) * radius, ly + math.sin(a1) * radius, bottom_z)
            p2 = (p1[0], p1[1], top_z)
            p3 = (p0[0], p0[1], top_z)
            self.add_face(material, [p0, p1, p2, p3])
            self.add_face(material, [bottom_center, p1, p0])
            self.add_face(material, [top_center, p3, p2])


def add_front_windows(mesh, y, z, damaged=False):
    for x in (-0.42, 0.42):
        mesh.box(MAT["window_blue"] if not damaged else MAT["damage_crack"], (x, y, z), (0.22, 0.055, 0.24))
        mesh.box(MAT["roof_trim_light"], (x, y - 0.038, z), (0.30, 0.035, 0.04))
        mesh.box(MAT["roof_trim_light"], (x, y - 0.04, z), (0.035, 0.036, 0.30))


def add_core_house(mesh, level, damaged=False):
    wall = MAT["wood_wall_shadow"] if damaged else MAT["wood_wall_pale"]
    roof = MAT["wood_wall_shadow"] if damaged else MAT["roof_cyan"]
    body_h = 0.72 if level == 1 else 1.20
    body_w = 1.30 if level == 1 else 1.40
    body_d = 1.02 if level == 1 else 1.08

    mesh.box(MAT["grass_bright"], (0, 0, -0.04), (3.55, 3.55, 0.08))
    mesh.box(MAT["path_warm"], (0, -1.15, 0.012), (0.78, 1.02, 0.03))
    if level >= 3:
        for ix in range(3):
            for iy in range(2):
                mesh.box(MAT["stone_path"], (-0.45 + ix * 0.22, -1.22 + iy * 0.18, 0.04), (0.18, 0.14, 0.035), rz=0.08)

    mesh.box(MAT["stone_light"], (0, 0, 0.08), (body_w + 0.26, body_d + 0.24, 0.16))
    mesh.box(wall, (0, 0, 0.16 + body_h / 2), (body_w, body_d, body_h))
    mesh.box(MAT["roof_trim_light"], (0, -body_d / 2 - 0.04, 0.42 + body_h * 0.38), (0.92, 0.055, body_h * 0.58))
    mesh.gable_roof(roof, (0, 0, 0.24 + body_h), (body_w + 0.40, body_d + 0.30, 0.42))
    mesh.box(MAT["roof_trim_light"], (0, 0, 0.66 + body_h), (0.08, body_d + 0.46, 0.07))
    mesh.box(MAT["roof_trim_light"], (-0.56, -0.73, 0.48 + body_h), (0.12, 0.08, 0.18), rz=0.16)
    mesh.box(MAT["roof_trim_light"], (0.56, -0.73, 0.48 + body_h), (0.12, 0.08, 0.18), rz=-0.16)

    mesh.box(MAT["door_warm"] if not damaged else MAT["damage_char"], (0, -body_d / 2 - 0.045, 0.40), (0.34, 0.08, 0.48))
    mesh.box(MAT["beam_dark"], (0, -body_d / 2 - 0.105, 0.66), (0.46, 0.055, 0.07))
    add_front_windows(mesh, -body_d / 2 - 0.065, 0.55, damaged)
    if level >= 2:
        add_front_windows(mesh, -body_d / 2 - 0.065, 1.05, damaged)
        mesh.box(MAT["stone_light"], (-0.55, -body_d / 2 - 0.16, 0.86), (0.34, 0.14, 0.10))
        mesh.box(MAT["fence_white"], (-0.55, -body_d / 2 - 0.20, 0.98), (0.42, 0.055, 0.22))

    mesh.box(MAT["stone_light"], (0, -0.76, 0.12), (0.62, 0.24, 0.08))
    mesh.box(MAT["path_warm"], (0, -0.93, 0.075), (0.78, 0.18, 0.055))
    mesh.cylinder(MAT["brick_chimney"], (-0.42, 0.24, body_h + 0.74), 0.10, 0.48, segments=8)
    mesh.box(MAT["stone_light"], (-0.42, 0.24, body_h + 1.01), (0.30, 0.26, 0.07))

    if level >= 3:
        add_annex(mesh, damaged)
    if damaged:
        mesh.box(MAT["damage_char"], (0.30, -0.18, body_h + 0.42), (0.34, 0.30, 0.04), rz=0.24)
        mesh.box(MAT["damage_crack"], (-0.18, -body_d / 2 - 0.11, 0.62), (0.05, 0.045, 0.58), rz=-0.34)
        mesh.box(MAT["damage_char"], (-0.70, -0.94, 0.08), (0.62, 0.10, 0.055), rz=-0.35)


def add_annex(mesh, damaged=False):
    wall = MAT["wood_wall_shadow"] if damaged else MAT["wood_wall_pale"]
    roof = MAT["wood_wall_shadow"] if damaged else MAT["roof_cyan"]
    mesh.box(MAT["stone_light"], (0.96, 0.08, 0.08), (0.86, 0.98, 0.16))
    mesh.box(wall, (0.96, 0.08, 0.44), (0.74, 0.84, 0.58))
    mesh.gable_roof(roof, (0.96, 0.08, 0.76), (0.92, 1.00, 0.28))
    mesh.box(MAT["roof_trim_light"], (0.96, 0.08, 1.05), (0.06, 1.12, 0.055))
    mesh.box(MAT["door_warm"] if not damaged else MAT["damage_char"], (0.96, -0.37, 0.34), (0.28, 0.07, 0.40))
    mesh.box(MAT["window_blue"] if not damaged else MAT["damage_crack"], (1.28, -0.36, 0.50), (0.18, 0.05, 0.18))


def add_fence_and_yard(mesh, level, damaged=False):
    fence_mat = MAT["construction_plank"] if damaged else (MAT["fence_white"] if level >= 2 else MAT["roof_trim_light"])
    xs = [-1.42, -1.10, -0.78, 0.78, 1.10, 1.42]
    for x in xs:
        if damaged and x in (-1.10, 1.10):
            continue
        mesh.box(fence_mat, (x, 0.98, 0.24), (0.08, 0.08, 0.46))
    mesh.box(fence_mat, (0, 0.98, 0.33), (2.90, 0.055, 0.055))
    if level <= 2:
        for y in (-0.35, 0.02, 0.39):
            mesh.box(fence_mat, (-1.46, y, 0.24), (0.08, 0.08, 0.46))
            mesh.box(fence_mat, (1.46, y, 0.24), (0.08, 0.08, 0.46))
        mesh.box(fence_mat, (-1.46, 0.12, 0.33), (0.055, 1.18, 0.055))
        mesh.box(fence_mat, (1.46, 0.12, 0.33), (0.055, 1.18, 0.055))

    bed_x = -0.90 if level >= 3 else 0.82
    mesh.box(MAT["path_warm"], (bed_x, -0.94, 0.045), (0.68, 0.36, 0.045))
    for x, y, mat_name in [(bed_x - 0.16, -0.96, "flower_red"), (bed_x + 0.02, -0.90, "flower_yellow"), (bed_x + 0.20, -0.99, "flower_red")]:
        mesh.box(MAT["leaf_green"], (x, y, 0.10), (0.14, 0.10, 0.05), rz=0.3)
        mesh.box(MAT[mat_name], (x, y, 0.15), (0.07, 0.07, 0.06), rz=0.3)
    if level == 1:
        mesh.box(MAT["tool_metal"], (-0.54, -1.30, 0.055), (0.34, 0.055, 0.035), rz=0.15)
        mesh.box(MAT["construction_plank"], (-0.72, -1.32, 0.08), (0.07, 0.28, 0.045), rz=0.15)
        mesh.box(MAT["tool_metal"], (-0.12, -1.31, 0.055), (0.36, 0.05, 0.035), rz=-0.42)
        mesh.box(MAT["construction_plank"], (-0.30, -1.22, 0.08), (0.055, 0.26, 0.045), rz=-0.42)
    if level >= 2:
        mesh.cylinder(MAT["watering_can"], (0.88, -1.22, 0.12), 0.11, 0.16, segments=10)
        mesh.box(MAT["watering_can"], (1.02, -1.22, 0.14), (0.22, 0.055, 0.055), rz=0.2)
    if level >= 3:
        mesh.box(MAT["tool_metal"], (-0.62, -1.33, 0.055), (0.24, 0.055, 0.035), rz=0.2)
        mesh.box(MAT["construction_plank"], (-0.76, -1.33, 0.08), (0.055, 0.26, 0.045), rz=0.2)


def add_construction_overlay(mesh, level):
    h = 1.04 if level == 1 else 1.58
    for x in (-0.86, 0.86):
        mesh.cylinder(MAT["construction_plank"], (x, -0.72, h / 2), 0.035, h, segments=7)
    mesh.box(MAT["construction_plank"], (0, -0.72, h * 0.70), (1.82, 0.06, 0.065))
    mesh.box(MAT["construction_plank"], (0, -0.72, h), (1.92, 0.06, 0.065))
    mesh.box(MAT["construction_plank"], (-0.46, -0.72, h * 0.55), (0.06, 0.055, h * 0.95), rz=0.40)
    mesh.box(MAT["construction_plank"], (0.46, -0.72, h * 0.55), (0.06, 0.055, h * 0.95), rz=-0.40)
    for i in range(3):
        mesh.box(MAT["construction_plank"], (-1.05, -0.58, 0.075 + i * 0.055), (0.68, 0.13, 0.045), rz=0.08)
    if level >= 3:
        mesh.box(MAT["construction_plank"], (1.16, -0.36, 0.72), (0.88, 0.06, 0.06))
    for i, x in enumerate((-0.28, 0.0, 0.28)):
        mesh.box(MAT["dust"], (x, -1.00, 0.11 + i * 0.02), (0.22, 0.16, 0.08), rz=0.2 * i)


def build_state(level, state):
    mesh = MeshBuilder()
    damaged = state == "damaged"
    add_core_house(mesh, level, damaged=damaged)
    add_fence_and_yard(mesh, level, damaged=damaged)
    if state == "construction":
        add_construction_overlay(mesh, level)
    return mesh.parts


def append_aligned(buffer, data):
    while len(buffer) % 4:
        buffer.extend(b"\x00")
    offset = len(buffer)
    buffer.extend(data)
    return offset


def write_glb(path, parts):
    by_mat = {i: {"positions": [], "normals": [], "indices": []} for i in range(len(MATERIALS))}
    for mat_index, vertex, n in parts:
        group = by_mat[mat_index]
        group["indices"].append(len(group["positions"]))
        group["positions"].append(vertex)
        group["normals"].append(n)

    buffer = bytearray()
    buffer_views = []
    accessors = []
    primitives = []

    def add_accessor(raw, target, component_type, accessor_type, count, min_value=None, max_value=None):
        offset = append_aligned(buffer, raw)
        view_index = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(raw), "target": target})
        accessor = {"bufferView": view_index, "componentType": component_type, "count": count, "type": accessor_type}
        if min_value is not None:
            accessor["min"] = min_value
            accessor["max"] = max_value
        accessors.append(accessor)
        return len(accessors) - 1

    for mat_index, group in by_mat.items():
        if not group["positions"]:
            continue
        positions = group["positions"]
        normals = group["normals"]
        indices = group["indices"]
        pos_raw = b"".join(struct.pack("<3f", *p) for p in positions)
        nrm_raw = b"".join(struct.pack("<3f", *n) for n in normals)
        idx_raw = b"".join(struct.pack("<H", i) for i in indices)
        mins = [min(p[i] for p in positions) for i in range(3)]
        maxs = [max(p[i] for p in positions) for i in range(3)]
        pos_accessor = add_accessor(pos_raw, 34962, 5126, "VEC3", len(positions), mins, maxs)
        normal_accessor = add_accessor(nrm_raw, 34962, 5126, "VEC3", len(normals))
        index_accessor = add_accessor(idx_raw, 34963, 5123, "SCALAR", len(indices))
        primitives.append({
            "attributes": {"POSITION": pos_accessor, "NORMAL": normal_accessor},
            "indices": index_accessor,
            "material": mat_index,
            "mode": 4,
        })

    materials = []
    for name, color in MATERIALS:
        material = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": color, "roughnessFactor": 0.78, "metallicFactor": 0.0}}
        if color[3] < 1:
            material["alphaMode"] = "BLEND"
        materials.append(material)

    gltf = {
        "asset": {"version": "2.0", "generator": "Real City wood house l01-l03 generator"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": path.stem, "mesh": 0}],
        "meshes": [{"name": f"{path.stem}_mesh", "primitives": primitives}],
        "materials": materials,
        "buffers": [{"byteLength": len(buffer)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }

    json_chunk = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_chunk) % 4:
        json_chunk += b" "
    while len(buffer) % 4:
        buffer.extend(b"\x00")

    total_length = 12 + 8 + len(json_chunk) + 8 + len(buffer)
    with path.open("wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, total_length))
        fh.write(struct.pack("<I4s", len(json_chunk), b"JSON"))
        fh.write(json_chunk)
        fh.write(struct.pack("<I4s", len(buffer), b"BIN\x00"))
        fh.write(buffer)


def project(vertex):
    x, y, z = vertex
    return (256 + (x - y) * 62, 258 + (x + y) * 30 - z * 78)


def material_color(material, normal_vec):
    r, g, b, a = MATERIALS[material][1]
    nx, ny, nz = normal_vec
    light = 0.64 + max(0, nz) * 0.22 + max(0, -ny) * 0.16 + max(0, -nx) * 0.08
    return (int(r * 255 * min(light, 1.12)), int(g * 255 * min(light, 1.12)), int(b * 255 * min(light, 1.12)), int(a * 255))


def draw_png(path, parts):
    image = Image.new("RGBA", SPRITE_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", SPRITE_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((118, 272, 402, 350), fill=(0, 0, 0, 84))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    draw = ImageDraw.Draw(image)

    triangles = []
    for index in range(0, len(parts), 3):
        tri = parts[index:index + 3]
        if len(tri) != 3:
            continue
        mat_index = tri[0][0]
        verts = [item[1] for item in tri]
        n = tri[0][2]
        triangles.append((sum(v[0] + v[1] + v[2] * 0.9 for v in verts) / 3, mat_index, verts, n))
    for _, mat_index, verts, n in sorted(triangles):
        points = [project(v) for v in verts]
        draw.polygon(points, fill=material_color(mat_index, n))
        draw.line(points + [points[0]], fill=(25, 35, 25, 28), width=1)
    image.save(path)


def main():
    GLB_OUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for level in LEVELS:
        for state in STATES:
            parts = build_state(level, state)
            glb_path = GLB_OUT_DIR / f"wood_house_l{level:02d}_{state}.glb"
            png_path = PNG_OUT_DIR / f"wood_house_l{level:02d}_{state}.png"
            write_glb(glb_path, parts)
            draw_png(png_path, parts)
            print(glb_path)
            print(png_path)


if __name__ == "__main__":
    main()
