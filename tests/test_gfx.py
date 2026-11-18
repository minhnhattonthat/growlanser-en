"""Graphics survey tools: pixel unpacking (rawgfx) and the title-texture source (vramsrc finding, docs/re/graphics.md G1)."""
import unittest
from pathlib import Path

from rawgfx import pixels

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "work/disc1/tree/MAP.DAT"


class TestPixels(unittest.TestCase):
    def test_4bpp_low_nibble_first(self):
        self.assertEqual(list(pixels(b"\x21", 4)), [1 * 17, 2 * 17])

    def test_16bpp_white_black(self):
        self.assertEqual(list(pixels(b"\xff\x7f\x00\x00", 16)), [255, 0])


@unittest.skipUnless(MAP.exists(), "unpacked disc not present")
class TestTitleSource(unittest.TestCase):
    def test_title_tiles_in_map_1161(self):
        from dat import entries
        d = MAP.read_bytes()
        start, n = entries(d)[1161]
        self.assertEqual((start, n), (50872, 59))
        self.assertLessEqual(start * 2048, 0x635D400)
        self.assertLess(0x635D400, (start + n) * 2048)


@unittest.skipUnless(MAP.exists(), "unpacked disc not present")
class TestCredits(unittest.TestCase):
    """G5: the credits pages round-trip, and the edit touches only the cast pages (2-7) and the last page (16)."""

    def test_records_and_edit(self):
        import credits
        head, body = credits.load()
        rs = credits.records(head)
        self.assertEqual(len(rs), 19)
        self.assertEqual(rs[-1]["sec"] + rs[-1]["n"], len(body) // 2048)  # records tile the entry
        b = bytearray(body)
        credits.put_indices(b, rs[2], credits.page_indices(body, rs[2]))
        self.assertEqual(bytes(b), body)  # 4bpp unpack/pack round-trip
        credits.edit(b, rs)  # asserts 36 cast lines found
        changed = {i for i, r in enumerate(rs) if credits.page_indices(b, r) != credits.page_indices(body, r)}
        self.assertEqual(changed, {2, 3, 4, 5, 6, 7, 16})

    def test_typeset_width(self):
        import credits
        head, body = credits.load()
        g = credits.atlas(body, credits.records(head))
        rows = credits.typeset(g, "Ab")
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(rows[0]), len(g["A"][0]) + credits.GAP + len(g["b"][0]))


if __name__ == "__main__":
    unittest.main()
