"""Centring check for every centred box in warp shots (phase 8 inkbox gate).

    python -X utf8 tools/inkqa.py DIR [DIR ..]      (warp_all.py output folders, --shot-every 20 recommended)

Boxes it finds by colour, one measurement per distinct box per folder:
  bubble  field-menu bubbles (cream 0xEEDEC5 inside), text = dark ink: inkcheck.py seed flood
  popup   place popup / scene caption (border 0x836252, dark inside), text = 0xC5A473
Animation frames (popup open/close scale) are skipped: a box counts only once it is the same in two frames
in a row. Exit 1 if any box is off-centre by more than 2 px.
"""
import glob
import os
import subprocess
import sys

from PIL import Image

from skill import SKILL

HERE = os.path.dirname(os.path.abspath(__file__))
CREAM, BORDER, INK = (0xEE, 0xDE, 0xC5), (131, 98, 82), (197, 164, 115)


def boxes(im):
    W, H = im.size
    px = im.load()
    out = []
    cream = [(x, y) for y in range(H) for x in range(160, W) if px[x, y] == CREAM]
    if len(cream) > 50:
        out.append(("bubble", (min(x for x, _ in cream) + 1, min(y for _, y in cream) + 1)))
    ink = [(x, y) for y in range(H) for x in range(W) if px[x, y] == INK]
    if len(ink) > 40:
        y = (min(p[1] for p in ink) + max(p[1] for p in ink)) // 2
        row = [x for x, yy in ink if yy == y] or [ink[0][0]]
        l, r = min(row), max(row)
        while l > 0 and px[l, y] != BORDER:
            l -= 1
        while r < W - 1 and px[r, y] != BORDER:
            r += 1
        top, bot = y, y
        while top > 0 and px[l + 1, top] != BORDER and px[l + 1, top][0] < 120:
            top -= 1
        while bot < H - 1 and px[l + 1, bot] != BORDER and px[l + 1, bot][0] < 120:
            bot += 1
        if 0 < l and r < W - 1 and r - l < 300:
            out.append(("popup", (l + 1, top + 1, r - l - 1, bot - top - 1)))
    return out


def todo(d):
    """[(kind, frame, geometry)]: bubbles once stable for two frames; popups at the widest frame of each run
    (the open/close animation scales the box, and a popup may be fully open in one 20-frame shot only)."""
    out, seen, prev, run = [], set(), {}, None
    for f in sorted(glob.glob(os.path.join(d, "f*.png"))):
        im = Image.open(f).convert("RGB")
        if im.width < 300:
            continue
        cur = dict(boxes(im))
        g = cur.get("bubble")
        if g and prev.get("bubble") == g and g not in seen:
            seen.add(g)
            out.append(("bubble", f, g))
        g = cur.get("popup")
        if g and (run is None or g[2] > run[2][2]):
            run = ("popup", f, g)
        if not g and run:
            out.append(run)
            run = None
        prev = cur
    return out + ([run] if run else [])


def main(dirs):
    bad = 0
    for d in dirs:
        for kind, f, geo in todo(d):
            if kind == "bubble":
                cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "inkcheck.py"), f, "%d,%d" % geo]
            else:
                cmd = [sys.executable, "-X", "utf8", f"{SKILL}/scripts/inkbox.py", f, "%d,%d,%d,%d" % geo,
                       "--ink", "%d,%d,%d" % INK, "--diff", "30"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            bad |= r.returncode == 1
            print(kind, os.path.relpath(f), r.stdout.strip())
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
