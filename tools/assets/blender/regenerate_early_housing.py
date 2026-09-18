"""Run through Blender MCP; build(), export_one(), finish() are separate steps."""

import json
import math
from pathlib import Path

import bpy
import bmesh
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
STATES = ("active", "construction", "damaged")
MATS = {}
COL = None
PREFIX = ""
REPORT = {}


def material(role, color):
    mat = bpy.data.materials.new("MAT_housing_" + role)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.78
    if role == "glass":
        shader.inputs["Emission Color"].default_value = (*color, 1)
        shader.inputs["Emission Strength"].default_value = 0.15
    MATS[role] = mat


def palette():
    for role, color in {
        "earth": (0.30, 0.16, 0.075), "grass": (0.24, 0.48, 0.065),
        "wood": (0.62, 0.34, 0.12), "beam": (0.19, 0.075, 0.029),
        "stone": (0.48, 0.48, 0.38), "roof": (0.48, 0.095, 0.047),
        "accent": (0.045, 0.34, 0.33), "glass": (1.0, 0.57, 0.14),
        "char": (0.045, 0.029, 0.021),
        "windleaf": (0.035, 0.30, 0.025), "leaf_light": (0.12, 0.44, 0.035),
    }.items():
        material(role, color)


def attach(obj, name, role):
    obj.name = PREFIX + "_" + name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    COL.objects.link(obj)
    obj.data.materials.append(MATS[role])
    return obj


def box(name, pos, size, role, bevel=0.02, rotation=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vertex in bm.verts:
        for axis in range(3):
            vertex.co[axis] *= size[axis]
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.24), segments=1, affect="EDGES")
    data = bpy.data.meshes.new(PREFIX + "_" + name)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(data.name, data)
    COL.objects.link(obj)
    data.materials.append(MATS[role])
    obj.location = pos
    obj.rotation_euler = rotation
    return obj


def mesh(name, verts, faces, role):
    data = bpy.data.meshes.new(PREFIX + "_" + name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(data.name, data)
    COL.objects.link(obj)
    data.materials.append(MATS[role])
    return obj


def beam(name, a, b, width, role="beam"):
    delta = Vector(b) - Vector(a)
    obj = box(name, (Vector(a) + Vector(b)) / 2, (width, width, delta.length), role)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def log(name, a, b, radius=0.075):
    delta = Vector(b) - Vector(a)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10, radius1=radius, radius2=radius, depth=delta.length)
    data = bpy.data.meshes.new(PREFIX + "_" + name)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(data.name, data)
    COL.objects.link(obj)
    obj.location = (Vector(a) + Vector(b)) / 2
    data.materials.append(MATS["beam"])
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(MATS["wood"])
    for face in obj.data.polygons:
        face.material_index = int(len(face.vertices) > 4)
    return obj


def base():
    box("earth_tile", (0, 0, -0.075), (3.6, 3.6, 0.15), "earth", 0.07)
    box("grass_tile", (0, 0, 0.015), (3.58, 3.58, 0.10), "grass", 0.06)
    for i in range(3):
        box("path_stone", (0.05 * math.sin(i), -1.12 - 0.23 * i, 0.08),
            (0.48, 0.21, 0.07), "stone", 0.04, (0, 0, 0.09 * (i - 1)))


def mound(level, damaged):
    rx, ry, height = 1.10 + 0.06 * level, 0.90 + 0.045 * level, 0.79 + 0.09 * level
    for shell, scale, role in (("earth_mound", 1, "earth"), ("turf_cap", 1.006, "grass")):
        verts, faces = [], []
        rings, segments = 7, 24
        for j in range(rings):
            t = j / (rings - 1)
            radius = 1 - 0.97 * t
            for i in range(segments):
                angle = i * math.tau / segments
                wobble = 1 + 0.035 * math.sin(angle * 3 + t * 2)
                x = rx * radius * math.cos(angle) * wobble * scale
                y = 0.22 + ry * radius * math.sin(angle) * scale
                z = 0.08 + height * math.sqrt(max(0, 1 - radius * radius))
                if shell == "turf_cap":
                    z += 0.055 + 0.025 * math.sin(angle * 5) * (1 - t)
                if damaged and x > 0.35 and y < 0.2:
                    z -= 0.10 * (1 - t)
                verts.append((x, y, z))
        for j in range(rings - 1):
            for i in range(segments):
                a = j * segments + i
                b = j * segments + (i + 1) % segments
                faces.append((a, b, b + segments, a + segments))
        faces.extend([tuple(reversed(range(segments))), tuple(range((rings - 1) * segments, rings * segments))])
        obj = mesh(shell, verts, faces, role)
        if shell == "turf_cap" and damaged:
            obj.data.materials.append(MATS["earth"])
        for face in obj.data.polygons:
            face.use_smooth = len(face.vertices) == 4
            if shell == "turf_cap" and damaged and face.center.x > 0.30 and -0.3 < face.center.y < 0.3:
                face.material_index = 1


