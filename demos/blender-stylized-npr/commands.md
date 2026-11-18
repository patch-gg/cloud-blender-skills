# blender-stylized-npr: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add kaykit:adventurers/characters/Knight.glb --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/Knight.glb 0
python <skills_dir>/blender-cloud/scripts/cloud.py look -o row.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-stylized-npr/scripts/toon_setup.py' -- --objects Knight_bands --bands 2 --shadow-tint 0.55 0.55 0.55 --outline 0
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-stylized-npr/scripts/toon_setup.py' -- --objects Knight_tint --bands 2 --outline 0
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-stylized-npr/scripts/toon_setup.py' -- --objects Knight_rim --bands 2 --rim 0.5 --outline 0
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-stylized-npr/scripts/toon_setup.py' -- --objects Knight_outline --bands 2 --rim 0.5 --outline 0.01
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Knight_pbr Knight_bands Knight_tint Knight_rim Knight_outline --rig hdri --backdrop --frames 96 --lens 50 --elevation 6
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Knight_outline --profile render --no-modifiers
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-stylized-npr/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_EEVEE --preset preview --samples 32 --res 1280 720 --percent 100
```
