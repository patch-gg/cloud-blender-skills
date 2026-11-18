"""blender-workflow-recipes on Patch's cloud Blender: recipe 2, "game prop, high -> low baked", end to end on
a jerry can. Every stage is its skill's own script: blockout -> hard-surface stack (the high) -> the low
(the blockout, recipe step 2's "or manual") -> UVs + texel density -> QA gate -> high-to-low bake -> PBR
material from the bake -> smart-material wear from the baked curvature/AO -> self-bake to a game texture
set -> budget + LODs -> QA gate (it catches a floating part on LOD3; deleted, re-checked) -> GLB + FBX
export, verified by re-import. Then the stages in order on the one asset and a turntable, Cycles on a GPU.

Prompt it stands for: "Make a game-ready jerry can: high-poly bake to a low-poly mesh with worn paint,
LODs, and export it for Unreal and the web."
Run: python demos/blender-workflow-recipes/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo, DemoError, SKILLS  # noqa: E402

PARTS = ["Body", "Flange", "Handles", "Spout", "Cap"]
HIGH = [f"{p}_high" for p in PARTS]
LOW = "SM_JerryCan"
LODS = [f"{LOW}_LOD{i}" for i in range(4)]
HDRI = "/opt/blender/5.2/datafiles/studiolights/world/studio.exr"   # ships with Blender
HS = "blender-hardsurface-modeling/scripts/apply_stack.py"
QA = "blender-asset-qa/scripts/qa_check.py"
BAKE = SKILLS / "blender-texture-baking" / "scripts" / "bake_maps.py"
PBR = "blender-pbr-materials/scripts/build_pbr_material.py"
EXPORT = "blender-export-pipelines/scripts/export_asset.py"
PAINT = ["--preset", "plastic", "--color", "0.6", "0.07", "0.05"]    # red enamel: a dielectric, no clear coat
                                                                    # (a coat would skew the roughness self-bake)
d = Demo(__file__)
n = {}

# 1. blockout at real scale (the parts and the boolean cutters the high will use); gate: dimensions
r = d.run("scene.py")
n["blockout"] = {"tris": r["tris"], "body_mm": [round(v * 1000) for v in r["body_dims_m"]],
                 "overall_mm": [round(v * 1000) for v in r["overall_m"]]}
d.look("01_blockout.jpg", "--angles", "4")
d.run("snap.py", "--stage", "blockout", "--look", "clayflat", "--objects", *PARTS, quiet=True)

# 2. the high: the hard-surface stack (booleans -> 4-segment bevels -> weighted normals) on copies of the parts
d.run("high.py")
stacks = [d.skill(HS, "--objects", "Body_high", "--preset", "render", "--cutters", "Cut_XA", "Cut_XB",
                  "--width", "0.005"),
          d.skill(HS, "--objects", "Cap_high", "--preset", "render", "--cutters", "Cut_Grip", "--width", "0.0012"),
          d.skill(HS, "--objects", "Flange_high", "Handles_high", "Spout_high", "--preset", "render",
                  "--width", "0.003")]
n["high_tris"] = sum(o["tris_final"] for s in stacks for o in s["objects"].values())
d.look("02_high.jpg", "--angles", "4")
d.run("snap.py", "--stage", "bevels", "--look", "clay", "--objects", *HIGH, quiet=True)

# 3. the low (the blockout, joined, hard edges at 60 deg) -> UVs with seams on those edges -> texel density
r = d.run("low.py")
n["low_tris"] = r["tris"]
r = d.skill("blender-retopology-uv/scripts/uv_pack.py", "--objects", LOW, "--method", "seams",
            "--seams-from-sharp", "60", "--margin-px", "16", "--res", "2048", "--shape", "CONCAVE")
n["uv"] = {"seams": r["objects"][LOW].get("seams_marked"), "fallback": r["objects"][LOW].get("fallback")}
r = d.skill("blender-retopology-uv/scripts/texel_density.py", "--objects", LOW, "--res", "2048")
td = r["objects"][LOW]
n["texel_density"] = {"px_per_m": td["px_per_m"], "spread": td["spread"], "islands": td["islands"], "res": 2048}
d.run("snap.py", "--stage", "uvs", "--look", "checker", "--objects", LOW, quiet=True)

# 4. gate: QA on the low (game) and the high (render) before baking
qa_low = d.skill(QA, "--objects", LOW, "--profile", "game")
qa_high = d.skill(QA, "--objects", *HIGH, "--profile", "render")
if not (qa_low.get("pass") and qa_high.get("pass")):
    raise DemoError(f"QA gate before the bake: {qa_low.get('errors')} {qa_high.get('errors')}")
n["qa_before_bake"] = {"low": {"pass": True, "uv_coverage_pct": qa_low["objects"][LOW]["uv_coverage_pct"]},
                       "high": {"pass": True, "warnings": len(qa_high.get("warnings", []))}}

# 5. bake high -> low: normal, AO, curvature, ID, packed ORM (Cycles in the session, CPU)
r = d.cloud("run", "--timeout", 1800, BAKE, "--", "--low", LOW, "--high", *HIGH, "--maps", "normal", "ao",
            "curvature", "id", "--pack-orm", "--res", "2048", "--margin-px", "16")
n["bake"] = {"maps": sorted(r["maps"]), "res": r["res"], "device": r["device"], "extrusion_m": r["extrusion"]}
d.run("snap.py", "--stage", "bake", "--look", "bakeclay", "--objects", LOW, quiet=True)

# 6. material from the baked set, smart-material wear from the baked curvature + AO, self-bake to textures
d.skill(PBR, "--name", "M_JerryCan", *PAINT, "--textures", "//textures", "--objects", LOW)
d.run("snap.py", "--stage", "material", "--look", "copy", "--objects", LOW, quiet=True)
WEAR = {"wear": 0.06, "grime": 0.5, "dust": 0.12, "scale": 0.08}   # NOTES.md: why wear is 0.06 here
d.skill("blender-texturing/scripts/smart_material.py", "--objects", LOW,
        "--curvature-map", "//textures/T_JerryCan_CURV.png", "--ao-map", "//textures/T_JerryCan_AO.png",
        *[x for k, v in WEAR.items() for x in (f"--{k}", str(v))])
d.run("snap.py", "--stage", "wear", "--look", "copy", "--objects", LOW, quiet=True)
r = d.cloud("run", "--timeout", 1800, BAKE, "--", "--low", LOW, "--maps", "basecolor", "roughness", "metallic",
            "--samples", "8", "--out", "//textures/game")
n["self_bake"] = sorted(r["maps"])
r = d.skill(PBR, "--name", "M_JerryCan", "--textures", "//textures/game/T_JerryCan_BC.png",
            "//textures/T_JerryCan_N.png", "//textures/game/T_JerryCan_R.png", "//textures/game/T_JerryCan_M.png",
            "//textures/T_JerryCan_AO.png", "--objects", LOW)
n["texture_set"] = sorted(r["maps"])
# gate: a lit look at the textured low (turntable.py's look-dev rig, which the clip reuses at the end)
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", LOW, "--rig", "both", "--hdri", HDRI,
        "--hdri-strength", "0.5", "--backdrop", "--frames", "184", "--lens", "85", "--elevation", "16")
d.run("show.py", LOW, quiet=True)
d.look("03_material.jpg", "--camera", "LD_Cam", "--engine", "eevee")

# 7. budget, LODs, and the QA gate on every LOD (each alone: they overlap in place)
r = d.skill("blender-game-optimization/scripts/mesh_stats.py", "--objects", LOW, "--budget", "web")
n["budget"] = {"name": "web", "pass": r["budget"]["pass"], "tris": r["total_tris"], "draw_calls": r["draw_calls_est"],
               "texture_vram_mb": r["texture_vram_mb_uncompressed"]}
r = d.skill("blender-game-optimization/scripts/make_lods.py", "--objects", LOW, "--rename")
made = r["lods"][LODS[0]]
n["lods_made"] = [made[f"LOD{i}"] for i in range(4)]
qa, caught = {}, None
for name in LODS:
    q = d.skill(QA, "--objects", name, "--profile", "game")
    qa[name] = {"pass": q["pass"], "errors": q["errors"]}
    for e in q["errors"]:
        m = re.search(r"floating/detached part in (\S+) \((\d+) verts at \[([^\]]+)\]\)", e)
        if m and caught is None:
            caught = {"lod": LODS.index(m.group(1)), "verts": int(m.group(2)),
                      "at": [float(v) for v in m.group(3).split(",")]}
        elif not m:
            raise DemoError(f"QA on {name}: {e}")
if caught:  # the skill's fix for floating debris: delete it, then re-run the gate
    name = LODS[caught["lod"]]
    r = d.run("fix_lod.py", name, *[str(v) for v in caught["at"]])
    caught["tris_before"], caught["tris_after"] = n["lods_made"][caught["lod"]], r["tris_after"]
    q = d.skill(QA, "--objects", name, "--profile", "game")
    qa[name]["after_fix"] = {"pass": q["pass"], "errors": q["errors"]}
    if not q["pass"]:
        raise DemoError(f"QA still fails on {name}: {q['errors']}")
n["lod_tris"] = [caught["tris_after"] if caught and i == caught["lod"] else t for i, t in enumerate(n["lods_made"])]
n["qa"] = {"caught": caught, "lods": qa, "pass": all(v.get("after_fix", v)["pass"] for v in qa.values())}
n["tris_per_stage"] = {"blockout": n["blockout"]["tris"], "high (bevels)": n["high_tris"], "low (bake target)":
                       n["low_tris"], **{f"lod{i}": t for i, t in enumerate(n["lod_tris"])}}

# 8. export (web GLB with meshopt + WebP; Unreal FBX with the LOD chain), verified by re-importing each file
glb = d.skill(EXPORT, "--preset", "web", "--objects", LODS[0], "--out", "//export/SM_JerryCan.glb")
fbx = d.skill(EXPORT, "--preset", "unreal", "--objects", *LODS, "--out", "//export/SM_JerryCan.fbx")
shutil.copy2(d.root / "verify_export.py", d.work / "verify_export.py")   # its own Blender: an empty scene
ver = d.cloud("run", "--process", d.work / "verify_export.py", "--", "/work/export/SM_JerryCan.glb",
              "/work/export/SM_JerryCan.fbx")
if not ver.get("ok"):
    raise DemoError(f"export verification failed: {ver}")
n["export"] = {"files": {Path(f["file"]).name: f["kb"] for f in glb["files"] + fbx["files"]},
               "glb": glb["files"][0]["summary"],
               "verified": {k: {"meshes": {m: {"tris": v["tris"], "dims_mm": [round(x * 1000) for x in v["dims_m"]],
                                               "scale": v["scale"]} for m, v in f["meshes"].items()},
                                "images": len(f["images"])} for k, f in ver["files"].items()}}

# 9. presentation: the exported GLB back in the scene, then the stage-by-stage cut on the look-dev rig
gi = d.run("import_glb.py", "/work/export/SM_JerryCan.glb")
pj = d.work / "present.json"
pj.write_text(json.dumps({
    "high_tris": n["high_tris"], "low_tris": n["low_tris"], "texel": round(td["px_per_m"]), "lods": n["lod_tris"],
    "lods_made": n["lods_made"], "caught_lod": caught["lod"] if caught else None,
    "caught_at": caught["at"] if caught else None,
    "glb_kb": round(glb["files"][0]["kb"]), "fbx_kb": round(fbx["files"][0]["kb"]),
    "glb_object": gi["imported"][0]["object"], "exposure": -1.2}), "utf-8")
p = d.run("present.py", pj)
d.expr("import bpy; bpy.context.scene.frame_set(66)", quiet=True)
d.look("04_present_wear.jpg", "--camera", "LD_Cam", "--engine", "eevee")
d.expr("import bpy; bpy.context.scene.frame_set(1)", quiet=True)
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "48",
             "--res", "1280", "720", "--percent", "100", frames=f"1-{p['frames']}", poster=124)
media = d.media(r, crop="crop=600:600:340:90")   # the picker picture: the whole can, not the floor
print(d.finish({**n, "stages": p["stages"], "render": {k: d.last_render.get(k) for k in
                ("engine", "device", "sec_per_image", "res", "denoiser")}, **media},
               prompt="Make a game-ready jerry can: high-poly bake to a low-poly mesh with worn paint, LODs, "
                      "and export it for Unreal and the web."))
