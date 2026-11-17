"""str2352.py: turn a dumpsxiso STR (2336-byte Mode 2 sectors) into 2352-byte raw sectors for ffmpeg's psxstr demuxer.

    python -X utf8 tools/str2352.py IN.STR OUT.STR
    ffmpeg -f psxstr -i OUT.STR -vf fps=0.5 frames/%04d.png
Sync + a dummy MSF header are prepended; ffmpeg ignores EDC/ECC.
"""
import sys

SYNC = b"\x00" + b"\xff" * 10 + b"\x00"
d = open(sys.argv[1], "rb").read()
assert len(d) % 2336 == 0, "not 2336-byte sectors"
with open(sys.argv[2], "wb") as f:
    for i in range(0, len(d), 2336):
        f.write(SYNC + b"\x00\x02\x00\x02" + d[i:i + 2336])
