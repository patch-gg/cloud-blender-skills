# blender-rendering: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:potted_plant_04 polyhaven:antique_ceramic_vase_01 polyhaven:brass_goblets polyhaven:wine_bottles_01 polyhaven:brass_vase_03 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/potted_plant_04.glb assets/antique_ceramic_vase_01.glb assets/brass_goblets.glb assets/wine_bottles_01.glb assets/brass_vase_03.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects potted_plant_04_dirt potted_plant_04_ground potted_plant_04_plant potted_plant_04_pot antique_ceramic_vase_01 brass_goblet_01 brass_goblet_02 brass_goblet_03 wine_bottles_01_alsace wine_bottles_01_burgundy brass_vase_03 --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/interior.exr --hdri-strength 0.3 --backdrop --frames 96 --lens 50 --elevation 8
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects potted_plant_04_dirt potted_plant_04_ground potted_plant_04_plant potted_plant_04_pot --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects antique_ceramic_vase_01 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects brass_goblet_01 brass_goblet_02 brass_goblet_03 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects wine_bottles_01_alsace --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects wine_bottles_01_burgundy --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects brass_vase_03 --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-rendering/work/workbench/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_WORKBENCH --view Standard --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-rendering/work/eevee/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_EEVEE --preset final --samples 32 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-rendering/work/cycles/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
python <skills_dir>/blender-cloud/scripts/cloud.py run --process compose.py -- --split 0.3533 0.6817 --frames 96 --out compose/demo.blend
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-rendering/work/compose/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_WORKBENCH --res 1280 720 --percent 100
```
