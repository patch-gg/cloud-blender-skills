# blender-texturing: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:metal_jerrycan --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/metal_jerrycan.glb decals/diesel.png
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_Paint --preset plastic --color 0.5 0.045 0.03 --objects JerryCan
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-texturing/scripts/smart_material.py' -- --objects JerryCan --wear 0.5 --grime 0.85 --dust 0.6 --edge-width 0.01 --scale 0.03 --grime-color 0.09 0.07 0.05
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-texturing/scripts/decal.py' -- --target JerryCan --at 0 -0.1 0.2 --image decals/diesel.png --size 0.17
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects JerryCan --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/studio.exr --hdri-strength 0.6 --backdrop --frames 96 --lens 85 --elevation 15
python <skills_dir>/blender-cloud/scripts/cloud.py look -o layers.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects JerryCan DC_diesel --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-texturing/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine CYCLES --preset preview --samples 64 --res 1280 720 --percent 100
```
