"""Find where each 16x16 screen cell's pixels come from in an 8bpp VRAM texture area, without knowing the CLUT:
a texture cell matches when every texel index maps to one screen colour.

    python -X utf8 tools/cellsrc.py SHOT.png VRAM.bin OUT.json [--hw-x 640] [--width 512] [--cells x0,y0,x1,y1]
                                    [--step 16]

SHOT = an emu.py shot (same frame as the VRAM dump, 1:1 texels), VRAM.bin = ppudump's 1024x512 halfword dump.
--hw-x / --width: texture area (VRAM halfword x, 8bpp texels wide). --step: texture search grid (1 = any offset).
OUT: {"cx,cy": [u, v] or null} in texels from the area's top-left. Used for the title (G1, docs/re/graphics.md).
"""
import argparse
import json

import numpy as np
from PIL import Image


def consistent(cell, t):
    m = {}
    for a, b in zip(t.ravel().tolist(), cell.ravel().tolist()):
        if m.setdefault(a, b) != b:
            return False
    return len(m) > 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("vram")
    ap.add_argument("out")
    ap.add_argument("--hw-x", type=int, default=640)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--cells")
    ap.add_argument("--step", type=int, default=16)
    a = ap.parse_args()
    scr = np.array(Image.open(a.shot).convert("RGB")).astype(np.int32)
    key = scr[:, :, 0] * 65536 + scr[:, :, 1] * 256 + scr[:, :, 2]
    v = np.frombuffer(open(a.vram, "rb").read(), dtype=np.uint8).reshape(-1, 2048)  # Redux dumps 1024 rows
    tex = v[:, a.hw_x * 2:a.hw_x * 2 + a.width]
    H, W = key.shape
    x0, y0, x1, y1 = map(int, a.cells.split(",")) if a.cells else (0, 0, W // 16, H // 16)
    res = {}
    for cy in range(y0, y1):
        for cx in range(x0, x1):
            cell = key[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
            if len(np.unique(cell)) < 4:
                continue
            hit = None
            for ty in range(0, 512 - 15, a.step):
                for tx in range(0, a.width - 15, a.step):
                    if consistent(cell, tex[ty:ty + 16, tx:tx + 16]):
                        hit = [tx, ty]
                        break
                if hit:
                    break
            res["%d,%d" % (cx, cy)] = hit
    json.dump(res, open(a.out, "w"), indent=0)
    print(sum(1 for h in res.values() if h), "of", len(res), "cells found")


if __name__ == "__main__":
    main()
