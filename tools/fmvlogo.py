"""fmvlogo.py: G8, drop the katakana subtitle グローランサー under the GROWLANSER logo in the two FMVs (D5).

The logo (red letters over a red bar line) sits over moving clouds in MOVIE0.STR (frames 760-827: static, then a
zoom into white) and MOVIE1.STR (frames 1500-1575: fade in and out). Per frame: find the bar line (longest red
run), take the subtitle rect relative to it (calibrated on MOVIE0 frame 800: line y 137, x 73-248, subtitle
x 92-158, y 142-152), or where the line is clipped by the zoom, the red pixels below it; mask the reddish pixels
in the rect, fill them by diffusion from the cloud around, and re-encode only that rect with jPSXdec
`partial-replace`.

    python -X utf8 tools/fmvlogo.py edit MOVIE0.STR       decode the window, write work/fmv/en/<movie>/ (png + xml)
    python -X utf8 tools/fmvlogo.py build                 patched STRs -> work/fmv/en/MOVIE{0,1}.STR (needs Java)
patched() (used by insert.patched) returns {name: bytes} of the built STRs.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREE = ROOT / "work/disc1/tree"
OUT = ROOT / "work/fmv/en"
JAR = ROOT / "tools/jpsxdec/jpsxdec_v2.1-beta/jpsxdec.jar"
# subtitle x0, x1 (from the line's left end) and bottom (below the bar's last full row), per unit of line length;
# measured on MOVIE0 f800 (with the hero figure: line x 73-248, bar bottom row 140, subtitle x 94-158, bottom 151)
# and MOVIE1 f1540 (no figure: line x 64-254, bar bottom 133, subtitle x 66-136, bottom 146)
FIGURE = (21 / 175, 85 / 175, 11 / 175)
PLAIN = (2 / 190, 72 / 190, 13 / 190)
# Both movies show the logo twice (a full-frame scan for the red bar: work/fmv/scan_*); frames just outside each
# span are red fire / white, no logo.
WINDOW = {"MOVIE0.STR": [(760, 827, FIGURE), (1508, 1580, PLAIN)],
          "MOVIE1.STR": [(750, 824, FIGURE), (1508, 1580, PLAIN)]}
PAD = 2  # right and bottom; the top stays clear of the bar's lower edge
DARK = 110  # luminance of the sword and legs (never masked, never a fill source)


def jpsxdec(*args, cwd):
    r = subprocess.run(["java", "-jar", str(JAR), *map(str, args)], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"jpsxdec {args}: {r.stdout[-2000:]} {r.stderr[-2000:]}")
    return r.stdout


def redness(a):
    return a[:, :, 0] - (a[:, :, 1] + a[:, :, 2]) / 2


def barline(red, t):
    best = (0, 0, 0, 0)
    for y in range(red.shape[0]):
        r = red[y] > t
        x = 0
        while x < r.size:
            if r[x]:
                s = x
                while x < r.size and r[x]:
                    x += 1
                if x - s > best[0]:
                    best = (x - s, y, s, x - 1)
            x += 1
    return best


def subtitle_rect(red, rel):
    """(x0, y0, x1, y1) inclusive, or None if no logo."""
    h, w = red.shape
    t = 40
    n, y, left, right = barline(red, t)
    if n < 100:
        t = 8
        n, y, left, right = barline(red, t)
        if n < 100:
            return None
    bottom = y
    while bottom + 1 < h and (red[bottom + 1, left:right + 1] > t).sum() > .8 * (right - left):
        bottom += 1
    if left > 0 and right < w - 1:
        width = right - left
        x0, x1 = left + rel[0] * width, left + rel[1] * width
        y0, y1 = bottom + 1, bottom + rel[2] * width
    else:  # zoomed past the screen edges: the reddish pixels below the bar, left of the middle
        ys, xs = (red[bottom + 2:, : w // 2 + 40] > 6).nonzero()
        if not len(ys):
            return None
        x0, x1, y0, y1 = xs.min(), xs.max(), bottom + 1, ys.max() + bottom + 2
    x0, y0 = max(0, int(x0)), int(y0)  # no left pad: the sword runs just left of the subtitle (MOVIE0)
    x1, y1 = min(w - 1, int(x1 + .5) + PAD), min(h - 1, int(y1 + .5) + PAD)
    return x0, y0, x1, y1


def inpaint(a, mask, block, iters=600):
    """Fill mask pixels by repeated 4-neighbour averaging (clouds are smooth); `block` pixels (the bar's red edge)
    never feed the fill."""
    import numpy as np
    out = a.astype(float).copy()
    src = ~mask & ~block
    for y in np.nonzero(mask.any(1))[0]:  # start from each row's background right of the hole (keeps the glow band;
        m = np.nonzero(mask[y])[0]  # the left side has the sword and legs)
        xs = [x for x in range(m.max() + 1, min(m.max() + 25, mask.shape[1])) if src[y, x]]
        if not xs:
            xs = [x for x in range(max(0, m.min() - 24), m.min()) if src[y, x]]
        if xs:
            out[y, m] = np.median(out[y, xs], 0)
    w = (~block).astype(float)
    for _ in range(iters):
        p = np.pad(out * w[:, :, None], ((1, 1), (1, 1), (0, 0)), mode="edge")
        q = np.pad(w, 1, mode="edge")
        n = q[:-2, 1:-1] + q[2:, 1:-1] + q[1:-1, :-2] + q[1:-1, 2:]
        s = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        avg = s / np.maximum(n, 1)[:, :, None]
        out[mask] = avg[mask]
    return out.clip(0, 255).astype("uint8")


def clean(a, rel):
    """(edited RGB array, rect) for one frame; rect None = no logo."""
    import numpy as np
    red = redness(a.astype(int))
    rect = subtitle_rect(red, rel)
    if rect is None:
        return a, None
    x0, y0, x1, y1 = rect
    mask = np.zeros(red.shape, bool)
    # per row, only pixels redder than the row's own background right of the rect (the bar's glow is a horizontal
    # band: keep it); median of up to 24 px there
    lum = a.astype(int).mean(2)
    for y in range(y0, y1 + 1):
        sl = slice(x1 + 1, x1 + 25) if x1 + 1 < red.shape[1] else slice(max(0, x0 - 24), x0)
        base = max(0.0, float(np.median(red[y, sl]))) if red[y, sl].size else 0.0
        lbase = float(np.median(lum[y, sl])) if lum[y, sl].size else 255.0
        row, lrow = red[y, x0:x1 + 1], lum[y, x0:x1 + 1]
        # the red glyphs, and their soft grey drop shadow (not the sword / legs: those are darker than DARK)
        mask[y, x0:x1 + 1] = (row > base + 8) | ((lrow < lbase - 20) & (lrow > DARK))
    for _ in range(2):  # dilate 2 px, inside the rect
        m = mask.copy()
        m[1:] |= mask[:-1]
        m[:-1] |= mask[1:]
        m[:, 1:] |= mask[:, :-1]
        m[:, :-1] |= mask[:, 1:]
        box = np.zeros_like(m)
        box[y0:y1 + 1, x0:x1 + 1] = True
        mask = m & box
    if not mask.any():
        return a, None
    block = ((red > 40) | (lum <= DARK)) & ~mask  # the bar, the figure and the sword never feed the fill
    return inpaint(a, mask, block, iters=20), rect  # few rounds: smooth the row fill, keep its bands


def edit(movie):
    import numpy as np
    from PIL import Image
    d = OUT / movie.split(".")[0]
    (d / "orig").mkdir(parents=True, exist_ok=True)
    for p in list(d.glob("*.png")) + list((d / "orig").glob("*.png")):  # files only: a shell may sit in the dir
        p.unlink()
    jpsxdec("-f", TREE / movie, "-x", d / "src.idx", cwd=d)
    xml = ['<?xml version="1.0"?>', '<str-replace version="0.3">']
    for a, b, rel in WINDOW[movie]:
        jpsxdec("-x", d / "src.idx", "-i", 0, "-vf", "png", "-start", a, "-end", b, "-noaud", "-dir", d / "orig",
                cwd=d)
        for f in range(a, b + 1):
            xml += frame(d, movie, f, rel)
    xml.append("</str-replace>")
    (d / "replace.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    print(movie, len(xml) - 3, "frames ->", d)


def frame(d, movie, f, rel):
    """Edit one frame; [xml line] or []."""
    import numpy as np
    from PIL import Image
    src = d / "orig" / f"{movie}[0][{f:04d}].png"
    img, rect = clean(np.asarray(Image.open(src).convert("RGB")), rel)
    if rect is None:
        return []
    name = f"f{f:04d}.png"
    Image.fromarray(img).save(d / name)
    x0, y0, x1, y1 = rect
    return [f'  <partial-replace frame="{f}" tolerance="0" rect="{x0},{y0},{x1 - x0 + 1},{y1 - y0 + 1}">{name}'
            '</partial-replace>']


def build():
    for movie in WINDOW:
        d = OUT / movie.split(".")[0]
        if not (d / "replace.xml").exists():
            edit(movie)
        dst = OUT / movie
        shutil.copyfile(TREE / movie, dst)
        jpsxdec("-f", dst, "-x", d / "dst.idx", cwd=d)
        jpsxdec("-x", d / "dst.idx", "-i", 0, "-replaceframes", d / "replace.xml", cwd=d)
        print(movie, "->", dst)


def patched():
    """{ISO name: bytes} of the subtitle-free movies; builds them first if missing (Java + jPSXdec)."""
    if not all((OUT / m).exists() for m in WINDOW):
        build()
    return {m: (OUT / m).read_bytes() for m in WINDOW}


if __name__ == "__main__":
    if sys.argv[1] == "edit":
        edit(sys.argv[2])
    elif sys.argv[1] == "build":
        build()
