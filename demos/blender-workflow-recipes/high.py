"""High-poly source for the bake: a copy of every blockout part as <Part>_high in a High collection, each with
its own material (the ID map's mask). apply_stack.py then puts the hard-surface stack on these copies.
Run in the session: cloud.py run high.py"""
import hashlib
import json

import bpy

sc = bpy.context.scene
high = bpy.data.collections.get("High") or bpy.data.collections.new("High")
if high.name not in sc.collection.children:
    sc.collection.children.link(high)
names = []
for src in list(bpy.data.collections["Blockout"].objects):
    name = f"{src.name}_high"
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = ob.data.name = name
    high.objects.link(ob)
    mat = bpy.data.materials.get(f"M_ID_{src.name}") or bpy.data.materials.new(f"M_ID_{src.name}")
    h = hashlib.md5(mat.name.encode()).digest()
    mat.diffuse_color = (h[0] / 255, h[1] / 255, h[2] / 255, 1)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    src.hide_set(True)
    src.hide_render = True
    names.append(name)
print("@@JSON@@" + json.dumps({"ok": True, "high": names}))
