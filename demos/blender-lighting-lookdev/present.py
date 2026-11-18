"""Presentation for one panel of blender-lighting-lookdev's clip, run after each turntable.py call.

turntable.py's orbit stays as it built it (camera, lights and backdrop turn once in 120 frames, frame 121 =
frame 1). This only brings the camera in so the bust fills a 428x720 panel (its widest turn still fits the
width) and names the rig at the bottom. Re-running replaces the label.
Run in the session: cloud.py run present.py -- "<label>" [light|dark]   (ink: light on a dark panel)"""
import json
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
label, ink_tone = args[0], (args[1] if len(args) > 1 else "light")
W_PX, H_PX, FILL = 428, 720, 0.64           # panel size, share of its height the bust takes
EXPOSURE = -1.4                             # one exposure for every rig, as look-dev compares them
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W_PX, H_PX, 100
for o in [o for o in bpy.data.objects if o.name.startswith("DEMO_")]:
    bpy.data.objects.remove(o, do_unlink=True)
bust = bpy.data.objects["Bust"]
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera
sc.frame_set(1)                             # the orbit's start: pivot at 0
bpy.context.view_layer.update()

# --- camera: closer than the bounding-sphere fit, aimed a little above the middle (the head)
pts = [bust.matrix_world @ Vector(c) for c in bust.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + (hi.z - lo.z) * 0.53))
cam.data.sensor_fit = "VERTICAL"
cam.data.sensor_height = cam.data.sensor_width = 36.0
vfov = 2 * math.atan(cam.data.sensor_height / 2 / cam.data.lens)
dist = (hi.z - lo.z) / FILL / 2 / math.tan(vfov / 2)
el = math.radians(10)
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, dist * 20
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()

# --- the rig's name, small, at the bottom of the panel (camera rays only)
D = 0.5
H = 2 * D * math.tan(vfov / 2)
px = H / H_PX
cu = bpy.data.curves.new("DEMO_Label", "FONT")
cu.body, cu.size, cu.align_x = label, 22 * px, "CENTER"
ink = bpy.data.materials.get("DEMO_Ink") or bpy.data.materials.new("DEMO_Ink")   # one label per panel
nt = ink.node_tree
nt.nodes.clear()
em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
tone = (0.8, 0.8, 0.8, 1) if ink_tone == "light" else (0.006, 0.006, 0.006, 1)   # ~#111 when dark
em.inputs["Color"].default_value, em.inputs["Strength"].default_value = tone, 2 ** -EXPOSURE
nt.links.new(em.outputs[0], out.inputs["Surface"])
cu.materials.append(ink)
t = bpy.data.objects.new("DEMO_Label", cu)
t.location = (0, -H / 2 + 34 * px, -D)
for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
    setattr(t, k, False)
t.parent = cam
sc.collection.objects.link(t)

sc.view_settings.view_transform = "AgX"
sc.view_settings.exposure = EXPOSURE
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
print("@@JSON@@" + json.dumps({"ok": True, "label": label, "distance": round(dist, 3), "frames": [sc.frame_start, sc.frame_end]}))
