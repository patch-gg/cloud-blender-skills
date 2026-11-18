"""Presentation: the node tree's Radius input animates 0 -> full over frames 1-90, so the forest spreads out
from the middle of the island behind the pink ring (the Radius itself), which then fades; the rig turns 30
degrees around the island. Frames the island by its width. 1280x720, frames 1-120.
Run after turntable.py: cloud.py run present.py -- --radius 5.1"""
import argparse
import json
import math
import sys

import bpy
from bpy_extras import anim_utils
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--radius", type=float, default=5.1)
ap.add_argument("--modifier", default="GN_Forest")
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

F = 120
LIGHT_SCALE = 0.45             # turntable's studio rig is sized for about exposure -1 under AgX
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
island = bpy.data.objects["Island"]
mod = island.modifiers[args.modifier]
ins = {i.name: i.identifier for i in mod.node_group.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}


def key(name, frame, value):
    item = getattr(mod.properties.inputs, ins[name])
    item.value = value
    item.keyframe_insert("value", frame=frame)


# ---- the procedural part: animate the tree's own inputs
for f, v in ((1, 0.0), (90, args.radius)):
    key("Radius", f, v)
for f, v in ((1, 0.03), (84, 0.03), (100, 0.0)):
    key("Ring Width", f, v)

# ---- stage: frame the island by its width, a high three-quarter view, the rig turning 30 degrees
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
el = math.radians(30)
target = Vector((0, 0, 0.7))
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * 30
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
pts = [island.matrix_world @ Vector(c) for c in island.bound_box]
pts += [p + Vector((0, 0, 2.0)) for p in pts]                        # room for the grown trees
fit, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), [v for p in pts for v in p])
cam.location = fit + (fit - target).normalized() * (fit - target).length * 0.06
dist = (cam.location - target).length
cam.data.clip_end = dist * 4
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, -15), (121, 15)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
cb = anim_utils.action_get_channelbag_for_slot(pivot.animation_data.action, pivot.animation_data.action_slot)
for fc in (cb.fcurves if cb else []):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
for lt in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LD_")]:
    lt.data.energy *= LIGHT_SCALE

# ---- look
P = lambda nt: next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")  # noqa: E731
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

# ---- what the tree makes at full growth: count the instances
sc.frame_set(F)
dg = bpy.context.evaluated_depsgraph_get()
trees = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == island)
tris = 0
for i in dg.object_instances:
    if i.is_instance and i.parent and i.parent.original == island and i.object.type == "MESH":
        tris += sum(len(p.vertices) - 2 for p in i.object.data.polygons)
sc.frame_set(60)
print("@@JSON@@" + json.dumps({"ok": True, "trees_at_full": trees, "instanced_tris": tris,
                               "distance": round(dist, 2), "radius": args.radius}))
