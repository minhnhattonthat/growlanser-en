"""title.py: English title screen (G1, docs/re/graphics.md "G1 title layout").

The title is one mosaic of 16x16 screen cells, each drawn from a 16x16 cell of the 8bpp texture in MAP.DAT entry 1161.
gfx/title/cells.json holds the cell map (screen cell -> texel u, v) and the CLUT (texel index -> RGB), both read off a
cold-boot shot + VRAM dump. An edit is a whole-screen PNG (gfx/title/title_en.png): every mapped pixel whose colour
differs from the original is written back as the CLUT index of that colour.

    python -X utf8 tools/title.py cells SHOT.png VRAM.bin CELLMAP.json   -> gfx/title/cells.json (cellsrc.py output)
    python -X utf8 tools/title.py draw SHOT.png                          -> gfx/title/title_en.png (edits below)
    python -X utf8 tools/title.py check                                  apply + render back, report

insert.patched calls patch(map_dat) for the build.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import dat  # noqa: E402

ENTRY = 1161
CELLS = ROOT / "gfx" / "title" / "cells.json"
PNG = ROOT / "gfx" / "title" / "title_en.png"
TREE = ROOT / "work" / "disc1" / "tree"


def tex_off(u, v):
    """Texel (u, v) from VRAM hw x 640, y 0 -> offset in entry 1161 (4 upload rects back to back)."""
    if v < 256:
        return v * 256 + u if u < 256 else 65536 + v * 128 + u - 256
    if u < 64 and v < 352:
        return 98304 + (v - 256) * 64 + u
    if 128 <= u < 320 and v < 336:
        return 104448 + (v - 256) * 192 + u - 128
    raise ValueError((u, v))


def load():
    d = json.loads(CELLS.read_text(encoding="utf-8"))
    cells = {tuple(map(int, k.split(","))): v for k, v in d["cells"].items() if v}
    clut = {int(k): tuple(v) for k, v in d["clut"].items()}
    return cells, clut


def render(e, cells, clut, base=None):
    """Screen image from entry bytes; unmapped cells from base (or black)."""
    img = np.array(base.convert("RGB")) if base else np.zeros((238, 640, 3), np.uint8)
    for (cx, cy), (u, v) in cells.items():
        for dy in range(16):
            for dx in range(16):
                img[cy * 16 + dy, cx * 16 + dx] = clut[e[tex_off(u + dx, v + dy)]]
    return Image.fromarray(img)


def apply(e, cells, clut, png):
    """Entry bytes with png's colours written as CLUT indices. Raises on a colour far from every CLUT entry."""
    out = bytearray(e)
    want = np.array(png.convert("RGB")).astype(int)
    pal = np.array([clut[i] for i in sorted(clut)])
    idx = sorted(clut)
    far = 0
    for (cx, cy), (u, v) in cells.items():
        for dy in range(16):
            for dx in range(16):
                rgb = tuple(want[cy * 16 + dy, cx * 16 + dx])
                o = tex_off(u + dx, v + dy)
                if clut[e[o]] == rgb:
                    continue
                d = ((pal - rgb) ** 2).sum(1)
                far = max(far, int(d.min()))
                out[o] = idx[int(d.argmin())]
    if far > 48 ** 2:
        raise ValueError(f"title: a colour is {far ** .5:.0f} away from the CLUT")
    return bytes(out)


def patch(map_dat, log=None):
    """Write the English title into entry ENTRY of map_dat (a bytearray, in place, same size); log as insert.log_put."""
    cells, clut = load()
    start, n = dat.entries(map_dat)[ENTRY]
    off = start * dat.SECTOR
    old = bytes(dat.entry(map_dat, ENTRY))
    new = apply(old, cells, clut, Image.open(PNG))
    if log is not None:
        log.append(("MAP.DAT", off, old, new, "title.patch"))
    map_dat[off:off + len(new)] = new


# --- cmd: cells -------------------------------------------------------------------------------------------------

def cmd_cells(shot, vram, cellmap):
    scr = np.array(Image.open(shot).convert("RGB"))
    e = dat.entry((TREE / "MAP.DAT").read_bytes(), ENTRY)
    v8 = np.frombuffer(open(vram, "rb").read(), np.uint8).reshape(-1, 2048)
    cm = json.loads(Path(cellmap).read_text(encoding="utf-8"))
    clut = {}
    for k, uv in cm.items():
        if not uv:
            continue
        cx, cy = map(int, k.split(","))
        u, v = uv
        for dy in range(16):
            for dx in range(16):
                i = e[tex_off(u + dx, v + dy)]
                assert i == v8[v + dy, 1280 + u + dx], (k, dx, dy)  # entry == VRAM
                rgb = tuple(int(c) for c in scr[cy * 16 + dy, cx * 16 + dx])
                assert clut.setdefault(i, rgb) == rgb, (k, i, rgb, clut[i])
    CELLS.parent.mkdir(parents=True, exist_ok=True)
    CELLS.write_text(json.dumps({"cells": cm, "clut": {str(i): clut[i] for i in sorted(clut)}}), encoding="utf-8")
    print(len(clut), "CLUT colours,", sum(1 for x in cm.values() if x), "cells ->", CELLS)


