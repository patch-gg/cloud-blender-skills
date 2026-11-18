# notes

No script changes. Two things the demo needed:

- **The cloth sank through the crates.** With the crates themselves as `--colliders` (slatted lids, handles,
  sharp corners, up to 23k tris each), the denim tarp's 5 cm grid caught on them and the crates showed
  through it from the second half of the drape on; the bake also took 5 min on a small session. `proxies.py`
  gives each body a simple stand-in (its bounding box, a cylinder for barrels) parented to it, so it follows
  the baked keys, unseen by every ray but still in the render depsgraph; with those as the colliders the
  drape is clean and the bake takes about 30 s. That is the SKILL's "thicken the collider" advice, as
  separate proxy objects.
- **A cloth that starts later than the rigid bodies.** sim_setup.py has no start-frame flag, but `--frames`
  sets the cloth's cache range: the rigid bodies bake over 1-120 (to keys), the cloth over 48-120, so the
  tarp waits above the frame until the crates have settled; present.py puts the clip back to 1-120.
