"""vwfemu.py: run asm/vwf.asm's vwf_draw under unicorn on a fake canvas (tests, debugging).

    python -X utf8 tools/vwfemu.py "Text" [OUT.png]     draw Text (encoded with enfont.EnCodec) and print it

Canvas: one font pixel = one byte, two canvas rows per font row, as the game's 0x80071650 draws it.
"""
import struct
import sys
from pathlib import Path

from unicorn import UC_ARCH_MIPS, UC_MODE_32, UC_MODE_LITTLE_ENDIAN, Uc
from unicorn.mips_const import (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_GP, UC_MIPS_REG_RA,
                                UC_MIPS_REG_SP, UC_MIPS_REG_V0)

sys.path.insert(0, str(Path(__file__).parent))
import enfont  # noqa: E402
import insert  # noqa: E402

RAM = 0x80000000
GP = 0x80190000
STOP = 0x80001000         # return address: emulation ends here
CANVAS1, CANVAS2 = 0x801E0000, 0x801F0000
STRIDE, SPLIT = 0x100, 40  # canvas 1 holds cols 0-39 (240 px), canvas 2 the rest


class Emu:
    def __init__(self, exe=None):
        exe = exe or insert.armips((insert.TREE / insert.EXE).read_bytes())
        self.sym = insert.symbols()
        self.uc = uc = Uc(UC_ARCH_MIPS, UC_MODE_32 + UC_MODE_LITTLE_ENDIAN)
        uc.mem_map(0, 0x200000)  # unicorn runs KSEG0 (0x8xxxxxxx) on physical memory
        self.write(0x80010000, exe[0x800:])
        self.write(0x80069D64, struct.pack("<II", 0x03E00008, 0))  # WAIT: jr ra; nop
        self.write(0x801D2808, struct.pack("<6I", CANVAS1, STRIDE, SPLIT, 0, CANVAS2, STRIDE))
        self.write(GP + 0x99C, b"\x0F")
        self.write(GP + 0x9A0, struct.pack("<I", 0x800F7DC8))
        self.clear()

    def write(self, addr, data):
        self.uc.mem_write(addr & 0x1FFFFFFF, data)

    def read(self, addr, n):
        return bytes(self.uc.mem_read(addr & 0x1FFFFFFF, n))

    def clear(self):
        self.write(CANVAS1, bytes(0x20000))

    def call(self, fn, *args):
        uc = self.uc
        for r, v in zip((UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2), args):
            uc.reg_write(r, v)
        uc.reg_write(UC_MIPS_REG_SP, 0x801FFF00)
        uc.reg_write(UC_MIPS_REG_GP, GP)
        uc.reg_write(UC_MIPS_REG_RA, STOP)
        uc.emu_start(self.sym[fn], STOP, count=200000)
        return uc.reg_read(UC_MIPS_REG_V0)

    def draw(self, words, col=0, row=0, big=False):
        """Feed words to vwf_std / vwf_big like the printer does (s6 = returned col); returns the final col."""
        for w in words:
            col = self.call("vwf_big", col, row, w) if big else self.call("vwf_std", col, row + 1, w)
        return col

    def texel(self, x, y):
        """4bpp texel (x, y) of the canvas (canvas 2 from texel SPLIT * 12 on)."""
        base, x2 = (CANVAS1, x) if x < SPLIT * 12 else (CANVAS2, x - SPLIT * 12)
        b = self.read(base + y * STRIDE + x2 // 2, 1)[0]
        return b >> 4 if x2 & 1 else b & 0xF

    def grid(self, w, h, row=0, big=False, x0=0):
        """Font pixels as text: # ink (colour 15), + shadow (5), . blank."""
        s = 2 if big else 1
        y0 = row * 16 + 6 if big else (row + 1) * 16 + 2
        return ["".join({0: ".", 15: "#", 5: "+"}.get(self.texel(x0 + s * x, y0 + s * y), "?") for x in range(w))
                for y in range(h)]


if __name__ == "__main__":
    e = Emu()
    e.draw(enfont.EnCodec().encode(sys.argv[1]))
    print("\n".join(e.grid(min(enfont.width(sys.argv[1]) + 2, 300), 13)))
