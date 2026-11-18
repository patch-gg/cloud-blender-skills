"""blender-asset-qa on Patch's cloud Blender: a CC0 wine barrel from Patch's asset library, broken on purpose
(z-fighting, a floating part, flipped normals, an empty material slot), qa_check.py and review_shots.py on
it, the fix SKILL.md's table gives for each finding, and the clean pass.

Prompt it stands for: "QA this barrel before it ships: find what's broken, fix it, and show me it passes."
Run: python demos/blender-asset-qa/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo, DemoError  # noqa: E402

QA = "blender-asset-qa/scripts/qa_check.py"
SHOTS = "blender-asset-qa/scripts/review_shots.py"

d = Demo(__file__)
(glb,) = d.asset("polyhaven:wine_barrel_01")
asset = d.run("scene.py", glb)["objects"]                       # the barrel, broken four ways
d.look("broken.jpg")
qa1 = d.skill(QA, "--objects", *asset, "--profile", "game")
d.skill(SHOTS, "--objects", *asset, "--mode", "random", "--out", "//review_broken.png")

# each finding -> the fix from SKILL.md's table
caught, fix, gone = [], [], []
for z in qa1.get("zfighting", []):                               # a hidden duplicate: delete it
    dup = next((n for n in z["where"].split("<->") if re.search(r"\.\d{3}$", n)), None)
    if dup and dup not in gone:     # other pairs can come from flipped faces: re-run QA after the fixes
        caught.append("zfighting")
        fix += ["--delete", dup]
        gone.append(dup)
for f in qa1.get("floating", []):                                # move it to make contact
    caught.append("floating")
    fix += ["--snap", f["object"], *[str(c) for c in f["center"]]]
inside = [n for n, m in qa1["objects"].items() if m.get("inside_out_islands")]
if inside:                                                       # recalc normals outside
    caught.append("flipped")
    fix += ["--recalc", *inside]
empty = [e.split(":")[0] for e in qa1["errors"] if "empty/missing material slot" in e]
if empty:                                                        # assign the material
    caught.append("empty_slot")
    fix += ["--fill-slots", *empty]
if not caught:
    raise DemoError(f"qa_check caught nothing: {qa1}")

d.run("snapshot.py")                                             # keep the broken state for the clip
fixed = d.run("fix.py", *fix)
parts = [n for n in asset if n not in gone]
qa2 = d.skill(QA, "--objects", *parts, "--profile", "game")     # re-run until it passes
if not qa2.get("pass"):
    raise DemoError(f"still failing after the fixes: {qa2.get('errors')}")
d.skill(SHOTS, "--objects", *parts, "--mode", "random", "--out", "//review_fixed.png")
d.look("fixed.jpg")
sheets = [d.work / n for n in ("review_broken.png", "review_fixed.png")]
if not all(p.exists() and p.stat().st_size for p in sheets):
    raise DemoError("a review sheet didn't come back")

d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *parts, "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "22")
final = "qa pass · 0 errors" if qa2.get("pass") else f"qa · {len(qa2.get('errors', []))} errors"
d.run("present.py", "--caught", *caught, "--final", final)
d.look("present.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=30)
media = d.media(r, crop="crop=520:520:380:100")               # the barrel with its pink highlights
print(d.finish({"asset": "polyhaven:wine_barrel_01", "profile": "game", "pass_before": qa1.get("pass"),
                "errors_before": qa1.get("errors"), "caught": caught, "fixes": fixed.get("fixed"),
                "pass_after": qa2.get("pass"), "errors_after": qa2.get("errors"),
                "warnings_after": len(qa2.get("warnings", [])),
                "tris": sum(m["tris"] for m in qa2["objects"].values()),
                "review_sheets": [p.name for p in sheets],
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="QA this barrel before it ships: find what's broken, fix it, and show me it passes."))
