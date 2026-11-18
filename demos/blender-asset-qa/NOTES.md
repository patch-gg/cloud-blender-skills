# notes

- **Fixed: `scripts/review_shots.py` couldn't save its sheet in a cloud session** (found while making the
  blender-core demo). The live scene there is unsaved, so `bpy.path.abspath("//review.png")`, the docstring's
  own example, comes back as the bare relative `review.png`, and Blender's renderer can't write a relative
  path ("cannot save: 'review_front.png'"). Without `--out` the sheet goes to /tmp, which cloud.py never pulls
  back. Now the path is anchored to the working directory (`os.path.abspath`), which is /work in a session,
  so the sheet comes back with the call. One line of plain Python, so it works the same on Blender 5.2 and
  5.3. Both sheets here (`review_broken.png`, `review_fixed.png`) came back that way.
- **A limit in qa_check's floating check (not changed).** It skips the largest island, treating it as the
  asset's anchor, and only flags islands that touch nothing. So a detached part goes unflagged when it is
  the largest island, or when it is made of islands that touch each other. The first version of this demo
  slid the barrel's widest hoop loose: QA flagged only the 4 nails left behind, because that hoop is the
  barrel's largest island. Catching that would mean grouping touching islands into parts and picking a
  better anchor, which is more than a small fix, so the demo's floating part is the bung instead.
- One broken thing can show up as several findings. With one stave inside out, its glued side faces point
  the same way as their neighbours, so QA also reports z-fighting inside the body (94 tri pairs) and against
  the base (4). demo.py deletes only a z-fighting duplicate it can name (`Barrel_Lid.001`), fixes the rest,
  then re-runs QA as SKILL.md says. The extra z-fighting is gone after the normals are fixed: `game`
  profile, 0 errors.
- The floating fix slides the bung toward the barrel until it touches (within 1 mm, half qa_check's
  `--tol`). That is the first contact, at the hole's rim, so the bung ends about 2.4 cm prouder than in the
  Poly Haven original. It's attached and QA passes, but seating it fully would need to know the hole.
- The 4 warnings left after the fixes are hidden back-to-back faces (staves glued face to face). They come
  with the source barrel, which passes `game` with the same warnings before anything is broken.
- The stage uses the Khronos PBR Neutral view transform, not AgX. Under AgX the #F53CD1 highlights come out
  pastel; PBR Neutral keeps them pink.
