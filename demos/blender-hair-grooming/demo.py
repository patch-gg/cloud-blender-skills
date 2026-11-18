"""blender-hair-grooming on Patch's cloud Blender: the bald head from the shape-key demo gets a groom from Blender's
bundled hair node assets (one groom.py call), then game hair cards and their rendered strand atlas (a second call).
The clip spins both side by side in Cycles.

Prompt it stands for: "Give this character a short brown mop of hair with Blender's hair nodes, then turn it into
game-ready hair cards with a strand texture atlas."
Run: python demos/blender-hair-grooming/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

GROOM = "blender-hair-grooming/scripts/groom.py"
FACE = Path(__file__).resolve().parents[1] / "blender-facial-shapekeys"   # the same character, built by its files

d = Demo(__file__)
head = d.run("scene.py", FACE / "face.py", FACE / "scene.py")
d.look("bald.jpg")
groom = d.skill(GROOM, "--surface", "Head", "--mask", "Scalp", "--length", "0.08", "--density", "5000",
                "--children", "1500000", "--clump", "0.5", "--droop", "1.0", "--noise", "0.0003", "--radius", "0.00013",
                "--melanin", "0.55", "--redness", "0", "--roughness", "0.32", "--seed", "3")
d.look("groom.jpg")
cards = d.skill(GROOM, "--cards", "Hair", "--card-count", "900", "--card-width", "0.02", "--atlas-res", "1024",
                "--out", "//textures")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Head", "Hair_Cards", "--profile", "game")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Head", "Hair", "EyeL", "EyeR", "Neck", "Body",
        "--rig", "studio", "--backdrop", "--frames", "1", "--lens", "85", "--elevation", "4")
present = d.run("present.py")
d.look("look.jpg", "--camera", "LD_Cam")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", "48",
             "--res", "1280", "720", "--percent", "100", frames=f"1-{present['frames']}", poster=1)
web = Path(r["clip"]).with_name("clip_web.mp4")     # hair detail at d.render's crf 20 runs past the ~1.5 MB cap
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(r["clip"]), "-an", "-c:v", "libx264", "-preset", "slow",
                "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(web)], check=True)
media = d.media({"clip": web, "poster": r["poster"]}, crop="crop=420:420:102:96")   # the picker picture: the groom
print(d.finish({
    "groom": {k: groom.get(k) for k in ("curves", "points", "length_mean_m", "root_gap_max_m", "modifiers")},
    "strands_rendered": present["strands_rendered"],
    "cards": {k: cards.get(k) for k in ("card_count", "tris", "material")},
    "atlas": sorted(Path(p).name for p in cards["atlas"].values()),
    "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": len(qa.get("warnings", [])),
    "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser")}, **media},
    prompt="Give this character a short brown mop of hair with Blender's hair nodes, then turn it into game-ready "
           "hair cards with a strand texture atlas."))
