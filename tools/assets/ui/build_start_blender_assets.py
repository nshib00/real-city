"""Build the Real City start-page diorama and Eolia emblem in Blender."""
from pathlib import Path
import bpy
import math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "tools/assets/ui/start-city"
PUBLIC = ROOT / "frontend/public/assets/ui/start"
FAV_SOURCE = ROOT / "tools/assets/ui/favicon"
FAV = ROOT / "frontend/public"
OUT.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)
FAV_SOURCE.mkdir(parents=True, exist_ok=True)
FAV.mkdir(parents=True, exist_ok=True)

def material(name, color, roughness=0.82, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def cube(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Soft cut edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj

def ico(name, loc, scale, mat, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj

def cylinder(name, loc, radius, depth, mat, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.collections:
        if block.name != "Collection":
            bpy.data.collections.remove(block)
    base = bpy.context.scene.collection.children.get("Collection")
    if base:
        base.name = "COL_StartCity"
    else:
        base = bpy.data.collections.new("COL_StartCity")
        bpy.context.scene.collection.children.link(base)
    return base

def set_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[col.name]
    return col

def terrain_tile(x, y, mat, name):
    # One beveled square cell; the orthographic camera turns the grid into isometric diamonds.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, -0.08))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (1.62, 1.62, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Terrain cell bevel", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 1
    obj.modifiers.new("Terrain normals", "WEIGHTED_NORMAL")
    return obj

def import_model(path, name, center, width):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [o for o in bpy.context.scene.objects if o not in before and o.type in {"MESH", "EMPTY"}]
    meshes = [o for o in imported if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No meshes imported: {path}")
    bpy.context.view_layer.update()
    corners = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
    minv = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    maxv = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    span = max(maxv.x - minv.x, maxv.y - minv.y)
    factor = width / max(span, 0.001)
    root = bpy.data.objects.new(f"ROOT_{name}", None)
    bpy.context.scene.collection.objects.link(root)
    for obj in imported:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    root.scale = (factor, factor, factor)
    root.location = (center[0] - ((minv.x + maxv.x) * 0.5) * factor,
                     center[1] - ((minv.y + maxv.y) * 0.5) * factor,
                     -minv.z * factor)
    root.name = f"ROOT_{name}"
    return root, imported

def duplicate_model(root, source_objects, name, center):
    dup_root = bpy.data.objects.new(f"ROOT_{name}", None)
    bpy.context.scene.collection.objects.link(dup_root)
    for source in source_objects:
        dup = source.copy()
        if source.data:
            dup.data = source.data
        bpy.context.scene.collection.objects.link(dup)
        local = source.matrix_world.copy()
        dup.parent = dup_root
        dup.matrix_world = local
    dup_root.location = root.location.copy()
    dup_root.scale = root.scale.copy()
    # Shift in the scene plane without changing imported geometry.
    dup_root.location.x += center[0] - root.location.x
    dup_root.location.y += center[1] - root.location.y
    return dup_root

def add_tree(x, y, scale, mats, index):
    trunk = cylinder(f"SM_tree_trunk_{index}", (x, y, 0.48*scale), 0.15*scale, 0.96*scale, mats[0], 10)
    trunk.location.z = 0.48*scale
    for i, (z, radius, color) in enumerate(((0.85, 0.72, mats[1]), (1.35, 0.58, mats[2]), (1.78, 0.42, mats[1]))):
        ico(f"SM_tree_canopy_{index}_{i}", (x, y, z*scale), (radius*scale, radius*0.9*scale, radius*1.05*scale), color, 2)

def common_render(scene, camera, size, transparent=False):
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    if bpy.app.build_options.cycles:
        try:
            scene.render.engine = "CYCLES"
        except TypeError as exc:
            print("Cycles unavailable:", exc, flush=True)
    if scene.render.engine != "CYCLES":
        scene.render.engine = next(engine for engine in engines if engine.startswith("BLENDER_EEVEE"))
    if scene.render.engine == "CYCLES":
        scene.cycles.device = "CPU"
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
    else:
        scene.eevee.taa_render_samples = 48
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = transparent
    scene.camera = camera
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "Medium High Contrast"
    except TypeError:
        pass
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1

def render_start_city():
    reset_scene()
    scene = bpy.context.scene
    scene.world.color = (0.68, 0.78, 0.65)
    scene.render.resolution_percentage = 100
    grass = [material("MAT_grass_meadow", (0.37, 0.52, 0.30)),
             material("MAT_grass_sunlit", (0.48, 0.60, 0.35)),
             material("MAT_grass_sage", (0.31, 0.45, 0.31))]
    soil = material("MAT_earth_path", (0.48, 0.37, 0.23))
    backdrop = material("MAT_meadow_backdrop", (0.53, 0.63, 0.40))
    stone = material("MAT_road_stone", (0.72, 0.64, 0.47))
    trunk = material("MAT_tree_bark", (0.32, 0.22, 0.13))
    canopy_a = material("MAT_canopy_deep", (0.19, 0.39, 0.22))
    canopy_b = material("MAT_canopy_light", (0.32, 0.52, 0.27))
    gold = material("MAT_brass", (0.78, 0.52, 0.20), 0.32, 0.45)

    # A compact slice of the shared world, made from terrain cells and rendered game buildings.
    set_collection("COL_Terrain")
    cube("SM_meadow_underlay", (0, 0, -0.19), (12.2, 12.2, 0.04), backdrop, 0.3)
    for y in range(-3, 4):
        for x in range(-3, 4):
            terrain_tile(x*1.62, y*1.62, grass[(x+y*2) % 3], f"SM_terrain_{x}_{y}")
    # A curved pale-stone road, laid across the map as individual inset pavers.
    set_collection("COL_Road")
    route = [(-3.9, 0.0), (-3.1, 0.0), (-2.3, 0.0), (-1.5, 0.0), (-0.7, 0.0), (0.1, 0.0), (0.9, 0.0), (1.7, 0.0), (2.5, 0.0), (3.3, 0.0), (4.1, 0.0)]
    for i, (x, y) in enumerate(route):
        cube(f"SM_road_paver_{i}", (x, y, 0.012), (0.68, 0.42, 0.07), stone, 0.045)
    # Small market garden beds and visible rows, placed beside the path.
    set_collection("COL_Garden")
    for bed in range(3):
        x = -3.4 + bed*0.74
        cube(f"SM_garden_soil_{bed}", (x, 2.7, 0.06), (0.62, 1.06, 0.12), soil, 0.05)
        for row in range(4):
            for plant in range(4):
                px = x - 0.22 + plant*0.145
                py = 2.34 + row*0.23
                cylinder(f"SM_crop_stem_{bed}_{row}_{plant}", (px, py, 0.19), 0.025, 0.24, canopy_a, 6)
                ico(f"SM_crop_leaf_{bed}_{row}_{plant}", (px+0.045, py, 0.28), (0.08, 0.035, 0.04), canopy_b, 1)
    # Place original Real City models; scale from their actual GLB bounds to the scene footprint.
    set_collection("COL_Buildings")
    asset = ROOT / "frontend/public/assets/buildings"
    town, town_objs = import_model(asset/"center/town_hall/town_hall_l01_active_LOD0.glb", "town_hall", (-0.2, 0.15), 2.45)
    villa, villa_objs = import_model(asset/"housing/villa/villa_l01_active_LOD0.glb", "villa", (3.05, -1.6), 2.45)
    # The second dwelling reuses mesh data from the same authored house model.
    duplicate_model(villa, villa_objs, "villa_neighbor", (-3.25, -1.6))
    # Trees frame the settlement and leave open negative space around the town center.
    set_collection("COL_Forest")
    spots = [(-5.0,-2.7,1.05),(-5.2,-0.9,0.86),(-4.8,1.7,0.98),(-3.9,4.0,0.84),
             (4.6,3.7,0.92),(5.1,2.0,1.06),(5.0,-1.9,0.90),(4.3,-3.7,1.02),
             (1.8,4.1,0.8),(-1.0,4.5,0.95)]
    for i, (x,y,s) in enumerate(spots):
        add_tree(x,y,s,(trunk,canopy_a,canopy_b),i)
    # Flags and lanterns provide small warm landmarks without competing with the map.
    set_collection("COL_Details")
    cylinder("SM_waystone_base", (0.8, 1.55, 0.22), 0.22, 0.44, stone, 8)
    ico("SM_waystone_crystal", (0.8, 1.55, 0.64), (0.14,0.14,0.30), gold, 1)

    # Render from an orthographic strategy-game camera. Keep the whole map softly framed.
    bpy.ops.object.camera_add(location=(11,-14,16))
    cam = bpy.context.object
    cam.name = "CAM_Start_Diorama"
    aim(cam, (0,0,0.3))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 15.8
    cam.data.lens = 50
    cam.data.dof.use_dof = False
    bpy.ops.object.light_add(type="AREA", location=(-5,-7,12))
    key = bpy.context.object
    key.name = "LGT_Key"
    key.data.energy = 950
    key.data.shape = "DISK"
    key.data.size = 8
    aim(key, (0,0,0))
    bpy.ops.object.light_add(type="AREA", location=(6,4,8))
    fill = bpy.context.object
    fill.name = "LGT_Fill"
    fill.data.energy = 260
    fill.data.size = 7
    aim(fill,(0,0,0))
    if scene.world and scene.world.use_nodes:
        bg = next((n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg:
            bg.inputs["Color"].default_value = (0.68, 0.75, 0.60, 1)
            bg.inputs["Strength"].default_value = 0.45
    scene.world.color = (0.68,0.75,0.60)
    common_render(scene, cam, (1200, 820), False)
    scene.render.filepath = str(OUT/"start-city-render.png")
    print("START_CITY_RENDER", scene.render.engine, scene.cycles.device if scene.render.engine == "CYCLES" else "", flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"start-city.blend"))
    bpy.ops.render.render(write_still=True)
    print("START_CITY_RENDER_DONE", flush=True)

def build_emblem():
    reset_scene()
    scene = bpy.context.scene
    scene.world.color = (1,1,1)
    green = material("MAT_emblem_forest", (0.14,0.34,0.24), 0.42)
    light = material("MAT_emblem_stone", (0.95,0.86,0.67), 0.7)
    brass = material("MAT_emblem_brass", (0.82,0.57,0.22), 0.28, 0.35)
    dark = material("MAT_emblem_outline", (0.09,0.21,0.17), 0.6)
    # Raised lozenge base echoes the game's isometric map tile.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
    base = bpy.context.object
    base.name = "SM_emblem_tile"
    base.dimensions = (2.6,2.6,0.34)
    base.rotation_euler[2] = math.radians(45)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    base.data.materials.append(light)
    bevel = base.modifiers.new("Cut stone bevel", "BEVEL")
    bevel.width = 0.13
    bevel.segments = 3
    base.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    # Main house/tower mark: gabled body, inset arch, green roof, and a brass wind pennant.
    cube("SM_emblem_body", (0,0,0.62), (1.22,0.82,0.95), green, 0.09)
    cube("SM_emblem_door", (0,-0.424,0.45), (0.34,0.055,0.57), dark, 0.07)
    cube("SM_emblem_window_left", (-0.4,-0.427,0.79), (0.20,0.055,0.22), brass, 0.045)
    cube("SM_emblem_window_right", (0.4,-0.427,0.79), (0.20,0.055,0.22), brass, 0.045)
    # Two sloped roof halves form a clear, compact silhouette.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.34,0,1.24))
    roof_a=bpy.context.object; roof_a.name="SM_emblem_roof_left"; roof_a.dimensions=(0.76,1.04,0.19); roof_a.rotation_euler[1]=math.radians(-34); roof_a.data.materials.append(dark)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.34,0,1.24))
    roof_b=bpy.context.object; roof_b.name="SM_emblem_roof_right"; roof_b.dimensions=(0.76,1.04,0.19); roof_b.rotation_euler[1]=math.radians(34); roof_b.data.materials.append(green)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cylinder("SM_emblem_pennant_pole", (0.0,0,1.75), 0.055, 0.92, brass, 10)
    # A small wind ribbon gives the mark its original Eolian identity.
    mesh=bpy.data.meshes.new("ME_emblem_wind_ribbon")
    verts=[(0.03,-0.02,2.15),(0.73,-0.02,2.05),(0.48,-0.02,1.82),(0.03,-0.02,1.93),
           (0.03,0.02,2.15),(0.73,0.02,2.05),(0.48,0.02,1.82),(0.03,0.02,1.93)]
    faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mesh.from_pydata(verts,[],faces); mesh.materials.append(brass)
    wind=bpy.data.objects.new("SM_emblem_wind_ribbon",mesh); bpy.context.collection.objects.link(wind)

    bpy.ops.object.camera_add(location=(4,-7,6))
    cam=bpy.context.object; cam.name="CAM_Emblem"; aim(cam,(0,0,0.9)); cam.data.type="ORTHO"; cam.data.ortho_scale=3.65
    bpy.ops.object.light_add(type="AREA", location=(-3,-4,7)); key=bpy.context.object; key.name="LGT_Emblem_Key"; key.data.energy=900; key.data.size=4; aim(key,(0,0,0))
    bpy.ops.object.light_add(type="AREA", location=(4,3,4)); fill=bpy.context.object; fill.name="LGT_Emblem_Fill"; fill.data.energy=400; fill.data.size=3; aim(fill,(0,0,1))
    common_render(scene,cam,(512,512),True)
    scene.render.filepath=str(FAV_SOURCE/"eolia-emblem-512.png")
    print("EMBLEM_RENDER", scene.render.engine, scene.cycles.device if scene.render.engine == "CYCLES" else "", flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(FAV_SOURCE/"eolia-emblem.blend"))
    bpy.ops.render.render(write_still=True)
    print("EMBLEM_RENDER_DONE", flush=True)

render_start_city()
build_emblem()
print("START_ASSETS_READY", OUT, FAV_SOURCE, PUBLIC, FAV)
