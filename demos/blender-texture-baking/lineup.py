"""After the bake: copy the low poly (Crate_baked gets the baked texture set next) and spread the three
crates into a row, high | low | low + bake, with a small placard under each. The bake needed them on top of
each other; the row only moves them. Run in the session: cloud.py run lineup.py -- <high tris>"""
import json
import sys

import bpy

STEP = 1.0                                   # metres between crate centres
high_tris = int(sys.argv[sys.argv.index("--") + 1])
sc = bpy.context.scene
cut = bpy.data.objects.get("Crate_cut")      # apply_stack.py applied it; it has done its job
if cut:
    bpy.data.objects.remove(cut, do_unlink=True)
low = bpy.data.objects["Crate_low"]
baked = low.copy()
baked.data = low.data.copy()
baked.name = baked.data.name = "Crate_baked"
sc.collection.objects.link(baked)
for n, x in (("Crate_high", -STEP), ("Crate_bolts", -STEP), ("Crate_low", 0.0), ("Crate_baked", STEP)):
    bpy.data.objects[n].location.x = x

ink = bpy.data.materials.new("DEMO_Placard")
b = next(x for x in ink.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value, b.inputs["Roughness"].default_value = (0.75, 0.75, 0.75, 1), 0.6
for word, x in ((f"high · {high_tris:,} tris", -STEP), ("low · 12 tris", 0.0), ("low + bake", STEP)):
    cu = bpy.data.curves.new("Label", "FONT")
    cu.body, cu.size, cu.align_x = word, 0.06, "CENTER"
    cu.materials.append(ink)
    t = bpy.data.objects.new("DEMO_Label", cu)
    t.location, t.rotation_euler = (x, -0.62, 0.012), (1.5708, 0, 0)   # a placard standing in front
    sc.collection.objects.link(t)
print("@@JSON@@" + json.dumps({"ok": True, "row": ["Crate_high", "Crate_low", "Crate_baked"], "step_m": STEP}))
