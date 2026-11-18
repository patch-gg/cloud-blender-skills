"""blender-cloud on Patch's cloud Blender: one scene, forked into six sessions, each running a
different skill at the same time, then rendered on a GPU and tiled.

Prompt it stands for: "Show me that hydrant six ways at once: studio, toon, snow, rain, golden hour
and night."
Run: python demos/blender-cloud/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import shutil
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import SKILLS, Demo  # noqa: E402

KIT = Path.home() / "patch/brand/handoff/out/04 Type/Funnel Sans/FunnelSans[wght].ttf"  # labels only
LOOKS = {  # fork -> the skill calls that make its look
    "studio": [("run", "studio.py"), ("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Hydrant",
               "--rig", "studio", "--backdrop", "--frames", "120", "--lens", "50", "--elevation", "10")],
    "toon": [("blender-stylized-npr/scripts/toon_setup.py", "--objects", "Hydrant", "Ground", "--bands", "3",
              "--outline", "0.006", "--rim", "0.45")],
    "snow": [("run", "outdoor.py"), ("blender-time-of-day/scripts/scene_mood.py", "--time", "noon", "--overcast", "0.85"),
             ("blender-weather-fx/scripts/surface_weather.py", "--objects", "Hydrant", "Ground", "--snow", "0.85",
              "--snow-depth", "0.04"),
             ("blender-weather-fx/scripts/precipitation.py", "--type", "snow", "--intensity", "moderate",
              "--ground", "Ground", "Hydrant", "--loop-frames", "120", "--distance", "10")],
    "rain": [("run", "outdoor.py"), ("blender-time-of-day/scripts/scene_mood.py", "--time", "blue_hour", "--overcast", "0.6"),
             ("blender-weather-fx/scripts/surface_weather.py", "--objects", "Hydrant", "Ground", "--wetness", "0.9",
              "--puddles", "0.5", "--ripples", "1"),
             ("blender-weather-fx/scripts/precipitation.py", "--type", "rain", "--intensity", "heavy",
              "--ground", "Ground", "Hydrant", "--loop-frames", "120", "--distance", "10")],
    "golden hour": [("run", "outdoor.py"), ("blender-time-of-day/scripts/scene_mood.py", "--time", "golden", "--heading", "200")],
    "night": [("run", "outdoor.py"), ("blender-time-of-day/scripts/scene_mood.py", "--time", "night", "--city-glow", "0.6",
               "--stars", "1")],
}

d = Demo(__file__)
glb = d.asset("polyhaven:fire_hydrant")[0]
base = d.run("scene.py", glb)
d.skill("blender-pbr-materials/scripts/build_pbr_material.py", "--name", "M_Ground", "--preset", "concrete",
        "--objects", "Ground")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Hydrant", "--rig", "studio", "--frames", "120",
        "--lens", "50", "--elevation", "10")
d.look("base.jpg")
forks = d.cloud("fork", "--count", len(LOOKS) - 1)["forks"]
sessions = dict(zip(LOOKS, [d.session] + forks))
results, errors = {}, []


def make(look, sid):
    try:
        for step in LOOKS[look]:
            if step[0] == "run":
                shutil.copy2(d.root / step[1], d.work / step[1])
                d.cloud("run", d.work / step[1], session=sid)
            else:
                d.cloud("run", SKILLS / step[0], "--", *step[1:], session=sid)
        name = look.replace(" ", "-")
        d.cloud("look", "-o", d.work / f"look-{name}.jpg", session=sid, quiet=True)
        code = ("import bpy, os\nos.makedirs('/work/v-" + name + "', exist_ok=True)\n"
                "try:\n    bpy.ops.file.pack_all()\nexcept RuntimeError:\n    pass\n"
                f"bpy.ops.wm.save_as_mainfile(filepath='/work/v-{name}/scene.blend', copy=True)")
        d.cloud("expr", code, session=sid, quiet=True)
        d.cloud("pull", f"v-{name}/scene.blend", session=sid, quiet=True)
        # a folder per fork, so the six renders in the GPU session don't share a render/ folder
        results[look] = d.render(d.work / f"v-{name}" / "scene.blend", "--engine", "BLENDER_EEVEE",
                                 "--res", "640", "540", "--percent", "100", frames="1-120")
    except Exception as e:  # report every fork, then fail
        errors.append(f"{look}: {e}")


threads = [threading.Thread(target=make, args=(k, s)) for k, s in sessions.items()]
for t in threads:
    t.start()
for t in threads:
    t.join()
for sid in forks:
    d.cloud("stop", session=sid, quiet=True, check=False)
if errors:
    raise SystemExit("\n".join(errors))

# tile the six clips: 3 x 2 cells of 426 x 360 with a 2 px dark gap, a small label in each
grid = d.work / "grid.mp4"
font = d.work / "label.ttf"
shutil.copy2(KIT, font)
inputs, chains = [], []
for i, look in enumerate(LOOKS):
    inputs += ["-i", str(results[look]["clip"])]
    chains.append(f"[{i}:v]crop=853:720:213:0,scale=424:358:flags=lanczos,pad=426:360:1:1:color=0x0b0b0c,"
                  f"drawtext=fontfile='{font}':text='{look}':fontsize=17:fontcolor=white@0.92:x=14:y=h-30:"
                  f"box=1:boxcolor=0x0b0b0c@0.55:boxborderw=6[c{i}]")
layout = "0_0|426_0|852_0|0_360|426_360|852_360"
fc = ";".join(chains) + ";" + "".join(f"[c{i}]" for i in range(6)) + f"xstack=inputs=6:layout={layout},pad=1280:720:1:0:color=0x0b0b0c[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-an", "-c:v", "libx264",
                "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(grid)], check=True)
poster = d.work / "grid-poster.png"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.5", "-i", str(grid), "-frames:v", "1", str(poster)], check=True)
media = d.media({"clip": grid, "poster": poster}, crop="crop=360:360:20:0")
print(d.finish({"sessions_at_once": len(sessions), "looks": list(LOOKS), "hydrant": base,
                "skills": sorted({s[0].split("/")[0] for v in LOOKS.values() for s in v if s[0] != "run"}), **media},
               prompt="Show me that hydrant six ways at once: studio, toon, snow, rain, golden hour and night."))
