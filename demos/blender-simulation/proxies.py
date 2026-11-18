"""Collision proxies for the cloth: the crates are detailed meshes (slats, handles, corners) that a 5 cm cloth
grid catches on and sinks through, so each body gets a simple hidden stand-in (its bounding box, a cylinder
for barrels) parented to it, so it follows the baked keys. Pass the proxies to sim_setup.py --colliders.
Run in the session after the rigid-body bake:  cloud.py run proxies.py -- --bodies Crate_00 Barrel_04 ...
"""
import argparse
import json
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser()
ap.add_argument("--bodies", nargs="+", required=True)
ap.add_argument("--pad", type=float, default=0.01, help="m added on every side")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

sc = bpy.context.scene
names = []
for n in a.bodies:
    body = bpy.data.objects[n]
    pts = [Vector(c) for c in body.bound_box]  # local: the body's mesh is centred on its origin
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))) - Vector((a.pad,) * 3)
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))) + Vector((a.pad,) * 3)
    size, centre = hi - lo, (hi + lo) / 2
    bm = bmesh.new()
    if n.startswith("Barrel"):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=size.x / 2, radius2=size.x / 2, depth=size.z)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    old = bpy.data.objects.get("Proxy_" + n)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new("Proxy_" + n)
    bm.to_mesh(me)
    bm.free()
    px = bpy.data.objects.new("Proxy_" + n, me)
    sc.collection.objects.link(px)
    px.parent = body
    px.matrix_parent_inverse = Matrix.Identity(4)
    # unseen by every ray but still in the render depsgraph, so a cloth that re-simulates while rendering
    # still collides with it (hide_render would drop it)
    for vis in ("visible_camera", "visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
                "visible_volume_scatter"):
        setattr(px, vis, False)
    px.display_type = "WIRE"
    names.append(px.name)
print("@@JSON@@" + json.dumps({"ok": True, "proxies": names}))
