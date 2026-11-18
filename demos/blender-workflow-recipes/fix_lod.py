"""Fix what the QA gate caught on an LOD: delete the loose part(s) that qa_check.py reported as floating
(blender-asset-qa: "floating ... delete floating debris"). The parts are picked by the location QA printed.
Before deleting, keeps two hidden copies for the clip: the LOD as QA saw it (QA_<lod>) and the flagged part
alone (QA_<lod>_caught). Run in the session: cloud.py run fix_lod.py -- SM_JerryCan_LOD3 -0.088 0 0.491"""
import json
import sys

import bmesh
import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
name, at, radius = a[0], Vector(map(float, a[1:4])), 0.01   # qa_check reports a part by its bbox centre
ob = bpy.data.objects[name]
bm = bmesh.new()
bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table()
seen, islands = set(), []
for v in bm.verts:                                   # connected parts
    if v.index in seen:
        continue
    stack, part = [v], []
    seen.add(v.index)
    while stack:
        cur = stack.pop()
        part.append(cur)
        for e in cur.link_edges:
            o = e.other_vert(cur)
            if o.index not in seen:
                seen.add(o.index)
                stack.append(o)
    islands.append(part)
mw = ob.matrix_world


def bbox_centre(part):
    pts = [mw @ v.co for v in part]
    return Vector([(min(q[i] for q in pts) + max(q[i] for q in pts)) / 2 for i in range(3)])


flagged = [p for p in islands if len(p) < len(bm.verts) / 2 and (bbox_centre(p) - at).length < radius]
flag_idx = {v.index for p in flagged for v in p}

coll = bpy.data.collections.get("Stages") or bpy.data.collections.new("Stages")
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)
for suffix, keep in (("", None), ("_caught", flag_idx)):   # the LOD as QA saw it, and the flagged part
    nm = f"QA_{name}{suffix}"
    old = bpy.data.objects.get(nm)
    if old:
        bpy.data.objects.remove(old)
    me = ob.data.copy()
    me.name = nm
    if keep is not None:
        b2 = bmesh.new()
        b2.from_mesh(me)
        b2.verts.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[v for v in b2.verts if v.index not in keep], context="VERTS")
        b2.to_mesh(me)
        b2.free()
    c = bpy.data.objects.new(nm, me)
    c.matrix_world = ob.matrix_world.copy()
    coll.objects.link(c)
    c.hide_render = True
    c.hide_set(True)

removed = len(flag_idx)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in flag_idx], context="VERTS")
bm.to_mesh(ob.data)
bm.free()
ob.data.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": bool(flagged), "object": name, "parts_removed": len(flagged),
                               "verts_removed": removed, "tris_after": len(ob.data.loop_triangles)}))
