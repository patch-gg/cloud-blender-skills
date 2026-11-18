"""Presentation: the operator's three gears as a working train. Each gear is turned so its teeth sit in the
gaps of the gear it meshes with, then spun at the true ratio (12 : 36 : 20). The pinion makes one full turn in
120 frames, so each gear turns through whole teeth and whole spoke steps (6 spokes on 36 teeth, 5 on 20)
and the clip loops seamlessly. A small label under each gear gives the parameters its operator call used.
The gears keep the metal their operator call gave them. 1280x720.

Run in the session after make_gears.py and turntable.py: cloud.py run present.py
"""
import json
import math

import bpy
from bpy_extras import anim_utils
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

FRAMES = 120
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
gears = sorted([o for o in bpy.data.objects if "gear" in o], key=lambda o: o.location.x)
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera


# --- mesh and spin: phase_a(psi) + phase_b(psi + pi) = 1/2, tooth centres at local angle 0 -----------------
def phase(theta, n, direction):
    return ((direction - theta) * n / (2 * math.pi)) % 1.0


theta = [0.0]
speed = [-2 * math.pi]                            # the pinion: one full turn over the clip
for prev, (a, b) in enumerate(zip(gears, gears[1:])):
    na, nb = a["gear"]["teeth"], b["gear"]["teeth"]
    d = b.location - a.location
    psi = math.atan2(d.y, d.x)
    theta.append(psi + math.pi - (0.5 - phase(theta[prev], na, psi)) * 2 * math.pi / nb)
    speed.append(-speed[prev] * na / nb)
for g, t0, w in zip(gears, theta, speed):
    g.animation_data_clear()
    for f, t in ((1, t0), (FRAMES + 1, t0 + w)):  # frame 121 == frame 1: a whole number of teeth later
        g.rotation_euler = (0, 0, t)
        g.keyframe_insert("rotation_euler", index=2, frame=f)
    ad = g.animation_data
    for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"                # constant speed, no easing at the loop point

# --- labels: the operator's parameters, flat on the floor under each gear --------------------------------
lm = bpy.data.materials.get("FX_Label") or bpy.data.materials.new("FX_Label")
lb = next(n for n in lm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
lb.inputs["Base Color"].default_value = (0.0056, 0.0056, 0.0056, 1)   # #111 on the light floor
lb.inputs["Roughness"].default_value = 1.0
lb.inputs["Specular IOR Level"].default_value = 0.0    # no sheen: #111 stays dark under the lights
fx = bpy.data.collections.get("FX") or bpy.data.collections.new("FX")
if fx.name not in sc.collection.children:
    sc.collection.children.link(fx)
labels = []
for g in gears:
    p = g["gear"]
    body = f"{p['teeth']} teeth" + (f" · {p['spokes']} spokes" if p["spokes"] else "")
    cu = bpy.data.curves.new("FX_Label_" + g.name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = body, 0.03, "CENTER", "TOP"
    cu.materials.append(lm)
    t = bpy.data.objects.new("FX_Label_" + g.name, cu)
    r_tip = p["module"] * (p["teeth"] / 2 + 1)
    t.location = (g.location.x, g.location.y - r_tip - 0.035, 0.001)
    t.visible_shadow = False
    fx.objects.link(t)
    labels.append((t.location.copy(), len(body) * 0.55 * cu.size))

# --- camera: look down at the train, framed by its width --------------------------------------------------
pts = [g.matrix_world @ Vector(c) for g in gears for c in g.bound_box]
for loc, w in labels:                             # the labels count too
    pts += [loc + Vector((-w / 2, -0.04, 0)), loc + Vector((w / 2, -0.04, 0))]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), 0))
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
width = (hi.x - lo.x) * 1.12
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(52)
target = (lo + hi) / 2
cam.parent = None
corners = [p + Vector((0, 0, z)) for p in pts for z in (0.0, 0.03)]
view = Vector((0, -math.cos(el), math.sin(el)))
for _ in range(6):                                # fit every gear and label corner, centred, ~90% of the frame
    cam.location = target + view * dist
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    uv = [world_to_camera_view(sc, cam, c) for c in corners]
    x0, x1 = min(q.x for q in uv), max(q.x for q in uv)
    y0, y1 = min(q.y for q in uv), max(q.y for q in uv)
    w_frame = 2 * dist * math.tan(hfov / 2)
    target += cam.matrix_world.to_3x3() @ Vector((((x0 + x1) / 2 - 0.5) * w_frame,
                                                   ((y0 + y1) / 2 - 0.5) * w_frame * 720 / 1280, 0))
    dist *= max((x1 - x0) / 0.9, (y1 - y0) / 0.86)
cam.location = target + view * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()

bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.03, 0.03, 0.033, 1)
    b.inputs["Roughness"].default_value = 0.6
sc.view_settings.exposure = -0.9
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 3, 8
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "gears": [g.name for g in gears],
                               "turns": [round(w / (2 * math.pi), 3) for w in speed],
                               "distance": round(dist, 2)}))
