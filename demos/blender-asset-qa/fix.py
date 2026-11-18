"""blender-asset-qa's fixes, one per qa_check finding (the table in SKILL.md), in the live session:
  --delete OBJ          z-fighting with a hidden duplicate: delete the duplicate
  --snap OBJ X Y Z      floating part (the island centred there): slide it toward the body's axis until it
                        touches again (within 1 mm), measured against a BVH of everything else
  --recalc OBJ          closed parts with normals pointing in: turn those parts outside out
  --fill-slots OBJ      faces on an empty slot: back onto the object's material, empty slots removed

Run in the session: cloud.py run fix.py -- --delete Barrel_Lid.001 --snap Barrel_Body 0 0 0.6 ...
"""
import argparse
import json
import sys
from collections import defaultdict

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = argparse.ArgumentParser()
a.add_argument("--delete", nargs="*", default=[])
a.add_argument("--snap", nargs=4, action="append", default=[], metavar=("OBJ", "X", "Y", "Z"))
a.add_argument("--recalc", nargs="*", default=[])
a.add_argument("--fill-slots", nargs="*", default=[])
o = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
done = []


def islands(bm):
    bm.verts.ensure_lookup_table()
    parent = list(range(len(bm.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        x, y = find(e.verts[0].index), find(e.verts[1].index)
        if x != y:
            parent[x] = y
    out = defaultdict(list)
    for v in bm.verts:
        out[find(v.index)].append(v)
    return list(out.values())


for name in o.delete:                                   # z-fighting: the hidden duplicate goes
    ob = bpy.data.objects[name]
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)
    done.append(f"deleted {name}")

for name, *xyz in o.snap:                               # floating: slide in until it touches
    ob = bpy.data.objects[name]
    mw = ob.matrix_world
    target = mw.inverted() @ Vector(map(float, xyz))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    isl = islands(bm)
    part = min(isl, key=lambda vs: ((sum((v.co for v in vs), Vector()) / len(vs)) - target).length)
    inpart = set(part)
    rest = [f for f in bm.faces if f.verts[0] not in inpart]
    others = [[mw @ v.co for v in f.verts] for f in rest]
    tris = []
    verts = []
    for poly in others:                                 # this object's other faces ...
        base = len(verts)
        verts += poly
        tris += [(base, base + i, base + i + 1) for i in range(1, len(poly) - 1)]
    for other in [x for x in ob.users_collection[0].objects if x != ob and x.type == "MESH"]:
        m2 = other.matrix_world                         # ... and the asset's other objects
        for p in other.data.polygons:
            base = len(verts)
            verts += [m2 @ other.data.vertices[i].co for i in p.vertices]
            tris += [(base, base + i, base + i + 1) for i in range(1, len(p.vertices) - 1)]
    bvh = BVHTree.FromPolygons(verts, tris)
    home = [v.co.copy() for v in part]
    c = sum(home, Vector()) / len(home)
    step = -Vector((c.x, c.y, 0)).normalized() * 0.0005   # toward the body's axis, half a millimetre at a time

    def gap(k):
        for v, h in zip(part, home):
            v.co = h + step * k
        return min(bvh.find_nearest(mw @ v.co)[3] for v in part)
    k = 0
    while gap(k) > 0.001 and k < 400:                  # until it touches again (qa_check's tol is 2 mm)
        k += 1
    final_gap = gap(k)
    bm.to_mesh(ob.data)
    bm.free()
    done.append(f"slid {len(part)}-vert part of {name} {k * 0.5:.1f} mm in (gap now {final_gap * 1000:.2f} mm)")

for name in o.recalc:                                   # inside-out closed parts: outside out
    ob = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = 0
    for vs in islands(bm):
        s = set(vs)
        faces = {f for v in vs for f in v.link_faces}
        if any(len(e.link_faces) != 2 for v in vs for e in v.link_edges):
            continue                                    # open parts have no inside to point at
        ref = vs[0].co
        vol = 0.0
        for f in faces:
            co = [v.co - ref for v in f.verts]
            for i in range(1, len(co) - 1):
                vol += co[0].dot(co[i].cross(co[i + 1])) / 6
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=list(faces))
            n += 1
    bm.to_mesh(ob.data)
    bm.free()
    done.append(f"turned {n} inside-out part(s) of {name} outside out")

for name in o.fill_slots:                               # faces on an empty slot: back on the material
    ob = bpy.data.objects[name]
    me = ob.data
    keep = next(i for i, m in enumerate(me.materials) if m)
    empty = [i for i, m in enumerate(me.materials) if m is None]
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", idx)
    moved = sum(1 for i in idx if i in empty)
    me.polygons.foreach_set("material_index", [keep if i in empty else i for i in idx])
    for i in reversed(empty):
        me.materials.pop(index=i)
    done.append(f"moved {moved} faces of {name} onto {me.materials[keep].name}, removed {len(empty)} empty slot(s)")

bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": True, "fixed": done}))
