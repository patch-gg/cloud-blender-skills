"""Still life for the render comparison: import the props (GLBs from Patch's asset library) and set them
out in a loose row, a prop on each third of the frame and one across each divider.
Run in the session: cloud.py run scene.py -- <a.glb> <b.glb> ..."""
import json
import math
import sys

import bpy

# x: left to right across the frame, y: depth (away from the camera), z-rotation in degrees
PLACE = {
    "potted_plant_04": (-0.42, 0.04, 40),
    "antique_ceramic_vase_01": (-0.21, 0.14, 35),    # across the workbench | eevee divider
    "brass_goblets": (-0.02, -0.11, 0),              # the three goblets keep their own layout
    "wine_bottles_01_burgundy": (0.225, -0.03, -20),  # across the eevee | cycles divider
    "wine_bottles_01_alsace": (0.33, 0.13, 0),
    "brass_vase_03": (0.45, -0.13, 15),
}
DROP = ("wine_bottles_01_bordeaux", "wine_bottles_01_champagne")

paths = sys.argv[sys.argv.index("--") + 1:]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
props = []
for p in paths:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    group = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    for o in new:
        if o.name in DROP:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        key = o.name if o.name in PLACE else group
        x, y, rz = PLACE[key]
        if key == group and len(new) > 1 and group != "potted_plant_04":
            o.location.x += x            # a set (the goblets): move it as one, keep its layout
            o.location.y += y
        else:
            o.location.x, o.location.y = x, y
            o.rotation_euler.z = math.radians(rz)
        if group == "potted_plant_04":   # the plant's parts share one origin: turn them together
            o.location.x, o.location.y = x + o.location.x * 0, y
            o.rotation_euler.z = math.radians(rz)
        props.append(o.name)
bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": True, "props": props}))
