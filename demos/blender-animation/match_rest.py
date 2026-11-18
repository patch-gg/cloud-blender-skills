"""Match the target's rest pose to the source's (the skill: "rest poses must match: pose the target's rest
like the source's first"). Each listed limb bone is turned so it points the way its source bone points at
rest (parents first, about its head), the skinned meshes take that pose, and it becomes the rest pose.
Run in the session: cloud.py run match_rest.py -- --source Mocap --target GAME_RIG_Body --map map.json
    --bones upper_arm.L upper_arm.R forearm.L forearm.R ...      (map.json = retarget.py --show-map's map)
"""
import json
import math
import sys

import bpy
from mathutils import Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag):
    return argv[argv.index(flag) + 1]


src, tgt = bpy.data.objects[arg("--source")], bpy.data.objects[arg("--target")]
with open(bpy.path.abspath(arg("--map")), encoding="utf-8") as f:
    bmap = json.load(f)
i = argv.index("--bones") + 1
names = []
while i < len(argv) and not argv[i].startswith("--"):
    names.append(argv[i])
    i += 1
names.sort(key=lambda n: len(tgt.data.bones[n].parent_recursive))  # parents first
for pb in tgt.pose.bones:
    pb.matrix_basis = Matrix()
vl = bpy.context.view_layer
turned = {}
for n in names:
    sb = src.data.bones[bmap[n]]
    want = (src.matrix_world.to_3x3() @ sb.matrix_local.to_3x3()).col[1].normalized()
    vl.update()
    pb = tgt.pose.bones[n]
    M = tgt.matrix_world @ pb.matrix
    have = M.to_3x3().col[1].normalized()
    q = have.rotation_difference(want)
    h = M.translation.copy()
    pb.matrix = tgt.matrix_world.inverted() @ (Matrix.Translation(h) @ q.to_matrix().to_4x4()
                                              @ Matrix.Translation(-h) @ M)
    turned[n] = round(math.degrees(q.angle), 1)
vl.update()
meshes = [o for o in bpy.data.objects if o.type == "MESH" and any(
    m.type == "ARMATURE" and m.object == tgt for m in o.modifiers)]
for ob in meshes:  # the meshes keep the new pose as their shape
    m = next(m for m in ob.modifiers if m.type == "ARMATURE" and m.object == tgt)
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=m.name)
for o in vl.objects:
    o.select_set(False)
vl.objects.active = tgt
tgt.select_set(True)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.armature_apply(selected=False)                 # ... and the armature takes it as its rest
bpy.ops.object.mode_set(mode="OBJECT")
for ob in meshes:
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = tgt
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
print("@@JSON@@" + json.dumps({"ok": True, "target": tgt.name, "turned_deg": turned,
                               "meshes": [o.name for o in meshes]}))
