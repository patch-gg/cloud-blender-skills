# notes

- **How the side-by-side is made.** `compose.py` (run in a separate Blender with `cloud.py run --process`) builds a
  VSE-only scene whose image strips read `//../<engine>/render/f_####.png`. Those are the PNGs `d.render` leaves next
  to each engine's .blend in the GPU box, so rendering `work/compose/demo.blend` there joins the three renders before
  the clip's single encode. The compose file only works where those frames are: the box `d.render` just rendered in.
  So this demo needs `BAS_RENDER_SESSION`. Without it, `d.render` sends each .blend to its own GPU job, and the
  compose job would get only the .blend (VSE image strips can't be packed), so its bands would come out empty.
- **Two Blender 5.2 VSE quirks, worked around in `compose.py`:**
  - An opaque image strip still counts as covering the whole frame after it's cropped, so the VSE skips every strip
    under it (the EEVEE and Cycles bands came out empty). The bands blend at 0.999 instead of 1.
  - Colour strips draw nothing once cropped or transformed, so each seam is a 2 px crop of an image strip, made white
    with a Bright/Contrast modifier.
