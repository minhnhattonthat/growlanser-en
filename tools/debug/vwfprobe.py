"""vwfprobe.py: inspect asm/vwf.asm state in RAM dumps (emu.py --script $SKILL/scripts/lua/probes/ramdump.lua).

    python tools/debug/vwfprobe.py slots DIR      vwf_state (scale, y0, round-robin, 4 canvas slots) per dump, on change
    python tools/debug/vwfprobe.py readers RAM.bin every lw 0x9A0(gp) (font pointer) and jal into the glyph code
"""
import glob
import struct
import sys

STATE, FREE_END, CANVAS = 0x800FF508, 0x80100A0E, 0x801D2808


def slots(d):
    prev = None
    for f in sorted(glob.glob(d + "/ram_*.bin")):
        r = open(f, "rb").read()
        st = struct.unpack_from("<20i", r, STATE & 0x1FFFFF)
        base1 = struct.unpack_from("<I", r, CANVAS & 0x1FFFFF)[0]
        if (st, base1) != prev:
            sl = [("%08X" % (s[0] & 0xFFFFFFFF),) + s[1:] for s in (st[4 + 4 * k:8 + 4 * k] for k in range(4))]
            print(f[-10:-4], "scale/y0/rr", st[:3], "slots (base, x, col, row)", sl, "base1 %08X" % base1)
            prev = (st, base1)


def readers(path):
    r = open(path, "rb").read()
    for i in range(0, len(r) - 4, 4):
        w = struct.unpack_from("<I", r, i)[0]
        if w >> 26 == 0x23 and (w >> 21) & 31 == 28 and w & 0xFFFF == 0x9A0:
            print("lw 0x9a0(gp) at %08X" % (0x80000000 + i))
        if w >> 26 == 3:
            t = ((w & 0x3FFFFFF) << 2) | 0x80000000
            if t in (0x800711E0, 0x80071650) or STATE <= t < FREE_END:
                print("jal %08X at %08X" % (t, 0x80000000 + i))


if __name__ == "__main__":
    {"slots": slots, "readers": readers}[sys.argv[1]](sys.argv[2])
