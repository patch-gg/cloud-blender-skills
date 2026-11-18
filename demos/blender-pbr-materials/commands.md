# blender-pbr-materials: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Gold --preset gold --objects Ball_gold
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Copper --preset copper --objects Ball_copper
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Chrome --preset chrome --objects Ball_chrome
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Paint --preset paint --objects Ball_paint
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Ceramic --preset ceramic --objects Ball_ceramic
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Rubber --preset rubber --objects Ball_rubber
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Ball_gold Ball_copper Ball_chrome Ball_paint Ball_ceramic Ball_rubber --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/courtyard.exr --hdri-strength 0.6 --backdrop --frames 96 --lens 50 --elevation 7
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_gold --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_copper --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_chrome --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_paint --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_ceramic --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Ball_rubber --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-pbr-materials/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
```
