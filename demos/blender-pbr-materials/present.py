"""Presentation: frame the row by its width, keep the HDRI still and swing the camera and lights gently
(+-16 degrees) so reflections slide across the metals. 1280x720, frames 1-96, a seamless loop.
Swinging the camera, not the HDRI, keeps Cycles fast: a moving world rebuilds its light map every frame."""
import json
import math

import bpy
from mathutils import Vector

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
balls = [o for o in bpy.data.objects if o.name.startswith("Ball_")]
xs = [o.location.x for o in balls]
width = (max(xs) - min(xs)) + 0.84 + 0.9
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(7)
target = pivot.location.copy()  # the row's centre; moving the pivot would move the backdrop and lights too
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, 0), (25, 16), (49, 0), (73, -16), (97, 0)):  # frame 97 = frame 1
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.04, 0.04, 0.045, 1)
    b.inputs["Roughness"].default_value = 0.7
sc.view_settings.exposure = -1.0
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "lens": cam.data.lens, "distance": round(dist, 2)}))
