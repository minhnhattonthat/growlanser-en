"""scendump.py: read a scene's text in order (choices included), or a one-line summary of every scene.

    python -X utf8 tools/scendump.py N [SCEN.DAT]        all strings of scene N (entry 280+N), numbered
    python -X utf8 tools/scendump.py --summary [SCEN.DAT] per scene: string count, short names, first lines

Used to find what a scene is (scene 18 = the developers' check menu, docs/re/debug.md).
"""
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dat  # noqa: E402
import gltext  # noqa: E402
import scen  # noqa: E402


def all_strings(e):
    """Every terminated string in the text section, in file order (the offset table skips choice lines)."""
    sec, size, offs = scen.text_section(e)
    p, out = sec + 4 + 2 * len(offs), []
    while p < sec + size:
        ws = []
        while p < sec + size:
            w = struct.unpack_from("<H", e, p)[0]
            p += 2
            ws.append(w)
            if w in (0xFFFE, 0xFFFF):
                break
        out.append(ws)
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = next((a for a in args if a.lower().endswith(".dat")), "work/disc1/tree/SCEN.DAT")
    data = open(path, "rb").read()
    c = gltext.Codec()
    if "--summary" in sys.argv:
        for n in range(280):
            e = dat.entry(data, 280 + n)
            if not e or scen.text_section(e) is None:
                print(n, "-")
                continue
            txt = [re.sub(r"\{[^}]*\}", "", c.decode(w)) for w in all_strings(e)]
            names = [t for t in txt[:12] if 0 < len(t) < 8][:6]
            body = [t[:40] for t in txt if len(t) >= 8][:2]
            print(n, len(txt), "/".join(names), "|", " / ".join(body))
    else:
        e = dat.entry(data, 280 + int(args[0]))
        for i, ws in enumerate(all_strings(e)):
            print(i, c.decode(ws).replace("{n}", " "))
