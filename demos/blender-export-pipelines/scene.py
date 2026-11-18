"""The asset to export, prepared with the export SKILL.md checklist the way an agent would before exporting:
import the GLB, name it (SM_ object, M_ materials, T_ textures), apply its transforms, put the origin at
the bottom centre on the world origin (facing -Y), and write the textures the GLB carried packed out to
real files beside the exports (export/textures/T_*.jpg|png), so FBX presets reference files that exist.
Run in the session: cloud.py run scene.py -- assets/rubber_duck_toy.glb SM_RubberDuck"""
import json
import os
import sys

import bpy
from mathutils import Matrix, Vector

src, name = sys.argv[sys.argv.index("--") + 1:][:2]
base = name.split("_", 1)[1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
bpy.data.orphans_purge(do_recursive=True)   # a rerun starts clean (no M_x.001 names)
bpy.ops.import_scene.gltf(filepath=src)

ob = next(o for o in bpy.context.scene.objects if o.type == "MESH")
ob.name = ob.data.name = name

# transforms applied; origin at the bottom centre, standing on the world origin
ob.data.transform(ob.matrix_world)
ob.matrix_world = Matrix.Identity(4)
bb = [Vector(c) for c in ob.bound_box]
lo = Vector([min(v[i] for v in bb) for i in range(3)])
hi = Vector([max(v[i] for v in bb) for i in range(3)])
ob.data.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
ob.data.update()

# M_ materials, T_ textures written out as files (the packed bytes as they are: no re-encode)
tex_dir = os.path.abspath("export/textures")
os.makedirs(tex_dir, exist_ok=True)
slots = [s.material for s in ob.material_slots if s.material]
textures = {}
for i, m in enumerate(slots):
    m.name = f"M_{base}" if len(slots) == 1 else f"M_{base}_{i + 1}"
    for n in m.node_tree.nodes:
        if n.type != "TEX_IMAGE" or not n.image or not n.image.packed_file:
            continue
        img = n.image
        to = {l.to_node.type for l in n.outputs["Color"].links}
        sockets = {l.to_socket.name for l in n.outputs["Color"].links}
        role = ("BaseColor" if "Base Color" in sockets else "Normal" if "NORMAL_MAP" in to else
                "MetalRough" if "SEPARATE_COLOR" in to else "Roughness" if "Roughness" in sockets else "Map")
        tname = m.name.replace("M_", "T_", 1) + "_" + role
        data = img.packed_file.data
        path = os.path.join(tex_dir, tname + (".png" if data[:4] == b"\x89PNG" else ".jpg"))
        with open(path, "wb") as f:
            f.write(data)
        new = bpy.data.images.load(path)
        new.colorspace_settings.name = img.colorspace_settings.name
        new.alpha_mode = img.alpha_mode
        img.user_remap(new)
        bpy.data.images.remove(img)
        new.name = tname
        textures[tname] = os.path.relpath(path, os.getcwd())

bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({
    "ok": True, "object": ob.name, "dims_m": [round(v, 4) for v in ob.dimensions],
    "origin": list(ob.location), "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons),
    "materials": [m.name for m in slots], "textures": textures,
    "still_packed": [i.name for i in bpy.data.images if i.packed_file]}))
