# blender-export-pipelines: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add polyhaven:rubber_duck_toy --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/rubber_duck_toy.glb SM_RubberDuck
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects SM_RubberDuck --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset godot --objects SM_RubberDuck --out export/SM_RubberDuck_godot.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset web --objects SM_RubberDuck --out export/SM_RubberDuck_web.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset usd --objects SM_RubberDuck --out export/SM_RubberDuck.usdz
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset unity --objects SM_RubberDuck --out export/SM_RubberDuck_unity.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset unreal --objects SM_RubberDuck --out export/SM_RubberDuck_unreal.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-export-pipelines/scripts/export_asset.py' -- --preset roblox --objects SM_RubberDuck --out export/SM_RubberDuck_roblox.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py run roundtrip.py -- SM_RubberDuck godot=export/SM_RubberDuck_godot.glb web=export/SM_RubberDuck_web.glb usd=export/SM_RubberDuck.usdz unity=export/SM_RubberDuck_unity.fbx unreal=export/SM_RubberDuck_unreal.fbx roblox=export/SM_RubberDuck_roblox.fbx
python <skills_dir>/blender-cloud/scripts/cloud.py look -o roundtrip.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects SM_RubberDuck.001 SM_RubberDuck.006 SM_RubberDuck.004 SM_RubberDuck.005 SM_RubberDuck.003 SM_RubberDuck.002 Label_godot Label_web Label_usd Label_unity Label_unreal Label_roblox --rig studio --backdrop --frames 96 --lens 50 --elevation 13
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee --max-size 1280
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-export-pipelines/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-96 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
