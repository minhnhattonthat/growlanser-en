import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RomListing(unittest.TestCase):
    def test_sha1_listing_has_no_placeholder(self):
        text = (ROOT / "rom.sha1").read_text(encoding="utf-8")
        self.assertNotIn("<sha1>", text)
        lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(len(lines), 3)
        for l in lines:
            self.assertEqual(len(l.split()[0]), 40)
