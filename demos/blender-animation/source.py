"""The animated source: Patch's CC0 anymove woman (mocap-style clips from video), imported beside the target.

Renames her armature `Mocap` (mesh `MocapBody`), makes `--clip` its active action, drops the GLB's collision
shape, and stands her at `--x` (the retarget only reads changes from rest, so where she stands doesn't matter).
Run in the session: cloud.py run source.py -- assets/woman.glb --clip Walk --x -1.3
"""
import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
glb = argv[0]
clip = argv[argv.index("--clip") + 1] if "--clip" in argv else "Walk"
x = float(argv[argv.index("--x") + 1]) if "--x" in argv else -1.3

before = set(bpy.data.objects)
acts_before = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=bpy.path.abspath(glb))
new = [o for o in bpy.data.objects if o not in before]
arm = next(o for o in new if o.type == "ARMATURE")
for o in new:
    if o.type == "MESH" and not (o.parent and o.parent.type == "ARMATURE"):
        bpy.data.objects.remove(o, do_unlink=True)          # the GLB's collision shape
root = arm
while root.parent:
    root = root.parent
root.location.x += x
arm.name = "Mocap"
body = next(o for o in new if o.name in bpy.data.objects and o.type == "MESH")
body.name = "MocapBody"
act = bpy.data.actions[clip]
arm.animation_data.action = act
if arm.animation_data.action_slot is None:
    arm.animation_data.action_slot = next(iter(arm.animation_data.action_suitable_slots), None)
for a in set(bpy.data.actions) - acts_before:
    a.use_fake_user = a == act                              # keep the clip we use, let the rest go on save
bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": True, "armature": arm.name, "mesh": body.name, "clip": act.name,
                               "frames": [round(v, 2) for v in act.frame_range],
                               "clips_in_file": sorted(a.name for a in set(bpy.data.actions) - acts_before),
                               "height_m": round(body.dimensions.z, 3), "bones": len(arm.data.bones)}))
