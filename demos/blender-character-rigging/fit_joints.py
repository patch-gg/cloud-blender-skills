"""Place the metarig's joints on the mesh (the skill's step 3: "the fit only scales").

Joints go to the pivot of rotation, inside the volume: legs and spine at cross-section centres, arms along
their medial axis (traced slice by slice from the upper arm to the fingertips; the elbow is where it bends
most, so the slight bend Rigify's IK needs comes from the mesh). Each bone keeps the metarig's roll
convention (align_roll to its old Z axis), and the right side is the mirror of the left.
Run in the session: cloud.py run fit_joints.py -- --metarig META_Body --mesh Body [--extra Shirt]
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


meta = bpy.data.objects[arg("--metarig", "META_Body")]
obs = [bpy.data.objects[arg("--mesh", "Body")]] + ([bpy.data.objects[arg("--extra")]] if arg("--extra") else [])
dg = bpy.context.evaluated_depsgraph_get()
V, E = [], []
for ob in obs:
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ed = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", ed)
    M = np.array(ob.matrix_world)
    E.append(ed.reshape(-1, 2) + sum(len(v) for v in V))
    V.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
    eo.to_mesh_clear()
V, E = np.concatenate(V), np.concatenate(E)
H = V[:, 2].max()


def cut(q, n):
    """Points where the surface crosses the plane through q with normal n (edge intersections)."""
    s = (V - q) @ n
    a, b = s[E[:, 0]], s[E[:, 1]]
    m = a * b < 0
    t = (a[m] / (a[m] - b[m]))[:, None]
    return V[E[m, 0]] + t * (V[E[m, 1]] - V[E[m, 0]])


def hcut(z, keep):
    """Horizontal section at height z, filtered by keep(P) -> bool mask."""
    P = cut(np.array([0.0, 0.0, z]), np.array([0.0, 0.0, 1.0]))
    return P[keep(P)] if len(P) else P


# ---------------------------------------------------------------- legs
crotch = None
for z in np.arange(0.25 * H, 0.65 * H, 0.0025):          # lowest height where the surface closes between the legs
    if len(hcut(z, lambda P: np.abs(P[:, 0]) < 0.01)):
        crotch = float(z)
        break
left = lambda P: P[:, 0] > 0.0                            # noqa: E731
hip_z, ankle_z = crotch + 0.055 * H, 0.05 * H
thigh_c = hcut(crotch - 0.03 * H, left).mean(0)
hip = Vector((thigh_c[0] + 0.01, thigh_c[1] + 0.045, hip_z))     # the femoral head sits behind the thigh's centre
ankle = Vector(hcut(ankle_z, left).mean(0))
knee = Vector(hcut((hip_z + ankle_z) / 2, left).mean(0))
line = hip.lerp(ankle, (hip.z - knee.z) / (hip.z - ankle.z))
knee.y = min(knee.y, line.y - 0.015)                      # a slight bend forward so the IK bends the right way
foot = V[(V[:, 0] > 0) & (V[:, 2] < 0.06 * H)]
y_front, y_back, x_foot = float(foot[:, 1].min()), float(foot[:, 1].max()), float(foot[:, 0].mean())
ball = Vector((x_foot, y_front + 0.32 * (y_back - y_front), 0.015 * H))
toe = Vector((x_foot, y_front + 0.015, 0.015 * H))
heel = (Vector((x_foot - 0.045, ankle.y + 0.035, 0.0)), Vector((x_foot + 0.045, ankle.y + 0.035, 0.0)))

# ---------------------------------------------------------------- spine: a set depth into each section
torso = lambda P: np.abs(P[:, 0]) < 0.13                  # noqa: E731


def spine_pt(z, f):
    P = hcut(z, torso)
    yf, yb = float(P[:, 1].min()), float(P[:, 1].max())
    return Vector((0.0, yb - f * (yb - yf), z))


neck_z, skull_z = 0.868 * H, 0.92 * H
sp = [spine_pt(hip_z + 0.01, 0.41), spine_pt(hip_z + 0.05 * H, 0.27), spine_pt(hip_z + 0.09 * H, 0.3),
      spine_pt(hip_z + 0.13 * H, 0.28), spine_pt(neck_z, 0.38)]
skull = Vector((0.0, float(hcut(skull_z + 0.03 * H, lambda P: np.abs(P[:, 0]) < 0.12)[:, 1].mean()) + 0.02, skull_z))
neck_mid = sp[4].lerp(skull, 0.5)                         # (a section here would catch the jaw)
top = Vector((0.0, skull.y, H))

# ---------------------------------------------------------------- arms (left): medial axis, slice by slice


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def march(p, d, step=0.015, n=90, radius=0.085):
    pts = [p]
    for _ in range(n):
        q = p + d * step
        P = cut(q, d)
        P = P[(P[:, 0] > 0) & (np.linalg.norm(P - q, axis=1) < radius)] if len(P) else P
        if len(P) < 4:
            break
        c = P.mean(0)
        d = unit(0.5 * d + 0.5 * unit(c - p))
        p = c
        pts.append(p)
    return np.array(pts)


P0 = hcut(0.75 * H, left)                                 # a section through the upper arm, clear of the torso:
xs = np.sort(P0[:, 0])                                    # the arm is what lies past the widest gap in x
gaps = np.where(xs[:-1] > 0.08, np.diff(xs), 0)
gi = int(np.argmax(gaps))
start = P0[P0[:, 0] > xs[gi] + gaps[gi] / 2].mean(0)
down = march(start, unit(np.array([0.5, 0.0, -0.8])))
k = 4
ang = [0.0] * len(down)
for i in range(k, len(down) - k):
    u, w = unit(down[i] - down[i - k]), unit(down[i + k] - down[i])
    ang[i] = math.degrees(math.acos(max(-1.0, min(1.0, float(u @ w)))))
ei = int(np.argmax(ang[: int(len(down) * 0.75)]))       # the elbow: where the axis bends most
elbow = Vector(down[ei])
Ps = hcut(0.81 * H, left)                                 # shoulder: ~8 cm in from the outside of the deltoid
outer = Ps[Ps[:, 0] > Ps[:, 0].max() - 0.05]
sh = Vector((float(Ps[:, 0].max()) - 0.04 * H, float(outer[:, 1].min() + outer[:, 1].max()) / 2, 0.81 * H))
fore = down[ei:]
cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(fore, axis=0), axis=1))])
wrist = Vector(fore[min(int(np.searchsorted(cum, 0.14 * H)), len(fore) - 1)])
tip = Vector(down[-1])
hand_tail = wrist.lerp(tip, 0.45)
clav = (Vector((0.02, sp[3].y - 0.07, neck_z - 0.045)), Vector((sh.x - 0.03, sh.y + 0.005, sh.z + 0.02)))
cf = float(hcut(0.74 * H, torso)[:, 1].min())
breast = (Vector((0.105, cf + 0.09, 0.74 * H)), Vector((0.105, cf - 0.02, 0.74 * H)))
pelvis = (sp[0].copy(), Vector((0.11, float(hcut(hip_z + 0.03 * H, torso)[:, 1].min()) + 0.04, hip_z + 0.07)))

# ---------------------------------------------------------------- write the edit bones
L = {"spine": (sp[0], sp[1]), "spine.001": (sp[1], sp[2]), "spine.002": (sp[2], sp[3]),
     "spine.003": (sp[3], sp[4]), "spine.004": (sp[4], neck_mid), "spine.005": (neck_mid, skull),
     "spine.006": (skull, top), "shoulder.L": clav, "upper_arm.L": (sh, elbow), "forearm.L": (elbow, wrist),
     "hand.L": (wrist, hand_tail), "breast.L": breast, "pelvis.L": pelvis, "thigh.L": (hip, knee),
     "shin.L": (knee, ankle), "foot.L": (ankle, ball), "toe.L": (ball, toe), "heel.02.L": heel}


def mirror(v):
    return Vector((-v.x, v.y, v.z))


for o in bpy.context.view_layer.objects:
    o.select_set(False)
bpy.context.view_layer.objects.active = meta
meta.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = meta.data.edit_bones
mw_inv = meta.matrix_world.inverted()
zaxis = {b.name: b.z_axis.copy() for b in eb}
order = sorted(eb, key=lambda b: len(b.parent_recursive))
done = []
for b in order:
    key = b.name
    src = L.get(key) or (L.get(key[:-2] + ".L") if key.endswith(".R") else None)
    if src is None:
        continue
    h, tl = src
    if key.endswith(".R"):
        h, tl = mirror(h), mirror(tl)
    b.head, b.tail = mw_inv @ h, mw_inv @ tl
    b.align_roll(zaxis[key])
    done.append(key)
for b in eb:                                              # connected children follow their parents' tails
    if b.use_connect and b.parent:
        b.head = b.parent.tail
bpy.ops.object.mode_set(mode="OBJECT")


def r(v):
    return [round(float(x), 3) for x in v]


print("@@JSON@@" + json.dumps({"ok": True, "metarig": meta.name, "bones_placed": len(done),
                               "height_m": round(float(H), 3), "crotch_m": round(crotch, 3),
                               "joints": {"hip": r(hip), "knee": r(knee), "ankle": r(ankle), "ball": r(ball),
                                          "shoulder": r(sh), "elbow": r(elbow), "wrist": r(wrist),
                                          "neck": r(sp[4]), "skull": r(skull)}}))
