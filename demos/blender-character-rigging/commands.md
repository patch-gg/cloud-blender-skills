# blender-character-rigging: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add mpfb:human-0255 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run avatar.py -- assets/human-0255.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o mesh.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --add basic_human --fit Body
python <skills_dir>/blender-cloud/scripts/cloud.py run fit_joints.py -- --metarig META_Body --mesh Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --metarig META_Body --generate
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/bind_mesh.py' -- --armature RIG_Body --meshes Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --rig RIG_Body --game-skeleton
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rig_check.py' -- --armature GAME_RIG_Body --profile unity
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/stress_poses.py' -- --armature RIG_Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Body --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Body --rig studio --backdrop --frames 120 --lens 50 --elevation 6
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-character-rigging/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
