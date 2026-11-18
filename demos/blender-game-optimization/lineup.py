"""The LOD chain make_lods.py made, side by side (LOD0 left): unhidden, in a row, each statue turning between
-10 and 40 degrees (profile to front three-quarter) in sync on its own base (frames 1-96, frame 97 = frame 1), a small tri-count label in front of each, and a pink
"fits <budget>" under the LODs mesh_stats.py passed against that platform budget.
Run in the session before turntable.py: cloud.py run lineup.py -- SM_Horse mobile 3"""
import json
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
base = args[0] if args else "SM_Horse"
budget = args[1] if len(args) > 1 else None
fits = {int(a) for a in args[2:]}
SP = 0.19            # centre to centre, metres (the statue is 0.164 wide)
sc = bpy.context.scene
lods = sorted((o for o in bpy.data.objects if o.name.startswith(base + "_LOD") and o.type == "MESH"),
              key=lambda o: o.name)
counts = []
for i, ob in enumerate(lods):
    ob.hide_set(False)
    ob.hide_viewport = ob.hide_render = False
    ob.location = ((i - (len(lods) - 1) / 2) * SP, 0, 0)
    ob.animation_data_clear()
    ob.rotation_mode = "XYZ"                      # glTF imports in QUATERNION mode, which ignores euler keys
    for f, deg in ((1, -10), (49, 40), (97, -10)):
        ob.rotation_euler = (0, 0, math.radians(deg))
        ob.keyframe_insert("rotation_euler", index=2, frame=f)
    ob.rotation_euler = (0, 0, math.radians(-10))
    me = ob.data
    me.calc_loop_triangles()
    counts.append(len(me.loop_triangles))


def label_material(name, rgb, glow=None):
    """Diffuse grey for the labels; glow= makes an emission-only colour (AgX turns lit saturated text pastel)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1) if glow is None else (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 0.8
    if glow is not None:
        b.inputs["Specular IOR Level"].default_value = 0.0
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = glow
    return m


grey = label_material("M_Label", (0.62, 0.62, 0.62))
pink = label_material("M_Label_Pink", (0.913, 0.045, 0.637), glow=1.6)   # #F53CD1 in linear
for o in [o for o in bpy.data.objects if o.name.startswith("Label_")]:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
front = min((o.matrix_world @ Vector(c)).y for o in lods for c in o.bound_box)


def label(name, text, x, z, size, mat):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x = text, size, "CENTER"
    cu.materials.append(mat)
    t = bpy.data.objects.new(name, cu)
    t.location = (x, front - 0.25, z)             # z lifts the baseline so descenders clear the floor
    t.rotation_euler = (math.radians(90), 0, 0)   # a small placard standing on the floor
    t.visible_shadow = False
    sc.collection.objects.link(t)
    return t


for i, (ob, n) in enumerate(zip(lods, counts)):
    label(f"Label_lod{i}", f"lod{i} · {n:,} tris", ob.location.x, 0.0175, 0.0102, grey)
    if i in fits and budget:
        label(f"Label_fits{i}", f"fits {budget}", ob.location.x, 0.0035, 0.0092, pink)
print("@@JSON@@" + json.dumps({"ok": True, "lods": [o.name for o in lods], "tris": counts,
                               "fits": sorted(fits), "budget": budget}))
