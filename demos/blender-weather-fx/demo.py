"""blender-weather-fx on Patch's cloud Blender: a night street (blender-time-of-day, moonless, 400 m fog) gets
heavy rain with splashes (precipitation.py), wet surfaces, puddles with ripples and wall streaks
(surface_weather.py: porous and hard materials in two calls) and a three-stroke lightning strike
(lightning.py). A 3.75 s seamless loop, Cycles on a GPU.

Prompt it stands for: "Make this street a rainy night with puddles and a lightning strike."
Run: python demos/blender-weather-fx/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

ASSETS = {"facade": "modular_urban_apartments_facade", "lamp": "street_lamp_01", "hydrant": "fire_hydrant",
          "bin": "metal_trash_can", "bag": "trashbag", "car": "covered_car"}
SW = "blender-weather-fx/scripts/surface_weather.py"

d = Demo(__file__)
got = {Path(p).stem: p for p in d.asset(*[f"polyhaven:{v}" for v in ASSETS.values()])}
scene = d.run("scene.py", *[x for k, v in ASSETS.items() for x in (f"--{k}", got[v])])
d.look("street.jpg", "--camera", "Cam")
mood = d.skill("blender-time-of-day/scripts/scene_mood.py", "--time", "moonless", "--fog-visibility", 400,
               "--city-glow", 0.15)  # less sodium haze: blue-grey fog against the warm lamps
rain = d.skill("blender-weather-fx/scripts/precipitation.py", "--type", "rain", "--intensity", "heavy",
               "--ground", "Road", "Sidewalk", "Kerb", "Car", "--wind", 1.5, 0)
porous = d.skill(SW, "--objects", "Road", "Sidewalk", "Kerb", "Car", "Bag_A", "Bag_B", *scene["facade_porous"],
                 "--wetness", 0.8, "--puddles", 0.45, "--ripples", 1, "--streaks", 0.5, "--porosity", 0.7)
hard = d.skill(SW, "--objects", *scene["lamps"], "Hydrant", "Bin", *scene["facade_hard"],
               "--wetness", 0.8, "--streaks", 0.3, "--porosity", 0.15)
bolt = d.skill("blender-weather-fx/scripts/lightning.py", "--flashes", 1, "--frames", 46, "--strokes", 3,
               "--at", -270, 30)
d.run("present.py", "--exposure", -3, "--lamp-w", 1500, "--glass", 40, "--windows", 18)
d.look("look.jpg", "--camera", "Cam")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Road", "Sidewalk", "Kerb", "--profile", "render")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "CYCLES", "--preset", "preview", "--samples", 48,
             "--res", 1280, 720, "--percent", 100, frames="1-90", poster=46)  # the poster is the strike
media = d.media(r, crop="crop=420:420:230:220")  # the picker picture: the bolt, the car, its reflection
print(d.finish({"rain": {k: rain.get(k) for k in ("count", "box_m", "speed_ms", "streak_m", "life_s", "loop_frames",
                                                    "ground")},
                "wet_porous": {k: porous.get(k) for k in ("materials", "params")},
                "wet_hard": {k: hard.get(k) for k in ("materials", "params")},
                "lightning": {k: bolt.get(k) for k in ("flash_frames", "keys", "peak_strength", "bolt", "sky_flash")},
                "mood": {k: mood.get(k) for k in ("time", "exposure", "fog")}, "exposure_offset": -3,
                "facade_pieces": scene.get("facade_pieces"),
                "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": qa.get("warnings"),
                "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res", "denoiser")},
                **media},
               prompt="Make this street a rainy night with puddles and a lightning strike."))
