# notes

## fixed: a second smart_material.py call broke the first one's materials

`skills/blender-texturing/scripts/smart_material.py`, `build_group()`. Every call cleared and recreated the
shared `TX_Layers` group's sockets. That dropped the links and reset the amounts in every material an
earlier call had layered, so layering a second prop broke the first. Found while making the
blender-stylized-npr demo, where `toon_setup.py` builds its group the same way. The fix is the same in
both: keep the sockets when they already match, and still rebuild the group's inside. Checked on Blender
5.2: after `--objects C --wear 0.5`, then `--objects D`, C keeps its links and wear 0.5.

## worth knowing

- `smart_material.py` wraps Base Color, Roughness and Metallic, not Coat. On a clear-coated base, such as
  `build_pbr_material.py --preset paint`, the chips, grime and dust all stay under a glossy coat. This demo
  uses a base without a coat: the `plastic` preset with the paint colour, which is what enamel is.
- `qa_check.py` fails this asset on z-fighting: 449 triangle pairs where two plates of the cap clamp sit
  0.9 mm apart in Poly Haven's mesh. The decal itself has no z-fighting (it sits 1.2 to 3.1 mm off the surface).
