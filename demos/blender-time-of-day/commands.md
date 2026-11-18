# blender-time-of-day: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyfork:old-lighthouse-48ca6c --to assets
pch assets add kenney:nature-kit/rock_largeA.glb kenney:nature-kit/rock_largeC.glb kenney:nature-kit/rock_largeE.glb kenney:nature-kit/rock_tallA.glb kenney:nature-kit/rock_tallB.glb kenney:nature-kit/rock_tallH.glb --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- --lighthouse assets/old-lighthouse-48ca6c.glb --rocks assets/rock_largeA.glb assets/rock_largeC.glb assets/rock_largeE.glb assets/rock_tallA.glb assets/rock_tallB.glb assets/rock_tallH.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o scene.jpg --camera Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Lighthouse --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time sunrise --heading 75 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py run shot.py -- --label dawn --lamp 0
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-time-of-day/work/dawn/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-28 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time noon --heading 200 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py run shot.py -- --label noon --lamp 0
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-time-of-day/work/noon/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 21-52 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time golden --heading 335 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py run shot.py -- --label 'golden hour' --lamp 0
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-time-of-day/work/golden_hour/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 45-76 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time blue_hour --heading 300 --elevation -5 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py run shot.py -- --label 'blue hour' --lamp 2 --exposure -1.5
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-time-of-day/work/blue_hour/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 69-100 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time night --heading 300 --fog-visibility 700 --fog-height 15 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py run shot.py -- --label night --lamp 1
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-time-of-day/work/night/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 93-120 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
```
