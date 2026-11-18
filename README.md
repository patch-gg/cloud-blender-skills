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

That's any headless call from the skills with `--cloud` added. Under it is
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

**Needs:** Blender 5.2 LTS or newer on your machine, or Patch's `pch` for the cloud. Optional: a Blender MCP server, so
agents can work in your open Blender.

## the demos.

Every clip is one skill, run by an agent on Patch's cloud Blender from an empty session: the scene built in bpy or
taken from [Patch's asset library](https://patch.gg/create/toolbox/assets), the skill's own scripts doing the work,
its QA gate, and a final render on a cloud GPU. Click one for the commands that made it.

<!-- demos -->
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
- Models in the demos come from Patch's asset library, each with its licence: the fire hydrant is
  [Poly Haven's](https://polyhaven.com/a/fire_hydrant) (CC0). A demo that uses others lists them in its CREDITS.md.

MIT, like the original. The demo clips and pictures are CC0.

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/footer-evening.png">
  <img alt="patch.gg" src="docs/readme/footer-day.png" width="500">
</picture>
