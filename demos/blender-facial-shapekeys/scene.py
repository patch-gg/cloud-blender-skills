"""The input for blender-facial-shapekeys: a stylized head from face.py (clean loops around a real mouth, eyelids,
brows, ears, teeth and tongue as islands of one Head mesh), separate eyes, and a neck and shoulders to sit it on.
Run in the session: cloud.py run scene.py -- face.py"""
import importlib.util
import json
import math
import sys

import bmesh
import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
spec = importlib.util.spec_from_file_location("face", args[0] if args else "face.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

HEAD_Z = 0.355           # skull centre above the floor


def principled(name, color, rough, sss=0.0, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.006
    m.diffuse_color = (*color, 1)
    return m


def blush(mat, points, color=(0.86, 0.16, 0.16), radius=0.032, amount=0.6):
    """A soft flush over the cheeks: distance to each point in the head's own space, mixed into the base colour."""
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    near = None
    for p in points:
        dist = nt.nodes.new("ShaderNodeVectorMath")
        dist.operation = "DISTANCE"
        dist.inputs[1].default_value = tuple(p)
        nt.links.new(tc.outputs["Object"], dist.inputs[0])
        if near is None:
            near = dist.outputs["Value"]
        else:
            mn = nt.nodes.new("ShaderNodeMath")
            mn.operation = "MINIMUM"
            nt.links.new(near, mn.inputs[0])
            nt.links.new(dist.outputs["Value"], mn.inputs[1])
            near = mn.outputs[0]
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, radius
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = amount, 0.0
    nt.links.new(near, mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = b.inputs["Base Color"].default_value[:]
    mix.inputs[7].default_value = (*color, 1)
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])


def eye_material():
    m = bpy.data.materials.get("M_Eye") or bpy.data.materials.new("M_Eye")
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc, nrm, sep = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeVectorMath"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nrm.operation = "NORMALIZE"
    mr, ramp = nt.nodes.new("ShaderNodeMapRange"), nt.nodes.new("ShaderNodeValToRGB")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.85, -1.0   # -Y is the gaze
    nt.links.new(tc.outputs["Object"], nrm.inputs[0])
    nt.links.new(nrm.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    cr = ramp.color_ramp
    stops = [(0.0, (0.80, 0.79, 0.77)), (0.30, (0.80, 0.79, 0.77)), (0.335, (0.016, 0.010, 0.006)),
             (0.375, (0.10, 0.045, 0.016)), (0.62, (0.24, 0.12, 0.04)), (0.80, (0.09, 0.04, 0.012)),
             (0.825, (0.003, 0.003, 0.003)), (1.0, (0.003, 0.003, 0.003))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Specular IOR Level"].default_value = 0.6
    m.diffuse_color = (0.85, 0.85, 0.85, 1)
    return m


def mesh_object(name, verts, faces, mats, smooth=True, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs is not None:
        me.uv_layers.new(name="UVMap").uv.foreach_set("vector", np.array(uvs, np.float32).ravel())
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def lathe(name, profile, seg, mat, sy=1.0):
    """Surface of revolution around Z from (radius, z) pairs, capped at both ends, squashed in Y by sy."""
    verts, faces, uvs = [], [], []
    for r, z in profile:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((r * math.cos(a), sy * r * math.sin(a), z))
    n = len(profile)
    for j in range(n - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            faces.append((j * seg + i, j * seg + i2, (j + 1) * seg + i2, (j + 1) * seg + i))
            v0, v1 = 0.1 + 0.8 * j / (n - 1), 0.1 + 0.8 * (j + 1) / (n - 1)
            uvs += [(i / seg, v0), ((i + 1) / seg, v0), ((i + 1) / seg, v1), (i / seg, v1)]
    verts += [(0, 0, profile[0][1]), (0, 0, profile[-1][1])]
    for i in range(seg):                                  # caps: discs in the bottom and top strips
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        faces.append((n * seg, (i + 1) % seg, i))
        uvs += [(0.25, 0.05), (0.25 + 0.04 * math.cos(a1), 0.05 + 0.04 * math.sin(a1)),
                (0.25 + 0.04 * math.cos(a0), 0.05 + 0.04 * math.sin(a0))]
        faces.append((n * seg + 1, (n - 1) * seg + i, (n - 1) * seg + (i + 1) % seg))
        uvs += [(0.75, 0.95), (0.75 + 0.04 * math.cos(a0), 0.95 + 0.04 * math.sin(a0)),
                (0.75 + 0.04 * math.cos(a1), 0.95 + 0.04 * math.sin(a1))]
    return mesh_object(name, verts, faces, [mat], uvs=uvs)


for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

face = F.Face()
mats = [principled("M_Skin", (0.80, 0.43, 0.29), 0.42, sss=0.12, spec=0.45),
        principled("M_Lips", (0.50, 0.13, 0.12), 0.34, sss=0.1),
        principled("M_Mouth", (0.06, 0.008, 0.011), 0.4),
        principled("M_Teeth", (0.86, 0.84, 0.79), 0.28),
        principled("M_Tongue", (0.58, 0.12, 0.14), 0.36),
        principled("M_Brows", (0.048, 0.026, 0.018), 0.72, spec=0.3)]
blush(mats[0], [face.cheek["l"], face.cheek["r"]])
head = mesh_object("Head", face.rest, face.faces, mats)
me = head.data
me.polygons.foreach_set("material_index", face.mat)
uv = me.uv_layers.new(name="UVMap")
uv.uv.foreach_set("vector", np.array([c for f in face.uvs for c in f], np.float32).ravel())
head.location = (0, 0, HEAD_Z)
sub = head.modifiers.new("Subdivision", "SUBSURF")       # after the shape keys (they evaluate first)
sub.levels, sub.render_levels = 1, 2

eye_m = eye_material()
eyes = []
for side, sx in (("L", 1), ("R", -1)):
    ctr, fwd, _, _ = face.eye[side.lower()]
    em = bpy.data.meshes.new(f"Eye{side}")
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=F.RE, calc_uvs=True)
    bm.to_mesh(em)
    bm.free()
    em.shade_smooth()
    em.materials.append(eye_m)
    e = bpy.data.objects.new(f"Eye{side}", em)
    bpy.context.scene.collection.objects.link(e)
    e.parent = head
    e.location = tuple(ctr)
    e.rotation_euler = (0, 0, math.atan2(fwd[0], -fwd[1]))   # local -Y looks along the gaze
    eyes.append(e.name)

skin = mats[0]
shirt = principled("M_Shirt", (0.030, 0.033, 0.040), 0.65, spec=0.3)
neck = lathe("Neck", [(0.050, 0.10), (0.050, 0.17), (0.052, 0.23), (0.056, 0.29)], 40, skin)
body = lathe("Body", [(0.020, 0.0), (0.150, 0.0), (0.168, 0.04), (0.165, 0.09), (0.150, 0.13), (0.118, 0.163),
                      (0.075, 0.180), (0.048, 0.184)], 64, shirt, sy=0.58)


def beanie():
    """A knit beanie over the skull (a prop; the face rig never touches it)."""
    na, nt = 72, 16
    az = np.arange(na) * 2 * np.pi / na
    brim = 0.48 + 0.18 * np.cos(az)                     # low at the back, above the brows at the front
    rows = []
    for t, off in ((-0.020, 0.000), (-0.012, 0.0045), (0.0, 0.0085), (0.06, 0.0092), (0.12, 0.0088), (0.15, 0.0062)):
        rows.append((brim + t, off))                    # the folded cuff, rolled under at the bottom
    for k in range(1, nt + 1):
        t = k / (nt + 1)
        rows.append((brim + 0.15 + (np.pi / 2 - brim - 0.15) * t ** 0.85, 0.0062 + 0.012 * np.sin(np.pi * t * 0.8)))
    verts = []
    for el, off in rows:
        d = F._dir(az, el)
        p = F.shell(d)
        verts += list(p + F._n(p) * off)
    top = F.shell(np.array([0.0, 0.0, 1.0]))
    verts.append(top + np.array([0.0, 0.0, 0.0062 + 0.004]))
    nr = len(rows)
    faces, uvs = [], []
    for r in range(nr - 1):
        for i in range(na):
            i2 = (i + 1) % na
            faces.append((r * na + i, r * na + i2, (r + 1) * na + i2, (r + 1) * na + i))
            uvs += [(i / na, r / nr), ((i + 1) / na, r / nr), ((i + 1) / na, (r + 1) / nr), (i / na, (r + 1) / nr)]
    for i in range(na):
        faces.append((nr * na, (nr - 1) * na + i, (nr - 1) * na + (i + 1) % na))
        uvs += [((i + 0.5) / na, 1.0), (i / na, (nr - 1) / nr), ((i + 1) / na, (nr - 1) / nr)]
    ob = mesh_object("Beanie", verts, faces, [knit()], uvs=uvs)
    ob.parent = head
    ob.modifiers.new("Subdivision", "SUBSURF").render_levels = 2
    return ob


def knit():
    m = bpy.data.materials.new("M_Knit")
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.016, 0.017, 0.020, 1)
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Sheen Weight"].default_value = 0.12
    tc, sep, at, mul, sn, bump = (nt.nodes.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeSeparateXYZ",
                                                            "ShaderNodeMath", "ShaderNodeMath", "ShaderNodeMath",
                                                            "ShaderNodeBump"))
    at.operation, mul.operation, sn.operation = "ARCTAN2", "MULTIPLY", "SINE"
    mul.inputs[1].default_value = 64.0                  # ribs around the head
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], at.inputs[0])
    nt.links.new(sep.outputs["Y"], at.inputs[1])
    nt.links.new(at.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], sn.inputs[0])
    nt.links.new(sn.outputs[0], bump.inputs["Height"])
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (0.03, 0.03, 0.035, 1)
    return m


hat = beanie()
print("@@JSON@@" + json.dumps({"ok": True, "head": head.name, "props": [hat.name], "verts": len(me.vertices), "faces": len(me.polygons),
                               "islands": len(face.blocks), "eyes": eyes, "body": [neck.name, body.name]}))
