"""Glue: shift the scene's exposure by N stops (after scene_mood.py, which sets its own balance).
Usage: cloud.py run expose.py -- -0.8"""
import json
import sys

import bpy

ev = float(sys.argv[sys.argv.index("--") + 1])
vs = bpy.context.scene.view_settings
vs.exposure += ev
print("@@JSON@@" + json.dumps({"ok": True, "exposure": round(vs.exposure, 3)}))
