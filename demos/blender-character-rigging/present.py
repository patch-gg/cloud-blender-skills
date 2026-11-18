"""Presentation for the rigging demo (in the session, after turntable.py):

- the stress poses retimed to one every 20 frames and back to rest at 121, so frames 1-120 loop; the crouch
  lowers the root so the feet stay on the floor
- the game skeleton beside the character as octahedral bones, driven by the same control rig (pose-space
  copies), with the bones each pose stresses lit pink
- two small labels, the camera framed on the pair and swinging gently (+-10 degrees, no full turn)
Run in the session: cloud.py run present.py -- [--gap 1.75]
"""
import json
import math
import sys

import bmesh
import bpy
from bpy_extras import anim_utils
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GAP = float(argv[argv.index("--gap") + 1]) if "--gap" in argv else 1.75
PINK = (0.913, 0.045, 0.638, 1.0)          # #F53CD1 in linear
BONE = (0.9, 0.9, 0.88, 1.0)
sc = bpy.context.scene
rig, game, body = bpy.data.objects["RIG_Body"], bpy.data.objects["GAME_RIG_Body"], bpy.data.objects["Body"]
act = bpy.data.actions["QA_Stress"]
END = 121

# ---------------------------------------------------------------- retime the stress poses
POSE = {1: 1, 10: 21, 20: 41, 30: 61, 40: 81, 50: 101}
cb = anim_utils.action_get_channelbag_for_slot(act, rig.animation_data.action_slot)
for fc in cb.fcurves:
    pts = [(POSE.get(round(k.co.x), k.co.x), k.co.y) for k in fc.keyframe_points]
    pts.append((END, fc.evaluate(1)))
    fc.keyframe_points.clear()
    fc.keyframe_points.add(len(pts))
    for kp, (f, v) in zip(fc.keyframe_points, pts):
        kp.co = (f, v)
        kp.interpolation = "BEZIER"
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    fc.update()
sc.frame_start, sc.frame_end = 1, END - 1


def lowest():
    bpy.context.view_layer.update()
    eo = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = eo.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in me.vertices)
    eo.to_mesh_clear()
    return z


root = rig.pose.bones["root"]
sc.frame_set(1)
floor = lowest()
drops = {}
for f in list(POSE.values()) + [END]:   # keep the feet on the floor (the crouch would float otherwise)
    sc.frame_set(f)
    drops[f] = max(0.0, lowest() - floor - 0.005)
for f, dz in drops.items():
    root.matrix_basis = Matrix()
    sc.frame_set(f)
    root.location = root.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, -dz))
    root.keyframe_insert("location", frame=f)
root.matrix_basis = Matrix()

# ---------------------------------------------------------------- the skeleton beside the character
skel = game.copy()
skel.data = game.data.copy()
skel.name = skel.data.name = "Skeleton_Rig"
skel.animation_data_clear()
for c in game.users_collection:
    c.objects.link(skel)
for pb in skel.pose.bones:
    for c in pb.constraints:
        c.mute = False
        c.target_space = c.owner_space = "POSE"   # same pose, wherever the object stands
skel.location.x -= GAP
GROUPS = {"upper_arm": "arms", "forearm": "forearms", "thigh.L": "leg_l", "shin.L": "leg_l", "thigh.R": "leg_r",
          "shin.R": "leg_r", "spine.00": "spine", "spine.004": "neck", "spine.005": "neck", "spine.006": "neck"}


def group_of(name):
    for key in ("spine.004", "spine.005", "spine.006", "thigh.L", "shin.L", "thigh.R", "shin.R", "upper_arm",
                "forearm", "spine.00"):
        if name.startswith(key):
            return GROUPS[key]
    return "rest"


