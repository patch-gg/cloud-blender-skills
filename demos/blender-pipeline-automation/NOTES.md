# notes

- **Long batch output breaks `cloud.py run --process`.** `pch blender exec` returns at most ~20,000 characters of
  output and cuts the middle (`… 4,290 characters cut …`). batch_process streams one JSON line per file, and QA
  over all 15 files is about 24 KB, so the cut lands inside a `@@JSON@@` line and cloud.py's `json.loads` raises
  (a traceback, no JSON). The demo QAs in two `--shard`s, about 12 KB each. A fix belongs in cloud.py: skip
  marked lines that don't parse, or read the run's log file rather than the exec reply.
- **Demo keeps only the last JSON line.** `Demo.cloud` returns cloud.py's last line, which for batch_process is
  the summary (`"results": "streamed"`). demo.py keeps the call's whole output with a small wrapper around
  `subprocess.run` to read each file's line.
- Formats, not bugs: FBX with `embed_textures=true` keeps the colour and normal maps but not metal/roughness
  (they come back as roughness 0.5), so FBX gets the non-metal props. OBJ loses textures that are packed, as
  they are after a glTF import, so the inbox has no OBJ.
