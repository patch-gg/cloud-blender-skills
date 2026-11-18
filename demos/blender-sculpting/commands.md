# blender-sculpting: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o base.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run snap.py -- --name S0_base --slot 0 --of 5
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-sculpting/scripts/sculpt_ops.py' -- --objects Moai --ops remesh=0.02
python <skills_dir>/blender-cloud/scripts/cloud.py run snap.py -- --name S1_remesh --slot 1 --of 5
python <skills_dir>/blender-cloud/scripts/cloud.py look -o pass1_remesh.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-sculpting/scripts/sculpt_ops.py' -- --objects Moai --ops smooth=30 apply
python <skills_dir>/blender-cloud/scripts/cloud.py run snap.py -- --name S2_smooth --slot 2 --of 5
python <skills_dir>/blender-cloud/scripts/cloud.py look -o pass2_smooth.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-sculpting/scripts/sculpt_ops.py' -- --objects Moai --ops remesh=0.006 inflate=0.02 apply
python <skills_dir>/blender-cloud/scripts/cloud.py run snap.py -- --name S3_inflate --slot 3 --of 5
python <skills_dir>/blender-cloud/scripts/cloud.py look -o pass3_inflate.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-sculpting/scripts/sculpt_ops.py' -- --objects Moai --ops detail=0.018,0.11 detail=0.005,0.025 smooth=1 apply
python <skills_dir>/blender-cloud/scripts/cloud.py look -o pass4_detail.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Moai --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects S0_base S1_remesh S2_smooth S3_inflate Moai --rig studio --backdrop --frames 120 --lens 50 --elevation 9
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --labels base remesh smooth inflate detail
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-sculpting/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
