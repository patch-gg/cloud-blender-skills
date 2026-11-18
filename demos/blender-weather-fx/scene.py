"""A night street to rain on: a brick facade built from Poly Haven's modular facade kit (twelve 3 m bays,
four storeys, cornice), a sidewalk and kerb, an asphalt road, four street lamps, a hydrant, a bin, bags and a
covered car, some windows lit. Dry, so the weather scripts have something to change. Run in the session:
    cloud.py run scene.py -- --facade kit.glb --lamp lamp.glb --hydrant h.glb --bin b.glb --bag t.glb --car c.glb
"""
import argparse
import json
import math
import random
import sys

import bpy
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser()
for k in ("facade", "lamp", "hydrant", "bin", "bag", "car"):
    ap.add_argument(f"--{k}", required=True)
ap.add_argument("--frames", type=int, nargs=2, default=(1, 90))  # 3.75 s: ripples (1.6 Hz) loop too
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = a.frames[0], a.frames[1], 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.engine = "CYCLES"
rng = random.Random(7)


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children:
        sc.collection.children.link(c)
    return c


def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    for o in [o for o in new if o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    return [o for o in new if o.name in bpy.data.objects]


def prop(path, name, loc, yaw=0.0, c=None):
    """Import, join into one object `name`, base on z = 0 at loc, rotated by yaw degrees."""
    obs = load(path)
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = bounds(ob)
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    ob.data.transform(Matrix.Translation(-base))
    ob.location = loc
    ob.rotation_euler.z = math.radians(yaw)
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    (c or coll("Street")).objects.link(ob)
    return ob


# --- facade: the kit lays its modules out with gaps; stack six bays edge to edge, four storeys tall
kit = load(a.facade)
COLS = {"centered_large": 6.76, "centered_small": 10.76, "centered_double": 14.76, "offset_small": 18.76}
ROWS = [(1.0, 1.5, -1.0), (2.0, 5.0, -1.5), (6.0, 9.0, -2.5), (10.0, 13.0, -3.5), (14.0, 17.0, -4.5)]
BAYS = ["centered_double", "centered_large", "offset_small", "centered_small", "centered_double", "centered_large",
        "centered_small", "offset_small", "centered_double", "centered_large", "centered_small", "centered_double"]
fac = coll("Facade")
pieces = []
for k, col in enumerate(BAYS):
    x0 = COLS[col]
    for o in kit:
        lo, hi = bounds(o)
        if not (x0 - 0.05 <= lo.x and hi.x <= x0 + 3.05) or lo.y > -2.5:
            continue
        shift = next((s for z0, z1, s in ROWS if z0 - 0.05 <= lo.z and hi.z <= z1 + 0.05), None)
        if shift is None:
            continue
        d = o.copy()
        fac.objects.link(d)
        d.location += Vector((3.0 * k - x0, 0, shift))
        d.name = f"Facade_{k}_{o.name}"
        pieces.append(d)
for nm, z in (("cornice_standard_standard_01", 12.5), ("crown_standard_standard_01", 12.7)):
    src = next((o for o in kit if o.name.startswith(nm)), None)
    if src is None:
        continue
    lo, _hi = bounds(src)
    for k in range(len(BAYS)):
        d = src.copy()
        fac.objects.link(d)
        d.location += Vector((3.0 * k - lo.x, 0, z - lo.z))
        d.name = f"Facade_{k}_{nm}"
        pieces.append(d)
for o in kit:
    bpy.data.objects.remove(o, do_unlink=True)
width = 3.0 * len(BAYS)
front_y = -2.91

# lit windows: the kit's glass gets a warm glow on about a third of the window objects
glass = next((m for m in bpy.data.materials if "facade_glass" in m.name), None)
if glass:
    nt = glass.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    nt.links.new(oi.outputs["Random"], gt.inputs[0])
    gt.inputs[1].default_value = 0.62
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(gt.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = 4.0
    b.inputs["Emission Color"].default_value = (1.0, 0.62, 0.32, 1)
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])

# --- street: sidewalk + kerb + asphalt road, all real metres (z = 0 is the road)
def slab(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    vs = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    me.from_pydata(vs, [], [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)])
    for p in me.polygons:  # outward normals: flip the ones pointing into the box
        c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        if p.normal.dot(p.center - c) < 0:
            p.flip()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll("Street").objects.link(ob)
    me.materials.append(mat)
    uv = me.uv_layers.new(name="UVMap")
    for li, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co
        uv.data[li].uv = (co.x, co.y if abs(co.z - z1) < 1e-4 else co.z)
    return ob


