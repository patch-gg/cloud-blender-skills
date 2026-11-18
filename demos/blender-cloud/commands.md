# blender-cloud: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:fire_hydrant --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/fire_hydrant.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Ground --preset concrete --objects Ground
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Hydrant --rig studio --frames 120 --lens 50 --elevation 10
python <skills_dir>/blender-cloud/scripts/cloud.py look -o base.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py fork --count 5
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-stylized-npr/scripts/toon_setup.py' -- --objects Hydrant Ground --bands 3 --outline 0.006 --rim 0.45
python <skills_dir>/blender-cloud/scripts/cloud.py run studio.py
python <skills_dir>/blender-cloud/scripts/cloud.py run outdoor.py
python <skills_dir>/blender-cloud/scripts/cloud.py run outdoor.py
python <skills_dir>/blender-cloud/scripts/cloud.py run outdoor.py
python <skills_dir>/blender-cloud/scripts/cloud.py run outdoor.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time night --city-glow 0.6 --stars 1
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Hydrant --rig studio --backdrop --frames 120 --lens 50 --elevation 10
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time afternoon --overcast 0.5 --heading 140
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time golden --heading 200
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time blue_hour --overcast 0.6
python <skills_dir>/blender-cloud/scripts/cloud.py run expose.py -- -0.7
python <skills_dir>/blender-cloud/scripts/cloud.py run streetlamp.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/surface_weather.py' -- --objects Hydrant Ground --snow 0.85 --snow-depth 0.04
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/surface_weather.py' -- --objects Hydrant Ground --wetness 0.9 --puddles 0.5 --ripples 1
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/precipitation.py' -- --type snow --intensity moderate --ground Ground Hydrant --loop-frames 120 --distance 10
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-weather-fx/scripts/precipitation.py' -- --type rain --intensity heavy --ground Ground Hydrant --loop-frames 120 --distance 10
python <skills_dir>/blender-cloud/scripts/cloud.py run expose.py -- -1.0
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-toon/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-night/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-studio/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-golden-hour/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-rain/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-cloud/work/v-snow/scene.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --res 640 540 --percent 100
```
