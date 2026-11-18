#!/usr/bin/env python3
"""Run the headless Blender test suite.

Usage: python tools/run_tests.py [name-filter]     (BLENDER_EXE overrides discovery)
       python tools/run_tests.py --cloud [name-filter]   (on Patch's cloud Blender, through pch;
           costs credits; reuses the session in .cloud-blender.json, stop it with cloud.py stop)
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "blender-core" / "scripts"))
from run_in_blender import find_blender  # noqa: E402


KEEP = ("PASS", "FAIL", "SKIP", "Traceback", "  ", "AssertionError", "KeyError", "ValueError", "RuntimeError")


def report(stdout):
    out = stdout.splitlines()
    start = next((i for i, ln in enumerate(out) if ln.startswith(("PASS", "FAIL", "SKIP"))), len(out))
    return [ln for ln in out[start:] if ln.startswith(KEEP) or " passed, " in ln]


def cloud(flt):
    """The same suite in a Patch cloud Blender session (no window there: BAS_NO_WINDOW=1)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bas_cloud", ROOT / "skills" / "blender-cloud" / "scripts" / "cloud.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    o = c.parse(["--dir", str(ROOT), "--name", "blender-skills tests", "status"])
    o.size = o.gpu = None
    try:
        sid = c.session(o, c.load_state(ROOT))
        with tempfile.TemporaryDirectory(prefix="bas_tests_") as tmp:
            for d in ("skills", "shared", "tests"):
                shutil.copytree(ROOT / d, pathlib.Path(tmp) / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            c.pch("blender", "files", "upload", sid, tmp, "--to", "bas/", timeout=1800)
        cmd = ["env", "LD_LIBRARY_PATH=" + c.BLENDER_LIB, "BAS_NO_WINDOW=1", "blender", "-b", "--factory-startup",
               "--python-exit-code", "1", "-P", "bas/tests/run_all.py", "--", *flt]
        _, d = c.pch("blender", "exec", sid, "--timeout-s", 1800, "--wait", 1830, "--", *cmd, ok=(0, 1, 7), timeout=1900)
        d = c.wait_run(sid, d, 1800) or {}
    except c.CloudError as e:
        print(f"cloud: {e}")
        return e.code
    lines = report(d.get("stdout") or "")
    print("\n".join(lines) if lines else (d.get("stderr") or d.get("stdout") or "")[-3000:])
    spent = (d.get("cost") or {}).get("spent")
    print(f"cloud session {sid} (Blender 5.2.0), {spent} credits so far; "
          "stop it: python skills/blender-cloud/scripts/cloud.py stop")
    return d.get("exit_code", 1)


def main():
    if "--cloud" in sys.argv:
        return cloud([a for a in sys.argv[1:] if a != "--cloud"])
    exe = find_blender()
    if not exe:
        print("Blender not found; set BLENDER_EXE")
        return 2
    cmd = [exe, "-b", "--factory-startup", "--python-exit-code", "1",
           "-P", str(ROOT / "tests" / "run_all.py"), "--", *sys.argv[1:]]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = report(p.stdout)
    print("\n".join(lines))
    if p.returncode and not lines:
        print(p.stderr[-3000:])
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
