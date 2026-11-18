"""Presentation: the turntable rig's lights and backdrop without the orbit, the display framed by its width,
each tile popping in in the order batch_process went through the files (sorted names), and a running count
bottom left, flagged ones bottom right in pink. 1280x720, frames 1-96, EEVEE with ray tracing, AgX."""
import json
import math

import bpy
from mathutils import Vector

FRAMES, FIRST, STEP = 96, 4, 4      # tile i pops in at FIRST + STEP * i
INK = (0.0056, 0.0056, 0.0056, 1)   # #111 in linear
PINK = (0.913, 0.045, 0.637, 1)     # #F53CD1 in linear (shown at 0.6: AgX washes bright pink to pastel)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
pivot = bpy.data.objects["LD_Pivot"]
pivot.animation_data_clear()
pivot.rotation_euler = (0, 0, 0)

# ---- camera: fit the tiles (and the front step's edge) by width, then a slow push in
cam = sc.camera
cam.parent = None
cam.animation_data_clear()
cam.data.lens = 50
cam.data.dof.use_dof = False
hfov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
el = math.radians(22)
cam.rotation_euler = (math.pi / 2 - el, 0, 0)          # looking along +y, tilted down by el
bpy.context.view_layer.update()


def root(o):
    while o.parent:
        o = o.parent
    return o


pts = [o.matrix_world @ Vector(c) for o in bpy.data.objects
       if o.type == "MESH" and root(o).name.startswith("Tile_") for c in o.bound_box]
xs = [p.x for p in pts]
cx = (max(xs) + min(xs)) / 2
pts = [Vector((cx + (p.x - cx) * 1.1, p.y, p.z)) for p in pts]  # ~5% side margins
loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), [v for p in pts for v in p])
fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
dist = (sum(pts, Vector()) / len(pts) - Vector(loc)).length
cam.data.clip_start, cam.data.clip_end = 0.05, dist * 10
for f, k in ((1, 0.045), (FRAMES, -0.015)):        # push in by 6% of the distance over the clip
    cam.location = Vector(loc) - fwd * dist * k
    cam.keyframe_insert("location", frame=f)
bpy.context.view_layer.update()


def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):           # 5.2 still has the legacy accessor
        return list(act.fcurves)
    out = []
    for layer in act.layers:              # slotted actions
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


for fc in fcurves(cam):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# ---- tiles pop in, in the batch's order
tiles = sorted((o for o in bpy.data.objects if o.name.startswith("Tile_")), key=lambda o: o.name[5:])
starts = []
for i, t in enumerate(tiles):
    f = FIRST + STEP * i
    starts.append(f)
    for fr, s in ((f, 0.0), (f + 4, 1.1), (f + 7, 1.0)):
        t.scale = (s, s, s)
        t.keyframe_insert("scale", frame=fr)
    t.scale = (0, 0, 0)
    t.keyframe_insert("scale", frame=1)

# ---- running counts riding with the camera: files bottom left, flagged (pink) bottom right
D = 1.0
half_w = math.tan(hfov / 2) * D
half_h = half_w * sc.render.resolution_y / sc.render.resolution_x


def flat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Color"].default_value = color
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def counter(prefix, events, word, x, align, mat):
    """One text object per value, each shown from its event frame until the next (no handlers in a render)."""
    for o in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for i, on in enumerate(events):
        n = i + 1
        cu = bpy.data.curves.new(f"{prefix}{n:02d}", "FONT")
        cu.body = word(n)
        cu.size, cu.align_x = 0.015, align
        cu.materials.append(mat)
        t = bpy.data.objects.new(f"{prefix}{n:02d}", cu)
        sc.collection.objects.link(t)
        t.parent = cam
        t.location = (x, -half_h + 0.03, -D)
        off = events[i + 1] if i + 1 < len(events) else FRAMES + 1
        for fr, s in [(1, 0.0), (on, 1.0)] + ([(off, 0.0)] if off <= FRAMES else []):
            t.scale = (s, s, s)
            t.keyframe_insert("scale", frame=fr)
        for fc in fcurves(t):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


flagged = [f + 2 for f, t in zip(starts, tiles) if any(c.name.startswith("Flag_") for c in t.children)]
counter("Count_", [f + 2 for f in starts], lambda n: f"{n} file" + ("" if n == 1 else "s"), -half_w + 0.032,
        "LEFT", flat("M_Ink", INK))
counter("Flagged_", flagged, lambda n: f"{n} flagged", half_w - 0.032, "RIGHT",
        flat("M_FlagInk", tuple(c * 0.6 for c in PINK[:3]) + (1,)))

# ---- stage: the rig's 18% grey backdrop behind the white display, EEVEE ray tracing, AgX
sc.eevee.use_raytracing = True
sc.eevee.taa_render_samples = 32
sc.eevee.shadow_ray_count, sc.eevee.shadow_step_count = 4, 12  # the rig's big soft lights are grainy at 1 ray
sc.view_settings.view_transform = "AgX"
sc.view_settings.exposure = -1.0
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.frame_set(FRAMES)
print("@@JSON@@" + json.dumps({"ok": True, "camera": cam.name, "distance": round(dist, 2), "tiles": len(tiles),
                               "pop_frames": [starts[0], starts[-1] + 7], "files": len(starts),
                               "flagged": len(flagged)}))
