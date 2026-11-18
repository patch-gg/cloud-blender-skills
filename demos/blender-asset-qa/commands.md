# blender-asset-qa: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:wine_barrel_01 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/wine_barrel_01.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o broken.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Barrel_Body Barrel_Base Barrel_Bung Barrel_Lid Barrel_Lid.001 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/review_shots.py' -- --objects Barrel_Body Barrel_Base Barrel_Bung Barrel_Lid Barrel_Lid.001 --mode random --out //review_broken.png
python <skills_dir>/blender-cloud/scripts/cloud.py run snapshot.py
python <skills_dir>/blender-cloud/scripts/cloud.py run fix.py -- --delete Barrel_Lid.001 --snap Barrel_Bung -0.385 -0.176 0.436 --recalc Barrel_Body --fill-slots Barrel_Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Barrel_Body Barrel_Base Barrel_Bung Barrel_Lid --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/review_shots.py' -- --objects Barrel_Body Barrel_Base Barrel_Bung Barrel_Lid --mode random --out //review_fixed.png
python <skills_dir>/blender-cloud/scripts/cloud.py look -o fixed.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Barrel_Body Barrel_Base Barrel_Bung Barrel_Lid --rig studio --backdrop --frames 120 --lens 50 --elevation 22
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --caught zfighting floating flipped empty_slot --final 'qa pass · 0 errors'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o present.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-asset-qa/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 64 --res 1280 720 --percent 100
```
