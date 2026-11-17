import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dat  # noqa: E402
import extract  # noqa: E402
import gltext  # noqa: E402
import scen  # noqa: E402
import textsec  # noqa: E402

SCEN = ROOT / "work" / "disc1" / "tree" / "SCEN.DAT"
TREE = ROOT / "work" / "disc1" / "tree"


class Codec(unittest.TestCase):
    def test_roundtrip_controls(self):
        c = gltext.Codec()
        w = [0xF800, 0x12, 0x2C, 0x54, 0x49, 0xFFFC, 0x11B, 0x7C9, 0x0763, 0x0118, 0xFFEF, 0xF600, 0xFFED, 0xFFFE]
        self.assertEqual(c.encode(c.decode(w)), w)

    def test_known_line(self):
        c = gltext.Codec()
        self.assertEqual(c.decode([0x2C, 0x54, 0x49, 0x36, 0x19E, 0x34A]), "あなたが大切")


@unittest.skipUnless(SCEN.exists(), "needs work/disc1 (dumpsxiso -x tree ...)")
class Scenes(unittest.TestCase):
    def test_archive_tiles_file(self):
        d = SCEN.read_bytes()
        es = dat.entries(d)
        self.assertEqual(max(s + n for s, n in es) * dat.SECTOR, len(d))

    def test_every_scene_string_roundtrips(self):
        c = gltext.Codec()
        d = SCEN.read_bytes()
        n = 0
        for i in range(len(dat.entries(d))):
            e = dat.entry(d, i)
            if not e or scen.text_section(e) is None:
                continue
            sec, size, offs = scen.text_section(e)
            self.assertTrue(all(4 + 2 * len(offs) <= o < size for o in offs), i)
            for s in scen.strings(e):
                self.assertEqual(c.encode(c.decode(s)), s)
                n += 1
        self.assertEqual(n, 24113)

    def test_text_only_in_scene_entries(self):
        d = SCEN.read_bytes()
        found = [i for i in range(len(dat.entries(d))) if dat.entry(d, i) and scen.text_section(dat.entry(d, i))]
        self.assertTrue(set(found) <= set(extract.SCEN_ENTRIES))
        self.assertEqual(len(found), 245)


@unittest.skipUnless(SCEN.exists(), "needs work/disc1 (dumpsxiso -x tree ...)")
class Script(unittest.TestCase):
    """Phase 4: script/ is the whole text of the disc, and rebuilds it byte-for-byte."""

    def test_script_matches_disc_and_rebuilds(self):
        self.assertEqual(extract.check(), [])

    def test_pad_rule(self):
        c = gltext.Codec()
        for rel, doc in extract.pools():
            if doc["form"] == "section":
                strings = [[0] * (len(c.encode(e["jp"])) + 1) for e in doc["entries"]]
                self.assertEqual(textsec.pad_for(strings, len(doc["refs"].split())), doc["pad"], rel)

    def test_exe_range_covered(self):
        exe = (TREE / "SLPS_023.80").read_bytes()
        spans = [(o, o + n) for o, n in extract.EXE_PADS]
        for _, table, base, count, end in extract.EXE_TABLES:
            spans += [(table, table + 2 * count), (base, end)]
        spans.sort()
        p = extract.EXE_RANGE[0]
        for a, b in spans:
            self.assertEqual(a, p, "gap or overlap at %X" % p)
            p = b
        self.assertEqual(p, extract.EXE_RANGE[1])
        self.assertTrue(all(exe[o:o + n] == b"\0" * n for o, n in extract.EXE_PADS))

    def test_msys_range_covered(self):
        import scantext
        d = (TREE / "MSYS.DAT").read_bytes()
        p = extract.MSYS_RANGE[0]
        for _, off in extract.MSYS_SECTIONS:
            self.assertFalse(d[p:off].strip(b"\0"), "data between sections at %X" % p)
            p = off + struct.unpack_from("<I", d, off)[0]
        self.assertEqual(p, extract.MSYS_RANGE[1])
        self.assertFalse(d[p:0x4A000].strip(b"\0"))
        lo, hi = extract.MSYS_RANGE
        stray = []
        for off, ws in scantext.runs(d, 4):
            g = [w for w in ws if w < 0x7CB]
            kana = sum(1 for w in g if 0x2B <= w <= 0xCD)
            if not lo <= off < hi and ws[-1] in (0xFFFE, 0xFFFF) and kana >= 0.4 * len(g):
                stray.append(hex(off))
        self.assertEqual(stray, [])

    def test_disc2_text_files_identical(self):
        d2 = ROOT / "work" / "disc2" / "tree"
        if not d2.exists():
            self.skipTest("no work/disc2")
        for a, b in (("SCEN.DAT", "SCEN.DAT"), ("MSYS.DAT", "MSYS.DAT"), ("SLPS_023.80", "SLPS_023.81")):
            self.assertEqual((TREE / a).read_bytes(), (d2 / b).read_bytes(), a)
