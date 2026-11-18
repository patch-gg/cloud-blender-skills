"""blender-core on Patch's cloud Blender: the loop every skill rests on. env_report.py first, then a toy
rocket built in five small bpy steps with a look after each, then the verify step (numbers, qa_check,
a wire review sheet, files present), shown as a stop-motion of the build.

Prompt it stands for: "Build a little retro rocket in Blender one step at a time, check each step, and
verify it at the end."
Run: python demos/blender-core/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo, DemoError  # noqa: E402

STEPS = ["body", "nose", "fins", "window", "paint"]
NUMBERS = """import bpy
dg = bpy.context.evaluated_depsgraph_get()
obs = [o for o in bpy.data.objects if o.type == "MESH" and "build_step" in o]
tris = 0
for o in obs:
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    o.evaluated_get(dg).to_mesh_clear()
lo = min((o.matrix_world @ v.co).z for o in obs for v in o.data.vertices)
hi = max((o.matrix_world @ v.co).z for o in obs for v in o.data.vertices)
result = {"objects": len(obs), "tris": tris, "height_m": round(hi - lo, 3), "ground_z": round(lo, 4),
          "materials": sorted({s.material.name for o in obs for s in o.material_slots if s.material})}
"""

d = Demo(__file__)
env = d.skill("blender-core/scripts/env_report.py")             # first call in a session
made = {}
for i, step in enumerate(STEPS, 1):                              # small steps, a look after each
    made.update(d.run("build.py", "--step", step)["made"])
    d.look(f"{i}_{step}.jpg")
parts = list(made)

# verify: numbers, qa_check, a look at the topology, the files it wrote
nums = d.expr(NUMBERS)
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", *parts, "--profile", "game")
sheet = d.skill("blender-asset-qa/scripts/review_shots.py", "--objects", *parts, "--mode", "wire",
                "--out", "//review_wire.png")
pulled = d.work / "review_wire.png"
if not (pulled.exists() and pulled.stat().st_size > 0):
    raise DemoError(f"review sheet missing: {sheet}")
final = f"qa pass · {nums['tris']:,} tris" if qa.get("pass") else f"qa · {len(qa.get('errors', []))} errors"

d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *parts, "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "9")
d.run("present.py", "--env", "blender " + env["blender"].split()[0], "--final", final)
d.look("present.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=120)
media = d.media(r, crop="crop=620:620:365:30")                # the picker picture: the whole rocket
print(d.finish({"blender": env.get("blender"), "engines": env.get("engines"), "steps": STEPS,
                "looks": len(STEPS) + 1, **nums, "qa_profile": "game", "qa_pass": qa.get("pass"),
                "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "review_sheet": pulled.name, "review_sheet_kb": round(pulled.stat().st_size / 1024),
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="Build a little retro rocket in Blender one step at a time, check each step, and verify "
                      "it at the end."))
