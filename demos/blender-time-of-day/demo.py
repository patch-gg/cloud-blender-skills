"""blender-time-of-day on Patch's cloud Blender: one lighthouse shot taken through dawn, noon, golden hour,
blue hour and a foggy night with scene_mood.py (measured sky and sun or moon, exposure balance, height fog).
Each time is a slice of the same slow camera arc, rendered in Cycles on a GPU; the slices overlap by 8 frames
and crossfade into one 5 s clip.

Prompt it stands for: "Show this lighthouse at dawn, noon, golden hour, blue hour and on a foggy night."
Run: python demos/blender-time-of-day/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

KIT = "kenney:nature-kit/"
ROCKS = ["rock_largeA", "rock_largeC", "rock_largeE", "rock_tallA", "rock_tallB", "rock_tallH"]
# (scene_mood.py flags, label, shot.py flags): dawn's sun rises front right, golden hour's sets front left
TIMES = [(["--time", "sunrise", "--heading", 75], "dawn", ["--lamp", 0]),
         (["--time", "noon", "--heading", 200], "noon", ["--lamp", 0]),
         (["--time", "golden", "--heading", 335], "golden hour", ["--lamp", 0]),
         (["--time", "blue_hour", "--heading", 300, "--elevation", -5], "blue hour",
          ["--lamp", 2, "--exposure", -1.5]),  # exposed for the sky, not the grey card
         (["--time", "night", "--heading", 300, "--fog-visibility", 700, "--fog-height", 15], "night",
          ["--lamp", 1])]
CUTS, FADE = [1, 25, 49, 73, 97, 121], 8  # each time owns 24 frames; neighbours overlap by FADE


def crossfade(clips, out):
    """Chain ffmpeg xfades: clip k starts FADE/2 frames before its cut and fades in over FADE frames."""
    ins, chain, prev = [], [], "[0:v]"
    for c in clips:
        ins += ["-i", str(c)]
    for k in range(1, len(clips)):
        tag = f"[x{k}]" if k < len(clips) - 1 else "[out]"
        chain.append(f"{prev}[{k}:v]xfade=transition=fade:duration={FADE / 24:.4f}:"
                     f"offset={(CUTS[k] - FADE // 2 - 1) / 24:.4f}{tag}")
        prev = tag
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(chain), "-map", "[out]",
                    "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(out)], check=True)


d = Demo(__file__)
lighthouse = d.asset("polyfork:old-lighthouse-48ca6c")[0]
rocks = d.asset(*[f"{KIT}{n}.glb" for n in ROCKS])
scene = d.run("scene.py", "--lighthouse", lighthouse, "--rocks", *rocks)
d.look("scene.jpg", "--camera", "Cam")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Lighthouse", "--profile", "render")
segs, times = [], {}
for i, (flags, label, shot) in enumerate(TIMES):
    mood = d.skill("blender-time-of-day/scripts/scene_mood.py", *flags, "--keep-view")
    lamp = d.run("shot.py", "--label", label, *shot)
    a, b = max(CUTS[i] - FADE // 2, 1), min(CUTS[i + 1] + FADE // 2 - 1, 120)
    name = label.replace(" ", "_")
    d.expr(f"import os; os.makedirs('/work/{name}', exist_ok=True)", quiet=True)
    d.save(f"{name}/demo.blend")
    r = d.render(f"work/{name}/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", 64,
                 "--res", 1280, 720, "--percent", 100, frames=f"{a}-{b}")
    segs.append(r)
    times[label] = {"frames": [a, b], **{k: mood.get(k) for k in ("time", "key", "exposure", "fog")},
                    "exposure_offset": lamp.get("exposure"), "lamp": lamp.get("lamp"),
                    "sec_per_image": d.last_render.get("sec_per_image")}
clip = d.work / "clip.mp4"
crossfade([s["clip"] for s in segs], clip)
media = d.media({"clip": clip, "poster": segs[3]["poster"]}, crop="crop=380:380:575:170")  # blue hour, the tower
print(d.finish({"times": times, "lighthouse_m": scene.get("lighthouse_m"), "lantern": scene.get("lantern"),
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {"engine": "CYCLES", "samples": 64, "device": d.last_render.get("device"),
                           "denoiser": d.last_render.get("denoiser")}, **media},
               prompt="Show this lighthouse at dawn, noon, golden hour, blue hour and on a foggy night."))
