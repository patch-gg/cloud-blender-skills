"""blender-pbr-materials on Patch's cloud Blender: six measured presets, one call each, then a look-dev
rig and a Cycles render on a GPU.

Prompt it stands for: "Make a lineup of physically based materials (gold, copper, chrome, red paint,
ceramic, rubber) and render it so the reflections move."
Run: python demos/blender-pbr-materials/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

PRESETS = ["gold", "copper", "chrome", "paint", "ceramic", "rubber"]
HDRI = "/opt/blender/5.2/datafiles/studiolights/world/courtyard.exr"  # ships with Blender

d = Demo(__file__)
balls = d.run("scene.py")["balls"]
mats = {}
for p in PRESETS:
    r = d.skill("blender-pbr-materials/scripts/build_pbr_material.py", "--name", f"M_{p.title()}",
                "--preset", p, "--objects", f"Ball_{p}")
    mats[p] = {k: r.get(k) for k in ("base_color", "roughness", "metallic") if k in r} or r.get("ok")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *balls, "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.6", "--backdrop", "--frames", "96", "--lens", "50", "--elevation", "7")
d.run("present.py")
d.look("look.jpg", "--engine", "eevee")
qa = {b: d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", b, "--profile", "render") for b in balls}
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-96")
media = d.media(r, crop="crop=330:330:470:200")   # the picker picture: chrome and paint
print(d.finish({"materials": len(PRESETS), "presets": PRESETS,
                "qa_pass": sum(1 for r in qa.values() if r.get("pass")), "qa_checked": len(qa),
                "qa_errors": [e for r in qa.values() for e in r.get("errors", [])],
                "render": {k: d.last_render.get(k) for k in
                ("engine", "device", "sec_per_image", "res", "denoiser")}, **media},
               prompt="Make a lineup of physically based materials (gold, copper, chrome, red paint, "
                      "ceramic, rubber) and render it so the reflections move."))
