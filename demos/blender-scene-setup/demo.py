"""blender-scene-setup on Patch's cloud Blender: a deliberately messy scene (four CC0 props from Patch's
asset library with default names, an unapplied rotation, a mirror, a centimetre import, an origin left at
the world origin, everything in the scene root, orphan data, imperial units), scene_audit.py, its fixes,
the rest of the procedure (units, collections, names, origins) and the clean re-audit.

Prompt it stands for: "This .blend is a mess. Audit it and clean it up the way a studio would: names,
collections, transforms, origins, units and orphans."
Run: python demos/blender-scene-setup/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

ASSETS = {"polyhaven:potted_plant_02": "PottedPlant", "polyhaven:wine_barrel_01": "WineBarrel",
          "polyhaven:metal_tool_chest": "ToolChest", "polyhaven:side_table_tall_01": "SideTable"}
UNITS = {"FEET": "ft", "INCHES": "in", "METERS": "m", "CENTIMETERS": "cm"}

d = Demo(__file__)
paths = d.asset(*ASSETS)
mess = d.run("scene.py", *paths)["props"]                       # messy name -> what's wrong with it
d.look("before.jpg")
before = d.skill("blender-scene-setup/scripts/scene_audit.py")
fixed = d.skill("blender-scene-setup/scripts/scene_audit.py", "--fix", "purge", "scale")
base = {a.split(":")[1]: n for a, n in ASSETS.items()}
tidy = d.run("tidy.py", "--names", *[f"{old}={base[p['asset']]}" for old, p in mess.items()])["props"]
after = d.skill("blender-scene-setup/scripts/scene_audit.py")
d.look("after.jpg")
qa = {o: d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", o, "--profile", "render") for o in tidy}

# the placards: what the audit caught on each prop, then its clean name
iss = before["issues"]
items = []
for new, t in tidy.items():
    old, p = t["was"], mess[t["was"]]
    if old in iss.get("negative_scale", []):
        problem = "mirrored · scale -1"
    elif old in iss.get("rotated", []):
        problem = f"rotated {round(max(abs(v) for v in p['rotation_deg']))}°"
    elif old in iss.get("unapplied_scale", []):
        problem = f"scale {p['scale'][0]:g}"
    elif old in iss.get("origin_far", []):
        off = sum((a - b) ** 2 for a, b in zip(p["origin"], t["origin"])) ** 0.5
        problem = f"origin {off:.1f} m off"
    else:
        problem = "scene root"
    items.append({"name": new, "before": old, "problem": problem})
u0, u1 = before["units"]["length"], after["units"]["length"]
labels = {"items": items,
          "scene_before": f"units {UNITS.get(u0, u0.lower())} · {before['orphans']} orphans · "
                          f"{len(iss.get('in_scene_root', []))} in scene root",
          "scene_after": f"units {UNITS.get(u1, u1.lower())} · {after['orphans']} orphans · "
                         f"{len({t['collection'] for t in tidy.values()})} collections"}
(d.work / "labels.json").write_text(json.dumps(labels, ensure_ascii=False), "utf-8")

d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *tidy, "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "8")
d.run("present.py", d.work / "labels.json")
d.look("present.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "preview", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=30)
media = d.media(r, crop="crop=360:360:365:95")                # the barrel and its pink label
print(d.finish({"props": len(tidy), "issues_before": {k: len(v) for k, v in iss.items()},
                "units_before": [before["units"]["system"], u0], "orphans_before": before["orphans"],
                "fixed": fixed.get("fixed"), "issues_after": after["issues"],
                "units_after": [after["units"]["system"], u1], "orphans_after": after["orphans"],
                "renamed": {t["was"]: n for n, t in tidy.items()},
                "collections": sorted({t["collection"] for t in tidy.values()}),
                "qa_profile": "render", "qa_pass": sum(1 for r in qa.values() if r.get("pass")), "qa_checked": len(qa),
                "qa_errors": [e for r in qa.values() for e in r.get("errors", [])],
                "inside_out_after_fix": sum(m.get("inside_out_islands", 0) for r in qa.values()
                                            for m in r.get("objects", {}).values()),
                "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
               prompt="This .blend is a mess. Audit it and clean it up the way a studio would: names, collections, "
                      "transforms, origins, units and orphans."))
