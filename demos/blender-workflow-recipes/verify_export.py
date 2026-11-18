"""Verify exports the way blender-export-pipelines says: re-import each file into an empty scene and check
what came back (meshes, tris, dimensions, object scale, materials, images). Run as its own Blender:
cloud.py run --process verify_export.py -- /work/export/SM_JerryCan.glb /work/export/SM_JerryCan.fbx"""
import ctypes
import json
import os
import sys

import bpy

lib = os.path.join(os.path.dirname(os.path.realpath(bpy.app.binary_path)), "lib", "libmeshoptimizer.so")
if os.path.isfile(lib):  # Blender 5.2 (Linux) can't find its own meshopt decoder for the .glb import
    ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
files = sys.argv[sys.argv.index("--") + 1:]
out = {}
for path in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)       # a separate process: a fresh, empty scene
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".glb", ".gltf"):
            r = bpy.ops.import_scene.gltf(filepath=path)
        else:
            r = bpy.ops.import_scene.fbx(filepath=path)
    except Exception as e:  # noqa: BLE001 - report it as a failed check
        out[os.path.basename(path)] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        continue
    meshes = {}
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        ob.data.calc_loop_triangles()
        meshes[ob.name] = {"tris": len(ob.data.loop_triangles), "dims_m": [round(v, 3) for v in ob.dimensions],
                           "scale": [round(v, 3) for v in ob.matrix_world.to_scale()],
                           "materials": [m.name for m in ob.data.materials if m]}
    imgs = [i.name for i in bpy.data.images if i.type == "IMAGE"]
    out[os.path.basename(path)] = {"ok": r == {"FINISHED"} and bool(meshes), "kb": round(os.path.getsize(path) / 1024, 1),
                                   "meshes": meshes, "images": imgs}
print("@@JSON@@" + json.dumps({"ok": all(v.get("ok") for v in out.values()), "files": out}))
