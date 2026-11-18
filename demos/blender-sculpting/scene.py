"""The base for the sculpt: a stone head and shoulders (an island moai, 1.06 m tall) blocked out from 13
overlapping primitives in ONE mesh, at real scale, centred on X so symmetrize works. Voxel remesh will fuse
the parts. Run in the session: cloud.py run scene.py"""
import json

import bmesh
import bpy
from mathutils import Matrix

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.textures, bpy.data.cameras,
              bpy.data.lights):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
sc = bpy.context.scene
bm = bmesh.new()


def box(x0, x1, y0, y1, z0, z1, shear_y=0.0):
    """Axis-aligned box; shear_y pushes the bottom face forward (-Y) by that much (a wedge-ish nose)."""
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                              @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
    if shear_y:
        zmid = (z0 + z1) / 2
        for v in r["verts"]:
            if v.co.z < zmid:
                v.co.y -= shear_y


def ball(x, y, z, r):
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r,
                              matrix=Matrix.Translation((x, y, z)))


# body and head (the face looks down -Y)
box(-0.34, 0.34, -0.19, 0.22, 0.00, 0.30)          # shoulders
box(-0.21, 0.21, -0.13, 0.18, 0.24, 0.46)          # neck
box(-0.25, 0.25, -0.20, 0.22, 0.40, 1.06)          # head: tall, long-faced, flat on top
box(-0.27, 0.27, -0.29, -0.12, 0.80, 0.90)         # heavy brow
box(-0.075, 0.075, -0.30, -0.15, 0.56, 0.84, shear_y=0.05)   # long nose, wider and further out at the tip
ball(-0.068, -0.31, 0.585, 0.052)                  # nostril wings
ball(0.068, -0.31, 0.585, 0.052)
box(-0.14, 0.14, -0.27, -0.14, 0.475, 0.535)       # upper lip, pushed out
box(-0.16, 0.16, -0.245, -0.12, 0.40, 0.475)       # lower lip
box(-0.18, 0.18, -0.235, -0.10, 0.30, 0.41)        # chin
box(0.235, 0.30, -0.05, 0.08, 0.55, 0.93)          # long ears
box(-0.30, -0.235, -0.05, 0.08, 0.55, 0.93)
box(-0.26, 0.26, -0.16, 0.20, 1.00, 1.07)          # the flat crown

me = bpy.data.meshes.new("Moai")
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = False
ob = bpy.data.objects.new("Moai", me)
sc.collection.objects.link(ob)
m = bpy.data.materials.new("M_Clay")
b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.42, 0.39, 0.355, 1)
b.inputs["Roughness"].default_value = 0.62
m.diffuse_color = (0.42, 0.39, 0.355, 1)
me.materials.append(m)
print("@@JSON@@" + json.dumps({"ok": True, "object": ob.name, "parts": 13, "faces": len(me.polygons),
                               "size_m": [round(v, 3) for v in ob.dimensions]}))
