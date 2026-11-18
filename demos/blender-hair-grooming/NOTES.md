# notes

Everything ran on the cloud as written; nothing in `groom.py` was changed. What the demo ran into:

- **QA fails on the cards, and the demo reports it as is.** `qa_check.py --profile game` on Head + Hair_Cards finds
  z-fighting: about 2,270 coplanar card pairs and about 200 card/scalp pairs. `build_cards` lays each card along one
  strand at that strand's own height, so where the drooped strands overlap, their cards overlap in a single layer.
  SKILL.md says pros layer cards from the scalp outward; the script has no layering (or offset) option. A fix would
  lift each card a little along the surface normal, more for cards picked later.
- **The atlas colour is fixed.** `render_atlas` draws every strand in one brown, (0.12, 0.07, 0.04), and `run()` has no
  flag for it, so the cards don't follow `--melanin`. The groom here uses melanin 0.55, redness 0, to sit near it.
- **Atlas coverage is thin.** Atlas strands are always ~1.2 px wide (radius 0.6 / res) and 40 per column, so each card is
  mostly transparent, and more so at a higher `--atlas-res`. The default 120 cards read as a near-bald head; 900 cards
  at 20 mm (19,800 tris, inside SKILL.md's hero budget) read as hair.
- Hair Dynamics is switched off in `present.py`: the busts spin, and nothing should simulate in a turntable (SKILL.md:
  bake it before animated renders).
- `d.render` encodes at crf 20, which put this clip at 1.66 MB, over the ~1.5 MB cap. `demo.py` re-encodes the pulled
  clip at crf 22 (about 1.2 MB) before `d.media`.
