"""Round trip: import every exported file back into the live scene, each into its own collection, and
measure it against the original (size, triangles, materials, textures that load and drive base colour).
Then lay the six copies out on a two-step riser (3 + 3), each on a spin empty, with a small label.
Run in the session: cloud.py run roundtrip.py -- SM_RubberDuck godot=export/x.glb unity=export/x.fbx ..."""
import json
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
src = bpy.data.objects[args[0]]
files = [a.split("=", 1) for a in args[1:]]
PINK = (0.913, 0.047, 0.651, 1)     # #F53CD1 in linear
INK = (0.0056, 0.0056, 0.0056, 1)   # #111111 in linear

IMPORT = {".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p),
          ".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
          ".usdz": lambda p: bpy.ops.wm.usd_import(filepath=p)}


def bounds(obs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.evaluated_get(dg).bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def tris(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    eo.to_mesh_clear()
    return n


for c in [c for c in bpy.data.collections if c.name.startswith(("RT_", "Labels"))]:
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(c)
if bpy.data.objects.get("Riser"):
    bpy.data.objects.remove(bpy.data.objects["Riser"], do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)   # a rerun re-imports into a clean file
lo0, hi0 = bounds([src])
dims0 = hi0 - lo0
src.hide_set(True)   # the original stays in the file, out of the picture
src.hide_render = True
vl = bpy.context.view_layer
copies, report = [], {}
for preset, path in files:
    col = bpy.data.collections.new("RT_" + preset)
    bpy.context.scene.collection.children.link(col)
    vl.active_layer_collection = vl.layer_collection.children[col.name]
    before = set(bpy.data.objects)
    IMPORT[os.path.splitext(path)[1].lower()](os.path.abspath(path))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:  # every imported object in this copy's collection only
        for uc in list(o.users_collection):
            if uc != col:
                uc.objects.unlink(o)
        if col not in o.users_collection:
            col.objects.link(o)
    meshes = [o for o in new if o.type == "MESH"]
    lo, hi = bounds(meshes)
    dims = hi - lo
    mats = {s.material for o in meshes for s in o.material_slots if s.material}
    imgs, base_tex = set(), 0
    for m in mats:
        for n in (m.node_tree.nodes if m.node_tree else []):
            if n.type == "TEX_IMAGE" and n.image:
                imgs.add(n.image)
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.node_tree else None
        link = bsdf.inputs["Base Color"].links[0] if bsdf and bsdf.inputs["Base Color"].links else None
        while link and link.from_node.type not in ("TEX_IMAGE",) and link.from_node.inputs:
            ins = [i for i in link.from_node.inputs if i.links]
            link = ins[0].links[0] if ins else None
        base_tex += int(bool(link and link.from_node.type == "TEX_IMAGE" and link.from_node.image
                             and link.from_node.image.size[0] > 0))
    loaded = sum(1 for i in imgs if i.size[0] > 0)
    dev = max(abs(a - b) for a, b in zip(dims, dims0)) * 1000
    ok = dev < 1.0 and base_tex == len(mats) and loaded == len(imgs) and len(imgs) > 0
    kb = os.path.getsize(path) / 1024
    report[preset] = {"file": path, "kb": round(kb, 1), "dims_m": [round(v, 4) for v in dims],
                      "max_dev_mm": round(dev, 3), "tris": sum(tris(o) for o in meshes),
                      "objects": len(new), "materials": len(mats), "images": len(imgs),
                      "images_loaded": loaded, "base_color_textured": base_tex == len(mats), "ok": ok}
    roots = [o for o in new if o.parent is None or o.parent not in new]
    copies.append((preset, path, roots, ok))

# layout: front row of three on the floor, back row of three on a riser behind them
PITCH, BACK_Y, RISER_H = 0.42, 0.47, 0.36
slots = [(-PITCH, 0, 0), (0, 0, 0), (PITCH, 0, 0), (-PITCH, BACK_Y, RISER_H), (0, BACK_Y, RISER_H),
         (PITCH, BACK_Y, RISER_H)]
lab = bpy.data.collections.new("Labels")
bpy.context.scene.collection.children.link(lab)
ink = bpy.data.materials.get("M_Label") or bpy.data.materials.new("M_Label")
pink = bpy.data.materials.get("M_Label_Pink") or bpy.data.materials.new("M_Label_Pink")
for m, c in ((ink, INK), (pink, PINK)):
    m.diffuse_color = c
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.0
spins = []
for (preset, path, roots, ok), (x, y, z) in zip(copies, slots):
    col = bpy.data.collections["RT_" + preset]
    e = bpy.data.objects.new("Spin_" + preset, None)
    e.empty_display_size = 0.1
    col.objects.link(e)
    for r in roots:
        r.parent = e
    e.location = (x, y, z)
    spins.append(e.name)
    ext = os.path.splitext(path)[1][1:]
    kb = report[preset]["kb"]
    cu = bpy.data.curves.new("Label_" + preset, "FONT")
    cu.body = f"{preset} · {ext} · " + (f"{kb:.0f} kb" if kb < 1000 else f"{kb / 1024:.1f} mb")
    cu.size, cu.align_x = 0.034, "CENTER"
    cu.materials.append(ink if ok else pink)
    t = bpy.data.objects.new("Label_" + preset, cu)
    t.location = (x, y - 0.235, z + 0.012)
    t.rotation_euler = (1.5708, 0, 0)  # standing, facing the camera (-Y)
    t.visible_shadow = False           # a caption, not part of the set
    lab.objects.link(t)

# the step the back row stands on, wider than the frame
me = bpy.data.meshes.new("Riser")
w, d0, d1 = 5.0, BACK_Y - 0.25, BACK_Y + 0.32
v = [(-w / 2, d0, 0), (w / 2, d0, 0), (w / 2, d1, 0), (-w / 2, d1, 0),
     (-w / 2, d0, RISER_H), (w / 2, d0, RISER_H), (w / 2, d1, RISER_H), (-w / 2, d1, RISER_H)]
f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
me.from_pydata(v, [], f)
riser = bpy.data.objects.new("Riser", me)
bpy.context.scene.collection.objects.link(riser)
bev = riser.modifiers.new("Bevel", "BEVEL")
bev.width, bev.segments = 0.012, 4
vl.active_layer_collection = vl.layer_collection
bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": all(r["ok"] for r in report.values()), "original_dims_m":
                               [round(v_, 4) for v_ in dims0], "roundtrip": report, "spins": spins,
                               "labels": [o.name for o in lab.objects], "riser": riser.name,
                               "meshes": [o.name for c in bpy.data.collections if c.name.startswith("RT_")
                                          for o in c.objects if o.type == "MESH"]}))
