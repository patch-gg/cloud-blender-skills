"""blender-lighting-lookdev on Patch's cloud Blender: turntable.py's three rigs on one marble bust, side by
side and in sync: --rig studio (key, fill, rim area lights), --rig hdri (Blender's bundled sunset) and
--rig both. Each panel is turntable.py's own loop (camera, lights and backdrop orbit once in 120 frames,
frame 121 = frame 1), rendered in Cycles at one exposure.

A scene has one world, so the rigs can't share a frame: each is saved and rendered as its own 428x720
panel, and the three are set side by side here (ffmpeg, like d.media).

Prompt it stands for: "Set up a look-dev turntable for this bust and show it under a studio light rig, an
HDRI and both, side by side."
Run: python demos/blender-lighting-lookdev/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo, _ff  # noqa: E402

HDRI = "/opt/blender/5.2/datafiles/studiolights/world/sunset.exr"  # ships with Blender
RIGS = {  # --rig: (its flags, label, ink for the label)
    "studio": ([], "studio", "dark"),
    "hdri": (["--hdri", HDRI, "--hdri-strength", "2"], "hdri", "light"),
    "both": (["--hdri", HDRI, "--hdri-strength", "2"], "studio + hdri", "dark"),
}
POSTER = 105                                   # a three-quarter view of the face

d = Demo(__file__)
glb = d.asset("polyhaven:marble_bust_01")[0]   # CC0, 17k tris
scene = d.run("scene.py", glb)                 # also sets the 428x720 panel size turntable.py frames for
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Bust", "--profile", "render")
rigs, renders, timing = {}, {}, {}
for rig, (flags, label, ink) in RIGS.items():
    rigs[rig] = d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Bust", "--rig", rig, *flags,
                        "--backdrop", "--frames", "120", "--lens", "85", "--elevation", "10")
    d.run("present.py", label, ink)
    d.expr(f"import bpy; bpy.context.scene.frame_set({POSTER})", quiet=True)
    d.look(f"{rig}.jpg", "--engine", "eevee", "--camera", "LD_Cam")
    d.expr(f"import os; os.makedirs('/work/{rig}', exist_ok=True)", quiet=True)   # d.save won't make the folder
    d.save(f"{rig}/demo.blend")
for rig in RIGS:
    renders[rig] = d.render(f"work/{rig}/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "64",
                            "--res", "428", "720", "--percent", "100", frames="1-120", poster=POSTER)
    timing[rig] = {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser")}

# side by side: d.render pads each 428-wide panel into a 1280x720 clip, so cut the panels back out
out = d.work / "triptych"
out.mkdir(exist_ok=True)
three = "[0][1][2]hstack=inputs=3,crop=1280:720:2:0"
cut = ";".join(f"[{i}]crop=428:720:426:0[p{i}]" for i in range(3)) + ";" + three.replace("[0][1][2]", "[p0][p1][p2]")
_ff(*[a for r in renders.values() for a in ("-i", r["clip"])], "-filter_complex", cut, "-an", "-c:v", "libx264",
    "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out / "clip.mp4")
_ff(*[a for r in renders.values() for a in ("-i", r["poster"])], "-filter_complex", three, out / "poster.png")
media = d.media({"clip": out / "clip.mp4", "poster": out / "poster.png"}, crop="crop=330:330:500:140")  # hdri face
print(d.finish({"tris": scene["tris"], "hdri": Path(HDRI).name,
                "rigs": {k: {"lights": v.get("lights"), "distance": v.get("distance")} for k, v in rigs.items()},
                "frames": 120, "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors", []),
                "render": timing, **media},
               prompt="Set up a look-dev turntable for this bust and show it under a studio light rig, an HDRI "
                      "and both, side by side."))
