"""Glue for the night fork: a warm street lamp beside the hydrant, the light a night street really has."""
import json

import bpy

d = bpy.data.lights.new("Streetlamp", "POINT")
d.energy, d.color, d.shadow_soft_size = 180.0, (1.0, 0.72, 0.42), 0.15
lamp = bpy.data.objects.new("Streetlamp", d)
lamp.location = (-0.9, -1.1, 2.4)
bpy.context.scene.collection.objects.link(lamp)
print("@@JSON@@" + json.dumps({"ok": True, "light": lamp.name, "watts": d.energy}))
