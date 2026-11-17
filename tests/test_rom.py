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


@unittest.skipUnless((ROOT / "rom/Growlanser (Japan) (Disc 1).bin").is_file(), "no disc image in rom/")
class Identity(unittest.TestCase):
    def test_unpack_repack_is_byte_identical(self):
        """Unpack -> repack with no edits gives every original track bit for bit (both discs, disc 2 CD-DA)."""
        import subprocess
        import sys
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "build.py"), "--identity"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
