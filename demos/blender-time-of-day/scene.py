"""A lighthouse on a rocky islet in a calm sea, with its lamp (lantern + windows glow, two rotating beams)
ready to switch on, a slow camera arc and one small label. Lighting is left to scene_mood.py; shot.py sets
the label and the lamp for each time of day. Run in the session:
    cloud.py run scene.py -- --lighthouse lh.glb --rocks a.glb b.glb ...
"""
import argparse
import json
import math
import random
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--lighthouse", required=True)
ap.add_argument("--rocks", nargs="*", default=[])
ap.add_argument("--frames", type=int, nargs=2, default=(1, 120))
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
f0, f1 = a.frames
sc.frame_start, sc.frame_end, sc.render.fps = f0, f1, 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.engine = "CYCLES"
sc.view_settings.view_transform = "AgX"  # scene_mood.py runs with --keep-view and keeps this
sc.view_settings.look = "AgX - Medium High Contrast"
cy = sc.cycles
cy.volume_biased, cy.volume_step_rate = True, 0.05  # ray-marched night fog: no speckle from the lamp
cy.sample_clamp_indirect = 4.0
edit = bpy.context.preferences.edit
interp, edit.keyframe_new_interpolation_type = edit.keyframe_new_interpolation_type, "LINEAR"


def imported(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    meshes = [o for o in new if o.type == "MESH"]
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


# --- lighthouse: 16 m tall (the asset's size is estimated), base on z = 0
lh = imported(a.lighthouse)
lh.name = lh.data.name = "Lighthouse"
H = 16.0
s = H / lh.dimensions.z
for v in lh.data.vertices:
    v.co *= s
lh.data.update()
mat = lh.data.materials[0]
mat.name = "M_Lighthouse"
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.75
attr = next(n for n in nt.nodes if n.type == "VERTEX_COLOR")
# lamp glow: the lantern glass (0.64, 0.62, 0.5) and the windows (0.05, 0.07, 0.1) emit when the lamp is on


def near(rgb, tol=0.03):
    d = nt.nodes.new("ShaderNodeVectorMath")
    d.operation = "DISTANCE"
    nt.links.new(attr.outputs["Color"], d.inputs[0])
    d.inputs[1].default_value = rgb
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    nt.links.new(d.outputs["Value"], lt.inputs[0])
    lt.inputs[1].default_value = tol
    return lt.outputs[0]


lamp = nt.nodes.new("ShaderNodeValue")
lamp.name = lamp.label = "Lamp"  # shot.py sets 0 (off) or 1 (on)
lamp.outputs[0].default_value = 0.0
glass = nt.nodes.new("ShaderNodeMath")
glass.operation = "MULTIPLY"
nt.links.new(near((0.64, 0.62, 0.5)), glass.inputs[0])
glass.inputs[1].default_value = 40.0
win = nt.nodes.new("ShaderNodeMath")
win.operation = "MULTIPLY"
nt.links.new(near((0.05, 0.07, 0.1)), win.inputs[0])
win.inputs[1].default_value = 6.0
both = nt.nodes.new("ShaderNodeMath")
both.operation = "ADD"
nt.links.new(glass.outputs[0], both.inputs[0])
nt.links.new(win.outputs[0], both.inputs[1])
on = nt.nodes.new("ShaderNodeMath")
on.operation = "MULTIPLY"
nt.links.new(both.outputs[0], on.inputs[0])
nt.links.new(lamp.outputs[0], on.inputs[1])
bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.42, 1)  # warm tungsten ~2900 K
nt.links.new(on.outputs[0], bsdf.inputs["Emission Strength"])

# lantern centre and radius, from the glass faces
co = lh.data.color_attributes["Color"]
gl = [p for p in lh.data.polygons
      if (Vector(co.data[p.loop_start].color[:3]) - Vector((0.64, 0.62, 0.5))).length < 0.03]
zc = sum(p.center.z for p in gl) / len(gl)
cx = sum(p.center.x for p in gl) / len(gl)
cy = sum(p.center.y for p in gl) / len(gl)
r_glass = max(math.hypot(p.center.x - cx, p.center.y - cy) for p in gl)
centre = Vector((cx, cy, zc))

# beams: two spots back to back just outside the glass, on a rig turning once every 3 s
rig = bpy.data.objects.new("Lamp_Rig", None)
sc.collection.objects.link(rig)
rig.location = centre
for i, ang in enumerate((0.0, math.pi)):
    ld = bpy.data.lights.new(f"Lamp_Beam{i}", "SPOT")
    ld.energy, ld.spot_size, ld.spot_blend = 0.0, math.radians(9), 0.25
    ld.color, ld.shadow_soft_size = (1.0, 0.86, 0.7), 0.25
    ob = bpy.data.objects.new(f"Lamp_Beam{i}", ld)
    sc.collection.objects.link(ob)
    ob.parent = rig
    d = Vector((math.cos(ang), math.sin(ang), -0.04))  # aimed a touch below the horizon: it sweeps the water
    ob.location = d.normalized() * (r_glass + 0.15)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
