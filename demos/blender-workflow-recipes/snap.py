"""Presentation: keep a copy of what the asset looks like after a stage, for the clip's stage-by-stage cut.
Copies the named objects (modifiers applied, custom normals kept) into the collection STG_<stage>, hidden,
and dresses them for that stage:
  clayflat  grey clay, flat shaded (the blockout)
  clay      grey clay (the high poly)
  checker   a UV colour grid on the active UV map (the unwrap)
  bakeclay  grey clay with the baked normal and AO maps only (what the low carries after the bake)
  copy      the objects' own materials, copied, so later stages don't change this one
Run in the session: cloud.py run snap.py -- --stage uvs --look checker --objects SM_JerryCan"""
import argparse
import json
import sys

import bpy

p = argparse.ArgumentParser()
p.add_argument("--stage", required=True)
p.add_argument("--look", required=True, choices=["clayflat", "clay", "checker", "bakeclay", "copy"])
p.add_argument("--objects", nargs="+", required=True)
p.add_argument("--normal", default="T_JerryCan_N")
p.add_argument("--ao", default="T_JerryCan_AO")
a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])

sc = bpy.context.scene
root = bpy.data.collections.get("Stages") or bpy.data.collections.new("Stages")
if root.name not in sc.collection.children:
    sc.collection.children.link(root)
cname = f"STG_{a.stage}"
coll = bpy.data.collections.get(cname)
if coll:
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob)
else:
    coll = bpy.data.collections.new(cname)
    root.children.link(coll)


CLAY = (0.2, 0.2, 0.205, 1)   # 20% grey: lit for the red paint, a lighter clay clips to white


def fresh(name):
    """The named material, rebuilt from scratch (a re-run never reuses stale nodes)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = CLAY
    b.inputs["Roughness"].default_value = 0.55
    m.diffuse_color = CLAY
    return m, nt, b


def clay(name):
    return fresh(name)[0]


def checker():
    img = bpy.data.images.get("PR_UVGrid") or bpy.data.images.new("PR_UVGrid", 1024, 1024)
    img.generated_type = "COLOR_GRID"
    m, nt, b = fresh("PR_UVChecker")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    return m


def bakeclay():
    m, nt, b = fresh("PR_BakeClay")
    n_tex, ao_tex = nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeTexImage")
    n_tex.image, ao_tex.image = bpy.data.images[a.normal], bpy.data.images[a.ao]
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(n_tex.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], b.inputs["Normal"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type, mul.blend_type = "RGBA", "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = CLAY
    nt.links.new(ao_tex.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    return m


srcs = [bpy.data.objects[n] for n in a.objects]
hidden = [(o, o.hide_get()) for o in srcs]
for o, _ in hidden:
    o.hide_set(False)                     # hidden objects aren't evaluated, so their modifiers wouldn't apply
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
mat = None if a.look == "copy" else {"clayflat": lambda: clay("PR_Clay"), "clay": lambda: clay("PR_Clay"),
                                     "checker": checker, "bakeclay": bakeclay}[a.look]()   # only the one needed
made, tris = [], 0
for src in srcs:
    name = src.name
    stale = bpy.data.meshes.get(f"STG_{a.stage}_{name}")
    if stale and stale.users == 0:
        bpy.data.meshes.remove(stale)
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = f"STG_{a.stage}_{name}"
    ob = bpy.data.objects.new(me.name, me)
    ob.matrix_world = src.matrix_world.copy()
    coll.objects.link(ob)
    if a.look == "copy":
        for i, slot in enumerate(src.material_slots):
            me.materials[i] = slot.material.copy() if slot.material else None
    else:
        me.materials.clear()
        me.materials.append(mat)
        if a.look == "clayflat":
            me.shade_flat()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    ob.hide_render = True
    ob.hide_set(True)
    made.append(ob.name)
for o, was in hidden:
    o.hide_set(was)
print("@@JSON@@" + json.dumps({"ok": True, "stage": a.stage, "objects": made, "tris": tris}))
