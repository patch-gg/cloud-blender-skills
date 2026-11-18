"""blender-clothing on Patch's cloud Blender: a puffer vest made from a character's t-shirt with garment.py
(layered clothing: the shirt is the vest's body), skinned from it, the shirt hidden underneath, and checked for
poke-through in every stress pose; then the vest sweeping on, moving with him, and sweeping off.

Prompt it stands for: "Make a puffer vest for this character over his t-shirt, skinned to his rig, and check it
doesn't clip when he moves."
Run: python demos/blender-clothing/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
The character and his rig come from the blender-character-rigging demo's avatar.py and fit_joints.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

RIGDEMO = Path(__file__).resolve().parents[1] / "blender-character-rigging"
RIG, CLOTH = "blender-character-rigging/scripts/", "blender-clothing/scripts/garment.py"
d = Demo(__file__)
glb = d.asset("mpfb:human-0255")[0]                       # CC0 MakeHuman man in a t-shirt and jeans
avatar = d.run(RIGDEMO / "avatar.py", glb, "--shirt")     # unrigged: Body, and the t-shirt as its own mesh
d.look("mesh.jpg", "--angles", "2")
d.skill(RIG + "rigify_build.py", "--add", "basic_human", "--fit", "Body")
d.run(RIGDEMO / "fit_joints.py", "--metarig", "META_Body", "--mesh", "Body", "--extra", "Shirt")
d.skill(RIG + "rigify_build.py", "--metarig", "META_Body", "--generate")
bind = d.skill(RIG + "bind_mesh.py", "--armature", "RIG_Body", "--meshes", "Body", "Shirt")
d.skill(RIG + "rigify_build.py", "--rig", "RIG_Body", "--game-skeleton")
prep = d.run("vest_prep.py", "--mesh", "Shirt")           # smooth the shirt's creases; the vest's region
vest = d.skill(CLOTH, "--body", "Shirt", "--group", "Torso", "--name", "Vest", "--offset", "0.012",
               "--thickness", "0.01", "--subdiv", "1", "--hide-body")
d.look("vest.jpg", "--angles", "2")
stress = d.skill(RIG + "stress_poses.py", "--armature", "RIG_Body")
checks = {}
for f, pose in ((10, "arms raised 70"), (20, "elbows 130"), (30, "knee 120"), (40, "crouch"), (50, "twist 45")):
    d.expr(f"import bpy; bpy.context.scene.frame_set({f})")
    c = d.skill(CLOTH, "--check", "Vest", "--body", "Shirt")
    checks[pose] = {k: c.get(k) for k in ("covered_verts", "poke_verts", "poke_max_m")}
d.expr("import bpy; bpy.context.scene.frame_set(1)")
d.run("vest_finish.py", "--object", "Vest")                  # smooth its deformation; its material
qa = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Vest", "--profile", "game")
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", "Body", "Shirt", "Vest", "--rig", "studio",
        "--backdrop", "--frames", "120", "--lens", "50", "--elevation", "5")
pres = d.run("present.py")
shown = {}
for f in (62, 80, 96):                                    # the clip's own poses, checked the same way
    d.expr(f"import bpy; bpy.context.scene.frame_set({f})")
    c = d.skill(CLOTH, "--check", "Vest", "--body", "Shirt")
    shown[f] = c.get("poke_verts")
d.expr("import bpy; bpy.context.scene.frame_set(62)")
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "64",
             "--res", "1280", "720", "--percent", "100", frames="1-120", poster=62)
media = d.media(r, crop="crop=360:360:460:70")            # the picker picture: him in the vest
print(d.finish({
    "body": {"meshes": avatar["objects"], "shirt_verts": avatar["verts"].get("Shirt")},
    "shirt_prep": {k: prep.get(k) for k in ("crumpled_verts", "relaxed_verts", "body_panels", "region_verts")},
    "skin": {m: {k: v for k, v in s.items() if k in ("method", "unweighted_verts", "max_influences")}
             for m, s in bind["meshes"].items()},
    "garment": {k: vest.get(k) for k in ("garment", "region_verts", "offset_m", "thickness_m", "vertex_groups",
                                         "armature", "hidden_verts", "covered_verts", "poke_verts", "poke_max_m")},
    "poke_check_in_stress_poses": checks, "poke_check_in_clip_poses": shown,
    "stress_missing_roles": stress.get("missing_roles"),
    "qa": {"pass": qa.get("pass"), "errors": qa.get("errors"),
           "vest_tris": ((qa.get("objects") or {}).get("Vest") or {}).get("tris")},
    "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
    prompt="Make a puffer vest for this character over his t-shirt, skinned to his rig, and check it doesn't clip "
           "when he moves."))
