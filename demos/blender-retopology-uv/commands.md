# blender-retopology-uv: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add scenario:asset_3itGMDfk3jK3eUXPc7rZhr1G --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/peach_fox_creature.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o source.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/auto_retopo.py' -- --objects Fox --method quadriflow --tris 5000
python <skills_dir>/blender-cloud/scripts/cloud.py look -o retopo.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/uv_pack.py' -- --objects Fox_low --method smart --res 2048 --margin-px 8
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/texel_density.py' -- --objects Fox_low --res 2048
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/texel_density.py' -- --objects Fox_low --res 2048 --set 1024 --margin-px 8
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/texel_density.py' -- --objects Fox_low --res 2048
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Fox_low --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Fox Fox_low --rig studio --backdrop --frames 120 --lens 50 --elevation 8
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --density 1024 --res 2048 --labels 'ai mesh · 441,766 tris' 'quadriflow · 3,976 tris' 'uvs · 1,024 px/m'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-retopology-uv/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
