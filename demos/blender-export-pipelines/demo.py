"""blender-export-pipelines on Patch's cloud Blender: one asset prepared with the pre-export checklist and
QA'd, exported with six engine presets (one export_asset.py call each, every file verified), then every
file imported back into Blender and measured against the original. The clip: the six re-imported copies on
a step, spinning in sync, each labelled with its preset, format and file size.

Prompt it stands for: "Export this rubber duck for Godot, the web, USD, Unity, Unreal and Roblox, and prove
every file comes back into Blender the same."
Run: python demos/blender-export-pipelines/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

NAME = "SM_RubberDuck"
PRESETS = {"godot": f"export/{NAME}_godot.glb", "web": f"export/{NAME}_web.glb", "usd": f"export/{NAME}.usdz",
           "unity": f"export/{NAME}_unity.fbx", "unreal": f"export/{NAME}_unreal.fbx",
           "roblox": f"export/{NAME}_roblox.fbx"}

d = Demo(__file__)
glb = d.asset("polyhaven:rubber_duck_toy")[0]
prep = d.run("scene.py", glb, NAME)       # SM_/M_/T_ names, transforms applied, origin, textures as files
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", NAME, "--profile", "game")
exports = {}
for preset, out in PRESETS.items():
    r = d.skill("blender-export-pipelines/scripts/export_asset.py", "--preset", preset, "--objects", NAME,
                "--out", out)
    f = r["files"][0]
    exports[preset] = {"file": Path(f["file"]).name, "ok": f["ok"], "kb": f["kb"],
                       **({"glb": {k: f["summary"][k] for k in ("tris", "materials", "images", "extensions")}}
                          if "summary" in f else {})}
rt = d.run("roundtrip.py", NAME, *[f"{k}={v}" for k, v in PRESETS.items()])
d.look("roundtrip.jpg", "--engine", "eevee")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *rt["meshes"], *rt["labels"],
        "--rig", "studio", "--backdrop", "--frames", "96", "--lens", "50", "--elevation", "13")
d.run("present.py")
d.look("look.jpg", "--engine", "eevee", "--max-size", "1280")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-96", poster=1)
media = d.media(r, crop="crop=264:264:508:380")   # the picker picture: the front-middle duck
back = rt["roundtrip"]
print(d.finish({
    "asset": {"id": "polyhaven:rubber_duck_toy", "object": NAME, "tris": prep["tris"], "dims_m": prep["dims_m"],
              "materials": prep["materials"], "textures": sorted(prep["textures"])},
    "qa": {"pass": qa.get("pass"), "errors": qa.get("errors"), "warnings": qa.get("warnings")},
    "exports": exports,
    "exports_ok": sum(1 for e in exports.values() if e["ok"]),
    "roundtrip": {p: {k: v[k] for k in ("max_dev_mm", "tris", "materials", "images", "images_loaded",
                                        "base_color_textured", "ok")} for p, v in back.items()},
    "roundtrip_ok": sum(1 for v in back.values() if v["ok"]),
    "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res", "view")}, **media},
    prompt="Export this rubber duck for Godot, the web, USD, Unity, Unreal and Roblox, and prove every file "
           "comes back into Blender the same."))
