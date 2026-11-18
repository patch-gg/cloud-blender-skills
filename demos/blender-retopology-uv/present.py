"""Presentation: three in a row on the same slow +-35 degree swing - the dense source with its wireframe, the
retopo with its wireframe, and the retopo with a UV checker (checks about 3.5 cm on the model at the measured
texel density); a small label under each. Frames the row by its width. 1280x720, frames 1-120, a loop.
Run after turntable.py: cloud.py run present.py -- --density <px/m> --res 2048 --labels A B C"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--labels", nargs=3, required=True)
ap.add_argument("--density", type=float, required=True)
ap.add_argument("--res", type=int, default=2048)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

F, GAP = 120, 0.86
LIGHT_SCALE = 0.45             # turntable's studio rig is sized for about exposure -1 under AgX
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
src, low = bpy.data.objects["Fox"], bpy.data.objects["Fox_low"]
src.hide_set(False)
src.hide_render = False
uv = low.copy()
uv.data = low.data.copy()
uv.name = uv.data.name = "Fox_uv"
sc.collection.objects.link(uv)
row = [src, low, uv]
for i, o in enumerate(row):
    o.location = ((i - 1) * GAP, 0, 0)
low.data.shade_smooth()
uv.data.shade_smooth()

clay = bpy.data.materials["M_Clay"]
P = lambda nt: next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")  # noqa: E731
pick = lambda socks, name: next(s for s in socks if s.name == name and s.enabled)  # noqa: E731


def new_mat(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    P(m.node_tree).inputs["Base Color"].default_value = (*color, 1)
    P(m.node_tree).inputs["Roughness"].default_value = rough
    return m


# dense source: its own triangles, drawn by the shader (no extra geometry for 441k tris)
dense = clay.copy()
dense.name = "M_DenseWire"
nt = dense.node_tree
w = nt.nodes.new("ShaderNodeWireframe")
w.use_pixel_size = True
w.inputs["Size"].default_value = 0.6
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
pick(mix.inputs, "A").default_value = P(nt).inputs["Base Color"].default_value[:]
pick(mix.inputs, "B").default_value = (0.07, 0.07, 0.07, 1)
nt.links.new(w.outputs[0], pick(mix.inputs, "Factor"))
nt.links.new(pick(mix.outputs, "Result"), P(nt).inputs["Base Color"])
src.data.materials.clear()
src.data.materials.append(dense)

# retopo: real quad edges, as thin geometry over the clay
low.data.materials.clear()
low.data.materials.append(clay)
low.data.materials.append(new_mat("M_Wire", (0.02, 0.02, 0.02)))
wm = low.modifiers.new("Wire", "WIREFRAME")
wm.thickness, wm.use_replace, wm.use_even_offset, wm.material_offset = 0.0028, False, True, 1

# UV checker on the retopo's UV map
chk = bpy.data.materials.new("M_UVChecker")
nt = chk.node_tree
tc, ck = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexChecker")
ck.inputs["Scale"].default_value = args.res / (0.035 * args.density) / 2     # Blender's checker: 2 checks per 1/Scale
ck.inputs["Color1"].default_value = (0.78, 0.76, 0.72, 1)
ck.inputs["Color2"].default_value = (0.10, 0.10, 0.11, 1)
nt.links.new(tc.outputs["UV"], ck.inputs["Vector"])
nt.links.new(ck.outputs["Color"], P(nt).inputs["Base Color"])
P(nt).inputs["Roughness"].default_value = 0.6
uv.data.materials.clear()
uv.data.materials.append(chk)

# ---- stage: a still rig, the camera framed on the row's width
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
width = 2 * GAP + 0.8 + 0.4
height = max(o.dimensions.z for o in row)
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(8)
target = Vector((0, 0, height * 0.43))
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for lt in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lt.data.energy *= LIGHT_SCALE
FACE = -90          # the model looks down +X; turn it to the camera, then swing around that
for o in row:
    o.animation_data_clear()
    o.rotation_mode = "XYZ"                 # the glTF importer leaves objects in quaternion mode
    for f, deg in ((1, 0), (31, 35), (61, 0), (91, -35), (121, 0)):
        o.rotation_euler = (0, 0, math.radians(FACE + deg))
        o.keyframe_insert("rotation_euler", index=2, frame=f)

# ---- labels: small placards on the floor in front of each
lab = new_mat("M_Label", (0.006, 0.006, 0.006), 0.8)          # #111
for o, text in zip(row, args.labels):
    cu = bpy.data.curves.new("Label_" + o.name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = text, 0.05, "CENTER", "CENTER"
    cu.materials.append(lab)
    t = bpy.data.objects.new("Label_" + o.name, cu)
    t.location = (o.location.x, -0.55, 0.02)
    t.rotation_euler = (math.radians(90 - 8), 0, 0)
    sc.collection.objects.link(t)

# ---- look: a light clay stage
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    P(bd.node_tree).inputs["Base Color"].default_value = (0.36, 0.36, 0.36, 1)
    P(bd.node_tree).inputs["Roughness"].default_value = 0.9
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Base Contrast"
except TypeError:
    pass
sc.view_settings.exposure = -1.6
sc.frame_set(31)
print("@@JSON@@" + json.dumps({"ok": True, "row": [o.name for o in row], "checker_scale": round(ck.inputs["Scale"].default_value, 1),
                               "distance": round(dist, 2)}))
