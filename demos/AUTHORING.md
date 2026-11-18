# making a demo.

One demo per skill. A demo is an agent following that skill's SKILL.md on Patch's cloud Blender,
written down as a script anyone can run again, plus the clip it made.

## what a demo folder holds

```
demos/<skill>/
  demo.py          host-side driver: every step is a real cloud.py call (through demos/_lib/demo.py)
  scene.py, ...    bpy files the driver runs in the session (build the input scene, presentation glue)
  media/clip.mp4   1280x720, 24 fps, H.264, no sound, 3-5 s, loops where it can; at most ~1.5 MB
  media/poster.webp, media/thumb.webp   made from the clip by d.media()
  result.json      the numbers (written by d.finish)
  commands.md      the cloud.py commands that ran (written by d.finish)
  NOTES.md         only if something needed fixing or doesn't work on the cloud
  CREDITS.md       only if a CC-BY asset was used
  work/            scratch, mirrored to the session's /work, not committed
```

Run one: `python demos/<skill>/demo.py` from the repo root, with pch signed in. `BAS_RENDER_SESSION=ses_...`
renders the final clip in that GPU session; without it, `d.render` sends a GPU job (`cloud.py render`).

## how to build one

1. Read the skill's SKILL.md, and a `references/*.md` only where it points you. Use its scripts the way it
   says, with the flags its docstrings list. The scripts are the demo: don't reimplement them in scene code.
2. Build the input in bpy (`scene.py`), procedurally, or start from Patch's asset library:
   `pch assets search "<one noun>" --type model`, CC0 first; CC-BY-4.0 is fine with a line in CREDITS.md.
   Nothing from anywhere else.
3. Drive it from `demo.py` with `Demo`: `d.run("scene.py")`, `d.skill("<skill>/scripts/x.py", flags...)`,
   `d.look("step.jpg")` and open the picture after every step that changes what you'd see.
4. Finish geometry work with `blender-asset-qa/scripts/qa_check.py` and put its pass/errors in the numbers.
5. Present it, save (`d.save("demo.blend")`), render (`d.render(...)`), `d.media(clip)`, `d.finish({...}, prompt=...)`.
   `prompt` is the one-line ask the demo stands for, as a person would type it.

## how it should look

- **Show what the skill does, not only the end.** Before and after (a wipe or a hold-and-cut), a lineup with
  small labels, or the stages in order. Someone should get the skill from the clip with the sound off.
- **One quiet stage.** For assets: `blender-lighting-lookdev/scripts/turntable.py --rig studio --backdrop`
  (or `--rig both --hdri <a Blender studiolight>`), AgX, the subject filling most of the frame. Frame a wide
  subject by its width: a turntable fits a bounding sphere and leaves a 16:9 frame half empty. Skills about the
  world itself (time of day, weather, terrain, simulation) get a proper scene instead.
- **Words:** a few short lowercase labels at most ("before", "after", "lod2 · 1,204 tris"), small, dark grey
  (#111) on light or white on dark, as Blender text objects that read at 1280x720. No titles, logos or sentences:
  the page around the clip says what it is.
- **Pink (#F53CD1) only to point at something**, such as what QA caught.
- **Render:** EEVEE by default; Cycles when the skill is about light or materials, at 128 samples or fewer. Keep
  it 1280x720, 72-120 frames. Look at three frames of the finished clip (`ffmpeg -ss <t> -i clip.mp4 -frames:v 1 x.jpg`,
  then open them) and fix what's off before you call it done. Would this make someone want the skill?
  `demos/blender-pbr-materials` is the bar.

## cloud rules

- The scene in a session builds up between calls. `d.run`/`d.skill` pull whatever a call writes into `work/`.
- Cloud sessions are Blender 5.2.0, CPU only (small: 2 cores, 4 GB). Heavy scenes: `cloud.py start --size medium`
  first (`BAS_SESSION` to reuse it). No session GPU: the GPU box is shared, through `d.render` only.
- Stop what you start (`d.finish` stops the demo's session). Keep a demo under about 60 credits.
- If a skill's script fails on the cloud, find out why. A real bug in the script: fix it in `skills/` with the
  smallest change that keeps Blender 5.2 and 5.3 working, and say what and why in the demo's NOTES.md. A problem in
  `cloud.py`, `_bpyx.py` or `demos/_lib/demo.py`: report it, don't patch around it in the demo.
