"""A deliberately messy scene: four CC0 props from Patch's asset library, imported and joined the quick way,
left with default names, a transform mistake each (it renders the same, so nobody noticed), everything in
the scene root, the joined parts' meshes and the factory cube's data left as orphans, and imperial units.

Run in the session: cloud.py run scene.py -- assets/wine_barrel_01.glb assets/potted_plant_02.glb ...
Prints @@JSON@@ with each prop's messy name, its mistake and where its origin is.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

# glb stem -> (default name it ends up with, the mistake)
MESS = {"potted_plant_02": ("Mesh.002", "mirrored"),
        "wine_barrel_01": ("Cylinder.001", "rotated"),
        "metal_tool_chest": ("Cube.007", "cm_scale"),
        "side_table_tall_01": ("Cube.003", "origin_far")}
ORDER = ["potted_plant_02", "wine_barrel_01", "metal_tool_chest", "side_table_tall_01"]
GAP = 0.32

paths = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sc = bpy.context.scene
for ob in list(bpy.data.objects):          # the factory cube, light and camera; their data stays behind
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
us = sc.unit_settings
us.system, us.length_unit = "IMPERIAL", "FEET"

props = {}
for path in paths:
    stem = os.path.splitext(os.path.basename(path))[0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
    parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    main = max(parts, key=lambda o: len(o.data.polygons))
    if len(parts) > 1:                       # join the parts; their meshes become orphans
        with bpy.context.temp_override(active_object=main, object=main, selected_objects=parts,
                                       selected_editable_objects=parts):
            bpy.ops.object.join()
    for o in [o for o in bpy.data.objects if o not in before and o != main]:
        bpy.data.objects.remove(o, do_unlink=True)
    props[stem] = main

# a row on the floor, left to right
bpy.context.view_layer.update()
x = 0.0
row = []
for stem in ORDER:
    ob = props[stem]
    lo = Vector(min(v.co[i] for v in ob.data.vertices) for i in range(3))
    hi = Vector(max(v.co[i] for v in ob.data.vertices) for i in range(3))
    ob.data.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
    w = hi.x - lo.x
    ob.location = (x + w / 2, 0, 0)
    row.append((ob, w))
    x += w + GAP
shift = (x - GAP) / 2
for ob, _w in row:
    ob.location.x -= shift

out = {}
for stem in ORDER:
    ob = props[stem]
    name, mistake = MESS[stem]
    me = ob.data
    if mistake == "rotated":                 # a Y-up import's +90 X left on the object (glTF objects rotate
        me.transform(Matrix.Rotation(math.radians(-90), 4, "X"))   # with quaternions), undone in the mesh
        ob.rotation_quaternion = Quaternion((1, 0, 0), math.radians(90))
    elif mistake == "mirrored":              # mirrored with S X -1, never applied
        me.transform(Matrix.Diagonal((-1, 1, 1, 1)))
        me.flip_normals()
        ob.scale = (-1, 1, 1)
    elif mistake == "cm_scale":              # imported in centimetres: 100x mesh, 0.01 object scale
        me.transform(Matrix.Scale(100, 4))
        ob.scale = (0.01, 0.01, 0.01)
    elif mistake == "origin_far":            # origin left at the world origin
        off = ob.location.copy()
        me.transform(Matrix.Translation(off))
        ob.location = (0, 0, 0)
    for c in list(ob.users_collection):      # everything in the scene root
        c.objects.unlink(ob)
    sc.collection.objects.link(ob)
    ob.name = name
    bpy.context.view_layer.update()
    out[name] = {"asset": stem, "mistake": mistake, "origin": [round(v, 3) for v in ob.matrix_world.translation],
                 "scale": [round(v, 3) for v in ob.scale],
                 "rotation_deg": [round(math.degrees(v), 1) for v in ob.matrix_basis.to_euler()],
                 "dims": [round(v, 3) for v in ob.dimensions], "mesh": me.name}
for ob in bpy.context.view_layer.objects:  # nothing selected, as in a file someone saved and closed
    ob.select_set(False)
orphans = sum(1 for c in ("meshes", "materials", "images", "node_groups", "actions", "textures")
              for d in getattr(bpy.data, c) if d.users == 0)
print("@@JSON@@" + json.dumps({"ok": True, "props": out, "orphans": orphans, "units": us.system}))
