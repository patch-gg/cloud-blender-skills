#!/usr/bin/env python3
"""Fill README.md's demo grid (between <!-- demos --> and <!-- /demos -->) from block/catalog.json and each
demo's media and result.json: a poster per skill, linking to what ran, with its caption and cost.

Usage: python tools/readme_demos.py [--check]   (--check: exit 1 if README.md is stale)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLS = 3


def credits(res):
    s = sum(v for v in (res.get("sessions") or {}).values() if isinstance(v, (int, float)))
    return s


def cell(c):
    d = ROOT / "demos" / c["id"]
    if not (d / "media" / "poster.webp").exists():
        return None
    return (f'<td width="33%" valign="top"><a href="demos/{c["id"]}/commands.md">'
            f'<img src="demos/{c["id"]}/media/poster.webp" width="100%" alt="{c["label"]}: {c["caption"]}"></a>'
            f'<br><b>{c["id"]}</b><br><sub>{c["caption"]}</sub></td>')


def table():
    cat = json.loads((ROOT / "block" / "catalog.json").read_text("utf-8"))
    cells = [x for x in (cell(c) for c in cat) if x]
    rows = ["<tr>" + "".join(cells[i:i + COLS]) + "</tr>" for i in range(0, len(cells), COLS)]
    return "<table>\n" + "\n".join(rows) + "\n</table>", len(cells)


def main():
    readme = ROOT / "README.md"
    text = readme.read_text("utf-8")
    grid, n = table()
    new = re.sub(r"<!-- demos -->.*?<!-- /demos -->", f"<!-- demos -->\n{grid}\n<!-- /demos -->", text, flags=re.S)
    if "--check" in sys.argv:
        return 0 if new == text else 1
    readme.write_text(new, "utf-8")
    print(f"README: {n} demos in the grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