def door(y, top, damaged=False):
    bottom = 0.15
    box("door_recess", (-0.14, y, (top + bottom) / 2), (0.64, 0.15, top - bottom), "beam")
    for i in range(4):
        box("door_plank", (-0.35 + 0.14 * i, y - 0.10, (top + bottom) / 2),
            (0.13, 0.08, top - bottom - 0.06), "char" if damaged and i == 2 else "wood")
    for x in (-0.51, 0.23):
        box("door_jamb", (x, y - 0.02, (top + bottom) / 2), (0.11, 0.22, top - bottom + 0.14), "beam")
    box("door_lintel", (-0.14, y - 0.04, top + 0.05), (0.90, 0.23, 0.15), "wood")
    for z in (bottom + 0.16, top - 0.15):
        box("door_strap", (-0.14, y - 0.15, z), (0.53, 0.04, 0.055), "beam", 0.007)
    box("door_handle", (0.04, y - 0.185, 0.48), (0.07, 0.055, 0.07), "stone", 0.01)


def window(x, y, z, width=0.39, height=0.43, damaged=False, side=False):
    before = set(COL.objects)
    box("window_recess", (x, y, z), (width + 0.12, 0.12, height + 0.10), "beam")
    box("window_glass", (x, y - 0.075, z), (width, 0.025, height), "char" if damaged else "glass", 0)
    for dx in (-width / 2 - 0.025, 0, width / 2 + 0.025):
        box("window_frame", (x + dx, y - 0.12, z), (0.045, 0.06, height + 0.09), "wood", 0.007)
    for dz in (-height / 2, height / 2):
        box("window_frame", (x, y - 0.12, z + dz), (width + 0.14, 0.07, 0.06), "wood", 0.008)
    box("window_sill", (x, y - 0.16, z - height / 2 - 0.045), (width + 0.25, 0.25, 0.08), "wood")
    for dx in (-width / 2 - 0.15, width / 2 + 0.15):
        box("shutter", (x + dx, y - 0.05, z), (0.17, 0.07, height), "accent")
    if damaged:
        beam("broken_window_board", (x - width / 2, y - 0.17, z - height / 3),
             (x + width / 2, y - 0.17, z + height / 3), 0.055, "wood")
    if side:
        pivot = Vector((x, y, z))
        for obj in set(COL.objects) - before:
            offset = obj.location - pivot
            obj.location = pivot + Vector((-offset.y, offset.x, offset.z))
            obj.rotation_euler.z += math.pi / 2


def chimney(x, y, bottom, height, damaged=False):
    for i in range(4):
        box("chimney_course", (x + (0.025 if damaged and i == 3 else 0), y, bottom + height * (i + 0.5) / 4),
            (0.27, 0.29, height / 4 - 0.01), "stone")
    z = bottom + height
    for dx in (-0.14, 0.14):
        box("chimney_rim", (x + dx, y, z), (0.08, 0.40, 0.10), "stone")
    for dy in (-0.16, 0.16):
        box("chimney_rim", (x, y + dy, z), (0.24, 0.08, 0.10), "stone")
    box("chimney_soot", (x, y, z - 0.07), (0.20, 0.22, 0.025), "char", 0)


def fence(level):
    for y in (0.1, 0.65, 1.2):
        box("fence_post", (1.48, y, 0.30), (0.105, 0.12, 0.48), "beam")
    for z in (0.23, 0.43):
        box("fence_rail", (1.48, 0.65, z), (0.08, 1.25, 0.08), "wood")


