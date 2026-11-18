"""The input for blender-hair-grooming: the head from demos/blender-facial-shapekeys (its scene.py and face.py, run
as they are), without the beanie, and a Scalp vertex group painted procedurally: a soft hairline over the forehead
and temples, above the ears and down to the nape. Hair attaches by UV; the head already has non-overlapping UVs.
Run in the session: cloud.py run scene.py -- face.py face_scene.py"""
import importlib.util
import json
import runpy
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
face_py, face_scene = args[0], args[1]
old, sys.argv = sys.argv, [sys.argv[0], "--", face_py]
try:
    runpy.run_path(face_scene, run_name="__main__")      # Head, EyeL/R, Neck, Body (+ the beanie prop)
finally:
    sys.argv = old
spec = importlib.util.spec_from_file_location("face", face_py)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

bpy.data.objects.remove(bpy.data.objects["Beanie"], do_unlink=True)
head = bpy.data.objects["Head"]
sub = head.modifiers.get("Subdivision")
sub.levels = sub.render_levels = 1          # the same surface in the session and the render: hair attaches to it

# Scalp: weight by direction from the skull centre against a hairline (elevation by azimuth)
shell = F.Face().blocks["shell"]
co = np.empty(len(head.data.vertices) * 3)
head.data.vertices.foreach_get("co", co)
p = co.reshape(-1, 3)[shell.start:shell.stop]
d = p / np.linalg.norm(p, axis=1)[:, None]
az = np.abs(np.arctan2(d[:, 0], -d[:, 1]))
el = np.arcsin(np.clip(d[:, 2], -1, 1))
line = np.interp(az, [0.0, 0.55, 0.95, 1.35, 1.75, 2.2, 2.65, np.pi], [0.66, 0.62, 0.47, 0.36, 0.30, 0.02, -0.24, -0.32])
t = np.clip((el - (line - 0.03)) / 0.08, 0, 1)
w = t * t * (3 - 2 * t)
vg = head.vertex_groups.new(name="Scalp")
for i, wi in enumerate(w):
    if wi > 0.001:
        vg.add([shell.start + i], float(wi), "REPLACE")
print("@@JSON@@" + json.dumps({"ok": True, "surface": head.name, "uv": head.data.uv_layers.active.name,
                               "scalp_verts": int((w > 0.5).sum()), "scalp_soft_edge": int(((w > 0.001) & (w < 0.999)).sum()),
                               "objects": [o.name for o in bpy.data.objects]}))
