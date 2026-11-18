"""blender-environment-kits on Patch's cloud Blender: a ridged, eroded terrain with its slope/height material,
then two scatter layers (pines on gentle ground between 16 and 85 m, rocks weighted to steep slopes) growing
across it in a sweep, seen from a slow aerial drift at golden hour (blender-time-of-day), EEVEE on a GPU.

Prompt it stands for: "Make a mountain valley with pine forest and rocks placed by slope and height, and fly
over it at golden hour."
Run: python demos/blender-environment-kits/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

KIT = "kenney:nature-kit/"
PINES = ["tree_pineTallA_detailed", "tree_pineTallB_detailed", "tree_pineTallC_detailed",
         "tree_pineTallD_detailed", "tree_pineRoundA", "tree_pineRoundC"]
ROCKS = ["rock_largeA", "rock_largeB", "rock_largeD", "rock_largeF", "rock_tallA", "rock_tallB"]
TERRAIN = "blender-environment-kits/scripts/terrain.py"
SCATTER = "blender-environment-kits/scripts/scatter.py"

d = Demo(__file__)
pines = d.asset(*[f"{KIT}{n}.glb" for n in PINES])
rocks = d.asset(*[f"{KIT}{n}.glb" for n in ROCKS])
d.run("scene.py", "--pines", *pines, "--rocks", *rocks)
terrain = d.skill(TERRAIN, "--size", 600, "--res", 513, "--type", "ridged", "--scale", 400, "--octaves", 4,
                  "--height", 120, "--erosion", 40, "--material", "--seed", 3)
d.look("terrain.jpg")
# the far ranges: a second, coarser terrain whose flattened centre goes under the first (present.py --sink)
far = d.skill(TERRAIN, "--name", "Far", "--size", 2400, "--res", 257, "--type", "ridged", "--scale", 900,
              "--octaves", 5, "--height", 300, "--erosion", 8, "--flatten", 0, 0, 440, "--material", "--seed", 9)
# the sweep: a density mask that scatter.py reads (--mask), growing left to right in the shot
d.run("reveal.py", "--frames", 24, 90, "--x", -340, 340, "--width", 80, "--axis", 1, -0.075)
pine = d.skill(SCATTER, "--target", "Terrain", "--collection", "Pines", "--density", 0.045, "--min-distance", 4.5,
               "--max-slope", 30, "--height-min", 16, "--height-max", 85, "--scale", 0.7, 1.3, "--mask", "reveal",
               "--name", "ENV_Pines")
rock = d.skill(SCATTER, "--target", "Terrain", "--collection", "Rocks", "--density", 0.005, "--min-distance", 10,
               "--max-slope", 70, "--align", 0.8, "--scale", 0.6, 1.6, "--mask", "reveal_rock", "--seed", 2,
               "--name", "ENV_Rocks")
d.look("scatter.jpg")
d.run("present.py", "--cam-a", -20, -340, 140, "--cam-b", -5, -280, 132, "--look-a", 10, 60, 40,
      "--look-b", 15, 100, 38, "--lens", 32, "--frames", 1, 120, "--switch", 57, "--sink", "Far", "--labels",
      "terrain · ridged · 600 m", f"scatter · {pine['instances']:,} pines · {rock['instances']:,} rocks")
mood = d.skill("blender-time-of-day/scripts/scene_mood.py", "--time", "golden", "--elevation", 14, "--heading", 70,
               "--fog-visibility", 25000, "--fog-color", 1, 0.86, 0.68, "--fog-anisotropy", 0.4, "--keep-view")
d.expr("import bpy; bpy.context.scene.frame_set(60)", quiet=True)  # mid-sweep
d.look("look.jpg", "--camera", "Cam", "--engine", "eevee")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Terrain", "--profile", "game", "--no-modifiers")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", 32,
             "--res", 1280, 720, "--percent", 100, frames="1-120", poster=112)
media = d.media(r, crop="crop=400:400:150:180")   # the picker picture: the forested peak on the left
keys = ("size_m", "res", "tris", "height_range_m", "slope_mean_deg", "rock_pct")
layer = ("instances", "by_source", "slope_max_deg", "height_range", "per_m2")
print(d.finish({"terrain": {k: terrain.get(k) for k in keys}, "backdrop": {k: far.get(k) for k in keys},
                "pines": {k: pine.get(k) for k in layer}, "rocks": {k: rock.get(k) for k in layer},
                "mood": {k: mood.get(k) for k in ("time", "key", "exposure", "fog")},
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="Make a mountain valley with pine forest and rocks placed by slope and height, and fly "
                      "over it at golden hour."))