def barrel(x, y):
    verts, faces = [], []
    for z, radius in ((0.08, 0.15), (0.14, 0.18), (0.32, 0.195), (0.48, 0.16)):
        for i in range(12):
            angle = i * math.tau / 12
            verts.append((x + radius * math.cos(angle), y + radius * math.sin(angle), z))
    for j in range(3):
        for i in range(12):
            faces.append((j * 12 + i, j * 12 + (i + 1) % 12, (j + 1) * 12 + (i + 1) % 12, (j + 1) * 12 + i))
    faces += [tuple(reversed(range(12))), tuple(range(36, 48))]
    mesh("barrel_staves", verts, faces, "wood")
    for z, radius in ((0.16, 0.186), (0.39, 0.187)):
        verts, faces = [], []
        for i in range(12):
            a = i * math.tau / 12
            for j in range(4):
                b = j * math.tau / 4
                r = radius + 0.021 * math.cos(b)
                verts.append((x + r * math.cos(a), y + r * math.sin(a), z + 0.021 * math.sin(b)))
        for i in range(12):
            for j in range(4):
                faces.append((i * 4 + j, ((i + 1) % 12) * 4 + j, ((i + 1) % 12) * 4 + (j + 1) % 4, i * 4 + (j + 1) % 4))
        mesh("barrel_hoop", verts, faces, "beam")


def yard(level, wood=False):
    if level >= 2 or wood:
        for i in range(3):
            log("firewood", (-1.37 + 0.16 * i, -0.63, 0.18), (-1.37 + 0.16 * i, -0.10, 0.18), 0.075)
        log("firewood_top", (-1.21, -0.60, 0.31), (-1.21, -0.13, 0.31), 0.075)
    if level >= 3 or (wood and level >= 2):
        fence(level)
    if level >= 4 or wood:
        barrel(1.35, -0.65)
        for x in (0.55, 1.07):
            box("bench_leg", (x, -1.10, 0.21), (0.09, 0.22, 0.28), "beam")
        box("bench_seat", (0.81, -1.10, 0.38), (0.76, 0.28, 0.08), "wood")
    for x, y in ((-1.5, 0.7), (1.4, 1.1), (1.55, -1.35)):
        for i in range(3):
            beam("windleaf", (x, y, 0.08), (x + (i - 1) * 0.08, y + 0.06 * (i % 2), 0.25 + 0.06 * (i % 2)), 0.055, "grass")


def canopy(y, z, width=1.1):
    for i in range(5):
        box("canopy_board", (-width / 2 + width * (i + 0.5) / 5 - 0.14, y, z),
            (width / 5 - 0.01, 0.46, 0.075), "wood", rotation=(0.10, 0, 0))
    for x in (-width / 2 - 0.14, width / 2 - 0.14):
        beam("canopy_bracket", (x, y + 0.13, z - 0.37), (x, y - 0.18, z - 0.07), 0.08)


def dugout(level, damaged):
    base()
    mound(level, damaged)
    top = 0.74 + level * 0.065
    y = -0.64 - level * 0.025
    width = 0.9 + 0.11 * level
    for i in range(5 if level < 4 else 8):
        count = 5 if level < 4 else 8
        x = -width / 2 + width * (i + 0.5) / count
        box("retaining_facade", (x, y + 0.06, 0.50), (width / count - 0.012, 0.17, 0.90), "beam" if level < 4 else "wood")
    door(y - 0.07, top, damaged)
    for side in (-1, 1):
        log("roof_support", (side * width / 2, y, 0.12), (side * width / 2, y + 0.25, top + 0.10), 0.065)
    if level >= 2:
        for side in (-1, 1):
            for course in range(3):
                log("retaining_log", (side * (0.94 + level * 0.03), -0.53, 0.18 + course * 0.14),
                    (side * (0.94 + level * 0.03), 0.91, 0.18 + course * 0.14), 0.09)
        log("heavy_entry_lintel", (-0.72, y - 0.08, top + 0.13), (0.60, y - 0.08, top + 0.13), 0.11)
    if level >= 3:
        leaf_roof(level)
    if level >= 3:
        for side in (-1, 1):
            beam("side_brace", (side * (width / 2 + 0.20), y + 0.18, 0.12), (side * width / 2, y + 0.35, top), 0.10)
    if level >= 4:
        canopy(y - 0.27, top + 0.22)
        window(0.53, y - 0.08, 0.65, 0.21, 0.25, damaged)
    if level == 5:
        box("entry_platform", (-0.14, y - 0.31, 0.15), (1.0, 0.43, 0.14), "wood")
        for x in (-0.65, 0.38):
            beam("porch_post", (x, y - 0.43, 0.12), (x, y - 0.43, top + 0.18), 0.075, "wood")
        for course in range(3):
            z = 0.15 + course * 0.115
            for side in (-1, 1):
                box("perimeter_foundation_side", (side * 1.40, 0.22, z), (0.13, 2.42, 0.11), "wood")
            box("perimeter_foundation_back", (0, 1.40, z), (2.92, 0.14, 0.11), "wood")
            for x in (-0.98, 0.89):
                box("perimeter_foundation_front", (x, -0.98, z), (0.84, 0.14, 0.11), "wood")
    chimney(-0.43, 0.46, 0.76 + 0.075 * level, 0.29 + 0.055 * level, damaged)
    for i in range(3 + level):
        a = i * math.pi / (2 + level)
        box("mound_border_stone", (1.2 * math.cos(a), 0.22 + 1.0 * math.sin(a), 0.12), (0.23, 0.20, 0.17), "stone", 0.045, (0, 0, a))
    yard(level)
    if damaged:
        box("fallen_support", (0.60, -1.40, 0.16), (0.68, 0.13, 0.12), "char", rotation=(0, 0, 0.38))


