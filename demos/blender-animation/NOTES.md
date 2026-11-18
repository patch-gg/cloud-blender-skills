# notes

## skill fix (blender-animation)

- **retarget.py's auto map didn't understand the skeleton Rigify really makes.** Rigify names the hips
  `spine` and the neck and head `spine.004`-`spine.006`, so on the game skeleton from `rigify_build.py
  --game-skeleton` the auto map found no hips (`"hips": null`: no hip travel or bob at all), gave the head
  the source's chest rotation, and listed Rigify's `pelvis.L/.R` helpers as missing key parts. Now, when a
  rig has no hips, neck or head by name, they come from the ends of its spine chain (the lowest link is the
  hips, the links above the arms' parent are the neck and head), and sided hip helpers are skipped. The map
  this demo shows: 22 bones, `spine` <- `pelvis`, `spine.004` <- `neck`, `spine.006` <- `head`, nothing
  missing. The repo's retarget test passes; its "Rigify names" rig uses `DEF-hips`/`DEF-head`, which is why
  it didn't catch this.

## other things worth knowing

- **Rest poses.** The woman's arms hang lower than the man's and her forearms point down where his bend 50
  degrees forward, so the same rotations would have bent his elbows up. `match_rest.py` does the skill's "pose
  the target's rest like the source's first": his limb bones turned onto hers (forearms and hands 23 degrees,
  upper arms 9, legs 3) and applied as his rest pose.
- The game skeleton follows the control rig through Copy Transforms constraints; the demo mutes them (one
  `expr`) so it can carry the retargeted keys, and bake_action's self-bake then clears them.
- loop_check: no pops. It flags speed hitches across the seam (toe.L, shoulder.L, shin.R); the source mocap
  has the same ones at the same speeds, so they're in the clip itself, not added by the retarget, and
  `--fix` (which fixes pops) has nothing to do.
- bake_action's self-bake keys every bone of the constraint-free skeleton (36 bones, 360 curves), so the
  key count goes up (4,914 to 5,408) rather than down; the clip still loops after it.
- The two walkers are turned 25 degrees in place for the clip so the stride reads; the retarget only uses
  changes from rest, so where they stand doesn't matter.
