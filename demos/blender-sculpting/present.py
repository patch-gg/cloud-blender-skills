"""Presentation: the sculpt after each pass, in a row (left to right in the order the passes ran), each on
the same slow +-28 degree swing so the forms read in three-quarter view; a small label in front of each.
The first two also show their wireframe, because what remesh changes is the topology: 13 overlapping parts
become one even voxel grid. Frames the row by its width. 1280x720, frames 1-120, a seamless loop.
Run after turntable.py: cloud.py run present.py -- --labels base remesh smooth inflate detail"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--labels", nargs="+", required=True)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

F = 120
LIGHT_SCALE = 0.45             # turntable's studio rig is sized for about exposure -1 under AgX
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
row = sorted([o for o in bpy.data.collections["Stages"].objects] + [bpy.data.objects["Moai"]],
             key=lambda o: o.location.x)
assert len(row) == len(args.labels), (len(row), args.labels)

# ---- stage: a still rig, the camera framed on the row's width
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
xs = [o.location.x for o in row]
width = (max(xs) - min(xs)) + 0.7 + 0.45
height = max(o.dimensions.z for o in row)
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(9)
target = Vector(((max(xs) + min(xs)) / 2, 0, height * 0.42))
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for lt in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lt.data.energy *= LIGHT_SCALE

# ---- every stage rests on the floor and swings the same way, in sync
for o in row:
    o.location.z -= min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    o.animation_data_clear()
    for f, deg in ((1, 0), (31, 28), (61, 0), (91, -28), (121, 0)):
        o.rotation_euler = (0, 0, math.radians(deg))
        o.keyframe_insert("rotation_euler", index=2, frame=f)

# ---- labels: small placards on the floor in front of each stage
lab = bpy.data.materials.new("M_Label")
b = next(n for n in lab.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.006, 0.006, 0.006, 1)        # #111
b.inputs["Roughness"].default_value = 0.8
for o, text in zip(row, args.labels):
    cu = bpy.data.curves.new("Label_" + o.name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = text, 0.085, "CENTER", "CENTER"
    cu.materials.append(lab)
    t = bpy.data.objects.new("Label_" + o.name, cu)
    t.location = (o.location.x, -0.62, 0.03)
    t.rotation_euler = (math.radians(90 - 9), 0, 0)    # standing, facing the camera
    sc.collection.objects.link(t)

# ---- the topology of the first two stages, as a thin wire over the clay
wire = bpy.data.materials.new("M_Wire")
b = next(n for n in wire.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
b.inputs["Roughness"].default_value = 0.7
for o in row[:2]:
    if len(o.data.materials) < 2:
        o.data.materials.append(wire)
    w = o.modifiers.new("Wire", "WIREFRAME")
    w.thickness, w.use_replace, w.use_even_offset, w.material_offset = 0.0025, False, True, 1

# ---- look: a light clay stage
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.36, 0.36, 0.36, 1)
    b.inputs["Roughness"].default_value = 0.9
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Base Contrast"
except TypeError:
    pass
sc.view_settings.exposure = -1.6
sc.frame_set(31)
print("@@JSON@@" + json.dumps({"ok": True, "stages": [o.name for o in row], "distance": round(dist, 2)}))
