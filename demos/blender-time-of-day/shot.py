"""Per time of day: the label's words, the lighthouse lamp (lantern + window glow, the two rotating beams
and a warm point light on the gallery) and an optional exposure offset from scene_mood.py's metered one
(blue hour exposed for the sky). Practicals keep fixed wattages; scene_mood.py balances the sky and sun or
moon around them. Run in the session after scene_mood.py:
    cloud.py run shot.py -- --label "blue hour" --lamp 2 --exposure -1.5
"""
import argparse
import json
import sys

import bpy

ap = argparse.ArgumentParser()
ap.add_argument("--label", default="")
ap.add_argument("--lamp", type=float, default=0.0, help="0 off, 1 on (2 = twice as bright)")
ap.add_argument("--beam", type=float, default=1.2e6, help="W per beam (they show only in fog)")
ap.add_argument("--glow", type=float, default=300.0, help="W, the point light by the lantern")
ap.add_argument("--exposure", type=float, default=0.0, help="EV added to scene_mood.py's exposure")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

bpy.data.objects["Label"].data.body = a.label
nt = bpy.data.materials["M_Lighthouse"].node_tree
nt.nodes["Lamp"].outputs[0].default_value = a.lamp
for n in ("Lamp_Beam0", "Lamp_Beam1"):
    bpy.data.lights[n].energy = a.beam * a.lamp
bpy.data.lights["Lamp_Glow"].energy = a.glow * a.lamp
vs = bpy.context.scene.view_settings
vs.exposure += a.exposure  # scene_mood.py sets it on every run, so this never accumulates
print("@@JSON@@" + json.dumps({"ok": True, "label": a.label, "lamp": a.lamp,
                               "beam_w": a.beam * a.lamp, "glow_w": a.glow * a.lamp,
                               "exposure": round(vs.exposure, 2)}))
