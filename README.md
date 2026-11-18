---
kind: tool
---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/header-evening.png">
  <img alt="patch. cloud blender skills. 29 blender skills for your agent, in your blender or on patch." src="docs/readme/header-day.png" width="800">
</picture>

<br><br>

<a href="https://patch.gg/rehan/cloud-blender-skills"><img alt="One fire hydrant six ways at once, each look made by a different skill in its own cloud Blender session: studio, toon, snow, rain, golden hour and night." src="docs/readme/hero.webp" width="800"></a>

**[open the demos](https://patch.gg/rehan/cloud-blender-skills)** · [run it in the cloud](#run-it-in-the-cloud) ·
[install](#install) · [the demos](#the-demos) · [what's new here](#whats-new-here) · [the skills](#the-skills)

29 Blender skills for coding agents (Claude Code, Codex, Gemini CLI, Copilot, Cursor, OpenCode): modeling, UVs,
materials, baking, rigging, animation, clothing, hair, environments, weather, export, rendering and QA. Your agent runs
them in your own Blender, or on [Patch's cloud Blender](https://patch.gg/blender) with nothing to install: add `--cloud`.

The skills are [EL4CTEO's blender-skills](https://github.com/EL4CTEO/blender-skills) (MIT). This repo adds one skill,
`blender-cloud`, and the fixes we found by running every skill on the cloud. Each clip below was made by an agent
following one skill, start to finish on Patch's cloud Blender, and each folder in [demos/](demos) has the commands it ran.

## run it in the cloud.

```sh
npm i -g @patchgg/cli
pch login
python skills/blender-core/scripts/run_in_blender.py --cloud skills/blender-core/scripts/env_report.py
```

With `pch` installed, every call the skills make runs there by default, so your agent needs no Blender of its
own; `--local` keeps a call on your machine. Under it is
[`cloud.py`](skills/blender-cloud/scripts/cloud.py), which your agent learns from
[`blender-cloud`](skills/blender-cloud/SKILL.md):

- **One live scene.** The first call starts a session, a Blender 5.2 on Patch's machines, and later calls reuse it, so
  the scene builds up the way it does in an MCP session. Watch it at [patch.gg/blender](https://patch.gg/blender).
- **Files go both ways by themselves.** Paths in the arguments go up to the session, and whatever a call writes comes
  back to the same place in your folder: exports, renders, review sheets, saved .blend files.
- **GPU renders.** `cloud.py render scene.blend --frames 1-120 --video mp4` renders on an L40S and downloads the frames.
- **Side by side.** `cloud.py fork --count 5` copies a session, scene and all, so five takes run at once. The clip at
  the top is one hydrant in six sessions, six skills at the same time.
- **Look as you go.** `cloud.py look -o look.jpg --angles 4` is a preview of the live scene in about a second.
- **What it costs.** A small session is about 50 credits ($0.50) an hour and pauses itself when idle; an L40S render
  about 250 credits an hour. `cloud.py status` shows the session and your balance.

The test suite runs there too: `python tools/run_tests.py --cloud` passes 72 of 73 on the cloud in about a minute. The
one it skips tracks a camera, which needs a Blender window.

## install.

**Claude Code** (plugin):
```
/plugin marketplace add patch-gg/cloud-blender-skills
/plugin install cloud-blender-skills@cloud-blender-skills
```

**Any agent** (clone, then run the installer):
```bash
git clone https://github.com/patch-gg/cloud-blender-skills
./cloud-blender-skills/install/install.sh          # macOS / Linux
.\cloud-blender-skills\install\install.ps1         # Windows
```
It installs into `~/.claude/skills` and `~/.agents/skills` (read by Codex, OpenCode, Gemini CLI, Copilot and Cursor).
Options: `--agent claude|codex|opencode|gemini|copilot|cursor|all`, `--project DIR`, `--uninstall`.

**Then set up the cloud** (your agent can do this; the skills tell it how): `npm i -g @patchgg/cli`, then `pch login`.
From then on the skills run on Patch's cloud Blender. Without it they use Blender 5.2 LTS or newer on your machine.
Optional: a Blender MCP server, so agents can work in your open Blender.

## the demos.

Every clip is one skill, run by an agent on Patch's cloud Blender from an empty session: the scene built in bpy or
taken from [Patch's asset library](https://patch.gg/create/toolbox/assets), the skill's own scripts doing the work,
its QA gate, and a final render on a cloud GPU. Click one for the commands that made it.

<!-- demos -->
<table>
<tr><td width="33%" valign="top"><a href="demos/blender-workflow-recipes/commands.md"><img src="demos/blender-workflow-recipes/media/poster.webp" width="100%" alt="Recipes: a whole game prop, start to finish"></a><br><b>blender-workflow-recipes</b><br><sub>a whole game prop, start to finish</sub></td><td width="33%" valign="top"><a href="demos/blender-core/commands.md"><img src="demos/blender-core/media/poster.webp" width="100%" alt="Core: run bpy, look, check: the loop every skill uses"></a><br><b>blender-core</b><br><sub>run bpy, look, check: the loop every skill uses</sub></td><td width="33%" valign="top"><a href="demos/blender-cloud/commands.md"><img src="demos/blender-cloud/media/poster.webp" width="100%" alt="Cloud: the same skills on Patch's cloud Blender"></a><br><b>blender-cloud</b><br><sub>the same skills on Patch's cloud Blender</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-scene-setup/commands.md"><img src="demos/blender-scene-setup/media/poster.webp" width="100%" alt="Scene setup: names, units and collections, cleaned up"></a><br><b>blender-scene-setup</b><br><sub>names, units and collections, cleaned up</sub></td><td width="33%" valign="top"><a href="demos/blender-asset-qa/commands.md"><img src="demos/blender-asset-qa/media/poster.webp" width="100%" alt="Asset QA: catches z-fighting, floating parts and flipped normals"></a><br><b>blender-asset-qa</b><br><sub>catches z-fighting, floating parts and flipped normals</sub></td><td width="33%" valign="top"><a href="demos/blender-hardsurface-modeling/commands.md"><img src="demos/blender-hardsurface-modeling/media/poster.webp" width="100%" alt="Hard surface: bevels, booleans and weighted normals"></a><br><b>blender-hardsurface-modeling</b><br><sub>bevels, booleans and weighted normals</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-sculpting/commands.md"><img src="demos/blender-sculpting/media/poster.webp" width="100%" alt="Sculpting: procedural sculpt passes, no brush needed"></a><br><b>blender-sculpting</b><br><sub>procedural sculpt passes, no brush needed</sub></td><td width="33%" valign="top"><a href="demos/blender-retopology-uv/commands.md"><img src="demos/blender-retopology-uv/media/poster.webp" width="100%" alt="Retopo & UVs: a dense mesh made light, unwrapped and packed"></a><br><b>blender-retopology-uv</b><br><sub>a dense mesh made light, unwrapped and packed</sub></td><td width="33%" valign="top"><a href="demos/blender-geometry-nodes/commands.md"><img src="demos/blender-geometry-nodes/media/poster.webp" width="100%" alt="Geometry nodes: node trees built from a little JSON"></a><br><b>blender-geometry-nodes</b><br><sub>node trees built from a little JSON</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-pbr-materials/commands.md"><img src="demos/blender-pbr-materials/media/poster.webp" width="100%" alt="PBR materials: measured materials, one call each"></a><br><b>blender-pbr-materials</b><br><sub>measured materials, one call each</sub></td><td width="33%" valign="top"><a href="demos/blender-texturing/commands.md"><img src="demos/blender-texturing/media/poster.webp" width="100%" alt="Texturing: edge wear, grime, dust and decals"></a><br><b>blender-texturing</b><br><sub>edge wear, grime, dust and decals</sub></td><td width="33%" valign="top"><a href="demos/blender-texture-baking/commands.md"><img src="demos/blender-texture-baking/media/poster.webp" width="100%" alt="Baking: high-poly detail baked onto a low-poly mesh"></a><br><b>blender-texture-baking</b><br><sub>high-poly detail baked onto a low-poly mesh</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-stylized-npr/commands.md"><img src="demos/blender-stylized-npr/media/poster.webp" width="100%" alt="Toon & NPR: cel shading and outlines"></a><br><b>blender-stylized-npr</b><br><sub>cel shading and outlines</sub></td><td width="33%" valign="top"><a href="demos/blender-character-rigging/commands.md"><img src="demos/blender-character-rigging/media/poster.webp" width="100%" alt="Rigging: Rigify rig, skinning and stress poses"></a><br><b>blender-character-rigging</b><br><sub>Rigify rig, skinning and stress poses</sub></td><td width="33%" valign="top"><a href="demos/blender-facial-shapekeys/commands.md"><img src="demos/blender-facial-shapekeys/media/poster.webp" width="100%" alt="Face shapes: ARKit blendshapes and visemes"></a><br><b>blender-facial-shapekeys</b><br><sub>ARKit blendshapes and visemes</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-animation/commands.md"><img src="demos/blender-animation/media/poster.webp" width="100%" alt="Animation: retargeting, loops and root motion"></a><br><b>blender-animation</b><br><sub>retargeting, loops and root motion</sub></td><td width="33%" valign="top"><a href="demos/blender-clothing/commands.md"><img src="demos/blender-clothing/media/poster.webp" width="100%" alt="Clothing: a garment that follows the body"></a><br><b>blender-clothing</b><br><sub>a garment that follows the body</sub></td><td width="33%" valign="top"><a href="demos/blender-hair-grooming/commands.md"><img src="demos/blender-hair-grooming/media/poster.webp" width="100%" alt="Hair: hair curves and game hair cards"></a><br><b>blender-hair-grooming</b><br><sub>hair curves and game hair cards</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-environment-kits/commands.md"><img src="demos/blender-environment-kits/media/poster.webp" width="100%" alt="Environments: terrain and scatter by slope and height"></a><br><b>blender-environment-kits</b><br><sub>terrain and scatter by slope and height</sub></td><td width="33%" valign="top"><a href="demos/blender-time-of-day/commands.md"><img src="demos/blender-time-of-day/media/poster.webp" width="100%" alt="Time of day: one scene from dawn to night"></a><br><b>blender-time-of-day</b><br><sub>one scene from dawn to night</sub></td><td width="33%" valign="top"><a href="demos/blender-weather-fx/commands.md"><img src="demos/blender-weather-fx/media/poster.webp" width="100%" alt="Weather: rain, wet streets and lightning"></a><br><b>blender-weather-fx</b><br><sub>rain, wet streets and lightning</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-simulation/commands.md"><img src="demos/blender-simulation/media/poster.webp" width="100%" alt="Simulation: rigid bodies and cloth, baked headless"></a><br><b>blender-simulation</b><br><sub>rigid bodies and cloth, baked headless</sub></td><td width="33%" valign="top"><a href="demos/blender-lighting-lookdev/commands.md"><img src="demos/blender-lighting-lookdev/media/poster.webp" width="100%" alt="Look-dev: studio light rigs and turntables"></a><br><b>blender-lighting-lookdev</b><br><sub>studio light rigs and turntables</sub></td><td width="33%" valign="top"><a href="demos/blender-game-optimization/commands.md"><img src="demos/blender-game-optimization/media/poster.webp" width="100%" alt="Optimization: LODs and budgets per platform"></a><br><b>blender-game-optimization</b><br><sub>LODs and budgets per platform</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-export-pipelines/commands.md"><img src="demos/blender-export-pipelines/media/poster.webp" width="100%" alt="Export: engine presets, checked after export"></a><br><b>blender-export-pipelines</b><br><sub>engine presets, checked after export</sub></td><td width="33%" valign="top"><a href="demos/blender-rendering/commands.md"><img src="demos/blender-rendering/media/poster.webp" width="100%" alt="Rendering: Cycles, EEVEE and Workbench, batch rendered"></a><br><b>blender-rendering</b><br><sub>Cycles, EEVEE and Workbench, batch rendered</sub></td><td width="33%" valign="top"><a href="demos/blender-video-editing/commands.md"><img src="demos/blender-video-editing/media/poster.webp" width="100%" alt="Video editing: a reel cut in Blender's sequencer"></a><br><b>blender-video-editing</b><br><sub>a reel cut in Blender's sequencer</sub></td></tr>
<tr><td width="33%" valign="top"><a href="demos/blender-pipeline-automation/commands.md"><img src="demos/blender-pipeline-automation/media/poster.webp" width="100%" alt="Pipelines: batch conversion over many files"></a><br><b>blender-pipeline-automation</b><br><sub>batch conversion over many files</sub></td><td width="33%" valign="top"><a href="demos/blender-addon-development/commands.md"><img src="demos/blender-addon-development/media/poster.webp" width="100%" alt="Add-ons: an extension built, installed and run"></a><br><b>blender-addon-development</b><br><sub>an extension built, installed and run</sub></td></tr>
</table>
<!-- /demos -->

Make your own with [demos/AUTHORING.md](demos/AUTHORING.md); `python demos/<skill>/demo.py` runs one again.

## what's new here.

- **[`blender-cloud`](skills/blender-cloud/SKILL.md)**, a 29th skill: live cloud sessions through `pch`, files up and
  back, previews, GPU renders, forks and costs. `run_in_blender.py --cloud` and `run_tests.py --cloud` use it.
- **Faster GPU renders.** `render_batch.py` now denoises with OpenImageDenoise on the GPU and keeps data between
  frames: a 720p Cycles frame on an L40S went from 5.5 s to 0.4 s. It no longer picks the OptiX denoiser, which fails
  wherever the driver's weights file is missing (cloud GPUs, containers, WSL), and it reports the movie file Blender
  actually writes.
- **glTF compression on Blender 5.2.0.** 5.2.0 can't load its own meshopt encoder on Linux, so the `web` export preset
  failed there. `export_asset.py` now loads it first.
- More fixes from running every skill on the cloud are listed in [CHANGELOG.md](CHANGELOG.md).

## the skills.

| Skill | What it does |
|---|---|
| `blender-core` | Start here: runs code, routes tasks, 5.x API rules |
| `blender-cloud` | Patch's cloud Blender: sessions, files, previews, GPU renders, forks |
| `blender-scene-setup` | Units, naming, collections, asset libraries |
| `blender-hardsurface-modeling` | Bevels, booleans, weighted normals |
| `blender-sculpting` | Organic sculpting workflow |
| `blender-retopology-uv` | Retopology, UVs, texel density |
| `blender-pbr-materials` | Correct PBR materials from textures |
| `blender-texturing` | Edge wear, grime, dust, decals, trim sheets |
| `blender-texture-baking` | Normal, AO and curvature maps, ORM |
| `blender-geometry-nodes` | Procedural modeling from simple JSON |
| `blender-character-rigging` | Rigify, skinning, game skeletons |
| `blender-facial-shapekeys` | ARKit 52 blendshapes, visemes |
| `blender-animation` | Actions, mocap retargeting, loop checks, root motion |
| `blender-clothing` | Clothes that follow the body without clipping |
| `blender-hair-grooming` | Hair, fur and game hair cards |
| `blender-game-optimization` | Budgets, LODs, draw calls |
| `blender-export-pipelines` | Roblox, Unity, Unreal, Godot, web, USD |
| `blender-rendering` | Cycles and EEVEE, batch rendering |
| `blender-lighting-lookdev` | Studio lighting, HDRI, turntables |
| `blender-stylized-npr` | Toon/anime shading and outlines |
| `blender-environment-kits` | Terrain, forests, modular level kits |
| `blender-video-editing` | Edit videos, track cameras |
| `blender-simulation` | Rigid bodies, cloth, fluids |
| `blender-time-of-day` | Golden hour, night, fog and mood lighting |
| `blender-weather-fx` | Rain, snow, wet streets, puddles, lightning |
| `blender-addon-development` | Blender extensions |
| `blender-pipeline-automation` | Batch jobs and file conversion |
| `blender-asset-qa` | Catches z-fighting, floating parts, bad normals, weights and textures |
| `blender-workflow-recipes` | Complete asset playbooks |

## development.

```bash
python tools/validate_skills.py      # spec + token budget checks
python tools/run_tests.py            # the headless Blender tests (BLENDER_EXE to override)
python tools/run_tests.py --cloud    # the same tests on Patch's cloud Blender
python block/build.py                # the block's demo page on Patch, in dist/
```

## credits.

- The skills, their scripts and tests: [EL4CTEO/blender-skills](https://github.com/EL4CTEO/blender-skills), MIT. This
  repo keeps its history; our changes are the commits on top.
- Models in the demos come from Patch's asset library, each with its licence. Poly Haven's, Kenney's, KayKit's,
  MakeHuman's (MPFB) and anymove's are CC0. Two are CC-BY-4.0: Polyfork's Old Lighthouse in `blender-time-of-day` and
  Scenario's Peach fox creature in `blender-retopology-uv`. Each demo's CREDITS.md lists its models and their sources.

MIT, like the original. The demo clips and pictures are CC0, except those of `blender-time-of-day` and
`blender-retopology-uv`, which show the two CC-BY-4.0 models above and keep their credits.

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/footer-evening.png">
  <img alt="patch.gg" src="docs/readme/footer-day.png" width="500">
</picture>
