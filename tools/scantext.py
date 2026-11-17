"""scantext.py: find runs of Growlanser 16-bit text (glyph codes 0x01-0x7CA, controls >= 0xF000) in any file.

A run = >= MIN words, at even offsets, of glyph codes with at least one kana (0x2B-0xCD), ended by
FFFE/FFFF (or by a non-text word). Prints offset, length and the decoded text.

    python -X utf8 tools/scantext.py FILE [MIN=4] [--summary]
"""
import struct
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import gltext  # noqa: E402


def runs(data, minlen=4):
    n = len(data) // 2
    w = struct.unpack_from("<%dH" % n, data)
    i = 0
    while i < n:
        j = i
        kana = 0
        while j < n and (0 < w[j] <= 0x7CA or w[j] in (0xFFFC, 0xFFFD) or w[j] in (0xF600, 0xF800)):
            if 0x2B <= w[j] <= 0xCD:
                kana += 1
            if w[j] in (0xF600, 0xF800):
                j += 1
            j += 1
        if j - i >= minlen and kana >= 2:
            end = j + 1 if j < n and w[j] in (0xFFFE, 0xFFFF) else j
            yield i * 2, list(w[i:end])
            i = end
        else:
            i = j + 1 if j == i else j


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    minlen = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 4
    c = gltext.Codec()
    found = list(runs(data, minlen))
    if "--summary" in sys.argv:
        term = sum(1 for _, ws in found if ws[-1] in (0xFFFE, 0xFFFF))
        print(f"{len(found)} runs, {term} terminated, {sum(len(ws) for _, ws in found)} words")
    else:
        for off, ws in found:
            print("%06X %3d %s" % (off, len(ws), c.decode(ws)))
