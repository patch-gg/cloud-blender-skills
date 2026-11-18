# blender-simulation: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:wooden_crate_01 polyhaven:wooden_crate_02 polyhaven:wooden_military_crate --to assets
pch assets add polyhaven:Barrel_01 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- --crates assets/wooden_crate_01.glb assets/wooden_crate_02.glb assets/wooden_military_crate.glb --barrel assets/barrel_01.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o start.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-simulation/scripts/sim_setup.py' -- --rigid --active Crate_00 Crate_01 Crate_02 Crate_03 Barrel_04 Crate_05 Crate_06 Crate_07 Crate_08 Barrel_09 Crate_10 --passive Floor Wall_Back Wall_Side --density 500 --frames 1 120 --bake --to-keys
python <skills_dir>/blender-cloud/scripts/cloud.py look -o rigid.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run proxies.py -- --bodies Crate_00 Crate_01 Crate_02 Crate_03 Barrel_04 Crate_05 Crate_06 Crate_07 Crate_08 Barrel_09 Crate_10
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-simulation/scripts/sim_setup.py' -- --cloth Tarp --preset denim --colliders Proxy_Crate_00 Proxy_Crate_01 Proxy_Crate_02 Proxy_Crate_03 Proxy_Barrel_04 Proxy_Crate_05 Proxy_Crate_06 Proxy_Crate_07 Proxy_Crate_08 Proxy_Barrel_09 Proxy_Crate_10 Floor Wall_Back Wall_Side --frames 48 120 --bake
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --switch 48 --labels 'rigid bodies · 9 crates, 2 barrels' 'cloth · denim · 4,225 verts'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time afternoon --heading 150
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --camera Cam
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Tarp --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-simulation/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 32 --res 1280 720 --percent 100
```
