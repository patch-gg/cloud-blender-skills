# notes

## fixed in `skills/blender-environment-kits/scripts/scatter.py`

- **A second layer scattered onto the first layer's instances.** The SKILL's layering (trees, then rocks or
  bushes on the same target) stacks one `ENV_Scatter` modifier per layer, and Distribute Points on Faces read the
  whole incoming geometry, including the earlier layers' instances. Measured on the cloud (5.2.0): with pines, then
  rocks, then a third tree layer with no mask, 419 of that layer's 515 trees sat on top of pines, up to 15.4 m
  above the ground, and its result reported slopes to 43° and heights to 92 m against `--max-slope 20
  --height-max 26`. Fix: a Separate Components node feeds the distribution the mesh only. After it: 3,064
  instances in three layers, none more than 1 m above the surface, every layer inside its limits.
- **Each layer's numbers counted every layer.** `instances`, `by_source`, `slope_max_deg`, `height_range` and
  `per_m2` took every instance on the target, so a rocks layer reported the pines too (2,803 "rocks", 2,459 of
  them pines). Fix: count only instances of the layer's own collection.

`python tools/run_tests.py environment` passes on Blender 5.2.0 (no 5.3 here; both nodes and sockets used
exist in 5.2 and 5.3).

## how the demo uses the skills

- The sweep is a density mask: `reveal.py` writes `reveal` (and `reveal_rock` = reveal × `ENV_Slope`) from the
  Scene Time node, and scatter.py takes them as `--mask`. scatter.py reports at the current frame, so reveal.py
  leaves the scene after the sweep and the numbers count the whole forest.
- The far ranges are a second terrain.py call (`--name Far --flatten 0 0 440`); present.py lowers its flattened
  centre under the main terrain. Without it the sky model's dark below-horizon band shows past the terrain's edge
  (scene_mood's own gotcha).
- With the backdrop in the scene, scene_mood.py's fog box is 2.4 km wide and about 1 km tall, so thick haze
  (2.5-9 km visibility) metered the sun up to 5x and washed the frame out. 25 km visibility keeps the far ranges
  hazy and the exposure normal.
