"""A stylized head for the blender-facial-shapekeys demo, built in bpy + numpy (head-local metres; the
character faces -Y, its left is +X, up is +Z).

The Head mesh is what the skill's step 1 asks for: concentric loops around a real mouth opening (the lips roll
into a mouth bag), eyelids, brows, ears, teeth and a tongue as islands of the same mesh, the eyes as separate
objects, and everything exactly symmetric in X so --mirror can find each vertex's twin.
Face().positions(**controls) gives every Head vertex for an expression (jaw, smile_l, blink_r, ...), so one shape
key is one foreach_set; SHAPES maps ARKit / viseme key names to controls. Imported by scene.py and sculpt.py.
"""
import math

import numpy as np

A, B, C = 0.112, 0.106, 0.126           # skull semi-axes
BETA = math.radians(23.0)               # the mouth sits this far below the skull centre's horizon
M = np.array([0.0, -math.cos(BETA), -math.sin(BETA)])   # centre -> mouth
E1 = np.array([1.0, 0.0, 0.0])                          # mouth frame: across (character left)
E2 = np.array([0.0, -math.sin(BETA), math.cos(BETA)])   # mouth frame: up the face
NPHI = 80                                # loops around the mouth: even, so phi and pi - phi are twins
PHI = np.arange(NPHI) * (2 * math.pi / NPHI)
RE = 0.030                               # eyeball radius
HINGE = np.array([0.0, 0.004, -0.012])   # jaw pivot (x axis through here)
JAW_DEG = 17.0
SKIN, LIPS, MOUTH, TEETH, TONGUE, BROWS = range(6)   # material slots, in scene.py's order (M_Skin ... M_Brows)

# loops around the mouth, from the back of the mouth bag out across the face:
# half-width, upper / lower half-height, lip bulge, depth into the head (m)
MOUTH_RINGS = [
    (0.0100, 0.0050, 0.0065, 0.0, 0.025),
    (0.0160, 0.0085, 0.0100, 0.0, 0.018),
    (0.0210, 0.0075, 0.0085, 0.0, 0.009),
    (0.0258, 0.0014, 0.0014, 0.0006, 0.0030),
    (0.0270, 0.0007, 0.0007, 0.0010, 0.0),      # LIP_EDGE: the lips meet here
    (0.0282, 0.0028, 0.0031, 0.0020, 0.0),
    (0.0298, 0.0052, 0.0059, 0.0022, 0.0),
    (0.0318, 0.0072, 0.0082, 0.0011, 0.0),      # vermilion border
    (0.0345, 0.0100, 0.0112, 0.0003, 0.0),
    (0.0382, 0.0148, 0.0164, 0.0, 0.0),
    (0.0425, 0.0212, 0.0226, 0.0, 0.0),
    (0.0470, 0.0287, 0.0298, 0.0, 0.0),
    (0.0530, 0.0362, 0.0372, 0.0, 0.0),
    (0.0590, 0.0452, 0.0460, 0.0, 0.0),
    (0.0650, 0.0560, 0.0565, 0.0, 0.0),
]
LIP_EDGE = 4
LIP_FACES = range(3, 8)        # face strips between these loops and the next carry the lip colour
POLAR = [0.585, 0.645, 0.71, 0.78, 0.855, 0.935, 1.02, 1.11, 1.205, 1.305, 1.41, 1.52, 1.635, 1.755,
         1.88, 2.005, 2.13, 2.255, 2.38, 2.505, 2.625, 2.74, 2.85, 2.955, 3.05]