def leaf_roof(level):
    # Large overlapping, closed leaf meshes follow the mound surface.
    rows, columns = {3: (3, 9), 4: (5, 14), 5: (7, 18)}[level]
    rx, ry, height = 1.10 + 0.06 * level, 0.90 + 0.045 * level, 0.79 + 0.09 * level
    for row in range(rows):
        radius = 0.27 + row / max(1, rows - 1) * 0.59
        for col in range(columns):
            angle = math.tau * (col + (row % 2) * 0.5) / columns
            if level == 3 and -1.9 < angle - math.tau < -0.7:
                continue
            x, y = rx * radius * math.cos(angle), 0.22 + ry * radius * math.sin(angle)
            z = 0.18 + height * math.sqrt(1 - radius * radius)
            length = 0.42 if level == 3 else 0.46
            width = 0.25 if level == 3 else 0.30
            tangent = Vector((-math.sin(angle), math.cos(angle), 0))
            down = Vector((math.cos(angle), math.sin(angle), -radius / math.sqrt(1-radius*radius) * height / rx)).normalized()
            normal = tangent.cross(down).normalized()
            if normal.z < 0: normal.negate()
            center = Vector((x, y, z))
            outline = [center-down*length/2, center-tangent*width/2,
                       center+down*length/2, center+tangent*width/2]
            for point in outline:
                radial=(point.x/rx)**2+((point.y-0.22)/ry)**2
                point.z=0.17+height*math.sqrt(max(0,1-radial))
            verts = [tuple(v) for v in outline] + [tuple(center+normal*0.055), tuple(center-normal*0.018)]
            faces = [(i, (i+1)%4, 4) for i in range(4)] + [((i+1)%4, i, 5) for i in range(4)]
            mesh("windleaf_roof", verts, faces, "leaf_light" if (row+col)%3 == 0 else "windleaf")


def roof(width, depth, eaves, rise, damaged=False, cx=0, cy=0, rows=4, cols=7):
    def height(x):
        t = abs(x) / (width / 2)
        return eaves + rise * (1 - t) + 0.13 * t * t
    for side in (-1, 1):
        for row in range(rows):
            a, b = side * width / 2 * row / rows, side * width / 2 * (row + 1) / rows
            for col in range(cols):
                if damaged and side == 1 and row == 2 and col in (1, 2):
                    continue
                ya = cy - depth / 2 + col * depth / cols
                yb = ya + depth / cols - 0.012
                verts = [(cx + a, ya, height(a)), (cx + b, ya, height(b)), (cx + b, yb, height(b)), (cx + a, yb, height(a))]
                verts += [(x, y, z - 0.065) for x, y, z in verts]
                obj = mesh("roof_shingle", verts, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], "char" if damaged and row == 2 and col == 3 else "roof")
                # Consistent normals on both mirrored roof slopes.
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
                bm.to_mesh(obj.data)
                bm.free()
        for y in (cy - depth / 2 - 0.015, cy + depth / 2 + 0.015):
            for row in range(rows):
                a, b = side * width / 2 * row / rows, side * width / 2 * (row + 1) / rows
                beam("curved_bargeboard", (cx + a, y, height(a)), (cx + b, y, height(b)), 0.095, "wood")
        beam("eave_trim", (cx + side * width / 2, cy - depth / 2, height(width / 2)),
             (cx + side * width / 2, cy + depth / 2, height(width / 2)), 0.09, "accent")
    beam("ridge_cap", (cx, cy - depth / 2 - 0.06, eaves + rise + 0.03), (cx, cy + depth / 2 + 0.06, eaves + rise + 0.03), 0.12, "wood")


