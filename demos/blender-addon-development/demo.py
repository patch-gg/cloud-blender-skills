"""blender-addon-development on Patch's cloud Blender: a small extension made from the skill's template
(gear_maker/: the template's four files with an operator that adds involute spur gears, a sidebar panel and
a preference), validated, built and installed headless with Blender's extension command line, then its
operator run with different parameters: a meshing gear train that spins at the true ratios.

Prompt it stands for: "Write me a Blender extension that adds spur gears with a tooth count, size and
spokes; validate it, build it, install it, and show it working."
Run: python demos/blender-addon-development/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo, DemoError  # noqa: E402

HDRI = "/opt/blender/5.2/datafiles/studiolights/world/studio.exr"  # ships with Blender
ZIP = "dist/gear_maker-1.0.0.zip"

d = Demo(__file__)
src = d.work / "gear_maker"
shutil.rmtree(src, ignore_errors=True)
shutil.copytree(d.root / "gear_maker", src, ignore=shutil.ignore_patterns("__pycache__"))
d.cloud("push", src)                                             # -> /work/gear_maker
val = d.cloud("exec", "blender --factory-startup --command extension validate gear_maker")
d.cloud("exec", "mkdir -p dist && blender --factory-startup --command extension build "
                "--source-dir gear_maker --output-dir dist")      # build won't create its output folder
zip_ = d.work / ZIP
if not (zip_.exists() and zip_.stat().st_size):
    raise DemoError("the build made no zip")
inst = d.cloud("exec", f"blender --command extension install-file -r user_default -e {ZIP}")
if "Installed" not in inst.get("stdout", ""):                   # install-file exits 0 even when it fails
    raise DemoError(f"install failed: {inst.get('stdout', '')[-400:]}")

made = d.run("make_gears.py")["gears"]                           # the operator, once per gear
names = [g["object"] for g in made]
d.look("gears.jpg")
qa = {n: d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", n, "--profile", "render") for n in names}

d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *names, "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.8", "--backdrop", "--frames", "120", "--lens", "50", "--elevation", "52")
spin = d.run("present.py")
d.look("present.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120")
media = d.media(r, crop="crop=560:560:300:60")                  # the big gear and its neighbours
print(d.finish({"extension": "gear_maker 1.0.0", "validate": val.get("ok"), "zip_bytes": zip_.stat().st_size,
                "installed": inst.get("stdout", "").strip().splitlines()[-1],
                "operator": "gear_maker.add_gear",
                "calls": [{k: g[k] for k in ("teeth", "spokes", "bore", "metal", "tris", "diameter", "result")}
                          for g in made],
                "turns_per_loop": spin.get("turns"),
                "qa_pass": sum(1 for x in qa.values() if x.get("pass")), "qa_checked": len(qa),
                "qa_errors": [e for x in qa.values() for e in x.get("errors", [])],
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="Write me a Blender extension that adds spur gears with a tooth count, size and spokes; "
                      "validate it, build it, install it, and show it working."))
