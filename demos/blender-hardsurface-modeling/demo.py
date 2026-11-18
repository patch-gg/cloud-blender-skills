"""blender-hardsurface-modeling on Patch's cloud Blender: a power cell blocked out from primitives, then the
skill's production stack (booleans, bevel, weighted normals) part by part, shown as a before/after wipe.

Prompt it stands for: "Block out a sci-fi power cell, then finish it as a game-ready mid-poly prop:
boolean cut-outs, bevels and weighted normals."
Run: python demos/blender-hardsurface-modeling/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

STACK = "blender-hardsurface-modeling/scripts/apply_stack.py"
BEVEL = "0.008"                       # one bevel width for the whole prop (the SKILL: keep it consistent)
CUTS = {                              # part -> its boolean cutters (scene.py builds both)
    "Shell": ["Cut_Windows"],
    "Caps": ["Cut_CapRecess", "Cut_CapGrooves"],
    "Cradle": ["Cut_Saddle", "Cut_CradleHoles"],
    "Skid": ["Cut_SkidSlots"],
}
HDRI = "/opt/blender/5.2/datafiles/studiolights/world/studio.exr"  # ships with Blender

d = Demo(__file__)
s = d.run("scene.py")
parts = s["parts"]
d.look("blockout.jpg", "--angles", "4")
d.skill("blender-retopology-uv/scripts/uv_pack.py", "--objects", *parts, "--method", "smart")  # UV the base now
stack = {}
for part, cutters in CUTS.items():
    r = d.skill(STACK, "--objects", part, "--preset", "midpoly", "--width", BEVEL, "--cutters", *cutters)
    stack.update(r["objects"])
rest = [p for p in parts if p not in CUTS]
stack.update(d.skill(STACK, "--objects", *rest, "--preset", "midpoly", "--width", BEVEL)["objects"])
d.look("after.jpg", "--angles", "4")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", *parts, "--profile", "game")
tris_base = sum(v["tris_base"] for v in stack.values())
tris_final = sum(v["tris_final"] for v in stack.values())
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *parts, "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.6", "--backdrop", "--frames", "120", "--lens", "50", "--elevation", "14")
d.run("present.py", "--blockout-tris", tris_base, "--final-tris", tris_final)
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--samples", "64", "--res", "1280", "720",
             "--percent", "100", frames="1-120", poster=61)
media = d.media(r, crop="crop=400:400:200:90")     # the picker picture: the finished cap and a window
print(d.finish({"parts": len(parts), "cutters": sum(len(c) for c in CUTS.values()), "bevel_m": float(BEVEL),
                "tris_blockout": tris_base, "tris_final": tris_final,
                "stack": {k: v["stack"] for k, v in stack.items()},
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")},
                **media},
               prompt="Block out a sci-fi power cell, then finish it as a game-ready mid-poly prop: boolean "
                      "cut-outs, bevels and weighted normals."))
