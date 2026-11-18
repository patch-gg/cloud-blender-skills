"""Give the keys their shapes: the part of SKILL.md step 3 a person does in sculpt mode, done here in bpy from
face.py so every key moves. The keys the skill builds itself stay empty: eyeBlink and mouthSmile are sculpted
once, symmetric, for --split; browDownLeft is sculpted for --mirror to make browDownRight; viseme_sil is the rest
pose. Run in the session after shapekeys.py --create: cloud.py run sculpt.py -- face.py"""
import importlib.util
import json
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
spec = importlib.util.spec_from_file_location("face", args[0] if args else "face.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

ob = bpy.data.objects["Head"]
kbs = ob.data.shape_keys.key_blocks
face = F.Face()
if len(ob.data.vertices) != face.n:
    raise SystemExit(f"Head has {len(ob.data.vertices)} verts, face.py builds {face.n}: rebuild with scene.py")
by_skill = {f"{n}{s}" for n in F.SYMMETRIC for s in ("Left", "Right")} | {
    m.replace("Left", "Right") for m in F.MIRRORED}
done = []
for name, ctrl in F.SHAPES.items():
    if name in kbs and name not in by_skill:
        kbs[name].data.foreach_set("co", face.positions(**ctrl).astype(np.float32).ravel())
        done.append(name)
for name, ctrl in F.SYMMETRIC.items():          # sculpted once on both sides; --split makes Left/Right
    kb = kbs.get(name) or ob.shape_key_add(name=name, from_mix=False)
    kb.data.foreach_set("co", face.positions(**ctrl).astype(np.float32).ravel())
ob.data.update()
print("@@JSON@@" + json.dumps({"ok": True, "sculpted": len(done), "symmetric_sources": list(F.SYMMETRIC),
                               "left_for_the_skill": sorted(by_skill)}))
