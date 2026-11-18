# blender-hair-grooming: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- '<repo>/demos/blender-facial-shapekeys/face.py' '<repo>/demos/blender-facial-shapekeys/scene.py'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o bald.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hair-grooming/scripts/groom.py' -- --surface Head --mask Scalp --length 0.08 --density 5000 --children 1500000 --clump 0.5 --droop 1.0 --noise 0.0003 --radius 0.00013 --melanin 0.55 --redness 0 --roughness 0.32 --seed 3
python <skills_dir>/blender-cloud/scripts/cloud.py look -o groom.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hair-grooming/scripts/groom.py' -- --cards Hair --card-count 900 --card-width 0.02 --atlas-res 1024 --out //textures
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Head Hair_Cards --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Head Hair EyeL EyeR Neck Body --rig studio --backdrop --frames 1 --lens 85 --elevation 4
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-hair-grooming/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine CYCLES --preset preview --samples 48 --res 1280 720 --percent 100
```
