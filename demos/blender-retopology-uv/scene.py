"""The dense input: an AI-generated creature from Patch's asset library (Tripo image-to-3D, 441,766 tris of
triangle soup, 1 m tall), joined into one mesh named Fox, its textures and UVs dropped (it is shown as clay),
standing at the origin. Run in the session: cloud.py run scene.py -- <file.glb>"""
import json
import os
import sys

import bpy
from mathutils import Matrix, Vector

path = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
              bpy.data.lights):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
sc = bpy.context.scene
for p in ("/work/_skills/blender-retopology-uv/scripts",):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
try:
    import _bpyx
    _bpyx.gltf_meshopt_fix()
except ImportError:
    pass

bpy.ops.import_scene.gltf(filepath=path)
meshes = [o for o in sc.objects if o.type == "MESH"]
with bpy.context.temp_override(selected_editable_objects=meshes, selected_objects=meshes, active_object=meshes[0],
                               object=meshes[0]):
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    if len(meshes) > 1:
        bpy.ops.object.join()
ob = meshes[0]
for o in [o for o in sc.objects if o is not ob]:
    bpy.data.objects.remove(o, do_unlink=True)
with bpy.context.temp_override(selected_editable_objects=[ob], selected_objects=[ob], active_object=ob, object=ob):
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ob.name = ob.data.name = "Fox"
me = ob.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
for ca in list(me.color_attributes):
    me.color_attributes.remove(ca)
me.materials.clear()
for img in list(bpy.data.images):
    bpy.data.images.remove(img)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
# stand it at the origin, feet on the floor
pts = [Vector(c) for c in ob.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
me.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
clay = bpy.data.materials.new("M_Clay")
b = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.42, 0.39, 0.355, 1)
b.inputs["Roughness"].default_value = 0.62
me.materials.append(clay)
me.shade_smooth()
me.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "object": ob.name, "tris": len(me.loop_triangles),
                               "verts": len(me.vertices), "size_m": [round(v, 3) for v in ob.dimensions]}))
