"""blender-texture-baking on Patch's cloud Blender: a hard-surface crate (booleans and bevels with
blender-hardsurface-modeling) baked onto a 12-triangle box with bake_maps.py: normal, AO, curvature, base
colour, roughness and metallic, packed ORM. The row shows high | low | low + bake, and three maps small.

Prompt it stands for: "Bake this high-poly crate down to a 12-triangle box: normal, AO and curvature maps,
and show me the low poly with the bake next to the high."
Run: python demos/blender-texture-baking/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

MAPS = ["normal", "ao", "curvature", "basecolor", "roughness", "metallic"]

d = Demo(__file__)
scene = d.run("scene.py")                      # body + cutter, bolts (floaters), the 12-tri low with UVs
hs = d.skill("blender-hardsurface-modeling/scripts/apply_stack.py", "--objects", "Crate_high", "--preset",
             "render", "--cutters", "Crate_cut", "--width", "0.004", "--apply")
high_tris = hs["objects"]["Crate_high"]["tris_final"] + scene["bolt_tris"]
hide_low = "import bpy; bpy.data.objects['Crate_low'].hide_render = {}"   # the low sits over the high
d.expr(hide_low.format(True), quiet=True)
d.look("high.jpg", "--angles", "4")
d.expr(hide_low.format(False), quiet=True)
# QA before baking: flipped normals and floating chunks make most bake garbage
qa_high = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Crate_high", "Crate_bolts", "--profile", "render")
qa_low = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Crate_low", "--profile", "game")
bake = d.skill("blender-texture-baking/scripts/bake_maps.py", "--low", "Crate_low", "--high", "Crate_high",
               "Crate_bolts", "--maps", *MAPS, "--res", "1024", "--samples", "32", "--margin-px", "8",
               "--pack-orm", "--name", "Crate")
d.run("lineup.py", str(high_tris))             # copy the low for the textured version, spread the row
mat = d.skill("blender-pbr-materials/scripts/build_pbr_material.py", "--name", "M_Crate_baked", "--textures",
              d.work / "textures", "--objects", "Crate_baked")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Crate_high", "Crate_bolts", "Crate_low",
        "Crate_baked", "--rig", "studio", "--backdrop", "--frames", "96", "--lens", "50", "--elevation", "13")
d.run("present.py")
d.look("look.jpg", "--engine", "eevee", "--camera", "LD_Cam")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Crate_baked", "--profile", "game")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-96", poster=49)
media = d.media(r, crop="crop=330:330:860:105")   # the picker picture: the baked low poly
print(d.finish({"high_tris": high_tris, "low_tris": scene["low_tris"], "maps": sorted(bake.get("maps", {})),
                "bake": {k: bake.get(k) for k in ("device", "res", "extrusion")}, "material_maps": mat.get("maps"),
                "qa_high_pass": qa_high.get("pass"), "qa_low_pass": qa_low.get("pass"), "qa_pass": qa.get("pass"),
                "qa_errors": qa_high.get("errors", []) + qa_low.get("errors", []) + qa.get("errors", []),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser")},
                **media},
               prompt="Bake this high-poly crate down to a 12-triangle box: normal, AO and curvature maps, and "
                      "show me the low poly with the bake next to the high."))
