"""Presentation: the strand groom and its game cards side by side, each bust spinning once in step (96 frames,
seamless) under turntable.py's studio rig held still, with a small label under each. Hair Dynamics is switched off:
nothing should simulate in a turntable (SKILL.md: bake it before animated renders). Cycles gets extra transparent
bounces for the layered cards. Run in the session after groom.py --cards and turntable.py: cloud.py run present.py"""
import json
import math

import bpy
from bpy_extras import anim_utils
from mathutils import Matrix, Vector

FRAMES = 96
GAP = 0.40                          # bust centres apart (m)
INK = (0.006, 0.006, 0.006)
BACKDROP = (0.30, 0.30, 0.31)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
hair, cards, head = (bpy.data.objects[n] for n in ("Hair", "Hair_Cards", "Head"))
for md in hair.modifiers:
    if md.type == "NODES" and md.node_group and "Dynamics" in md.node_group.name:
        md.show_viewport = md.show_render = False

# strands as rendered (the session evaluates the viewport amount)
interp = next(md for md in hair.modifiers if md.node_group and md.node_group.name == "Interpolate Hair Curves")
amount = next(i for i in interp.node_group.interface.items_tree
              if getattr(i, "in_out", "") == "INPUT" and i.name == "Viewport Amount")
sock = getattr(interp.properties.inputs, amount.identifier)
viewport = sock.value
sock.value = 1.0
bpy.context.view_layer.update()
strands = len(hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.curves)
sock.value = viewport
tris = sum(len(p.vertices) - 2 for p in cards.data.polygons)

# the cards get their own copy of the bust (meshes shared), so both spin side by side
spin = {}
for side, x in (("strands", -GAP / 2), ("cards", GAP / 2)):
    e = bpy.data.objects.new(f"Spin_{side}", None)
    sc.collection.objects.link(e)
    e.location = (x, 0, 0)
    spin[side] = e
copies = {}
for name in ("Head", "EyeL", "EyeR", "Neck", "Body"):
    ob = bpy.data.objects[name]
    c = ob.copy()
    c.name = name + "_cards"
    sc.collection.objects.link(c)
    copies[name] = c
for name in ("EyeL", "EyeR"):
    copies[name].parent = copies["Head"]
pinv = cards.matrix_parent_inverse.copy()           # setting .parent resets it: keep groom.py's, same place
cards.parent = copies["Head"]
cards.matrix_parent_inverse = pinv
bpy.context.view_layer.update()
for name in ("Head", "Neck", "Body"):
    for ob, side in ((bpy.data.objects[name], "strands"), (copies[name], "cards")):
        ob.parent = spin[side]
        ob.matrix_parent_inverse = Matrix.Identity(4)
for e in spin.values():
    e.rotation_euler = (0, 0, 0)
    e.keyframe_insert("rotation_euler", index=2, frame=1)
    e.rotation_euler = (0, 0, 2 * math.pi)
    e.keyframe_insert("rotation_euler", index=2, frame=FRAMES + 1)   # frame 121 = frame 1
    bag = anim_utils.action_get_channelbag_for_slot(e.animation_data.action, e.animation_data.action_slot)
    for fc in bag.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# camera: still, framing both busts by their width
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
cam = sc.camera
cam.parent = None
cam.data.lens = 85
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
vfov = 2 * math.atan(cam.data.sensor_width * 9 / 16 / 2 / cam.data.lens)
width = GAP + 0.40
dist = width / 2 / math.tan(hfov / 2)
target = Vector((0, 0, 0.335))
el = math.radians(4)
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, 50

# labels under each bust, fixed to the camera
ink = bpy.data.materials.new("M_Label")
nt = ink.node_tree
nt.nodes.clear()
em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value = (*INK, 1)
nt.links.new(em.outputs[0], out.inputs["Surface"])
D = 0.5
half_h = D * math.tan(vfov / 2)
px = 2 * half_h / 720
fonts = bpy.utils.system_resource("DATAFILES") + "/fonts/DejaVuSansMono.woff2"
try:
    font = bpy.data.fonts.load(fonts, check_existing=True)
except RuntimeError:
    font = None
labels = {"strands": f"strands · {strands:,}", "cards": f"cards · {tris:,} tris"}
for side, text in labels.items():
    cu = bpy.data.curves.new(f"Label_{side}", "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = text, 30 * px, "CENTER", "BOTTOM"
    cu.offset = 0.6 * px
    if font:
        cu.font = font
    cu.materials.append(ink)
    t = bpy.data.objects.new(f"Label_{side}", cu)
    sc.collection.objects.link(t)
    t.parent = cam
    x = (GAP / 2 if side == "cards" else -GAP / 2) * D / dist        # under each bust's centre
    t.location = (x, -half_h + 40 * px, -D)

# the stage
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*BACKDROP, 1)
sc.render.engine = "CYCLES"
sc.cycles.transparent_max_bounces = 48              # layered alpha cards
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": FRAMES, "strands_rendered": strands,
                               "strands_in_session": len(hair.evaluated_get(
                                   bpy.context.evaluated_depsgraph_get()).data.curves),
                               "card_tris": tris, "labels": list(labels.values()), "distance": round(dist, 3)}))
