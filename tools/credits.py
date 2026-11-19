"""credits.py: the ending credits art (G5), MAP.DAT entry 1257 with its upload records in entry 1256.

Entry 1256 ends (offset table's last field, 0x13AC) with 12-byte records u16 sector, u16 flags, VRAM x, VRAM y,
width px, rows: flags low byte = sectors in entry 1257, 0x100 = 8bpp, else 4bpp (verified: sizes fit the sector
counts exactly). Pages 2-18 are 4bpp 256-px credit pages (white text, staff + cast).

    python -X utf8 tools/credits.py pages OUTDIR     render every page as greyscale index PNGs (index * 17)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "work/disc1/tree/MAP.DAT"
SECTOR = 2048


def records(head):
    o = struct.unpack_from("<I", head, 0x38)[0]  # last offset of the header's table (0x13AC)
    out = []
    while o + 12 <= len(head):
        r = struct.unpack_from("<6H", head, o)
        if r == (0,) * 6:
            break
        sec, flags, x, y, w, h = r
        out.append(dict(sec=sec, n=flags & 0xFF, bpp=8 if flags & 0x100 else 4, x=x, y=y, w=w, h=h))
        o += 12
    return out


def load(map_bytes=None):
    m = map_bytes or MAP.read_bytes()
    return dat.entry(m, 1256), dat.entry(m, 1257)


def page_indices(body, r):
    """Rows of pixel indices for one record."""
    off = r["sec"] * SECTOR
    if r["bpp"] == 8:
        stride = r["w"]
        return [list(body[off + y * stride: off + (y + 1) * stride]) for y in range(r["h"])]
    stride = r["w"] // 2
    rows = []
    for y in range(r["h"]):
        b = body[off + y * stride: off + (y + 1) * stride]
        row = []
        for v in b:
            row += [v & 15, v >> 4]
        rows.append(row)
    return rows


def put_indices(body, r, rows):
    """Write rows of 4bpp indices back into body (bytearray) for record r."""
    off = r["sec"] * SECTOR
    stride = r["w"] // 2
    for y, row in enumerate(rows):
        body[off + y * stride: off + (y + 1) * stride] = bytes(row[x] | row[x + 1] << 4 for x in range(0, r["w"], 2))


# --- English lettering from the game's own Latin atlas (page 18: 12x12 cells from (120, 0), baseline at cell row 9).
ATLAS_PAGE = 18
ATLAS_ROWS = ["ABCDEFGHIJ", "KLMNOPQRST", "UVWXYZ", "abcdefghij", "klmnopqrst", "uvwxyz", "0123456789",
              "+-%&!?♪~()"]
BASE = 9  # baseline row inside a cell
BG = 15  # page background index (ramp 1 = full ink .. 15 = background)
# Hand-drawn glyphs the atlas lacks: rows from cell row 0, '.' = background.
EXTRA = {"'": ["...", ".1.", ".1.", ".7."],
         "/": ["....", "...7", "..3.", "..3.", ".7..", ".3..", ".3..", "7...", "3...", "3..."]}
SPACE = 4
GAP = 1


def atlas(body, rs):
    a = page_indices(body, rs[ATLAS_PAGE])
    glyphs = {}
    for r, chars in enumerate(ATLAS_ROWS):
        for k, ch in enumerate(chars):
            x0, y0 = 120 + 12 * k, 12 * r
            cols = [x for x in range(x0, x0 + 12) if any(a[y][x] < BG for y in range(y0, y0 + 12))]
            glyphs[ch] = [a[y][cols[0]:cols[-1] + 1] for y in range(y0, y0 + 12)]
    for ch, art in EXTRA.items():
        w = len(art[0])
        g = [[BG if c == "." else int(c, 16) for c in row] for row in art]
        glyphs[ch] = g + [[BG] * w] * (12 - len(g))
    return glyphs


def typeset(glyphs, text, gap=GAP):
    """12 rows (baseline at row BASE) of indices for text."""
    rows = [[] for _ in range(12)]
    for i, ch in enumerate(text):
        if ch == " ":
            for row in rows:
                row += [BG] * SPACE
            continue
        g = glyphs[ch]
        for y in range(12):
            rows[y] += ([BG] * gap if i else []) + list(g[y])
    return rows


# --- the credits strip: pages 2-16 stacked as on screen (the scroll shows them in record order).
STRIP = range(2, 17)
CAST_PAGES = 6  # pages 2-7 hold the cast list
CAST = ["Tippi", "Luise", "Wallace", "Ariost", "Julian", "Karen", "Elliot", "Misha", "Xenos", "Sandra", "Lyell",
        "Reeves", "Ralph", "Princess Leticia", "King Alcadius", "General Bronson", "General Weber", "Irene", "Berger",
        "Headmaster Maxwell", "Headmaster's Secretary", "Vice Headmaster's Secretary", "Vice Headmaster Bradley",
        "Queen Mother Angela", "Lord Douglas", "Queen Stella", "King of Ranzak", "Bard", "Elliot's Foster Father",
        "Sierra", "Gevel (Monstrosity)", "Gamlan", "Grengal", "Oswald", "Wenzel"]
# Last page: 開発 キャリアソフト / 著作 アトラス／キャリアソフト / 制作 アトラス (then the (c) line, handled apart).
STAFF_END = ["Developed by CARRIER SOFT", "Copyright ATLUS / CARRIER SOFT", "Produced by ATLUS"]


def bands(strip, y0, y1, bg):
    """(top, bottom exclusive, left, right) of each run of rows holding ink (< bg) in strip[y0:y1]."""
    out, y = [], y0
    while y < y1:
        if any(v < bg for v in strip[y]):
            s = y
            while y < y1 and any(v < bg for v in strip[y]):
                y += 1
            xs = [x for x in range(256) if any(strip[yy][x] < bg for yy in range(s, y))]
            out.append((s, y, xs[0], xs[-1]))
        y += 1
    return out


def stamp(strip, rows, right, base, bg):
    """Draw typeset rows right-aligned at x=right (inclusive), baseline at strip row base; ink only (< 14)."""
    w = len(rows[0])
    x0 = right + 1 - w
    assert x0 >= 0, "line too wide"
    for y in range(12):
        for x in range(w):
            v = rows[y][x]
            if v < 14:
                strip[base - BASE + y][x0 + x] = min(strip[base - BASE + y][x0 + x], v)


def edit(body, rs):
    """English cast roles and closing lines, in place on body (bytearray of entry 1257)."""
    glyphs = atlas(body, rs)
    strip = [row for p in STRIP for row in page_indices(body, rs[p])]
    h = 255
    cast = bands(strip, 0, CAST_PAGES * h, BG)
    # a cast entry = a JP line (>= 10 rows) with the romanized actor line (<= 8 rows) 2-4 rows below it
    # (the cast ends at the "GAME PART STAFF" header, the first band starting at x=0 after "CAST")
    end = next(bd[0] for bd in cast[1:] if bd[2] == 0)
    pairs = [(a, b) for a, b in zip(cast, cast[1:])
             if a[1] - a[0] >= 10 and b[1] - b[0] <= 8 and b[0] - a[1] <= 4 and a[0] < end]
    assert len(pairs) == len(CAST), f"cast lines: {len(pairs)} found, {len(CAST)} names"
    small = small_caps(strip, [p[1] for p in pairs])
    for ((t, b, _l, r), (_t2, _b2, _l2, r2)), name in zip(pairs, CAST):
        for y in range(t, b):
            strip[y] = [BG] * 256
        # page column 255 never shows on screen (final "d" of Bard / Oswald lost); the JP names end at 254
        stamp(strip, typeset(glyphs, name), min(r2, 254), b - 2, BG)
    # last page (16): grey background 14 around the closing lines
    p0 = (16 - STRIP[0]) * h
    last = bands(strip, p0, p0 + 120, 14)
    i = next(k for k, bd in enumerate(last) if bd[1] - bd[0] >= 10)  # first tall (JP) line after "Publisher/..."
    jp = last[i:i + 4]
    for (t, b, _l, r), text in zip(jp, STAFF_END):
        for y in range(t, b):
            strip[y] = [v if v >= 14 else 14 for v in strip[y]]
        stamp(strip, typeset(glyphs, text), r, b - 2, 14)
    copyright_line(strip, small, jp[3])
    for k, p in enumerate(STRIP):
        put_indices(body, rs[p], strip[k * h:(k + 1) * h])
    player_label(body, rs, glyphs)
    return strip


# Atlas cells プレイヤー／ (row 10, ink x 120-194): the cast's player line draws them as one block, the name after it.
PLAYER = (120, 120, 76)  # x, y, width


def player_label(body, rs, glyphs):
    a = page_indices(body, rs[ATLAS_PAGE])
    x, y, w = PLAYER
    for row in a[y:y + 12]:
        row[x:x + w] = [BG] * w
    stamp(a, typeset(glyphs, "Player /"), x + w - 3, y + BASE, BG)  # slash ends where the JP ／ did
    put_indices(body, rs[ATLAS_PAGE], a)


# Small caps (the 7-row romanized actor font) harvested from cast actor lines: (cast index, the line's text).
SMALL_SRC = [(4, "CHIHARU TEZUKA"), (9, "SHIZUMI NIKI"), (20, "FUJINO")]  # text = the line's last letters
# ("TOMOKO FUJINO": TO and MO touch, so only FUJINO is cut)
# (c) line columns on page 16 (rows 93-102, caps 94-100): "(c)ATLUS／" 108-165, katakana 168-227, "1999" 235-254.
CR_KEEP = [(108, 165), (235, 254)]


def small_caps(strip, actor_bands):
    glyphs = {}
    for k, text in SMALL_SRC:
        t, b, _l, _r = actor_bands[k]
        cols = [x for x in range(256) if any(strip[y][x] < 14 for y in range(t, b))]  # 14 = faint, not stamped
        runs = []
        for x in cols:
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = x
            else:
                runs.append([x, x])
        letters = text.replace(" ", "")
        runs = runs[-len(letters):]
        assert all(x1 - x0 < 9 for x0, x1 in runs), (text, runs)  # one letter per run
        for ch, (x0, x1) in zip(letters, runs):
            cell = [[BG] * (x1 - x0 + 1) for _ in range(12)]
            for y in range(t, b):
                cell[BASE - (b - 1 - y)] = strip[y][x0:x1 + 1]
            glyphs.setdefault(ch, cell)
    return glyphs


def copyright_line(strip, small, band):
    """(c)ATLUS／キャリアソフト 1999 -> (c)ATLUS／CARRIER SOFT 1999 in the line's own small caps, right-aligned."""
    t, b, _l, right = band
    (a0, a1), (y0, y1) = CR_KEEP
    # caps baseline = lowest ink of "ATLUS／" (the (c) sign hangs 2 rows below it)
    base = max(y for y in range(t, b) if any(v < 14 for v in strip[y][a0 + 14:a1 + 1]))
    seg = lambda x0, x1: [[strip[y][x] if t <= y < b else BG for x in range(x0, x1 + 1)]  # noqa: E731
                          for y in range(base - BASE, base - BASE + 12)]
    parts = [seg(a0, a1), [[BG] * 2] * 12, typeset(small, "CARRIER SOFT", 2), [[BG] * 5] * 12, seg(y0, y1)]
    rows = [sum((p[y] for p in parts), []) for y in range(12)]
    for y in range(t, b):
        strip[y] = [v if v >= 14 else 14 for v in strip[y]]
    stamp(strip, rows, right, base, 14)


