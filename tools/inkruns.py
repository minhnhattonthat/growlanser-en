"""Column runs of bright ink in a screenshot band (glyph extents for graphics-text redraws).

    python -X utf8 tools/inkruns.py SHOT.png Y0 Y1 [--x0 0] [--x1 W] [--min 600]

Prints each run of columns x0-x1 where some pixel in rows Y0..Y1 has R+G+B >= --min.
"""
import argparse

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("png")
ap.add_argument("y0", type=int)
ap.add_argument("y1", type=int)
ap.add_argument("--x0", type=int, default=0)
ap.add_argument("--x1", type=int)
ap.add_argument("--min", type=int, default=600)
a = ap.parse_args()
im = Image.open(a.png).convert("RGB")
px = im.load()
x1 = a.x1 or im.width
runs, start = [], None
for x in range(a.x0, x1 + 1):
    ink = x < x1 and any(sum(px[x, y]) >= a.min for y in range(a.y0, a.y1 + 1))
    if ink and start is None:
        start = x
    if not ink and start is not None:
        runs.append((start, x - 1))
        start = None
print(" ".join("%d-%d" % r for r in runs))
