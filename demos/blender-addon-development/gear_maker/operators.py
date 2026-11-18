import math

import bmesh
import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty

METALS = (("STEEL", "Steel", ""), ("BRASS", "Brass", ""))
LOOK = {"STEEL": ((0.62, 0.63, 0.65), 0.24), "BRASS": ((0.62, 0.38, 0.14), 0.3)}  # base colour, roughness


def _inv(a):
    return math.tan(a) - a


def gear_outline(teeth, module, pressure=math.radians(20.0), flank=6):
    """(angle, radius) around an involute spur gear, counter-clockwise and increasing in angle."""
    r = module * teeth / 2                        # pitch circle
    rb = r * math.cos(pressure)                   # base circle: the involute starts here
    ra = r + module                               # tip
    rr = max(r - 1.25 * module, module)           # root
    pitch = 2 * math.pi / teeth
    half = math.pi / (2 * teeth) + _inv(pressure)  # half a tooth, as an angle, at the base circle
    r0 = max(rb, rr)

    def side(R):                                  # half the tooth's angle at radius R
        return max(half - _inv(math.acos(min(1.0, rb / R))), 0.06 * pitch)
    rs = [r0 + (ra - r0) * k / flank for k in range(flank + 1)]
    pts = []
    for i in range(teeth):
        c = i * pitch
        if rr < rb:
            pts.append((c - side(r0), rr))                       # straight flank below the base circle
        pts += [(c - side(R), R) for R in rs]                    # right flank, up
        pts += [(c + side(ra) * t, ra) for t in (-0.5, 0.0, 0.5)]  # tip
        pts += [(c + side(R), R) for R in reversed(rs)]          # left flank, down
        if rr < rb:
            pts.append((c + side(r0), rr))
        pts.append((c + pitch / 2, rr))                          # root, between teeth
    return pts, rr


def _arc(r, a0, a1, steps):
    return [(r * math.cos(a0 + (a1 - a0) * k / steps), r * math.sin(a0 + (a1 - a0) * k / steps))
            for k in range(steps + 1)]


def build_gear(me, teeth, module, width, bore, spokes):
    """Fill `me` with a closed gear: the tooth outline, the bore and (with spokes) the windows between
    straight spokes as loops, triangle-filled (inner loops stay holes), then extruded with walls."""
    outline, rr = gear_outline(teeth, module)
    rim = rr - 1.4 * module
    rb = min(max(bore, 0.002), rim * 0.5)
    hub = max(rb + 1.8 * module, 0.25 * rim)
    loops = [[(R * math.cos(a), R * math.sin(a)) for a, R in outline],
             _arc(rb, 0, 2 * math.pi, 32)[:-1]]
    w = max(1.4 * module, 0.18 * rim)                         # spoke width, the same from hub to rim
    if spokes and rim - hub > 2 * module and w / 2 < hub:
        for j in range(spokes):
            t0, t1 = 2 * math.pi * j / spokes, 2 * math.pi * (j + 1) / spokes
            r0, r1 = t0 + math.asin(w / 2 / rim), t1 - math.asin(w / 2 / rim)
            h0, h1 = t0 + math.asin(w / 2 / hub), t1 - math.asin(w / 2 / hub)
            if h1 - h0 > 0.05:
                loops.append(_arc(rim, r0, r1, 16) + _arc(hub, h1, h0, 8))
    bm = bmesh.new()
    edges = []
    for loop in loops:
        vs = [bm.verts.new((x, y, 0.0)) for x, y in loop]
        edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    flat = [v.co.xy.copy() for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    bm = bmesh.new()
    top = [bm.verts.new((p.x, p.y, width / 2)) for p in flat]
    bot = [bm.verts.new((p.x, p.y, -width / 2)) for p in flat]
    used = {}
    for f in faces:
        bm.faces.new([top[i] for i in f])
        bm.faces.new([bot[i] for i in reversed(f)])
        for a, b in zip(f, f[1:] + f[:1]):
            used[frozenset((a, b))] = used.get(frozenset((a, b)), 0) + 1
    for f in faces:                                              # walls on the open edges
        for a, b in zip(f, f[1:] + f[:1]):
            if used[frozenset((a, b))] == 1:
                bm.faces.new((top[a], top[b], bot[b], bot[a]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(30))
    return len(faces)


def gear_material(metal):
    """One shared material per metal, so a new gear never lands on an empty slot."""
    name = f"Gear {metal.title()}"
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")  # by type: names are localized
        color, rough = LOOK[metal]
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = rough
        m.diffuse_color = (*color, 1)
    return m


class GEARMAKER_PG_settings(bpy.types.PropertyGroup):
    teeth: IntProperty(name="Teeth", default=16, min=8, max=200)
    module: FloatProperty(name="Module", default=0.01, min=0.001, soft_max=0.1, unit="LENGTH",
                          description="Tooth size: pitch diameter / teeth")
    width: FloatProperty(name="Width", default=0.02, min=0.001, soft_max=0.2, unit="LENGTH")
    bore: FloatProperty(name="Bore", default=0.008, min=0.0, soft_max=0.1, unit="LENGTH")
    spokes: IntProperty(name="Spokes", default=0, min=0, max=12)
    metal: EnumProperty(name="Metal", items=METALS, default="STEEL")


class GEARMAKER_OT_add_gear(bpy.types.Operator):
    """Add an involute spur gear at the 3D cursor"""  # tooltip
    bl_idname = "gear_maker.add_gear"
    bl_label = "Gear"
    bl_options = {"REGISTER", "UNDO"}  # UNDO: one undo step; REGISTER: redo panel

    teeth: IntProperty(name="Teeth", default=16, min=8, max=200)
    module: FloatProperty(name="Module", default=0.01, min=0.001, soft_max=0.1, unit="LENGTH")
    width: FloatProperty(name="Width", default=0.02, min=0.001, soft_max=0.2, unit="LENGTH")
    bore: FloatProperty(name="Bore", default=0.008, min=0.0, soft_max=0.1, unit="LENGTH")
    spokes: IntProperty(name="Spokes", default=0, min=0, max=12)
    metal: EnumProperty(name="Metal", items=METALS, default="STEEL")

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        s = context.scene.gear_maker  # start from the panel settings
        for p in ("teeth", "module", "width", "bore", "spokes", "metal"):
            setattr(self, p, getattr(s, p))
        return self.execute(context)

    def execute(self, context):
        me = bpy.data.meshes.new(f"Gear_{self.teeth}")
        build_gear(me, self.teeth, self.module, self.width, self.bore, self.spokes)
        me.materials.append(gear_material(self.metal))
        ob = bpy.data.objects.new(me.name, me)
        ob.location = context.scene.cursor.location
        context.collection.objects.link(ob)
        prefs = context.preferences.addons[__package__].preferences
        if prefs.bevel:
            bev = ob.modifiers.new("Bevel", "BEVEL")
            bev.width, bev.segments, bev.limit_method = self.module * 0.12, 2, "ANGLE"
            bev.harden_normals = True
        for o in context.view_layer.objects:
            o.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        self.report({"INFO"}, f"Added {ob.name}: {self.teeth} teeth, pitch diameter "
                              f"{self.module * self.teeth:.3f} m")
        return {"FINISHED"}
