# notes

No script changes. Two things the demo works around:

- **Blue hour comes out day-bright.** scene_mood.py meters a grey card and scales the environment so it
  reads at the preset's brightness (0.35 of noon). With the sun below the horizon the sky is the only light,
  so it is lifted 9-10 EV and renders as bright as a noon sky. `shot.py --exposure -1.5` exposes blue hour
  for the sky instead, with the lamp doubled.
- **Night fog speckles around the lamp in Cycles.** The height fog (`--fog-height`) is a heterogeneous
  volume; with the default null-scattering integrator, the lantern's light scattering in the thin upper fog
  left grain that 64 samples and the denoiser didn't clear. scene.py sets `cycles.volume_biased` (ray
  marching, as the SKILL notes) with `volume_step_rate 0.05`: the fog box is 20 km wide, so the automatic
  step is too coarse for 1 m beams at the default rate.
