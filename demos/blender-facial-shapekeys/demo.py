"""blender-facial-shapekeys on Patch's cloud Blender: a stylized head gets the ARKit 52 and 15 viseme keys, a shape
for each, a left/right split, a mirror, a report and a driver rig, then an EEVEE clip that cycles through
expressions with each key's name.

Prompt it stands for: "Set up ARKit 52 blendshapes and visemes on this head, split the blink and smile into
left and right, mirror the brows, and give me sliders to animate it."
Run: python demos/blender-facial-shapekeys/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

SK = "blender-facial-shapekeys/scripts/shapekeys.py"
BODY = ["Head", "EyeL", "EyeR", "Neck", "Body", "Beanie"]
SHOWN = ["jawOpen", "mouthSmileLeft", "eyeBlinkLeft", "browInnerUp", "viseme_O", "viseme_E", "browDownRight",
         "cheekPuff"]

d = Demo(__file__)
face = d.work / "face.py"                      # the head's generator: scene.py and sculpt.py import it
shutil.copy2(d.root / "face.py", face)
head = d.run("scene.py", face)
d.look("head.jpg")
created = {s: d.skill(SK, "--mesh", "Head", "--create", s)["created"] for s in ("arkit", "visemes")}
sculpt = d.run("sculpt.py", face)
split = [d.skill(SK, "--mesh", "Head", "--split", k, "--falloff", f)["split"]
         for k, f in (("eyeBlink", "0.01"), ("mouthSmile", "0.02"))]
mirror = d.skill(SK, "--mesh", "Head", "--mirror", "browDownLeft")["mirrored"]
d.expr('import bpy\nob = bpy.data.objects["Head"]\n'          # the symmetric sources are split: drop them
       'for n in ("eyeBlink", "mouthSmile"):\n    ob.shape_key_remove(ob.data.shape_keys.key_blocks[n])')
report = d.skill(SK, "--mesh", "Head", "--report")
drivers = d.skill(SK, "--mesh", "Head", "--drivers", "FaceCtrl")["drivers"]
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", *BODY, "--profile", "render")
combo = ('import bpy\nc = bpy.data.objects["FaceCtrl"]\n'      # SKILL.md step 7: check a combination
         'for k in ("jawOpen", "mouthSmileLeft", "mouthSmileRight"):\n    c[k] = {v}\n'
         'bpy.context.view_layer.update()')
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *BODY[:5], "--rig", "studio", "--backdrop",
        "--frames", "1", "--lens", "85", "--elevation", "5")
d.expr(combo.format(v=1.0))
d.look("combo.jpg", "--engine", "eevee", "--camera", "LD_Cam")
d.expr(combo.format(v=0.0))
present = d.run("present.py")
d.look("look.jpg", "--engine", "eevee", "--camera", "LD_Cam")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "48",
             "--res", "1280", "720", "--percent", "100", frames=f"1-{present['frames']}", poster=23)
media = d.media(r, crop="crop=540:540:372:30")      # the picker picture: the face
print(d.finish({
    "head": {k: head[k] for k in ("verts", "faces", "islands")},
    "keys_created": created, "keys_sculpted": sculpt["sculpted"], "split": split, "mirrored": mirror,
    "report": {"keys": report["keys"], "unsculpted": report["unsculpted"],
               "arkit_missing": report.get("arkit_missing"),
               "max_offset_mm": {k: round(report["max_offset"][k] * 1000, 1) for k in SHOWN}},
    "drivers": drivers, "clip_keys": present["keys_shown"],
    "qa_pass": qa.get("pass"), "qa_errors": qa.get("errors"), "qa_warnings": len(qa.get("warnings", [])),
    "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")}, **media},
    prompt="Set up ARKit 52 blendshapes and visemes on this head, split the blink and smile into left and "
           "right, mirror the brows, and give me sliders to animate it."))
