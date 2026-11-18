"""Presentation for the animation demo (in the session, after turntable.py): the mocap source and the retargeted
target side by side at the same depth, both turned --face degrees so their stride reads, each playing its clip
twice (F-curve Cycles modifiers, preview only), so frames 1-106 loop; small labels with their heights; the camera
framed on the pair, swinging +-10 degrees.
Run in the session: cloud.py run present.py -- --source Mocap --target GAME_RIG_Body --cycle 53 [--face 25]
"""
import json
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


sc = bpy.context.scene
src, tgt = bpy.data.objects[arg("--source", "Mocap")], bpy.data.objects[arg("--target", "GAME_RIG_Body")]
CYCLE = int(arg("--cycle", "53"))
FACE = math.radians(float(arg("--face", "25")))
END = 2 * CYCLE + 1                                     # frame END == frame 1


def meshes_of(arm):
    return [o for o in bpy.data.objects if o.type == "MESH" and any(
        m.type == "ARMATURE" and m.object == arm for m in o.modifiers)]


def fcurves(ob):
    ad = ob.animation_data
    return [fc for layer in ad.action.layers for st in layer.strips
            for cb in st.channelbags if cb.slot == ad.action_slot for fc in cb.fcurves]


for ob in (src, tgt):
    for fc in fcurves(ob):
        if not any(m.type == "CYCLES" for m in fc.modifiers):
            fc.modifiers.new("CYCLES")
sc.frame_start, sc.frame_end = 1, END - 1


def height(arm):
    """Standing height: the meshes at the rig's rest pose."""
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for o in meshes_of(arm):
        me = o.evaluated_get(dg).to_mesh()
        zs += [(o.matrix_world @ v.co).z for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
    arm.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    return max(zs) - min(zs)


def centre_x(arm):
    pts = [o.matrix_world @ Vector(c) for o in meshes_of(arm) for c in o.bound_box]
    return (max(p.x for p in pts) + min(p.x for p in pts)) / 2


def label(text, x):
    cu = bpy.data.curves.new(f"Label_{text}", "FONT")
    cu.body, cu.size, cu.align_x = text, 0.08, "CENTER"
    t = bpy.data.objects.new(f"Label_{text}", cu)
    t.location = (x, -0.62, 0.012)
    t.rotation_euler = (math.radians(90), 0, 0)
    m = bpy.data.materials.new("M_Label")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.85, 0.85, 0.85, 1)
    b.inputs["Roughness"].default_value = 0.6
    cu.materials.append(m)
    sc.collection.objects.link(t)
    return t.name


hs, ht = height(src), height(tgt)
for arm in (src, tgt):                                      # turn each in place, about its own feet
    root = arm
    while root.parent:
        root = root.parent
    root.rotation_mode = "XYZ"                              # (glTF roots come in as quaternions)
    root.rotation_euler.z += FACE
bpy.context.view_layer.update()
xs, xt = centre_x(src), centre_x(tgt)
labels = [label(f"source · {hs:.2f} m", xs), label(f"target · {ht:.2f} m", xt)]

bd = bpy.data.materials.get("LD_Backdrop")                  # the same darker stage as the rigging demo
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.07, 0.07, 0.075, 1)
for lo in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lo.data.energy *= 0.75
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
pivot.location = Vector(((xs + xt) / 2, 0.0, 0.97))
cam = sc.camera
cam.data.lens = 50
cam.data.dof.use_dof = False
vfov = 2 * math.atan(cam.data.sensor_width * 9 / 16 / 2 / cam.data.lens)
dist = 1.38 / math.tan(vfov / 2)
el = math.radians(6)
cam.parent = None
target = pivot.location.copy()
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.1, 100
bpy.context.view_layer.update()
for o in [o for o in bpy.data.objects if o.parent == pivot] + [cam]:
    mw = o.matrix_world.copy()
    o.parent = pivot
    o.matrix_parent_inverse = pivot.matrix_world.inverted()
    o.matrix_world = mw
q = (END - 1) // 4
for f, deg in ((1, 0), (1 + q, 10), (1 + 2 * q, 0), (1 + 3 * q, -10), (END, 0)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": [1, END - 1], "cycle": CYCLE, "labels": labels,
                               "heights_m": [round(hs, 3), round(ht, 3)], "camera_distance_m": round(dist, 2)}))
