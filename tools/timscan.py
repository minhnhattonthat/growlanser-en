"""timscan.py: find PS1 TIM images in a file and render them (graphics-text survey, docs/re/graphics.md).

    python -X utf8 tools/timscan.py FILE [--render OUTDIR]     list (offset, bpp, w, h); --render writes PNGs
Only TIMs with sane headers are listed (magic 0x10, flags 0/1/2/3 +CLUT 8, block sizes consistent).
"""
import os
import struct
import sys

import numpy as np
from PIL import Image


def scan(d):
    i = 0
    n = len(d)
    while True:
        i = d.find(b"\x10\x00\x00\x00", i)
        if i < 0 or i + 20 > n:
            return
        if i % 4 == 0:
            flags = struct.unpack_from("<I", d, i + 4)[0]
            if flags & ~0xB == 0 and (flags & 3) != 3 or flags in (2, 3):
                t = parse(d, i, flags)
                if t:
                    yield t
        i += 4


def parse(d, i, flags):
    p = i + 8
    clut = None
    try:
        if flags & 8:
            blen, cx, cy, cw, ch = struct.unpack_from("<IHHHH", d, p)
            if blen != 12 + cw * ch * 2 or not (0 < cw <= 1024 and 0 < ch <= 512):
                return None
            clut = np.frombuffer(d, "<u2", cw * ch, p + 12).reshape(ch, cw)
            p += blen
        blen, x, y, w, h = struct.unpack_from("<IHHHH", d, p)
        if blen != 12 + w * h * 2 or not (0 < w <= 1024 and 0 < h <= 512) or p + blen > len(d):
            return None
        return dict(off=i, bpp=(4, 8, 16, 24)[flags & 3], w=w, h=h, clut=clut,
                    pix=np.frombuffer(d, "<u2", w * h, p + 12).reshape(h, w), end=p + blen)
    except struct.error:
        return None


def rgb(c):
    return np.stack([(c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3], -1).astype("uint8")


def image(t):
    px = t["pix"]
    if t["bpp"] == 4:
        idx = np.stack([(px >> (4 * k)) & 15 for k in range(4)], -1).reshape(px.shape[0], -1)
    elif t["bpp"] == 8:
        idx = np.stack([px & 255, px >> 8], -1).reshape(px.shape[0], -1)
    else:
        return Image.fromarray(rgb(px))
    pal = t["clut"][0] if t["clut"] is not None else (np.arange(256, dtype="<u2") * 0x421 % 0x8000)
    if len(pal) < idx.max() + 1:
        pal = np.resize(pal, idx.max() + 1)
    return Image.fromarray(rgb(pal[idx]))


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    out = sys.argv[sys.argv.index("--render") + 1] if "--render" in sys.argv else None
    if out:
        os.makedirs(out, exist_ok=True)
    k = 0
    for t in scan(d):
        print("%08X %2dbpp %4dx%-4d" % (t["off"], t["bpp"], t["w"], t["h"]))
        if out:
            image(t).save(os.path.join(out, "%08X.png" % t["off"]))
        k += 1
    print("tims", k, file=sys.stderr)
