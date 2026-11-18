# blender-scene-setup: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:potted_plant_02 polyhaven:wine_barrel_01 polyhaven:metal_tool_chest polyhaven:side_table_tall_01 --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/potted_plant_02.glb assets/wine_barrel_01.glb assets/metal_tool_chest.glb assets/side_table_tall_01.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o before.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-scene-setup/scripts/scene_audit.py'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-scene-setup/scripts/scene_audit.py' -- --fix purge scale
python <skills_dir>/blender-cloud/scripts/cloud.py run tidy.py -- --names Mesh.002=PottedPlant Cylinder.001=WineBarrel Cube.007=ToolChest Cube.003=SideTable
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-scene-setup/scripts/scene_audit.py'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o after.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_PottedPlant --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_WineBarrel --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_ToolChest --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_SideTable --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects SM_PottedPlant SM_WineBarrel SM_ToolChest SM_SideTable --rig studio --backdrop --frames 120 --lens 50 --elevation 8
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- labels.json
python <skills_dir>/blender-cloud/scripts/cloud.py look -o present.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-scene-setup/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 64 --res 1280 720 --percent 100
```
