# blender-animation: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add mpfb:human-0255 --to assets
pch assets add anymove:woman --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run avatar.py -- assets/human-0255.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --add basic_human --fit Body
python <skills_dir>/blender-cloud/scripts/cloud.py run fit_joints.py -- --metarig META_Body --mesh Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --metarig META_Body --generate
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/bind_mesh.py' -- --armature RIG_Body --meshes Body
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-character-rigging/scripts/rigify_build.py' -- --rig RIG_Body --game-skeleton
python <skills_dir>/blender-cloud/scripts/cloud.py run source.py -- assets/woman.glb --clip Walk --x -1.3
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy; [setattr(c, '"'"'mute'"'"', True) for pb in bpy.data.objects['"'"'GAME_RIG_Body'"'"'].pose.bones for c in pb.constraints]'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/retarget.py' -- --source Mocap --target GAME_RIG_Body --show-map
python <skills_dir>/blender-cloud/scripts/cloud.py run match_rest.py -- --source Mocap --target GAME_RIG_Body --map map.json --bones upper_arm.L upper_arm.R forearm.L forearm.R hand.L hand.R thigh.L thigh.R shin.L shin.R
python <skills_dir>/blender-cloud/scripts/cloud.py look -o rest.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/retarget.py' -- --source Mocap --target GAME_RIG_Body --name Walk
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/loop_check.py' -- --object Mocap --action Walk
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/loop_check.py' -- --object GAME_RIG_Body --action 'GAME_RIG_Body|Walk' --fix
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy; a = bpy.data.actions['"'"'GAME_RIG_Body|Walk'"'"']; result = {'"'"'keys'"'"': sum(len(fc.keyframe_points) for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves)}'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/bake_action.py' -- --source GAME_RIG_Body --target GAME_RIG_Body --actions 'GAME_RIG_Body|Walk'
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy; a = bpy.data.actions['"'"'GAME_RIG_Body|Walk'"'"']; result = {'"'"'keys'"'"': sum(len(fc.keyframe_points) for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves)}'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/loop_check.py' -- --object GAME_RIG_Body --action 'GAME_RIG_Body|Walk'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-animation/scripts/bake_action.py' -- --list
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Body MocapBody --rig studio --backdrop --frames 106 --lens 50 --elevation 6
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --source Mocap --target GAME_RIG_Body --cycle 53
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-animation/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-106 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
