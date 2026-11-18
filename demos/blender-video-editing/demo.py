"""blender-video-editing on Patch's cloud Blender: a reel of every other demo, cut in Blender's Video
Sequencer. The clips go up to the session, ffmpeg there takes about 0.8 s from the middle of each as a
folder of frames, and vse_edit.py lays them out with crossfades and a title and renders the H.264 edit.

Prompt it stands for: "Cut all the skill demos into one short reel with crossfades and a title."
Run (after the other demos): python demos/blender-video-editing/demo.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FRAMES = 20                     # 0.83 s at 24 fps per demo
d = Demo(__file__)
order = [c["id"] for c in json.loads((REPO / "block" / "catalog.json").read_text("utf-8"))]
clips = [s for s in order if s != d.skill_name and (REPO / "demos" / s / "media" / "clip.mp4").exists()]
src = d.work / "clips"
src.mkdir(exist_ok=True)
for s in clips:
    shutil.copy2(REPO / "demos" / s / "media" / "clip.mp4", src / f"{s}.mp4")
d.cloud("push", src)
# the middle FRAMES frames of each clip, as a folder of frames per demo (vse_edit takes folders)
cuts = []
for s in clips:
    cmd = (f"mkdir -p cuts/{s} && d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/{s}.mp4) && "
           f"ffmpeg -v error -y -ss $(python3 -c \"print(max(0, $d / 2 - {FRAMES / 48:.3f}))\") -i clips/{s}.mp4 "
           f"-frames:v {FRAMES} -vf scale=1280:720 cuts/{s}/f_%04d.png")
    d.cloud("exec", "--no-pull", cmd, quiet=True)
    cuts.append(f"cuts/{s}/")
r = d.cloud("--timeout", 1800, "run", REPO / "skills" / "blender-video-editing" / "scripts" / "vse_edit.py", "--",
            "--clips", *cuts, "--fps", "24", "--resolution", "1280", "720", "--crossfade", "4",
            "--title", "cloud blender skills", "--title-seconds", "1.6", "--out", "//reel.mp4", "--render",
            "--save", "reel.blend")
if not (d.work / "reel.mp4").exists():
    raise SystemExit(f"no reel: {r}")
# the edit renders at Blender's high H.264 quality; one more pass in the session makes it a web-sized clip
d.cloud("exec", "ffmpeg -v error -y -i reel.mp4 -an -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p "
        "-movflags +faststart reel-web.mp4", quiet=True)
reel = d.work / "reel-web.mp4"
poster = d.work / "poster.png"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "6", "-i", str(reel), "-frames:v", "1", str(poster)], check=True)
media = d.media({"clip": reel, "poster": poster})
print(d.finish({"clips": len(clips), "frames_each": FRAMES, "crossfade_frames": 4, "edit": {k: r.get(k) for k in
                ("frames", "fps", "resolution", "strips", "kb", "seconds") if k in r}, **media},
               prompt="Cut all the skill demos into one short reel with crossfades and a title."))
