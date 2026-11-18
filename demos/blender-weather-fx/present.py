"""Presentation: expose the rainy night for its lamps, not for scene_mood.py's grey card. The metered exposure
keeps an ambient-lit grey card at the preset's brightness, which leaves the overcast sky and fog five times
brighter than that card, and the wet road mirrors it white. So: exposure EV under the metered one, and the
practicals (lamp bulbs, lamp glass, lit windows) at absolute, brighter values. Optional small label.
Run in the session after scene_mood.py:
    cloud.py run present.py -- --exposure -3 --lamp-w 1500 --glass 40 --windows 18
"""
import argparse
import json
import sys

import bpy

ap = argparse.ArgumentParser()
ap.add_argument("--exposure", type=float, default=-3.0, help="EV added to scene_mood.py's exposure")
ap.add_argument("--lamp-w", type=float, default=1500.0)
ap.add_argument("--glass", type=float, default=40.0, help="lamp glass emission strength")
ap.add_argument("--windows", type=float, default=18.0, help="lit window emission strength")
ap.add_argument("--label", default="")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

sc = bpy.context.scene
sc.view_settings.exposure += a.exposure  # scene_mood.py sets it on every run
for ld in [l for l in bpy.data.lights if l.name.endswith("_Bulb")]:
    ld.energy = a.lamp_w
for m in bpy.data.materials:
    if m.name.startswith("street_lamp_01_glass"):
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Emission Strength"].default_value = a.glass
    if "facade_glass" in m.name:
        mul = next((n for n in m.node_tree.nodes if n.type == "MATH" and n.operation == "MULTIPLY"), None)
        if mul:
            mul.inputs[1].default_value = a.windows
labels = []
if a.label:  # small white text, bottom left, 1 m in front of the lens
    cam = sc.camera
    cd = cam.data
    half_w = 0.5 * cd.sensor_width / cd.lens
    half_h = half_w * sc.render.resolution_y / sc.render.resolution_x
    lm = bpy.data.materials.get("M_Label") or bpy.data.materials.new("M_Label")
    nt = lm.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.0 * 2 ** -a.exposure  # reads white whatever the exposure
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    cu = bpy.data.curves.get("Label") or bpy.data.curves.new("Label", "FONT")
    cu.body, cu.size, cu.align_x = a.label, half_h * 2 * 0.034, "LEFT"
    if not cu.materials:
        cu.materials.append(lm)
    t = bpy.data.objects.get("Label") or bpy.data.objects.new("Label", cu)
    if t.name not in sc.collection.objects:
        sc.collection.objects.link(t)
    t.parent = cam
    t.location = (-half_w + half_w * 2 * 0.035, -half_h + half_h * 2 * 0.06, -1.0)
    t.visible_shadow = False
    for vis in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(t, vis, False)
    labels.append(t.name)
print("@@JSON@@" + json.dumps({"ok": True, "exposure": round(sc.view_settings.exposure, 2), "lamp_w": a.lamp_w,
                               "glass": a.glass, "windows": a.windows, "labels": labels}))
