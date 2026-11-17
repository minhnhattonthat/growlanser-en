"""scenram.py: find which SCEN.DAT entries sit in a PS1 RAM dump, and where (scene load-buffer recon).

    python -X utf8 tools/scenram.py RAM.bin [SCEN.DAT]
Prints entry, RAM address, entry size, and how many bytes after it are zero (slack before other data).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dat import entries, SECTOR  # noqa: E402
import scen  # noqa: E402

ram = open(sys.argv[1], "rb").read()
d = open(sys.argv[2] if len(sys.argv) > 2 else "work/disc1/tree/SCEN.DAT", "rb").read()
for i, (s, n) in enumerate(entries(d)):
    if not n:
        continue
    e = d[s * SECTOR:(s + n) * SECTOR]
    body = e.rstrip(b"\x00")
    probe = body[:256]
    if len(set(probe)) < 8:
        continue
    j = ram.find(probe)
    if j < 0:
        # the header and script mutate at run time; the text section doesn't
        ts = scen.text_section(e)
        if ts and ts[1] > 64:
            k = ram.find(e[ts[0]:ts[0] + min(ts[1], 512)])
            if k >= 0:
                print(f"entry {i} text at 0x{0x80000000 + k:08X} (entry start ~0x{0x80000000 + k - ts[0]:08X}, "
                      f"header changed)")
        continue
    same = ram[j:j + len(body)] == body
    k = j + len(body)
    z = k
    while z < len(ram) and ram[z] == 0:
        z += 1
    print(f"entry {i} at 0x{0x80000000 + j:08X} size 0x{len(body):X} full={same} zeros after 0x{z - k:X} "
          f"(next data at 0x{0x80000000 + z:08X})")
