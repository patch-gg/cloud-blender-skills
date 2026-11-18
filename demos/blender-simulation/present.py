"""Presentation: the clip's frame range back to 1-120 (the cloth was set up and baked over 48-120, so it waits
above the frame until the crates have settled), a slow push-in on the pile, two small labels that switch
when the cloth starts, and the render settings (EEVEE, 1280x720, 24 fps). Run in the session:
    cloud.py run present.py -- --labels "rigid bodies" "cloth" --switch 48
"""
import argparse
import json
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--labels", nargs="*", default=[])
ap.add_argument("--switch", type=int, default=48)
ap.add_argument("--cam-a", type=float, nargs=3, default=(3.55, -4.3, 1.5))
ap.add_argument("--cam-b", type=float, nargs=3, default=(3.0, -3.65, 1.42))
ap.add_argument("--look", type=float, nargs=3, default=(-0.75, 0.55, 0.62))
ap.add_argument("--lens", type=float, default=35)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, 120, 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.engine = "BLENDER_EEVEE"
for n in ("Cam", "Cam_Target"):
    ob = bpy.data.objects.get(n)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
for ob in [o for o in bpy.data.objects if o.name.startswith("Label_")]:
    bpy.data.objects.remove(ob, do_unlink=True)
cd = bpy.data.cameras.new("Cam")
cd.lens, cd.clip_start, cd.clip_end = a.lens, 0.05, 200
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
tgt = bpy.data.objects.new("Cam_Target", None)
sc.collection.objects.link(tgt)
tgt.location = a.look
edit = bpy.context.preferences.edit
interp, edit.keyframe_new_interpolation_type = edit.keyframe_new_interpolation_type, "LINEAR"
for f, p in ((1, a.cam_a), (120, a.cam_b)):
    cam.location = p
    cam.keyframe_insert("location", frame=f)
edit.keyframe_new_interpolation_type = interp
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam

half_w = 0.5 * cd.sensor_width / cd.lens
half_h = half_w * 720 / 1280
lm = bpy.data.materials.get("M_Label") or bpy.data.materials.new("M_Label")
nt = lm.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.0056, 0.0056, 0.0056, 1)  # #111: dark grey on the sunlit concrete
em.inputs["Strength"].default_value = 1.0
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
labels = []
for i, text in enumerate(a.labels[:2]):
    cu = bpy.data.curves.new(f"Label_{i}", "FONT")
    cu.body, cu.size, cu.align_x = text, half_h * 2 * 0.034, "LEFT"
    cu.materials.append(lm)
    t = bpy.data.objects.new(f"Label_{i}", cu)
    sc.collection.objects.link(t)
    t.parent = cam
    t.location = (-half_w + half_w * 2 * 0.035, -half_h + half_h * 2 * 0.06, -1.0)
    t.visible_shadow = False
    if len(a.labels) > 1:
        for f, hidden in ((1, i != 0), (a.switch, i != 1)):
            t.hide_render = t.hide_viewport = hidden
            t.keyframe_insert("hide_render", frame=f)
            t.keyframe_insert("hide_viewport", frame=f)
    labels.append(t.name)
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": [1, 120], "camera": cam.name, "labels": labels}))
