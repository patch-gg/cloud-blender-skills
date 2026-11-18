"""The batch's delivered GLBs on a three-step display, five to a step, each scaled to fill its tile and turned
a little towards the key light, with a thin pink ring under every file QA flagged.
Run in the session after the batch: cloud.py run scene.py -- --dir delivered --flagged NAME ..."""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# back step to front step, left to right: colours spread so no two neighbours match (the files QA flags
# with the default game profile fall on a checkerboard here, so the pink rings spread evenly)
LAYOUT = [
    ["alarm_clock_01", "american_football", "korean_fire_extinguisher_01", "wicker_basket_02", "potted_plant_04"],
    ["barrel_01", "metal_toolbox", "rubber_duck_toy", "vintage_electric_kettle", "baseball_01"],
    ["wooden_bucket_01", "pot_enamel_01", "watering_can_metal_01", "garden_sprinkler_01", "measuring_tape_01"],
]
PITCH, DEPTH = 1.0, 1.0            # tile width and step depth (m)
TOPS = [1.2, 0.66, 0.12]           # step heights, back to front: each row clears the one in front
AREA, CAP = 0.30, 0.8              # each asset's front area (m2) and largest side
YAW = {"watering_can_metal_01": 72, "measuring_tape_01": 72}  # side-on; the rest turn -18 degrees
PINK = (0.913, 0.045, 0.637, 1)    # #F53CD1 in linear


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out, key = {"dir": ["delivered"], "flagged": []}, None
    for t in a:
        if t.startswith("--"):
            key = t[2:]
            out[key] = []
        elif key:
            out[key].append(t)
    return out["dir"][0], set(out["flagged"])


def bounds(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def material(name, color, rough=0.6, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = color
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = color
    return m


def display():
    """Three stacked boxes, one per step, as one mesh."""
    bm = bmesh.new()
    w = len(LAYOUT[0]) * PITCH + 0.5
    for r, top in enumerate(TOPS):
        y0 = (1 - r) * DEPTH           # back step at +y
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            v.co = Vector((v.co.x * w, y0 + v.co.y * DEPTH, (v.co.z + 0.5) * top))
    me = bpy.data.meshes.new("Display")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Display", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material("M_Display", (0.8, 0.8, 0.8, 1), 0.7))
    return ob


def ring(name, parent, radius):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    segs, minor = 64, 0.02
    for i in range(segs):  # a flat band lying on the step
        a = 2 * math.pi * i / segs
        for rr in (radius - minor, radius + minor):
            bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0.0))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bm.verts[2 * i], bm.verts[2 * i + 1], bm.verts[2 * j + 1], bm.verts[2 * j]))
    bm.to_mesh(me)
    bm.free()
    # AgX washes bright saturated colours toward pastel; a darker albedo reads as the brand pink on white
    me.materials.append(material("M_Flag", tuple(c * 0.6 for c in PINK[:3]) + (1,), 0.45))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location = (0, 0, 0.004)
    return ob


def main():
    folder, flagged = args()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    sc = bpy.context.scene
    display()
    tiles, meshes, missing = [], ["Display"], []
    for r, row in enumerate(LAYOUT):
        for c, name in enumerate(row):
            path = os.path.join(folder, name + ".glb")
            if not os.path.exists(path):
                missing.append(name)
                continue
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=path)
            new = [o for o in bpy.data.objects if o not in before]
            bpy.context.view_layer.update()
            yaw = math.radians(YAW.get(name, -18))
            for o in new:
                if o.parent is None:
                    o.matrix_world = Matrix.Rotation(yaw, 4, "Z") @ o.matrix_world
            bpy.context.view_layer.update()
            lo, hi = bounds(new)
            size = hi - lo           # x width, y depth, z height as the camera sees it
            s = min(math.sqrt(AREA / (size.x * size.z)), CAP / max(size.x, size.z), 0.85 / size.y)
            tile = bpy.data.objects.new("Tile_" + name, None)
            sc.collection.objects.link(tile)
            tile.empty_display_size = 0.3
            base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
            for o in new:
                if o.parent is None:  # roots: move the asset's base centre to the tile origin, scaled
                    o.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation(-base) @ o.matrix_world
                    o.parent = tile
                    o.matrix_parent_inverse = Matrix.Identity(4)
                if o.type == "MESH":
                    meshes.append(o.name)
            tile.location = ((c - 2) * PITCH, (1 - r) * DEPTH, TOPS[r])
            if name in flagged:
                ring("Flag_" + name, tile, 0.42)
            tiles.append(tile.name)
    bpy.context.view_layer.update()
    print("@@JSON@@" + json.dumps({"ok": not missing, "tiles": tiles, "missing": missing, "meshes": meshes,
                                   "flagged": sorted(flagged)}))


main()
