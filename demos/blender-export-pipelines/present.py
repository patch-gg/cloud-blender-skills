"""Presentation: a still camera framing the two rows by their width, the six re-imported copies spinning
in sync on their own axes (one turn over 96 frames; frame 97 = frame 1, so 1-96 loops), the step in the
backdrop's light grey, AgX. 1280x720. Run in the session after turntable.py: cloud.py run present.py"""
import json
import math

import bpy
from bpy_extras import anim_utils
from mathutils import Vector

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100

# turntable.py orbits camera + lights; here they hold still and the copies turn instead
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()

spins = sorted((o for o in bpy.data.objects if o.name.startswith("Spin_")), key=lambda o: o.name)
for e in spins:
    e.animation_data_clear()
    for f, turn in ((1, 0.0), (97, 1.0)):
        e.rotation_euler = (0, 0, math.radians(-38) + turn * 2 * math.pi)  # starts in a 3/4 pose
        e.keyframe_insert("rotation_euler", index=2, frame=f)
    ad = e.animation_data
    for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"

# frame the two rows by their width (a spinning copy sweeps a circle of ~0.19 m)
xs = [e.location.x for e in spins]
width = (max(xs) - min(xs)) + 2 * 0.19 + 0.62
cam = sc.camera
cam.parent = None
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(13)
target = Vector((0, 0.2, 0.30))
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, 60

# one light grey for the cyclorama and the step
bd = bpy.data.materials["LD_Backdrop"]
b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.42, 0.42, 0.42, 1)
b.inputs["Roughness"].default_value = 0.85
b.inputs["Specular IOR Level"].default_value = 0.0   # a matte set: no mirrored labels in the floor
riser = bpy.data.objects["Riser"]
riser.data.materials.clear()
riser.data.materials.append(bd)

sc.render.engine = "BLENDER_EEVEE"
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 3, 12   # smooth soft shadows from the big lights
for lo in (o for o in bpy.data.objects if o.type == "LIGHT"):
    lo.data.shadow_filter_radius = 2.0
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Punchy"
except TypeError:
    pass
sc.view_settings.exposure = -0.7
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "lens": cam.data.lens, "distance": round(dist, 2),
                               "spinning": [e.name for e in spins]}))
