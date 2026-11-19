"""tutorialgfx.py: English G7, the LLM magic class tutorial's status picture (MAP pair 575 = entries 1150/1151).

Rosaria's magic class (scene 1, `tut_status` warp) shows a picture of a status screen with baked Japanese: the
equipment names, the resistance grid (affinity labels + element kanji, like G2/G3) and a "STATUS画面" callout.
Entry 1150 (header): offset table at 0x18; CLUT upload records at 0x74 (12 bytes: u16 data offset, ?, VRAM x, y,
width, rows) with the CLUTs at 0xB0 (5 x 256 colours, VRAM rows 480-484); the picture's tilemap at 0x11CC (20 x 15
u16 words, 16 px cells, 0xFFFF empty; word = 0x2000 | page << 8 | cell row << 4 | cell column, page 0 = upload
record 0 (128 texels wide), page 1 = record 1 (64 wide)); upload records at the last table offset (credits.records).
Entry 1151 = the texture (8bpp). An edit is a 320x240 PNG of the tilemap layer; every changed pixel goes back to its
cell's texel as the nearest CLUT index (title.py's method).

    python -X utf8 tools/tutorialgfx.py render OUT.png [--clut K]    the tilemap layer as the game draws it
    python -X utf8 tools/tutorialgfx.py draw                         -> gfx/tutorial/status_en.png (edits below)
    python -X utf8 tools/tutorialgfx.py check                        apply + render back, report
"""
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import credits  # noqa: E402
import dat  # noqa: E402

HEAD, BODY = 1150, 1151
MAPOFF, MW, MH = 0x11CC, 20, 15
CLUT_K = 1  # the tilemap's CLUT: matches 95% of the warp shot's pixels (the rest are sprites drawn on top)
PNG = ROOT / "gfx" / "tutorial" / "status_en.png"


def load(map_bytes=None):
    m = map_bytes or credits.MAP.read_bytes()
    return dat.entry(m, HEAD), dat.entry(m, BODY)


def cluts(head):
    out = []
    for k in range(5):
        o = 0xB0 + 512 * k
        hw = struct.unpack_from("<256H", head, o)
        out.append([TRANS if c == 0 else ((c & 31) << 3 | (c & 31) >> 2, (c >> 5 & 31) << 3 | (c >> 5 & 31) >> 2,
                                          (c >> 10 & 31) << 3 | (c >> 10 & 31) >> 2) for c in hw])
    return out


TRANS = (255, 0, 255)  # CLUT colour 0x0000 = transparent (the name box shows the background layer through it)

# "Thick Clothes" runs past 厚手の服 into the empty cell (7, 11). Every texture cell is in use (this tilemap, or the
# background layer at head 0xF74: words 0x00XX, CLUT 0, a gradient + panels), but "Wizard Rod" is shorter than
# ウィザードロッド, so cells (8, 10) and (9, 10) end up fully transparent: (9, 10) shares (8, 10)'s cell and its own
# (0x2076) goes to (7, 11). apply() checks that every screen cell sharing a texture cell wants the same pixels.
REMAP = {(9, 10): (0x2076, 0x2077), (7, 11): (0xFFFF, 0x2076)}  # cell: (original word, English word)


def head_en(head):
    out = bytearray(head)
    for (cx, cy), (old, new) in REMAP.items():
        o = MAPOFF + 2 * (cy * MW + cx)
        assert struct.unpack_from("<H", head, o)[0] == old, (cx, cy)
        struct.pack_into("<H", out, o, new)
    return bytes(out)


def tilemap(head):
    return struct.unpack_from(f"<{MW * MH}H", head, MAPOFF)


def texel(recs, page, u, v):
    """Offset in entry 1151 of texel (u, v) of a page."""
    r = recs[page]
    assert 0 <= u < r["w"] and 0 <= v < r["h"], (page, u, v)
    return r["sec"] * credits.SECTOR + v * r["w"] + u