rig.rotation_euler = (0, 0, 0)
rig.keyframe_insert("rotation_euler", index=2, frame=f0)
rig.rotation_euler = (0, 0, 2 * math.pi * (f1 - f0) / 72)
rig.keyframe_insert("rotation_euler", index=2, frame=f1)
glow = bpy.data.lights.new("Lamp_Glow", "POINT")  # light on the gallery and the tower top
glow.energy, glow.color, glow.shadow_soft_size = 0.0, (1.0, 0.75, 0.45), 0.3
gob = bpy.data.objects.new("Lamp_Glow", glow)
sc.collection.objects.link(gob)
gob.location = centre + Vector((0, -(r_glass + 0.6), 0.2))

# --- islet: the kit's rocks, x1.5-2.6 (tall ones squashed), sunk into the water around the base
rocks = []
rng = random.Random(4)
base_r = max(lh.dimensions.x, lh.dimensions.y) * 0.45
for i, path in enumerate(a.rocks * 2):
    ob = imported(path)
    ob.name = f"Rock_{i}"
    ang = i / (len(a.rocks) * 2) * 2 * math.pi + rng.uniform(-0.25, 0.25)
    rad = base_r + rng.uniform(0.0, 3.5)
    k = rng.uniform(1.5, 2.6)
    tall = ob.dimensions.z > 0.8 * max(ob.dimensions.x, ob.dimensions.y)
    ob.scale = (k, k, k * (0.55 if tall else rng.uniform(0.7, 1.0)))
    ob.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi))
    ob.location = (math.cos(ang) * rad, math.sin(ang) * rad, -rng.uniform(0.4, 1.2))
    rocks.append(ob)
rock_mat = bpy.data.materials.new("M_Rock")
rb = next(n for n in rock_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
rb.inputs["Base Color"].default_value = (0.11, 0.1, 0.09, 1)
rb.inputs["Roughness"].default_value = 0.85
for ob in rocks:
    ob.data.materials.clear()
    ob.data.materials.append(rock_mat)

# --- sea: a 20 km plane (to the horizon), dark water with moving wind ripples
me = bpy.data.meshes.new("Sea")
R = 10000.0
me.from_pydata([(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0)], [], [(0, 1, 2, 3)])
sea = bpy.data.objects.new("Sea", me)
sc.collection.objects.link(sea)
sea.location.z = 0.35
sm = bpy.data.materials.new("M_Sea")
me.materials.append(sm)
snt = sm.node_tree
sb = next(n for n in snt.nodes if n.type == "BSDF_PRINCIPLED")
sb.inputs["Base Color"].default_value = (0.004, 0.012, 0.016, 1)
sb.inputs["Roughness"].default_value = 0.06
sb.inputs["IOR"].default_value = 1.333
tc = snt.nodes.new("ShaderNodeTexCoord")
mp = snt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (0.35, 1.0, 1.0)  # ripples stretched across the wind
snt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nz = snt.nodes.new("ShaderNodeTexNoise")
nz.noise_dimensions = "4D"
nz.inputs["Scale"].default_value = 1.2
nz.inputs["Detail"].default_value = 8.0
nz.inputs["Roughness"].default_value = 0.6
snt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
nz.inputs["W"].default_value = 0.0
nz.inputs["W"].keyframe_insert("default_value", frame=f0)
nz.inputs["W"].default_value = (f1 - f0) / 24 * 0.35
nz.inputs["W"].keyframe_insert("default_value", frame=f1)
bump = snt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.25
bump.inputs["Distance"].default_value = 0.05
snt.links.new(nz.outputs["Factor"], bump.inputs["Height"])
snt.links.new(bump.outputs["Normal"], sb.inputs["Normal"])

# --- camera: a slow arc round the lighthouse, aimed a little left of it so the sky gets the frame
cd = bpy.data.cameras.new("Cam")
cd.lens, cd.clip_start, cd.clip_end = 30, 0.1, 30000
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
tgt = bpy.data.objects.new("Cam_Target", None)
sc.collection.objects.link(tgt)
for f, ang, dist, z in ((f0, -24.0, 46.0, 4.2), (f1, -12.0, 41.0, 4.6)):
    th = math.radians(ang)
    cam.location = (math.sin(th) * dist, -math.cos(th) * dist, z)
    cam.keyframe_insert("location", frame=f)
for f, p in ((f0, (-6.0, 0.0, 9.0)), (f1, (-5.0, 0.0, 9.0))):
    tgt.location = p
    tgt.keyframe_insert("location", frame=f)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam
edit.keyframe_new_interpolation_type = interp

# --- the label: small white text, bottom left, 1 m in front of the lens (shot.py sets the words)
half_w = 0.5 * cd.sensor_width / cd.lens
half_h = half_w * 720 / 1280
lm = bpy.data.materials.new("M_Label")
lnt = lm.node_tree
lnt.nodes.clear()
em = lnt.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 3.0
lnt.links.new(em.outputs[0], lnt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
cu = bpy.data.curves.new("Label", "FONT")
cu.body, cu.size, cu.align_x = "", half_h * 2 * 0.034, "LEFT"
cu.materials.append(lm)
lab = bpy.data.objects.new("Label", cu)
sc.collection.objects.link(lab)
lab.parent = cam
lab.location = (-half_w + half_w * 2 * 0.035, -half_h + half_h * 2 * 0.06, -1.0)
lab.visible_shadow = False
for vis in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
    setattr(lab, vis, False)
bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": True, "lighthouse_m": round(lh.dimensions.z, 2), "rocks": len(rocks),
                               "lantern": {"z": round(zc, 2), "radius": round(r_glass, 2), "glass_faces": len(gl)},
                               "frames": [f0, f1]}))