def wood_house(level, damaged):
    base()
    width, depth, h = 1.48 + 0.13 * level, 1.27 + 0.08 * level, 1.05 + 0.12 * level
    if level >= 5:
        h += 0.48
    floor = 0.24
    box("foundation", (0, 0, 0.16), (width + 0.20, depth + 0.16, 0.24), "stone", 0.06)
    for i in range(7):
        z = floor + (i + 0.5) * h / 7
        for y in (-depth / 2, depth / 2):
            box("wall_siding", (0, y, z), (width, 0.12, h / 7 - 0.014), "char" if damaged and i in (2, 3) and y < 0 else "wood", bevel=0.02 if y < 0 else 0)
        for x in (-width / 2, width / 2):
            box("wall_siding", (x, 0, z), (0.12, depth, h / 7 - 0.014), "wood", bevel=0.02 if x > 0 else 0)
    for x in (-width / 2, width / 2):
        for y in (-depth / 2, depth / 2):
            box("corner_timber", (x, y, floor + h / 2), (0.16, 0.17, h + 0.10), "beam")
    eaves, rise = floor + h, 0.62 + 0.05 * level
    for y in (-depth / 2, depth / 2):
        verts = [(-width / 2, y - 0.06, eaves), (width / 2, y - 0.06, eaves), (0, y - 0.06, eaves + rise), (-width / 2, y + 0.06, eaves), (width / 2, y + 0.06, eaves), (0, y + 0.06, eaves + rise)]
        mesh("gable_wall", verts, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], "wood")
        box("gable_crossbeam", (0, y - 0.05, eaves), (width + 0.12, 0.16, 0.13), "beam")
    roof(width + 0.40, depth + 0.40, eaves, rise, damaged)
    door(-depth / 2 - 0.08, floor + 0.83, damaged)
    window(width / 2 + 0.08, 0.02, floor + 0.62, damaged=damaged, side=True)
    window(0.53, -depth / 2 - 0.085, floor + 0.62, 0.25, 0.35, damaged)
    canopy(-depth / 2 - 0.30, floor + 1.0, 0.95)
    box("porch", (-0.14, -depth / 2 - 0.32, 0.17), (0.92, 0.50, 0.20), "wood")
    chimney(-0.52, 0.28, eaves + 0.27, 0.68, damaged)
    if level >= 2:
        for x in (-0.70, 0.72):
            beam("facade_brace", (x, -depth / 2 - 0.1, eaves - 0.4), (x * 0.55, -depth / 2 - 0.1, eaves - 0.06), 0.08)
    if level == 3 or level >= 6:
        # A projecting attic window makes the third level distinct in isometry.
        box("dormer_body", (0.31, -0.50, eaves + 0.36), (0.68, 1.20, 0.59), "wood")
        window(0.31, -1.13, eaves + 0.40, 0.28, 0.30, damaged)
        roof(0.86, 1.40, eaves + 0.66, 0.27, damaged=False, cx=0.31, cy=-0.50, rows=2, cols=3)
    if level >= 4:
        for x in (-width/2, width/2):
            for y in (-depth/2, depth/2):
                for course in range(2 if level < 6 else 4):
                    box("stone_reinforcement", (x,y,0.28+course*0.19),
                        (0.30,0.29,0.18), "stone", 0.025)
        # The wing stays inside the same tile and projects toward the visible side.
        ax, ay, aw, ad, ah = width/2+0.17, 0.17, 0.66, 1.12, 1.0
        box("annex_foundation", (ax,ay,0.17), (aw+0.12,ad+0.1,0.25), "stone", 0.04)
        for row in range(6):
            z=0.28+(row+0.5)*ah/6
            for y in (ay-ad/2,ay+ad/2):
                box("annex_wall_siding", (ax,y,z), (aw,0.1,ah/6-0.01), "wood",0.015)
            box("annex_wall_siding", (ax+aw/2,ay,z), (0.1,ad,ah/6-0.01), "wood",0.015)
        roof(aw+0.16,ad+0.20,1.28,0.28,cx=ax,cy=ay,rows=2,cols=4)
        window(ax+aw/2+0.06,ay,0.88,0.34,0.42,side=True)
        window(-0.60,-depth/2-0.085,0.92,0.32,0.42)
        if level >= 5:
            for x in (-0.57,0.56):
                window(x,-depth/2-0.085,1.94,0.37,0.47)
            window(width/2+0.08,0.05,1.94,0.42,0.47,side=True)
            box("upper_floor_crossbeam",(0,-depth/2-0.08,1.5),(width+0.12,0.15,0.14),"beam")
            box("balcony_floor",(0,-depth/2-0.28,1.63),(1.48,0.5,0.11),"wood")
            for x in (-0.69,-0.35,0,0.35,0.69):
                box("balcony_post",(x,-depth/2-0.50,1.85),(0.06,0.06,0.42),"wood")
            box("balcony_rail",(0,-depth/2-0.50,2.06),(1.48,0.08,0.08),"accent")
        if level >= 6:
            for y in (-depth/2,depth/2):
                for x in (-0.83,0.83):
                    for course in range(4):
                        box("stone_block_reinforcement",(x,y-0.06,0.38+course*0.20),(0.36,0.20,0.19),"stone",0.018)
    yard(level, wood=True)
    if damaged:
        for i in range(3):
            box("fallen_roof_shingle", (0.65 + i * 0.15, -1.40, 0.12), (0.25, 0.19, 0.065), "roof", rotation=(0, 0.12 * i, i * 0.7))


