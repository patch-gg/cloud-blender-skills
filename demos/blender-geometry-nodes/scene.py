"""The ground and the parts for the scatter: a round island 11 m across (gentle hills on top, rocky sides,
standing on the floor), low-poly trees from Patch's asset library (Kenney Nature Kit, CC0), each joined
into one object with its origin at the base, in a collection "Trees" that only the node tree uses, and the
pink material for the ring that shows where the Radius input is.
Run in the session: cloud.py run scene.py -- <tree.glb> ..."""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

paths = sys.argv[sys.argv.index("--") + 1:]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
              bpy.data.lights, bpy.data.node_groups):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
sc = bpy.context.scene


def mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m


# ---- the island: a polar grid (round edge), hills that fade out toward the rim, rocky sides
R, RINGS, SEG = 5.5, 28, 128


def height(x, y):
    r = math.hypot(x, y) / R
    hills = 0.55 * noise.noise(Vector((x * 0.16, y * 0.16, 1.7))) + 0.18 * noise.noise(Vector((x * 0.45, y * 0.45, 4.2)))
    return 0.55 + max(hills, -0.25) * (1 - r ** 3) - 0.12 * r ** 4


bm = bmesh.new()
center = bm.verts.new((0, 0, height(0, 0)))
rings = []
for k in range(1, RINGS + 1):
    rr = R * k / RINGS
    rings.append([bm.verts.new((rr * math.cos(2 * math.pi * i / SEG), rr * math.sin(2 * math.pi * i / SEG),
                                height(rr * math.cos(2 * math.pi * i / SEG), rr * math.sin(2 * math.pi * i / SEG))))
                  for i in range(SEG)])
for i in range(SEG):
    bm.faces.new((center, rings[0][i], rings[0][(i + 1) % SEG]))
for k in range(RINGS - 1):
    a, b = rings[k], rings[k + 1]
    for i in range(SEG):
        bm.faces.new((a[i], b[i], b[(i + 1) % SEG], a[(i + 1) % SEG]))
top_faces = len(bm.faces)
# sides: three bands down to the floor, wobbling in and out like rock
prev = rings[-1]
rim = [v.co.z for v in prev]
for band, (frac, grow) in enumerate(((0.7, 1.025), (0.35, 1.01), (0.0, 0.97))):
    cur = []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        wob = 1 + 0.035 * noise.noise(Vector((math.cos(a) * 3, math.sin(a) * 3, band * 1.3)))
        cur.append(bm.verts.new((R * grow * wob * math.cos(a), R * grow * wob * math.sin(a), rim[i] * frac)))
    for i in range(SEG):
        bm.faces.new((prev[i], prev[(i + 1) % SEG], cur[(i + 1) % SEG], cur[i]))
    prev = cur
bm.faces.new(list(reversed(prev)))          # the bottom, on the floor
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("Island")
bm.to_mesh(me)
bm.free()
me.materials.append(mat("M_Grass", (0.2, 0.36, 0.1), 0.9))
me.materials.append(mat("M_Rock", (0.20, 0.15, 0.11), 0.85))
for p in me.polygons:
    p.material_index = 0 if p.index < top_faces else 1
    p.use_smooth = p.index < top_faces
island = bpy.data.objects.new("Island", me)
sc.collection.objects.link(island)
front = mat("M_Front", (0.913, 0.045, 0.637), 0.5)       # #F53CD1: the ring that marks the Radius input
b = next(n for n in front.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Emission Color"].default_value = (0.913, 0.045, 0.637, 1)
b.inputs["Emission Strength"].default_value = 1.5

# ---- the trees: one object per model, origin at the base, in a collection only the node tree uses
trees = bpy.data.collections.new("Trees")
sc.collection.children.link(trees)
names = []
for path in paths:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    with bpy.context.temp_override(selected_editable_objects=meshes, selected_objects=meshes,
                                   active_object=meshes[0], object=meshes[0]):
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        if len(meshes) > 1:
            bpy.ops.object.join()
    ob = meshes[0]
    for o in new:
        if o is not ob and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    with bpy.context.temp_override(selected_editable_objects=[ob], selected_objects=[ob], active_object=ob, object=ob):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(c) for c in ob.bound_box]
    base = Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2,
                   (min(p.y for p in pts) + max(p.y for p in pts)) / 2, min(p.z for p in pts)))
    ob.data.transform(Matrix.Translation(-base))
    ob.name = ob.data.name = os.path.splitext(os.path.basename(path))[0]
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    trees.objects.link(ob)
    names.append(ob.name)
trees.hide_render = True
bpy.context.view_layer.layer_collection.children["Trees"].exclude = True
print("@@JSON@@" + json.dumps({"ok": True, "island": island.name, "top_faces": top_faces, "trees": names,
                               "radius_m": R}))
