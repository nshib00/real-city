"""Create the nine Real City weapon resource GLBs and transparent inventory icons.

Run with Blender in the background. Existing resource assets are never rewritten.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
RESOURCE_DIR = ROOT / "frontend/public/assets/resources/icons"


def import_neighbor(name: str, filename: str):
    source = Path(__file__).with_name(filename)
    module_spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
    return module


R = import_neighbor("real_city_weapon_resource_pipeline", "regenerate_resource_models.py")
G = R.G

WEAPONS = (
    ("throwing_knives", "Метательные клинки"),
    ("hunting_traps", "Охотничий капкан"),
    ("blackpowder_bomb", "Пороховая бомба"),
    ("shaped_charge", "Направленный заряд"),
    ("firebomb", "Огненная бомба"),
    ("shock_charge", "Импульсный заряд"),
    ("siege_mine", "Осадная мина"),
    ("breach_bomb", "Проломная бомба"),
    ("resonance_charge", "Резонансный заряд"),
)


def material(name, srgb, *, metal=0, rough=.45, emission=0, alpha=1):
    color = tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in srgb)
    mat = G.mat(name, (*color, alpha), rough, metal, alpha=alpha,
                emission=(*color, 1) if emission else None, emission_strength=emission)
    mat.diffuse_color = (*color, alpha)
    return mat


def section(name, col, a, b, radius, mat, sides=12):
    a, b = Vector(a), Vector(b)
    obj = G.cylinder(name, col, (a + b) / 2, radius, (b - a).length, mat, vertices=sides)
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


def ring(name, col, loc, major, minor, mat, rot=(0, 0, 0), segments=28):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=segments, minor_segments=6,
                                     location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return G.link_to(col, obj)


def faceted_blade(name, col, x, y, z, angle, mats):
    # A closed beveled-looking wedge, with the brighter upper facet visible in the icon.
    outline = [(-.11, -.30), (.11, -.30), (.14, -.05), (.04, .38), (0, .53), (-.04, .38), (-.14, -.05)]
    verts = [(px, py, h) for h in (0, .065) for px, py in outline]
    verts.append((0, .03, .11))
    faces = [tuple(range(6, -1, -1))]
    faces += [(i, (i + 1) % 7, (i + 1) % 7 + 7, i + 7) for i in range(7)]
    faces += [(i + 7, (i + 1) % 7 + 7, 14) for i in range(7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.location = (x, y, z)
    obj.rotation_euler.z = angle
    mesh.materials.append(mats["steel"])
    handle = G.cube(name + "_wood_grip", col, (x, y - .43, z + .025), (.12, .34, .09), mats["wood"])
    handle.rotation_euler.z = angle
    pin = G.cylinder(name + "_grip_pin", col, (x, y - .42, z + .085), .026, .02, mats["gold"], vertices=10)
    pin.rotation_euler.z = angle


def throwing_knives(col, m):
    for i, (x, y, a) in enumerate(((-.32, -.01, -.32), (0, .06, 0), (.32, -.01, .32))):
        faceted_blade(f"throwing_blade_{i}", col, x, y, .11 + i * .03, a, m)
    for i, x in enumerate((-.34, 0, .34)):
        G.cube(f"blade_edge_glint_{i}", col, (x - .035, .2, .21 + i * .02), (.025, .30, .015), m["silver"], (0, 0, (i - 1) * .32))


def hunting_traps(col, m):
    G.cube("trap_wood_mount", col, (0, .04, .055), (1.04, .72, .11), m["wood"])
    G.cylinder("trap_steel_base", col, (0, 0, .16), .47, .14, m["iron"], vertices=24)
    G.cylinder("trap_pressure_plate", col, (0, 0, .245), .20, .045, m["silver"], vertices=16)
    for side in (-1, 1):
        for j in range(5):
            t = j / 4 * math.pi
            x, y = .44 * math.cos(t), side * .37 * math.sin(t)
            section(f"jaw_{side}_{j}", col, (x, y, .25), (x, y, .36), .043, m["iron"], 8)
            if j < 4:
                tn = (j + 1) / 4 * math.pi
                section(f"jaw_arc_{side}_{j}", col, (x, y, .27),
                        (.44 * math.cos(tn), side * .37 * math.sin(tn), .27), .055, m["steel"], 8)
    ring("trap_rope_loop", col, (0, .55, .14), .12, .023, m["rope"], (math.pi / 2, 0, 0), 20)


def blackpowder_bomb(col, m):
    G.sphere("clay_bomb_body", col, (0, 0, .40), (.45, .43, .38), m["clay"], 20)
    ring("clay_bomb_lower_band", col, (0, 0, .24), .38, .024, m["light_clay"], segments=24)
    G.cylinder("bomb_collar", col, (0, 0, .76), .17, .16, m["iron"], vertices=16)
    ring("paper_seal", col, (0, 0, .76), .18, .028, m["paper"], segments=20)
    section("unglit_fuse", col, (0, 0, .83), (.13, -.06, 1.07), .035, m["rope"], 10)
    G.cube("paper_wrap_front", col, (0, -.39, .43), (.38, .045, .13), m["paper"])
    for x in (-.22, .22):
        G.cube(f"charcoal_mark_{x}", col, (x, -.32, .54), (.055, .045, .11), m["coal"])


def shaped_charge(col, m):
    body = G.cone("directed_steel_cone", col, (0, 0, .40), .36, .16, .61, m["steel"], vertices=24,
                  rot=(0, math.pi / 2, .16))
    G.cylinder("dark_front_cup", col, (.33, -.06, .40), .27, .035, m["coal"], vertices=24,
               rot=(0, math.pi / 2, .16))
    ring("front_steel_lip", col, (.35, -.06, .40), .265, .045, m["silver"],
         (0, math.pi / 2, .16), 24)
    G.cube("fabric_gasket", col, (-.32, .08, .40), (.10, .56, .50), m["paper"], (0, 0, .16))
    for x in (-.12, .18):
        ring(f"steel_clamp_{x}", col, (x, 0, .40), .25 if x < 0 else .31, .035, m["gold"],
             (0, math.pi / 2, .16), 24)
    for y in (-.24, .24):
        G.cube(f"charge_mount_{y}", col, (-.25, y, .10), (.28, .10, .14), m["iron"])


def firebomb(col, m):
    G.sphere("amber_resin_liquid", col, (0, 0, .43), (.38, .36, .42), m["amber"], 20)
    G.sphere("thick_glass_shell", col, (0, 0, .45), (.42, .40, .46), m["clear_glass"], 20)
    G.cylinder("bottle_neck", col, (0, 0, .86), .15, .19, m["glass"], vertices=18)
    G.cylinder("cloth_plug", col, (0, 0, 1.01), .18, .16, m["paper"], vertices=14)
    ring("protective_base", col, (0, 0, .13), .31, .04, m["iron"], segments=24)
    ring("protective_middle", col, (0, 0, .51), .41, .035, m["iron"], segments=24)
    for i in range(6):
        a = i * math.tau / 6
        section(f"bottle_cage_bar_{i}", col, (.30 * math.cos(a), .30 * math.sin(a), .16),
                (.39 * math.cos(a), .39 * math.sin(a), .72), .025, m["steel"], 8)
    G.cube("resin_belt", col, (0, -.37, .34), (.36, .025, .09), m["dark_amber"])


def shock_charge(col, m):
    G.cylinder("shock_lower_casing", col, (0, 0, .19), .30, .17, m["iron"], vertices=20)
    G.cylinder("shock_upper_casing", col, (0, 0, .76), .30, .15, m["iron"], vertices=20)
    G.cylinder("glass_core", col, (0, 0, .48), .235, .58, m["blue_glass"], vertices=18)
    for i in range(5):
        ring(f"copper_coil_{i}", col, (0, 0, .24 + i * .12), .265, .028, m["copper"], segments=24)
    for side in (-1, 1):
        section(f"contact_pin_{side}", col, (side * .15, 0, .81), (side * .15, 0, 1.05), .046, m["silver"])
        G.sphere(f"pin_cap_{side}", col, (side * .15, 0, 1.05), (.075, .075, .075), m["blue_light"], 12)
    G.cylinder("shock_base", col, (0, 0, .105), .34, .12, m["steel"], vertices=20)


def siege_mine(col, m):
    G.cylinder("mine_steel_disk", col, (0, 0, .18), .52, .25, m["iron"], vertices=24)
    ring("mine_outer_ring", col, (0, 0, .31), .46, .037, m["steel"], segments=24)
    G.cylinder("central_pressure_pad", col, (0, 0, .36), .22, .085, m["silver"], vertices=20)
    for i in range(4):
        a = i * math.pi / 2
        obj = G.cube(f"armor_sector_{i}", col, (.36 * math.cos(a), .36 * math.sin(a), .35),
                     (.23, .22, .09), m["steel"])
        obj.rotation_euler.z = a
        G.cube(f"ochre_mark_{i}", col, (.36 * math.cos(a), .36 * math.sin(a), .41),
               (.13, .05, .012), m["ochre"], (0, 0, a))
    for x in (-.56, .56):
        ring(f"rope_carry_handle_{x}", col, (x, 0, .23), .11, .022, m["rope"],
             (math.pi / 2, 0, 0), 18)


def breach_bomb(col, m):
    G.cube("breach_charge_core", col, (0, 0, .44), (.80, .48, .79), m["iron"])
    G.cube("fuel_heart", col, (0, -.258, .44), (.47, .045, .43), m["amber"])
    for x in (-.34, .34):
        G.cube(f"side_armor_{x}", col, (x, -.29, .44), (.16, .10, .79), m["steel"])
        for z in (.16, .72):
            G.cylinder(f"armor_rivet_{x}_{z}", col, (x, -.351, z), .036, .026,
                       m["gold"], vertices=10, rot=(math.pi / 2, 0, 0))
    for z in (.08, .80):
        G.cube(f"horizontal_binder_{z}", col, (0, -.30, z), (.83, .10, .12), m["silver"])
    for x in (-.28, .28):
        G.cube(f"wall_mount_hook_{x}", col, (x, .29, .53), (.14, .16, .27), m["iron"])
    G.cube("front_direction_plate", col, (0, -.373, .45), (.15, .026, .30), m["ochre"])


def resonance_charge(col, m):
    G.cylinder("resonance_core", col, (0, 0, .48), .27, .70, m["steel"], vertices=8)
    G.cylinder("violet_core_slit", col, (0, -.265, .50), .15, .42, m["violet"], vertices=8)
    for i, angle in enumerate((math.pi / 2, math.pi / 2 + .64)):
        ring(f"calibration_ring_{i}", col, (0, 0, .49), .48 + i * .06, .035,
             m["gold"] if i else m["steel"], (angle, .20, .32 + i * .35), 30)
    for i in range(4):
        a = i * math.pi / 2
        x, y = .34 * math.cos(a), .34 * math.sin(a)
        section(f"precision_conductor_{i}", col, (x, y, .20), (x, y, .77), .024,
                m["copper"], 8)
        G.sphere(f"calibration_lock_{i}", col, (x, y, .77), (.055, .055, .055), m["gold"], 12)
    G.cylinder("resonance_base", col, (0, 0, .11), .35, .15, m["iron"], vertices=16)


BUILDERS = {
    "throwing_knives": throwing_knives,
    "hunting_traps": hunting_traps,
    "blackpowder_bomb": blackpowder_bomb,
    "shaped_charge": shaped_charge,
    "firebomb": firebomb,
    "shock_charge": shock_charge,
    "siege_mine": siege_mine,
    "breach_bomb": breach_bomb,
    "resonance_charge": resonance_charge,
}


def export_static_glb(path, collection):
    """Write static, material-preserving GLB when this Blender install lacks glTF modules."""
    binary = bytearray()
    buffer_views = []
    accessors = []
    meshes = []
    nodes = []
    materials = []
    material_ids = {}

    def view(payload, target):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(payload)
        result = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset,
                             "byteLength": len(payload), "target": target})
        return result

    def accessor(view_index, count, component_type, shape, bounds=None):
        result = len(accessors)
        item = {"bufferView": view_index, "componentType": component_type,
                "count": count, "type": shape}
        if bounds:
            item["min"], item["max"] = bounds
        accessors.append(item)
        return result

    def material_index(mat):
        if mat.name in material_ids:
            return material_ids[mat.name]
        shader = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        base = tuple(shader.inputs["Base Color"].default_value) if shader else tuple(mat.diffuse_color)
        alpha = float(shader.inputs["Alpha"].default_value) if shader else 1.0
        info = {
            "name": mat.name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [float(base[0]), float(base[1]), float(base[2]), alpha],
                "metallicFactor": float(shader.inputs["Metallic"].default_value) if shader else 0,
                "roughnessFactor": float(shader.inputs["Roughness"].default_value) if shader else .6,
            },
            "doubleSided": True,
        }
        if alpha < .999:
            info["alphaMode"] = "BLEND"
        if shader and "Emission Color" in shader.inputs:
            emission = tuple(shader.inputs["Emission Color"].default_value)
            strength = float(shader.inputs["Emission Strength"].default_value)
            if strength:
                info["emissiveFactor"] = [min(1, float(value) * strength) for value in emission[:3]]
        material_ids[mat.name] = len(materials)
        materials.append(info)
        return material_ids[mat.name]

    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        positions = []
        normals = []
        primitives = []
        by_material = {}
        for triangle in mesh.loop_triangles:
            by_material.setdefault(mesh.polygons[triangle.polygon_index].material_index, []).append(triangle)
        for local_material, triangles in by_material.items():
            positions.clear()
            normals.clear()
            for triangle in triangles:
                face_normal = triangle.normal
                normal = (float(face_normal.x), float(face_normal.z), float(-face_normal.y))
                for index in triangle.vertices:
                    p = mesh.vertices[index].co
                    positions.extend((float(p.x), float(p.z), float(-p.y)))
                    normals.extend(normal)
            count = len(positions) // 3
            indices = list(range(count))
            pos_view = view(struct.pack("<" + "f" * len(positions), *positions), 34962)
            norm_view = view(struct.pack("<" + "f" * len(normals), *normals), 34962)
            index_view = view(struct.pack("<" + "I" * count, *indices), 34963)
            bounds = ([min(positions[i::3]) for i in range(3)],
                      [max(positions[i::3]) for i in range(3)])
            pos_accessor = accessor(pos_view, count, 5126, "VEC3", bounds)
            norm_accessor = accessor(norm_view, count, 5126, "VEC3")
            index_accessor = accessor(index_view, count, 5125, "SCALAR")
            mat = mesh.materials[local_material] if len(mesh.materials) > local_material else None
            primitive = {"attributes": {"POSITION": pos_accessor, "NORMAL": norm_accessor},
                         "indices": index_accessor, "mode": 4}
            if mat:
                primitive["material"] = material_index(mat)
            primitives.append(primitive)
        if primitives:
            meshes.append({"name": obj.name, "primitives": primitives})
            nodes.append({"name": obj.name, "mesh": len(meshes) - 1})
    document = {"asset": {"version": "2.0", "generator": "Real City static weapon exporter"},
                "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
                "nodes": nodes, "meshes": meshes, "materials": materials,
                "accessors": accessors, "bufferViews": buffer_views,
                "buffers": [{"byteLength": len(binary)}]}
    json_chunk = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    binary.extend(b"\x00" * ((-len(binary)) % 4))
    total = 12 + 8 + len(json_chunk) + 8 + len(binary)
    with open(path, "wb") as handle:
        handle.write(struct.pack("<4sII", b"glTF", 2, total))
        handle.write(struct.pack("<I4s", len(json_chunk), b"JSON"))
        handle.write(json_chunk)
        handle.write(struct.pack("<I4s", len(binary), b"BIN\x00"))
        handle.write(binary)


def main(args):
    output = Path(args.output or RESOURCE_DIR)
    output.mkdir(parents=True, exist_ok=True)
    # This script runs only in an isolated background Blender. Remove its default cube,
    # camera and light so they cannot enter the inventory renders.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    R.configure_geometry()
    mats = {
        "steel": G.MATS["steel"], "silver": G.MATS["metal"],
        "iron": G.MATS["iron"], "wood": G.MATS["wood"],
        "gold": G.MATS["gold"], "rope": G.MATS["rope"],
        "clay": G.MATS["clay"], "coal": G.MATS["coal"],
        "glass": G.MATS["glass"], "fabric": G.MATS["fabric"],
        "copper": G.MATS["copper"],
        "amber": material("weapon_amber", (1, .43, .015), emission=.20),
        "clear_glass": material("weapon_clear_glass", (.88, .95, 1), rough=.15, alpha=.16),
        "dark_amber": material("weapon_resin", (.38, .075, .02)),
        "blue_glass": material("weapon_blue_glass", (.09, .55, .83), emission=.14),
        "blue_light": material("weapon_blue_light", (.36, .88, 1), emission=.45),
        "violet": material("weapon_violet", (.47, .13, .83), emission=.42),
        "ochre": material("weapon_ochre", (.94, .62, .17)),
        "paper": material("weapon_paper", (.88, .74, .52)),
        "light_clay": G.MATS["clay_light"],
    }
    scene = bpy.context.scene
    scene.name = "Real_City_Weapon_Resources"
    G.setup_camera()
    scene.camera.rotation_euler = Vector((-5, 7, -5.5)).to_track_quat("-Z", "Y").to_euler()
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("weapon_resource_daylight")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (.72, .8, 1, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = .4
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    selected_ids = set(args.ids or BUILDERS)
    report = []
    collections = []
    for rid, name in WEAPONS:
        if rid not in selected_ids:
            continue
        collection = bpy.data.collections.new("weapon_resource_" + rid)
        scene.collection.children.link(collection)
        BUILDERS[rid](collection, mats)
        R.bake(collection)
        R.camera(scene, collection)
        bpy.ops.object.select_all(action="DESELECT")
        triangles = 0
        for obj in collection.objects:
            obj.select_set(True)
            obj.data.calc_loop_triangles()
            triangles += len(obj.data.loop_triangles)
        if triangles > 6000:
            raise ValueError(f"{rid} has {triangles} triangles; budget is 6000")
        export_static_glb(output / (rid + ".glb"), collection)
        scene.render.filepath = str(output / (rid + ".png"))
        bpy.ops.render.render(write_still=True)
        report.append({"id": rid, "name": name, "category": "weapons", "file": rid + ".png",
                       "model": rid + ".glb", "triangles": triangles,
                       "ortho_scale": scene.camera.data.ortho_scale,
                       "camera_location": list(scene.camera.location)})
        bpy.ops.object.select_all(action="DESELECT")
        collection.hide_render = True
        collection.hide_viewport = True
        collections.append(collection)
        (output / "weapon-generation-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("WEAPON_DONE", rid, triangles, flush=True)
    if not report:
        raise ValueError("No weapon IDs selected")
    collections[0].hide_render = False
    collections[0].hide_viewport = False
    R.camera(scene, collections[0])
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "weapon_resources.blend"))
    print("WEAPONS_COMPLETE", len(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ids", nargs="*", choices=list(BUILDERS))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main(args)
