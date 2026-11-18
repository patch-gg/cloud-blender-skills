"""Run the installed extension's operator in the live session. `blender --command extension install-file`
put Gear Maker in the user_default repo from a separate process, so this Blender enables it by module name,
then calls bpy.ops.gear_maker.add_gear once per gear with different parameters: a meshing train (same module,
centres one pitch radius apart), laid flat on the floor.

Run in the session: cloud.py run make_gears.py
"""
import json
import math
import sys

import addon_utils
import bpy

MOD = "bl_ext.user_default.gear_maker"
M, W = 0.012, 0.03                                  # module (tooth size) and face width, shared by the train
TRAIN = [dict(teeth=12, spokes=0, bore=0.010, metal="BRASS"),   # each gear meshes with the one before it
         dict(teeth=36, spokes=6, bore=0.016, metal="STEEL"),
         dict(teeth=20, spokes=5, bore=0.012, metal="BRASS")]   # 5 spokes: 216 degrees a loop is 3 spoke steps
TURN = [None, 0.0, -32.0]                           # direction from the previous gear's centre, degrees

for ob in list(bpy.data.objects):                   # a fresh session's factory cube, light and camera
    bpy.data.objects.remove(ob, do_unlink=True)
addon_utils.disable(MOD)                            # a reinstall in a live session: drop the old code first
for k in [k for k in sys.modules if k == MOD or k.startswith(MOD + ".")]:
    del sys.modules[k]
mod = addon_utils.enable(MOD, default_set=True)
if mod is None or not hasattr(bpy.ops.gear_maker, "add_gear"):
    raise RuntimeError(f"{MOD} didn't enable")

sc = bpy.context.scene
made, pos = [], (0.0, 0.0)
for i, g in enumerate(TRAIN):
    if i:
        prev = TRAIN[i - 1]
        d = M * (prev["teeth"] + g["teeth"]) / 2    # centre distance of two meshing spur gears
        a = math.radians(TURN[i])
        pos = (pos[0] + d * math.cos(a), pos[1] + d * math.sin(a))
    sc.cursor.location = (pos[0], pos[1], W / 2)    # resting on the floor
    r = bpy.ops.gear_maker.add_gear(module=M, width=W, **g)
    ob = bpy.context.view_layer.objects.active
    ob["gear"] = {**g, "module": M, "width": W}
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    made.append({"object": ob.name, "result": sorted(r), **g, "tris": len(me.loop_triangles),
                 "diameter": round(ob.dimensions.x, 3), "at": [round(v, 3) for v in ob.location]})
    ob.evaluated_get(dg).to_mesh_clear()
print("@@JSON@@" + json.dumps({"ok": True, "extension": MOD, "enabled": MOD in bpy.context.preferences.addons,
                               "gears": made}))
