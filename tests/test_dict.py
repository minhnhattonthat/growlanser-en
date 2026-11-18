"""tools/dictenc.py: dictionary compression keeps the text and never starts a code where the printer auto-wraps."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dictenc  # noqa: E402
import enfont  # noqa: E402


class Dict(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec, cls.font = enfont.EnCodec(), enfont.load()
        cls.d = dictenc.Dict([" the", " end.", " of the", "Hello"], cls.codec, cls.font)

    def expand(self, words):
        out = []
        for w in words:
            if w >= dictenc.DICT and w < dictenc.DICT + dictenc.MAXN:
                out += self.codec.encode(self.d.entries[w - dictenc.DICT])
            else:
                out.append(w)
        return self.codec.decode(out)

    def test_roundtrip_and_shorter(self):
        text = "Hello, this is the end.{n}All of the rest{s:0010} of the end."
        words = self.codec.encode(text)
        packed = self.d.compress(words)
        self.assertEqual(self.expand(packed), self.codec.decode(words))
        self.assertLess(len(packed), len(words))

    def test_no_code_past_wrap_column(self):
        # a line filled close to 288 px: whatever the grouping, no code may start past 276 px
        def starts(words):
            x, out = 0, []
            for w in words:
                out.append(x)
                x += enfont.width(self.expand([w]))
            return out
        tried = 0
        for k in range(60):
            line = ("Hello the end. " * 9)[:k + 40]
            if enfont.width(line) < 250 or max(starts(self.codec.encode(line))) > dictenc.LIMIT:
                continue  # the letter pairs auto-wrap already: the lint rejects such a line
            tried += 1
            self.assertLessEqual(max(starts(self.d.compress(self.codec.encode(line)))), dictenc.LIMIT, line)
        self.assertGreater(tried, 5)
