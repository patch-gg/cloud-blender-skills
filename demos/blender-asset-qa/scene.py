"""The input: a CC0 wine barrel from Patch's asset library (Poly Haven), imported, its glTF seam splits
merged (0.1 mm) and its parts named, then broken on purpose the ways real assets break:
  1 z-fighting: the lid duplicated in place and turned 90 degrees
  2 floating:   the bung pulled 6 cm out of its hole
  3 flipped:    one stave inside out
  4 empty slot: two staves moved to a new, empty material slot (they render grey)
Each broken face gets the face attribute qa_problem = 1..4 (presentation only; QA doesn't read it).

Run in the session: cloud.py run scene.py -- assets/wine_barrel_01.glb
"""
import json
import math
import os
import sys
from collections import defaultdict

import bmesh
import bpy
from mathutils import Matrix, Vector

NAMES = {"wine_barrel_01": "Barrel_Body", "wine_barrel_01_Lid": "Barrel_Lid",
         "wine_barrel_01_base": "Barrel_Base", "wine_barrel_01_bung": "Barrel_Bung"}

path = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
col = bpy.data.collections.new("Barrel")
bpy.context.scene.collection.children.link(col)
parts = {}
for ob in [o for o in bpy.data.objects if o.type == "MESH"]:
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    ob.name = ob.data.name = NAMES[ob.name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)   # glTF splits every seam
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.attributes.new("qa_problem", "INT", "FACE")
    ob.data.transform(Matrix.Rotation(math.radians(-65), 4, "Z"))   # bung to the camera's left, in profile
    parts[ob.name] = ob
for ob in bpy.context.view_layer.objects:
    ob.select_set(False)


def islands(bm):
    bm.verts.ensure_lookup_table()
    parent = list(range(len(bm.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    out = defaultdict(list)
    for v in bm.verts:
        out[find(v.index)].append(v)
    return list(out.values())


def tag(bm, faces, k):
    lay = bm.faces.layers.int["qa_problem"]
    for f in faces:
        f[lay] = k


body = parts["Barrel_Body"]
bm = bmesh.new()
bm.from_mesh(body.data)
isl = islands(bm)
hoops = [vs for vs in isl if len(vs) == 384]
staves = [vs for vs in isl if max(v.co.z for v in vs) - min(v.co.z for v in vs) > 0.8 and len(vs) < 200]


def angle(vs):
    c = sum((v.co for v in vs), Vector()) / len(vs)
    return math.degrees(math.atan2(c.y, c.x)) % 360


def faces_of(vs):
    s = set(vs)
    return {f for v in vs for f in v.link_faces if all(w in s for w in f.verts)}


# 3 flipped: a front-left stave (the camera looks from -Y), turned inside out
flip = min(staves, key=lambda s: abs(angle(s) - 250))
flip_deg = round(angle(flip))
ff = faces_of(flip)
bmesh.ops.reverse_faces(bm, faces=list(ff))
tag(bm, ff, 3)
# 4 empty slot: two front-right staves on a new, empty slot
body.data.materials.append(None)
empty = sorted(staves, key=lambda s: abs(angle(s) - 300))[:2]
empty_deg = [round(angle(s)) for s in empty]
ef = set().union(*(faces_of(s) for s in empty))
for f in ef:
    f.material_index = len(body.data.materials) - 1
tag(bm, ef, 4)
bm.to_mesh(body.data)
bm.free()

# 2 floating: the bung pulled 6 cm straight out of its hole
bung = parts["Barrel_Bung"]
c = sum((v.co for v in bung.data.vertices), Vector()) / len(bung.data.vertices)
out = Vector((c.x, c.y, 0)).normalized() * 0.06
bung.data.transform(Matrix.Translation(out))
bung.data.attributes["qa_problem"].data.foreach_set("value", [2] * len(bung.data.polygons))

# 1 z-fighting: the lid duplicated in place and turned a quarter (cross-grain, same planes)
lid = parts["Barrel_Lid"]
dup = lid.copy()
dup.data = lid.data.copy()
dup.data.name = dup.name = "Barrel_Lid.001"
dup.data.transform(Matrix.Rotation(math.radians(90), 4, "Z"))
dup.data.attributes["qa_problem"].data.foreach_set("value", [1] * len(dup.data.polygons))
col.objects.link(dup)

bpy.context.view_layer.update()
print("@@JSON@@" + json.dumps({"ok": True, "objects": [o.name for o in col.objects],
                               "planted": {"zfighting": dup.name, "floating": f"bung, {round(out.length * 100)} cm out",
                                           "flipped": f"stave at {flip_deg} deg",
                                           "empty_slot": f"{len(empty)} staves at {empty_deg} deg"}}))
