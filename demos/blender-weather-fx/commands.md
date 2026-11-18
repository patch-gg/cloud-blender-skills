# blender-weather-fx: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:modular_urban_apartments_facade polyhaven:street_lamp_01 polyhaven:fire_hydrant polyhaven:metal_trash_can polyhaven:trashbag polyhaven:covered_car --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- --facade assets/modular_urban_apartments_facade.glb --lamp assets/street_lamp_01.glb --hydrant assets/fire_hydrant.glb --bin assets/metal_trash_can.glb --bag assets/trashbag.glb --car assets/covered_car.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o street.jpg --camera Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time moonless --fog-visibility 400 --city-glow 0.15
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/precipitation.py' -- --type rain --intensity heavy --ground Road Sidewalk Kerb Car --wind 1.5 0
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/surface_weather.py' -- --objects Road Sidewalk Kerb Car Bag_A Bag_B Facade_0_crown_standard_standard_01 Facade_0_dado_door_centered_small_02 Facade_0_wall_door_centered_small_02 --wetness 0.8 --puddles 0.45 --ripples 1 --streaks 0.5 --porosity 0.7
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/surface_weather.py' -- --objects Lamp_0 Lamp_1 Lamp_2 Lamp_3 Hydrant Bin Facade_0_door_centered_small_02 Facade_0_window_centered_double_01 --wetness 0.8 --streaks 0.3 --porosity 0.15
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/lightning.py' -- --flashes 1 --frames 46 --strokes 3 --at -270 30
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --exposure -3 --lamp-w 1500 --glass 40 --windows 18
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --camera Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Road Sidewalk Kerb --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-weather-fx/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-90 --engine CYCLES --preset preview --samples 48 --res 1280 720 --percent 100
```