def cells(head):
    """[(cx, cy, page, u0, v0)] for every drawn cell."""
    out = []
    for i, w in enumerate(tilemap(head)):
        if w == 0xFFFF:
            continue
        assert w >> 9 == 0x10, hex(w)
        out.append((i % MW, i // MW, w >> 8 & 1, (w & 15) * 16, (w >> 4 & 15) * 16))
    return out


def render(head, body, k=CLUT_K):
    recs = credits.records(head)
    pal = cluts(head)[k]
    img = np.zeros((MH * 16, MW * 16, 3), np.uint8)
    for cx, cy, p, u0, v0 in cells(head):
        for dy in range(16):
            for dx in range(16):
                img[cy * 16 + dy, cx * 16 + dx] = pal[body[texel(recs, p, u0 + dx, v0 + dy)]]
    return Image.fromarray(img)


def apply(head, body, png, k=CLUT_K):
    """Body bytes with png's changed pixels written as CLUT indices. Raises when two screen cells that share a
    texture cell want different pixels, or a colour is far from the CLUT."""
    recs = credits.records(head)
    pal = np.array(cluts(head)[k])
    want = np.array(png.convert("RGB")).astype(int)
    out = bytearray(body)
    owner = {}
    far = 0
    for cx, cy, p, u0, v0 in cells(head):
        for dy in range(16):
            for dx in range(16):
                o = texel(recs, p, u0 + dx, v0 + dy)
                rgb = want[cy * 16 + dy, cx * 16 + dx]
                d = ((pal - rgb) ** 2).sum(1)
                i = int(body[o]) if d[body[o]] == 0 else int(d.argmin())
                far = max(far, int(d[i]))
                if owner.setdefault(o, i) != i:
                    raise ValueError(f"tutorialgfx: texel {o:#x} shared by cells wanting {owner[o]} and {i} ({cx},{cy})")
                out[o] = i
    if far > 48 ** 2:
        raise ValueError(f"tutorialgfx: a colour is {far ** .5:.0f} away from the CLUT")
    return bytes(out)


def patch(map_dat, log=None):
    """Write the English picture into entries HEAD (tilemap words) and BODY of map_dat (bytearray, in place); log as
    insert.log_put."""
    head, body = load(bytes(map_dat))
    head2 = head_en(head)
    for i, old, new in ((HEAD, head, head2), (BODY, body, apply(head2, body, Image.open(PNG)))):
        off = dat.entries(map_dat)[i][0] * dat.SECTOR
        if log is not None:
            log.append(("MAP.DAT", off, bytes(old), new, "tutorialgfx.patch"))
        map_dat[off:off + len(new)] = new


# --- draw ---------------------------------------------------------------------------------------------------------
# The picture is a screenshot of the status screen: the grid is the same art as G2/G3 at the same screen place, so
# it gets statusgfx's words and pictograms (D15). Icon cell origin (176 + 40c, 160 + 16r), label (192 + 40c,
# 162 + 16r), measured on the English gear_status shot. Equipment names: the game's English font.
GRID = ["VITAL", "HALF", "VITAL", "WEAK", "EVEN", "WEAK", "EVEN", "DRAIN", "NULL"]  # 急所 半減 急所 / 弱点 普通 弱点 / 普通 吸収 無効
NAMES = ["Wizard Rod", "Thick Clothes", "Mirror Earrings"]  # exe.items.0022 / 0098 / 0150
NAME_X, NAME_X1 = 57, 164  # the names' column (icons end at 52, the box's inner edge is 166)


def mode(px):
    vals, counts = np.unique(px.reshape(-1, 3), axis=0, return_counts=True)
    return vals[counts.argmax()]


def stamp(img, art, top, left, ink, bg_rows, rows, cols):
    h, w = len(art), len(art[0])
    t0, l0 = top + (len(rows) - h) // 2, left + (len(cols) - w) // 2
    for r in rows:
        for x in cols:
            on = 0 <= r - t0 < h and 0 <= x - l0 < w and art[r - t0][x - l0] == "#"
            img[r, x] = ink if on else bg_rows[r]


def draw_grid(img):
    import statusgfx
    icons = [img[160 + 16 * (k // 3) + 2:160 + 16 * (k // 3) + 13, 176 + 40 * (k % 3) + 3:176 + 40 * (k % 3) + 14]
             for k in range(9)]
    # plate gradient per row: the commonest colour of that row over all nine plates (each kanji covers other pixels)
    rows_ = [np.concatenate([a[i] for a in icons]).astype(int) for i in range(11)]
    plate = [mode(rw[rw.sum(1) >= 290]).astype(np.uint8) for rw in rows_]  # kanji shades are <= 254, plate >= 302
    dark = min((a.reshape(-1, 3)[a.reshape(-1, 3).sum(1).argmin()] for a in icons), key=lambda v: v.sum()).copy()
    for k in range(9):
        c, r = k % 3, k // 3
        x, y = 176 + 40 * c, 160 + 16 * r
        rows, cols = list(range(y + 2, y + 13)), list(range(x + 3, x + 14))
        stamp(img, statusgfx.ICONS[k], rows[0], cols[0], dark, dict(zip(rows, plate)), rows, cols)
        x, y = 192 + 40 * c, 162 + 16 * r
        rows, cols = list(range(y + 1, y + 10)), list(range(x + 2, x + 21))
        area = img[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1].reshape(-1, 3).astype(int)
        bgc = mode(area[area.sum(1) < 120]).copy()
        vals, counts = np.unique(area, axis=0, return_counts=True)
        score = [(v.max() - v.min()) * 2 + v.sum() if n >= 3 else -1 for v, n in zip(vals, counts)]
        ink = vals[int(np.argmax(score))].copy()
        stamp(img, statusgfx.word(GRID[k]), rows[0], cols[0], ink, {rr: bgc for rr in rows}, rows, cols)


def draw_names(img):
    import enfont
    font = enfont.load()
    band = img[158:212, NAME_X:NAME_X1].astype(int)
    ink = (band.sum(2) > 200) & ~(band == TRANS).all(2)
    ink_rows = np.flatnonzero(ink.sum(1) > 0) + 158
    lines = np.split(ink_rows, np.flatnonzero(np.diff(ink_rows) > 1) + 1)
    lines = [ln for ln in lines if len(ln) > 4]
    assert len(lines) == 3, [(ln[0], ln[-1]) for ln in lines]
    area = band[lines[0][0] - 158:lines[0][-1] - 157].reshape(-1, 3)
    area = area[ink[lines[0][0] - 158:lines[0][-1] - 157].ravel()]
    inks = [v for v, n in sorted(zip(*np.unique(area, axis=0, return_counts=True)), key=lambda t: -t[1])[:2]]
    # the Japanese and its 1 px black drop shadow (opaque, unlike the transparent box interior) go
    img[lines[0][0] - 1:lines[-1][-1] + 3, NAME_X:NAME_X1 + 2] = TRANS
    for ln, text in zip(lines, NAMES):
        x = NAME_X + 2
        for ch in text:
            top, rows, adv = font[ch]
            for shadow in (1, 0):
                for dy, row in enumerate(rows):
                    for dx, p in enumerate(row):
                        if p == "#":
                            yy, xx = ln[0] + top + dy + shadow, x + dx + shadow
                            img[yy, xx] = (0, 0, 0) if shadow else inks[(xx + yy) & 1]  # the picture's two-tone dither
            x += adv
        assert x <= NAME_X1, text


def draw():
    head, body = load()
    img = np.array(render(head_en(head), body))  # remapped cells show other cells' pixels until the names are erased
    draw_names(img)
    drawn = {(cx, cy) for cx, cy, *_ in cells(head_en(head))}
    for cy in range(MH):
        for cx in range(MW):
            if (cx, cy) not in drawn:  # no cell there (render() leaves it black): the erase may cover it, ink may not
                c = img[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
                assert ((c == TRANS).all(2) | (c == 0).all(2)).all(), ("ink in an empty cell", cx, cy)
                c[:] = 0
    draw_grid(img)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(PNG)
    return PNG


def check():
    head, body = load()
    head = head_en(head)
    new = apply(head, body, Image.open(PNG))
    back = np.array(render(head, new))
    want = np.array(Image.open(PNG).convert("RGB"))
    diff = int((np.abs(back.astype(int) - want).max(2) > 24).sum())
    print(f"{sum(a != b for a, b in zip(body, new))} texels changed, {diff} pixels differ after apply + render")
    return diff


def main(argv):
    if argv and argv[0] == "render":
        head, body = load()
        k = int(argv[argv.index("--clut") + 1]) if "--clut" in argv else CLUT_K
        render(head, body, k).save(argv[1])
    elif argv and argv[0] == "draw":
        print(draw())
    elif argv and argv[0] == "check":
        sys.exit(1 if check() else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
