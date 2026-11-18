"""Host-side helper for the demos: every step is a real `cloud.py` call, the same command an agent
types, logged to the demo's commands.md. Standard library only (plus ffmpeg on PATH for media).

    from demo import Demo
    d = Demo(__file__)                           # demos/<skill>/, works in demos/<skill>/work/
    d.run("scene.py")                            # your own bpy file, in the live session
    r = d.skill("blender-asset-qa/scripts/qa_check.py", "--objects", "Crate")
    d.look("after.jpg", "--angles", "4")
    clip = d.render("work/demo.blend", "--engine", "BLENDER_EEVEE", "--frames", "1-96")
    d.media(clip)                                # media/clip.mp4, poster.webp, thumb.webp
    d.finish({"tris": 1234})                     # result.json + commands.md (and stops the session)

Env: BAS_SESSION (a session to use, else one per demo, saved in work/.cloud-blender.json),
BAS_RENDER_SESSION (a GPU session for d.render; without it d.render uses `cloud.py render`, a GPU job),
PCH / PCH_ENV / PCH_CONFIG as for pch.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLOUD = REPO / "skills" / "blender-cloud" / "scripts" / "cloud.py"
SKILLS = REPO / "skills"


class DemoError(RuntimeError):
    pass


class Demo:
    def __init__(self, file, name=None):
        self.root = Path(file).resolve().parent
        self.skill_name = name or self.root.name
        self.work = self.root / "work"
        self.work.mkdir(parents=True, exist_ok=True)
        self.media_dir = self.root / "media"
        self.session = os.environ.get("BAS_SESSION")
        self.render_session = os.environ.get("BAS_RENDER_SESSION")
        self.log, self.t0, self.spent = [], time.time(), {}

    # ------------------------------------------------------------ calls

    def cloud(self, *args, session=None, dir_=None, check=True, quiet=False):
        """python cloud.py --dir <work> [--session S] <args>; returns the last JSON line."""
        d = Path(dir_ or self.work)
        cmd = [sys.executable, str(CLOUD), "--dir", str(d)]
        s = session or self.session
        if s:
            cmd += ["--session", s]
        cmd += [str(a) for a in args]
        t = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        secs = round(time.time() - t, 1)
        lines = [ln for ln in p.stdout.splitlines() if ln.strip().startswith(("{", "["))]
        try:
            out = json.loads(lines[-1]) if lines else {}
        except ValueError:
            out = {"ok": False, "raw": p.stdout[-2000:]}
        cl = out.get("cloud") if isinstance(out, dict) else None
        if cl and cl.get("session"):
            self.spent[cl["session"]] = cl.get("spent")
            if not self.session and s is None and session is None:
                self.session = cl["session"]
        self.log.append({"cmd": self._pretty(args, s, d), "secs": secs, "ok": p.returncode == 0,
                         "quiet": quiet})
        if check and p.returncode != 0:
            raise DemoError(f"cloud.py {' '.join(map(str, args[:3]))} failed ({p.returncode}): "
                            f"{(p.stdout or p.stderr)[-1500:]}")
        return out

    def _pretty(self, args, s, d):
        def rel(a):
            a = str(a)
            for base, name in ((SKILLS, "<skills_dir>"), (d, "."), (REPO, "<repo>")):
                if str(base) in a:
                    return a.replace(str(base) + os.sep, "" if name == "." else name + "/").replace(str(base), name)
            return a
        sess = " --session $BOX" if s and s == self.render_session else ""
        return "python <skills_dir>/blender-cloud/scripts/cloud.py" + sess + " " + " ".join(
            shlex.quote(rel(a)) for a in args)

    def run(self, script, *args, **kw):
        """Run a bpy file from this demo's folder (or any path) in the live session."""
        p = Path(script)
        if not p.is_absolute():
            p = self.root / p
        dst = self.work / p.name
        if p.resolve() != dst.resolve():
            shutil.copy2(p, dst)          # inside --dir, so it lands at /work/<name>
        return self.cloud("run", dst, *(["--"] + list(args) if args else []), **kw)

    def skill(self, rel, *args, process=False, blend=None, **kw):
        """Run skills/<rel> (e.g. "blender-asset-qa/scripts/qa_check.py") with its flags."""
        a = ["run"] + (["--process"] if process else []) + (["--blend", blend] if blend else [])
        return self.cloud(*a, SKILLS / rel, *(["--"] + list(args) if args else []), **kw)

    def expr(self, code, **kw):
        return self.cloud("expr", code, check=kw.pop("check", True), **kw)

    def look(self, name, *args, **kw):
        out = self.work / name
        return self.cloud("look", "-o", out, *args, **kw)

    def save(self, rel="demo.blend"):
        """Save the live scene to work/<rel> (packed) and pull it here."""
        code = ("import bpy\ntry:\n    bpy.ops.file.pack_all()\nexcept RuntimeError:\n    pass\n"
                f"bpy.ops.wm.save_as_mainfile(filepath='/work/{rel}', copy=True)")
        self.expr(code, quiet=True)
        self.cloud("pull", rel, quiet=True)
        return self.work / rel

    def render(self, blend, *render_args, out="//render/clip", fmt="MP4", timeout=1800):
        """Render a .blend with render_batch.py on a GPU and return the local path of the output.
        With BAS_RENDER_SESSION: a separate `blender -b` in that GPU session (process mode).
        Without: `cloud.py render`, a GPU job (one at a time per org)."""
        blend = Path(blend)
        if not blend.is_absolute():
            blend = self.root / blend
        if self.render_session:
            box_dir = self.root.parent      # demos/, so each demo's files keep their own folder
            rel = blend.relative_to(box_dir).as_posix()
            self.cloud("push", blend, session=self.render_session, dir_=box_dir, quiet=True)
            r = self.cloud("--timeout", timeout, "run", "--process", "--no-pull", "--blend", rel,
                           SKILLS / "blender-rendering" / "scripts" / "render_batch.py", "--",
                           "--out", out, "--format", fmt, "--device", "GPU", *render_args,
                           session=self.render_session, dir_=box_dir)
            files = [f if not f.startswith("/work/") else f[len("/work/"):] for f in r.get("files", [])]
            got = self.cloud("pull", *files, session=self.render_session, dir_=box_dir, quiet=True)
            paths = [box_dir / f for f in got.get("pulled", [])]
            if not paths:
                raise DemoError(f"render produced nothing: {r}")
            self.last_render = r
            return paths[0] if len(paths) == 1 else paths
        r = self.cloud("--timeout", timeout, "render", blend, "-o", self.work / "render", *render_args)
        files = [self.work / "render" / f for f in r.get("files", [])]
        self.last_render = r
        return files[0] if len(files) == 1 else files

    # ------------------------------------------------------------ media

    def media(self, clip, poster_at=0.5, crop=None, loop=True):
        """clip -> media/clip.mp4 (H.264, 1280x720, no audio), poster.webp, thumb.webp (112x112)."""
        self.media_dir.mkdir(parents=True, exist_ok=True)
        clip = Path(clip)
        out = self.media_dir / "clip.mp4"
        vf = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
        _ff("-i", clip, "-an", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "24",
            "-movflags", "+faststart", out)
        dur = _duration(out)
        _ff("-ss", f"{dur * poster_at:.3f}", "-i", out, "-frames:v", "1", "-c:v", "libwebp",
            "-quality", "82", self.media_dir / "poster.webp")
        c = crop or "crop=ih:ih,scale=112:112:flags=lanczos"
        _ff("-ss", f"{dur * poster_at:.3f}", "-i", out, "-frames:v", "1", "-vf", c, "-c:v", "libwebp",
            "-quality", "80", self.media_dir / "thumb.webp")
        return {"clip_kb": round(out.stat().st_size / 1024), "seconds": round(dur, 2)}

    # ------------------------------------------------------------ end

    def credits(self):
        """Credits each session this demo used has spent so far (from pch)."""
        out = {}
        for s in list(self.spent):
            try:
                r = self.cloud("status", session=s, quiet=True, check=False)
                out[s] = (r.get("cost") or {}).get("spent")
            except DemoError:
                out[s] = self.spent[s]
        return out

    def finish(self, numbers, stop=True, prompt=None):
        if stop and self.session and self.session != self.render_session:
            r = self.cloud("stop", quiet=True, check=False)
            if r.get("spent") is not None:
                self.spent[self.session] = r["spent"]
        per = self.credits() if not stop else {k: v for k, v in self.spent.items()}
        result = {"skill": self.skill_name, "prompt": prompt, "numbers": numbers,
                  "sessions": per, "minutes": round((time.time() - self.t0) / 60, 1),
                  "blender": "5.2.0 LTS (Patch cloud)"}
        (self.root / "result.json").write_text(json.dumps(result, indent=1) + "\n", "utf-8")
        lines = [f"# {self.skill_name}: what ran", "",
                 "Every step ran on Patch's cloud Blender through `cloud.py`. `$BOX` is a GPU session used",
                 "for the final render; without one, `cloud.py render` sends the same .blend to a GPU job.", "",
                 "```bash"]
        lines += [e["cmd"] for e in self.log if not e["quiet"]]
        lines += ["```", ""]
        (self.root / "commands.md").write_text("\n".join(lines), "utf-8")
        return result


def _ff(*args):
    cmd = ["ffmpeg", "-v", "error", "-y", *[str(a) for a in args]]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise DemoError("ffmpeg: " + p.stderr[-800:])


def _duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(p.stdout.strip() or 0)
