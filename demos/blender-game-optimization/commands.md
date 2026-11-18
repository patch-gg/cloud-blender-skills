# blender-game-optimization: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:horse_statue_01 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/horse_statue_01.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 01_source.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_Horse --budget mobile
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/make_lods.py' -- --objects SM_Horse --cleanup --rename
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_Horse_LOD0 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_Horse_LOD1 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_Horse_LOD2 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_Horse_LOD3 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run fix_lod.py -- SM_Horse_LOD3
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_Horse_LOD3 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_Horse_LOD0 --budget mobile
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_Horse_LOD1 --budget mobile
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_Horse_LOD2 --budget mobile
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_Horse_LOD3 --budget mobile
python <skills_dir>/blender-cloud/scripts/cloud.py run lineup.py -- SM_Horse mobile 3
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 02_lineup.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects SM_Horse_LOD0 SM_Horse_LOD1 SM_Horse_LOD2 SM_Horse_LOD3 --rig studio --backdrop --frames 96 --lens 50 --elevation 8
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- SM_Horse
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-game-optimization/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
