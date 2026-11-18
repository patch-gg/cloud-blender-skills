"""Presentation: the build as a stop-motion. Every part appears on the frame of the step that made it
(ob["build_step"]), in clay until the paint step, then a wire pass for the verify step, then the finished
rocket with the QA result. One small placard under the rocket names each beat. The camera rig from
turntable.py turns slowly and settles on a three-quarter view. 1280x720, 120 frames.

Run in the session after turntable.py: cloud.py run present.py -- --env "blender 5.2.0" --final "qa pass"
"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector

a = argparse.ArgumentParser()
a.add_argument("--env", default="blender")
a.add_argument("--final", default="qa pass")
o = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

FRAMES = 120
# beat: (first frame, label); parts of build step k appear at BEATS[k][0]
BEATS = [(1, o.env), (11, "1 · body"), (25, "2 · nose"), (39, "3 · fins"), (53, "4 · window"),
         (67, "5 · paint"), (81, "verify"), (95, o.final)]
PAINT, VERIFY, DONE = BEATS[5][0], BEATS[6][0], BEATS[7][0]

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
parts = [ob for ob in bpy.data.objects if "build_step" in ob]
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera
# the rig turns about the rocket's axis, not its bbox centre (the three fins push that 10 cm off)
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
pivot.location.x = pivot.location.y = 0.0
bpy.context.view_layer.update()


def key_visible(ob, start, end=None):
    """Hidden before `start` (and from `end` on): constant keys on hide_render/hide_viewport."""
    for f, hide in ((1, start > 1), (start, False)) + (((end, True),) if end else ()):
        ob.hide_render = ob.hide_viewport = hide
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)


# --- stop-motion: each part pops in on its step's frame ----------------------------------------
for ob in parts:
    key_visible(ob, BEATS[int(ob["build_step"])][0])

# --- clay until the paint step: mix clay -> the real material, keyed on one frame ---------------
for m in {s.material for ob in parts for s in ob.material_slots if s.material}:
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    clay = nt.nodes.new("ShaderNodeBsdfPrincipled")
    clay.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
    clay.inputs["Roughness"].default_value = 0.55
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(clay.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    fac = mix.inputs[0]
    for f, v in ((1, 0.0), (PAINT - 1, 0.0), (PAINT, 1.0)):
        fac.default_value = v
        fac.keyframe_insert("default_value", frame=f)

# --- verify: a dark wire pass over the painted rocket, for one beat ------------------------------
wm = bpy.data.materials.get("FX_Wire") or bpy.data.materials.new("FX_Wire")
wb = next(n for n in wm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
wb.inputs["Base Color"].default_value = (0.012, 0.012, 0.012, 1)
wb.inputs["Roughness"].default_value = 0.6
fx = bpy.data.collections.get("FX") or bpy.data.collections.new("FX")
if fx.name not in sc.collection.children:
    sc.collection.children.link(fx)
for ob in parts:
    w = bpy.data.objects.new("FX_Wire_" + ob.name, ob.data)
    w.matrix_world = ob.matrix_world.copy()
    fx.objects.link(w)
    for md in ob.modifiers:                      # keep the fins' bevel, then wire it
        nm = w.modifiers.new(md.name, md.type)
        for k in ("width", "segments", "limit_method"):
            if hasattr(md, k):
                setattr(nm, k, getattr(md, k))
    wire = w.modifiers.new("Wire", "WIREFRAME")
    wire.thickness, wire.use_replace, wire.use_even_offset = 0.0022, True, True
    wire.material_offset = 0
    w.material_slots[0].link = "OBJECT" if w.material_slots else "DATA"
    if w.material_slots:
        w.material_slots[0].material = wm
    key_visible(w, VERIFY, DONE)

# --- camera: frame the rocket's height with room for the placard, lower and closer ---------------
zs = [(ob.matrix_world @ Vector(c)).z for ob in parts for c in ob.bound_box]
lo_z, hi_z = min(zs), max(zs)
target = Vector((pivot.location.x, pivot.location.y, (hi_z + lo_z) / 2 - 0.05))
cam.data.lens = 50
cam.data.dof.use_dof = False
vfov = 2 * math.atan(math.tan(math.atan(cam.data.sensor_width / 2 / cam.data.lens)) / (1280 / 720))
dist = ((hi_z - lo_z) * 1.30) / 2 / math.tan(vfov / 2)
el = math.radians(9)
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, 70), (FRAMES, -28)):          # a slow turn: window to camera at step 4, settles 3/4
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

# --- one placard on the floor in front of the rocket, riding with the camera rig ------------------
lm = bpy.data.materials.get("FX_Label") or bpy.data.materials.new("FX_Label")
lb = next(n for n in lm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
lb.inputs["Base Color"].default_value = (0.0056, 0.0056, 0.0056, 1)  # #111
lb.inputs["Roughness"].default_value = 0.6
inv = Matrix.Translation(pivot.location).inverted()
for i, (start, text) in enumerate(BEATS):
    cu = bpy.data.curves.new(f"FX_Label_{i}", "FONT")
    cu.body, cu.size, cu.align_x = text, 0.072, "CENTER"
    cu.materials.append(lm)
    t = bpy.data.objects.new(f"FX_Label_{i}", cu)
    t.location = (pivot.location.x, pivot.location.y - 0.62, 0.012)
    t.rotation_euler = (math.pi / 2, 0, 0)
    t.visible_shadow = False                     # the rim light behind it would mirror it on the floor
    fx.objects.link(t)
    t.parent = pivot
    t.matrix_parent_inverse = inv
    end = BEATS[i + 1][0] if i + 1 < len(BEATS) else None
    key_visible(t, start, end)

# --- look: a light neutral stage ------------------------------------------------------------------
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.1, 0.1, 0.105, 1)
    b.inputs["Roughness"].default_value = 0.75
sc.view_settings.exposure = -0.7
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 3, 8   # smooth soft shadows at 64 samples
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.frame_set(FRAMES)                             # looks show the finished rocket
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "beats": [b[1] for b in BEATS],
                               "parts": len(parts), "distance": round(dist, 2)}))
