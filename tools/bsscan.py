"""bsscan.py: find PS1 MDEC .BS still-image headers (u16 len, u16 0x3800, u16 qscale, u16 version 1-3) in files.

    python -X utf8 tools/bsscan.py FILE..
"""
import struct
import sys

for path in sys.argv[1:]:
    d = open(path, "rb").read()
    i = d.find(b"\x00\x38")
    while i >= 0:
        if i >= 2 and i % 2 == 0 and i + 6 <= len(d):
            ln, magic, q, ver = struct.unpack_from("<HHHH", d, i - 2)
            if 1 <= ver <= 3 and 0 < q < 64 and ln > 0:
                print(f"{path} 0x{i - 2:X} len {ln} q {q} v {ver}")
        i = d.find(b"\x00\x38", i + 1)
