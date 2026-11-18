"""Presentation: the recipe's stages in order on the one asset, each held about half a second with a small
label, then a slow turntable of the exported prop. Every stage shows the copy snap.py kept of it (and the
LODs, the part QA caught, the re-imported .glb). Labels and texture cards ride on the camera; the camera and
lights (turntable.py's rig) drift slowly through the stages and speed up into the turntable.
Run in the session after turntable.py: cloud.py run present.py -- present.json"""
import json
import math
import sys

import bmesh
import bpy
from bpy_extras import anim_utils
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

N = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sc = bpy.context.scene
cam, pivot = bpy.data.objects["LD_Cam"], bpy.data.objects["LD_Pivot"]
PINK = (0.913, 0.045, 0.639)                     # #F53CD1, linear
WHITE = (0.9, 0.9, 0.9)

# ---------------------------------------------------------------- timeline (frames at 24 fps)
CI = N.get("caught_lod")                       # the LOD whose floating part QA caught (None: nothing caught)
STAGES = [("blockout", 12), ("bevels", 12), ("uvs", 12), ("bake", 12), ("material", 12), ("wear", 12),
          ("lods", 14), ("qa_caught", 9), ("qa", 10), ("export", 13), ("turntable", 66)]
if CI is None:
    STAGES = [s for s in STAGES if s[0] != "qa_caught"]
span, f = {}, 1
for name, n in STAGES:
    span[name] = (f, f + n - 1)
    f += n
END = f - 1
sc.frame_start, sc.frame_end = 1, END
sc.render.fps = 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100

# ---------------------------------------------------------------- clean a previous run
for ob in [o for o in bpy.data.objects if o.name.startswith("PR_")]:
    bpy.data.objects.remove(ob)
for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
    for d in [d for d in coll if d.name.startswith("PR_") and d.users == 0]:
        coll.remove(d)
pres = bpy.data.collections.get("Present") or bpy.data.collections.new("Present")
if pres.name not in sc.collection.children:
    sc.collection.children.link(pres)
for ob in sc.objects:                            # nothing renders unless a stage below shows it
    if ob.name.startswith("LD_") or ob.type in ("CAMERA", "LIGHT"):
        continue
    ob.animation_data_clear()
    ob.hide_render = True


def show(ob, *stages):
    """Key hide_render so ob renders only during the given stages."""
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=1)
    for s in stages:
        a, b = span[s]
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=a)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=b + 1)
    ob.hide_set(False)


# ---------------------------------------------------------------- camera: slow drift, then the turntable
def angle_at(frame):
    """Pivot angle (deg): 0.15 deg/frame through the stages, eased up to 1.8 deg/frame for the turntable,
    eased down over the last 16 frames."""
    t0 = span["turntable"][0]
    a, v = 26.0, 0.0
    for k in range(1, frame):
        if k < t0:
            v = 0.15
        elif k < t0 + 14:
            s = (k - t0) / 14
            v = 0.15 + (1.8 - 0.15) * s * s * (3 - 2 * s)
        elif k < END - 16:
            v = 1.8
        else:
            s = (k - (END - 16)) / 16
            v = 1.8 + (0.6 - 1.8) * s * s * (3 - 2 * s)
        a += v
    return a


pivot.animation_data_clear()
for fr in range(1, END + 2):
    pivot.rotation_euler = (0, 0, math.radians(angle_at(fr)))
    pivot.keyframe_insert("rotation_euler", index=2, frame=fr)
ad = pivot.animation_data
for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
cam.data.dof.use_dof = False

# ---------------------------------------------------------------- look
bd = bpy.data.objects["LD_Backdrop"].material_slots[0].material
b = next(n for n in bd.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.03, 0.03, 0.034, 1)
b.inputs["Roughness"].default_value = 0.7
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.view_settings.exposure = N.get("exposure", -1.2)
GAIN = 2 ** -sc.view_settings.exposure                    # overlays read the same at any exposure
LINEUP = tuple(st for st in ("lods", "qa_caught", "qa") if st in span)
SHIFT = N.get("lineup_shift", -0.085)                     # lens shift while the small LODs stand in a row
cam.data.animation_data_clear()
for stage, val in (("blockout", 0.0), ("lods", SHIFT), ("export", 0.0)):
    cam.data.shift_y = val
    cam.data.keyframe_insert("shift_y", frame=span[stage][0])
cad = cam.data.animation_data
for fc in anim_utils.action_get_channelbag_for_slot(cad.action, cad.action_slot).fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "CONSTANT"


# ---------------------------------------------------------------- materials
def emission(name, color, strength=1.0, image=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    if image is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image, tex.interpolation = image, "Cubic"
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def overlay_only(ob):
    """Seen by the camera only: no shadows, no reflections in the steel chips."""
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
                 "visible_volume_scatter"):
        setattr(ob, attr, False)


