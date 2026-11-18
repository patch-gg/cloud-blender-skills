"""Presentation: frame the still life by its width, warm the key light and cool the fill, a warm grey
backdrop, a slow camera sway (+-10 degrees, a seamless 96-frame loop) and a Workbench look worth comparing
(studio light, textures, cavity, shadows). AgX for EEVEE and Cycles. Prints where the two dividers go: the
screen x of the props they cross. Run after turntable.py."""
import json
import math

import bpy
from bpy_extras import anim_utils
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
props = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("LD_")]
pts = [o.matrix_world @ Vector(c) for o in props for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
cam = sc.camera
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
width = (hi.x - lo.x) * 1.3
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(8)
target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + (hi.z - lo.z) * 0.44))
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, 100
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, 0), (25, 10), (49, 0), (73, -10), (97, 0)):  # frame 97 = frame 1
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)
ad = pivot.animation_data
for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
    fc.modifiers.new("CYCLES")  # cyclic auto handles: no ease-out hitch where the loop wraps
    fc.update()
# lights: a warm key, a cool fill, a soft rim
for name, color, k in (("LD_Key", (1.0, 0.8, 0.62), 0.9), ("LD_Fill", (0.7, 0.82, 1.0), 0.3),
                       ("LD_Rim", (1.0, 0.92, 0.82), 0.45)):
    ld = bpy.data.objects[name].data
    ld.color, ld.energy = color, ld.energy * k
bd = bpy.data.objects["LD_Backdrop"].active_material
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.045, 0.037, 0.032, 1)
    b.inputs["Roughness"].default_value = 0.75
    bd.diffuse_color = (0.85, 0.75, 0.66, 1)  # Workbench's colour: lands near the tone the lit backdrop renders
# Workbench: what the viewport's solid mode shows, made deliberate
sh = sc.display.shading
sh.light, sh.studio_light = "STUDIO", "paint.sl"
sh.color_type = "TEXTURE"
sh.show_cavity, sh.cavity_type = True, "BOTH"
sh.show_shadows, sh.shadow_intensity = True, 0.55
sh.show_specular_highlight = True
sc.display.light_direction = (-0.55, -0.45, 0.7)
sc.display.render_aa = "16"
# EEVEE: ray-traced reflections/refraction come from the render preset; soft shadows here
sc.eevee.use_shadows = True
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.view_settings.exposure = 0.0
sc.frame_set(1)
split = []
for name in ("antique_ceramic_vase_01", "wine_bottles_01_burgundy"):
    ob = bpy.data.objects[name]
    c = ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8)
    split.append(round(world_to_camera_view(sc, cam, c).x, 4))
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 3),
                               "width": round(width, 3), "props": len(props), "split": split}))
