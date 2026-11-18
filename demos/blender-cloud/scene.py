"""Base scene for the six forks: Poly Haven's fire hydrant (CC0) on a big ground plane, at the 640x540
the grid's cells need. Usage: cloud.py run scene.py -- <fire_hydrant.glb>"""
import json
import sys

import bpy

glb = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
for o in [o for o in bpy.data.objects if o not in before and o.name.endswith("_aged")]:
    bpy.data.objects.remove(o, do_unlink=True)  # the file holds a clean and an aged hydrant: keep the clean one
meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]:
    for c in o.children:
        c.matrix_parent_inverse = o.matrix_world.inverted() @ c.matrix_parent_inverse
    bpy.data.objects.remove(o, do_unlink=True)
with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes, object=meshes[0]):
    if len(meshes) > 1:
        bpy.ops.object.join()
hyd = meshes[0]
hyd.name = hyd.data.name = "Hydrant"
hyd.parent = None
with bpy.context.temp_override(active_object=hyd, selected_editable_objects=[hyd], object=hyd):
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
pts = [hyd.matrix_world @ v.co for v in hyd.data.vertices]
hyd.location.x -= (min(p.x for p in pts) + max(p.x for p in pts)) / 2
hyd.location.y -= (min(p.y for p in pts) + max(p.y for p in pts)) / 2
hyd.location.z -= min(p.z for p in pts)
me = bpy.data.meshes.new("Ground")
me.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
me.uv_layers.new(name="UVMap")
g = bpy.data.objects.new("Ground", me)
bpy.context.scene.collection.objects.link(g)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 540, 100
d = hyd.dimensions
print("@@JSON@@" + json.dumps({"ok": True, "hydrant": hyd.name, "dims_m": [round(x, 3) for x in d],
                               "tris": sum(len(p.vertices) - 2 for p in hyd.data.polygons)}))
