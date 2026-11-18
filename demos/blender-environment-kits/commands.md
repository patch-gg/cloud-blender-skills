# blender-environment-kits: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add kenney:nature-kit/tree_pineTallA_detailed.glb kenney:nature-kit/tree_pineTallB_detailed.glb kenney:nature-kit/tree_pineTallC_detailed.glb kenney:nature-kit/tree_pineTallD_detailed.glb kenney:nature-kit/tree_pineRoundA.glb kenney:nature-kit/tree_pineRoundC.glb --to assets
pch assets add kenney:nature-kit/rock_largeA.glb kenney:nature-kit/rock_largeB.glb kenney:nature-kit/rock_largeD.glb kenney:nature-kit/rock_largeF.glb kenney:nature-kit/rock_tallA.glb kenney:nature-kit/rock_tallB.glb --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- --pines assets/tree_pineTallA_detailed.glb assets/tree_pineTallB_detailed.glb assets/tree_pineTallC_detailed.glb assets/tree_pineTallD_detailed.glb assets/tree_pineRoundA.glb assets/tree_pineRoundC.glb --rocks assets/rock_largeA.glb assets/rock_largeB.glb assets/rock_largeD.glb assets/rock_largeF.glb assets/rock_tallA.glb assets/rock_tallB.glb
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-environment-kits/scripts/terrain.py' -- --size 600 --res 513 --type ridged --scale 400 --octaves 4 --height 120 --erosion 40 --material --seed 3
python <skills_dir>/blender-cloud/scripts/cloud.py look -o terrain.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-environment-kits/scripts/terrain.py' -- --name Far --size 2400 --res 257 --type ridged --scale 900 --octaves 5 --height 300 --erosion 8 --flatten 0 0 440 --material --seed 9
python <skills_dir>/blender-cloud/scripts/cloud.py run reveal.py -- --frames 24 90 --x -340 340 --width 80 --axis 1 -0.075
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-environment-kits/scripts/scatter.py' -- --target Terrain --collection Pines --density 0.045 --min-distance 4.5 --max-slope 30 --height-min 16 --height-max 85 --scale 0.7 1.3 --mask reveal --name ENV_Pines
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-environment-kits/scripts/scatter.py' -- --target Terrain --collection Rocks --density 0.005 --min-distance 10 --max-slope 70 --align 0.8 --scale 0.6 1.6 --mask reveal_rock --seed 2 --name ENV_Rocks
python <skills_dir>/blender-cloud/scripts/cloud.py look -o scatter.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --cam-a -20 -340 140 --cam-b -5 -280 132 --look-a 10 60 40 --look-b 15 100 38 --lens 32 --frames 1 120 --switch 57 --sink Far --labels 'terrain · ridged · 600 m' 'scatter · 3,713 pines · 375 rocks'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-time-of-day/scripts/scene_mood.py' -- --time golden --elevation 14 --heading 70 --fog-visibility 25000 --fog-color 1 0.86 0.68 --fog-anisotropy 0.4 --keep-view
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --camera Cam --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Terrain --profile game --no-modifiers
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-environment-kits/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 32 --res 1280 720 --percent 100
```
