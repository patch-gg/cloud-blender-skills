# notes

## fixed in `skills/blender-weather-fx/scripts/`

- **surface_weather.py: a second call wiped the first call's materials.** Every call rebuilt the shared
  `ENV_Weather` group (`nodes.clear()`, `interface.clear()`), which drops every material's links to it, and
  then rewired only its own materials. The SKILL's porosity advice (0.6-0.9 for asphalt and brick, 0.1-0.2
  for metal and glass) means two calls, so the road, sidewalk and facade from the first call ended up with
  their BSDF unlinked: Base Color back to 0.8 white, no normal map, no coat. Measured on the cloud (5.2.0)
  as a white road and a pale facade. Fix: reuse the group when it exists (`_snow_tree` had the same
  pattern for the snow modifier's inputs). After it, the first call's road stays wired, params intact.
- **surface_weather.py: materials whose inputs come from a Mix node failed.** It records a linked input's
  source socket by identifier and looked it up with `outputs[identifier]`, which matches names; a Mix node
  names all four outputs `Result` (`Result_Float`, `Result_Color`, ...), so any Mix-fed Base Color raised
  `KeyError: 'Result_Color'` halfway through, leaving the material half-wired. Fix: find the output by
  identifier (`_out()`), in apply and in `--remove`.
- **lightning.py: the bolt showed between flashes.** The bolt is an emission curve keyed to strength 0
  when unlit, which renders black, so against a lit sky, fog or city glow it showed as a dark crack for
  the whole clip. Fix: key the bolt's `hide_render` with the same envelope (hidden at 0).

`python tools/run_tests.py weather` passes on Blender 5.2.0 (no 5.3 here).

## choices in the demo

- `scene_mood.py --time moonless`: the metered exposure keeps an ambient-lit grey card at the preset's
  brightness, which leaves the overcast sky and fog about five times brighter than that card; the wet road
  then mirrors it white. `present.py` exposes the night for its lamps instead: 3 EV under the metered value,
  lamps 1500 W. `--city-glow 0.15` keeps the fog blue-grey against the warm lamps.
- 90 frames: precipitation.py loops over any length, but surface_weather's ripples run at 1.6 Hz, so the
  clip loops cleanly only when its length x 1.6 is whole (3.75 s, 5 s).
- Cycles: EEVEE with ray tracing (needed for puddle reflections) took 24 s a frame with 300k rain streaks
  on the L40S; Cycles takes about 4.
