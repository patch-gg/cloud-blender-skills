"""Input for blender-stylized-npr: KayKit's knight (CC0), posed with its own Idle_A clip and frozen into one
mesh (scale applied, as toon outlines need), then copied into a row with one material each, so every
copy can take its own toon_setup.py call. Names: Knight_<stage>, left to right.
Run in the session: cloud.py run scene.py -- assets/Knight.glb [pose frame]"""
import json
import sys

import bpy
from mathutils import Matrix

STAGES = ("pbr", "bands", "tint", "rim", "outline")
STEP = 1.05                                  # metres between knights

argv = sys.argv[sys.argv.index("--") + 1:]
glb, pose_frame = argv[0], int(argv[1]) if len(argv) > 1 else 0
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.armatures, bpy.data.actions,
             bpy.data.node_groups, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
arm.animation_data.action = bpy.data.actions["Idle_A"]
sc.frame_set(pose_frame)
dg = bpy.context.evaluated_depsgraph_get()

# freeze the pose: the deformed parts, in world space, joined into one mesh
parts = [o for o in sc.objects if o.type == "MESH" and o.parent == arm]
frozen = []
for p in parts:
    me = bpy.data.meshes.new_from_object(p.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(p.matrix_world)
    o = bpy.data.objects.new(p.name, me)
    sc.collection.objects.link(o)
    frozen.append(o)
for o in [o for o in sc.objects if o not in frozen]:   # rig, pivot and a stray icosphere in the file
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
with bpy.context.temp_override(active_object=frozen[0], object=frozen[0], selected_objects=frozen,
                               selected_editable_objects=frozen):
    bpy.ops.object.join()
knight = frozen[0]
knight.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
pts = [v.co for v in knight.data.vertices]
lo = [min(p[i] for p in pts) for i in range(3)]
hi = [max(p[i] for p in pts) for i in range(3)]
knight.data.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))  # feet on z=0
# merge by distance before any Solidify (the skill's hull gotcha): split vertices tear the outline. Sharp
# edges from the custom normals keep the shading as it was.
split = len(knight.data.vertices)
knight.select_set(True)
bpy.context.view_layer.objects.active = knight
with bpy.context.temp_override(active_object=knight, object=knight, selected_objects=[knight],
                               selected_editable_objects=[knight]):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode="OBJECT")
merged = split - len(knight.data.vertices)

# the row: one copy per stage, each with its own material
names = []
for i, stage in enumerate(STAGES):
    ob = knight if i == 0 else knight.copy()
    if i:
        ob.data = knight.data.copy()
        sc.collection.objects.link(ob)
        ob.data.materials[0] = knight.data.materials[0].copy()
    ob.name = ob.data.name = f"Knight_{stage}"
    ob.data.materials[0].name = f"M_Knight_{stage}"
    ob.location.x = (i - (len(STAGES) - 1) / 2) * STEP
    names.append(ob.name)
knight.data.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "objects": names, "tris": len(knight.data.loop_triangles),
                               "merged_verts": merged, "dims_m": [round(x, 3) for x in knight.dimensions],
                               "pose": ["Idle_A", pose_frame]}))
