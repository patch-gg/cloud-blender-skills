"""Presentation glue, run before the fixes: keep a hidden copy of the broken asset (its own mesh data, the
qa_problem tags included) in a QA_Before collection, so the clip can show the broken and the fixed state.

Run in the session: cloud.py run snapshot.py
"""
import json

import bpy

src = bpy.data.collections["Barrel"]
dst = bpy.data.collections.get("QA_Before") or bpy.data.collections.new("QA_Before")
if dst.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(dst)
names = []
for ob in src.objects:
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = "Before_" + ob.name
    c.hide_viewport = c.hide_render = True        # present.py shows them for the first half
    dst.objects.link(c)
    names.append(c.name)
print("@@JSON@@" + json.dumps({"ok": True, "copies": names}))
