"""blender-stylized-npr on Patch's cloud Blender: one knight in a row of five, each a toon_setup.py call that
adds one thing: plain pbr, toon bands, shadow tint, rim, inverted-hull outline. The key sun every toon copy
follows swings side to side, so the bands sweep across them all.

Prompt it stands for: "Make this knight cel-shaded: two-tone bands, cool shadows, a rim light and ink
outlines, and show me each step next to the plain render."
Run: python demos/blender-stylized-npr/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

TOON = "blender-stylized-npr/scripts/toon_setup.py"
STAGES = {  # one call per copy, each adding one thing to the one before
    "Knight_bands": ["--bands", "2", "--shadow-tint", "0.55", "0.55", "0.55", "--outline", "0"],  # grey shadows
    "Knight_tint": ["--bands", "2", "--outline", "0"],                                         # default cool tint
    "Knight_rim": ["--bands", "2", "--rim", "0.5", "--outline", "0"],
    "Knight_outline": ["--bands", "2", "--rim", "0.5", "--outline", "0.01"],  # ~2 px at this framing
}

d = Demo(__file__)
glb = d.asset("kaykit:adventurers/characters/Knight.glb")[0]   # CC0, rigged, 5.8k tris
scene = d.run("scene.py", glb, "0")                            # posed (Idle_A), frozen, five copies
d.look("row.jpg", "--angles", "2")
toon = {name: d.skill(TOON, "--objects", name, *flags) for name, flags in STAGES.items()}
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *scene["objects"], "--rig", "hdri",
        "--backdrop", "--frames", "96", "--lens", "50", "--elevation", "6")
d.run("present.py")
d.expr("import bpy; bpy.context.scene.frame_set(73)", quiet=True)   # key from the left
d.look("look.jpg", "--engine", "eevee", "--camera", "LD_Cam")
# the mesh itself (the outline hull has flipped normals by design, so modifiers are left out); render
# profile, since node toon shading lives in renders (engines rebuild it, see the skill)
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Knight_outline", "--profile", "render",
             "--no-modifiers")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", "32",
             "--res", "1280", "720", "--percent", "100", frames="1-96", poster=73)
media = d.media(r, crop="crop=330:330:955:70")   # the picker picture: the outlined knight
print(d.finish({"tris": scene["tris"], "merged_verts": scene["merged_verts"],
                "stages": {k: " ".join(v) for k, v in STAGES.items()},
                "key_light": toon["Knight_bands"].get("key_light"),
                "view_transform": toon["Knight_outline"].get("view_transform"),
                "outline": toon["Knight_outline"].get("outline"),
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors", []), "qa_warnings": qa.get("warnings", []),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")}, **media},
               prompt="Make this knight cel-shaded: two-tone bands, cool shadows, a rim light and ink outlines, "
                      "and show me each step next to the plain render."))
