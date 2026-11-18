# blender-lighting-lookdev: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:marble_bust_01 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/marble_bust_01.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Bust --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Bust --rig studio --backdrop --frames 120 --lens 85 --elevation 10
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- studio dark
python <skills_dir>/blender-cloud/scripts/cloud.py look -o studio.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Bust --rig hdri --hdri /opt/blender/5.2/datafiles/studiolights/world/sunset.exr --hdri-strength 2 --backdrop --frames 120 --lens 85 --elevation 10
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- hdri light
python <skills_dir>/blender-cloud/scripts/cloud.py look -o hdri.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Bust --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/sunset.exr --hdri-strength 2 --backdrop --frames 120 --lens 85 --elevation 10
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- 'studio + hdri' dark
python <skills_dir>/blender-cloud/scripts/cloud.py look -o both.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-lighting-lookdev/work/studio/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine CYCLES --preset preview --samples 64 --res 428 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-lighting-lookdev/work/hdri/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine CYCLES --preset preview --samples 64 --res 428 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-lighting-lookdev/work/both/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine CYCLES --preset preview --samples 64 --res 428 720 --percent 100
```
