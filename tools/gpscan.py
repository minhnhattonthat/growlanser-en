"""gpscan.py: every EXE instruction that uses gp + OFFSET (loads, stores, addiu), for RE of game globals.

    python -X utf8 tools/gpscan.py 0x854 [0x898 ..]     list instructions touching gp+0x854 (and others)
"""
import sys
from pathlib import Path

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "work" / "disc1" / "tree" / "SLPS_023.80"
BASE = 0x8000F800  # file offset -> RAM


def scan(data, offsets):
    md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)
    want = {"0x%x($gp)" % o for o in offsets} | {"$gp, 0x%x" % o for o in offsets}
    for off in range(0x800, len(data) - 3, 4):
        for ins in md.disasm(data[off:off + 4], BASE + off):
            if any(ins.op_str.endswith(w) for w in want):
                yield ins.address, ins.mnemonic, ins.op_str


if __name__ == "__main__":
    offs = [int(a, 16) for a in sys.argv[1:]]
    for a, m, o in scan(EXE.read_bytes(), offs):
        print("%08X  %-6s %s" % (a, m, o))
