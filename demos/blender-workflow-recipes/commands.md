# blender-workflow-recipes: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 01_blockout.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run high.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Body_high --preset render --cutters Cut_XA Cut_XB --width 0.005
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Cap_high --preset render --cutters Cut_Grip --width 0.0012
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-hardsurface-modeling/scripts/apply_stack.py' -- --objects Flange_high Handles_high Spout_high --preset render --width 0.003
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 02_high.jpg --angles 4
python <skills_dir>/blender-cloud/scripts/cloud.py run low.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/uv_pack.py' -- --objects SM_JerryCan --method seams --seams-from-sharp 60 --margin-px 16 --res 2048 --shape CONCAVE
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-retopology-uv/scripts/texel_density.py' -- --objects SM_JerryCan --res 2048
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Body_high Flange_high Handles_high Spout_high Cap_high --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run --timeout 1800 '<skills_dir>/blender-texture-baking/scripts/bake_maps.py' -- --low SM_JerryCan --high Body_high Flange_high Handles_high Spout_high Cap_high --maps normal ao curvature id --pack-orm --res 2048 --margin-px 16
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_JerryCan --preset plastic --color 0.6 0.07 0.05 --textures //textures --objects SM_JerryCan
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-texturing/scripts/smart_material.py' -- --objects SM_JerryCan --curvature-map //textures/T_JerryCan_CURV.png --ao-map //textures/T_JerryCan_AO.png --wear 0.06 --grime 0.5 --dust 0.12 --scale 0.08
python <skills_dir>/blender-cloud/scripts/cloud.py run --timeout 1800 '<skills_dir>/blender-texture-baking/scripts/bake_maps.py' -- --low SM_JerryCan --maps basecolor roughness metallic --samples 8 --out //textures/game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-pbr-materials/scripts/build_pbr_material.py' -- --name M_JerryCan --textures //textures/game/T_JerryCan_BC.png //textures/T_JerryCan_N.png //textures/game/T_JerryCan_R.png //textures/game/T_JerryCan_M.png //textures/T_JerryCan_AO.png --objects SM_JerryCan
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects SM_JerryCan --rig both --hdri /opt/blender/5.2/datafiles/studiolights/world/studio.exr --hdri-strength 0.5 --backdrop --frames 184 --lens 85 --elevation 16
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 03_material.jpg --camera LD_Cam --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/mesh_stats.py' -- --objects SM_JerryCan --budget web
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-game-optimization/scripts/make_lods.py' -- --objects SM_JerryCan --rename
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan_LOD0 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan_LOD1 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan_LOD2 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan_LOD3 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run fix_lod.py -- SM_JerryCan_LOD3 -0.088 0.0 0.491
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_JerryCan_LOD3 --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset web --objects SM_JerryCan_LOD0 --out //export/SM_JerryCan.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset unreal --objects SM_JerryCan_LOD0 SM_JerryCan_LOD1 SM_JerryCan_LOD2 SM_JerryCan_LOD3 --out //export/SM_JerryCan.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py run --process verify_export.py -- /work/export/SM_JerryCan.glb /work/export/SM_JerryCan.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py run import_glb.py -- /work/export/SM_JerryCan.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- present.json
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 04_present_wear.jpg --camera LD_Cam --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-workflow-recipes/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-184 --engine CYCLES --preset preview --samples 48 --res 1280 720 --percent 100
```
