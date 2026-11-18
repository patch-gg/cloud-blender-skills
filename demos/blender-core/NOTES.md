# notes

- **Fixed: `blender-asset-qa/scripts/review_shots.py` couldn't save its sheet in a cloud session.** The live
  scene there is unsaved, so `bpy.path.abspath("//review_wire.png")` comes back as the bare relative
  `review_wire.png`, and Blender's renderer can't write a relative path ("cannot save:
  'review_wire_front.png'"). Without `--out` the sheet goes to /tmp, which cloud.py never pulls back. The fix
  is one line in the script: the path is anchored to the working directory (`os.path.abspath`), which is
  /work in a session, so the sheet comes back with the call. It's plain Python, so it works the same on
  Blender 5.2 and 5.3.
- The verify step's first QA run caught a real gap in the build: `bmesh.ops.create_uvsphere(calc_uvs=True)`
  only fills a UV layer that already exists, so the window lens had no UV map (`game` profile error).
  build.py now creates the layer first. The run recorded here passes with 0 errors and 0 warnings.