def material(name, rgb, rough, tex=None):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 3.0, 10.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(nz.outputs["Factor"], ramp.inputs[0])
    ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = 0.75, 1.25
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type, col.blend_type = "RGBA", "MULTIPLY"
    col.inputs[0].default_value = 1.0
    col.inputs[6].default_value = (*rgb, 1)
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(ramp.outputs[0], cc.inputs[i])
    if tex == "slabs":  # 1.2 m concrete flags with dark joints
        br = nt.nodes.new("ShaderNodeTexBrick")
        nt.links.new(tc.outputs["UV"], br.inputs["Vector"])
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.012
        br.inputs["Brick Width"].default_value = 1.2
        br.inputs["Row Height"].default_value = 1.2
        br.offset = 0.0
        br.inputs["Color1"].default_value = br.inputs["Color2"].default_value = (1, 1, 1, 1)
        br.inputs["Mortar"].default_value = (0.35, 0.35, 0.35, 1)
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type, m2.blend_type = "RGBA", "MULTIPLY"
        m2.inputs[0].default_value = 1.0
        nt.links.new(cc.outputs[0], m2.inputs[6])
        nt.links.new(br.outputs["Color"], m2.inputs[7])
        nt.links.new(m2.outputs[2], col.inputs[7])
    else:
        nt.links.new(cc.outputs[0], col.inputs[7])
    nt.links.new(col.outputs[2], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    fine = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    fine.inputs["Scale"].default_value = 60.0
    nt.links.new(fine.outputs["Factor"], bump.inputs["Height"])
    bump.inputs["Strength"].default_value = 0.15
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


asphalt = material("M_Asphalt", (0.045, 0.045, 0.048), 0.75)
concrete = material("M_Concrete", (0.2, 0.195, 0.19), 0.8, tex="slabs")
kerb_m = material("M_Kerb", (0.28, 0.27, 0.26), 0.7)
x0, x1 = -14.0, width + 30.0
slab("Sidewalk", x0, x1, -5.9, front_y + 0.02, 0.0, 0.15, concrete)
slab("Kerb", x0, x1, -6.1, -5.9, 0.0, 0.15, kerb_m)
slab("Road", x0, x1, -40.0, -6.1, -0.2, 0.0, asphalt)

# --- props
st = coll("Street")
lamps = [prop(a.lamp, f"Lamp_{i}", (x, -5.45, 0.15), 90) for i, x in enumerate((31.0, 20.5, 10.0, -0.5))]
prop(a.hydrant, "Hydrant", (26.0, -5.35, 0.15), 70)
prop(a.bin, "Bin", (23.4, -3.45, 0.15), 0)
prop(a.bag, "Bag_A", (24.4, -3.4, 0.15), 30)
prop(a.bag, "Bag_B", (24.95, -3.55, 0.15), 110)
prop(a.car, "Car", (15.5, -7.35, 0.0), 90)
# lamp bulbs: a warm point light in each lantern, the glass glows
for lp in lamps:
    lo, hi = bounds(lp)
    head = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z - 0.42))
    ld = bpy.data.lights.new(lp.name + "_Bulb", "POINT")
    ld.energy, ld.shadow_soft_size = 220.0, 0.08
    ld.use_temperature, ld.temperature = True, 2700
    lo_ = bpy.data.objects.new(lp.name + "_Bulb", ld)
    st.objects.link(lo_)
    lo_.location = head
lg = next((m for m in bpy.data.materials if m.name.startswith("street_lamp_01_glass")), None)
if lg:
    b = next(n for n in lg.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Emission Color"].default_value = (1.0, 0.7, 0.4, 1)
    b.inputs["Emission Strength"].default_value = 12.0

# --- camera: on the road, low, looking along the kerb so the lamps line up and the sky shows above the roofs
cd = bpy.data.cameras.new("Cam")
cd.lens, cd.clip_start, cd.clip_end = 28, 0.1, 2000
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
cam.location = (36.0, -12.0, 1.4)
cam.rotation_euler = (Vector((14.0, -3.5, 4.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
# one facade object per material, so the weather scripts reach every facade material: brick and stone trims
# are porous, the doors, frames and glass are not
reps = {}
for o in pieces:
    for m in o.data.materials:
        reps.setdefault(m.name, o.name)
porous = sorted({n for m, n in reps.items() if "plaster" in m or "trim" in m})
hard = sorted({n for m, n in reps.items() if n not in porous})
print("@@JSON@@" + json.dumps({"ok": True, "facade_pieces": len(pieces), "facade_m": [width, 13.4],
                               "lamps": [l.name for l in lamps], "glass": glass.name if glass else None,
                               "facade_porous": porous, "facade_hard": hard}))
