import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dat  # noqa: E402
import gltext  # noqa: E402
import scen  # noqa: E402

SCEN = ROOT / "work" / "disc1" / "tree" / "SCEN.DAT"


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
