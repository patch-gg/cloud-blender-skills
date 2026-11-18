# notes

Everything runs on the cloud as is; no script was changed. QA (`qa_check.py --profile game`) failed the first
builds of the prop, and each failure was an input that fights `apply_stack.py`'s defaults (bevel by angle,
30°, one width per object). Worth knowing when you use the skill:

- **12-segment cylinders**: their side faces meet at exactly 30°, the default `--angle`. Float noise then
  bevels some side edges and not others (zero-area faces). Use 16 segments, or pass another `--angle`.
- **A coaxial ring cutter with the cylinder's own segment count and phase** (a groove, "lined up with the
  loops") makes the Exact boolean leave sub-0.1 mm slivers that the bevel then folds. Turn the cutter half a
  segment.
- **Features under about twice the bevel width** (a 14 mm bolt hole, a 2 cm groove, a 1.5 cm slot with an
  8 mm bevel) collapse under clamp overlap. Make them bigger, or give them their own part and width.
- **One long wall face notched by two cutters** triangulates into overlapping slivers once bevelled (QA
  reports z-fighting inside one object). Add edge loops across the cut region, never on a cutter's face (that
  is coplanar and much worse).

The look-dev rig from `turntable.py` is about 2 EV too bright under AgX at exposure 0 (its key light is
60·d² W, about 19 W/m² at the subject), so `present.py` scales the `LD_` lights by 0.4 and sets exposure -1.8.

The before/after is two view layers (the prop, the blockout copy) mixed in the compositor by an animated
screen position. Overlapping the two copies in one layer and cutting them with material alpha gave shadow and
depth artifacts where their surfaces coincide.
