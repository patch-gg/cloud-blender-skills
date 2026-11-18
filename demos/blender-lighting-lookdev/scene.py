"""Input for blender-lighting-lookdev: Poly Haven's marble bust (CC0) as one object named Bust, standing on
z=0 at the origin, and the render size of one panel of the clip (428x720), set before turntable.py runs
because its framing depends on the aspect. Run in the session: cloud.py run scene.py -- assets/marble_bust_01.glb"""
import json
import sys

import bpy

glb = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
             bpy.data.lights, bpy.data.node_groups, bpy.data.worlds):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in sc.objects if o.type == "MESH"]
if len(meshes) > 1:
    with bpy.context.temp_override(active_object=meshes[0], object=meshes[0], selected_objects=meshes,
                                   selected_editable_objects=meshes):
        bpy.ops.object.join()
bust = meshes[0]
for o in [o for o in sc.objects if o != bust]:
    bpy.data.objects.remove(o, do_unlink=True)
bust.name = bust.data.name = "Bust"
mw = bust.matrix_world.copy()
bust.data.transform(mw)
bust.matrix_world.identity()
xs, ys, zs = zip(*[v.co for v in bust.data.vertices])
for v in bust.data.vertices:
    v.co.x -= (min(xs) + max(xs)) / 2
    v.co.y -= (min(ys) + max(ys)) / 2
    v.co.z -= min(zs)
bust.data.update()
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 428, 720, 100
bust.data.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "object": bust.name, "tris": len(bust.data.loop_triangles),
                               "dims_m": [round(x, 3) for x in bust.dimensions],
                               "materials": [s.material.name for s in bust.material_slots if s.material]}))
