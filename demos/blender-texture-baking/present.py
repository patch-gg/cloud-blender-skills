"""Presentation for blender-texture-baking: frame the row (high | low | low + bake) by its width, swing
camera and lights gently (+-14 degrees) so the baked normals catch the light the way the real geometry
does, and show three of the baked maps small along the bottom (normal, ao, curvature), as images.

Principled has no AO input (build_pbr_material.py routes AO to the glTF output only), so for display the
baked AO multiplies the baked base colour here, as a game engine's ambient term would.
Frames 1-96, frame 97 = frame 1. Run in the session after turntable.py: cloud.py run present.py"""
import json
import math
import os

import bpy
from mathutils import Vector

F, SWING, EXPOSURE = 96, 14.0, -1.5
TILES = (("normal", "T_Crate_N.png"), ("ao", "T_Crate_AO.png"), ("curvature", "T_Crate_CURV.png"))
TEX = "/work/textures"

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
pivot = bpy.data.objects["LD_Pivot"]
cam = sc.camera

# --- AO into the baked base colour (display only)
mat = bpy.data.objects["Crate_baked"].active_material
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
sep = next(n for n in nt.nodes if n.type == "SEPARATE_COLOR")      # ORM: R = AO
base = bsdf.inputs["Base Color"].links[0].from_socket
mul = nt.nodes.new("ShaderNodeMix")
mul.data_type, mul.blend_type, mul.location = "RGBA", "MULTIPLY", (bsdf.location.x - 220, bsdf.location.y + 300)
mul.inputs[0].default_value = 1.0
nt.links.new(base, mul.inputs[6])
nt.links.new(sep.outputs["Red"], mul.inputs[7])
nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])

# --- camera: frame the row by its width, lifted a little (shift) to leave the bottom for the maps
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
row = [bpy.data.objects[n] for n in ("Crate_high", "Crate_bolts", "Crate_low", "Crate_baked")]
pts = [o.matrix_world @ Vector(c) for o in row for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
target = (lo + hi) / 2
width = (hi.x - lo.x) + 0.75
cam.data.lens, cam.data.sensor_fit, cam.data.dof.use_dof = 50, "HORIZONTAL", False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
dist = width / 2 / math.tan(hfov / 2)
el = math.radians(13)
cam.parent = None
cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * dist
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.shift_y = -0.085
cam.data.clip_start, cam.data.clip_end = 0.05, dist * 10
bpy.context.view_layer.update()
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
for f, deg in ((-23, -SWING), (25, SWING), (73, -SWING), (121, SWING)):   # extremes outside 1..97
    pivot.rotation_euler = (0, 0, math.radians(deg))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f)

# --- the maps, small, in front of the lens (camera rays only), each with its name under it
D = 0.5
W = 2 * D * math.tan(hfov / 2)
px = W / 1280
tw, th, gap, bottom = 168 * px, 112 * px, 16 * px, 58 * px    # tile size (3:2, the used UV rows)
x0 = -(3 * tw + 2 * gap) / 2


def camera_only(ob):
    for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
              "visible_volume_scatter"):
        setattr(ob, k, False)
    ob.parent = cam
    sc.collection.objects.link(ob)


def emission(name, image=None, color=(0.8, 0.8, 0.8, 1)):
    m = bpy.data.materials.new(name)
    t = m.node_tree
    t.nodes.clear()
    out, em = t.nodes.new("ShaderNodeOutputMaterial"), t.nodes.new("ShaderNodeEmission")
    if image:
        tex = t.nodes.new("ShaderNodeTexImage")
        tex.image, tex.interpolation = image, "Cubic"
        t.links.new(tex.outputs["Color"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = 2 ** -EXPOSURE   # shown as the file is, whatever the exposure
    t.links.new(em.outputs[0], out.inputs["Surface"])
    return m


# the frame's centre in lens space moves with shift_y: the visible window is offset by shift * width
cy = cam.data.shift_y * W
for i, (word, fn) in enumerate(TILES):
    img = bpy.data.images.load(os.path.join(TEX, fn), check_existing=False)   # a display copy, shown as sRGB
    img.colorspace_settings.name = "sRGB"
    me = bpy.data.meshes.new("DEMO_Tile_" + word)
    x = x0 + i * (tw + gap)
    y = cy - W * 720 / 1280 / 2 + bottom
    me.from_pydata([(x, y, -D), (x + tw, y, -D), (x + tw, y + th, -D), (x, y + th, -D)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, (u, v) in zip(me.loops, ((0, 1 / 3), (1, 1 / 3), (1, 1), (0, 1))):   # the 3x2 islands
        uv.data[lp.index].uv = (u, v)
    me.materials.append(emission("DEMO_Tile_" + word, img))
    camera_only(bpy.data.objects.new("DEMO_Tile_" + word, me))
    cu = bpy.data.curves.new("DEMO_TileLabel", "FONT")
    cu.body, cu.size, cu.align_x = word, 19 * px, "CENTER"
    cu.materials.append(emission("DEMO_TileInk", color=(0.85, 0.85, 0.85, 1)))
    lab = bpy.data.objects.new("DEMO_TileLabel", cu)
    lab.location = (x + tw / 2, y - 26 * px, -D)
    camera_only(lab)

# --- stage: a dark backdrop, colours shown as they are (Khronos PBR Neutral), the scene a stop and a half down
bd = bpy.data.materials.get("LD_Backdrop")
if bd:
    b = next(x for x in bd.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.04, 0.04, 0.045, 1)
    b.inputs["Roughness"].default_value = 0.7
try:
    sc.view_settings.view_transform = "Khronos PBR Neutral"
except TypeError:
    pass
sc.view_settings.look = "None"
sc.view_settings.exposure = EXPOSURE
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 2), "tiles": [t[0] for t in TILES]}))
