"""The fix blender-asset-qa gives for a z-fighting error: delete the hidden one of each pair of parallel, same-facing,
overlapping triangles closer than --eps (1 mm, qa_check's default). At low ratios Decimate can fold two nearby
layers into such pairs (on this statue: the porcelain ground and the wooden base, under the base's rim).
Run in the session: cloud.py run fix_lod.py -- SM_Horse_LOD3 [more objects] [--eps 0.001]"""
import json
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_point_tri

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
eps = float(args[args.index("--eps") + 1]) if "--eps" in args else 0.001
names = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--eps")]
out = {}
for name in names:
    ob = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.faces.index_update()
    bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm)
    hidden = set()
    for f in bm.faces:
        if f.calc_area() < 1e-12 or f.index in hidden:
            continue
        n, c = f.normal, f.calc_center_median()
        fv = set(f.verts)
        for p in [c] + [c.lerp(v.co, 0.6) for v in f.verts]:
            for _, _, j, _ in bvh.find_nearest_range(p, eps):
                g = bm.faces[j] if j is not None else None
                if g is None or g is f or g.index in hidden or fv & set(g.verts) or n.dot(g.normal) < 0.999:
                    continue
                a, b, cc = (v.co for v in g.verts)
                if intersect_point_tri(p - g.normal * g.normal.dot(p - a), a, b, cc) is None:
                    continue
                # the one further back along the shared normal is the hidden duplicate
                hidden.add(f.index if n.dot(g.calc_center_median() - c) > 0 else g.index)
                break
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in hidden], context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    out[name] = {"removed_tris": len(hidden), "tris": len(ob.data.polygons)}
print("@@JSON@@" + json.dumps({"ok": True, "eps": eps, "fixed": out}))
