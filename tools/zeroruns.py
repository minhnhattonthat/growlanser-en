"""zeroruns.py: list the longest runs of one fill byte in a file (free-space recon).

    python -X utf8 tools/zeroruns.py FILE [--min 256] [--byte 0] [--base 0x80010000-0x800]
--base maps file offsets to addresses (PS-X EXE: RAM = offset - 0x800 + 0x80010000).
"""
import argparse
import re

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--min", type=int, default=256)
ap.add_argument("--byte", type=lambda s: int(s, 0), default=0)
ap.add_argument("--base", type=lambda s: int(eval(s, {})), default=0)
a = ap.parse_args()
d = open(a.file, "rb").read()
runs = [(m.end() - m.start(), m.start()) for m in re.finditer(re.escape(bytes([a.byte])) + b"+", d)
        if m.end() - m.start() >= a.min]
for n, s in sorted(runs, reverse=True)[:20]:
    print(f"0x{s:06X} (addr 0x{s + a.base:08X}) len 0x{n:X}")
print(f"{len(runs)} runs >= {a.min}, total 0x{sum(n for n, _ in runs):X}")
