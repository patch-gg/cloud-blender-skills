"""The triptych: each engine's frames side by side (workbench | eevee | cycles), split where the dividers
cross a prop, with a thin seam and a small label per band. A VSE-only scene saved as compose/demo.blend;
its image strips read //../<engine>/render/f_####.png, the PNGs d.render leaves beside each engine's .blend
in the GPU box, so rendering this file there composes them losslessly.
Run in a separate Blender: cloud.py run --process compose.py -- --split 0.35 0.68 --frames 96"""
import argparse
import json
import os
import sys

import bpy

p = argparse.ArgumentParser()
p.add_argument("--split", nargs=2, type=float, required=True, help="divider x positions, 0..1 of the width")
p.add_argument("--frames", type=int, default=96)
p.add_argument("--out", default="compose/demo.blend")
o = p.parse_args(sys.argv[sys.argv.index("--") + 1:])

W, H = 1280, 720
INK = (0.067, 0.067, 0.067, 1)  # #111 (strip colours are display values)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, o.frames
sc.render.use_sequencer = True
sc.view_settings.view_transform = "Standard"  # the frames are already display-ready: pass them through
sc.view_settings.look = "None"
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))  # render_batch.py wants a camera
sc.collection.objects.link(cam)
sc.camera = cam

se = sc.sequence_editor_create()
x1, x2 = round(o.split[0] * W), round(o.split[1] * W)
bands = (("cycles", x2, W), ("eevee", x1, x2), ("workbench", 0, x1))  # bottom channel first


def frames(name, channel, left, right):
    s = se.strips.new_image(f"{name}_{channel}", f"//../{name}/render/f_0001.png", channel, 1)
    for f in range(2, o.frames + 1):
        s.elements.append(f"f_{f:04d}.png")
    s.crop.min_x, s.crop.max_x = left, W - right  # keep only this band, in place
    return s


for ch, (name, left, right) in enumerate(bands, start=1):
    # 0.999, not 1: Blender 5.2's VSE treats an opaque strip as covering the frame even when cropped
    # and then skips every strip below it
    frames(name, ch, left, right).blend_alpha = 0.999
for i, x in enumerate((x1, x2)):  # the seams: 2 px of white (5.2 drops colour strips once cropped)
    s = frames("cycles", 4 + i, x - 1, x + 1)
    s.modifiers.new("white", "BRIGHT_CONTRAST").bright = 100
    s.blend_alpha = 0.85
font = bpy.data.fonts.load(os.path.join(bpy.utils.resource_path("LOCAL"), "datafiles", "fonts", "Inter.woff2"))
font.pack()  # Blender's own UI font, carried inside the .blend
for i, (name, left, right) in enumerate(bands):
    t = se.strips.new_effect(f"label_{name}", "TEXT", 6 + i, 1, length=o.frames)
    t.text, t.font = name, font
    t.font_size = 22
    t.color = INK
    t.anchor_x, t.anchor_y = "CENTER", "BOTTOM"
    t.location = ((left + right) / 2 / W, 24 / H)

out = o.out if os.path.isabs(o.out) else os.path.join(os.getcwd(), o.out)
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False)
print("@@JSON@@" + json.dumps({"ok": True, "saved": o.out, "split_px": [x1, x2], "frames": o.frames,
                               "strips": len(se.strips)}))
