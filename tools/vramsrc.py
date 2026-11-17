"""vramsrc.py: find where a 16bpp VRAM rectangle (e.g. a framebuffer image) comes from in the disc files.

    python -X utf8 tools/vramsrc.py VRAM.bin X Y W [ROWS] FILE..

Takes rows Y..Y+ROWS of VRAM x X..X+W (halfwords; PCSX-Redux dump = 1024 halfwords per row) and searches each
FILE for each row's bytes; prints file, row, offset and the stride between consecutive row hits.
"""
import sys


def main():
    vram = open(sys.argv[1], "rb").read()
    x, y, w = (int(v, 0) for v in sys.argv[2:5])
    rest = sys.argv[5:]
    rows = int(rest.pop(0)) if rest and rest[0].isdigit() else 4
    for path in rest:
        d = open(path, "rb").read()
        last = None
        for r in range(y, y + rows):
            row = vram[(r * 1024 + x) * 2:(r * 1024 + x + w) * 2]
            if len(set(row)) < 4:
                continue
            i = d.find(row)
            if i >= 0:
                print(f"{path} row {r} at 0x{i:X}" + (f" stride {i - last}" if last is not None else ""))
                last = i


if __name__ == "__main__":
    main()
