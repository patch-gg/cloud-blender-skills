"""blender-scene-setup's procedure, steps 2-6, after scene_audit.py --fix purge scale has applied rotation
and scale and purged the orphans: metric units, one ASSET_<Name> collection per prop, SM_/M_/T_ names
(textures by what they feed: _BC, _N, _ORM), origins at the bottom centre with props on z = 0.

Run in the session: cloud.py run tidy.py -- --names Mesh.002=PottedPlant Cylinder.001=WineBarrel ...
"""
import argparse
import json
import sys

import bpy
from mathutils import Matrix, Vector

a = argparse.ArgumentParser()
a.add_argument("--names", nargs="+", required=True, help="old=Name pairs")
o = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

sc = bpy.context.scene
us = sc.unit_settings
us.system, us.scale_length, us.length_unit = "METRIC", 1.0, "METERS"     # step 2


def suffix(node):
    """What an image texture feeds, by node type (names are localized): _BC, _N, _ORM, _E, _M."""
    for lk in node.outputs["Color"].links:
        t, s = lk.to_node.type, lk.to_socket.name
        if t == "NORMAL_MAP":
            return "N"
        if t in ("SEPARATE_COLOR", "SEPARATE_RGB") or s in ("Roughness", "Metallic"):
            return "ORM"
        if s == "Emission Color":
            return "E"
        if s == "Alpha":
            return "M"
    return "BC"


done = {}
for pair in o.names:
    old, base = pair.split("=")
    ob = bpy.data.objects[old]
    ob.name = ob.data.name = f"SM_{base}"                                  # step 4
    mats = [s.material for s in ob.material_slots if s.material]
    for m in mats:
        part = "" if len(mats) == 1 else "_" + m.name.rsplit("_", 1)[-1].title()
        m.name = f"M_{base}{part}"
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and not n.image.name.startswith("T_"):
                n.image.name = f"T_{base}{part}_{suffix(n)}"
    col = bpy.data.collections.get(f"ASSET_{base}") or bpy.data.collections.new(f"ASSET_{base}")  # step 3
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    bpy.context.view_layer.update()                                         # step 5: origin to bottom centre
    mw = ob.matrix_world.copy()
    pts = [mw @ v.co for v in ob.data.vertices]
    lo = Vector(min(p[i] for p in pts) for i in range(3))
    hi = Vector(max(p[i] for p in pts) for i in range(3))
    base_w = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    ob.data.transform(Matrix.Translation(-(mw.inverted() @ base_w)))
    mw.translation = base_w
    ob.matrix_world = mw
    ob.location.z = 0.0                                                      # props sit on the ground
    bpy.context.view_layer.update()
    done[ob.name] = {"was": old, "collection": col.name, "origin": [round(v, 3) for v in ob.location],
                     "materials": [m.name for m in mats], "dims": [round(v, 3) for v in ob.dimensions]}
print("@@JSON@@" + json.dumps({"ok": True, "units": [us.system, us.scale_length, us.length_unit], "props": done}))
