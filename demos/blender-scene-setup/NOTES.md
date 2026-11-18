# notes

Two fixes in `skills/blender-scene-setup/scripts/scene_audit.py`, both found by this demo's messy scene. Both are
plain data API calls, so they work the same on Blender 5.2 and 5.3:

- **`--fix scale` left mirrored meshes inside out.** `_apply_rot_scale` baked a negative scale into the mesh
  with `Mesh.transform` but never flipped the face winding. Tested on a cube at scale (-1, 1, 1): its signed
  volume stayed -1.0 after the fix. The same happened on the Poly Haven side table with its custom normals:
  faces and normals both pointed in. So the fix turned a `negative_scale` finding into an inside-out asset,
  which is what qa_check calls "normals pointing inward". It now calls `Mesh.flip_normals()` when the applied
  matrix has a negative determinant, as Blender's own Apply Scale does. That keeps faces and custom normals
  pointing out (checked on the table: signed volume +, corner normals along the faces). In this demo the mirrored
  plant comes out with 0 inside-out parts.
- **The "rotated" check read `rotation_euler` whatever the rotation mode.** glTF imports rotate with
  quaternions. A barrel turned 90 degrees that way was never flagged, and `--fix scale` left it rotated. The
  opposite case broke too: a stale `rotation_euler` that Blender ignores in quaternion mode was flagged
  forever, because the fix can't clear it. A small `_rotation(ob)` helper now reads the rotation the object
  really uses (Euler, quaternion or axis-angle).

Other things worth knowing:

- With no `--objects`, the audit (like every script built on `_bpyx.objects`) checks the **selection** if
  anything is selected. A glTF import leaves its objects selected, so the first run here audited only the
  last import. scene.py now ends with nothing selected, as a saved-and-closed file would. When you mean the
  whole scene, pass `--objects` or clear the selection first.
- qa_check (render profile) passes on the barrel. It reports z-fighting on the plant (46 tri pairs), tool
  chest (48) and side table (94). Those faces are in the Poly Haven source files: a fresh import of the
  original table shows the same 94 pairs, tiny faces at its feet and shelf. Scene setup doesn't change the
  geometry, so they're reported as they are. After the fix, 0 parts are inside out.
- The stage uses the Khronos PBR Neutral view transform, not AgX. Under AgX the #F53CD1 labels come out
  pastel (215, 146, 197); PBR Neutral keeps them pink (about 230, 90, 200).
