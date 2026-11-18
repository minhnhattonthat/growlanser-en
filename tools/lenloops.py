"""lenloops.py: find string-length loops in the EXE (RE helper): a short backward branch whose body loads a halfword,
steps a pointer by 2 and a counter by 1. Code that sizes windows by code count shows up here.

    python -X utf8 tools/lenloops.py [LO HI]       candidates (loop start .. branch) in RAM range LO-HI (hex)
"""
import sys
from pathlib import Path

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "work" / "disc1" / "tree" / "SLPS_023.80"
BASE = 0x8000F800


def loops(data, lo=0x80010000, hi=0x80114000):
    md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True  # else disassembly stops at the first data word
    ins ={i.address: i for i in md.disasm(data[0x800:], BASE + 0x800)}
    for a, i in ins.items():
        if not (lo <= a < hi) or not i.mnemonic.startswith("b") or not i.op_str:
            continue
        try:
            target = int(i.op_str.split(",")[-1].strip(), 16)
        except ValueError:
            continue
        if not (a - 160 <= target < a):
            continue
        body = [ins[x] for x in range(target, a + 8, 4) if x in ins]
        ops = [(b.mnemonic, b.op_str) for b in body]
        if any(m == "lhu" for m, _ in ops) and any(m == "addiu" and o.endswith(", 2") for m, o in ops) \
                and any(m == "addiu" and o.endswith(", 1") for m, o in ops):
            yield target, a, ops


if __name__ == "__main__":
    lo, hi = (int(x, 16) for x in sys.argv[1:3]) if len(sys.argv) > 2 else (0x80010000, 0x80114000)
    for t, a, ops in loops(EXE.read_bytes(), lo, hi):
        print("%08X..%08X  %s" % (t, a, "; ".join("%s %s" % o for o in ops)))
