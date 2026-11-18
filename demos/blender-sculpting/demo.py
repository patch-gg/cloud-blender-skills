"""blender-sculpting on Patch's cloud Blender: a stone head blocked out from primitives, then sculpt_ops.py's
headless passes in order (remesh to fuse, smooth, remesh finer + inflate, noise detail), keeping a copy after
each pass for the lineup.

Prompt it stands for: "Sculpt a weathered stone head from a primitive blockout, headless: fuse it, soften
the forms, then add eroded-stone detail, and show each pass."
Run: python demos/blender-sculpting/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

OPS = "blender-sculpting/scripts/sculpt_ops.py"
PASSES = [  # (label, ops) - each pass runs on the same object, in order
    ("remesh", ["remesh=0.02"]),                                   # fuse the 13 parts into one surface
    ("smooth", ["smooth=30", "apply"]),                            # primary forms, softened
    ("inflate", ["remesh=0.006", "inflate=0.02", "apply"]),       # density for detail, fuller forms
    ("detail", ["detail=0.018,0.11", "detail=0.005,0.025", "smooth=1", "apply"]),  # weathered stone
]

d = Demo(__file__)
d.run("scene.py")
d.look("base.jpg", "--angles", "4")
d.run("snap.py", "--name", "S0_base", "--slot", "0", "--of", len(PASSES) + 1)
stages = {"base": {"faces": None}}
for i, (label, ops) in enumerate(PASSES, start=1):
    r = d.skill(OPS, "--objects", "Moai", "--ops", *ops)["objects"]["Moai"]
    stages[label] = {"ops": ops, "faces": r["base_faces"], "tris": r["evaluated_tris"]}
    if i < len(PASSES):
        d.run("snap.py", "--name", f"S{i}_{label}", "--slot", i, "--of", len(PASSES) + 1)
    d.look(f"pass{i}_{label}.jpg", "--angles", "2")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Moai", "--profile", "render")
row = ["S0_base"] + [f"S{i}_{p[0]}" for i, p in enumerate(PASSES[:-1], start=1)] + ["Moai"]
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *row, "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "9")
d.run("present.py", "--labels", "base", *[p[0] for p in PASSES])
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=31)
media = d.media(r, crop="crop=280:280:977:165")    # the picker picture: the finished stone face
print(d.finish({"passes": [{"label": k, **v} for k, v in stages.items()],
                "final_tris": stages["detail"]["tris"],
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")},
                **media},
               prompt="Sculpt a weathered stone head from a primitive blockout, headless: fuse it, soften the "
                      "forms, then add eroded-stone detail, and show each pass."))
