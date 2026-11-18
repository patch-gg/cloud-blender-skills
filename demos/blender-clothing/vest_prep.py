"""Get the t-shirt ready to carry a vest (it is the vest's "body": layered clothing, garment.py --body Shirt).

1. Smooth the body there (the skill's fix): the shirt is creased under the arms and at its turned-up hem, faces
   meeting at 70+ degrees. Offset outward, a tight crease folds over and the vest's thickness spikes out of it,
   so those verts (and a ring around them) are relaxed first. Open edges (hem, collar, cuffs) stay put.
2. The vest's region: a `Torso` vertex group of the shirt's body panels (front and back), so the vest's
   armholes, neckline and hem follow the shirt's own seams. Panels are UV islands (faces joined across
   edges whose UVs match); the body panels cross the centre line, the sleeves don't.
Run after bind_mesh (its weight cleanup would normalise a group made earlier together with the skin weights).
Run in the session: cloud.py run vest_prep.py -- --mesh Shirt [--group Torso]
"""
import json
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ob = bpy.data.objects[argv[argv.index("--mesh") + 1] if "--mesh" in argv else "Shirt"]
name = argv[argv.index("--group") + 1] if "--group" in argv else "Torso"
bm = bmesh.new()
bm.from_mesh(ob.data)
bm.normal_update()
uv = bm.loops.layers.uv.active


def joined(e):
    """Two faces share this edge with the same UVs at both ends (no UV seam)."""
    if len(e.link_faces) != 2:
        return False
    f1, f2 = e.link_faces
    a = {lp.vert: lp[uv].uv for lp in f1.loops if lp.vert in e.verts}
    b = {lp.vert: lp[uv].uv for lp in f2.loops if lp.vert in e.verts}
    return all((a[v] - b[v]).length < 1e-5 for v in e.verts)


# 1. relax crumples
CREASE = 0.34                                             # faces meeting at more than ~70 degrees


def creased(v):
    return any(f.normal.dot(g.normal) < CREASE for f in v.link_faces for g in v.link_faces)


crumpled = {v for v in bm.verts if creased(v)}
ring = {o for v in crumpled for e in v.link_edges for o in e.verts}
relax = [v for v in crumpled | ring if not v.is_boundary]
for _ in range(8):
    bmesh.ops.smooth_vert(bm, verts=relax, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.normal_update()
left = sum(1 for v in bm.verts if not v.is_boundary and creased(v))
# 2. the body panels
seen, panels = set(), []
for f in bm.faces:
    if f.index in seen:
        continue
    stack, isl = [f], []
    seen.add(f.index)
    while stack:
        x = stack.pop()
        isl.append(x)
        for e in x.edges:
            if joined(e):
                for o in e.link_faces:
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
    panels.append(isl)
mw = ob.matrix_world
body = [p for p in panels if min((mw @ f.calc_center_median()).x for f in p) < 0 <
        max((mw @ f.calc_center_median()).x for f in p)]
keep = sorted({v.index for p in body for f in p for v in f.verts})
bm.to_mesh(ob.data)
bm.free()
ob.data.update()
vg = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
vg.add(keep, 1.0, "REPLACE")
print("@@JSON@@" + json.dumps({"ok": True, "mesh": ob.name, "crumpled_verts": len(crumpled),
                               "relaxed_verts": len(relax), "crumpled_after": left, "group": name,
                               "panels": len(panels), "body_panels": len(body), "region_verts": len(keep),
                               "of": len(ob.data.vertices)}))
