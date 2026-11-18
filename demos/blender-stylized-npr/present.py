"""Presentation for blender-stylized-npr: the row of knights (pbr | bands | + shadow tint | + rim | + outline)
under one key light. The camera holds still; the key sun that toon_setup.py drives every toon copy with
(NPR_Key) swings from the left side to the right and back, so the bands, the tinted shadows and the rim
sweep across all of them while the pbr copy takes the same light physically. Frames 1-96, a seamless loop.
Run in the session after toon_setup.py and turntable.py: cloud.py run present.py"""
import json
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

F = 96
TILT, SWING = 0.82, 1.15                    # sun: radians from straight down, azimuth swing either side
LABELS = {"pbr": "pbr", "bands": "bands", "tint": "+ shadow tint", "rim": "+ rim", "outline": "+ outline"}
INK = (0.012, 0.012, 0.012, 1)              # ~#111 under the Standard view toon_setup.py sets

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera
row = [o for o in bpy.data.objects if o.name.startswith("Knight_")]
row.sort(key=lambda o: o.location.x)

# --- camera: still, the row framed by its width
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in row for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + (hi.z - lo.z) * 0.42))
width = (hi.x - lo.x) + 0.55
cam.data.lens, cam.data.sensor_fit, cam.data.dof.use_dof = 50, "HORIZONTAL", False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(6)
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, dist * 10
bpy.context.view_layer.update()

# --- the key: swing the sun's azimuth, extremes keyed outside 1..97 so frame 97 = frame 1
sun = bpy.data.objects["NPR_Key"]
sun.animation_data_clear()
for f, az in ((-23, -SWING), (25, SWING), (73, -SWING), (121, SWING)):
    sun.rotation_euler = (TILT, 0, az)
    sun.keyframe_insert("rotation_euler", frame=f)
sun.data.angle = math.radians(1.5)          # a little softness on the cast shadows
sun.data.energy = 4.0

# --- labels under each knight, in front of the lens (camera rays only)
D = 0.5
W = 2 * D * math.tan(hfov / 2)
H = W * 720 / 1280
px = W / 1280
ink = bpy.data.materials.new("DEMO_Ink")
nt = ink.node_tree
nt.nodes.clear()
em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value = INK
nt.links.new(em.outputs[0], out.inputs["Surface"])
for o in row:
    stage = o.name.split("_", 1)[1]
    u = world_to_camera_view(sc, cam, o.matrix_world.translation).x      # feet centre, 0..1 across the frame
    cu = bpy.data.curves.new("DEMO_" + stage, "FONT")
    cu.body, cu.size, cu.align_x = LABELS[stage], 22 * px, "CENTER"
    cu.materials.append(ink)
    t = bpy.data.objects.new("DEMO_Label_" + stage, cu)
    t.location = ((u - 0.5) * W, -H / 2 + 112 * px, -D)
    for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(t, k, False)
    t.parent = cam
    sc.collection.objects.link(t)

# --- stage: a light backdrop and a dim, even world as fill for the pbr copy (the toon copies ignore both)
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(x for x in bd.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.55, 0.55, 0.57, 1)
    b.inputs["Roughness"].default_value = 0.9
bg = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0.2, 0.2, 0.22, 1), 1.0
sc.view_settings.exposure = 0.0
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 2), "key": sun.name,
                               "labels": [LABELS[o.name.split("_", 1)[1]] for o in row]}))
