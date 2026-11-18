# blender-geometry-nodes: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
pch assets add kenney:nature-kit/tree_pineDefaultA.glb kenney:nature-kit/tree_pineDefaultB.glb kenney:nature-kit/tree_cone.glb kenney:nature-kit/tree_detailed.glb kenney:nature-kit/plant_bushDetailed.glb --to assets
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- assets/tree_pineDefaultA.glb assets/tree_pineDefaultB.glb assets/tree_cone.glb assets/tree_detailed.glb assets/plant_bushDetailed.glb
python <skills_dir>/blender-cloud/scripts/cloud.py look -o island.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-geometry-nodes/scripts/gn_builder.py' -- --describe GeometryNodeDistributePointsOnFaces GeometryNodeInstanceOnPoints GeometryNodeCollectionInfo GeometryNodeRaycast FunctionNodeRandomValue
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-geometry-nodes/scripts/gn_builder.py' -- --spec forest.json --apply Island --set Radius=5.1 Trees=Trees Ring=M_Front Seed=3
python <skills_dir>/blender-cloud/scripts/cloud.py look -o forest.jpg --angles 2
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Island --no-modifiers --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Island --rig studio --backdrop --frames 120 --lens 50 --elevation 30
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --radius 5.1
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-geometry-nodes/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset final --samples 64 --res 1280 720 --percent 100
```
