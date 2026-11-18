"""Glue for the outdoor forks: drop the studio lights so the sky and sun scene_mood.py makes are the
only light. Run before scene_mood.py."""
import json

import bpy

gone = [o.name for o in bpy.data.objects if o.name in ("LD_Key", "LD_Fill", "LD_Rim")]
for n in gone:
    bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
print("@@JSON@@" + json.dumps({"ok": True, "removed": gone}))
