"""Generate the three seamless Real City road kits (16 masks x 4 states)."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.assets.blender.real_city.scene import setup_lighting, setup_render

OUTPUT = ROOT / "frontend/public/assets/buildings/roads"
SHAPES = {
    "single": "", "end_n": "n", "end_e": "e", "end_s": "s", "end_w": "w",
    "straight_ns": "ns", "straight_ew": "ew", "corner_ne": "ne", "corner_es": "es",
    "corner_sw": "sw", "corner_wn": "wn", "t_nes": "nes", "t_esw": "esw",
    "t_swn": "swn", "t_wne": "wne", "cross": "nesw",
}
STATES = ("active", "construction", "damaged", "ruined")
KITS = {
    "ground_road": {"name": "Грунтовая дорога", "surface": (0.58, 0.35, 0.21), "light": (0.72, 0.48, 0.29), "dark": (0.39, 0.24, 0.16), "edge": (0.65, 0.45, 0.28), "slab": (0.58, 0.35, 0.21)},
    "common_road": {"name": "Обычная дорога", "surface": (0.53, 0.51, 0.43), "light": (0.70, 0.67, 0.56), "dark": (0.36, 0.37, 0.32), "edge": (0.67, 0.61, 0.48), "slab": (0.53, 0.51, 0.43)},
    "paved_road": {"name": "Мостовая", "surface": (0.48, 0.47, 0.42), "light": (0.75, 0.70, 0.60), "dark": (0.32, 0.33, 0.31), "edge": (0.68, 0.57, 0.44), "slab": (0.56, 0.55, 0.49)},
}
GRID = (-1.8, -1.1, 1.1, 1.8)
PORT_Z = 0.055


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Roughness"].default_value = 0.87
    return mat


def surface_texture(kit, mat, output):
    """Stable hand-painted-like color variation embedded into exported GLBs."""
    size = 256
    image = bpy.data.images.new("TEX_" + kit + "_surface", width=size, height=size, alpha=True)
    rng = random.Random(int.from_bytes(hashlib.sha256(kit.encode()).digest()[:8], "big"))
    coarse = [[rng.uniform(-1, 1) for _ in range(18)] for _ in range(18)]
    palette = KITS[kit]
    base = palette["surface"]
    pixels = [0.0] * (size * size * 4)
    for y in range(size):
        for x in range(size):
            gx, gy = x * 16 / size, y * 16 / size
            ix, iy = int(gx), int(gy)
            fx, fy = gx - ix, gy - iy
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            a = coarse[iy][ix] * (1 - fx) + coarse[iy][ix + 1] * fx
            b = coarse[iy + 1][ix] * (1 - fx) + coarse[iy + 1][ix + 1] * fx
            variation = (a * (1 - fy) + b * fy) * 0.15 + rng.uniform(-0.025, 0.025)
            if kit == "ground_road":
                variation += 0.025 * math.sin((x + y * 0.45) * 0.15)
            elif kit == "common_road":
                if rng.random() < 0.12:
                    variation += rng.choice((-0.15, 0.11))
            else:
                row = y // 26
                shifted = (x + (13 if row % 2 else 0)) % 38
                joint = y % 26 < 2 or shifted < 2
                variation += -0.15 if joint else 0.025 * ((row * 7 + x // 38) % 5 - 2)
            offset = (y * size + x) * 4
            for channel in range(3):
                pixels[offset + channel] = max(0.03, min(0.95, base[channel] + variation))
            pixels[offset + 3] = 1
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(output / f"{kit}_surface.png")
    image.file_format = "PNG"
    image.save()
    image.pack()
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Base Color"])


def make_box(collection, name, xyz, size, mat, angle=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    obj.rotation_euler.z = angle
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for parent in list(obj.users_collection):
        parent.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def make_chip(collection, name, x, y, rx, ry, mat, rng, height=0.015):
    sides = 7
    phase = rng.uniform(0, math.tau)
    vertices = []
    for z in (0.056, 0.056 + height):
        for i in range(sides):
            angle = phase + i * math.tau / sides
            radius = rng.uniform(0.82, 1.08)
            vertices.append((x + math.cos(angle) * rx * radius, y + math.sin(angle) * ry * radius, z))
    faces = [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))]
    faces += [(i, (i + 1) % sides, (i + 1) % sides + sides, i + sides) for i in range(sides)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="road_xy")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            point = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = ((point.x + 1.8) / 3.6, (point.y + 1.8) / 3.6)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def road_cells(dirs):
    cells = {(1, 1)}
    for d, cell in (("w", (0, 1)), ("e", (2, 1)), ("s", (1, 0)), ("n", (1, 2))):
        if d in dirs:
            cells.add(cell)
    return cells


def road_mesh(collection, dirs, mat):
    """One closed mesh with shared top vertices; no overlapping center plates."""
    cells = road_cells(dirs)
    vertices, faces, lookup = [], [], {}

    def v(co):
        key = tuple(round(x, 6) for x in co)
        if key not in lookup:
            lookup[key] = len(vertices)
            vertices.append(co)
        return lookup[key]

    for i, j in sorted(cells):
        x0, x1, y0, y1 = GRID[i], GRID[i + 1], GRID[j], GRID[j + 1]
        top = [v(p) for p in ((x0, y0, PORT_Z), (x1, y0, PORT_Z), (x1, y1, PORT_Z), (x0, y1, PORT_Z))]
        bot = [v(p) for p in ((x0, y0, 0.028), (x1, y0, 0.028), (x1, y1, 0.028), (x0, y1, 0.028))]
        faces.append(tuple(top))
        faces.append(tuple(reversed(bot)))
        for neighbor, edge in (
            ((i, j - 1), (0, 1)), ((i + 1, j), (1, 2)),
            ((i, j + 1), (2, 3)), ((i - 1, j), (3, 0)),
        ):
            if neighbor not in cells:
                a, b = edge
                faces.append((top[b], top[a], bot[a], bot[b]))
    mesh = bpy.data.meshes.new("SM_road_connected_surface")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def inside(x, y, dirs, margin=0.0):
    if abs(x) < 1.1 - margin and abs(y) < 1.1 - margin:
        return True
    return (("n" in dirs and y > 1.1 and abs(x) < 1.1 - margin) or
            ("s" in dirs and y < -1.1 and abs(x) < 1.1 - margin) or
            ("e" in dirs and x > 1.1 and abs(y) < 1.1 - margin) or
            ("w" in dirs and x < -1.1 and abs(y) < 1.1 - margin))


def safe_detail(x, y, dirs, margin=0.09):
    return abs(x) < 1.54 and abs(y) < 1.54 and inside(x, y, dirs, margin)


def dress(collection, kit, state, dirs, mats, seed):
    rng = random.Random(seed)
    placed = []

    def free_point(x, y, distance):
        if not safe_detail(x, y, dirs, 0.17):
            return False
        if any((x - px) ** 2 + (y - py) ** 2 < distance ** 2 for px, py in placed):
            return False
        placed.append((x, y))
        return True
    # Large readable construction cues, all kept away from the shared port.
    if kit == "ground_road":
        for k in range(105):
            x, y = rng.uniform(-1.45, 1.45), rng.uniform(-1.45, 1.45)
            if free_point(x, y, 0.23):
                make_chip(collection, "SM_compacted_clay", x, y, rng.uniform(0.07, 0.19), rng.uniform(0.035, 0.10), mats["light" if k % 4 else "dark"], rng, 0.005)
    elif kit == "paved_road":
        # A dense staggered cut-stone field; the flat base remains continuous at all ports.
        for row in range(11):
            y = -1.45 + row * 0.29
            for col in range(9):
                x = -1.45 + col * 0.36 + (0.15 if row % 2 else 0)
                if safe_detail(x, y, dirs, 0.22):
                    make_box(collection, "SM_cut_paver", (x, y, 0.066), (0.33, 0.25, 0.015), mats["light" if (row + col) % 7 == 0 else "slab"])
    else:
        for idx in range(180):
            x, y = rng.uniform(-1.48, 1.48), rng.uniform(-1.48, 1.48)
            if free_point(x, y, 0.15):
                make_chip(collection, "SM_graded_stone", x, y, rng.uniform(0.04, 0.11), rng.uniform(0.035, 0.09), mats["light" if idx % 3 else "dark"], rng, 0.014)

    # Exterior shoulder stones follow the open mask and never cross a port.
    for x, y, horizontal in ((-1.17, 0, False), (1.17, 0, False), (0, -1.17, True), (0, 1.17, True)):
        if not inside(x, y, dirs, 0.01):
            if kit != "ground_road":
                make_box(collection, "SM_shoulder_edge", (x, y, 0.073), (1.28, 0.075, 0.038) if horizontal else (0.075, 1.28, 0.038), mats["edge"])
            else:
                for offset in (-0.38, 0, 0.38):
                    px, py = (offset, y) if horizontal else (x, offset)
                    make_box(collection, "SM_clay_shoulder", (px, py, 0.063), (0.28, 0.13, 0.016), mats["light"], rng.uniform(-0.2, 0.2))

    if state == "construction":
        supplies = []
        for k in range(5):
            x, y = rng.uniform(-0.77, 0.77), rng.uniform(-0.77, 0.77)
            if all((x - px) ** 2 + (y - py) ** 2 > 0.28 ** 2 for px, py in supplies):
                supplies.append((x, y))
                make_box(collection, "SM_unlaid_material", (x, y, 0.098), (0.24, 0.15, 0.038), mats["light"], rng.uniform(-0.4, 0.4))
    elif state in ("damaged", "ruined"):
        count = 7 if state == "damaged" else 14
        debris = []
        for k in range(count * 3):
            x, y = rng.uniform(-0.83, 0.83), rng.uniform(-0.83, 0.83)
            if all((x - px) ** 2 + (y - py) ** 2 > 0.32 ** 2 for px, py in debris):
                debris.append((x, y))
                make_box(collection, "SM_broken_surface", (x, y, 0.105), (rng.uniform(0.14, 0.27), rng.uniform(0.10, 0.20), 0.025), mats["dark" if k % 4 == 0 else "light"], rng.uniform(-0.5, 0.5))
                if len(debris) >= count:
                    break


def setup():
    scene = bpy.data.scenes.new("Real_City_Road_Kits_V2")
    bpy.context.window.scene = scene
    scene.unit_settings.system = "METRIC"
    from tools.assets.blender.real_city.scene import setup_isometric_camera
    from tools.assets.blender.real_city.constants import RenderProfile
    profile = RenderProfile(sprite_size=(512, 512), anchor=(256, 320), tile_size=3.6, ground_pixel_width=480, view_transform="Standard")
    setup_isometric_camera(scene, profile)
    setup_lighting(scene, prefix="road_v2")
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= 0.27
    setup_render(scene, profile)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 6
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    return scene


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--kits", nargs="*", default=list(KITS))
    parser.add_argument("--shapes", nargs="*", default=list(SHAPES))
    parser.add_argument("--states", nargs="*", default=list(STATES))
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    scene = setup()
    grass = material("MAT_road_grass", (0.43, 0.50, 0.30))
    for kit in args.kits:
        colors = KITS[kit]
        mats = {role: material("MAT_" + kit + "_" + role, colors[role]) for role in ("surface", "light", "dark", "edge", "slab")}
        out = args.output / kit
        out.mkdir(parents=True, exist_ok=True)
        surface_texture(kit, mats["surface"], out)
        records = {}
        kit_collections = []
        for shape in args.shapes:
            for state in args.states:
                name = f"{kit}_{shape}_{state}"
                collection = bpy.data.collections.new(name)
                scene.collection.children.link(collection)
                kit_collections.append(collection)
                make_box(collection, "SM_road_grass_tile", (0, 0, 0.002), (3.6, 3.6, 0.006), grass)
                surface = road_mesh(collection, SHAPES[shape], mats["surface"])
                seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
                dress(collection, kit, state, SHAPES[shape], mats, seed)
                for obj in scene.objects:
                    obj.select_set(False)
                for obj in collection.objects:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = surface
                glb = out / f"{name}.glb"
                bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True)
                scene.render.filepath = str(out / f"{name}.png")
                bpy.ops.render.render(write_still=True)
                tris = sum(sum(len(poly.vertices) - 2 for poly in obj.data.polygons) for obj in collection.objects if obj.type == "MESH")
                records[name] = {"shape": shape, "state": state, "triangles": tris, "objects": len(collection.objects), "png": f"{name}.png", "glb": glb.name}
                print("ROAD_ASSET", name, tris, flush=True)
                if args.preview:
                    bpy.data.collections.remove(collection, do_unlink=True)
                else:
                    collection.hide_render = True
        if not args.preview:
            (out / "manifest.json").write_text(json.dumps({"id": kit, "building_type": "road", "display_name": colors["name"], "style": "Aeolian handcrafted modular roads v2", "size": [512, 512], "footprint": 3.6, "anchor": [256, 320], "levels": [1], "shapes": list(SHAPES), "states": list(STATES), "port": {"width": 2.2, "height": PORT_Z}, "assets": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for collection in kit_collections:
                collection.hide_render = False
            bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{kit}.blend"))
            for collection in kit_collections:
                bpy.data.collections.remove(collection, do_unlink=True)


if __name__ == "__main__":
    main()
