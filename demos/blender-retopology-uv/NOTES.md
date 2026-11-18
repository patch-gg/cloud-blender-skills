# notes

## fixed: `auto_retopo.py --method quadriflow` failed or hung on Blender 5.2

On the cloud (5.2.0) the script stopped with `quadriflow failed on voxel remesh and source (non-manifold?)`
on this mesh, and on as plain a mesh as Suzanne. Two causes, both fixed in
`skills/blender-retopology-uv/scripts/auto_retopo.py`:

- **QuadriFlow refuses any edge under 1e-4**, as part of its manifold check, and it refuses silently:
  CANCELLED, no report. Voxel remesh output often has a few such edges (Suzanne remeshed at 2.3 cm had
  3). The script now collapses them (`bmesh.ops.dissolve_degenerate`, 0.2 mm) before each QuadriFlow call.
- **`use_preserve_sharp=True` stalled QuadriFlow.** On a voxel surface the "sharp" edges are voxel steps.
  With it, QuadriFlow ran past 5 minutes on this creature (the run had to be cancelled, and Blender was
  restarted), and past 2 minutes at a 2 cm voxel. Without it: 1.6 s. The script now passes `False`.

Both changes are a plain bmesh op and an operator flag, the same on 5.2 and 5.3.

## what QA and the density check changed

- At `--tris 6000`-`8000`, `qa_check.py` found 1-2 overlapping coplanar triangle pairs: thin parts
  collapse onto each other under the script's shrinkwrap. `--tris 5000` (3,976 out) came out clean.
- Smart UVs left the 124 islands at 970-1,668 px/m (spread 1.72, over the SKILL's 1.3), so the demo runs
  `texel_density.py --set 1024`: every island at 1,024 px/m, still inside 0-1.

Not fixed: when QuadriFlow fails, the script leaves its half-made `<name>_low` object in the scene.
