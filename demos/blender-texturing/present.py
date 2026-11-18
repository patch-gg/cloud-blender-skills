"""Presentation for blender-texturing: a before/after wipe across the frame.

The smart_material.py layers stay as built; this only gates them. Its TX_Layers amounts (wear, grime,
dust, rust, breakup) are multiplied by a screen-space mask, so left of a moving line the layers are on
and right of it the paint is as clean as the blender-pbr-materials base. The decal's alpha takes the same
mask. Camera, lights and backdrop swing gently about a 3/4 view (frame 97 = frame 1, a seamless loop).
Run in the session after turntable.py: cloud.py run present.py"""
import json
import math

import bpy
from mathutils import Vector

F, CENTER, SWING = 96, -28.0, 8.0   # frames, view azimuth and swing in degrees
EDGE = 0.0015                       # half-width of the wipe edge, in frame widths (~2 px)
INK = (0.92, 0.92, 0.92, 1)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
can = bpy.data.objects["JerryCan"]
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera

# --- camera: closer than the bounding-sphere fit, the can filling ~80% of the height
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
pts = [can.matrix_world @ Vector(c) for c in can.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
target = (lo + hi) / 2
cam.data.lens, cam.data.sensor_fit = 85, "HORIZONTAL"
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
vfov = 2 * math.atan(math.tan(hfov / 2) * 720 / 1280)
dist = (hi.z - lo.z) / 0.8 / (2 * math.tan(vfov / 2))
el = math.radians(15)
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_start, cam.data.clip_end = 0.05, dist * 20
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
# extremes keyed half a cycle outside 1..97, so frame 1 and frame 97 match in value and speed
for f, deg in ((-23, CENTER - SWING), (25, CENTER + SWING), (73, CENTER - SWING), (121, CENTER + SWING)):
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

# --- the wipe: one animated value u (frame x of the line, 0 = left edge) shared by every mask
wipe = bpy.data.node_groups.new("DEMO_Wipe", "ShaderNodeTree")
wipe.interface.new_socket("After", in_out="OUTPUT", socket_type="NodeSocketFloat")
n = wipe.nodes
tc, sep, val = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeSeparateXYZ"), n.new("ShaderNodeValue")
val.name = "U"
mr = n.new("ShaderNodeMapRange")
mr.interpolation_type, mr.clamp = "SMOOTHSTEP", True
lo_e, hi_e = n.new("ShaderNodeMath"), n.new("ShaderNodeMath")
lo_e.operation, hi_e.operation = "SUBTRACT", "ADD"
for m in (lo_e, hi_e):
    wipe.links.new(val.outputs[0], m.inputs[0])
    m.inputs[1].default_value = EDGE
wipe.links.new(tc.outputs["Window"], sep.inputs[0])
wipe.links.new(sep.outputs["X"], mr.inputs["Value"])
wipe.links.new(hi_e.outputs[0], mr.inputs["From Min"])  # left of the line -> 1 (after)
wipe.links.new(lo_e.outputs[0], mr.inputs["From Max"])
go = n.new("NodeGroupOutput")
wipe.links.new(mr.outputs["Result"], go.inputs[0])
KEYS = ((1, -0.01), (9, -0.01), (33, 1.01), (63, 1.01), (87, -0.01), (97, -0.01))  # off-screen at rest
for f, u in KEYS:
    val.outputs[0].default_value = u
    val.outputs[0].keyframe_insert("default_value", frame=f)


def mask_node(nt, x, y):
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree, g.location = wipe, (x, y)
    return g.outputs[0]


def times(nt, a, b, x, y):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation, m.location = "MULTIPLY", (x, y)
    for i, v in enumerate((a, b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, m.inputs[i])
        else:
            m.inputs[i].default_value = v
    return m.outputs[0]


gated = {}
for mat in bpy.data.materials:
    nt = mat.node_tree
    if not nt:
        continue
    for g in [g for g in nt.nodes if g.type == "GROUP" and g.node_tree and g.node_tree.name == "TX_Layers"]:
        mk = mask_node(nt, g.location.x - 520, g.location.y + 300)
        for k in ("Wear", "Grime", "Dust", "Rust", "Breakup"):
            amt = g.inputs[k].default_value
            nt.links.new(times(nt, amt, mk, g.location.x - 300, g.location.y + 300), g.inputs[k])
            gated[k] = round(amt, 3)
dmat = bpy.data.objects["DC_diesel"].active_material
tex = next(x for x in dmat.node_tree.nodes if x.type == "TEX_IMAGE")
bsdf = next(x for x in dmat.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
dmat.node_tree.links.new(times(dmat.node_tree, tex.outputs["Alpha"], mask_node(dmat.node_tree, -600, -300),
                               -200, -300), bsdf.inputs["Alpha"])


# --- overlay in front of the lens: the wipe line and two labels, seen by camera rays only
def overlay(ob, mat):
    ob.data.materials.append(mat)
    sc.collection.objects.link(ob)
    ob.parent = cam
    for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
              "visible_volume_scatter"):
        setattr(ob, k, False)
    return ob


def ink(name, alpha=None):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out, em = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value, em.inputs["Strength"].default_value = INK, 3.0
    if alpha is None:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        return m
    mix, tr = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
    a = mask_node(nt, -500, 200)
    if alpha == "before":
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation, inv.inputs[0].default_value = "SUBTRACT", 1.0
        nt.links.new(a, inv.inputs[1])
        a = inv.outputs[0]
    nt.links.new(a, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


D = 0.5                                    # overlay plane distance in front of the lens
W = 2 * D * math.tan(hfov / 2)             # frame width there (m)
H = W * 720 / 1280
px = W / 1280
lw = 2.2 * px
line = bpy.data.meshes.new("DEMO_WipeLine")
line.from_pydata([(-lw / 2, -H / 2 - px, 0), (lw / 2, -H / 2 - px, 0), (lw / 2, H / 2 + px, 0),
                  (-lw / 2, H / 2 + px, 0)], [], [(0, 1, 2, 3)])
lo_ = overlay(bpy.data.objects.new("DEMO_WipeLine", line), ink("DEMO_Line"))
for f, u in KEYS:
    lo_.location = ((u - 0.5) * W, 0, -D)
    lo_.keyframe_insert("location", index=0, frame=f)
for word, side in (("after", "after"), ("before", "before")):
    cu = bpy.data.curves.new("DEMO_" + word, "FONT")
    cu.body, cu.size = word, 24 * px
    cu.align_x = "LEFT" if side == "after" else "RIGHT"
    t = overlay(bpy.data.objects.new("DEMO_" + word, cu), ink("DEMO_Ink_" + side, side))
    t.location = ((-W / 2 + 44 * px) if side == "after" else (W / 2 - 44 * px), -H / 2 + 40 * px, -D)

# --- stage: dark backdrop, a touch under-exposed so the paint stays red and the bare metal glints
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(x for x in bd.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.7
sc.view_settings.exposure = -1.0
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 3), "gated": gated,
                               "wipe_keys": KEYS}))
