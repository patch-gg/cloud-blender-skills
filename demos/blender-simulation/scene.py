"""A loading-dock corner for the physics: a concrete floor slab and two walls (thick boxes, so their collision
hulls are solid), nine wooden crates and two barrels from Poly Haven held in the air in staggered, tilted
layers, and a 3.6 m canvas tarp (64 x 64 quads) waiting above the frame. Run in the session:
    cloud.py run scene.py -- --crates a.glb b.glb c.glb --barrel d.glb
"""
import argparse
import json
import math
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector

ap = argparse.ArgumentParser()
ap.add_argument("--crates", nargs="+", required=True)
ap.add_argument("--barrel", required=True)
ap.add_argument("--tarp-z", type=float, default=3.7)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, 120, 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.engine = "BLENDER_EEVEE"
rng = random.Random(3)


def mat(name, rgb, rough, brick=None, axes=("X", "Z"), weave=False):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 1.5, 8.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(nz.outputs["Factor"], mr.inputs[0])
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.7, 1.2
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for i, c in enumerate(rgb):
        mm = nt.nodes.new("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        nt.links.new(mr.outputs[0], mm.inputs[0])
        mm.inputs[1].default_value = c
        nt.links.new(mm.outputs[0], cc.inputs[i])
    col = cc.outputs[0]
    if brick:  # concrete blocks: brick texture as joints, laid in the wall's own plane
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        uv = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(sep.outputs[axes[0]], uv.inputs["X"])
        nt.links.new(sep.outputs[axes[1]], uv.inputs["Y"])
        br = nt.nodes.new("ShaderNodeTexBrick")
        nt.links.new(uv.outputs[0], br.inputs["Vector"])
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value, br.inputs["Row Height"].default_value = brick
        br.inputs["Mortar Size"].default_value = 0.008
        br.inputs["Color1"].default_value = br.inputs["Color2"].default_value = (1, 1, 1, 1)
        br.inputs["Mortar"].default_value = (0.45, 0.45, 0.45, 1)
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type, mx.blend_type = "RGBA", "MULTIPLY"
        mx.inputs[0].default_value = 1.0
        nt.links.new(col, mx.inputs[6])
        nt.links.new(br.outputs["Color"], mx.inputs[7])
        col = mx.outputs[2]
    nt.links.new(col, b.inputs["Base Color"])
    if weave:  # canvas: a fine weave bump
        wv = nt.nodes.new("ShaderNodeTexWave")
        nt.links.new(tc.outputs["UV"], wv.inputs["Vector"])
        wv.inputs["Scale"].default_value = 220.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Sheen Weight"].default_value = 0.3
    return m


def box(name, lo, hi, m):
    me = bpy.data.meshes.new(name)
    vs = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    me.from_pydata(vs, [], [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)])
    c = Vector([(l + h) / 2 for l, h in zip(lo, hi)])
    for p in me.polygons:
        if p.normal.dot(p.center - c) < 0:
            p.flip()
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(m)
    return ob


concrete = mat("M_Floor", (0.32, 0.31, 0.29), 0.85)
floor = box("Floor", (-8, -8, -0.3), (8, 8, 0.0), concrete)
wall_b = box("Wall_Back", (-8, 2.4, 0.0), (8, 2.7, 4.5), mat("M_Wall_Back", (0.42, 0.4, 0.37), 0.9, brick=(0.4, 0.2)))
wall_s = box("Wall_Side", (-3.1, -8, 0.0), (-2.8, 2.7, 4.5),
             mat("M_Wall_Side", (0.42, 0.4, 0.37), 0.9, brick=(0.4, 0.2), axes=("Y", "Z")))


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    meshes = [o for o in new if o.type == "MESH"]
    for o in [o for o in new if o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(c) for c in ob.bound_box]
    centre = sum(pts, Vector()) / 8  # origin at the box centre: rigid bodies spin about it
    ob.data.transform(Matrix.Translation(-centre))
    ob.location = (0, 0, 0)
    return ob


sources = [load(p) for p in a.crates] + [load(a.barrel)]
crate_src, barrel_src = sources[:-1], sources[-1]
kinds = [crate_src[i % len(crate_src)] for i in range(9)] + [barrel_src, barrel_src]
rng.shuffle(kinds)
# four staggered layers, three per layer on a 1.45 m triangle, each layer turned; tilts up to 35 degrees
bodies = []
for i, src in enumerate(kinds):
    layer, k = divmod(i, 3)
    ang = math.radians(120 * k + 47 * layer)
    p = Vector((-0.55, 0.55, 0)) + Vector((math.cos(ang), math.sin(ang), 0)) * 0.84
    p.z = 0.75 + 0.95 * layer + rng.uniform(0.0, 0.25)
    ob = src.copy()
    ob.data = src.data  # linked: one mesh per kind
    sc.collection.objects.link(ob)
    ob.name = f"{'Barrel' if src is barrel_src else 'Crate'}_{i:02d}"
    ob.location = p
    ob.rotation_mode = "XYZ"  # glTF imports come in as quaternions
    ob.rotation_euler = Euler((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0, math.tau)))
    bodies.append(ob)
for s in sources:
    bpy.data.objects.remove(s, do_unlink=True)

# tarp: canvas, 64 x 64 quads over 3.6 m (5.6 cm edges), turned 20 degrees, above the frame
bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=3.6,
                                location=(-0.45, 0.45, a.tarp_z), rotation=(0, 0, math.radians(20)))
tarp = bpy.context.active_object
tarp.name = tarp.data.name = "Tarp"
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
tarp.data.materials.append(mat("M_Canvas", (0.085, 0.1, 0.05), 0.9, weave=True))  # olive drab
tarp.data.shade_smooth()
print("@@JSON@@" + json.dumps({"ok": True, "bodies": [o.name for o in bodies],
                               "crates": sum(o.name.startswith("Crate") for o in bodies),
                               "barrels": sum(o.name.startswith("Barrel") for o in bodies),
                               "tarp_verts": len(tarp.data.vertices),
                               "colliders": ["Floor", "Wall_Back", "Wall_Side"]}))
