"""Presentation: the tidied props in a row, framed by width, each with a placard. Before: the default name
and what the audit caught, in pink. Then the placards flip, left to right, to the clean names in dark grey,
and the scene line flips from the units/orphans/root problems to the fixed state. 1280x720, 120 frames.

Run in the session after turntable.py: cloud.py run present.py -- labels.json
labels.json: {"items": [{"name", "before", "problem"}], "scene_before": str, "scene_after": str}
"""
import json
import math
import sys

import bpy
from mathutils import Vector

FRAMES, FLIP, STAGGER, HALF = 120, 50, 4, 3      # flips start at FLIP, one placard every STAGGER frames
PINK = (0.913, 0.045, 0.638)                      # #F53CD1, linear
DARK = (0.0056, 0.0056, 0.0056)                   # #111

spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
props = [bpy.data.objects[i["name"]] for i in spec["items"]]
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera
bpy.context.view_layer.update()


def bounds(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    return (Vector(min(p[i] for p in pts) for i in range(3)), Vector(max(p[i] for p in pts) for i in range(3)))


def mat(name, color, emit):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.6
    if emit:                                      # pink stays pink under the studio lights
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


M_PINK, M_DARK = mat("FX_Pink", PINK, 1.5), mat("FX_Dark", DARK, 0)
fx = bpy.data.collections.get("FX") or bpy.data.collections.new("FX")
if fx.name not in sc.collection.children:
    sc.collection.children.link(fx)


def text(name, body, size, loc, m):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x = body, size, "CENTER"
    cu.materials.append(m)
    t = bpy.data.objects.new(name, cu)
    t.location, t.rotation_euler = loc, (math.pi / 2, 0, 0)   # a placard standing on the floor
    t.visible_shadow = False
    fx.objects.link(t)
    return t


def flip(objs_out, objs_in, f):
    """Flip-board: the old placard folds flat (scale z 1 -> 0), then the new one unfolds (0 -> 1)."""
    for t in objs_out:
        for k, s in ((1, 1), (f, 1), (f + HALF, 0)):
            t.scale = (1, s, 1)
            t.keyframe_insert("scale", index=1, frame=k)
    for t in objs_in:
        for k, s in ((1, 0), (f + HALF, 0), (f + 2 * HALF, 1)):
            t.scale = (1, s, 1)
            t.keyframe_insert("scale", index=1, frame=k)


lo, hi = bounds(props)
y_card = lo.y - 0.75                              # well in front, so placards sit below the props
for i, (ob, it) in enumerate(zip(props, spec["items"])):
    plo, phi = bounds([ob])
    x = (plo.x + phi.x) / 2
    before = [text(f"FX_Before_{i}", it["before"], 0.11, (x, y_card, 0.115), M_PINK),
              text(f"FX_Problem_{i}", it["problem"], 0.08, (x, y_card, 0.012), M_PINK)]
    after = [text(f"FX_After_{i}", it["name"], 0.11, (x, y_card, 0.06), M_DARK)]
    flip(before, after, FLIP + i * STAGGER)
f_scene = FLIP + len(props) * STAGGER
line_before = text("FX_Scene_Before", spec["scene_before"], 0.08, ((lo.x + hi.x) / 2, y_card - 0.7, 0.012), M_PINK)
line_after = text("FX_Scene_After", spec["scene_after"], 0.08, ((lo.x + hi.x) / 2, y_card - 0.7, 0.012), M_DARK)
flip([line_before], [line_after], f_scene)

# camera: frame the row by its width (a turntable fits a sphere and leaves 16:9 half empty)
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
width = (hi.x - lo.x) + 0.7
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(15)
target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2 - 0.8, 0.2))
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((1, -5), (FRAMES, 5)):             # a slow swing so the props turn a little
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.1, 0.1, 0.105, 1)
    b.inputs["Roughness"].default_value = 0.75
sc.view_settings.view_transform = "Khronos PBR Neutral"   # keeps #F53CD1 pink; AgX turns it pastel
sc.view_settings.look = "None"
sc.view_settings.exposure = -1.0
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 3, 8
sc.frame_set(30)                                  # looks show the "before"
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "flips": [FLIP + i * STAGGER for i in range(len(props))]
                               + [f_scene], "distance": round(dist, 2)}))
