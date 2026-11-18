"""blender-geometry-nodes on Patch's cloud Blender: gn_builder.py turns a JSON spec (forest.json, 28 nodes) into
a Geometry Nodes tree on an island - Poisson-disc points on the flat ground, low-poly trees from Patch's asset
library picked, turned and sized at random, grown in by distance from the centre - and its Radius input is
animated so the forest spreads out behind a ring that marks it.

Prompt it stands for: "Build a geometry nodes setup that scatters a forest over this island from a seed, and
animate its radius so the forest grows out from the middle."
Run: python demos/blender-geometry-nodes/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

GN = "blender-geometry-nodes/scripts/gn_builder.py"
TREES = ["kenney:nature-kit/tree_pineDefaultA.glb", "kenney:nature-kit/tree_pineDefaultB.glb",
         "kenney:nature-kit/tree_cone.glb", "kenney:nature-kit/tree_detailed.glb",
         "kenney:nature-kit/plant_bushDetailed.glb"]          # CC0
RADIUS = 5.1

d = Demo(__file__)
paths = d.asset(*TREES)
s = d.run("scene.py", *paths)
d.look("island.jpg", "--angles", "2")
spec = d.work / "forest.json"                      # the spec goes up with the run, like scene.py
shutil.copy2(d.root / "forest.json", spec)
nodes = list(json.loads(spec.read_text())["nodes"])
d.skill(GN, "--describe", "GeometryNodeDistributePointsOnFaces", "GeometryNodeInstanceOnPoints",
        "GeometryNodeCollectionInfo", "GeometryNodeRaycast", "FunctionNodeRandomValue")
gn = d.skill(GN, "--spec", spec, "--apply", "Island", "--set", f"Radius={RADIUS}", "Trees=Trees",
             "Ring=M_Front", "Seed=3")
d.look("forest.jpg", "--angles", "2")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Island", "--no-modifiers", "--profile", "render")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Island", "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "30")
p = d.run("present.py", "--radius", RADIUS)
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=62)
media = d.media(r, crop="crop=360:360:460:120")    # the picker picture: trees around the ring
print(d.finish({"tree": gn.get("tree"), "nodes": gn.get("nodes"), "links": gn.get("links"),
                "node_warnings": gn.get("node_warnings"), "inputs_animated": ["Radius", "Ring Width"],
                "trees_at_full": p.get("trees_at_full"), "instanced_tris": p.get("instanced_tris"),
                "kinds": len(TREES), "island_qa_pass": qa.get("pass"), "island_qa_errors": qa.get("errors"),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")},
                **media},
               prompt="Build a geometry nodes setup that scatters a forest over this island from a seed, and "
                      "animate its radius so the forest grows out from the middle."))
