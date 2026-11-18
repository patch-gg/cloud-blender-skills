"""blender-game-optimization on Patch's cloud Blender: measure a detailed prop against a platform budget, build its
LOD chain with make_lods.py, QA every level (fixing what QA catches), re-measure each against the budget, and show
the chain side by side with a 1 px wire so the triangle density reads.

Prompt it stands for: "This statue is too heavy for a mobile game: make LODs and tell me which one fits the budget."
Run: python demos/blender-game-optimization/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

GO = "blender-game-optimization/scripts/"
QA = "blender-asset-qa/scripts/qa_check.py"
BUDGET = "mobile"
LODS = [f"SM_Horse_LOD{i}" for i in range(4)]

d = Demo(__file__)
src = d.asset("polyhaven:horse_statue_01")[0]          # Poly Haven, CC0: a porcelain horse, 22k tris
scene = d.run("scene.py", src)
d.look("01_source.jpg")

# 1. measure  2. clean + LODs (make_lods.py halves the tris per level)  3. QA every level, fix, re-check
before = d.skill(GO + "mesh_stats.py", "--objects", "SM_Horse", "--budget", BUDGET)
lods = d.skill(GO + "make_lods.py", "--objects", "SM_Horse", "--cleanup", "--rename")
qa, first, fixed = {}, {}, {}
for n in LODS:
    r = d.skill(QA, "--objects", n, "--profile", "game")
    first[n] = r.get("errors", [])
    if any(e.startswith("z-fighting") for e in first[n]):   # qa_check's fix: delete the hidden duplicate
        fixed[n] = d.run("fix_lod.py", n)["fixed"][n]
        r = d.skill(QA, "--objects", n, "--profile", "game")
    qa[n] = r
# 4. re-measure every level against the budget
stats = {n: d.skill(GO + "mesh_stats.py", "--objects", n, "--budget", BUDGET) for n in LODS}
fits = [str(i) for i, n in enumerate(LODS) if stats[n]["budget"]["pass"]]

# present: the chain side by side, the studio stage from blender-lighting-lookdev, a wire, labels
d.run("lineup.py", "SM_Horse", BUDGET, *fits)
d.look("02_lineup.jpg")                                  # every LOD's silhouette, side by side
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *LODS, "--rig", "studio", "--backdrop",
        "--frames", "96", "--lens", "50", "--elevation", "8")
d.run("present.py", "SM_Horse")
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-96")
media = d.media(r, crop="crop=380:380:880:140")          # the picker picture: lod3's big triangles

chain = []
for i, n in enumerate(LODS):
    s, q = stats[n], qa[n]
    chain.append({"lod": i, "tris": s["total_tris"], "verts": s["total_verts"],
                  "ratio": round(s["total_tris"] / stats[LODS[0]]["total_tris"], 3),
                  f"fits_{BUDGET}": s["budget"]["pass"], "qa_pass": q.get("pass"),
                  "qa_errors_first": first[n], "qa_fixed": fixed.get(n), "qa_warnings": q.get("warnings", [])})
print(d.finish({
    "asset": "polyhaven:horse_statue_01", "source_tris": scene["tris"], "source_verts": scene["verts"],
    "budget": {"platform": BUDGET, "prop_tris": before["budget"]["limits"]["prop_tris"],
               "source_over": before["budget"]["over"]},
    "cleanup_removed_verts": lods["lods"]["SM_Horse_LOD0"].get("cleanup_removed_verts"),
    "lods": chain, "fits": [LODS[int(i)] for i in fits],
    "draw_calls_est": stats[LODS[0]]["draw_calls_est"],
    "texture_vram_mb_uncompressed": stats[LODS[0]]["texture_vram_mb_uncompressed"],
    "qa_pass": sum(1 for q in qa.values() if q.get("pass")), "qa_checked": len(qa),
    "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")}, **media},
    prompt="This statue is too heavy for a mobile game: make LODs and tell me which one fits the budget."))
