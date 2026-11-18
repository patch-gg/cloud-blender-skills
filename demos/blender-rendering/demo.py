"""blender-rendering on Patch's cloud Blender: one still life, the same shot rendered by render_batch.py in
Workbench, EEVEE and Cycles on a GPU, then set side by side, split where a prop crosses each divider.

Prompt it stands for: "Render this still life in Workbench, EEVEE and Cycles, same shot, so I can compare them."
Run: python demos/blender-rendering/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

PROPS = ["polyhaven:potted_plant_04", "polyhaven:antique_ceramic_vase_01", "polyhaven:brass_goblets",
         "polyhaven:wine_bottles_01", "polyhaven:brass_vase_03"]
HDRI = "/opt/blender/5.2/datafiles/studiolights/world/interior.exr"  # ships with Blender
FRAMES = "1-96"
RES = ["--res", "1280", "720", "--percent", "100"]
ENGINES = {  # render_batch.py flags; everything else (camera, lights, materials) is the same .blend
    "workbench": ["--engine", "BLENDER_WORKBENCH", "--view", "Standard"],
    "eevee": ["--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "32"],
    "cycles": ["--engine", "CYCLES", "--preset", "preview", "--samples", "64"],
}

d = Demo(__file__)
props = d.run("scene.py", *map(str, d.asset(*PROPS)))["props"]
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *props, "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.3", "--backdrop", "--frames", "96", "--lens", "50", "--elevation", "8")
split = d.run("present.py")["split"]
d.look("look.jpg")
groups = {}  # QA each library asset on its own (a set's pieces are checked together)
for name in props:
    groups.setdefault(name.split("_0")[0] if name.startswith(("brass_goblet", "potted_plant")) else name,
                      []).append(name)
qa = {g: d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", *obs, "--profile", "render")
      for g, obs in groups.items()}
shot = d.save("shot.blend")

renders = {}
for name, flags in ENGINES.items():  # the same .blend three times, each in its own folder (d.render's frames)
    blend = d.work / name / "demo.blend"
    blend.parent.mkdir(exist_ok=True)
    shutil.copy2(shot, blend)
    d.render(blend, *flags, *RES, frames=FRAMES)
    renders[name] = {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser",
                                                      "view")}
renders["eevee"]["samples"], renders["cycles"]["samples"] = 32, 64

shutil.copy2(d.root / "compose.py", d.work / "compose.py")  # the side-by-side, as a VSE scene
d.cloud("run", "--process", d.work / "compose.py", "--", "--split", *map(str, split), "--frames", "96",
        "--out", "compose/demo.blend")
r = d.render("work/compose/demo.blend", "--engine", "BLENDER_WORKBENCH", *RES, frames=FRAMES)
media = d.media(r, crop="crop=340:340:703:215")  # the picker picture: the bottle on the eevee | cycles seam
print(d.finish({"engines": renders, "split": split, "frames": 96,
                "qa_pass": sum(1 for v in qa.values() if v.get("pass")), "qa_checked": len(qa),
                "qa_errors": [e for v in qa.values() for e in v.get("errors", [])], **media},
               prompt="Render this still life in Workbench, EEVEE and Cycles, same shot, so I can compare them."))
