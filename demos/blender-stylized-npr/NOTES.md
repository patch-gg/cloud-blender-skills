# notes

## fixed: a second toon_setup.py call broke the first one's materials

`skills/blender-stylized-npr/scripts/toon_setup.py`, `build_group()`. Every call cleared and recreated the
shared `NPR_Toon` group's sockets. New sockets drop every link to the old ones, so each material an earlier
call had set up lost its surface link (it rendered with no shader) and its values went back to the
defaults. Measured on Blender 5.2: after `--objects A --bands 3 --rim 0.4`, then `--objects B`, A had no
surface link and rim 0, bands 0.

The fix keeps the sockets when they already match and still rebuilds the group's inside on every call.
After a call on B, A keeps its link and values. Re-running on A still updates it in place, and `--remove`
still restores. This demo needs that, because it gives each knight its own call. The same check is in
`blender-texturing/scripts/smart_material.py`, which had the same bug.
