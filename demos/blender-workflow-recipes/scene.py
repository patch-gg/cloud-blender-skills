"""Blockout of a jerry can at real scale (345 x 165 x 470 mm body), from sharp primitives, plus the boolean
cutters the high poly will use. Run in the session: cloud.py run scene.py

Parts (collection Blockout): Body, Flange (the weld seam lip), Handles (three bars), Spout, Cap.
Cutters (collection Cutters, hidden): Cut_XA / Cut_XB (the pressed X on both sides), Cut_Grip (cap grip).
Front is -Y (Blender's front); the spout leans toward +X."""
import json
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

W, D, H = 0.345, 0.165, 0.47          # body length (X), thickness (Y), height (Z), metres
SPOUT_AT, SPOUT_TILT = Vector((0.118, 0.0, H)), math.radians(35)

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
sc = bpy.context.scene
sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 1.0


def collection(name, hide=False):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    return c


def obj(name, bm, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def add_box(bm, size, matrix):
    r = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=matrix @ Matrix.Diagonal((*size, 1.0)), verts=r["verts"])


def sweep(bm, path, half_w, half_t):
    """A rectangular bar (half_w across X, half_t across the path normal) along a YZ-plane path, capped."""
    rings = []
    for i, p in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
        t = (b - a).normalized()
        n = Vector((1, 0, 0)).cross(t).normalized()              # in the YZ plane, perpendicular to t
        if 0 < i < len(path) - 1:                                  # mitre: keep the bar thickness at bends
            t0, t1 = (p - path[i - 1]).normalized(), (path[i + 1] - p).normalized()
            n = n / max(math.cos(t0.angle(t1) / 2), 0.5)
        rings.append([bm.verts.new(p + Vector((sx * half_w, 0, 0)) + n * (sy * half_t))
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def cylinder(bm, radius, length, start, axis, segments=24):
    r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segments,
                              radius1=radius, radius2=radius, depth=length)
    rot = Vector((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(start + axis * (length / 2)) @ rot, verts=r["verts"])


blockout, cutters = collection("Blockout"), collection("Cutters")

# body: a sharp box resting on z = 0
bm = bmesh.new()
add_box(bm, (W, D, H), Matrix.Translation((0, 0, H / 2)))
body = obj("Body", bm, blockout)

# weld-seam flange: a U-shaped lip around the sides and top, 8 mm thick, standing 6 mm proud and sunk
# 2 mm into the body (any deeper is hidden surface that still costs texture space)
bm = bmesh.new()
xo, xi, zt, zi, zb, t = W / 2 + 0.006, W / 2 - 0.002, H + 0.006, H - 0.002, 0.012, 0.004
pts = {"L0": (-xo, zb), "L1": (-xi, zb), "L2": (-xi, zi), "L3": (-xo, zi), "L4": (-xo, zt), "L5": (-xi, zt)}
pts.update({"R" + k[1:]: (-x, z) for k, (x, z) in pts.items()})
quads = [("L0", "L1", "L2", "L3"), ("L3", "L2", "L5", "L4"), ("L2", "R2", "R5", "L5"),
         ("R2", "R3", "R4", "R5"), ("R1", "R0", "R3", "R2")]
front = {k: bm.verts.new((x, -t, z)) for k, (x, z) in pts.items()}
back = {k: bm.verts.new((x, t, z)) for k, (x, z) in pts.items()}
for q in quads:
    bm.faces.new([front[k] for k in q])
    bm.faces.new([back[k] for k in reversed(q)])
ring =["L0", "L3", "L4", "L5", "R5", "R4", "R3", "R0", "R1", "R2", "L2", "L1"]   # boundary loop, in order
for a, b in zip(ring, ring[1:] + ring[:1]):
    bm.faces.new((front[a], back[a], back[b], front[b]))
for side in (front, back):  # seams where the top bar meets the uprights: three straight UV strips, not a U
    for a_, b_ in (("L2", "L5"), ("R2", "R5")):
        bm.edges.get((side[a_], side[b_])).seam = True
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
flange = obj("Flange", bm, blockout)

# three carry handles: flat bars bridging front to back over the seam
bm = bmesh.new()
y0, r, zleg = D / 2 - 0.016, 0.022, H + 0.012          # legs at +-y0, rounded over into a flat top span
arc = [(-y0 + r - r * math.cos(a), zleg + r * math.sin(a)) for a in
       (math.radians(d) for d in (0, 22.5, 45, 67.5, 90))]
half = [(-y0, H - 0.008)] + arc
path = [Vector((0, y, z)) for y, z in half + [(-y, z) for y, z in reversed(half)]]
for x in (-0.088, -0.038, 0.012):
    sweep(bm, [p + Vector((x, 0, 0)) for p in path], 0.011, 0.0055)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
handles = obj("Handles", bm, blockout)

# spout and cap, leaning toward +X
axis = Vector((math.sin(SPOUT_TILT), 0, math.cos(SPOUT_TILT)))
bm = bmesh.new()
cylinder(bm, 0.021, 0.060, SPOUT_AT - axis * 0.014, axis)
spout = obj("Spout", bm, blockout)
cap_start, cap_len, cap_r = SPOUT_AT + axis * 0.040, 0.026, 0.027
bm = bmesh.new()
cylinder(bm, cap_r, cap_len, cap_start, axis)
cap = obj("Cap", bm, blockout)

# cutters: the pressed X on both big faces (two crossing channels, 32 mm wide, 6 mm deep)
span_x, span_z = 0.27, 0.38
ang, length = math.atan2(span_z, span_x), math.hypot(span_x, span_z) + 0.02
for name, sign in (("Cut_XA", 1), ("Cut_XB", -1)):
    bm = bmesh.new()
    for side in (-1, 1):
        m = (Matrix.Translation((0, side * (D / 2 + 0.010 - 0.006), H / 2)) @
             Matrix.Rotation(sign * ang, 4, "Y"))
        add_box(bm, (length, 0.020, 0.032), m)
    obj(name, bm, cutters)
# cutter: 16 grip grooves around the cap (1.5 mm deep, kept off the cap's ends)
bm = bmesh.new()
rot = Vector((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4()
for k in range(16):
    a = 2 * math.pi * k / 16
    local = (Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((cap_r + 0.0015, 0, cap_len / 2)))
    add_box(bm, (0.006, 0.0035, 0.018), Matrix.Translation(cap_start) @ rot @ local)
obj("Cut_Grip", bm, cutters)
for ob in cutters.objects:
    ob.display_type, ob.hide_render = "WIRE", True
    ob.hide_set(True)

parts = [o.name for o in blockout.objects]
dims = {o.name: [round(v, 4) for v in o.dimensions] for o in blockout.objects}
lo = [min((o.matrix_world @ Vector(c))[i] for o in blockout.objects for c in o.bound_box) for i in range(3)]
hi = [max((o.matrix_world @ Vector(c))[i] for o in blockout.objects for c in o.bound_box) for i in range(3)]
print("@@JSON@@" + json.dumps({"ok": True, "parts": parts, "cutters": [o.name for o in cutters.objects],
                               "body_dims_m": dims["Body"], "overall_m": [round(b - a, 4) for a, b in zip(lo, hi)],
                               "tris": sum(len(p.vertices) - 2 for o in blockout.objects for p in o.data.polygons)}))
