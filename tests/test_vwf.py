"""asm/vwf.asm under unicorn (tools/vwfemu.py): what vwf_std / vwf_big draw must match the font, pixel for pixel."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import vwfemu
    import enfont
    HAVE = (ROOT / "work" / "disc1" / "tree" / "SLPS_023.80").exists() and (ROOT / "tools/armips/armips.exe").exists()
except ImportError:  # unicorn missing
    HAVE = False


def expected(text, w, h=13):
    """Reference rendering: ink '#', shadow '+' below and below-right of ink, '.' blank."""
    font, ink = enfont.load(), set()
    x = 0
    for ch in text:
        top, rows, adv = font[ch]
        ink |= {(x + rx, top + ry) for ry, r in enumerate(rows) for rx, c in enumerate(r) if c == "#"}
        x += adv
    shadow = {(px + dx, py + 1) for px, py in ink for dx in (0, 1)} - ink
    return ["".join("#" if (x, y) in ink else "+" if (x, y) in shadow else "." for x in range(w)) for y in range(h)]


@unittest.skipUnless(HAVE, "needs work/disc1/tree, armips and unicorn")
class Vwf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.emu = vwfemu.Emu()
        cls.codec = enfont.EnCodec()

    def run_text(self, text, col=0, row=0, big=False):
        self.emu.clear()
        self.emu.call("vwf_std", 99, 99, 0)  # leave state from another place: the draw must resync
        self.emu.clear()
        end = self.emu.draw(self.codec.encode(text), col, row, big)
        w = enfont.width(text)
        return end, self.emu.grid(w + 2, 13, row, big, x0=col * 12)

    def test_std(self):
        text = "The quick brown fox, Riviera!"
        end, got = self.run_text(text, col=1, row=2)
        self.assertEqual(got, expected(text, enfont.width(text) + 2))
        self.assertEqual(end, 1 + -(-enfont.width(text) // 12))

    def test_split_boundary(self):
        # canvas 1 ends at texel 480 (40 cols): text from col 38 crosses into canvas 2
        text = "Wwwwwm across"
        _, got = self.run_text(text, col=38)
        self.assertEqual(got, expected(text, enfont.width(text) + 2))

    def test_big(self):
        text = "Big Ag"
        _, got = self.run_text(text, col=3, row=1, big=True)
        self.assertEqual(got, expected(text, enfont.width(text) + 2))

    def test_interleaved_windows(self):
        """A typewriter line drawn a word at a time, with another window drawn between: no gap, no overlap."""
        e, c = self.emu, self.codec
        e.clear()
        col = e.draw(c.encode("Who "))
        e.write(0x801D2808, vwfemu.struct.pack("<I", vwfemu.CANVAS1 + 0x8000))  # another window's canvas
        e.draw(c.encode("Tag"), 0, 0)
        e.write(0x801D2808, vwfemu.struct.pack("<I", vwfemu.CANVAS1))
        e.draw(c.encode("goes"), col, 0)
        text = "Who goes"
        self.assertEqual(e.grid(enfont.width(text) + 2, 13), expected(text, enfont.width(text) + 2))

    def test_dictionary_codes(self):
        """Dictionary codes (tools/dictenc.py) draw their entry's letters: same pixels and end column as pairs."""
        import dictenc
        import insert
        d = dictenc.Dict([" quick", " brown fox,", "The"])
        exe = bytearray((insert.TREE / insert.EXE).read_bytes())
        info = insert.exe_heap(exe, [], d)
        emu = vwfemu.Emu(insert.armips(bytes(exe), dict(zip(("DICT_TAB", "DICT_BASE", "DICT_N"), info))))
        text = "The quick brown fox, Riviera!"
        words = d.compress(self.codec.encode(text))
        self.assertEqual(sum(w >= dictenc.DICT for w in words), 3)
        emu.clear()
        end = emu.draw(words, 1, 2)
        w = enfont.width(text)
        self.assertEqual(emu.grid(w + 2, 13, 2, x0=12), expected(text, w + 2))
        self.assertEqual(end, 1 + -(-w // 12))

    def test_odd_length_and_game_glyph(self):
        # "Ab" + bullet (game glyph 0xD1, 12 px) + "c": no gap after the single "c", glyph at x = 11
        self.emu.clear()
        words = self.codec.encode("Ab・c")
        self.assertEqual(len(words), 3)
        end = self.emu.draw(words)
        self.assertEqual(end, -(-(enfont.width("Ab") + 12 + enfont.width("c")) // 12))
        dot = self.emu.grid(30, 13)
        self.assertIn("#", "".join(r[enfont.width("Ab"):enfont.width("Ab") + 12] for r in dot))


if __name__ == "__main__":
    unittest.main()
