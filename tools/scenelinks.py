"""scenelinks.py: find scene-change ops in SCEN.DAT scripts (debug-tool recon, docs/re/debug.md).

Event VM ops 0x78 / 0x7A: [op][sub u8][area u16][scene u16] set area/sub (map, via the table at EXE RAM 0x80100A10)
and request scene `scene` (0x80113D66). 0x79 is the same with sub taken from a variable. This is a byte-pattern
scan, not a parse: a hit must name an (area, sub) pair the map table knows and a scene id 0-279.

    python -X utf8 tools/scenelinks.py [SCEN.DAT] [EXE]     prints: from_scene entry offset op -> scene area sub
"""
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dat import entries, SECTOR  # noqa: E402
import scen as scen_mod  # noqa: E402

EXE_RAM = 0x80010000 - 0x800
MAP_TABLE = 0x80100A10
NSCENE = 280


def map_pairs(exe):
    """{(area, sub): map id} from the EXE table at 0x80100A10 (u8 area, u8 sub, u16 map; 0x5BE rows, the count
    0x80044014 searches). First match wins, as in the game."""
    pairs = {}
    for i in range(0x5BE):
        a, s, m = struct.unpack_from("<BBH", exe, MAP_TABLE - EXE_RAM + 4 * i)
        pairs.setdefault((a, s), m)
    return pairs


def links(scen, exe):
    """Yield (from_scene, entry, offset, op, to_scene, area, sub) for every plausible scene-change op."""
    pairs = map_pairs(exe)
    ents = entries(scen)
    for i, (s, n) in enumerate(ents):
        if not n:
            continue
        e = scen[s * SECTOR:(s + n) * SECTOR]
        ts = scen_mod.text_section(e)
        end = ts[0] if ts else len(e)  # u16 glyph codes in the text section look like ops
        for j in range(end - 5):
            op = e[j]
            if op not in (0x78, 0x7A):
                continue
            sub, area, to = e[j + 1], *struct.unpack_from("<HH", e, j + 2)
            if to < NSCENE and (area, sub) in pairs:
                yield i % NSCENE, i, j, op, to, area, sub


if __name__ == "__main__":
    scen = open(sys.argv[1] if len(sys.argv) > 1 else "work/disc1/tree/SCEN.DAT", "rb").read()
    exe = open(sys.argv[2] if len(sys.argv) > 2 else "work/disc1/tree/SLPS_023.80", "rb").read()
    into = defaultdict(set)
    for f, i, j, op, to, area, sub in links(scen, exe):
        print(f"{f:3d} entry {i:3d} +0x{j:05X} op {op:02X} -> scene {to:3d} area {area:2d} sub {sub:2d}")
        into[to].add((area, sub))
    print(f"# {len(into)} target scenes")