def patch(map_dat, log=None):
    """English credits into entry 1257 of map_dat (bytearray, in place, same size); log as insert.log_put."""
    start, _n = dat.entries(map_dat)[1257]
    off = start * SECTOR
    head, old = dat.entry(map_dat, 1256), bytes(dat.entry(map_dat, 1257))
    new = bytearray(old)
    edit(new, records(head))
    if log is not None:  # pages 2-16 and the atlas page 18 only (tools/allowed.txt)
        rs = records(head)
        spans = [(rs[STRIP[0]], rs[STRIP[-1]]), (rs[ATLAS_PAGE], rs[ATLAS_PAGE])]
        spans = [(a["sec"] * SECTOR, (b["sec"] + b["n"]) * SECTOR) for a, b in spans]
        kept = bytearray(new)
        for lo, hi in spans:
            kept[lo:hi] = old[lo:hi]
            log.append(("MAP.DAT", off + lo, old[lo:hi], bytes(new[lo:hi]), "credits.patch"))
        assert kept == old
    map_dat[off:off + len(new)] = new


def main(argv):
    from PIL import Image
    head, body = load()
    rs = records(head)
    if argv[0] == "show":
        b = bytearray(body)
        strip = edit(b, rs)
        out = Path(argv[1])
        out.mkdir(parents=True, exist_ok=True)
        for k in range(len(STRIP)):
            im = Image.new("L", (256, 255))
            im.putdata([v * 17 for row in strip[k * 255:(k + 1) * 255] for v in row])
            im.save(out / f"e{STRIP[k]:02d}.png")
    if argv[0] == "pages":
        out = Path(argv[1])
        out.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(rs):
            rows = page_indices(body, r)
            im = Image.new("L", (r["w"], r["h"]))
            k = 17 if r["bpp"] == 4 else 1
            im.putdata([v * k for row in rows for v in row])
            im.save(out / f"p{i:02d}.png")
            print(i, r)


if __name__ == "__main__":
    main(sys.argv[1:])
