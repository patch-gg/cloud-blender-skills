"""Presentation: a before/after wipe. The finished prop (collection Prop) and its blockout copy (collection
Blockout) sit in the same place, each in its own view layer, so each renders clean with its own shadows.
The compositor mixes the two by an animated screen position, and a thin line in front of the camera marks
it: left of the line the production stack, right of it the blockout. The line sweeps across and back in
120 frames, a seamless loop, while the rig drifts +-5 degrees so the bevels catch the light.
Run after turntable.py: cloud.py run present.py -- --blockout-tris N --final-tris N"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--blockout-tris", type=int, default=0)
ap.add_argument("--final-tris", type=int, default=0)
ap.add_argument("--az", type=float, default=-30.0)
ap.add_argument("--el", type=float, default=14.0)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

F = 120
LO, HI = 0.07, 0.93            # where the line turns, as a fraction of the frame width
KEYS = ((1, LO), (61, HI), (121, LO))
LIGHT_SCALE = 0.4              # turntable's studio rig is sized for about exposure -1 under AgX
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
prop, blockout = bpy.data.collections["Prop"], bpy.data.collections["Blockout"]
parts = [o for o in prop.objects if o.type == "MESH"]

# ---- stage: turn the whole rig to a three-quarter view, frame the prop by its projected width
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
az, el = math.radians(args.az), math.radians(args.el)
pivot.rotation_euler = (0, 0, az)
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
center = pivot.location.copy()
look = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
cam.location = center + look * 3.0
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
fit, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), [v for p in pts for v in p])
cam.location = fit + (fit - center) * 0.24          # room around the prop and for the labels
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, -5), (61, 5), (121, -5)):
    pivot.rotation_euler = (0, 0, az + math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
for lt in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lt.data.energy *= LIGHT_SCALE

# ---- two view layers: the finished prop, and the blockout
vl_after = sc.view_layers[0]
vl_after.name = "after"
vl_before = sc.view_layers.get("blockout") or sc.view_layers.new("blockout")
blockout.hide_render = False
for vl, hide in ((vl_after, "Blockout"), (vl_before, "Prop")):
    for lc in vl.layer_collection.children:
        lc.exclude = lc.name in (hide, "Cutters")
        lc.hide_viewport = False

# ---- the line and the labels, in front of the camera (no shadows, not in reflections)
tan_h = cam.data.sensor_width / 2 / cam.data.lens          # sensor fit AUTO, landscape: horizontal
tan_v = tan_h * sc.render.resolution_y / sc.render.resolution_x
D = 1.0


def on_cam(ob, coll):
    coll.objects.link(ob)
    ob.parent = cam
    ob.matrix_parent_inverse.identity()
    for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
              "visible_volume_scatter"):
        setattr(ob, k, False)


def flat(name, color):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Specular IOR Level"].default_value = 0.0
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = 1.0
    return m


line_me = bpy.data.meshes.new("WipeLine")
w = 2.0 / sc.render.resolution_x * 2 * tan_h * D          # 2 px
y0, y1 = (0.1 - 0.5) * 2 * tan_v * D, tan_v * D * 1.02     # from just above the labels to the top
line_me.from_pydata([(-w / 2, y0, 0), (w / 2, y0, 0), (w / 2, y1, 0), (-w / 2, y1, 0)], [], [(0, 1, 2, 3)])
line_me.materials.append(flat("M_WipeLine", (2.2, 2.2, 2.2)))
line = bpy.data.objects.new("WipeLine", line_me)
on_cam(line, sc.collection)                                 # in both layers
for f, v in KEYS:
    line.location = ((v - 0.5) * 2 * tan_h * D, 0, -D)
    line.keyframe_insert("location", index=0, frame=f)

cap = 0.024 * 2 * tan_v * D                                 # cap height: 2.4% of the frame height
for coll, text, sx, align in ((prop, "midpoly stack · {:,} tris".format(args.final_tris), 0.035, "LEFT"),
                              (blockout, "blockout · {:,} tris".format(args.blockout_tris), 0.965, "RIGHT")):
    cu = bpy.data.curves.new("Label_" + coll.name, "FONT")
    cu.body, cu.size, cu.align_x = text, cap / 0.72, align
    cu.materials.append(flat("M_Label", (2.2, 2.2, 2.2)) if not bpy.data.materials.get("M_Label")
                        else bpy.data.materials["M_Label"])
    t = bpy.data.objects.new("Label_" + coll.name, cu)
    on_cam(t, sc.collection)                                # in both layers: a legend for the two sides
    t.location = ((sx - 0.5) * 2 * tan_h * D, (0.05 - 0.5) * 2 * tan_v * D, -D)

# ---- compositor: after where x < line, blockout elsewhere
ng = bpy.data.node_groups.new("Wipe", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
N = ng.nodes.new
rl_a, rl_b = N("CompositorNodeRLayers"), N("CompositorNodeRLayers")
rl_a.scene = rl_b.scene = sc
rl_a.layer, rl_b.layer = "after", "blockout"
co, sep, cmp, val = N("CompositorNodeImageCoordinates"), N("ShaderNodeSeparateXYZ"), N("ShaderNodeMath"), \
    N("ShaderNodeValue")
cmp.operation = "LESS_THAN"
mix = N("ShaderNodeMix")
mix.data_type = "RGBA"
out = N("NodeGroupOutput")
L = ng.links.new
L(rl_a.outputs["Image"], co.inputs["Image"])
L(co.outputs["Normalized"], sep.inputs["Vector"])
L(sep.outputs["X"], cmp.inputs[0])
L(val.outputs[0], cmp.inputs[1])
pick = lambda socks, name: next(s for s in socks if s.name == name and s.enabled)  # noqa: E731
L(cmp.outputs[0], pick(mix.inputs, "Factor"))
L(rl_b.outputs["Image"], pick(mix.inputs, "A"))
L(rl_a.outputs["Image"], pick(mix.inputs, "B"))
L(pick(mix.outputs, "Result"), out.inputs[0])
for f, v in KEYS:
    val.outputs[0].default_value = v
    val.outputs[0].keyframe_insert("default_value", frame=f)
sc.compositing_node_group = ng
sc.render.use_compositing = True

# ---- look
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.03, 0.03, 0.033, 1)
    b.inputs["Roughness"].default_value = 0.6
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.view_settings.exposure = -1.8
sc.frame_set(31)
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "layers": [v.name for v in sc.view_layers],
                               "distance": round((cam.matrix_world.translation - center).length, 2),
                               "wipe": [LO, HI], "frames": F}))
