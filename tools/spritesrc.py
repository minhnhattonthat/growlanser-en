"""spritesrc.py: map every screen pixel of a sprite-built screen to its 8bpp VRAM texel, without the CLUT.

For screens drawn from many sprites at arbitrary positions (G7 tutorial status picture), where cellsrc.py's fixed
16 px screen grid straddles sprite edges. Every 8x8 screen patch (step 4) is searched over the whole texture area:
differing screen colours must be differing texel indices (vectorised filter), then the full index -> colour
consistency check. Each patch with exactly one hit votes its offset (u - x, v - y) for its pixels; a pixel takes
its most voted offset, and only when its texel index agrees with that offset group's index -> colour map.

    python -X utf8 tools/spritesrc.py SHOT.png VRAM.bin OUT.json [--hw-x 320] [--width 640] [--rect x,y,w,h]

OUT: {"px": {"x,y": [u, v]}, "groups": {"du,dv": {"index": [r, g, b]}}} (u, v in texels from hw-x).
"""
import argparse
import json
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

P = 8


def consistent(t, cell):
    """Each texel index's screen colours agree within the dither noise (2 levels of 5 bits per channel)."""
    order = np.argsort(t, kind="stable")
    ts, cs = t[order], cell[order]
    cuts = np.flatnonzero(np.diff(ts)) + 1
    for g in np.split(cs, cuts):
        if len(g) > 1 and (g.max(0) - g.min(0)).max() > 2:
            return False
    return True


def search(lvl, tex, x, y):
    """Texture positions where screen patch (x, y) is consistent; [] if the patch is too plain.
    lvl = screen colours as 5-bit levels (h, w, 3); PS1 dithering moves each channel by up to 1 level."""
    cell = lvl[y:y + P, x:x + P].reshape(-1, 3)
    bright = cell.sum(1)
    if bright.max() - bright.min() < 6:
        return []
    H, W = tex.shape
    mask = np.ones((H - P + 1, W - P + 1), bool)
    order = np.argsort(bright, kind="stable")
    pairs = [(order[i], order[-1 - j]) for i in range(4) for j in range(4)]
    pairs += [(a, b) for a, b in zip(order[::7], order[3::7])]
    for a, b in pairs:
        if np.abs(cell[a] - cell[b]).max() <= 2:
            continue
        (ya, xa), (yb, xb) = divmod(int(a), P), divmod(int(b), P)
        mask &= tex[ya:ya + H - P + 1, xa:xa + W - P + 1] != tex[yb:yb + H - P + 1, xb:xb + W - P + 1]
        if not mask.any():
            return []
    hits = []
    for ty, tx in zip(*np.nonzero(mask)):
        if consistent(tex[ty:ty + P, tx:tx + P].ravel(), cell):
            hits.append((int(tx), int(ty)))
            if len(hits) > 1:
                break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("vram")
    ap.add_argument("out")
    ap.add_argument("--hw-x", type=int, default=320)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--rect")
    a = ap.parse_args()
    scr = np.array(Image.open(a.shot).convert("RGB")).astype(np.int64)
    lvl = scr >> 3
    v = np.frombuffer(open(a.vram, "rb").read(), np.uint8).reshape(-1, 2048)[:512]
    tex = v[:, a.hw_x * 2:a.hw_x * 2 + a.width].astype(np.int32)
    H, W = lvl.shape[:2]
    x0, y0, w, h = map(int, a.rect.split(",")) if a.rect else (0, 0, W, H)
    votes = defaultdict(Counter)
    for y in range(y0, min(y0 + h, H) - P + 1, 4):
        for x in range(x0, min(x0 + w, W) - P + 1, 4):
            hits = search(lvl, tex, x, y)
            if len(hits) == 1:
                d = (hits[0][0] - x, hits[0][1] - y)
                for yy in range(y, y + P):
                    for xx in range(x, x + P):
                        votes[(xx, yy)][d] += 1
    groups = defaultdict(dict)
    px = {}
    for (x, y), c in votes.items():
        for d, _ in c.most_common():
            u, t = x + d[0], y + d[1]
            g = groups[d]
            i, col = int(tex[t, u]), tuple(int(c) for c in scr[y, x])
            if max(abs(p - q) >> 3 for p, q in zip(g.setdefault(i, col), col)) <= 2:
                px[(x, y)] = (u, t, d)
                break
    out = {"px": {f"{x},{y}": [u, t] for (x, y), (u, t, d) in px.items()},
           "groups": {f"{d[0]},{d[1]}": {str(i): list(c) for i, c in g.items()} for d, g in groups.items()}}
    json.dump(out, open(a.out, "w"))
    print(len(px), "of", w * h, "pixels mapped,", len(groups), "offset groups ->", a.out)


if __name__ == "__main__":
    main()
