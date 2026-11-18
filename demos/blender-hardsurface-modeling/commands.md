# blender-hardsurface-modeling: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o blockout.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/uv_pack.py' -- --objects Shell Caps Core CoreRings Hubs Bolts Rails Cradle Skid --method smart
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Shell --preset midpoly --width 0.008 --cutters Cut_Windows
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Caps --preset midpoly --width 0.008 --cutters Cut_CapRecess Cut_CapGrooves
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Cradle --preset midpoly --width 0.008 --cutters Cut_Saddle Cut_CradleHoles
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Skid --preset midpoly --width 0.008 --cutters Cut_SkidSlots
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Core CoreRings Hubs Bolts Rails --preset midpoly --width 0.008
python <skills_dir>/blender-cloud/scripts/cloud.py look -o after.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Shell Caps Core CoreRings Hubs Bolts Rails Cradle Skid --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Shell Caps Core CoreRings Hubs Bolts Rails Cradle Skid --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/studio.exr --hdri-strength 0.6 --backdrop --frames 120 --lens 50 --elevation 14
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --blockout-tris 2744 --final-tris 18152
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-hardsurface-modeling/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --samples 64 --res 1280 720 --percent 100
```
