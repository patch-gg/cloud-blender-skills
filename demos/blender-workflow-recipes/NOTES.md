# blender-workflow-recipes: notes

Recipe 2 (game prop, high → low baked) run end to end on Patch's cloud Blender 5.2.0. Two skill scripts
had real bugs that broke the recipe; both are fixed in `skills/` with the smallest change that keeps
Blender 5.2 working (5.3 couldn't be run here: the cloud and this machine are both 5.2.0).

## fixed: `export_asset.py` dropped hidden objects from `--objects`

`make_lods.py` leaves LOD1+ hidden, and `export_asset.py` exports with `use_selection=True`. Hidden
objects can't be selected, so recipe 1 step 7 (`export_asset.py --preset <engine> --objects SM_X_LOD0
SM_X_LOD1 ...`) wrote an FBX with only LOD0 while its result listed all four. Re-importing the file
showed one mesh. Fix (blender-export-pipelines/scripts/export_asset.py): unhide hidden members for the
export, then hide them again. The re-imported FBX now has LOD0-3.

## fixed: `build_pbr_material.py` broke the glTF importer in the same scene

To route AO to glTF it creates a "glTF Material Output" node group with only an Occlusion socket.
Blender 5.2's glTF importer reuses any group by that name and expects all of its own sockets, so after
`build_pbr_material.py --textures` (with an AO or ORM map), importing any .glb into that scene failed
with `KeyError: 'Iridescence Factor'`. Fix (blender-pbr-materials/scripts/build_pbr_material.py):
create the group with the glTF add-on's own `create_settings_group` when it can be imported, else the
old minimal group. Checked on 5.2: build a material with AO, then import a .glb into the same scene
(it imports), and export still writes `occlusionTexture`.

## not changed: wear amount with a baked curvature map

Recipe 2 step 6 suggests `smart_material.py --curvature-map ... --wear 0.4 --grime 0.4`. The curvature
map `bake_maps.py` derives from the normal map saturates at 1.0 on bevels a few millimetres wide (here
5 mm bevels, 2048 px, ~2,000 px/m), and the chip noise only moves the wear threshold by about ±0.12. So
any wear of about 0.12 or more wears every edge solid, which reads as a chrome outline rather than
chipped paint. This demo uses `--wear 0.06` (broken chips along the edges). Worth a line in the recipe
or the texturing skill: with a baked curvature map, 0.05-0.1 is "used".

## choices the recipe leaves open

- The low is the blockout itself (recipe 2 step 2: "or manual"). `auto_retopo.py --method planar` keeps
  every bevel segment of a beveled high, so it barely reduces it, and `decimate` gives a triangle soup.
- Paint is `--preset plastic --color ...` (a dielectric with no clear coat), not `paint`: Cycles' roughness
  bake averages over all closures, so the `paint` preset's clear coat would skew the self-baked roughness.
- The QA gate on the LODs catches a real problem: `make_lods.py` decimates LOD3 so far that one handle
  becomes a 6-vertex part floating above the can. `fix_lod.py` deletes the part QA reports (the skill's
  fix for floating debris) and the gate passes again. The clip shows it in pink.

## on the cloud

Everything ran. The high-to-low bake (normal, AO, ID at 2048, 64 samples) takes about 3 minutes on a
small session's 2 CPU cores; the self-bake (8 samples) about a minute. Re-running `bake_maps.py` in the
same live session writes `T_<name>_N.001.png` and so on, because the earlier bake's images keep the
names; a fresh run (this demo) never hits it.
