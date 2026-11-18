# notes

Nothing in the skill's scripts needed fixing. Two steps from SKILL.md don't work as written, though, and
the demo works around both:

- **`extension build` won't create its output folder.** SKILL.md's
  `blender --command extension build --source-dir ./my_tool --output-dir ./dist` fails on a fresh checkout:
  `FATAL_ERROR: Error creating archive "[Errno 2] No such file or directory: 'dist/.gear_maker-1.0.0.zip'"`.
  The repo's own test makes the folder first. The demo runs `mkdir -p dist` before building. SKILL.md
  should say so.
- **`extension install-file` exits 0 when it fails.** Pointed at a zip that wasn't there, it printed
  `ERROR Error extracting archive` and still returned 0. The demo checks the output for
  `Installed "gear_maker"` instead of trusting the exit code.

How the steps run on the cloud:

- The extension CLI goes through `cloud.py exec "<shell command>"` in the session's /work, and the built
  zip comes back with that call. It installs to `/root/.config/blender/5.2/extensions/user_default/`.
- The live Blender was already running when `install-file` ran in a separate process. So make_gears.py
  enables the extension by module name: `addon_utils.enable("bl_ext.user_default.gear_maker")`. Then
  `bpy.ops.gear_maker.add_gear(...)` runs headless with no context override. After a re-install into the same
  live session, the old modules have to leave `sys.modules` first, or the old code keeps running.
  make_gears.py does that; in a fresh session it's a no-op.
- qa_check caught a real gap in the first version of the extension. Its operator made gears with no
  material, and the render profile flags that as an error ("faces use empty/missing material slot(s)").
  The operator now has a **Metal** parameter (steel or brass) and puts the gear on a shared material, so
  what it delivers passes as is. qa_check (render profile) passes on all three gears: closed, no
  inside-out parts, on the ground. Two warnings are expected: no UV map (plain procedural metal) and some
  duplicate vertices on the spoked gears. Those come from the Bevel modifier at the window corners. The
  operator's own mesh has none (`--no-modifiers`: 0).
