#!/usr/bin/env python3
"""Build dist/, the block's live demo on Patch, and recipe.json, its controls.

dist/ holds index.html (block/index.html with the demo list and the block section filled in), each demo's
clip, poster and picker picture, Patch's demo helper (patch-block.classic.js, fetched from patch.gg) and
the licence. block/catalog.json sets the order, the groups, the labels and the captions.

Usage: python block/build.py        then: pch validate && pch publish (patch.json names the project)
"""
import json
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
HELPER = "https://patch.gg/patch-block.classic.js"


def main():
    catalog = json.loads((ROOT / "block" / "catalog.json").read_text("utf-8"))
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "media").mkdir(parents=True)
    (DIST / "thumbs").mkdir()
    demos, missing = [], []
    for c in catalog:
        m = ROOT / "demos" / c["id"] / "media"
        if not (m / "clip.mp4").exists():
            missing.append(c["id"])
            continue
        shutil.copy2(m / "clip.mp4", DIST / "media" / f"{c['id']}.mp4")
        shutil.copy2(m / "poster.webp", DIST / "media" / f"{c['id']}.webp")
        shutil.copy2(m / "thumb.webp", DIST / "thumbs" / f"{c['id']}.webp")
        if (DIST / "thumbs" / f"{c['id']}.webp").stat().st_size > 48 * 1024:
            sys.exit(f"{c['id']}: thumb.webp is over Patch's 48 KB for option pictures")
        demos.append({"id": c["id"], "label": c["label"], "group": c["group"], "caption": c["caption"],
                      "clip": f"media/{c['id']}.mp4", "poster": f"media/{c['id']}.webp"})
    if not demos:
        sys.exit("no demos with media yet")
    first = next((d["id"] for d in demos if d["id"] == "blender-workflow-recipes"), demos[0]["id"])
    block = {"controls": [
        {"id": "skill", "label": "Skill", "type": "choice", "default": first, "essential": True,
         "hint": "Each clip is one skill, run by an agent on Patch's cloud Blender. The commands it ran are in "
                 "the repo, under demos/.",
         "options": [{"value": d["id"], "label": d["label"], "group": d["group"],
                      "image": f"thumbs/{d['id']}.webp"} for d in demos]},
        {"id": "caption", "label": "Caption", "type": "toggle", "default": True, "essential": True,
         "hint": "The skill's name and what the clip shows."},
        {"id": "speed", "label": "Speed", "type": "number", "min": 0.25, "max": 2, "step": 0.25, "default": 1,
         "unit": "×", "hint": "How fast the clip plays."},
    ]}
    credits = []  # every model the clips show, with its licence (CC-BY ones need the line)
    for d in demos:
        res = ROOT / "demos" / d["id"] / "result.json"
        seen = set()
        for a in (json.loads(res.read_text("utf-8")).get("assets") or []) if res.exists() else []:
            key = (a.get("author"), a.get("license"), a.get("source"))
            if key in seen:
                continue
            seen.add(key)
            credits.append({"files": f"media/{d['id']}.*", "license": a.get("license"), "author": a.get("author"),
                            "source": a.get("source")})
    recipe = {"mode": "browser", "block": block, "credits": credits}
    (ROOT / "recipe.json").write_text(json.dumps(recipe, indent="\t", ensure_ascii=False) + "\n", "utf-8")
    html = (ROOT / "block" / "index.html").read_text("utf-8")
    html = html.replace("/*DEMOS*/[]", json.dumps(demos, ensure_ascii=False))
    html = html.replace("/*BLOCK*/{}", json.dumps(block, ensure_ascii=False))
    (DIST / "index.html").write_text(html, "utf-8")
    with urllib.request.urlopen(HELPER, timeout=30) as r:
        (DIST / "patch-block.classic.js").write_bytes(r.read())
    shutil.copy2(ROOT / "LICENSE", DIST / "LICENSE.txt")
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"dist: {len(demos)} demos, {size / 1048576:.1f} MB" + (f"; no media yet: {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
