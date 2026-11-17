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


if __name__ == "__main__":
    unittest.main()
