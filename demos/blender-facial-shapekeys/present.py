"""Presentation: a portrait camera on the face with a gentle +-6 degree swing (seamless), and the FaceCtrl
properties (from shapekeys.py --drivers) keyed through a sequence of keys. The active key's name is a small
label in the corner, with a bar that fills with its value. 1280x720, frames 1-120, starts and ends neutral.
Run in the session after turntable.py: cloud.py run present.py"""
import json
import math
import os

import bpy
from mathutils import Vector

SEQ = [  # what the clip shows, in order: label lines, FaceCtrl values
    (["jawOpen"], {"jawOpen": 1.0}),
    (["mouthSmileLeft", "mouthSmileRight"], {"mouthSmileLeft": 1.0, "mouthSmileRight": 1.0}),
    (["eyeBlinkLeft"], {"eyeBlinkLeft": 1.0}),
    (["browInnerUp"], {"browInnerUp": 1.0}),
    (["viseme_O"], {"viseme_O": 1.0}),
    (["viseme_E"], {"viseme_E": 1.0}),
    (["browDownLeft", "browDownRight"], {"browDownLeft": 1.0, "browDownRight": 1.0}),
    (["cheekPuff"], {"cheekPuff": 1.0}),
]
SEG = 15                               # frames per key: 4 in, 7 held, 4 out
FRAMES = SEG * len(SEQ)
INK = (0.006, 0.006, 0.006)            # #111-ish label ink
BACKDROP = (0.30, 0.30, 0.31)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
head = bpy.data.objects["Head"]
ctrl = bpy.data.objects["FaceCtrl"]
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera

# ---- camera: frame the head by its height, slightly from the character's left
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
pts = [head.matrix_world @ Vector(c) for c in head.bound_box]
zlo, zhi = min(p.z for p in pts), max(p.z for p in pts)
target = Vector((0.0, 0.0, (zlo + zhi) / 2 - 0.012))
cam.data.lens = 85
cam.data.dof.use_dof = False
vfov = 2 * math.atan(cam.data.sensor_width * 9 / 16 / 2 / cam.data.lens)
dist = (zhi - zlo) * 1.30 / 2 / math.tan(vfov / 2)
az, el = math.radians(16), math.radians(5)
cam.parent = None
cam.location = target + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, 50
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, 0), (31, 6), (61, 0), (91, -6), (121, 0)):     # frame 121 = frame 1
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

# ---- the expressions: FaceCtrl properties drive the keys (shapekeys.py --drivers)
keys = sorted({k for _, vals in SEQ for k in vals})
for k in keys:
    ctrl[k] = 0.0
    ctrl.keyframe_insert(f'["{k}"]', frame=1)
    ctrl.keyframe_insert(f'["{k}"]', frame=FRAMES + 1)
for i, (_, vals) in enumerate(SEQ):
    s = 1 + i * SEG
    for k, v in vals.items():
        for f, x in ((s, 0.0), (s + 4, v), (s + 11, v), (s + SEG, 0.0)):
            ctrl[k] = x
            ctrl.keyframe_insert(f'["{k}"]', frame=f)

# ---- label + value bar, fixed to the camera
fonts = os.path.join(bpy.utils.system_resource("DATAFILES"), "fonts")
try:
    font = bpy.data.fonts.load(os.path.join(fonts, "DejaVuSansMono.woff2"), check_existing=True)
except RuntimeError:
    font = None
ink = bpy.data.materials.new("M_Label")
ink.use_nodes = True
nt = ink.node_tree
nt.nodes.clear()
em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value = (*INK, 1)
nt.links.new(em.outputs[0], out.inputs["Surface"])
D = 0.5                                               # labels sit this far in front of the lens
half_h = D * math.tan(vfov / 2)
half_w = half_h * 16 / 9
px = 2 * half_h / 720                                 # metres per pixel at that distance
x0, y0 = -half_w + 72 * px, -half_h + 72 * px         # bottom-left, 72 px in
size = 34 * px
labels = []
for i, (lines, _) in enumerate(SEQ):
    cu = bpy.data.curves.new(f"Label_{i}", "FONT")
    cu.body = "\n".join(lines)
    cu.size, cu.align_x, cu.align_y = size, "LEFT", "BOTTOM"
    cu.space_line = 1.05
    cu.offset = 0.7 * px                               # a touch heavier than the regular weight
    if font:
        cu.font = font
    cu.materials.append(ink)
    t = bpy.data.objects.new(f"Label_{i}", cu)
    sc.collection.objects.link(t)
    t.parent = cam
    t.location = (x0, y0 + 18 * px, -D)
    s = 1 + i * SEG
    for f, hidden in ((1, True), (s, False), (s + SEG, True)):
        t.hide_render = t.hide_viewport = hidden
        t.keyframe_insert("hide_render", frame=f)
        t.keyframe_insert("hide_viewport", frame=f)
    labels.append(t.name)
bar_me = bpy.data.meshes.new("ValueBar")
w, hh = 210 * px, 3 * px
bar_me.from_pydata([(0, -hh, 0), (w, -hh, 0), (w, hh, 0), (0, hh, 0)], [], [(0, 1, 2, 3)])
bar_me.materials.append(ink)
bar = bpy.data.objects.new("ValueBar", bar_me)
sc.collection.objects.link(bar)
bar.parent = cam
bar.location = (x0, y0, -D)
bar.scale = (0.0, 1, 1)
bar.keyframe_insert("scale", index=0, frame=1)
for i, (_, vals) in enumerate(SEQ):
    s, v = 1 + i * SEG, max(vals.values())
    for f, x in ((s, 0.0), (s + 4, v), (s + 11, v), (s + SEG, 0.0)):
        bar.scale = (x, 1, 1)
        bar.keyframe_insert("scale", index=0, frame=f)

# ---- the stage
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*BACKDROP, 1)
    b.inputs["Roughness"].default_value = 0.8
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.frame_set(1 + 1 * SEG + 7)
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "keys_shown": [l for l, _ in SEQ], "lens": 85,
                               "distance": round(dist, 3), "labels": len(labels)}))
