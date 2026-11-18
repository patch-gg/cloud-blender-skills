"""Presentation: bring the exported .glb back into the scene as GLB_<name> (collection Export, hidden), so the
clip's export stage and closing turntable show what an engine receives.
Run in the session: cloud.py run import_glb.py -- /work/export/SM_JerryCan.glb"""
import json
import os
import sys

import bpy

path = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
coll = bpy.data.collections.get("Export") or bpy.data.collections.new("Export")
if coll.name not in sc.collection.children:
    sc.collection.children.link(coll)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=path)
new = [o for o in bpy.data.objects if o not in before]
out = []
for ob in new:
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    if ob.type == "MESH":
        base = ob.name.rsplit(".", 1)[0] if ob.name[-4:-3] == "." and ob.name[-3:].isdigit() else ob.name
        old = bpy.data.objects.get(f"GLB_{base}")              # (the import is SM_X.001 next to SM_X)
        if old:
            bpy.data.objects.remove(old)
        ob.name = f"GLB_{base}"
        ob.data.calc_loop_triangles()
        out.append({"object": ob.name, "tris": len(ob.data.loop_triangles),
                    "images": sorted({n.image.name for m in ob.data.materials if m for n in m.node_tree.nodes
                                      if n.type == "TEX_IMAGE" and n.image})})
    ob.hide_render = True
    ob.hide_set(True)
print("@@JSON@@" + json.dumps({"ok": bool(out), "file": os.path.basename(path), "imported": out}))
