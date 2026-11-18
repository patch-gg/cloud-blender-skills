"""Presentation after turntable.py: a thin pixel-wide wire over the porcelain so each LOD's triangle density
reads, the rig held still (the statues turn instead), the row framed by its width, a dark backdrop, AgX.
1280x720, frames 1-96. Run in the session: cloud.py run present.py -- SM_Horse"""
import json
import math
import sys

import bpy
from mathutils import Vector

base = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "SM_Horse"
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
lods = sorted((o for o in bpy.data.objects if o.name.startswith(base + "_LOD") and o.type == "MESH"),
              key=lambda o: o.name)

# the wire: a 1 px line mixed into the material's base colour (every LOD shares the material)
mat = lods[0].material_slots[0].material
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
if not any(n.type == "WIREFRAME" for n in nt.nodes):
    src = bsdf.inputs["Base Color"].links[0].from_socket if bsdf.inputs["Base Color"].is_linked else None
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.0
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = 0.85                     # line opacity
    nt.links.new(wire.outputs["Fac"], k.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MIX"
    nt.links.new(k.outputs[0], mix.inputs["Factor"])
    if src:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = bsdf.inputs["Base Color"].default_value
    mix.inputs[7].default_value = (0.012, 0.012, 0.014, 1)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

# the stage from turntable.py, held still and framed by the row's width (a sphere fit leaves 16:9 half empty)
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
bpy.context.view_layer.update()
xs = [(o.matrix_world @ Vector(c)).x for o in lods for c in o.bound_box]
width = (max(xs) - min(xs)) + 0.10
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(8)
target = Vector(((max(xs) + min(xs)) / 2, 0, 0.085))
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
# the placards stand nearer the camera than the statues: scale their x so each sits under its statue in frame
fwd = (target - cam.location).normalized()
for t in [o for o in bpy.data.objects if o.name.startswith("Label_")]:
    i = int("".join(ch for ch in t.name if ch.isdigit()))
    x = lods[i].location.x
    t.location.x = cam.location.x + (x - cam.location.x) * (t.location - cam.location).dot(fwd) / (
        (Vector((x, 0, target.z)) - cam.location).dot(fwd))
bd_ob = bpy.data.objects.get("LD_Backdrop")
bd = bd_ob.active_material if bd_ob else None      # by object: each turntable.py run makes a new material
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.012, 0.012, 0.013, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.15   # at this grazing angle the floor is mostly gloss
sc.view_settings.exposure = -0.6
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 3),
                               "frame_width_m": round(width, 3)}))
