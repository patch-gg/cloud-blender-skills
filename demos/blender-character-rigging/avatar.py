"""The character for the rigging, animation and clothing demos: Patch's CC0 MPFB human, made unrigged.

Imports the GLB, removes the skeleton it was exported with (armature, Armature modifiers, vertex groups),
welds the vertices glTF split along UV seams (bone heat needs connected surfaces), and stands the result
at the origin as one mesh, `Body`: facing -Y, centred on X, feet on Z=0, scale applied (the skill's
"prepare the mesh" step). `--shirt` keeps the t-shirt as its own mesh, `Shirt`, for layered clothing.
Run in the session: cloud.py run avatar.py -- assets/human-0255.glb [--shirt] [--name Body]
"""
import json
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
glb = argv[0]
keep_shirt = "--shirt" in argv
name = argv[argv.index("--name") + 1] if "--name" in argv else "Body"

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=bpy.path.abspath(glb))
new = [o for o in bpy.data.objects if o not in before]
bpy.context.view_layer.update()

PARTS = {"male_generic": "Skin", "male_casualsuit06": "Outfit", "shoes05": "Shoes", "high-poly": "Eyes",
         "eyebrow001": "Brows", "eyelashes04": "Lashes"}
meshes = {}
for ob in new:
    if ob.type != "MESH" or not (ob.parent and ob.parent.type == "ARMATURE"):  # not the collision shape
        continue
    mw = ob.matrix_world.copy()
    for m in [m for m in ob.modifiers if m.type == "ARMATURE"]:
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    ob.parent = None
    ob.matrix_world = mw
    meshes[PARTS.get(ob.name.split(".")[-1], ob.name)] = ob
for ob in new:
    if ob.name in bpy.data.objects and ob not in meshes.values():
        bpy.data.objects.remove(ob, do_unlink=True)   # the exported skeleton, its pivot, the collision shape


def islands(bm):
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            isl.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        out.append(isl)
    return out


def bake(ob):
    """World-space verts, seams welded, smooth shading, identity transform."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    welded = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    welded -= len(bm.verts)
    bm.to_mesh(ob.data)
    bm.free()
    ob.matrix_world = Matrix()
    if ob.data.has_custom_normals:  # glTF's split normals no longer match the welded verts
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob],
                                       selected_editable_objects=[ob]):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    ob.data.shade_smooth()
    return welded


# split the outfit into the t-shirt (pieces that reach the chest) and the jeans, before welding
out = meshes.pop("Outfit")
bm = bmesh.new()
bm.from_mesh(out.data)
bm.transform(out.matrix_world)
top = max(v.co.z for v in bm.verts)
shirt_verts = {v.index for isl in islands(bm) if max(v.co.z for v in isl) > 0.75 * top for v in isl}
bm.free()
shirt = out.copy()
shirt.data = out.data.copy()
bpy.context.scene.collection.objects.link(shirt)
for ob, keep in ((shirt, True), (out, False)):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.index in shirt_verts) != keep], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
meshes["Shirt"], meshes["Jeans"] = shirt, out
welded = {k: bake(ob) for k, ob in meshes.items()}

# stand it up: centred on X/Y, feet on Z=0
pts = [v.co for ob in meshes.values() for v in ob.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
shift = Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
for ob in meshes.values():
    ob.data.transform(shift)
    ob.data.update()

# one mesh (or two: Body + Shirt)
join = [ob for k, ob in meshes.items() if not (keep_shirt and k == "Shirt")]
main = meshes["Skin"]
with bpy.context.temp_override(active_object=main, object=main, selected_objects=join,
                               selected_editable_objects=join):
    bpy.ops.object.join()
main.name = main.data.name = name
objs = [main]
if keep_shirt:
    shirt.name = shirt.data.name = "Shirt"
    objs.append(shirt)
for ob in objs:
    for i, m in enumerate(ob.data.materials):
        if m:
            m.name = m.name.split(".")[-1]
bpy.context.view_layer.update()
res = {"ok": True, "objects": [o.name for o in objs], "height_m": round(hi.z - lo.z, 3),
       "verts": {o.name: len(o.data.vertices) for o in objs},
       "tris": {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs},
       "seam_verts_welded": sum(welded.values())}
print("@@JSON@@" + json.dumps(res))
