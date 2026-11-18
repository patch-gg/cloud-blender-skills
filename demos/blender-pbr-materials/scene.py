"""Six material balls in a row, with a small label under each. Run in the session: cloud.py run scene.py"""
import json

import bmesh
import bpy

PRESETS = ["gold", "copper", "chrome", "paint", "ceramic", "rubber"]

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
names = []
for i, p in enumerate(PRESETS):
    me = bpy.data.meshes.new(f"Ball_{p}")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=0.42)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = bpy.data.objects.new(f"Ball_{p}", me)
    ob.location = ((i - 2.5) * 1.0, 0, 0.42)
    sc.collection.objects.link(ob)
    names.append(ob.name)
    cu = bpy.data.curves.new(f"Label_{p}", "FONT")
    cu.body, cu.size, cu.align_x = p, 0.1, "CENTER"
    t = bpy.data.objects.new(f"Label_{p}", cu)
    t.location = ((i - 2.5) * 1.0, -0.55, 0.012)  # a small placard standing in front of each ball
    t.rotation_euler = (1.5708, 0, 0)
    sc.collection.objects.link(t)
    m = bpy.data.materials.new("M_Label")
    m.diffuse_color = (0.7, 0.7, 0.7, 1)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.7, 0.7, 0.7, 1)
    b.inputs["Roughness"].default_value = 0.6
    cu.materials.append(m)
print("@@JSON@@" + json.dumps({"ok": True, "balls": names}))
