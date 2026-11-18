# blender-core: what ran

Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used
for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.

```bash
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-core/scripts/env_report.py'
python <skills_dir>/blender-cloud/scripts/cloud.py run build.py -- --step body
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 1_body.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run build.py -- --step nose
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 2_nose.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run build.py -- --step fins
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 3_fins.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run build.py -- --step window
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 4_window.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py run build.py -- --step paint
python <skills_dir>/blender-cloud/scripts/cloud.py look -o 5_paint.jpg
python <skills_dir>/blender-cloud/scripts/cloud.py expr 'import bpy
dg = bpy.context.evaluated_depsgraph_get()
obs = [o for o in bpy.data.objects if o.type == "MESH" and "build_step" in o]
tris = 0
for o in obs:
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    o.evaluated_get(dg).to_mesh_clear()
lo = min((o.matrix_world @ v.co).z for o in obs for v in o.data.vertices)
hi = max((o.matrix_world @ v.co).z for o in obs for v in o.data.vertices)
result = {"objects": len(obs), "tris": tris, "height_m": round(hi - lo, 3), "ground_z": round(lo, 4),
          "materials": sorted({s.material.name for o in obs for s in o.material_slots if s.material})}
'
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/qa_check.py' -- --objects Body Nose Nozzle Fin_1 Fin_2 Fin_3 Window_Ring Window_Glass --profile game
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-asset-qa/scripts/review_shots.py' -- --objects Body Nose Nozzle Fin_1 Fin_2 Fin_3 Window_Ring Window_Glass --mode wire --out //review_wire.png
python <skills_dir>/blender-cloud/scripts/cloud.py run '<skills_dir>/blender-lighting-lookdev/scripts/turntable.py' -- --objects Body Nose Nozzle Fin_1 Fin_2 Fin_3 Window_Ring Window_Glass --rig studio --backdrop --frames 120 --lens 50 --elevation 9
python <skills_dir>/blender-cloud/scripts/cloud.py run present.py -- --env 'blender 5.2.0' --final 'qa pass · 9,348 tris'
python <skills_dir>/blender-cloud/scripts/cloud.py look -o present.jpg --engine eevee
python <skills_dir>/blender-cloud/scripts/cloud.py --session $BOX --timeout 1800 run --process --no-pull --blend blender-core/work/demo.blend '<skills_dir>/blender-rendering/scripts/render_batch.py' -- --out '//render/f_####' --format PNG --device GPU --frames 1-120 --engine BLENDER_EEVEE --preset preview --samples 64 --res 1280 720 --percent 100
```