# ---------------------------------------------------------------- screen-space items (parented to the camera)
D = 0.5                                                   # metres in front of the lens
W = D * cam.data.sensor_width / cam.data.lens            # visible width there (sensor fit: width)
H = W * 720 / 1280
PX = W / 1280                                             # one pixel, in metres at D


def at_screen(ob, u, v, z=0.0, shift=0.0):
    """Place a camera child at screen position (u, v) in pixels from the bottom-left (shift: the lens shift
    while it shows)."""
    ob.parent = cam
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = (u * PX - W / 2, v * PX - H / 2 + shift * W, -D + z)
    ob.rotation_euler = (0, 0, 0)
    pres.objects.link(ob)
    overlay_only(ob)
    return ob


def text(name, body, u, v, px=26, color=WHITE, align="LEFT", shift=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x = body, px * PX, align
    if N.get("font"):
        cu.font = bpy.data.fonts.load(N["font"], check_existing=True)
    pink = color == PINK
    cu.materials.append(emission(f"PR_txt_{'pink' if pink else 'white'}", color, (1.0 if pink else 1.6) * GAIN))
    return at_screen(bpy.data.objects.new(name, cu), u, v, shift=shift)


def small(image, px):
    """A copy of image at 2x the card's pixel size, packed: Cycles has no mipmaps, so a 2k map squeezed
    onto a 160 px card would sparkle."""
    name = f"PR_{image.name}_{px}"
    img = bpy.data.images.get(name)
    if img is None:
        img = image.copy()
        img.name = name
        img.scale(2 * px, 2 * px)
        img.filepath_raw = ""
        img.pack()
    return img


def card(name, image, u, v, px):
    me = bpy.data.meshes.new(name)
    h = px * PX / 2
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, co in zip(uv.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp.uv = co
    me.materials.append(emission(f"PR_{name}", (1, 1, 1), 0.7 * GAIN, small(image, px)))
    return at_screen(bpy.data.objects.new(name, me), u, v)


def label(stage, body, color=WHITE):
    show(text(f"PR_label_{stage}", body, 52, 46, 26, color, shift=SHIFT if stage in LINEUP else 0.0), stage)


# ---------------------------------------------------------------- stages 1-6: the copies snap.py kept
for stage in ("blockout", "bevels", "uvs", "bake", "material", "wear"):
    for ob in bpy.data.collections[f"STG_{stage}"].objects:
        show(ob, stage)
label("blockout", "blockout")
label("bevels", f"bevels · {N['high_tris']:,} tris")
label("uvs", f"uvs · {N['texel']:,} px/m")
label("bake", f"bake · {N['low_tris']:,} tris")
label("material", "material")
label("wear", "wear")

# the unwrap as a card, the way the UV editor shows it: islands filled with the grid, outlined, on a dark card
uv_src = bpy.data.collections["STG_uvs"].objects[0].data
grid = small(bpy.data.images["PR_UVGrid"], 300)
CU, CV, CS = 1070, 360, 300
bg = bpy.data.meshes.new("PR_card_uvs")
h = (CS + 16) * PX / 2
bg.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
bg.materials.append(emission("PR_card_dark", (0.06, 0.06, 0.065), GAIN))
show(at_screen(bpy.data.objects.new("PR_card_uvs", bg), CU, CV), "uvs")
for name, z, fill in (("PR_uvfill", 0.0003, True), ("PR_uvwire", 0.0006, False)):
    bm = bmesh.new()
    uvw = bm.loops.layers.uv.new("UVMap")
    uvl = uv_src.uv_layers.active.data
    for poly in uv_src.polygons:
        pts = [uvl[i].uv.copy() for i in poly.loop_indices]
        fc_ = bm.faces.new([bm.verts.new(((p.x - 0.5) * CS * PX, (p.y - 0.5) * CS * PX, 0)) for p in pts])
        for lp, p in zip(fc_.loops, pts):
            lp[uvw].uv = p
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if fill:
        me.materials.append(emission("PR_uvfill", (1, 1, 1), 0.7 * GAIN, grid))
    else:
        wm = ob.modifiers.new("wire", "WIREFRAME")
        wm.thickness, wm.use_even_offset, wm.use_relative_offset = 1.3 * PX, True, False
        me.materials.append(emission("PR_uvwire", (0.85, 0.85, 0.85), GAIN))
    show(at_screen(ob, CU, CV, z=z), "uvs")

# the bake's maps as cards
for i, key in enumerate(("N", "AO", "CURV")):
    show(card(f"PR_card_bake_{key}", bpy.data.images[f"T_JerryCan_{key}"], 1110, 540 - i * 180, 160), "bake")

# ---------------------------------------------------------------- stages 7-8: the LOD lineup and the QA catch
def screen_of(world, frame):
    sc.frame_set(frame)
    p = world_to_camera_view(sc, cam, world)
    return p.x * 1280, p.y * 720


mid = (span["lods"][0] + span["qa"][1]) // 2
sc.frame_set(mid)
th = math.radians(angle_at(mid))
row = Vector((math.cos(th), math.sin(th), 0))           # the camera's right, at the middle of the lineup
toward = Vector((math.sin(th), -math.cos(th), 0))       # toward the camera
S, GAP = N.get("lineup_scale", 0.55), N.get("lineup_gap", 0.31)
centre = Vector((0, 0, 0)) + toward * N.get("lineup_forward", 0.0)
lods = [bpy.data.objects[f"SM_JerryCan_LOD{i}"] for i in range(4)]
base = {}


def lineup(name, mesh, i, stages):
    ob = bpy.data.objects.new(name, mesh)
    ob.matrix_world = Matrix.Translation(base[i]) @ Matrix.Diagonal((S, S, S, 1))
    pres.objects.link(ob)
    show(ob, *stages)
    return ob


for i, src in enumerate(lods):
    base[i] = centre + row * (i - 1.5) * GAP
    u, v = screen_of(base[i] + toward * 0.06, mid)
    if i != CI:
        lineup(f"PR_lod{i}", src.data, i, LINEUP)
        show(text(f"PR_lodlabel{i}", f"lod{i} · {N['lods'][i]:,}", u, v - 28, 17, align="CENTER", shift=SHIFT),
             *LINEUP)
    else:  # as make_lods.py made it (QA's catch included), then without the part QA caught
        lineup(f"PR_lod{i}_made", bpy.data.objects[f"QA_SM_JerryCan_LOD{i}"].data, i, ("lods",))
        lineup(f"PR_lod{i}", src.data, i, ("qa_caught", "qa"))
        show(text(f"PR_lodlabel{i}_made", f"lod{i} · {N['lods_made'][i]:,}", u, v - 28, 17, align="CENTER",
                  shift=SHIFT), "lods", "qa_caught")
        show(text(f"PR_lodlabel{i}", f"lod{i} · {N['lods'][i]:,}", u, v - 28, 17, align="CENTER", shift=SHIFT), "qa")


def ring(u, v):
    """A pink ring around what QA caught, with a small pink label."""
    me = bpy.data.meshes.new("PR_ring")
    bm = bmesh.new()
    r0, r1, seg = 34 * PX, 38 * PX, 48
    outer = [bm.verts.new((r1 * math.cos(2 * math.pi * k / seg), r1 * math.sin(2 * math.pi * k / seg), 0))
             for k in range(seg)]
    inner = [bm.verts.new((r0 * math.cos(2 * math.pi * k / seg), r0 * math.sin(2 * math.pi * k / seg), 0))
             for k in range(seg)]
    for k in range(seg):
        bm.faces.new((outer[k], outer[(k + 1) % seg], inner[(k + 1) % seg], inner[k]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(emission("PR_pink", PINK, GAIN))
    show(at_screen(bpy.data.objects.new("PR_ring", me), u, v, shift=SHIFT), "qa_caught")
    show(text("PR_caught_label", "floating part", u + 46, v + 22, 17, PINK, shift=SHIFT), "qa_caught")


if CI is not None:
    frag = lineup("PR_caught", bpy.data.objects[f"QA_SM_JerryCan_LOD{CI}_caught"].data.copy(), CI, ("qa_caught",))
    frag.data.materials.clear()
    frag.data.materials.append(emission("PR_pink", PINK, GAIN))
    fc = Matrix.Translation(base[CI]) @ Matrix.Diagonal((S, S, S, 1)) @ Vector(N["caught_at"])
    ring(*screen_of(fc, span["qa_caught"][0] + 4))
    label("qa_caught", "qa")
label("lods", "lods")
label("qa", "qa ✓")

# ---------------------------------------------------------------- stage 9 + turntable: the exported .glb
glb = bpy.data.objects[N["glb_object"]]
show(glb, "export", "turntable")
imgs = {n.image.name: n.image for m in glb.data.materials if m for n in m.node_tree.nodes
        if n.type == "TEX_IMAGE" and n.image}
order = sorted(imgs, key=lambda k: (0 if "_BC" in k else 1 if "_N" in k else 2))
for i, k in enumerate(order[:3]):
    show(card(f"PR_card_glb_{i}", imgs[k], 1110, 540 - i * 180, 160), "export")
label("export", f"export · glb {N['glb_kb']:,} kb · fbx {N['fbx_kb']:,} kb")

sc.frame_set(1)
print("@@JSON@@" + json.dumps({"ok": True, "frames": END, "seconds": round(END / 24, 2),
                               "stages": {k: list(v) for k, v in span.items()},
                               "angle_deg": [round(angle_at(1), 1), round(angle_at(END), 1)]}))
