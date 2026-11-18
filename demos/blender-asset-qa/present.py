"""Presentation: the broken barrel with what qa_check caught highlighted in pink (a see-through overlay on the
faces, a small label beside the barrel and a thin leader line to it), then a cut to the fixed barrel and the
clean pass. The camera rig from turntable.py swings slowly the whole time. 1280x720, 120 frames.

Run in the session after snapshot.py, fix.py and turntable.py:
  cloud.py run present.py -- --caught zfighting floating flipped empty_slot --final "qa pass · 0 errors"
"""
import argparse
import json
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

a = argparse.ArgumentParser()
a.add_argument("--caught", nargs="*", default=[])
a.add_argument("--final", default="qa pass")
o = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

FRAMES, CUT = 120, 61
PINK = (0.913, 0.045, 0.638)                      # #F53CD1, linear
DARK = (0.0056, 0.0056, 0.0056)                   # #111
# qa_problem tag -> (finding, label, where the label sits: side (-1 left, 1 right, 0 above), height)
PROBLEMS = {1: ("zfighting", "z-fighting", 0, 0.97), 2: ("floating", "floating", -1, 0.64),
            3: ("flipped", "flipped normals", -1, 0.22), 4: ("empty_slot", "empty slot", 1, 0.46)}

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
before = list(bpy.data.collections["QA_Before"].objects)
after = list(bpy.data.collections["Barrel"].objects)
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera
fx = bpy.data.collections.get("FX") or bpy.data.collections.new("FX")
if fx.name not in sc.collection.children:
    sc.collection.children.link(fx)


def key_visible(ob, start, end=None):
    for f, hide in ((1, start > 1), (start, False)) + (((end, True),) if end else ()):
        ob.hide_render = ob.hide_viewport = hide
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)


def emit_mat(name, color, strength, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1) if strength == 0 else (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Alpha"].default_value = alpha
    if alpha < 1:
        m.surface_render_method = "BLENDED"
    return m


M_FILL = emit_mat("FX_PinkFill", PINK, 1.3, alpha=0.5)
M_PINK = emit_mat("FX_Pink", PINK, 1.5)
M_DARK = emit_mat("FX_Dark", DARK, 0)


def text(name, body, size, loc, m, track=True):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = body, size, "CENTER", "CENTER"
    cu.materials.append(m)
    t = bpy.data.objects.new(name, cu)
    t.location = loc
    t.visible_shadow = False
    fx.objects.link(t)
    if track:                                     # always faces the camera, upright
        c = t.constraints.new("TRACK_TO")
        c.target, c.track_axis, c.up_axis = cam, "TRACK_Z", "UP_Y"
    return t


def line(name, p, q, m, r=0.0025):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=(q - p).length)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = Matrix.Translation((p + q) / 2) @ (q - p).to_track_quat("Z", "Y").to_matrix().to_4x4()
    ob.visible_shadow = False
    fx.objects.link(ob)
    return ob


# --- the two states: broken copies for the first half, the fixed asset after the cut ---------------
for ob in before:
    key_visible(ob, 1, CUT)
for ob in after:
    key_visible(ob, CUT)

# --- what QA caught, in pink -------------------------------------------------------------------------
axis = sum((ob.matrix_world.translation for ob in after), Vector()) / len(after)
shown = []
for k, (finding, label, side, z_label) in PROBLEMS.items():
    if finding not in o.caught:
        continue
    bm = bmesh.new()
    for ob in before:
        me = ob.data
        if "qa_problem" not in me.attributes:
            continue
        tags = [0] * len(me.polygons)
        me.attributes["qa_problem"].data.foreach_get("value", tags)
        if k not in tags:
            continue
        part = bmesh.new()
        part.from_mesh(me)
        lay = part.faces.layers.int["qa_problem"]
        bmesh.ops.delete(part, geom=[f for f in part.faces if f[lay] != k], context="FACES")
        part.transform(ob.matrix_world)
        tmp = bpy.data.meshes.new("tmp")
        part.to_mesh(tmp)
        part.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    if not bm.verts:
        bm.free()
        continue
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])   # outward, even on the inside-out part
    bm.normal_update()
    for v in bm.verts:                            # just off the surface, so it never fights it
        v.co += v.normal * 0.003
    cen = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    me = bpy.data.meshes.new(f"FX_Hi_{finding}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M_FILL)
    hi = bpy.data.objects.new(f"FX_Hi_{finding}", me)
    hi.visible_shadow = False
    fx.objects.link(hi)
    key_visible(hi, 1, CUT)
    # label beside the barrel (or above it), with a leader line to the nearest highlighted point
    # in front of the barrel, so the leader line runs outside it, not through it
    lpos = (Vector((axis.x + side * 0.5, axis.y - 0.55, z_label)) if side
            else Vector((axis.x + 0.3, axis.y - 0.1, z_label)))
    near = min((v.co for v in me.vertices), key=lambda c: (c - lpos).length)
    t = text(f"FX_Label_{finding}", label, 0.058, lpos, M_PINK)
    t.data.align_x = {-1: "RIGHT", 1: "LEFT", 0: "CENTER"}[side]   # side labels run outward from the barrel
    key_visible(t, 1, CUT)
    start = lpos + (near - lpos).normalized() * 0.08          # a little gap after the word
    ln = line(f"FX_Line_{finding}", start, near, M_PINK)
    key_visible(ln, 1, CUT)
    shown.append(finding)

# --- camera: frame the barrel and its labels, a slow swing -------------------------------------------
lo = Vector(min((ob.matrix_world @ Vector(c))[i] for ob in after for c in ob.bound_box) for i in range(3))
hi_ = Vector(max((ob.matrix_world @ Vector(c))[i] for ob in after for c in ob.bound_box) for i in range(3))
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
pivot.location.x, pivot.location.y = axis.x, axis.y   # x/y only: z would lift the backdrop
bpy.context.view_layer.update()
cam.data.lens = 50
cam.data.dof.use_dof = False
vfov = 2 * math.atan(math.tan(math.atan(cam.data.sensor_width / 2 / cam.data.lens)) / (1280 / 720))
dist = 1.5 / 2 / math.tan(vfov / 2)                # about 1.5 m of height in frame: barrel, labels, placard
el = math.radians(22)
target = Vector((axis.x, axis.y, 0.42))
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, -14), (FRAMES, 14)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

# --- the result, after the cut: a placard on the floor that rides with the rig -----------------------
res = text("FX_Result", o.final, 0.06, (axis.x, axis.y - 0.5, 0.012), M_DARK, track=False)
res.rotation_euler = (math.pi / 2, 0, 0)
res.data.align_y = "BOTTOM"
res.parent = pivot
res.matrix_parent_inverse = pivot.matrix_world.inverted()
key_visible(res, CUT)

bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.1, 0.1, 0.105, 1)
    b.inputs["Roughness"].default_value = 0.75
sc.view_settings.view_transform = "Khronos PBR Neutral"   # keeps #F53CD1 pink; AgX turns it pastel
sc.view_settings.look = "None"
sc.view_settings.exposure = -1.0
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 3, 8
sc.frame_set(30)                                  # looks show the broken state
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "cut": CUT, "highlighted": shown,
                               "distance": round(dist, 2)}))