def bone_mesh(bones, name):
    bm = bmesh.new()
    dl = bm.verts.layers.deform.verify()      # before any vert exists (adding a layer frees old refs)
    for b in bones:
        h, t = b.head_local, b.tail_local
        L = (t - h).length
        x, z = b.matrix_local.col[0].to_3d() * 0.13 * L, b.matrix_local.col[2].to_3d() * 0.13 * L
        m = h + (t - h) * 0.12
        vh, vt = bm.verts.new(h), bm.verts.new(t)
        ring = [bm.verts.new(m + d) for d in (x, z, -x, -z)]
        for i in range(4):
            a, c = ring[i], ring[(i + 1) % 4]
            bm.faces.new((vh, c, a))
            bm.faces.new((vt, a, c))
        for v in [vh, vt] + ring:
            v[dl][len(groups_seen)] = 1.0
        groups_seen.append(b.name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


mats, parts = {}, []
for g in ("arms", "forearms", "leg_l", "leg_r", "spine", "neck", "rest"):
    bones = [b for b in skel.data.bones if b.use_deform and group_of(b.name) == g]
    if not bones:
        continue
    groups_seen = []
    me = bone_mesh(bones, f"Bones_{g}")
    ob = bpy.data.objects.new(f"Bones_{g}", me)
    for n in groups_seen:
        ob.vertex_groups.new(name=n)
    ob.parent = skel
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = skel
    mat = bpy.data.materials.new(f"M_Bones_{g}")
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = BONE
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Emission Color"].default_value = PINK
    bsdf.inputs["Emission Strength"].default_value = 0.0
    me.materials.append(mat)
    for c in skel.users_collection:
        c.objects.link(ob)
    mats[g] = bsdf
    parts.append(ob.name)
# the bones each pose bends glow pink while it holds
LIT = {"arms": [21, 41], "forearms": [41], "leg_l": [61, 81], "leg_r": [81], "spine": [101], "neck": [101]}
for g, frames in LIT.items():
    if g not in mats:
        continue
    col, em = mats[g].inputs["Base Color"], mats[g].inputs["Emission Strength"]
    keys = {1: 0.0, END: 0.0}
    for f in frames:
        keys.update({f - 13: keys.get(f - 13, 0.0), f - 5: 1.0, f + 5: 1.0})
        keys.setdefault(f + 13, 0.0)
    for f in sorted(keys):
        on = keys[f]
        col.default_value = [BONE[i] + (PINK[i] - BONE[i]) * on for i in range(4)]
        em.default_value = 0.6 * on
        col.keyframe_insert("default_value", frame=f)
        em.keyframe_insert("default_value", frame=f)

# ---------------------------------------------------------------- labels
def label(text, x):
    cu = bpy.data.curves.new(f"Label_{text}", "FONT")
    cu.body, cu.size, cu.align_x = text, 0.08, "CENTER"
    t = bpy.data.objects.new(f"Label_{text}", cu)
    t.location = (x, -0.62, 0.012)
    t.rotation_euler = (math.radians(90), 0, 0)
    m = bpy.data.materials.new("M_Label")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.85, 0.85, 0.85, 1)
    b.inputs["Roughness"].default_value = 0.6
    cu.materials.append(m)
    sc.collection.objects.link(t)
    return t.name


bones_n = sum(1 for b in game.data.bones)
labels = [label(f"rig · {bones_n} bones", -GAP), label("skin · 4 weights", 0.0)]

# ---------------------------------------------------------------- camera: the pair, by height
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
pivot.location = Vector((-GAP / 2, 0.0, 0.97))
cam = sc.camera
cam.data.lens = 50
cam.data.dof.use_dof = False
vfov = 2 * math.atan(cam.data.sensor_width * 9 / 16 / 2 / cam.data.lens)
dist = 1.36 / math.tan(vfov / 2)
el = math.radians(6)
cam.parent = None
target = pivot.location.copy()
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.1, 100
bpy.context.view_layer.update()
for o in [o for o in bpy.data.objects if o.parent == pivot] + [cam]:
    mw = o.matrix_world.copy()
    o.parent = pivot
    o.matrix_parent_inverse = pivot.matrix_world.inverted()
    o.matrix_world = mw
for f, deg in ((1, 0), (31, 10), (61, 0), (91, -10), (END, 0)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
bd = bpy.data.materials.get("LD_Backdrop")            # a darker stage, so white bones and labels read
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.07, 0.07, 0.075, 1)
for lo in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lo.data.energy *= 0.75
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": [1, END - 1], "poses_at": list(POSE.values()),
                               "crouch_drop_m": round(drops.get(81, 0), 3), "skeleton_parts": parts,
                               "labels": labels, "camera_distance_m": round(dist, 2)}))
