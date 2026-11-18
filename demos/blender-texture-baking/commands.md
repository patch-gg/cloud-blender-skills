# blender-texture-baking: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Crate_high --preset render --cutters Crate_cut --width 0.004 --apply
python <skills_dir>/blender-cloud/scripts/cloud.py look -o high.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Crate_high Crate_bolts --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Crate_low --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-texture-baking/scripts/bake_maps.py' -- --low Crate_low --high Crate_high Crate_bolts --maps normal ao curvature basecolor roughness metallic --res 1024 --samples 32 --margin-px 8 --pack-orm --name Crate
python <skills_dir>/blender-cloud/scripts/cloud.py run lineup.py -- 13204
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Crate_baked --textures textures --objects Crate_baked
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Crate_high Crate_bolts Crate_low Crate_baked --rig studio --backdrop --frames 96 --lens 50 --elevation 13
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Crate_baked --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-texture-baking/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
```
