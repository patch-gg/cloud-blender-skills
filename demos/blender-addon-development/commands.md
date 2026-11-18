# blender-addon-development: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py push gear_maker
python <skills_dir>/blender-cloud/scripts/cloud.py exec 'blender --factory-startup --command extension validate gear_maker'
python <skills_dir>/blender-cloud/scripts/cloud.py exec 'mkdir -p dist && blender --factory-startup --command extension build --source-dir gear_maker --output-dir dist'
python <skills_dir>/blender-cloud/scripts/cloud.py exec 'blender --command extension install-file -r user_default -e dist/gear_maker-1.0.0.zip'
python <skills_dir>/blender-cloud/scripts/cloud.py run make_gears.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o gears.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Gear_12 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Gear_36 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Gear_20 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Gear_12 Gear_36 Gear_20 --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/studio.exr --hdri-strength 0.8 --backdrop --frames 120 --lens 50 --elevation 52
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o present.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-addon-development/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 64 --res 1280 720 --percent 100
```
