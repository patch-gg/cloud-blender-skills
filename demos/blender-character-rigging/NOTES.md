# notes

## skill fixes (blender-character-rigging)

- **rigify_build.py `--fit` left the rig off the mesh.** It centred the metarig by moving the object but
  applied only rotation and scale. Rigify builds the rig from the bones' local coordinates at the origin,
  so the control rig and the game skeleton came out shifted by the metarig's leftover location, here
  3.6 cm forward of every joint placed on the mesh. It now applies location too.
- **stress_poses.py's spine twist turned the whole body.** The spine role picked `spine_fk.001`, which in
  Rigify's basic spine sits below the pivot (the hips side), so frame 50 rotated hips and legs with the
  chest and the waist never twisted. It now picks `spine_fk.002`, the first FK bone above the pivot
  (default pivot); measured: feet stay put, the chest turns 45 degrees.
- **bind_mesh.py left verts unweighted.** Bone heat missed the 250 eyelash verts (1.6%, under the 2% that
  switches to the proxy), so they would stay behind in every pose and rig_check failed the rig. Verts heat
  misses now take the weights of their nearest weighted vert (`filled_from_nearest` in its JSON).

All three keep the repo's rigging tests passing on Blender 5.2.

## other things worth knowing

- The library's MPFB character ships with an exported game skeleton. `avatar.py` removes it so the demo
  starts from an unrigged mesh, and welds the 1,094 verts glTF split along UV seams (bone heat needs
  connected surfaces).
- `fit_joints.py` is the skill's "place the joints" step: plane sections through the mesh for legs and
  spine, and a medial axis traced through the arm for shoulder, elbow and wrist. It lands within 1-2 cm of
  the asset's own exported joints (used only to check it while building the demo, never as input).
- qa_check's 53 z-fighting tri pairs come with the asset, not the rig: MPFB's eyebrow and eyelash cards
  lie on the skin, and the eye is layered (cornea over iris), each within 1 mm.
- In the clip the stress poses are spaced 20 frames apart, and the crouch lowers the root 0.585 m so the
  feet stay on the floor (the skill keys the crouch with the hips where they were, so it floats). The
  skeleton beside him is a pose-space copy of the game skeleton, its bones lit pink while their pose holds.
- `avatar.py` and `fit_joints.py` are also used by the blender-animation and blender-clothing demos.