def _n(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _ss(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _azel(d):
    return np.arctan2(d[..., 0], -d[..., 1]), np.arcsin(np.clip(d[..., 2], -1, 1))


def _dir(az, el):
    az, el = np.asarray(az, float), np.asarray(el, float)
    return np.stack([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)], -1)


D_EYE = _n([0.40, -0.87, 0.10])
BUMPS = [  # centre direction, amplitude (m), sigma across / up (rad), on both sides
    (_n([0, -1, -0.10]), 0.016, 0.095, 0.075, False),      # nose
    (_n([0, -1, 0.02]), 0.004, 0.05, 0.16, False),         # nose bridge
    (_n([0.56, -0.74, -0.26]), 0.007, 0.28, 0.26, True),   # cheeks
    (_n([0, -0.72, -0.70]), 0.006, 0.17, 0.14, False),     # chin
    (D_EYE, -0.009, 0.19, 0.17, True),                     # eye sockets
    (_n([0.36, -0.86, 0.33]), 0.004, 0.22, 0.10, True),    # brow ridge
]


def shell(d):
    """Skin point along each direction d (..., 3) from the skull centre."""
    d = _n(d)
    r = 1.0 / np.sqrt((d[..., 0] / A) ** 2 + (d[..., 1] / B) ** 2 + (d[..., 2] / C) ** 2)
    az, el = _azel(d)
    for c, amp, sh, sv, both in BUMPS:
        caz, cel = _azel(c)
        for sx in ((1, -1) if both else (1,)):
            r = r + amp * np.exp(-0.5 * (((az - sx * caz) / sh) ** 2 + ((el - cel) / sv) ** 2))
    p = d * r[..., None]
    t = _ss(0.015, -0.10, p[..., 2])      # narrower jaw
    p[..., 0] *= 1 - 0.15 * t
    p[..., 1] *= 1 - 0.05 * t
    return p


RM = float(np.linalg.norm(shell(M)))


def mouth_dir(h, v):
    """Offsets (m) across / up the face at the mouth -> unit direction."""
    h, v = np.broadcast_arrays(np.asarray(h, float), np.asarray(v, float))
    return _n(M * RM + h[..., None] * E1 + v[..., None] * E2)


def _gauss(p, c, s):
    return np.exp(-np.sum((p - c) ** 2, axis=-1) / (2 * s * s))


def _rot_x(p, pivot, deg):
    """Rotate points about the x axis through pivot by per-point angles (deg)."""
    a = np.radians(deg)
    q = p - pivot
    y = q[:, 1] * np.cos(a) - q[:, 2] * np.sin(a)
    z = q[:, 1] * np.sin(a) + q[:, 2] * np.cos(a)
    return np.stack([q[:, 0], y, z], 1) + pivot


def _mirror(p):
    return p * np.array([-1.0, 1.0, 1.0])


BOXES = {  # UV atlas (u0, v0, u1, v1): no two islands share UV space
    "shell": (0.0, 0.0, 0.5, 1.0),
    "lid_up_l": (0.50, 0.0, 0.625, 0.25), "lid_lo_l": (0.625, 0.0, 0.75, 0.25),
    "lid_up_r": (0.75, 0.0, 0.875, 0.25), "lid_lo_r": (0.875, 0.0, 1.0, 0.25),
    "brow_l": (0.50, 0.26, 0.75, 0.36), "brow_r": (0.75, 0.26, 1.0, 0.36),
    "ear_l": (0.50, 0.37, 0.75, 0.52), "ear_r": (0.75, 0.37, 1.0, 0.52),
    "teeth_up": (0.50, 0.53, 0.75, 0.68), "teeth_lo": (0.75, 0.53, 1.0, 0.68),
    "tongue": (0.50, 0.69, 0.75, 0.84),
}


def _sphere_topo(nr, nk):
    """nr rings of nk verts plus two poles (index nr*nk before ring 0, nr*nk+1 after the last ring):
    quads and pole fans wound outward, with [0,1] UVs per corner (seams unwrapped)."""
    faces, uv = [], []
    V = lambda r: (r + 1) / (nr + 1)  # noqa: E731
    for r in range(nr - 1):
        for k in range(nk):
            k2 = (k + 1) % nk
            faces.append((r * nk + k, r * nk + k2, (r + 1) * nk + k2, (r + 1) * nk + k))
            uv.append(((k / nk, V(r)), ((k + 1) / nk, V(r)), ((k + 1) / nk, V(r + 1)), (k / nk, V(r + 1))))
    p0, p1 = nr * nk, nr * nk + 1
    for k in range(nk):
        k2 = (k + 1) % nk
        faces.append((p0, k2, k))
        uv.append((((k + 0.5) / nk, 0.0), ((k + 1) / nk, V(0)), (k / nk, V(0))))
        faces.append((p1, (nr - 1) * nk + k, (nr - 1) * nk + k2))
        uv.append((((k + 0.5) / nk, 1.0), (k / nk, V(nr - 1)), ((k + 1) / nk, V(nr - 1))))
    return faces, uv


def _flip(faces, uvs):
    """Mirrored islands: reverse each face (and its UV corners) so normals stay outward."""
    return [f[::-1] for f in faces], [u[::-1] for u in uvs]


class Face:
    """Topology once; positions(**controls) for any expression."""

    def __init__(self):
        self.blocks, self.faces, self.mat, self.uvs = {}, [], [], []
        self.n = 0
        self._shell()
        self._eye_frames()
        for side in ("l", "r"):
            self._lid(side, upper=True)
            self._lid(side, upper=False)
            self._brow(side)
            self._ear(side)
        self._teeth()
        self._tongue()
        self.rest = self.positions()
        p = self.rest
        s = self.blocks["shell"]
        ring = lambda j, i: s.start + j * NPHI + i  # noqa: E731
        self.corner = {"l": p[ring(LIP_EDGE, 0)], "r": p[ring(LIP_EDGE, NPHI // 2)]}
        self.mouth_c = (p[ring(LIP_EDGE, NPHI // 4)] + p[ring(LIP_EDGE, 3 * NPHI // 4)]) / 2
        self.upper_lip = {"l": p[ring(LIP_EDGE + 2, 9)], "r": p[ring(LIP_EDGE + 2, NPHI // 2 - 9)]}
        self.lower_lip = {"l": p[ring(LIP_EDGE + 2, NPHI - 9)], "r": p[ring(LIP_EDGE + 2, NPHI // 2 + 9)]}
        self.chin = shell(_n([0, -0.75, -0.66]))
        self.cheek = {}
        self.cheek_hi = {}
        self.cheek_puff = {}
        self.nose_side = {}
        for k, sx in (("l", 1), ("r", -1)):
            self.cheek[k] = shell(_n([0.50 * sx, -0.80, -0.22]))
            self.cheek_hi[k] = shell(_n([0.46 * sx, -0.84, -0.05]))
            self.cheek_puff[k] = shell(_n([0.52 * sx, -0.78, -0.38]))
            self.nose_side[k] = shell(_n([0.11 * sx, -1, -0.13]))
        self.normal0 = _n(self.rest)        # outward from the skull centre: good enough for small pushes

    # ------------------------------------------------------------ topology

    def _add(self, name, n, faces, mats, uvs):
        """Register an island: faces local to it, per-corner UVs in [0,1] (placed in its BOXES slot)."""
        self.blocks[name] = range(self.n, self.n + n)
        u0, v0, u1, v1 = BOXES[name]
        for f, m, uv in zip(faces, mats, uvs):
            self.faces.append(tuple(self.n + i for i in f))
            self.mat.append(m)
            self.uvs.append(tuple((u0 + (u1 - u0) * a, v0 + (v1 - v0) * b) for a, b in uv))
        self.n += n

    def _shell(self):
        nr = len(MOUTH_RINGS) + len(POLAR)
        faces, mats, uvs = [], [], []
        cap, pole = nr * NPHI, nr * NPHI + 1
        V = lambda j: (j + 0.5) / (nr + 1)  # noqa: E731
        for j in range(nr - 1):
            for i in range(NPHI):
                i2 = (i + 1) % NPHI
                faces.append((j * NPHI + i, (j + 1) * NPHI + i, (j + 1) * NPHI + i2, j * NPHI + i2))
                mats.append(MOUTH if j < 3 else LIPS if j in LIP_FACES else SKIN)
                u0, u1 = i / NPHI, (i + 1) / NPHI
                uvs.append(((u0, V(j)), (u0, V(j + 1)), (u1, V(j + 1)), (u1, V(j))))
        for i in range(NPHI):
            i2 = (i + 1) % NPHI
            u0, u1 = i / NPHI, (i + 1) / NPHI
            faces.append((cap, i, i2))
            mats.append(MOUTH)
            uvs.append((((i + 0.5) / NPHI, 0.0), (u0, V(0)), (u1, V(0))))
            last = (nr - 1) * NPHI
            faces.append((last + i, pole, last + i2))
            mats.append(SKIN)
            uvs.append(((u0, V(nr - 1)), ((i + 0.5) / NPHI, 1.0), (u1, V(nr - 1))))
        self._add("shell", nr * NPHI + 2, faces, mats, uvs)
        # per-vertex data for the deformers
        sinp = np.tile(np.sin(PHI), nr)
        j = np.repeat(np.arange(nr), NPHI)
        self.s_ring = np.concatenate([j, [-1, -2]])
        self.s_sin = np.concatenate([sinp, [0.0, 0.0]])

    def _shell_pos(self):
        out = []
        for W, Hu, Hl, bulge, depth in MOUTH_RINGS:
            s = np.sin(PHI)
            h = W * np.cos(PHI)
            v = np.where(s >= 0, Hu, Hl) * s
            d = mouth_dir(h, v)
            out.append(shell(d) + d * (bulge - depth))
        for psi in POLAR:
            d = np.cos(psi) * M + np.sin(psi) * (np.cos(PHI)[:, None] * E1 + np.sin(PHI)[:, None] * E2)
            out.append(shell(d))
        d0 = mouth_dir(0.0, -0.001)
        out.append((shell(d0) - d0 * 0.027)[None])
        out.append(shell(-M)[None])
        return np.concatenate(out)

    def _eye_frames(self):
        self.eye = {}
        for k, sx in (("l", 1), ("r", -1)):
            d = D_EYE * np.array([sx, 1, 1])
            ctr = shell(d) - d * (0.5 * RE)
            f = _n([0.085 * sx, -1.0, 0.0])
            u = np.array([0.0, 0.0, 1.0])
            s = np.cross(u, f)          # left eye: towards +X (out), right eye: towards +X (in)
            self.eye[k] = (ctr, f, s * sx, u)   # s now points outward on both sides

    LID = {  # radius rows (outer..rim..inner) as (elevation offset from the edge in deg, radius / RE)
        True: [(60, 1.16), (45, 1.16), (32, 1.16), (21, 1.16), (13, 1.16), (8, 1.16), (4.5, 1.158),
               (1.4, 1.152), (0.0, 1.132), (1.4, 1.102), (5.0, 1.078), (12, 1.068), (23, 1.068), (35, 1.068),
               (47, 1.068), (60, 1.068)],
        False: [(46, 1.105), (32, 1.105), (21, 1.105), (13, 1.105), (7.5, 1.105), (4.5, 1.103), (1.4, 1.097),
                (0.0, 1.086), (1.4, 1.075), (5.0, 1.067), (12, 1.062), (22, 1.062), (34, 1.062), (46, 1.062)],
    }
    LID_AZ = np.radians(np.linspace(-96, 96, 29))

    def _lid(self, side, upper):
        rows = self.LID[upper]
        na, nrw = len(self.LID_AZ), len(rows)
        faces, uvs, mats = [], [], []
        for r in range(nrw - 1):
            for a in range(na - 1):
                q = (r * na + a, r * na + a + 1, (r + 1) * na + a + 1, (r + 1) * na + a)
                q = q[::-1] if upper else q          # outer surface faces away from the eye
                faces.append(q)
                mats.append(BROWS if upper and 6 <= r <= 8 else SKIN)   # a lash line along the upper margin
                uvs.append(tuple(((x % na) / (na - 1), (x // na) / (nrw - 1)) for x in q))
        if side == "r":
            faces, uvs = _flip(faces, uvs)
        self._add(f"lid_{'up' if upper else 'lo'}_{side}", na * nrw, faces, mats, uvs)

    def _lid_pos(self, side, upper, d_el=0.0, d_az=0.0, d_arch=0.0):
        """Lid vertices for the left eye frame (mirrored for the right): rotations as elevation/azimuth offsets."""
        ctr, f, s, u = self.eye["l"]
        rows = self.LID[upper]
        az = self.LID_AZ + math.radians(d_az)
        if upper:
            edge = np.radians(22.0 + 6.0 * np.cos(self.LID_AZ * 0.95))
        else:
            edge = np.radians(-36.0 - 5.0 * np.cos(self.LID_AZ * 0.95))
        pts = []
        top = rows[0][0]
        for off, rad in rows:      # the margin turns the full angle, the buried top less: the lid stretches
            w = 1.0 - (0.7 if upper else 0.6) * min(1.0, max(0.0, off - 8.0) / (top - 8.0))
            el = edge + math.radians(off) * (1 if upper else -1) + np.radians((d_el + d_arch * (1 - np.cos(az))) * w)
            dirs = (np.cos(el)[:, None] * (np.cos(az)[:, None] * f + np.sin(az)[:, None] * s)
                    + np.sin(el)[:, None] * u)
            pts.append(ctr + dirs * (rad * RE))
        p = np.concatenate(pts)
        return _mirror(p) if side == "r" else p

    BROW_T = np.linspace(0, 1, 18)
    BROW_RING = 10

    def _brow(self, side):
        nt, nr = len(self.BROW_T), self.BROW_RING
        faces, uvs = _sphere_topo(nt, nr)
        uvs = [tuple((b, a) for a, b in u) for u in uvs]      # along the brow = u
        if side == "r":
            faces, uvs = _flip(faces, uvs)
        self._add(f"brow_{side}", nt * nr + 2, faces, [BROWS] * len(faces), uvs)

    def _brow_pos(self, side, down=0.0, inner_up=0.0, outer_up=0.0):
        t = self.BROW_T
        az = 0.14 + (0.66 - 0.14) * t - 0.06 * down * (1 - t)
        el = (0.43 + 0.055 * np.sin(np.pi * t ** 0.85) - 0.07 * t
              - 0.11 * down * (0.5 + 0.5 * (1 - t))
              + 0.12 * inner_up * (1 - t) ** 1.4 - 0.02 * inner_up * t
              + 0.10 * outer_up * t ** 1.3)
        d = _dir(az, el)
        base = shell(d)
        nrm = _n(base)
        tang = _n(np.gradient(base, axis=0))
        bin_ = _n(np.cross(nrm, tang))
        prof = (0.5 + 0.5 * (1 - t)) * np.sqrt(np.clip(np.minimum((t + 0.03) / 0.16, (1.03 - t) / 0.2), 0, 1))
        w, hgt = 0.0062 * prof, 0.0030 * prof
        ctr = base + nrm * (0.35 * hgt)[:, None]
        th = np.arange(self.BROW_RING) * 2 * np.pi / self.BROW_RING
        ring = (ctr[:, None, :] + np.cos(th)[None, :, None] * (w[:, None, None] * bin_[:, None, :])
                + np.sin(th)[None, :, None] * (hgt[:, None, None] * nrm[:, None, :]))
        p = np.concatenate([ring.reshape(-1, 3), (ctr[0] - tang[0] * 0.002)[None],
                            (ctr[-1] + tang[-1] * 0.002)[None]])
        return _mirror(p) if side == "r" else p

    EAR = (14, 10)

    def _ear(self, side):
        nu, nv = self.EAR
        faces, uvs = _sphere_topo(nv, nu)
        if side == "r":
            faces, uvs = _flip(faces, uvs)
        self._add(f"ear_{side}", nu * nv + 2, faces, [SKIN] * len(faces), uvs)

    def _ear_pos(self, side):
        nu, nv = self.EAR
        ctr = shell(_dir(math.radians(98), -0.07))
        ctr = ctr + np.array([0.004, 0.0, 0.0])
        a = np.arange(nu) * 2 * np.pi / nu
        b = np.linspace(-0.5 * np.pi + np.pi / (nv + 1), 0.5 * np.pi - np.pi / (nv + 1), nv)
        u_, v_ = np.meshgrid(a, b)
        x = 0.0125 * np.cos(v_) * np.cos(u_)
        y = 0.025 * np.cos(v_) * np.sin(u_)
        z = 0.038 * np.sin(v_)
        cup = np.where(x > 0, 0.0085 * (1 - (y / 0.025) ** 2 - (z / 0.038) ** 2).clip(0, 1), 0.0)
        x = x - cup
        p = np.stack([x.ravel(), y.ravel(), z.ravel()], 1)
        p = np.concatenate([p, [[0, 0, -0.038], [0, 0, 0.038]]])
        flare, tilt = math.radians(14), math.radians(-10)
        rz = np.array([[math.cos(flare), -math.sin(flare), 0], [math.sin(flare), math.cos(flare), 0], [0, 0, 1]])
        rx = np.array([[1, 0, 0], [0, math.cos(tilt), -math.sin(tilt)], [0, math.sin(tilt), math.cos(tilt)]])
        p = p @ (rz @ rx).T + ctr
        return _mirror(p) if side == "r" else p

    TEETH_H = 17

    def _slab(self, nh):
        """Closed slab: a front grid (3 rows of nh) then a back grid. Faces + UVs unfolded front, top, back,
        bottom down the box, the two end caps in a strip on the right."""
        f, uv = [], []
        cu = lambda i: 0.9 * i / (nh - 1)  # noqa: E731
        for r in range(2):
            for i in range(nh - 1):
                a = r * nh + i
                f.append((a, a + 1, a + nh + 1, a + nh))                                   # front
                uv.append(((cu(i), 0.2 * r), (cu(i + 1), 0.2 * r), (cu(i + 1), 0.2 * r + 0.2), (cu(i), 0.2 * r + 0.2)))
                b = 3 * nh + r * nh + i
                f.append((b, b + nh, b + nh + 1, b + 1))                                   # back
                vb = lambda rr: 0.5 + 0.2 * (2 - rr)  # noqa: E731
                uv.append(((cu(i), vb(r)), (cu(i), vb(r + 1)), (cu(i + 1), vb(r + 1)), (cu(i + 1), vb(r))))
        for i in range(nh - 1):
            f.append((2 * nh + i, 2 * nh + i + 1, 5 * nh + i + 1, 5 * nh + i))              # top
            uv.append(((cu(i), 0.4), (cu(i + 1), 0.4), (cu(i + 1), 0.5), (cu(i), 0.5)))
            f.append((i, 3 * nh + i, 3 * nh + i + 1, i + 1))                               # bottom
            uv.append(((cu(i), 1.0), (cu(i), 0.9), (cu(i + 1), 0.9), (cu(i + 1), 1.0)))
        for e, u0 in ((0, 0.92), (nh - 1, 0.96)):
            col = [r * nh + e for r in range(3)] + [3 * nh + r * nh + e for r in range(3)]
            for q, rr in (((col[0], col[1], col[4], col[3]), 0), ((col[1], col[2], col[5], col[4]), 1)):
                c = ((u0, 0.2 * rr), (u0, 0.2 * rr + 0.2), (u0 + 0.04, 0.2 * rr + 0.2), (u0 + 0.04, 0.2 * rr))
                if e:
                    q, c = q[::-1], c[::-1]
                f.append(q)
                uv.append(c)
        return f, uv

    def _teeth(self):
        nh = self.TEETH_H
        for name in ("teeth_up", "teeth_lo"):
            faces, uvs = self._slab(nh)
            self._add(name, 6 * nh, faces, [TEETH] * len(faces), uvs)

    def _teeth_pos(self, upper):
        nh = self.TEETH_H
        half = 0.0190 if upper else 0.0160
        h = half * np.sin(np.linspace(-np.pi / 2, np.pi / 2, nh))
        rows = (-0.0018, 0.0030, 0.0078) if upper else (-0.0090, -0.0060, -0.0031)
        front = (0.0062 if upper else 0.0072) + 0.0065 * (h / half) ** 2
        pts = []
        for back in (0.0, 0.0034):
            for v in rows:
                d = mouth_dir(h, np.full(nh, v))
                pts.append(shell(d) - d * (front + back)[:, None])
        return np.concatenate(pts)

    TONGUE = (16, 9)

    def _tongue(self):
        nu, nv = self.TONGUE
        faces, uvs = _sphere_topo(nv, nu)
        self._add("tongue", nu * nv + 2, faces, [TONGUE] * len(faces), uvs)

    def _tongue_pos(self, out=0.0):
        nu, nv = self.TONGUE
        d0 = mouth_dir(0.0, -0.0038)
        ctr = shell(d0) - d0 * (0.0135 - 0.030 * out)
        ctr = ctr - E2 * 0.004 * out
        ax_w, ax_l, ax_h = E1, -M, E2
        a = np.arange(nu) * 2 * np.pi / nu
        b = np.linspace(-0.5 * np.pi + np.pi / (nv + 1), 0.5 * np.pi - np.pi / (nv + 1), nv)
        u_, v_ = np.meshgrid(a, b)
        x = 0.0145 * np.cos(v_) * np.cos(u_)
        y = (0.0110 + 0.004 * out) * np.cos(v_) * np.sin(u_)
        z = 0.0036 * np.sin(v_)
        p = np.stack([x.ravel(), y.ravel(), z.ravel()], 1)
        p = np.concatenate([p, [[0, 0, -0.0036], [0, 0, 0.0036]]])
        return ctr + p[:, :1] * ax_w + p[:, 1:2] * ax_l + p[:, 2:] * ax_h

    # ------------------------------------------------------------ deformation

    def positions(self, **k):
        g = lambda name: float(k.get(name, 0.0))  # noqa: E731
        P = np.zeros((self.n, 3))
        sh = self.blocks["shell"]
        P[sh.start:sh.stop] = self._shell_pos()
        for side in ("l", "r"):
            blink, wide, squint = g(f"blink_{side}"), g(f"wide_{side}"), g(f"squint_{side}")
            lu, ld, li, lo = (g(f"look_{x}_{side}") for x in ("up", "down", "in", "out"))
            smile, csq = g(f"smile_{side}"), g(f"cheek_squint_{side}")
            up = -52 * blink + 12 * wide - 6 * squint + 10 * lu - 15 * ld - 3 * smile
            low = 23 * blink - 4 * wide + 12 * squint + 6 * lu - 6 * ld + 7 * smile + 8 * csq
            yaw = 7 * (lo - li)
            for upper, d_el in ((True, up), (False, low)):
                b = self.blocks[f"lid_{'up' if upper else 'lo'}_{side}"]
                arch = 12 * blink if upper else 0.0     # the closed lid line curves down in the middle
                P[b.start:b.stop] = self._lid_pos(side, upper, d_el, yaw, arch)
            b = self.blocks[f"brow_{side}"]
            P[b.start:b.stop] = self._brow_pos(side, g(f"brow_down_{side}"), g("brow_inner_up"),
                                               g(f"brow_outer_up_{side}"))
            b = self.blocks[f"ear_{side}"]
            P[b.start:b.stop] = self._ear_pos(side)
        for upper in (True, False):
            b = self.blocks["teeth_up" if upper else "teeth_lo"]
            P[b.start:b.stop] = self._teeth_pos(upper)
        b = self.blocks["tongue"]
        P[b.start:b.stop] = self._tongue_pos(g("tongue"))
        if not hasattr(self, "rest"):
            return P
        return self._deform(P, g)

    def _masks(self):
        if hasattr(self, "_m"):
            return self._m
        n = self.n
        sh = self.blocks["shell"]
        ring = np.full(n, -9)
        sinp = np.zeros(n)
        ring[sh.start:sh.stop] = self.s_ring
        sinp[sh.start:sh.stop] = self.s_sin
        p = self.rest
        lower_phi = _ss(0.22, -0.22, sinp)
        v_rel = (p - self.mouth_c) @ E2
        tau = 0.006 + 0.4 * np.clip(np.abs(p[:, 0]) - 0.024, 0, None)
        lower_pos = _ss(tau, -tau, v_rel)
        kk = np.interp(ring, [7, 8, 9, 10, 11], [0.0, 0.25, 0.5, 0.75, 1.0])
        kk = np.where(ring < 0, 1.0, kk)
        front = _ss(0.034, -0.036, p[:, 1] - HINGE[1])
        jaw = np.where(ring >= 0, (lower_phi * (1 - kk) + lower_pos * kk) * front, 0.0)
        jaw[ring == -1] = 0.5                                     # back of the mouth bag
        for name in ("teeth_lo", "tongue"):
            b = self.blocks[name]
            jaw[b.start:b.stop] = 1.0
        lips = (ring >= 3) & (ring <= 8)
        mouth = (ring >= 0) & (ring <= 9)
        self._m = {
            "jaw": jaw,
            "lip_up": np.where(lips, 1 - lower_phi, 0.0), "lip_lo": np.where(lips, lower_phi, 0.0),
            "mouth_up": np.where(mouth, 1 - lower_phi, 0.0), "mouth_lo": np.where(mouth, lower_phi, 0.0),
            "skin": (ring >= 0).astype(float),
            "bulge": np.array([MOUTH_RINGS[j][3] if 0 <= j < len(MOUTH_RINGS) else 0.0 for j in ring]),
        }
        return self._m

    def _deform(self, P, g):
        m = self._masks()
        sk = m["skin"][:, None]          # mouth/face fields move the skin shell only
        nrm = self.normal0
        R = self.rest
        dP = np.zeros_like(P)
        for side, sx in (("l", 1.0), ("r", -1.0)):
            c = self.corner[side]
            G1 = _gauss(R, c, 0.014)[:, None]
            dP += g(f"smile_{side}") * (G1 * np.array([0.0045 * sx, 0.0030, 0.0100])
                                        + _gauss(R, self.cheek[side], 0.020)[:, None]
                                        * np.array([0.0012 * sx, -0.0025, 0.0040]))
            dP += g(f"frown_{side}") * G1 * np.array([0.0006 * sx, 0.0006, -0.0070])
            dP += g(f"stretch_{side}") * _gauss(R, c, 0.017)[:, None] * np.array([0.0065 * sx, 0.0015, -0.0028])
            dP += g(f"dimple_{side}") * _gauss(R, c, 0.010)[:, None] * np.array([0.0010 * sx, 0.0042, 0.0005])
            side_w = _ss(-0.008, 0.008, sx * R[:, 0])[:, None]
            dP -= g(f"press_{side}") * side_w * nrm * (m["bulge"] * 0.75)[:, None]
            dP += g(f"press_{side}") * _gauss(R, c, 0.010)[:, None] * np.array([0.0015 * sx, 0.0, 0.0])
            dP += g(f"upper_up_{side}") * (m["lip_up"] * _gauss(R, self.upper_lip[side], 0.015))[:, None] \
                * (E2 * 0.0042)
            dP += g(f"upper_up_{side}") * _gauss(R, self.nose_side[side], 0.010)[:, None] * (E2 * 0.0012)
            dP += g(f"lower_down_{side}") * (m["lip_lo"] * _gauss(R, self.lower_lip[side], 0.015))[:, None] \
                * (E2 * -0.0048)
            dP += g(f"cheek_squint_{side}") * _gauss(R, self.cheek_hi[side], 0.018)[:, None] \
                * np.array([0.0, -0.0012, 0.0042])
            dP += g(f"sneer_{side}") * (_gauss(R, self.nose_side[side], 0.010)[:, None]
                                        * np.array([0.0006 * sx, -0.0010, 0.0036])
                                        + (m["lip_up"] * _gauss(R, self.upper_lip[side], 0.012))[:, None]
                                        * (E2 * 0.0016))
            dP += g("cheek_puff") * _gauss(R, self.cheek_puff[side], 0.028)[:, None] * nrm * 0.016
        x_rel = (R - self.mouth_c)[:, 0:1] * E1
        Gp = _gauss(R, self.mouth_c, 0.022)[:, None]
        dP += g("pucker") * Gp * (-0.38 * x_rel + M * 0.010)
        dP += g("funnel") * (Gp * (-0.26 * x_rel + M * 0.007)
                             + _gauss(R, self.mouth_c, 0.018)[:, None]
                             * (m["mouth_up"][:, None] * E2 * 0.0036 - m["mouth_lo"][:, None] * E2 * 0.0048))
        dP += g("cheek_puff") * Gp * M * 0.002
        dP += g("roll_upper") * m["lip_up"][:, None] * (-nrm * 0.0035 - E2 * 0.0014)
        dP += g("roll_lower") * m["lip_lo"][:, None] * (-nrm * 0.0035 + E2 * 0.0014)
        dP += g("shrug_upper") * (m["lip_up"] * _gauss(R, self.mouth_c, 0.02))[:, None] * (E2 * 0.003)
        dP += g("shrug_lower") * ((m["lip_lo"] * _gauss(R, self.mouth_c, 0.02))[:, None] * (E2 * 0.0035)
                                  + _gauss(R, self.chin, 0.02)[:, None] * (E2 * 0.003))
        dP += g("mouth_side") * _gauss(R, self.mouth_c, 0.024)[:, None] * np.array([0.0072, 0.0015, 0.0])
        P = P + dP * sk
        # the jaw: per-vertex rotation about the hinge, then slides
        jaw = m["jaw"]
        P = P + jaw[:, None] * (g("jaw_fwd") * np.array([0.0, -0.0065, 0.0])
                                + g("jaw_side") * np.array([0.0075, 0.0, 0.0]))
        ang = JAW_DEG * (g("jaw") * jaw - g("close") * m["lip_lo"])
        if np.any(ang):
            P = _rot_x(P, HINGE, ang)
        return P


def _lr(prefix, ctrl):
    return {f"{prefix}Left": {f"{ctrl}_l": 1.0}, f"{prefix}Right": {f"{ctrl}_r": 1.0}}


SHAPES = {
    **_lr("browDown", "brow_down"), "browInnerUp": {"brow_inner_up": 1.0}, **_lr("browOuterUp", "brow_outer_up"),
    "cheekPuff": {"cheek_puff": 1.0}, **_lr("cheekSquint", "cheek_squint"),
    **_lr("eyeBlink", "blink"), **_lr("eyeLookDown", "look_down"), **_lr("eyeLookIn", "look_in"),
    **_lr("eyeLookOut", "look_out"), **_lr("eyeLookUp", "look_up"), **_lr("eyeSquint", "squint"),
    **_lr("eyeWide", "wide"),
    "jawForward": {"jaw_fwd": 1.0}, "jawLeft": {"jaw_side": 1.0}, "jawOpen": {"jaw": 1.0}, "jawRight": {"jaw_side": -1.0},
    "mouthClose": {"close": 1.0}, **_lr("mouthDimple", "dimple"), **_lr("mouthFrown", "frown"),
    "mouthFunnel": {"funnel": 1.0}, "mouthLeft": {"mouth_side": 1.0}, **_lr("mouthLowerDown", "lower_down"),
    **_lr("mouthPress", "press"), "mouthPucker": {"pucker": 1.0}, "mouthRight": {"mouth_side": -1.0},
    "mouthRollLower": {"roll_lower": 1.0}, "mouthRollUpper": {"roll_upper": 1.0},
    "mouthShrugLower": {"shrug_lower": 1.0}, "mouthShrugUpper": {"shrug_upper": 1.0},
    **_lr("mouthSmile", "smile"), **_lr("mouthStretch", "stretch"), **_lr("mouthUpperUp", "upper_up"),
    **_lr("noseSneer", "sneer"), "tongueOut": {"tongue": 1.0},
    # Oculus visemes, as mixes of the same controls ("sil" is the rest pose)
    "viseme_PP": {"press_l": 1.0, "press_r": 1.0, "roll_upper": 0.3, "roll_lower": 0.3},
    "viseme_FF": {"jaw": 0.08, "roll_lower": 0.9, "upper_up_l": 0.35, "upper_up_r": 0.35},
    "viseme_TH": {"jaw": 0.22, "tongue": 0.38},
    "viseme_DD": {"jaw": 0.26, "stretch_l": 0.2, "stretch_r": 0.2},
    "viseme_kk": {"jaw": 0.32, "stretch_l": 0.12, "stretch_r": 0.12, "upper_up_l": 0.15, "upper_up_r": 0.15},
    "viseme_CH": {"jaw": 0.18, "funnel": 0.5, "upper_up_l": 0.3, "upper_up_r": 0.3},
    "viseme_SS": {"jaw": 0.08, "stretch_l": 0.5, "stretch_r": 0.5, "upper_up_l": 0.35, "upper_up_r": 0.35,
                  "lower_down_l": 0.35, "lower_down_r": 0.35},
    "viseme_nn": {"jaw": 0.18, "stretch_l": 0.15, "stretch_r": 0.15},
    "viseme_RR": {"jaw": 0.2, "funnel": 0.35, "pucker": 0.2},
    "viseme_aa": {"jaw": 0.78, "stretch_l": 0.1, "stretch_r": 0.1},
    "viseme_E": {"jaw": 0.32, "stretch_l": 0.55, "stretch_r": 0.55, "upper_up_l": 0.3, "upper_up_r": 0.3},
    "viseme_I": {"jaw": 0.2, "stretch_l": 0.45, "stretch_r": 0.45, "smile_l": 0.2, "smile_r": 0.2},
    "viseme_O": {"jaw": 0.42, "funnel": 0.9},
    "viseme_U": {"jaw": 0.12, "pucker": 1.0},
}
# sculpted once and symmetric, then split by the skill (--split), or one side then mirrored (--mirror)
SYMMETRIC = {"eyeBlink": {"blink_l": 1.0, "blink_r": 1.0}, "mouthSmile": {"smile_l": 1.0, "smile_r": 1.0}}
MIRRORED = ["browDownLeft"]
