"""blender-pipeline-automation on Patch's cloud Blender: batch_process.py over a folder of mixed files.

Fifteen CC0 props from Patch's asset library arrive as GLB; four batch converts turn them into a mixed inbox
(FBX, USDZ, .blend, GLB), then one batch inventories it, two shards QA every file with blender-asset-qa, and
one batch delivers everything as GLB. Every batch is a separate `blender -b` in the session (--process), the way
the skill runs it. The delivered files then go on a stepped display, popping in in the order the batch went
through them, with a pink ring under each file QA flagged.

Prompt it stands for: "Take this folder of mixed FBX, USDZ, .blend and glTF models, inventory it, QA every file
and deliver them all as GLB."
Run: python demos/blender-pipeline-automation/demo.py   (pch signed in; BAS_RENDER_SESSION optional)
"""
import contextlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from demo import Demo  # noqa: E402

BATCH = "blender-pipeline-automation/scripts/batch_process.py"
QA = "/work/_skills/blender-asset-qa/scripts/qa_check.py"   # the session's copy of the QA skill
# how the library's GLBs reach the inbox: FBX keeps colour and normal maps but not metal/roughness (so it gets
# the non-metal props), USDZ and .blend keep everything, OBJ would drop the packed textures (not used)
INBOX = {
    "fbx": ["rubber_duck_toy", "baseball_01", "american_football", "wicker_basket_02"],
    "usdz": ["korean_fire_extinguisher_01", "watering_can_metal_01", "vintage_electric_kettle", "potted_plant_04"],
    "blend": ["metal_toolbox", "alarm_clock_01", "garden_sprinkler_01", "wooden_bucket_01"],
    "glb": ["barrel_01", "pot_enamel_01", "measuring_tape_01"],
}
EXPORT_SET = {"fbx": ["--set", "embed_textures=true", "path_mode=COPY"]}
IDS = ["polyhaven:" + n for n in ("alarm_clock_01", "wooden_bucket_01", "korean_fire_extinguisher_01",
                                  "watering_can_metal_01", "potted_plant_04", "rubber_duck_toy", "metal_toolbox",
                                  "Barrel_01", "vintage_electric_kettle", "wicker_basket_02", "baseball_01",
                                  "pot_enamel_01", "garden_sprinkler_01", "american_football", "measuring_tape_01")]

d = Demo(__file__)


@contextlib.contextmanager
def whole_output():
    """Demo.cloud returns cloud.py's last JSON line, which for batch_process is the summary; the per-file lines
    stream before it. Keep the whole output of the call too (reported upstream, see NOTES.md)."""
    got, real = [], subprocess.run

    def run(*a, **k):
        p = real(*a, **k)
        got.append(p.stdout or "")
        return p
    subprocess.run = run
    try:
        yield got
    finally:
        subprocess.run = real


def batch(*args):
    """batch_process.py as its own Blender process; returns (summary, one record per file)."""
    with whole_output() as got:
        summary = d.skill(BATCH, *args, process=True)
    lines = [json.loads(ln) for ln in got[-1].splitlines() if ln.startswith("{")]
    files = [j for j in lines if "file" in j]
    if len(files) != summary.get("files"):
        raise SystemExit(f"batch streamed {len(files)} of {summary.get('files')} files: {summary}")
    return summary, files


def op(summary, files):
    return {"files": summary["files"], "ok": sum(1 for f in files if f.get("ok")), "failed": summary["failed"],
            "sec": summary["sec"]}


# 1. a mixed inbox, the way such folders arrive: the library's GLBs batch-converted four ways
src = {p.stem: p for p in d.asset(*IDS)}
made = {}
for to, names in INBOX.items():
    made[to] = op(*batch("--in", *[src[n] for n in names], "--op", "convert", "--to", to, "--out", "inbox/",
                         *EXPORT_SET.get(to, [])))

# 2. inventory
rep_sum, report = batch("--in", "inbox/", "--op", "report")

# 3. QA every file in two shards: two processes, and each reply stays under the session's 20 KB output limit
qa_sums, qa = [], []
for shard in ("0/2", "1/2"):
    s, files = batch("--in", "inbox/", "--op", "script", "--script", QA, "--kwargs", '{"profile":"game"}',
                     "--shard", shard)
    qa_sums.append(s)
    qa += files
flagged = sorted(Path(f["file"]).stem for f in qa if not (f.get("result") or {}).get("pass"))

# 4. deliver everything as GLB
dl_sum, delivered = batch("--in", "inbox/", "--op", "convert", "--to", "glb", "--out", "delivered/")

# verify: every file the batches wrote came back here, non-empty
inbox = sorted(p for p in (d.work / "inbox").iterdir() if p.is_file())   # (FBX imports leave .fbm folders)
out = sorted((d.work / "delivered").glob("*.glb"))
pulled_ok = all(p.stat().st_size > 0 for p in inbox + out) and len(out) == len(IDS)

# present: the delivered GLBs on a stepped display, a pink ring under each flagged file
meshes = d.run("scene.py", "--dir", "delivered", "--flagged", *flagged)["meshes"]
d.skill("blender-lighting-lookdev/scripts/turntable.py", "--objects", *meshes, "--rig", "studio", "--backdrop",
        "--frames", "96", "--lens", "50", "--elevation", "22")
d.run("present.py")
d.look("look.jpg", "--engine", "eevee")
d.save("demo.blend")
r = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--preset", "final", "--samples", "32",
             "--res", "1280", "720", "--percent", "100", frames="1-96", poster=92)
media = d.media(r, crop="crop=380:380:330:270")   # the picker picture: toolbox, duck, pot, watering can

kinds = Counter(Path(f["file"]).suffix[1:] for f in report)
errors = {Path(f["file"]).stem: sorted({e.split(":")[0] if e.startswith("z-fighting") else e.split(": ", 1)[-1]
                                        for e in (f.get("result") or {}).get("errors", [])}) or [f.get("error")]
          for f in qa if (f.get("result") or {}).get("errors") or not f.get("ok")}
print(d.finish({
    "files_in": len(IDS), "inbox": dict(kinds), "inbox_mb": round(sum(p.stat().st_size for p in inbox) / 1e6, 1),
    "make_inbox": made,
    "report": {**op(rep_sum, report), "tris": sum(f.get("tris", 0) for f in report),
               "materials": sum(f.get("materials", 0) for f in report),
               "images": sum(f.get("images", 0) for f in report),
               "missing_images": sum(len(f.get("missing_images", [])) for f in report)},
    "qa": {"profile": "game", "shards": 2, "files": len(qa), "pass": len(qa) - len(flagged), "flagged": flagged,
           "errors": errors, "sec": [s["sec"] for s in qa_sums],
           "failed": [x for s in qa_sums for x in s["failed"]]},
    "deliver": {**op(dl_sum, delivered), "glb": len(out), "mb": round(sum(p.stat().st_size for p in out) / 1e6, 1)},
    "pulled_ok": pulled_ok,
    "render": {k: d.last_render.get(k) for k in ("engine", "sec_per_image", "res")}, **media},
    prompt="Take this folder of mixed FBX, USDZ, .blend and glTF models, inventory it, QA every file and "
           "deliver them all as GLB."))
