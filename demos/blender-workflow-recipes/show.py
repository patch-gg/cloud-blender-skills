"""Show only the named objects (and the look-dev rig); hide every other part, copy and cutter, in the
viewport and in renders. Run in the session: cloud.py run show.py -- Name1 Name2 ..."""
import json
import sys

import bpy

keep = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
missing = sorted(n for n in keep if n not in bpy.data.objects)
for ob in bpy.context.scene.objects:
    if ob.name.startswith("LD_") or ob.type in ("CAMERA", "LIGHT"):
        continue
    vis = ob.name in keep
    ob.hide_render = not vis
    ob.hide_set(not vis)
print("@@JSON@@" + json.dumps({"ok": not missing, "shown": sorted(keep), "missing": missing}))
