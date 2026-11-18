"""Keep a copy of the sculpt as it is now, for the lineup: the evaluated mesh of Moai becomes object
<name> at slot <slot> of <of> along X (the working object sits in the last slot).
Run in the session: cloud.py run snap.py -- --name S1_remesh --slot 1 --of 5"""
import argparse
import json
import sys

import bpy

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--slot", type=int, required=True)
ap.add_argument("--of", type=int, default=5)
ap.add_argument("--spacing", type=float, default=0.84)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

src = bpy.data.objects["Moai"]
x = lambda k: (k - (a.of - 1) / 2) * a.spacing  # noqa: E731
src.location.x = x(a.of - 1)
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
me.name = a.name
ob = bpy.data.objects.new(a.name, me)
coll = bpy.data.collections.get("Stages") or bpy.data.collections.new("Stages")
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)
coll.objects.link(ob)
ob.location = (x(a.slot), 0, 0)
me.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "object": ob.name, "x": round(ob.location.x, 3),
                               "faces": len(me.polygons), "tris": len(me.loop_triangles)}))
