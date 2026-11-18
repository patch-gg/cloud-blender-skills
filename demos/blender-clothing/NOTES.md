# notes

## skill fix (blender-clothing)

- **garment.py normalised a region group into the skin weights.** It copies every vertex group of the body
  onto the garment, then limits to 4 influences and normalises all of them. With the documented
  `--group Torso` usage the region group came along: it took one of the 4 slots and halved the real bone
  weights (they summed to about 0.49 per vert; Blender's Armature modifier renormalises, engines don't).
  Groups that aren't deform bones of the body's rig are now dropped after the transfer, before the limit and
  normalise: the vest has 35 bone groups summing to 1.0. The repo's clothing tests still pass.

## other things worth knowing

- **Layered clothing.** Patch's MPFB export has the skin under the clothes removed, so the vest is made over
  the t-shirt: `garment.py --body Shirt`, the skill's "a vest over the shirt". `avatar.py --shirt` keeps the
  shirt as its own mesh; both are rigged with the rigging demo's chain.
- **vest_prep.py**, before garment.py:
  - smooths the body there (one of the skill's fixes). The shirt is creased under the arms and at its
    turned-up hem, with faces meeting at more than 70 degrees. Offset 12 mm, a crease under the right arm
    folded over and the vest's Solidify thickness shot a 30 cm spike out of it (it also made the poke check
    report 37 false hits along the sleeve). Relaxing the 214 verts around those creases removed the fold.
  - makes the region from the shirt's body panels (UV islands), so the vest's armholes, neckline and hem
    follow the shirt's own seams. A region from weights (verts the upper arm moves less than half) gave
    jagged, saw-tooth armholes on this triangulated mesh.
- **vest_finish.py** adds a Corrective Smooth after the vest's Armature (the rigging skill's fix for
  collapsing): the 32-degree twist in the clip pinched two short creases into the vest's front without it.
  Engines don't run Corrective Smooth; for a game export, bake the clip or leave it off.
- The vest casts no shadow in the clip: in EEVEE it shadowed its own grazing sides into a grey speckle under
  the arms (higher GI, shadow-ray and filter settings didn't clear it; shadows off did, and Cycles never had it).
- **Poke check** in each stress pose: 0 everywhere except arms raised 70 degrees, where 5 verts of the shirt's
  shoulder seams come up through the vest's shoulder straps. The clip's own poses (twists, arms out to
  horizontal) check 0.
- The vest is 53,760 tris evaluated (subdivision 1 and the 10 mm thickness); without `--subdiv` it is about a
  fifth of that, the size a game would want.
