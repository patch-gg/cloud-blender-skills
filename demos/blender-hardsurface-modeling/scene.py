"""Blockout of a sci-fi power cell at real scale (1.24 m long): plain primitives, flat shaded, one
object per part, plus the boolean cutters the production stack will use (in a Cutters collection).
A copy of the blockout (collection Blockout, hidden) is kept for the before/after. Run in the session: cloud.py run scene.py"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix

AXIS = 0.31          # height of the cell's long axis (X)
SEG = 32             # cylinder segments: large parts, a multiple of 8 so cuts line up with loops

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
sc = bpy.context.scene


def mat(name, color, rough, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    return m


PAINT = mat("M_Paint", (0.3, 0.305, 0.31), 0.3)
DARK = mat("M_Dark", (0.04, 0.042, 0.046), 0.36, metal=1.0)
CORE = mat("M_Core", (0.0, 0.0, 0.0), 0.5, emit=((1.0, 0.8, 0.55), 6.0))


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def S(x, y, z):
    return Matrix.Diagonal((x, y, z, 1.0))


ROT_ZX = Matrix.Rotation(math.pi / 2, 4, "Y")    # primitives are built along Z; this lays them along X


def cyl_x(bm, r, x0, x1, seg=SEG, y=0.0, z=AXIS):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r,
                          depth=x1 - x0, calc_uvs=True, matrix=T((x0 + x1) / 2, y, z) @ ROT_ZX)


def box(bm, x0, x1, y0, y1, z0, z1, around=None):
    m = T((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) @ S(x1 - x0, y1 - y0, z1 - z0)
    if around is not None:   # rotate about the cell axis by `around` radians
        m = T(0, 0, AXIS) @ Matrix.Rotation(around, 4, "X") @ T(0, 0, -AXIS) @ m
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True, matrix=m)


def tube_x(bm, r_out, r_in, xs, seg=SEG):
    """Open tube with wall thickness, closed and manifold, with an edge loop at each x in xs. Loops through
    the windows (never on a cutter's face: that is coplanar) keep each cut wall face a simple L shape
    instead of one long face notched twice, whose triangulation folds over itself once bevelled."""
    rows = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        rows.append([[bm.verts.new((x, r * c, AXIS + r * s)) for x in xs] for r in (r_out, r_in)])
    n = len(xs)
    for i in range(seg):
        (oa, ia), (ob, ib) = rows[i], rows[(i + 1) % seg]
        for k in range(n - 1):
            bm.faces.new((oa[k], ob[k], ob[k + 1], oa[k + 1]))     # outer wall
            bm.faces.new((ia[k], ia[k + 1], ib[k + 1], ib[k]))     # inner wall
        bm.faces.new((oa[0], ia[0], ib[0], ob[0]))                 # end rings
        bm.faces.new((oa[-1], ob[-1], ib[-1], ia[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def ring_x(bm, xc, radius, h, seg=SEG):
    """Square-section ring around the X axis: a groove cutter. Turned half a segment against the cylinder
    it cuts: with the same angles its edges would cross the cylinder's edges at (nearly) the same points,
    and the boolean leaves sub-0.1 mm slivers that the bevel then folds."""
    rings = []
    for i in range(seg):
        a = 2 * math.pi * (i + 0.5) / seg
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((xc + dx, (radius + dr) * c, AXIS + (radius + dr) * s))
                      for dx, dr in ((-h, -h), (h, -h), (h, h), (-h, h))])
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def part(name, build, material=None, coll=None):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False          # blockout: flat shaded
    ob = bpy.data.objects.new(name, me)
    (coll or prop).objects.link(ob)
    if material:
        me.materials.append(material)
    return ob


prop = bpy.data.collections.new("Prop")
sc.collection.children.link(prop)

nt = CORE.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
lw = nt.nodes.new("ShaderNodeLayerWeight")
inv = nt.nodes.new("ShaderNodeMath")
inv.operation, inv.inputs[0].default_value = "SUBTRACT", 1.0
pw = nt.nodes.new("ShaderNodeMath")
pw.operation, pw.inputs[1].default_value = "POWER", 2.0
st = nt.nodes.new("ShaderNodeMapRange")
st.inputs["To Min"].default_value, st.inputs["To Max"].default_value = 1.5, 14.0
col = nt.nodes.new("ShaderNodeMix")
col.data_type = "RGBA"
pick = lambda socks, name: next(x for x in socks if x.name == name and x.enabled)  # noqa: E731
pick(col.inputs, "A").default_value = (1.0, 0.42, 0.12, 1)
pick(col.inputs, "B").default_value = (1.0, 0.86, 0.66, 1)
nt.links.new(lw.outputs["Facing"], inv.inputs[1])
nt.links.new(inv.outputs[0], pw.inputs[0])
nt.links.new(pw.outputs[0], st.inputs["Value"])
nt.links.new(pw.outputs[0], pick(col.inputs, "Factor"))
nt.links.new(st.outputs["Result"], b.inputs["Emission Strength"])
nt.links.new(pick(col.outputs, "Result"), b.inputs["Emission Color"])
glow = bpy.data.lights.new("CoreGlow", "POINT")
glow.energy, glow.color, glow.shadow_soft_size = 25.0, (1.0, 0.62, 0.3), 0.05
gl = bpy.data.objects.new("CoreGlow", glow)
gl.location = (0, 0, AXIS)
prop.objects.link(gl)
cutters = bpy.data.collections.new("Cutters")
sc.collection.children.link(cutters)

# ---- parts (the blockout)
parts = [
    part("Shell", lambda bm: tube_x(bm, 0.20, 0.168, (-0.42, -0.35, -0.15, 0.0, 0.15, 0.35, 0.42)), PAINT),
    part("Caps", lambda bm: [cyl_x(bm, 0.25, x0, x0 + 0.14) for x0 in (0.40, -0.54)], PAINT),
    part("Core", lambda bm: cyl_x(bm, 0.135, -0.42, 0.42), CORE),
    part("CoreRings", lambda bm: [cyl_x(bm, 0.158, x - 0.018, x + 0.018) for x in (-0.15, 0.15)], DARK),
    part("Hubs", lambda bm: [cyl_x(bm, 0.075, x0, x0 + 0.085, seg=24) for x0 in (0.49, -0.575)], DARK),
    part("Bolts", lambda bm: [cyl_x(bm, 0.017, x0, x0 + 0.026, seg=16,
                                    y=0.208 * math.cos(math.radians(22.5 + 45 * k)),
                                    z=AXIS + 0.208 * math.sin(math.radians(22.5 + 45 * k)))
                              for x0 in (0.530, -0.556) for k in range(8)], DARK),
    part("Rails", lambda bm: [box(bm, -0.42, 0.42, -0.0225, 0.0225, AXIS + 0.215 - 0.0225, AXIS + 0.215 + 0.0225,
                                  around=math.radians(a)) for a in (45, 135, 225, 315)], DARK),
    part("Cradle", lambda bm: [box(bm, x - 0.05, x + 0.05, -0.20, 0.20, 0.04, AXIS) for x in (-0.47, 0.47)], DARK),
    part("Skid", lambda bm: box(bm, -0.62, 0.62, -0.24, 0.24, 0.0, 0.05), DARK),
]

# ---- cutters (closed meshes that reach past the surface they cut)
cut_specs = {
    "Shell": [part("Cut_Windows", lambda bm: [box(bm, x0, x0 + 0.24, -0.05, 0.05, AXIS + 0.14, AXIS + 0.28,
                                                   around=math.radians(a))
                                               for a in (0, 90, 180, 270) for x0 in (-0.27, 0.03)], coll=cutters)],
    "Caps": [part("Cut_CapRecess", lambda bm: [cyl_x(bm, 0.165, x0, x0 + 0.085) for x0 in (0.515, -0.60)], coll=cutters),
             part("Cut_CapGrooves", lambda bm: [ring_x(bm, x, 0.25, 0.02) for x in (-0.47, 0.47)], coll=cutters)],
    "Cradle": [part("Cut_Saddle", lambda bm: cyl_x(bm, 0.252, -0.62, 0.62), coll=cutters),
               part("Cut_CradleHoles", lambda bm: [cyl_x(bm, 0.04, x - 0.08, x + 0.08, seg=16, y=y, z=0.14)
                                                   for x in (-0.47, 0.47) for y in (-0.10, 0.10)], coll=cutters)],
    "Skid": [part("Cut_SkidSlots", lambda bm: [box(bm, -0.70, 0.70, y - 0.03, y + 0.03, 0.025, 0.09)
                                               for y in (-0.14, 0.14)], coll=cutters)],
}
for c in cutters.objects:
    c.display_type = "WIRE"
    c.hide_render = True
bpy.data.objects["Core"].visible_shadow = False   # the glow inside passes through the core, not the shell

# ---- a hidden copy of the blockout, for the before/after
keep = bpy.data.collections.new("Blockout")
sc.collection.children.link(keep)
for ob in parts:
    cp = ob.copy()
    cp.data = ob.data.copy()
    cp.name = cp.data.name = "BO_" + ob.name
    keep.objects.link(cp)
keep.hide_render = True
bpy.context.view_layer.layer_collection.children["Blockout"].hide_viewport = True

tris = 0
for ob in parts:
    ob.data.calc_loop_triangles()
    tris += len(ob.data.loop_triangles)
print("@@JSON@@" + json.dumps({"ok": True, "parts": [o.name for o in parts],
                               "cutters": {k: [c.name for c in v] for k, v in cut_specs.items()},
                               "blockout_tris": tris,
                               "size_m": [1.24, 0.5, round(AXIS + 0.25, 2)]}))
