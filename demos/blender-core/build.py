"""A retro toy rocket, built one step per call in the live session, the way blender-core works:
data API only (bmesh/from_pydata, no operators), explicit names, nodes found by type.

Run in the session: cloud.py run build.py -- --step body|nose|fins|window|paint
Each step tags what it makes with ob["build_step"] (present.py turns that into the stop-motion)
and prints @@JSON@@ with the objects it made, their tris and dimensions.
"""
import argparse
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector

STEPS = ["body", "nose", "fins", "window", "paint"]

# the rocket's silhouette, radius r at height z (m); body and nose are cut from it
SIL = [(0.13, 0.16), (0.17, 0.25), (0.205, 0.40), (0.22, 0.55), (0.215, 0.70), (0.19, 0.85),
       (0.155, 0.98), (0.11, 1.10), (0.062, 1.22), (0.022, 1.32), (0.0, 1.37)]


def r_at(z):
    """Silhouette radius at height z (linear between the control points)."""
    for (r0, z0), (r1, z1) in zip(SIL, SIL[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return SIL[0][0] if z < SIL[0][1] else 0.0


def smooth(points, sub=6):
    """Catmull-Rom through (r, z) points: a smooth profile from a few control points."""
    out = []
    p = [points[0]] + points + [points[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (Vector(x) for x in p[i - 1:i + 3])
        for k in range(sub):
            t = k / sub
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(points[-1])
    return out


def lathe(name, prof, segs=48):
    """Mesh from spinning a (r, z) profile (bottom to top) around Z; r == 0 ends become poles.
    Quads around, triangle fans at the poles, a cylindrical UV map, outward normals."""
    verts, faces, uvs = [], [], []
    rings = []
    for r, z in prof:
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            ring = []
            for s in range(segs):
                a = 2 * math.pi * s / segs
                ring.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            rings.append(ring)
    lens = [0.0]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        lens.append(lens[-1] + math.hypot(r1 - r0, z1 - z0))
    vs = [x / lens[-1] for x in lens]
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for s in range(segs):
            s1 = (s + 1) % segs
            u0, u1 = s / segs, (s + 1) / segs
            if len(a) == 1:
                faces.append((a[0], b[s], b[s1]))
                uvs.append([((u0 + u1) / 2, vs[i]), (u0, vs[i + 1]), (u1, vs[i + 1])])
            elif len(b) == 1:
                faces.append((a[s], a[s1], b[0]))
                uvs.append([(u0, vs[i]), (u1, vs[i]), ((u0 + u1) / 2, vs[i + 1])])
            else:
                faces.append((a[s], a[s1], b[s1], b[s]))
                uvs.append([(u0, vs[i]), (u1, vs[i]), (u1, vs[i + 1]), (u0, vs[i + 1])])
    return _mesh(name, verts, faces, uvs)


def torus(name, major, minor, segs=48, sides=12):
    verts, faces, uvs = [], [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(sides):
            b = 2 * math.pi * j / sides
            rr = major + minor * math.cos(b)
            verts.append((rr * math.cos(a), rr * math.sin(a), minor * math.sin(b)))
    for i in range(segs):
        for j in range(sides):
            i1, j1 = (i + 1) % segs, (j + 1) % sides
            faces.append((i * sides + j, i1 * sides + j, i1 * sides + j1, i * sides + j1))
            uvs.append([(i / segs, j / sides), ((i + 1) / segs, j / sides),
                        ((i + 1) / segs, (j + 1) / sides), (i / segs, (j + 1) / sides)])
    return _mesh(name, verts, faces, uvs)


def _mesh(name, verts, faces, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    if uvs:
        uv = me.uv_layers.new(name="UVMap")
        flat = [c for f in uvs for xy in f for c in xy]
        uv.data.foreach_set("uv", flat)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.validate()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(50))
    return me


def place(me, name, step, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Link a new object with the transform baked into the mesh (applied scale/rotation, origin kept)."""
    from mathutils import Euler, Matrix
    me.transform(Matrix.LocRotScale(None, Euler(rot), None))
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    col = bpy.data.collections.get("Rocket")
    if col is None:
        col = bpy.data.collections.new("Rocket")
        bpy.context.scene.collection.children.link(col)
    col.objects.link(ob)
    ob["build_step"] = step
    return ob


def fin(name, angle):
    """A swept fin in the radial plane: root buried 2 cm in the body, foot on the ground (z = 0)."""
    root = [(r_at(z) - 0.02, z) for z in (0.64, 0.56, 0.48, 0.40, 0.32, 0.24)]
    outer = [(0.30, 0.10), (0.37, 0.0), (0.43, 0.0), (0.445, 0.05), (0.41, 0.17), (0.35, 0.33),
             (0.28, 0.48), (0.22, 0.60)]
    outline = root + outer   # top-down along the root, then out and back up the leading edge
    n, t = len(outline), 0.017
    verts = [(x, -t, z) for x, z in outline] + [(x, t, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]          # front, back
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]   # sides
    uvs = [[(x / 0.9, z / 0.7) for x, z in outline], [(0.5 + x / 0.9, z / 0.7) for x, z in reversed(outline)]]
    uvs += [[(i / n, 0.9), ((i + 1) / n, 0.9), ((i + 1) / n, 1.0), (i / n, 1.0)] for i in range(n)]
    me = _mesh(name, verts, faces, uvs)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])  # concave n-gons -> tris
    bm.to_mesh(me)
    bm.free()
    ob = place(me, name, 3, rot=(0, 0, angle))
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width, bev.segments, bev.limit_method = 0.008, 3, "ANGLE"
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(50))
    return ob


def material(name, color, rough, metal=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")  # by type, never by name
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*color, 1)
    return m


def step_body():
    for ob in list(bpy.data.objects):            # a fresh session's factory cube, light and camera
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)
    prof = smooth([p for p in SIL if p[1] <= 0.98], 4)
    prof = [(0.0, prof[0][1])] + prof + [(0.0, prof[-1][1])]
    return [place(lathe("Body", prof), "Body", 1)]


def step_nose():
    z0 = 0.965
    pts = [(r_at(z0) + 0.006, z0)] + [p for p in SIL if p[1] > 0.98]
    nose = smooth(pts, 4)
    nose = [(0.0, z0)] + nose
    bell = [(0.0, 0.112), (0.07, 0.10), (0.112, 0.082), (0.118, 0.09), (0.098, 0.13), (0.078, 0.18),
            (0.07, 0.215), (0.0, 0.215)]
    return [place(lathe("Nose", nose), "Nose", 2), place(lathe("Nozzle", smooth(bell, 3), 40), "Nozzle", 2)]


def step_fins():
    return [fin(f"Fin_{i + 1}", math.radians(a)) for i, a in enumerate((90, 210, 330))]


def step_window():
    zc = 0.70
    y = -(r_at(zc) - 0.004)
    ring = place(torus("Window_Ring", 0.064, 0.013), "Window_Ring", 4, loc=(0, y, zc),
                 rot=(math.pi / 2, 0, 0))
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")              # calc_uvs only fills a layer that already exists
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=0.058, calc_uvs=True)
    for v in bm.verts:
        v.co.z *= 0.42                            # a lens, flattened in the mesh, not by object scale
    me = bpy.data.meshes.new("Window_Glass")
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    glass = place(me, "Window_Glass", 4, loc=(0, y + 0.006, zc), rot=(math.pi / 2, 0, 0))
    return [ring, glass]


def step_paint():
    m = {"Body": material("M_Body", (0.72, 0.64, 0.50), 0.38, coat=0.25),
         "Red": material("M_Red", (0.45, 0.018, 0.012), 0.3, coat=0.6),
         "Chrome": material("M_Chrome", (0.92, 0.92, 0.92), 0.12, metal=1.0),
         "Glass": material("M_Glass", (0.02, 0.07, 0.09), 0.04, coat=1.0),
         "Nozzle": material("M_Nozzle", (0.16, 0.16, 0.17), 0.32, metal=0.9)}
    plan = {"Body": "Body", "Nose": "Red", "Nozzle": "Nozzle", "Window_Ring": "Chrome",
            "Window_Glass": "Glass", "Fin_1": "Red", "Fin_2": "Red", "Fin_3": "Red"}
    obs = []
    for name, key in plan.items():
        ob = bpy.data.objects[name]
        ob.data.materials.clear()
        ob.data.materials.append(m[key])
        obs.append(ob)
    return obs


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--step", required=True, choices=STEPS)
    o = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    made = globals()["step_" + o.step]()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for ob in made:
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        out[ob.name] = {"tris": len(me.loop_triangles), "dims": [round(v, 3) for v in ob.dimensions],
                        "materials": [s.material.name for s in ob.material_slots if s.material]}
        ob.evaluated_get(dg).to_mesh_clear()
    print("@@JSON@@" + json.dumps({"ok": True, "step": o.step, "made": out,
                                   "objects": len([o for o in bpy.data.objects if o.type == "MESH"])}))


main()
