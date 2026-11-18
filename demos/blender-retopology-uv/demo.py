"""blender-retopology-uv on Patch's cloud Blender: a 441,766-triangle AI-generated creature from Patch's
asset library, retopologised with auto_retopo.py (QuadriFlow) to a 5,000-triangle budget, unwrapped and
packed with uv_pack.py, then texel_density.py measures the islands and evens them out to 1,024 px/m.

Prompt it stands for: "Retopologise this 440k-triangle AI mesh into a clean quad mesh under 5k triangles,
unwrap it and even out the texel density."
Run: python demos/blender-retopology-uv/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

S = "blender-retopology-uv/scripts/"
RES = 2048
DENSITY = 1024     # px/m: the measured spread is over the SKILL's 1.3, so set one density
ASSET = "scenario:asset_3itGMDfk3jK3eUXPc7rZhr1G"   # "Peach fox creature", Tripo image-to-3D, CC-BY-4.0

d = Demo(__file__)
glb = d.asset(ASSET)[0]
src = d.run("scene.py", glb)
d.look("source.jpg", "--angles", "2")
ret = d.skill(S + "auto_retopo.py", "--objects", "Fox", "--method", "quadriflow", "--tris", "5000")
low = ret["objects"]["Fox"]
d.look("retopo.jpg", "--angles", "2")
uvr = d.skill(S + "uv_pack.py", "--objects", low["low"], "--method", "smart", "--res", RES, "--margin-px", "8")
td = d.skill(S + "texel_density.py", "--objects", low["low"], "--res", RES)["objects"][low["low"]]
ts = d.skill(S + "texel_density.py", "--objects", low["low"], "--res", RES, "--set", DENSITY,
             "--margin-px", "8")["objects"][low["low"]]
after = d.skill(S + "texel_density.py", "--objects", low["low"], "--res", RES)["objects"][low["low"]]
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", low["low"], "--profile", "game")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Fox", low["low"], "--rig", "studio",
        "--backdrop", "--frames", "120", "--lens", "50", "--elevation", "8")
d.run("present.py", "--density", after["px_per_m"], "--res", RES, "--labels",
      "ai mesh · {:,} tris".format(src["tris"]), "quadriflow · {:,} tris".format(low["tris_after"]),
      "uvs · {:,} px/m".format(round(after["px_per_m"])))
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=31)
media = d.media(r, crop="crop=300:300:490:150")    # the picker picture: the quad retopo's head
print(d.finish({"source_tris": src["tris"], "retopo": {"method": ret["method"], **low},
                "reduction": round(src["tris"] / max(low["tris_after"], 1), 1),
                "uv": {"method": uvr["method"], "margin_fraction": uvr["margin_fraction"], "res": RES},
                "texel_density": {"measured": td, "set": DENSITY, "fits_0_1": ts.get("after", {}).get("fits_0_1"),
                                  "after": after},
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"),
                "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")},
                **media},
               prompt="Retopologise this 440k-triangle AI mesh into a clean quad mesh under 5k triangles, "
                      "unwrap it and even out the texel density."))
