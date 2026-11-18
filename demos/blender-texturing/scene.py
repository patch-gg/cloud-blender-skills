"""Input for blender-texturing: Poly Haven's metal jerry can (CC0) as one mesh named JerryCan, standing on
z=0 at the origin, and a stencil decal image (decals/diesel.png) drawn here with a Blender text object.
Run in the session: cloud.py run scene.py -- assets/metal_jerrycan.glb decals/diesel.png"""
import json
import os
import sys

import bpy

glb, decal_png = sys.argv[sys.argv.index("--") + 1:][:2]

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
             bpy.data.lights, bpy.data.node_groups):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
can = next(o for o in sc.objects if o.type == "MESH")
can.name = can.data.name = "JerryCan"
bpy.context.view_layer.update()
lo = [min((can.matrix_world @ v.co)[i] for v in can.data.vertices) for i in range(3)]
hi = [max((can.matrix_world @ v.co)[i] for v in can.data.vertices) for i in range(3)]
can.location.x -= (lo[0] + hi[0]) / 2  # centre it on the origin, standing on z=0
can.location.y -= (lo[1] + hi[1]) / 2
can.location.z -= lo[2]

# --- the decal artwork: white stencil lettering in a thin frame, on transparent, rendered once on the CPU
art = bpy.data.scenes.new("DecalArt")
cu = bpy.data.curves.new("DecalText", "FONT")
cu.body, cu.align_x, cu.align_y, cu.size, cu.space_character, cu.offset = "DIESEL", "CENTER", "CENTER", 1.0, 1.18, 0.018
txt = bpy.data.objects.new("DecalText", cu)
art.collection.objects.link(txt)
white = bpy.data.materials.new("DecalInk")
nt = white.node_tree
nt.nodes.clear()
em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value = (0.92, 0.9, 0.86, 1)
nt.links.new(em.outputs[0], out.inputs["Surface"])
cu.materials.append(white)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
w = txt.evaluated_get(dg).dimensions.x
h = txt.evaluated_get(dg).dimensions.y
fw, fh, t = w + 0.62, h + 0.5, 0.07  # frame: outer size and line width
frame = bpy.data.meshes.new("DecalFrame")
v = [(-fw / 2, -fh / 2, 0), (fw / 2, -fh / 2, 0), (fw / 2, fh / 2, 0), (-fw / 2, fh / 2, 0)]
v += [(x - t * (1 if x > 0 else -1), y - t * (1 if y > 0 else -1), 0) for x, y, _ in v]
frame.from_pydata(v, [], [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
frame.materials.append(white)
fo = bpy.data.objects.new("DecalFrame", frame)
art.collection.objects.link(fo)
cam = bpy.data.objects.new("DecalCam", bpy.data.cameras.new("DecalCam"))
cam.data.type, cam.data.ortho_scale = "ORTHO", fw + 0.04
cam.location = (0, 0, 5)
art.collection.objects.link(cam)
art.camera = cam
r = art.render
r.engine, r.film_transparent = "CYCLES", True
art.cycles.device, art.cycles.samples = "CPU", 16
r.resolution_x, r.resolution_y, r.resolution_percentage = 1024, round(1024 * (fh + 0.04) / (fw + 0.04)), 100
r.image_settings.file_format, r.image_settings.color_mode = "PNG", "RGBA"
art.view_settings.view_transform = "Standard"
r.filepath = os.path.abspath(decal_png)
os.makedirs(os.path.dirname(r.filepath), exist_ok=True)
bpy.ops.render.render(write_still=True, scene=art.name)
for o in (txt, fo, cam):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.scenes.remove(art)

me = can.data
me.calc_loop_triangles()
print("@@JSON@@" + json.dumps({"ok": True, "object": can.name, "tris": len(me.loop_triangles),
                               "dims_m": [round(x, 3) for x in can.dimensions], "decal": decal_png,
                               "decal_px": [r.resolution_x, r.resolution_y]}))
