"""blender-animation on Patch's cloud Blender: a mocap-style walk (Patch's CC0 anymove woman) retargeted with
retarget.py onto a different body (the 1.97 m man the rigging demo rigs), its loop checked with loop_check.py,
and the clip baked clean onto his game skeleton with bake_action.py; then both walking side by side.

Prompt it stands for: "Put this mocap walk on my character (he's much taller), make sure it loops, and bake it
onto his game skeleton for export."
Run: python demos/blender-animation/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
The target and his rig come from the blender-character-rigging demo's avatar.py and fit_joints.py.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

RIGDEMO = Path(__file__).resolve().parents[1] / "blender-character-rigging"
RIG, ANIM = "blender-character-rigging/scripts/", "blender-animation/scripts/"
LIMBS = ["upper_arm.L", "upper_arm.R", "forearm.L", "forearm.R", "hand.L", "hand.R", "thigh.L", "thigh.R",
         "shin.L", "shin.R"]
KEYS = ("import bpy; a = bpy.data.actions['GAME_RIG_Body|Walk']; "
        "result = {'keys': sum(len(fc.keyframe_points) for l in a.layers for s in l.strips for cb in s.channelbags "
        "for fc in cb.fcurves)}")
d = Demo(__file__)
man = d.asset("mpfb:human-0255")[0]                       # the target: CC0 MakeHuman man, 1.97 m
woman = d.asset("anymove:woman")[0]                       # the source: CC0 anymove woman, mocap-style clips
d.run(RIGDEMO / "avatar.py", man)
d.skill(RIG + "rigify_build.py", "--add", "basic_human", "--fit", "Body")
d.run(RIGDEMO / "fit_joints.py", "--metarig", "META_Body", "--mesh", "Body")
d.skill(RIG + "rigify_build.py", "--metarig", "META_Body", "--generate")
d.skill(RIG + "bind_mesh.py", "--armature", "RIG_Body", "--meshes", "Body")
d.skill(RIG + "rigify_build.py", "--rig", "RIG_Body", "--game-skeleton")
src = d.run("source.py", woman, "--clip", "Walk", "--x", "-1.3")
# the game skeleton follows the control rig through constraints; mute them so it plays its own keys
d.expr("import bpy; [setattr(c, 'mute', True) for pb in bpy.data.objects['GAME_RIG_Body'].pose.bones "
       "for c in pb.constraints]")
shown = d.skill(ANIM + "retarget.py", "--source", "Mocap", "--target", "GAME_RIG_Body", "--show-map")
(d.work / "map.json").write_text(json.dumps(shown["map"], indent=1), "utf-8")
rest = d.run("match_rest.py", "--source", "Mocap", "--target", "GAME_RIG_Body", "--map", d.work / "map.json",
             "--bones", *LIMBS)
d.look("rest.jpg", "--angles", "2")
rt = d.skill(ANIM + "retarget.py", "--source", "Mocap", "--target", "GAME_RIG_Body", "--name", "Walk")
loop_src = d.skill(ANIM + "loop_check.py", "--object", "Mocap", "--action", "Walk")
loop = d.skill(ANIM + "loop_check.py", "--object", "GAME_RIG_Body", "--action", "GAME_RIG_Body|Walk", "--fix")
keys_before = d.expr(KEYS)
bake = d.skill(ANIM + "bake_action.py", "--source", "GAME_RIG_Body", "--target", "GAME_RIG_Body",
               "--actions", "GAME_RIG_Body|Walk")
keys_after = d.expr(KEYS)
loop_after = d.skill(ANIM + "loop_check.py", "--object", "GAME_RIG_Body", "--action", "GAME_RIG_Body|Walk")
clips = d.skill(ANIM + "bake_action.py", "--list")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Body", "MocapBody", "--rig", "studio",
        "--backdrop", "--frames", "106", "--lens", "50", "--elevation", "6")
cycle = int(round(rt["frames"][1] - rt["frames"][0]))
pres = d.run("present.py", "--source", "Mocap", "--target", "GAME_RIG_Body", "--cycle", cycle)
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames=f"1-{2 * cycle}", poster=14)
media = d.media(r, crop="crop=520:520:400:85")            # the picker picture: the two of them
walk = next((c for c in clips.get("actions", []) if c["name"] == "GAME_RIG_Body|Walk"), {})
print(d.finish({
    "source": {"rig": src.get("armature"), "clip": src.get("clip"), "frames": src.get("frames"),
               "height_m": pres.get("heights_m", [None])[0], "bones": src.get("bones")},
    "target": {"rig": "GAME_RIG_Body", "height_m": pres.get("heights_m", [None, None])[1]},
    "rest_matched_deg": rest.get("turned_deg"),
    "retarget": {k: rt.get(k) for k in ("mapped", "hips", "hips_scale", "unmapped_key_parts", "max_error_deg",
                                        "frames")},
    "loop_check": {"source": {"loops": loop_src.get("loops"), "pops": len(loop_src.get("pops") or []),
                              "hitches": [h["bone"] for h in loop_src.get("hitches") or []]},
                   "target": {"loops": loop.get("loops"), "pops": len(loop.get("pops") or []),
                              "fixed_curves": loop.get("fixed_curves", 0),
                              "hitches": [h["bone"] for h in loop.get("hitches") or []]},
                   "target_after_bake": {"loops": loop_after.get("loops"), "pops": len(loop_after.get("pops") or [])}},
    "bake": {"baked": bake.get("baked"), "keys_before": keys_before.get("keys"), "keys_after": keys_after.get("keys"),
             "clip": {k: walk.get(k) for k in ("name", "range", "fcurves", "fake_user")}},
    "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
    prompt="Put this mocap walk on my character (he's much taller), make sure it loops, and bake it onto his game "
           "skeleton for export."))
