"""Scatter sources from Patch's asset library (Kenney Nature Kit, CC0): each .glb becomes one object in its
layer's collection, joined, transforms applied, origin at the base centre (scatter.py instances each child
at its own origin) and sized to real-world metres (the kit is game-scale). Run in the session:
    cloud.py run scene.py -- --pines a.glb ... --broadleaf b.glb ... --rocks c.glb ...
"""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--pines", nargs="*", default=[])
ap.add_argument("--broadleaf", nargs="*", default=[])
ap.add_argument("--rocks", nargs="*", default=[])
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
sc = bpy.context.scene

# layer -> (collection, target height in m; rocks are scaled x4)
LAYERS = {"pines": ("Pines", 15.0), "broadleaf": ("Broadleaf", 11.0), "rocks": ("Rocks", None)}
# the kit's pastel teal/salmon -> natural albedos that sit with terrain.py's grass/rock/snow
ALBEDO = {"leafsDark": ((0.022, 0.05, 0.024), 0.85), "leafsGreen": ((0.05, 0.085, 0.022), 0.8),
          "woodBark": ((0.07, 0.045, 0.03), 0.9), "woodBarkDark": ((0.05, 0.035, 0.025), 0.9),
          "_defaultMat": ((0.2, 0.185, 0.17), 0.85), "dirt": ((0.12, 0.09, 0.06), 0.9),
          "grass": ((0.05, 0.075, 0.022), 0.9)}


def load(path, coll, height):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in new:  # unparent, keeping the world transform, then drop the empties
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = Path(path).stem
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = ob.data
    lo = Vector((min(v.co.x for v in me.vertices), min(v.co.y for v in me.vertices), min(v.co.z for v in me.vertices)))
    hi = Vector((max(v.co.x for v in me.vertices), max(v.co.y for v in me.vertices), max(v.co.z for v in me.vertices)))
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    s = height / (hi.z - lo.z) if height else 4.0  # rocks: the kit's 2.5 m boulders become ~10 m outcrops
    for v in me.vertices:
        v.co = (v.co - base) * s
    if height is None:
        for v in me.vertices:  # sink rocks 15% so they sit in the slope instead of on it
            v.co.z -= 0.15 * (hi.z - lo.z) * s
    me.update()
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob.location = (0, 0, 0)
    return ob.name, round((hi.z - lo.z) * s, 2), len(me.polygons)


out = {}
for key, (cname, h) in LAYERS.items():
    files = getattr(a, key)
    if not files:
        continue
    coll = bpy.data.collections.new(cname)
    sc.collection.children.link(coll)
    out[cname] = [load(f, coll, h) for f in files]
for m in bpy.data.materials:
    base = m.name.split(".")[0]
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.node_tree else None
    if base in ALBEDO and b is not None:
        rgb, rough = ALBEDO[base]
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
        m.diffuse_color = (*rgb, 1)
mats = sorted({m.name.split(".")[0] for m in bpy.data.materials if m.users})
print("@@JSON@@" + json.dumps({"ok": True, "layers": out, "materials": mats}))
