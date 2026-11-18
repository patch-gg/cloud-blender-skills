"""Presentation: a slow aerial drift (camera moves at constant speed from A to B while aiming at a target
that moves from T0 to T1), two small labels parented to the camera that switch as the scatter sweeps in,
the render settings (EEVEE, 1280x720, 24 fps, AgX Medium High Contrast), and --sink: lower a backdrop terrain (made by terrain.py with
--flatten 0 0 R) so its flattened centre sits just under the main terrain and only its far ranges show.
Run in the session:
    cloud.py run present.py -- --cam-a X Y Z --cam-b X Y Z --look-a X Y Z --look-b X Y Z --lens 32
        --frames 1 120 --labels "terrain" "scatter" --switch 56 --sink Far
"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--cam-a", type=float, nargs=3, required=True)
ap.add_argument("--cam-b", type=float, nargs=3, required=True)
ap.add_argument("--look-a", type=float, nargs=3, required=True)
ap.add_argument("--look-b", type=float, nargs=3, required=True)
ap.add_argument("--lens", type=float, default=32)
ap.add_argument("--frames", type=int, nargs=2, default=(1, 120))
ap.add_argument("--labels", nargs="*", default=[])
ap.add_argument("--switch", type=int, default=0, help="frame the second label replaces the first")
ap.add_argument("--sink", default=None, help="backdrop terrain to lower under the main one")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

sc = bpy.context.scene
f0, f1 = a.frames
sc.frame_start, sc.frame_end = f0, f1
sc.render.fps = 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "AgX"  # scene_mood.py runs with --keep-view and keeps this
sc.view_settings.look = "AgX - Medium High Contrast"

sunk = None
if a.sink:
    bd = bpy.data.objects[a.sink]
    me = bd.data
    res = int(round(len(me.vertices) ** 0.5))
    zc = me.vertices[(res // 2) * res + res // 2].co.z  # the flattened centre
    bd.location.z = sunk = round(-zc - 3.0, 2)

for n in ("Cam", "Cam_Target"):
    ob = bpy.data.objects.get(n)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
for ob in [o for o in bpy.data.objects if o.name.startswith("Label_")]:
    bpy.data.objects.remove(ob, do_unlink=True)

cd = bpy.data.cameras.new("Cam")
cd.lens, cd.clip_start, cd.clip_end = a.lens, 0.1, 5000
cd.dof.use_dof = False
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
tgt = bpy.data.objects.new("Cam_Target", None)
sc.collection.objects.link(tgt)
edit = bpy.context.preferences.edit
interp, edit.keyframe_new_interpolation_type = edit.keyframe_new_interpolation_type, "LINEAR"
for ob, p0, p1 in ((cam, a.cam_a, a.cam_b), (tgt, a.look_a, a.look_b)):
    for f, p in ((f0, p0), (f1, p1)):  # constant speed: a slice of a longer flight
        ob.location = p
        ob.keyframe_insert("location", frame=f)
edit.keyframe_new_interpolation_type = interp
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam

# labels: small white text in the bottom-left corner, 1 m in front of the lens
half_w = 0.5 * cd.sensor_width / cd.lens
half_h = half_w * 720 / 1280
mat = bpy.data.materials.get("M_Label") or bpy.data.materials.new("M_Label")
nt = mat.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1, 1, 1, 1)
em.inputs["Strength"].default_value = 3.0
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
labels = []
for i, text in enumerate(a.labels):
    cu = bpy.data.curves.new(f"Label_{i}", "FONT")
    cu.body, cu.size, cu.align_x = text, half_h * 2 * 0.034, "LEFT"
    cu.materials.append(mat)
    t = bpy.data.objects.new(f"Label_{i}", cu)
    sc.collection.objects.link(t)
    t.parent = cam
    t.location = (-half_w + half_w * 2 * 0.035, -half_h + half_h * 2 * 0.06, -1.0)
    t.visible_shadow = False
    if len(a.labels) > 1 and a.switch:
        show = [(f0, i != 0), (a.switch, i != 1)] if i < 2 else []
        for f, hidden in show:
            t.hide_render = t.hide_viewport = hidden
            t.keyframe_insert("hide_render", frame=f)
            t.keyframe_insert("hide_viewport", frame=f)
    labels.append(t.name)
bpy.context.view_layer.update()
sc.frame_set(f0)
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "lens": a.lens, "frames": [f0, f1],
                               "speed_m_s": round((Vector(a.cam_b) - Vector(a.cam_a)).length / ((f1 - f0) / 24), 1),
                               "labels": labels, "backdrop_z": sunk, "hfov_deg": round(math.degrees(2 * math.atan(half_w)), 1)}))
