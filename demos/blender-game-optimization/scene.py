"""The input: a detailed game prop from Patch's asset library (Poly Haven's porcelain horse statue, 22k tris),
imported and named the way the game skills expect (SM_<Name>, transforms applied, pivot at the bottom centre).
Run in the session: cloud.py run scene.py -- assets/horse_statue_01.glb"""
import json
import sys

import bpy

path = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
    for x in list(block):
        if x.users == 0:
            block.remove(x)
bpy.ops.import_scene.gltf(filepath=path)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
ob = meshes[0]
ob.name = ob.data.name = "SM_Horse"
for o in list(bpy.context.scene.objects):  # glTF import may add empties/parents: keep only the mesh
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
ob.parent = None
bpy.context.view_layer.objects.active = ob
for o in bpy.context.selected_objects:
    o.select_set(False)
ob.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
lo = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
xs = [(ob.matrix_world @ v.co).x for v in ob.data.vertices]
ys = [(ob.matrix_world @ v.co).y for v in ob.data.vertices]
ob.location.x -= (max(xs) + min(xs)) / 2
ob.location.y -= (max(ys) + min(ys)) / 2
ob.location.z -= lo
me = ob.data
me.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "object": ob.name, "tris": len(me.loop_triangles),
                               "verts": len(me.vertices), "dims_m": [round(v, 3) for v in ob.dimensions],
                               "materials": [s.material.name for s in ob.material_slots if s.material]}))
