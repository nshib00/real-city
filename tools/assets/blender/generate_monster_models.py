"""Build the eight original Real City creatures in Blender 5.2.

Call build_monster(asset_id) from a live Blender Python console or via Blender MCP.
Each call saves a single rigged .blend, animated GLB and rendered preview.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector


ROOT = "/home/nshib/projects/real-city"
KINDS = (
    "roaming_melee", "resource_guardian", "ruins_guardian", "forest_stalker",
    "spore_beast", "ironback_brute", "ember_wisp", "ancient_colossus",
)
COLORS = {
    "roaming_melee": {"body": (0.45, .25, .14), "secondary": (.67, .46, .24), "hard": (.21, .20, .16), "accent": (.80, .54, .18)},
    "resource_guardian": {"body": (.46, .49, .43), "secondary": (.66, .64, .49), "hard": (.23, .34, .32), "accent": (.23, .68, .69)},
    "ruins_guardian": {"body": (.63, .60, .48), "secondary": (.82, .76, .59), "hard": (.24, .31, .27), "accent": (.32, .70, .61)},
    "forest_stalker": {"body": (.15, .34, .25), "secondary": (.36, .47, .25), "hard": (.13, .20, .17), "accent": (.80, .75, .39)},
    "spore_beast": {"body": (.70, .62, .46), "secondary": (.43, .28, .47), "hard": (.28, .23, .33), "accent": (.92, .65, .44)},
    "ironback_brute": {"body": (.31, .25, .19), "secondary": (.48, .35, .24), "hard": (.30, .35, .33), "accent": (.78, .49, .23)},
    "ember_wisp": {"body": (.30, .16, .11), "secondary": (.92, .39, .10), "hard": (.16, .18, .19), "accent": (1.0, .68, .25)},
    "ancient_colossus": {"body": (.52, .53, .47), "secondary": (.75, .70, .55), "hard": (.23, .31, .27), "accent": (.78, .56, .25)},
}
FREQUENCIES = {"idle": (8, 6), "walk": (12, 10), "attack": (10, 12), "hit": (5, 10), "death": (14, 10)}


def destination(path):
    if sys.platform == "win32":
        return "\\\\wsl.localhost\\Debian" + path.replace("/", "\\")
    return path


def material(name, rgb, rough=.78, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if glow:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
        bsdf.inputs["Emission Strength"].default_value = glow
    else:
        tex = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 4.8
        tex.inputs["Detail"].default_value = 3
        # Keep a constant base color: glTF cannot represent Blender's procedural
        # color ramp, and would otherwise export these meshes as white.
        bump = mat.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .18
        bump.inputs["Distance"].default_value = .07
        mat.node_tree.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in tuple(bpy.data.collections):
        bpy.data.collections.remove(collection)
    staging = bpy.data.collections.new("Collection")
    bpy.context.scene.collection.children.link(staging)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[staging.name]
    for data in tuple(bpy.data.actions):
        bpy.data.actions.remove(data)
    for mat in tuple(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def rig_for(kind):
    quadruped = kind in ("resource_guardian", "forest_stalker", "ironback_brute", "spore_beast")
    giant = kind == "ancient_colossus"
    floaty = kind == "ember_wisp"
    scale = 1.6 if giant else 1.0
    if floaty:
        scale = .84
    arm = bpy.data.armatures.new("ARM_" + kind)
    obj = bpy.data.objects.new("RIG_" + kind, arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = {
        "root": ((0, 0, 0), (0, 0, .2), None),
        "torso": ((0, 0, .78 * scale), (0, 0, 1.15 * scale), "root"),
        "head": ((0, -.67 * scale if quadruped else -.14 * scale, 1.28 * scale if quadruped else 1.65 * scale),
                 (0, -.75 * scale if quadruped else -.22 * scale, 1.5 * scale if quadruped else 1.9 * scale), "torso"),
        "front_l": ((-.43 * scale, -.47 * scale if quadruped else 0, 1.02 * scale if quadruped else 1.43 * scale),
                    (-.43 * scale, -.50 * scale if quadruped else 0, .50 * scale if quadruped else .95 * scale), "torso"),
        "front_r": ((.43 * scale, -.47 * scale if quadruped else 0, 1.02 * scale if quadruped else 1.43 * scale),
                    (.43 * scale, -.50 * scale if quadruped else 0, .50 * scale if quadruped else .95 * scale), "torso"),
        "back_l": ((-.28 * scale, .52 * scale if quadruped else 0, .76 * scale),
                   (-.28 * scale, .53 * scale if quadruped else 0, .17 * scale), "root"),
        "back_r": ((.28 * scale, .52 * scale if quadruped else 0, .76 * scale),
                   (.28 * scale, .53 * scale if quadruped else 0, .17 * scale), "root"),
        "tail": ((0, .68 * scale if quadruped else .32 * scale, 1.05 * scale),
                 (0, 1.2 * scale if quadruped else .68 * scale, 1.0 * scale), "torso"),
    }
    for name, (start, end, _) in bones.items():
        bone = arm.edit_bones.new(name)
        bone.head, bone.tail = start, end
    for name, (_, _, parent) in bones.items():
        if parent:
            arm.edit_bones[name].parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.show_in_front = True
    obj.select_set(False)
    return obj, scale


def bind(obj, rig, bone):
    if not rig or bone is None:
        return obj
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    group = obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    mod = obj.modifiers.new("rig", "ARMATURE")
    mod.object = rig
    return obj


def blob(name, center, size, mat, rig=None, bone="torso", rings=8, segments=12, facets=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=center)
    obj = bpy.context.object
    obj.name = "SM_" + name
    obj.scale = size
    # Gentle asymmetric surface detail gives organic pieces broad planes without a blockout appearance.
    seed = sum(ord(ch) for ch in name)
    for v in obj.data.vertices:
        x, y, z = v.co
        f = 1 + .025 * math.sin(seed * .17 + x * 4.7 + z * 3.1) * math.cos(y * 5.2)
        v.co *= f
    obj.data.materials.append(mat)
    if not facets:
        for face in obj.data.polygons:
            face.use_smooth = True
    return bind(obj, rig, bone)


def tapered(name, points, radii, mat, rig=None, bone="torso", sides=9):
    verts, faces = [], []
    for idx, point in enumerate(points):
        p = Vector(point)
        direction = Vector(points[min(idx+1, len(points)-1)]) - Vector(points[max(idx-1, 0)])
        direction.normalize()
        tangent = direction.cross(Vector((0, 0, 1)))
        if tangent.length < .01:
            tangent = direction.cross(Vector((0, 1, 0)))
        tangent.normalize()
        bitangent = direction.cross(tangent).normalized()
        for j in range(sides):
            phi = 2*math.pi*j/sides
            verts.append(p + radii[idx]*(tangent*math.cos(phi)+bitangent*math.sin(phi)))
        if idx:
            for j in range(sides):
                a = (idx-1)*sides+j
                b = (idx-1)*sides+(j+1)%sides
                c = idx*sides+(j+1)%sides
                d = idx*sides+j
                faces.append((a,b,c,d))
    faces += [tuple(reversed(range(sides))), tuple((len(points)-1)*sides+j for j in range(sides))]
    mesh = bpy.data.meshes.new("MESH_"+name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("SM_"+name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = len(face.vertices) == 4
    return bind(obj, rig, bone)


def face(kind, rig, mats, center, width, z, quad=False):
    x, y = center
    for side in (-1, 1):
        blob(kind+"_eye_"+str(side), (x+side*width, y, z), (.08,.065,.085), mats["hard"], rig, "head", 8, 10)
        blob(kind+"_eye_glint_"+str(side), (x+side*width, y-.058, z+.012), (.026,.013,.03), mats["accent"], rig, "head", 7, 8)
    if quad:
        blob(kind+"_jaw", (x, y-.12, z-.19), (.24,.19,.10), mats["secondary"], rig, "head")


def legs(kind, rig, mats, quad, width=.4, front_y=-.48, rear_y=.53, height=1):
    for side in (-1, 1):
        for front in ((True, False) if quad else (False,)):
            limb = ("front_" if front else "back_") + ("l" if side == -1 else "r")
            x = side*(width if front else width*.72)
            y = front_y if front else (rear_y if quad else .02)
            upper = .48*height if front else .43*height
            blob(kind+"_"+limb+"_thigh", (x, y, upper+.16*height), (.16*height,.17*height,.32*height), mats["body"], rig, limb)
            blob(kind+"_"+limb+"_shin", (x, y-.08*height, .26*height), (.105*height,.13*height,.23*height), mats["secondary"], rig, limb)
            blob(kind+"_"+limb+"_foot", (x,y-.19*height,.09*height), (.20*height,.25*height,.095*height), mats["hard"], rig, limb)
            for toe in (-1,0,1):
                tapered(kind+"_"+limb+"_claw_"+str(toe), [(x+toe*.11*height,y-.33*height,.105*height),
                    (x+toe*.13*height,y-.47*height,.075*height)], [.048*height,.005*height], mats["accent"], rig, limb, 7)


def make_creature(kind, rig, size, mats):
    rnd = random.Random(kind)
    b, s, h, a = (mats[k] for k in ("body", "secondary", "hard", "accent"))
    if kind == "roaming_melee":
        blob("raider_pelvis", (0,.02,.91), (.35,.30,.25), s, rig, "root")
        blob("raider_torso", (0,-.07,1.38), (.40,.31,.55), b, rig)
        blob("raider_chest", (0,-.25,1.54), (.33,.19,.23), s, rig)
        blob("raider_head", (0,-.37,1.96), (.36,.32,.31), b, rig,"head",11,18)
        blob("raider_muzzle", (0,-.65,1.87), (.23,.25,.14), s, rig,"head")
        face(kind,rig,mats,(0,-.64),.17,2.01)
        legs(kind,rig,mats,False,width=.31)
        for side in (-1,1):
            limb = "front_l" if side == -1 else "front_r"
            blob("raider_arm_"+limb, (side*.49,-.09,1.26), (.17,.18,.43), b,rig,limb)
            blob("raider_paw_"+limb, (side*.55,-.21,.91), (.15,.17,.17), h,rig,limb)
            for j in range(3):
                tapered("raider_finger_"+limb+str(j),[(side*(.48+j*.075),-.33,.87),(side*(.48+j*.075),-.51,.76)], [.05,.006], a,rig,limb)
        for j in range(9):
            z=1.50+j*.075
            tapered("raider_mane_"+str(j),[(rnd.uniform(-.18,.18),.13,z),(.03,.23,z+.11),(.01,.30,z+.17)], [.09,.055,.008],h,rig,"head" if j>=6 else "torso")
        for side in (-1,1):
            blob("raider_cheek_"+str(side),(side*.27,-.55,1.82),(.12,.13,.18),h,rig,"head")
        for side in (-1,1):
            tapered("raider_brow_"+str(side),[(side*.16,-.68,2.09),(side*.32,-.5,2.17)], [.1,.015],h,rig,"head")
    elif kind in ("resource_guardian","forest_stalker","ironback_brute"):
        swift = kind=="forest_stalker"
        heavy = kind=="ironback_brute"
        width = .37 if swift else (.60 if heavy else .51)
        length = .86 if swift else (.96 if heavy else .83)
        z = .98 if swift else 1.18
        blob(kind+"_core",(0,.05,z),(width,length,.39 if swift else .52),b,rig,segments=20,rings=12)
        blob(kind+"_chest",(0,-.48,z+.08),(width*.94,.52,.47 if heavy else .37),s,rig)
        blob(kind+"_neck",(0,-.69,z+.05),(.31,.42,.31),b,rig,"head")
        blob(kind+"_head",(0,-.94,z+.04),(.39 if swift else .52,.42,.29 if swift else .38),b,rig,"head",11,18)
        blob(kind+"_snout",(0,-1.30,z-.055),(.26,.26,.16),s,rig,"head")
        face(kind,rig,mats,(0,-1.24),.23,z+.11,True)
        legs(kind,rig,mats,True,width=width*.86,height=1.0 if swift else 1.14)
        if swift:
            for side in (-1,1):
                tapered("stalker_ear_"+str(side),[(side*.25,-.86,1.18),(side*.49,-.62,1.55),(side*.56,-.55,1.67)], [.11,.07,.005],h,rig,"head")
                tapered("stalker_tail_"+str(side),[(0,.77,1.08),(side*.19,1.22,1.30),(side*.39,1.58,1.24),(side*.51,1.78,1.34)], [.13,.095,.055,.005],s,rig,"tail")
            for j in range(7):
                tapered("stalker_spine_"+str(j),[(rnd.uniform(-.19,.19),-.34+j*.18,1.24),
                    (rnd.uniform(-.22,.22),-.19+j*.18,1.50)], [.10,.004],s,rig)
        else:
            for j in range(12 if heavy else 9):
                x = ((j%3)-1)*width*.67
                y = -.56+(j//3)*.40
                zz = z + (.44 if heavy else .39)
                blob(kind+"_back_plate_"+str(j),(x,y,zz),(.19,.24,.075) if heavy else (.19,.21,.12),
                     h if heavy else s,rig,facets=True)
                if j%3 == 1:
                    tapered(kind+"_ridge_"+str(j),[(x,y,zz+.06),(x,y+.09,zz+.27),(x,y+.19,zz+.38)],
                            [.12,.07,.008],h,rig)
            for side in (-1,1):
                tapered(kind+"_horn_"+str(side),[(side*.32,-1.17,z+.28),(side*.49,-1.33,z+.42),(side*.50,-1.42,z+.51)],
                        [.13,.07,.004], h,rig,"head")
            if not heavy:
                for j in range(6):
                    blob("guardian_crystal_"+str(j), (rnd.uniform(-.35,.35),rnd.uniform(-.45,.53),z+.49),
                         (.07,.09,rnd.uniform(.09,.20)),a,rig,facets=True)
            else:
                blob("brute_shoulder_shield",(-.54,-.42,1.49),(.21,.44,.31),h,rig,facets=True)
                blob("brute_shoulder_shield_r",(.54,-.42,1.49),(.21,.44,.31),h,rig,facets=True)
                for side in (-1,1):
                    for j in range(3):
                        blob("brute_side_shield_"+str(side)+str(j),(side*.64,-.28+j*.40,1.37),
                             (.12,.20,.21),h,rig,facets=True)
                tapered("brute_battering_crest",[(0,-1.22,1.44),(0,-1.43,1.52),
                    (0,-1.58,1.49)], [.20,.15,.015],h,rig,"head")
    elif kind == "ruins_guardian":
        blob("ruins_pelvis",(0,0,.9),(.35,.30,.25),h,rig,"root",facets=True)
        blob("ruins_torso",(0,0,1.46),(.50,.32,.67),b,rig,segments=18,rings=12,facets=True)
        blob("ruins_inner",(0,-.27,1.47),(.25,.09,.42),h,rig)
        blob("ruins_head",(0,-.07,2.13),(.28,.25,.32),s,rig,"head",facets=True)
        face(kind,rig,mats,(0,-.29),.15,2.17)
        legs(kind,rig,mats,False,width=.39)
        for side in (-1,1):
            limb = "front_l" if side==-1 else "front_r"
            blob("ruins_pauldron_"+str(side),(side*.56,-.04,1.82),(.30,.38,.23),s,rig,limb,facets=True)
            blob("ruins_arm_"+str(side),(side*.62,-.11,1.25),(.19,.20,.47),h,rig,limb,facets=True)
            blob("ruins_fist_"+str(side),(side*.63,-.22,.91),(.19,.21,.17),b,rig,limb)
        # Broken arc is unmistakable at map scale, including its rear silhouette.
        for side in (-1,1):
            tapered("ruins_arch_"+str(side),[(side*.49,.06,1.78),(side*.70,.12,2.10),(side*.68,.11,2.44),
                (side*.38,.05,2.60)], [.13,.15,.12,.015],s,rig)
        blob("ruins_shield",(-.72,-.29,1.15),(.17,.31,.48),b,rig,"front_l",facets=True)
        tapered("ruins_arch_lintel",[(-.36,.06,2.58),(-.12,.04,2.64),(.12,.04,2.64),(.33,.06,2.56)],
                 [.13,.14,.14,.12],s,rig)
        for j in range(8):
            side = -1 if j%2 else 1
            y = -.23 if j<4 else .20
            z = 1.02+(j%4)*.25
            blob("ruins_chipped_brick_"+str(j),(side*.39,y,z),(.08,.07,.09),s,rig,facets=True)
        for j in range(5):
            blob("ruins_moss_"+str(j), (rnd.uniform(-.43,.43),rnd.uniform(-.18,.20),rnd.uniform(1.4,2.0)),
                 (.09,.07,.16),h,rig,facets=True)
    elif kind == "spore_beast":
        blob("spore_stem",(0,.06,1.04),(.47,.41,.61),b,rig,segments=20,rings=13)
        blob("spore_mantle",(0,0,1.72),(.73,.66,.22),s,rig,segments=22,rings=10)
        blob("spore_under_cap",(0,-.02,1.62),(.66,.59,.105),a,rig,segments=18)
        for j in range(6):
            angle=j*math.tau/6
            blob("spore_rim_"+str(j),(.59*math.cos(angle),.51*math.sin(angle),1.72),(.27,.27,.18),s,rig)
        face(kind,rig,mats,(0,-.42),.25,1.13)
        legs(kind,rig,mats,True,width=.39,height=.91)
        for j in range(11):
            angle=j*2.4
            rad=.20+(j%3)*.12
            blob("spore_pouch_"+str(j),(rad*math.cos(angle),rad*math.sin(angle),1.9-(j%3)*.03),
                 (.08+(j%2)*.03,.10,.07),a,rig,facets=True)
        for j in range(14):
            angle=j*math.tau/14
            tapered("spore_gill_"+str(j),[(.16*math.cos(angle),.14*math.sin(angle),1.61),
                (.47*math.cos(angle),.43*math.sin(angle),1.62)], [.026,.012],h,rig)
        for j in range(6):
            tapered("spore_root_"+str(j),[(0,.1,.86),(.4*math.cos(j),.38*math.sin(j),.34),
                 (.53*math.cos(j),.52*math.sin(j),.06)],[.12,.09,.02],h,rig)
    elif kind == "ember_wisp":
        blob("wisp_shell",(0,0,1.18),(.31,.30,.45),h,rig,segments=20,rings=13)
        blob("wisp_core",(0,-.06,1.24),(.22,.23,.36),s,rig,segments=18,rings=12)
        blob("wisp_tip",(0,-.02,1.61),(.11,.12,.28),a,rig)
        face(kind,rig,mats,(0,-.26),.13,1.30)
        for ring in range(3):
            angle_shift = ring*1.3
            points=[]
            for j in range(9):
                angle=(j/10)*math.tau+angle_shift
                points.append((math.cos(angle)*(.43+ring*.09), math.sin(angle)*(.37+ring*.075),1.21+ring*.14+math.sin(angle*2)*.05))
            tapered("wisp_ash_ring_"+str(ring),points,[.046]*7+[.034,.005],b,rig,"tail",7)
        for j in range(10):
            angle=j*2.41
            blob("wisp_ember_"+str(j),(.28*math.cos(angle),.28*math.sin(angle),1.12+(j%5)*.14),
                 (.025,.025,.04),a,rig,facets=True)
        for j in range(5):
            tapered("wisp_smoke_"+str(j),[(rnd.uniform(-.11,.11),.1,.92),
                (rnd.uniform(-.18,.18),.28,.69),(rnd.uniform(-.21,.21),.39,.55)],
                [.075,.055,.004],h,rig,"tail",7)
    elif kind == "ancient_colossus":
        blob("colossus_pelvis",(0,.02,1.48),(.50,.41,.29),h,rig,"root",facets=True)
        blob("colossus_core",(0,0,2.33),(.66,.51,.96),b,rig,segments=22,rings=15,facets=True)
        blob("colossus_chest",(0,-.26,2.72),(.78,.37,.40),s,rig,facets=True)
        blob("colossus_head",(0,-.20,3.24),(.28,.28,.30),h,rig,"head",facets=True)
        face(kind,rig,mats,(0,-.47),.14,3.29)
        legs(kind,rig,mats,False,width=.45,height=1.55)
        for side in (-1,1):
            limb = "front_l" if side==-1 else "front_r"
            blob("colossus_shoulder_"+str(side),(side*.83,-.08,2.91),(.32,.41,.28),s,rig,limb,facets=True)
            blob("colossus_arm_"+str(side),(side*.94,-.08,2.22),(.28,.33,.62),b,rig,limb,facets=True)
            blob("colossus_fist_"+str(side),(side*.93,-.27,1.65),(.34,.39,.29),h,rig,limb,facets=True)
            tapered("colossus_arch_"+str(side),[(side*.65,.24,2.9),(side*.87,.18,3.45),
                (side*.67,.12,3.91),(side*.38,.06,4.02)], [.16,.19,.15,.04],s,rig)
        for j in range(8):
            x = ((j%3)-1)*.36
            z = 1.83+(j//3)*.39
            blob("colossus_ancient_plate_"+str(j),(x,-.47,z),(.19,.12,.22),s,rig,facets=True)
            if j%2==0:
                blob("colossus_runelight_"+str(j),(x,-.59,z),(.045,.025,.11),a,rig,facets=True)
        for j in range(9):
            tapered("colossus_root_"+str(j),[(rnd.uniform(-.23,.23),.27,2.72),
                (rnd.uniform(-.6,.6),.41,1.8),(rnd.uniform(-.5,.5),.53,.87)],
                [.075,.052,.007],h,rig)
        blob("colossus_mallet_heart",(.94,-.27,1.51),(.40,.38,.33),s,rig,"front_r",facets=True)
        for side in (-1,1):
            tapered("colossus_crown_"+str(side),[(side*.18,-.19,3.43),
                 (side*.35,-.1,3.67),(side*.38,.01,3.81)], [.10,.07,.004],h,rig,"head")


def animate(kind, rig):
    rig.animation_data_create()
    for name, (count, fps) in FREQUENCIES.items():
        action = bpy.data.actions.new("AN_"+kind+"_"+name)
        action.use_fake_user = True
        rig.animation_data.action = action
        for idx in range(count+1 if name in ("idle","walk") else count):
            t = idx / count
            frame = 1 + idx * (30 / fps)
            phase = 2*math.pi*t
            amount = .0
            if name == "attack":
                amount = (math.sin(math.pi * t)**3)
            elif name == "hit":
                amount = math.sin(math.pi*t)
            elif name == "death":
                amount = t*t*(3-2*t)
            for bone in rig.pose.bones:
                bone.rotation_mode = "XYZ"
                rot = (0.,0.,0.)
                if name == "idle":
                    if bone.name=="torso": rot = (.025*math.sin(phase),.025*math.cos(phase),.025*math.sin(phase))
                    if bone.name=="head": rot = (.06*math.sin(phase),0,.065*math.sin(phase))
                    if bone.name=="tail": rot = (0,.06*math.cos(phase),.10*math.sin(phase))
                elif name == "walk":
                    side = 1 if bone.name.endswith("l") else -1
                    if bone.name in ("front_l","front_r"): rot = (side*.30*math.sin(phase),0,side*.055*math.sin(phase))
                    if bone.name in ("back_l","back_r"): rot = (-side*.33*math.sin(phase),0,0)
                    if bone.name=="torso": rot = (.035*math.cos(phase*2),.04*math.sin(phase),.025*math.sin(phase))
                    if bone.name=="head": rot = (-.025*math.sin(phase*2),0,0)
                    if bone.name=="tail": rot = (0,0,.16*math.sin(phase))
                elif name == "attack":
                    if bone.name=="torso": rot = (-.26*amount,0,.12*amount)
                    if bone.name=="head": rot = (-.32*amount,0,0)
                    if bone.name in ("front_l","front_r"): rot = (-.66*amount,0,.19*amount if bone.name.endswith("l") else -.19*amount)
                elif name == "hit":
                    if bone.name=="torso": rot = (.24*amount,0,-.10*amount)
                    if bone.name=="head": rot = (.20*amount,.10*amount,0)
                elif name == "death":
                    if bone.name=="torso": rot = (.65*amount,.12*amount,.35*amount)
                    if bone.name=="head": rot = (.26*amount,0,-.20*amount)
                    if bone.name in ("front_l","front_r"): rot = (.38*amount,0,0)
                bone.rotation_euler = rot
                bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone.name)
                if bone.name == "root":
                    bob = .035*math.sin(phase*2) if name=="walk" else .015*math.sin(phase) if name=="idle" else 0
                    bone.location = (0, -.08*amount if name=="attack" else 0, bob-.24*amount if name=="death" else bob)
                    bone.keyframe_insert(data_path="location", frame=frame, group="root")
        action.frame_start = 1
        action.frame_end = 1 + (count if name in ("idle","walk") else count-1)*30/fps
        print("ANIMATION", kind, name, len(action.fcurves) if hasattr(action,"fcurves") else "slotted")
    rig.animation_data.action = bpy.data.actions.get("AN_"+kind+"_idle")
    bpy.context.scene.frame_set(1)


def set_preview(kind):
    world = bpy.data.worlds.new("World_"+kind)
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.23,.33,.32,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .35
    bpy.context.scene.world = world
    cam_data = bpy.data.cameras.new("CAM_Iso_Monster")
    camera = bpy.data.objects.new("CAM_Iso_Monster",cam_data)
    bpy.context.collection.objects.link(camera)
    target = Vector((0,0,1.75 if kind=="ancient_colossus" else 1.02))
    camera.location=(5,-7,6.0 if kind != "ancient_colossus" else 7.0)
    direction=target-Vector(camera.location)
    camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    cam_data.type="ORTHO"
    cam_data.ortho_scale=(5.8 if kind=="ancient_colossus" else
                         3.7 if kind in ("ruins_guardian", "forest_stalker") else 3.25)
    bpy.context.scene.camera=camera
    for name,xyz,power,size in (
        ("Key",(3,-4,7),400,4),
        ("Fill",(-4,-2,5),175,5),
        ("Rim",(1,4,6),260,3),
    ):
        data=bpy.data.lights.new("LGT_"+name,"AREA")
        data.energy=power
        data.shape="DISK"
        data.size=size
        light=bpy.data.objects.new("LGT_"+name,data)
        bpy.context.collection.objects.link(light)
        light.location=xyz
        light.rotation_euler=(target-Vector(xyz)).to_track_quat('-Z','Y').to_euler()
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.samples=16
    scene.render.resolution_x=512
    scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.view_transform="AgX"


def organize_scene(rig):
    for name in ("BODY", "RIG", "PROPS", "FX", "CAMERAS", "LIGHTS"):
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    for obj in tuple(bpy.context.scene.objects):
        if obj == rig:
            category = "RIG"
        elif obj.type == "CAMERA":
            category = "CAMERAS"
        elif obj.type == "LIGHT":
            category = "LIGHTS"
        elif any(word in obj.name for word in ("glint", "ember", "smoke", "runelight")):
            category = "FX"
        elif any(word in obj.name for word in ("shield", "arch", "plate", "crystal", "pouch", "mallet")):
            category = "PROPS"
        else:
            category = "BODY"
        bpy.data.collections[category].objects.link(obj)
        for collection in tuple(obj.users_collection):
            if collection.name != category:
                collection.objects.unlink(obj)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children["BODY"]
    bpy.data.collections.remove(bpy.data.collections["Collection"])


def build_monster(kind, output=True):
    assert kind in KINDS, kind
    reset()
    rig, scale = rig_for(kind)
    mats={name:material("MAT_"+kind+"_"+name, col, glow=.45 if name=="accent" and kind=="ember_wisp" else 0)
          for name,col in COLORS[kind].items()}
    make_creature(kind,rig,scale,mats)
    animate(kind,rig)
    set_preview(kind)
    organize_scene(rig)
    scene=bpy.context.scene
    geometry=[obj for obj in scene.objects if obj.type=="MESH"]
    triangles=sum(len(poly.vertices)-2 for obj in geometry for poly in obj.data.polygons)
    folder=destination(ROOT+"/frontend/public/assets/monsters/"+kind)
    os.makedirs(folder, exist_ok=True)
    if output:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder,kind+".blend"),compress=True)
        scene.render.filepath=os.path.join(folder,kind+"_preview.png")
        bpy.ops.render.render(write_still=True)
        bpy.ops.object.select_all(action="DESELECT")
        rig.select_set(True)
        for obj in geometry:
            obj.select_set(True)
        bpy.context.view_layer.objects.active=rig
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder,kind+"_preview.glb"), export_format="GLB",use_selection=True,
                                  export_animations=True,export_nla_strips=False,export_force_sampling=True)
        with open(os.path.join(folder,"model-report.json"),"w",encoding="utf8") as f:
            json.dump({"id":kind,"triangles":triangles,"meshes":len(geometry),"bones":len(rig.data.bones),
                       "actions":list(FREQUENCIES),"blend":kind+".blend","glb":kind+"_preview.glb",
                       "preview":kind+"_preview.png"},f,indent=2)
    print("MONSTER_COMPLETE",kind,"tris",triangles,"meshes",len(geometry),"bones",len(rig.data.bones),"folder",folder)
    return {"id":kind,"tris":triangles,"meshes":len(geometry),"folder":folder}
