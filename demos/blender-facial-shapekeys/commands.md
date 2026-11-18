# blender-facial-shapekeys: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run scene.py -- face.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o head.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --create arkit
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --create visemes
python <skills_dir>/blender-cloud/scripts/cloud.py run sculpt.py -- face.py
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --split eyeBlink --falloff 0.01
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --split mouthSmile --falloff 0.02
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --mirror browDownLeft
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy
ob = bpy.data.objects["Head"]
for n in ("eyeBlink", "mouthSmile"):
    ob.shape_key_remove(ob.data.shape_keys.key_blocks[n])'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --report
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-facial-shapekeys/scripts/shapekeys.py' -- --mesh Head --drivers FaceCtrl
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Head EyeL EyeR Neck Body Beanie --profile render
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Head EyeL EyeR Neck Body --rig studio --backdrop --frames 1 --lens 85 --elevation 5
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy
c = bpy.data.objects["FaceCtrl"]
for k in ("jawOpen", "mouthSmileLeft", "mouthSmileRight"):
    c[k] = 1.0
bpy.context.view_layer.update()'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o combo.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy
c = bpy.data.objects["FaceCtrl"]
for k in ("jawOpen", "mouthSmileLeft", "mouthSmileRight"):
    c[k] = 0.0
bpy.context.view_layer.update()'
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py
python <skills_dir>/blender-cloud/scripts/cloud.py look -o look.jpg --engine eevee --camera LD_Cam
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-facial-shapekeys/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset final --samples 48 --res 1280 720 --percent 100
```
