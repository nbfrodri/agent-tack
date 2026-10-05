#!/usr/bin/env python3
"""Writes index.html for a `tack shots` folder: before and after screenshots side by side, per
page and width, followed by score.md when a reviewer wrote one.

Usage: lib/shots-index.py <folder>
"""
import html
import sys
from pathlib import Path

WIDTHS = ("mobile", "desktop")


def pages(folder):
    names = set()
    for phase in ("before", "after"):
        for image in (folder / phase).glob("*.png"):
            stem, _, width = image.stem.rpartition("-")
            if width in WIDTHS:
                names.add(stem)
    return sorted(names)


def cell(folder, phase, page, width):
    relative = f"{phase}/{page}-{width}.png"
    if not (folder / relative).exists():
        return "<td class=missing>none</td>"
    src = html.escape(relative, quote=True)
    return f'<td><a href="{src}"><img src="{src}" alt="{html.escape(f"{page} {width} {phase}")}"></a></td>'


def main(folder):
    rows = []
    for page in pages(folder):
        for width in WIDTHS:
            rows.append(f"<tr><th>{html.escape(page)}<br><small>{width}</small></th>"
                        f"{cell(folder, 'before', page, width)}{cell(folder, 'after', page, width)}</tr>")
    score = folder / "score.md"
    score_html = (f"<h2>Score</h2><pre>{html.escape(score.read_text(encoding='utf-8', errors='replace'))}</pre>"
                  if score.exists() else "<p>No score yet: the reviewer writes score.md here.</p>")
    title = html.escape(folder.name)
    (folder / "index.html").write_text(encoding="utf-8", data=f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Screenshots {title}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; text-align: left; }}
img {{ max-width: 100%; height: auto; display: block; }}
td.missing {{ color: #777; }}
pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 12px; }}
@media (prefers-color-scheme: dark) {{ body {{ background: #111; color: #eee; }} pre {{ background: #222; }} th, td {{ border-color: #444; }} }}
</style></head><body>
<h1>Screenshots {title}</h1>
<table><thead><tr><th>Page</th><th>Before</th><th>After</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table>
{score_html}
</body></html>
""")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