def construction(kind, level):
    h = 1.12 + 0.09 * level if kind == "dugout" else 1.52 + 0.12 * level
    for x in (-1.47, 1.47):
        for y in (-0.98, 0.65):
            box("scaffold_upright", (x, y, h / 2 + 0.06), (0.085, 0.085, h), "wood")
        for z in (0.50, h - 0.20):
            box("scaffold_rail", (x, -0.165, z), (0.07, 1.76, 0.09), "wood")
        beam("scaffold_diagonal", (x, -0.94, 0.18), (x, 0.60, h - 0.14), 0.07)
        for dx in (-0.075, 0.075):
            box("scaffold_deck", (x + dx, -0.16, h - 0.42), (0.14, 1.80, 0.06), "wood")
    for x in (-1.4, -1.03):
        beam("ladder_side", (x, -1.48, 0.08), (x, -0.92, h - 0.40), 0.055)
    for i in range(5):
        t = (i + 1) / 6
        beam("ladder_rung", (-1.4, -1.48 + 0.56 * t, 0.08 + (h - 0.48) * t), (-1.03, -1.48 + 0.56 * t, 0.08 + (h - 0.48) * t), 0.05, "wood")
    for i in range(3):
        box("spare_boards", (0.8, 1.36, 0.14 + i * 0.07), (0.82, 0.26, 0.065), "wood")


def clean_meshes(collection):
    bpy.context.view_layer.update()
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        obj.data.transform(obj.matrix_world)
        obj.matrix_world.identity()
        obj.data.calc_loop_triangles()
    bpy.context.view_layer.update()


