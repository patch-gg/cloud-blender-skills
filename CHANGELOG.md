# Changelog

## cloud-blender-skills [1.0.0] - 2026-11-18
Based on blender-skills 1.3.2. Every skill now runs on Patch's cloud Blender, and each has a demo made there.
- New skill `blender-cloud` and `cloud.py`: live cloud sessions through `pch` (run, expr, exec, look, render,
  fork, push, pull, status, stop), files up and back by themselves, GPU renders, costs.
- `run_in_blender.py --cloud` and `run_tests.py --cloud` (72 pass on the cloud; camera tracking needs a window and
  skips there, as it does with `BAS_NO_WINDOW=1`).
- `render_batch.py`: OpenImageDenoise on the GPU and persistent data for GPU renders (a 720p Cycles frame on an L40S
  went from 5.5 s to 0.4 s); no OptiX denoiser, which fails where the driver's weights file is missing; a retry after a
  failed render no longer renders black; reports the movie file Blender actually writes.
- `export_asset.py`: the `web` preset works on Blender 5.2.0, which can't load its own meshopt encoder on Linux.
- `demos/`: one demo per skill, with the commands that ran (`demos/AUTHORING.md` says how to make one).
- Fixes found by running every skill on the cloud for its demo:
  - `retarget.py`: the auto bone map reads the names Rigify really generates (hips, neck and head from the ends of
    the spine chain; `pelvis.L/.R` helpers skipped). Before, a Rigify game skeleton got no hip travel and its head
    took the chest's rotation.
  - `rigify_build.py`: `--fit` applies the metarig's location too, so the generated rig no longer sits off the mesh.
  - `stress_poses.py`: the spine twist uses Rigify's `spine_fk.002`; `.001` is on the hips side and turned the body.
  - `bind_mesh.py`: vertices bone heat misses (eyelash cards, buttons; under the 2% proxy threshold) take the weights
    of their nearest weighted vertex instead of staying behind in every pose.
  - `garment.py`: region groups such as `--group Torso` no longer get normalised in with the skin weights (bone
    weights summed to about 0.5 and the region used one of the 4 influences).
  - `smart_material.py`, `toon_setup.py`, `surface_weather.py`: a second call no longer unlinks or resets the
    materials an earlier call set up (their shared node groups keep matching sockets).
  - `lightning.py`: the bolt is hidden between flashes; unlit, it rendered black against a lit sky.
  - `scatter.py`: each layer scatters on the mesh only, not on earlier layers' instances, and counts its own.
  - `scene_audit.py`: `--fix scale` flips mirrored meshes back outside out, and the rotation check reads the rotation
    mode an object uses (glTF imports are quaternions).
  - `auto_retopo.py`: collapses the tiny edges that made QuadriFlow cancel without a word, and stops preserving voxel
    steps as sharp edges (minutes of stalling became 1.6 s on a detailed creature).
  - `gn_builder.py`: collection, material and image sockets take a name, as object sockets already did.
  - `export_asset.py`: hidden members (`make_lods.py` hides LOD1+) are exported instead of silently dropped.
  - `build_pbr_material.py`: makes the glTF add-on's own "glTF Material Output" group, so its importer finds every
    socket it expects.
  - `review_shots.py`, `vse_edit.py`: `//` outputs work in an unsaved scene (a cloud session, `blender -b` with no
    file); `vse_edit.py` rendered nothing there.
  - `turntable.py`: re-runs reuse the backdrop material instead of adding `LD_Backdrop.001`, `.002`...
  - `blender-addon-development`: `extension build --output-dir` needs the folder to exist, and `install-file` exits 0
    even when it fails.

## [1.3.2] - 2026-11-17
- `rig_check`: no longer crashes with `slice steps not supported` on skinned meshes with 4000+ vertices (#11, thanks @JairAgu).

## [1.3.1] - 2026-11-14
- Fixes from end-to-end prop and rigged-character runs (#8, thanks @Sebiria): `loop_check` no longer flags smooth reversals as hitches (now reports `kink`/`dip`), glTF export drops other rigs' actions, `rig_check` ignores muted constraints and maps Rigify bones to Unity Humanoid correctly, PBR presets set the viewport color, Git Bash path note.
- Retopo: Quadriflow voxel-remeshes first again (≈4x faster on dense meshes) and retries on the source mesh only if that fails.
- `review_shots`: 1–3 views fit on one row; unused grid cells use the background instead of white.
- `uv_pack`: warns when `seams`/`min_stretch` runs on a mesh with no seams.

## [1.3.0] - 2026-11-13
- Blender 5.3 support (5.2 LTS still works). All 69 tests pass on 5.3.0; CI tests both 5.2.3 and 5.3.0.
- Core: 5.3 migration table (compositor effects stack, glTF compressed-image options, VSE `RIPPLE`, LoopTools ops, Gaussian-splat point clouds, rotation-mode conversion).
- Export: KTX2 textures from Blender via the `web` preset (`--set export_compressed_images_type=KTX2`), plus the new glTF options and collection centers.
- Notes for 5.3 in rendering, time of day (sky table re-checked, sun disc now emits light), geometry nodes, rigging, modeling, retopo, video, animation, PBR, add-ons and pipeline.

## [1.2.0] - 2026-10-30
- New skills: `blender-texturing` (wear/grime/dust, decals), `blender-stylized-npr` (toon shading, outlines), `blender-hair-grooming` (hair, fur, hair cards), `blender-environment-kits` (terrain, scatter, modular kits), `blender-clothing` (garments, no clipping), `blender-video-editing` (VSE edits, camera tracking).
- Animation: mocap retargeting with auto bone maps (`retarget.py`), loop pop/hitch checker (`loop_check.py`).
- Asset QA: catches faces on empty material slots, missing textures, and data maps set to sRGB.
- Sculpting: proportions, hard-surface and bake-source reference.
- Fix: re-running `surface_weather.py` no longer disconnects the weather layer.
- Validator flags script names that don't exist. Verified on Blender 5.2.3.

## [1.1.0] - 2026-10-16
- New `blender-time-of-day`: sky + sun measured from Blender's sky model, night with moon/stars, fog from visibility, moods (cyberpunk, horror, underwater, desert).
- New `blender-weather-fx`: looping rain/snow/dust/embers, wet surfaces, puddles with ripples, snow cover, lightning.
- With vs without skills comparison page, README banner and icon.

## [0.1.0] - 2026-10-14
- 20 Blender 5.2 skills for AI agents (Claude Code, Codex, OpenCode, Gemini CLI, Copilot, Cursor).
- 26 tested scripts (MCP + headless): QA, baking, UV/texel density, retopo, LODs, export presets, Rigify, skinning, animation bake, GN builder, render, lookdev, simulation, batch.
- Installers for every agent, Claude Code plugin/marketplace, validator, headless test suite, CI.
