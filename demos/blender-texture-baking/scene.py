"""Input for blender-texture-baking: a hard-surface crate, built the way blender-hardsurface-modeling
does it, and its 12-triangle low poly.

- Crate_high: a 60 cm box (painted). Crate_cut: one cutter with a square channel and a round recess on
  every face, for apply_stack.py (booleans, then bevel, then weighted normals).
- Crate_bolts: hex bolts at the face corners, as floaters (steel).
- Crate_low: the plain box, one UV island per face in a 3x2 grid, flat shaded (every edge is a seam).
Run in the session: cloud.py run scene.py"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

S = 0.6                       # crate size (m)
RING_OUT, RING_IN, RING_D = 0.235, 0.2, 0.016    # channel: outer/inner half-size, depth
HOLE_R, HOLE_D = 0.115, 0.011                    # round recess: radius, depth
BOLT_AT = 0.268                                  # bolt offset from the face centre, both axes
PAINT, STEEL = (0.75, 0.38, 0.07), (0.56, 0.57, 0.58)   # sRGB

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
             bpy.data.lights, bpy.data.node_groups):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
sc = bpy.context.scene


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(name, color, rough, metal):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(color), 1)
    b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value = rough, metal
    m.diffuse_color = (*lin(color), 1)
    return m


def faces():
    """(normal, u, v) for the six faces of the box, right-handed."""
    for axis in range(3):
        for sign in (-1, 1):
            n = Vector([0, 0, 0])
            n[axis] = sign
            u = Vector([0, 0, 0])
            u[(axis + 1) % 3] = 1
            yield n, u, n.cross(u)


def obj(name, bm, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location.z = S / 2
    sc.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


paint = material("M_Paint", PAINT, 0.42, 0.0)

# --- high poly body: just the box; apply_stack.py cuts and bevels it
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=S)
high = obj("Crate_high", bm, paint, smooth=False)

# --- one cutter: per face a square ring (the channel) and a disc (the recess), straddling the face
bm = bmesh.new()
for n, u, v in faces():
    rot = Matrix((u, v, n)).transposed().to_4x4()
    base = Matrix.Translation(n * (S / 2)) @ rot
    ring = []
    for z in (-RING_D, RING_D):
        for r in (RING_OUT, RING_IN):
            ring.append([bm.verts.new(base @ Vector((x * r, y * r, z))) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    (bo, bi), (to, ti) = ring[:2], ring[2:]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((to[i], to[j], ti[j], ti[i]))      # top
        bm.faces.new((bo[j], bo[i], bi[i], bi[j]))      # bottom
        bm.faces.new((bo[i], bo[j], to[j], to[i]))      # outer wall
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))      # inner wall
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=HOLE_R, radius2=HOLE_R, depth=2 * HOLE_D,
                          matrix=base)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
cut = obj("Crate_cut", bm, smooth=False)

# --- bolts: hex heads with a chamfered top, at the face corners (floaters, 1 mm into the surface)
bm = bmesh.new()
for n, u, v in faces():
    if n.z < -0.5:
        continue                                # nothing on the bottom: the crate stands on it
    rot = Matrix((u, v, n)).transposed().to_4x4()
    for su in (-1, 1):
        for sv in (-1, 1):
            m = Matrix.Translation(n * (S / 2 + 0.003) + u * (su * BOLT_AT) + v * (sv * BOLT_AT)) @ rot
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.013, radius2=0.013, depth=0.008,
                                      matrix=m)
            top = [e for e in bm.edges if e.verts[0] in r["verts"] and e.verts[1] in r["verts"]
                   and all((m.inverted() @ x.co).z > 0.003 for x in e.verts)]
            bmesh.ops.bevel(bm, geom=top, offset=0.003, segments=2, affect="EDGES")
bolts = obj("Crate_bolts", bm, material("M_Steel", STEEL, 0.3, 1.0))
bolts.data.set_sharp_from_angle(angle=math.radians(35))

# --- low poly: the plain box, one UV island per face in a 3x2 grid, flat (every edge is a seam)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=S)
uv = bm.loops.layers.uv.new("UVMap")
pad = 0.012
for i, f in enumerate(sorted(bm.faces, key=lambda f: (round(f.normal.z), round(f.normal.y), round(f.normal.x)))):
    col, row = i % 3, i // 3
    x0, y0, cell = col / 3 + pad, 1 - (row + 1) / 3 + pad, 1 / 3 - 2 * pad
    n = f.normal
    t = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((0, 1, 0))
    bu = t.cross(n).normalized()
    bv = n.cross(bu).normalized()
    for lp in f.loops:
        p = lp.vert.co
        lp[uv].uv = (x0 + (p.dot(bu) / S + 0.5) * cell, y0 + (p.dot(bv) / S + 0.5) * cell)
for e in bm.edges:
    e.seam = True
low = obj("Crate_low", bm, material("M_Low", PAINT, 0.42, 0.0), smooth=False)


def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


print("@@JSON@@" + json.dumps({"ok": True, "high": [high.name, bolts.name], "cutter": cut.name, "low": low.name,
                               "bolt_tris": tris(bolts), "low_tris": tris(low), "size_m": S}))