# --- cmd: draw ----------------------------------------------------------------------------------------------------
# Interior masks of the (c) line's lettering, 7 rows high (screen rows 166-172). Each letter is drawn as: dark
# bevelled interior, a cream ring 2 px wide (1 px above/below), a 1 px black outline, a darkened shadow below/right.
GLYPHS = {  # stems 2 px, bars 1-2 rows, 8 wide: the weight of the original ATLUS / 1999
    "C": [".#######", "##....##", "##......", "##......", "##......", "##....##", ".#######"],
    "A": ["...##...", "..####..", ".##..##.", "##....##", "########", "##....##", "##....##"],
    "R": ["#######.", "##....##", "##....##", "#######.", "##..##..", "##...##.", "##....##"],
    "I": ["##"] * 7,
    "E": ["########", "##......", "##......", "#######.", "##......", "##......", "########"],
    "S": [".#######", "##......", "##......", ".######.", "......##", "......##", "#######."],
    "O": [".######.", "##....##", "##....##", "##....##", "##....##", "##....##", ".######."],
    "F": ["########", "##......", "##......", "#######.", "##......", "##......", "##......"],
    "T": ["########", "...##...", "...##...", "...##...", "...##...", "...##...", "...##..."],
    "1": [".##.", "###.", ".##.", ".##.", ".##.", ".##.", "####"],
    "9": [".######.", "##....##", "##....##", ".#######", "......##", "##....##", ".######."],
}
TOP = 166  # first interior row
GAP, SPACE = 3, 8


def dil(m, dx, dy):
    o = m.copy()
    for y in range(-dy, dy + 1):
        for x in range(-dx, dx + 1):
            o |= np.roll(np.roll(m, y, 0), x, 1)
    return o


def letter_line(img, text, x0):
    """Draw text into img (HxWx3 int array) starting with the first letter's outline at x0. Returns the end x."""
    H, W, _ = img.shape
    L = np.zeros((H, W), bool)
    x = x0 + 4  # outline 1 + anti-alias 1 + ring 2
    for ch in text:
        if ch == " ":
            x += SPACE
            continue
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, p in enumerate(row):
                if p == "#":
                    L[TOP + r, x + c] = True
        x += len(g[0]) + 8 + GAP
    ring = (dil(L, 2, 0) | dil(L, 1, 1)) & ~L  # rounded corners
    body = L | ring
    edge = dil(body, 1, 0) & ~body  # anti-alias column
    out = dil(body | edge, 1, 1) & ~(body | edge)
    fig = body | edge | out
    shadow = (np.roll(fig, 2, 0) | np.roll(np.roll(fig, 1, 0), 1, 1)) & ~fig
    img[shadow] = img[shadow] * 2 // 5
    img[out] = (0, 0, 0)
    img[edge] = (115, 98, 90)
    for y, xx in zip(*np.nonzero(ring)):
        img[y, xx] = ((222, 197, 180) if not body[y - 1, xx] else (230, 205, 189) if not body[y + 1, xx]
                      else (238, 213, 205))
    for y, xx in zip(*np.nonzero(L)):  # bevel: lit top edge, soft left edge, black core
        if not L[y - 1, xx] and L[y + 1, xx]:
            img[y, xx] = (115, 98, 90)
        elif not L[y, xx - 1] and L[y, xx + 1] or not L[y + 1, xx] and L[y - 1, xx]:
            img[y, xx] = (57, 49, 49)
        else:
            img[y, xx] = (0, 0, 0)
    return x - GAP - 4


def cmd_draw(shot):
    img = np.array(Image.open(shot).convert("RGB")).astype(int)
    src = img.copy()
    # 1. katakana subtitle (x 38-252, y 97-119): marble from 22 rows below, then the logo bar's bottom edge again
    for x in range(36, 256):
        for y in range(99, 121):
            img[y, x] = src[y + 22, x]
        if x >= 47:
            img[96:99, x] = src[96:99, 300]
    # the light marble patch right of the subtitle (x 256+) had its left edge hidden: mirror it in, ragged edge
    for y in range(99, 121):
        b = 242 + int(6 * np.sin(y * 0.3) + 2 * np.sin(y * 0.9))
        for x in range(b, 256):
            img[y, x] = src[y, 511 - x]
    # 2. (c) line: erase キャリアソフト 1999 (x 338-635, glyph band rows 161-178) with marble from x 0-159, mirrored
    # back and forth (no hard seam inside), starting where the source column best matches the column left of 338
    band = slice(161, 179)
    s = min(range(160), key=lambda c: np.abs(src[band, c] - src[band, 337]).sum())
    for x in range(338, 636):
        k = (s + x - 338) % 318
        img[band, x] = src[band, k if k < 159 else 317 - k]
    end = letter_line(img, "CARRIER SOFT 1999", 342)
    print("(c) line ends at x", end)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img.astype(np.uint8)).save(PNG)
    print("->", PNG)


def cmd_check():
    cells, clut = load()
    e = dat.entry((TREE / "MAP.DAT").read_bytes(), ENTRY)
    png = Image.open(PNG)
    new = apply(e, cells, clut, png)
    got = np.array(render(new, cells, clut)).astype(int)
    want = np.array(png.convert("RGB")).astype(int)
    m = np.zeros(want.shape[:2], bool)
    for cx, cy in cells:
        m[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16] = True
    err = np.abs(got - want).sum(2)[m]
    print(f"{sum(a != b for a, b in zip(e, new))} texels changed, max colour error {err.max()}, "
          f"pixels off {int((err > 0).sum())}")
    render(new, cells, clut).save(ROOT / "work" / "gfx" / "title" / "check.png")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"cells": cmd_cells, "draw": cmd_draw, "check": cmd_check}[cmd](*args)
