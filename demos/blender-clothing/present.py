"""Presentation for the clothing demo (in the session, after turntable.py), frames 1-120, looping:

  1-16 the t-shirt | 16-46 the vest sweeps on, hem to collar, behind a thin pink edge | 46-104 he twists
  both ways and lifts his arms, the vest moving with him | 104-120 it sweeps off again
The shirt's Hidden_Vest mask (garment.py --hide-body) is on only while the vest is whole. Poses are keyed on
the control rig's FK controls with stress_poses.py's world-axis helper; the camera frames him from the knees
up and drifts +-14 degrees.
Run in the session: cloud.py run present.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

here = os.path.dirname(os.path.abspath(__file__))
for d in (os.path.join(here, "_skills"), os.path.join(here, "..", "..", "skills")):  # session, repo
    if os.path.isdir(d):
        sys.path.insert(0, os.path.join(d, "blender-character-rigging", "scripts"))
        break
import stress_poses as sp  # noqa: E402

sc = bpy.context.scene
rig, shirt, vest = bpy.data.objects["RIG_Body"], bpy.data.objects["Shirt"], bpy.data.objects["Vest"]
END = 121
ON, OFF = 46, 104

# ---------------------------------------------------------------- the moves
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    if "IK_FK" in pb.keys():
        pb["IK_FK"] = 1.0
    pb.matrix_basis = Matrix()
act = bpy.data.actions.new("Show")
rig.animation_data_create()
rig.animation_data.action = act
MOVES = {1: [], ON: [], 62: [("spine", None, (0, 0, 1), 32), ("head", None, (0, 0, 1), 18),
                             ("upper_arm", "L", (1, 0, 0), 25), ("upper_arm", "R", (1, 0, 0), -25)],
         80: [("spine", None, (0, 0, 1), -32), ("head", None, (0, 0, 1), -18),
              ("upper_arm", "L", (1, 0, 0), -25), ("upper_arm", "R", (1, 0, 0), 25)],
         96: [("upper_arm", "L", (0, 1, 0), -48), ("upper_arm", "R", (0, 1, 0), 48),
              ("forearm", "L", (0, 1, 0), -12), ("forearm", "R", (0, 1, 0), 12)],
         OFF: [], END: []}
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
try:
    for f, ops in MOVES.items():
        sc.frame_set(f)
        for pb in rig.pose.bones:
            pb.matrix_basis = Matrix()
        for role, side, axis, deg in ops:
            pb = sp._find(rig, role, side)
            if pb:
                sp._rotate(rig, pb, axis, deg)
        for pb in rig.pose.bones:
            for path in ("location", "rotation_quaternion", "rotation_euler", "scale"):
                pb.keyframe_insert(path, frame=f)
finally:
    bpy.ops.object.mode_set(mode="OBJECT")
sc.frame_start, sc.frame_end = 1, END - 1

# ---------------------------------------------------------------- the vest sweeps on and off
rev = vest.active_material.node_tree.nodes["Reveal"].outputs[0]
for f, v in ((1, -0.1), (16, -0.04), (ON, 1.05), (OFF, 1.05), (END - 1, -0.04), (END, -0.1)):
    rev.default_value = v
    rev.keyframe_insert("default_value", frame=f)
mask = shirt.modifiers["Hidden_Vest"]
for f, on in ((1, False), (ON, True), (OFF, False)):
    mask.show_render = mask.show_viewport = on
    mask.keyframe_insert("show_render", frame=f)
    mask.keyframe_insert("show_viewport", frame=f)
for idb in (shirt, ):
    for fc in [fc for layer in idb.animation_data.action.layers for st in layer.strips
               for cb in st.channelbags for fc in cb.fcurves]:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

# ---------------------------------------------------------------- stage
vest.visible_shadow = False   # EEVEE's shadow maps speckled the vest's own grazing sides (it shadowed itself)
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.07, 0.07, 0.075, 1)
for lo in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lo.data.energy *= 0.75
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
pivot.location = Vector((0.0, 0.06, 1.3))
cam = sc.camera
cam.data.lens = 50
cam.data.dof.use_dof = False
vfov = 2 * math.atan(cam.data.sensor_width * 9 / 16 / 2 / cam.data.lens)
dist = 0.86 / math.tan(vfov / 2)
el = math.radians(5)
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
for f, deg in ((1, -14), (61, 14), (END, -14)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": [1, END - 1], "vest_on": [16, ON], "vest_off": [OFF, END - 1],
                               "moves_at": sorted(MOVES), "camera_distance_m": round(dist, 2)}))
