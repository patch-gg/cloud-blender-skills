"""The game mesh, made by hand (recipe 2, step 2: "or manual"): the blockout parts joined into SM_JerryCan,
smooth shaded with hard edges above 60 degrees (uv_pack.py --seams-from-sharp 60 puts a UV seam on each
of them), plus one seam down the back of each cylinder so it unwraps as a strip.
Run in the session: cloud.py run low.py"""
import json
import math

import bmesh
import bpy

sc = bpy.context.scene
low = bpy.data.collections.get("Low") or bpy.data.collections.new("Low")
if low.name not in sc.collection.children:
    sc.collection.children.link(low)
old = bpy.data.objects.get("SM_JerryCan")
if old:
    bpy.data.objects.remove(old)

bm = bmesh.new()
cyl_faces = []
for src in bpy.data.collections["Blockout"].objects:
    me = src.data.copy()
    me.transform(src.matrix_world)
    n0 = len(bm.faces)
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bm.faces.ensure_lookup_table()
    if src.name in ("Spout", "Cap"):
        cyl_faces.append(bm.faces[n0:])
for f in bm.faces:
    f.smooth = True
hard = 0
for e in bm.edges:
    if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(60):
        e.smooth = False                       # a hard edge: it gets a seam, so the bake has no gradient there
        hard += 1
seams = 0
for faces in cyl_faces:                        # the lengthwise edge furthest back (+Y) of each cylinder
    side = [f for f in faces if len(f.verts) == 4]
    edges ={e for f in side for e in f.edges if all(len(lf.verts) == 4 for lf in e.link_faces)}
    best = max(edges, key=lambda e: (e.verts[0].co + e.verts[1].co).y)
    best.seam = True
    seams += 1
me = bpy.data.meshes.new("SM_JerryCan")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("SM_JerryCan", me)
low.objects.link(ob)
# its one material slot, named now (engines key materials by name); build_pbr_material.py fills it later
me.materials.append(bpy.data.materials.get("M_JerryCan") or bpy.data.materials.new("M_JerryCan"))
me.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "low": ob.name, "tris": len(me.loop_triangles),
                               "verts": len(me.vertices), "hard_edges": hard, "cylinder_seams": seams,
                               "dims_m": [round(v, 4) for v in ob.dimensions]}))
