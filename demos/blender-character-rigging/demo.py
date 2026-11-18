"""blender-character-rigging on Patch's cloud Blender: an unrigged character from Patch's library through the
skill's whole chain (Rigify metarig, joints placed on the mesh, control rig, skin weights, a game skeleton,
rig_check, stress poses), then the stress poses rendered beside the game skeleton.

Prompt it stands for: "Rig this character with Rigify, skin it, give me a Unity-ready game skeleton and
stress-test the deformation."
Run: python demos/blender-character-rigging/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
avatar.py and fit_joints.py here are shared with the blender-animation and blender-clothing demos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

RIG = "blender-character-rigging/scripts/"
d = Demo(__file__)
glb = d.asset("mpfb:human-0255")[0]                       # CC0 MakeHuman man, exported with his own skeleton
avatar = d.run("avatar.py", glb)                          # that skeleton dropped: an unrigged, welded mesh
d.look("mesh.jpg", "--angles", "2")                       # the unrigged input
meta = d.skill(RIG + "rigify_build.py", "--add", "basic_human", "--fit", "Body")
joints = d.run("fit_joints.py", "--metarig", "META_Body", "--mesh", "Body")
gen = d.skill(RIG + "rigify_build.py", "--metarig", "META_Body", "--generate")
bind = d.skill(RIG + "bind_mesh.py", "--armature", "RIG_Body", "--meshes", "Body")
game = d.skill(RIG + "rigify_build.py", "--rig", "RIG_Body", "--game-skeleton")
check = d.skill(RIG + "rig_check.py", "--armature", "GAME_RIG_Body", "--profile", "unity")
stress = d.skill(RIG + "stress_poses.py", "--armature", "RIG_Body")
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Body", "--profile", "game")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Body", "--rig", "studio", "--backdrop",
        "--frames", "120", "--lens", "50", "--elevation", "6")
pres = d.run("present.py")
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=21)
media = d.media(r, crop="crop=300:300:740:28")            # the picker picture: his head and chest
skin = bind["meshes"]["Body"]
print(d.finish({
    "character": {"verts": avatar["verts"]["Body"], "tris": avatar["tris"]["Body"], "height_m": avatar["height_m"]},
    "metarig_fit_scale": meta.get("fit_scale"), "joints_placed": joints.get("bones_placed"),
    "control_rig": {"bones": gen.get("bones"), "deform_bones": gen.get("deform_bones")},
    "skin": {"method": skin["method"], "groups": skin["groups"], "max_influences": skin["max_influences"],
             "unweighted_verts": skin["unweighted_verts"], "filled_from_nearest": skin.get("filled_from_nearest")},
    "game_skeleton": game.get("game_skeleton"),
    "rig_check": {"pass": check.get("pass"), "errors": check.get("errors"), "warnings": check.get("warnings"),
                  "unity_humanoid_unmapped": [k for k, v in (check.get("profile") or {}).get("humanoid_map", {}).items()
                                              if v is None]},
    "stress_poses": {"frames": stress.get("frames"), "missing_roles": stress.get("missing_roles"),
                     "shown_at": pres.get("poses_at"), "crouch_drop_m": pres.get("crouch_drop_m")},
    "qa": {"pass": qa.get("pass"), "errors": qa.get("errors")},
    "render": {k: d.last_render.get(k) for k in ("engine", "device", "sec_per_image", "res")}, **media},
    prompt="Rig this character with Rigify, skin it, give me a Unity-ready game skeleton and stress-test the "
           "deformation."))