def setup_camera(scene):
    data = bpy.data.cameras.new("housing_isometric_camera")
    cam = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(cam)
    cam.location = (8, -8, math.sqrt(128) / math.sqrt(3))
    cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = 512 * 3.6 * math.sqrt(2) / 278
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 512, 384
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    target_y = 1 - 292 / 384
    initial = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y
    data.shift_y = 0.1
    delta = world_to_camera_view(scene, cam, Vector((0, 0, 0))).y - initial
    data.shift_y = (target_y - initial) * 0.1 / delta
    for name, pos, energy, size in (("key", (-3, -5, 8), 1000, 5), ("fill", (5, 1, 6), 650, 5)):
        light = bpy.data.lights.new("housing_" + name, "AREA")
        light.energy, light.shape, light.size = energy, "DISK", size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("housing_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.65, 0.75, 0.90, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"


def build(kind):
    global COL, PREFIX, REPORT
    REPORT = {}
    scene = bpy.data.scenes.new(kind + "_regenerated")
    bpy.context.window.scene = scene
    scene.unit_settings.system = "METRIC"
    palette()
    count = 5 if kind == "dugout" else 3
    for level in range(1, count + 1):
        for state in STATES:
            PREFIX = f"{kind}_l{level:02d}_{state}"
            COL = bpy.data.collections.new(PREFIX)
            scene.collection.children.link(COL)
            root = COL
            (dugout if kind == "dugout" else wood_house)(level, state == "damaged")
            if state == "construction":
                COL = bpy.data.collections.new(PREFIX + "_overlay")
                root.children.link(COL)
                construction(kind, level)
            clean_meshes(root)
            tris = sum(len(obj.data.loop_triangles) for obj in root.all_objects if obj.type == "MESH")
            used = {mat.name for obj in root.all_objects if obj.type == "MESH" for mat in obj.data.materials}
            coords = [obj.matrix_world @ Vector(corner) for obj in root.all_objects if obj.type == "MESH" for corner in obj.bound_box]
            bounds = [[min(v[i] for v in coords), max(v[i] for v in coords)] for i in range(3)]
            assert all(abs(v) <= 1.81 for axis in bounds[:2] for v in axis), (PREFIX, bounds)
            assert tris <= (8500 if state == "construction" else 7500), (PREFIX, tris)
            REPORT[PREFIX] = {"triangles": tris, "materials": len(used), "bounds": bounds}
    setup_camera(scene)
    show(f"{kind}_l01_active")
    print(json.dumps(REPORT))


def show(name):
    for collection in bpy.context.scene.collection.children:
        collection.hide_render = collection.name != name
        collection.hide_viewport = collection.name != name
    bpy.context.view_layer.update()


def export_one(name, render=True):
    kind = "dugout" if name.startswith("dugout") else "wood_house"
    folder = ROOT / "frontend/src/assets/buildings/housing" / kind
    folder.mkdir(parents=True, exist_ok=True)
    show(name)
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    for obj in bpy.data.collections[name].all_objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(folder / (name + ".glb")), export_format="GLB", use_selection=True, use_active_scene=True, export_extras=True)
    if render:
        output = ROOT / "frontend/public/assets/buildings/housing" / kind / (name + ".png")
        bpy.context.scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
    print("EXPORTED " + name)


def finish(kind):
    folder = ROOT / "frontend/src/assets/buildings/housing" / kind
    if kind == "wood_house" and not bpy.data.collections.get("wood_house_l04_active"):
        old = folder / "wood_house_levels.blend"
        with bpy.data.libraries.load(str(old), link=False) as (source, target):
            target.collections = [name for name in source.collections if any(name == f"wood_house_l{level:02d}_{state}" for level in (4, 5, 6) for state in STATES)]
        assert len(target.collections) == 9, "Missing preserved wood-house levels"
        for collection in target.collections:
            bpy.context.scene.collection.children.link(collection)
    for collection in bpy.context.scene.collection.children:
        collection.hide_viewport = False
        collection.hide_render = False
    bpy.context.view_layer.update()
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    gallery_positions = []
    for collection in bpy.context.scene.collection.children:
        if not collection.name.startswith(kind + "_l"):
            continue
        level = int(collection.name.split("_l")[1][:2])
        state = collection.name.rsplit("_", 1)[1]
        members = set(collection.all_objects)
        corners = [obj.matrix_world @ Vector(corner) for obj in members if obj.type == "MESH" for corner in obj.bound_box]
        center = Vector(((min(v.x for v in corners) + max(v.x for v in corners)) / 2,
                         (min(v.y for v in corners) + max(v.y for v in corners)) / 2, 0))
        delta = Vector(((level - 1) * 4.4, STATES.index(state) * 4.4, 0)) - center
        for obj in collection.all_objects:
            obj.select_set(True)
            if obj.parent not in members:
                gallery_positions.append((obj, obj.location.copy()))
                obj.location += delta
    try:
        bpy.context.view_layer.update()
        bpy.ops.export_scene.gltf(filepath=str(folder / (kind + "_levels.glb")), export_format="GLB", use_selection=True, use_active_scene=True)
    finally:
        for obj, location in gallery_positions:
            obj.location = location
        bpy.context.view_layer.update()
    show(kind + "_l01_active")
    # Write only this asset scene so unrelated open scenes are preserved in memory.
    bpy.data.libraries.write(str(folder / (kind + "_levels.blend")), {bpy.context.scene}, fake_user=True)
    report = {"sprite_size": [512, 384], "anchor": [256, 292], "tile_size": 3.6, "assets": REPORT}
    (folder / "regeneration-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SAVED " + str(folder))
