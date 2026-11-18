"""Glue for the studio fork: the turntable's backdrop stands in for the ground."""
import json

import bpy

bpy.data.objects["Ground"].hide_render = True
print("@@JSON@@" + json.dumps({"ok": True}))
