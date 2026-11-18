"""blender-simulation on Patch's cloud Blender: nine wooden crates and two barrels drop into a loading-dock
corner as rigid bodies (sim_setup.py --rigid, wood at 500 kg/m3, baked headless to keyframes), then a canvas
tarp (classic cloth, denim preset) falls over the pile, baked headless over frames 48-120 against simple
collision proxies of the crates. Afternoon light from blender-time-of-day, EEVEE on a GPU, played once.

Prompt it stands for: "Drop a pile of wooden crates and barrels into a corner, then throw a tarp over them."
Run: python demos/blender-simulation/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

SIM = "blender-simulation/scripts/sim_setup.py"
WALLS = ["Floor", "Wall_Back", "Wall_Side"]

d = Demo(__file__)
crates = d.asset("polyhaven:wooden_crate_01", "polyhaven:wooden_crate_02", "polyhaven:wooden_military_crate")
barrel = d.asset("polyhaven:Barrel_01")[0]
scene = d.run("scene.py", "--crates", *crates, "--barrel", barrel)
bodies = scene["bodies"]
d.look("start.jpg")
t = time.time()
rigid = d.skill(SIM, "--rigid", "--active", *bodies, "--passive", *WALLS, "--density", 500, "--frames", 1, 120,
                "--bake", "--to-keys")
rigid_s = round(time.time() - t, 1)
d.look("rigid.jpg")  # the last frame: the pile at rest
proxies = d.run("proxies.py", "--bodies", *bodies)["proxies"]
t = time.time()
cloth = d.skill(SIM, "--cloth", "Tarp", "--preset", "denim", "--colliders", *proxies, *WALLS, "--frames", 48, 120,
                "--bake")
cloth_s = round(time.time() - t, 1)
d.run("present.py", "--switch", 48, "--labels",
      f"rigid bodies · {scene['crates']} crates, {scene['barrels']} barrels",
      f"cloth · denim · {scene['tarp_verts']:,} verts")
mood = d.skill("blender-time-of-day/scripts/scene_mood.py", "--time", "afternoon", "--heading", 150)
d.expr("import bpy; bpy.context.scene.frame_set(100)", quiet=True)
d.look("look.jpg", "--camera", "Cam")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Tarp", "--profile", "render")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", 32,
             "--res", 1280, 720, "--percent", 100, frames="1-120", poster=110)
media = d.media(r, crop="crop=420:420:430:200")  # the picker picture: the tarp over the crates
res = rigid.get("result", {})
print(d.finish({"rigid": {"bodies": len(bodies), "kg": round(sum(v["mass"] for k, v in rigid["rigid"].items()
                                                                if k in bodies), 1),
                          "settled_min_z": min(res[b]["min_z"] for b in bodies),
                          "on_another": sum(1 for b in bodies if res[b]["min_z"] > 0.05),
                          "frames": [1, 120], "bake_s": rigid_s, "to_keys": len(rigid.get("baked_to_keyframes", []))},
                "cloth": {"preset": "denim", "verts": scene["tarp_verts"], "frames": [48, 120], "bake_s": cloth_s,
                          "colliders": len(proxies) + len(WALLS),
                          "min_z": cloth.get("result", {}).get("Tarp", {}).get("min_z")},
                "mood": {k: mood.get(k) for k in ("time", "key", "exposure")},
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="Drop a pile of wooden crates and barrels into a corner, then throw a tarp over them."))
