"""blender-texturing on Patch's cloud Blender: a clean painted jerry can, then smart_material.py's layers
(edge wear to bare steel, cavity grime, dust on top) and a decal.py stencil, shown as a before/after wipe.

Prompt it stands for: "Make this jerry can look used: chipped paint on the edges, grime in the creases,
dust on top, and a DIESEL stencil on the side."
Run: python demos/blender-texturing/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

HDRI = "/opt/blender/5.2/datafiles/studiolights/world/studio.exr"  # ships with Blender
LAYERS = {"wear": 0.5, "grime": 0.85, "dust": 0.6}

d = Demo(__file__)
glb = d.asset("polyhaven:metal_jerrycan")[0]                    # CC0, 20k tris, bevelled mid-poly
scene = d.run("scene.py", glb, "decals/diesel.png")             # one mesh + the stencil artwork
# the clean base: red enamel, no clear coat (a coat would stay glossy over dust and grime)
d.skill("blender-pbr-materials/scripts/build_pbr_material.py", "--name", "M_Paint", "--preset", "plastic",
        "--color", "0.5", "0.045", "0.03", "--objects", "JerryCan")
sm = d.skill("blender-texturing/scripts/smart_material.py", "--objects", "JerryCan",
             *[a for k, v in LAYERS.items() for a in (f"--{k}", str(v))],
             "--edge-width", "0.01", "--scale", "0.03", "--grime-color", "0.09", "0.07", "0.05")
dc = d.skill("blender-texturing/scripts/decal.py", "--target", "JerryCan", "--at", "0", "-0.1", "0.2",
             "--image", d.work / "decals" / "diesel.png", "--size", "0.17")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "JerryCan", "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.6", "--backdrop", "--frames", "96", "--lens", "85", "--elevation", "15")
d.look("layers.jpg", "--engine", "eevee", "--camera", "LD_Cam")
d.run("present.py")
d.expr("import bpy; bpy.context.scene.frame_set(22)", quiet=True)  # mid-wipe
d.look("look.jpg", "--engine", "eevee", "--camera", "LD_Cam")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "JerryCan", "DC_diesel", "--profile", "render")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-96", poster=22)
media = d.media(r, crop="crop=520:520:385:105")   # the picker picture: the can across the wipe line
print(d.finish({"tris": scene.get("tris"), "layers": LAYERS, "curvature": sm.get("curvature", {}).get("JerryCan"),
                "curvature_note": sm.get("note"),
                "decal": {k: dc.get(k) for k in ("size_m", "offset_m", "subdiv", "gap_min_m", "gap_max_m")},
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors", []), "zfighting": qa.get("zfighting"),
                "decal_zfight_pairs": sum(z["tri_pairs"] for z in qa.get("zfighting") or [] if "DC_" in z["where"]),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser")},
                **media},
               prompt="Make this jerry can look used: chipped paint on the edges, grime in the creases, dust on "
                      "top, and a DIESEL stencil on the side."))
