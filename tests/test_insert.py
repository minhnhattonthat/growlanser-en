"""tools/insert.py: jp-only insert is byte-identical; marker insert fits and every EXE string reads back."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402

HAVE = (extract.TREE / "SCEN.DAT").exists() and (ROOT / "tools/armips/armips.exe").exists()


@unittest.skipUnless(HAVE, "needs work/disc1/tree and armips")
class Insert(unittest.TestCase):
    def test_jp_identity(self):
        import insert
        self.assertEqual(insert.check(), [])

    def test_marker_exe_tables_read_back(self):
        """Emulate each getter (base + 2 * table[i], read to the terminator) on the marker EXE."""
        import insert
        exe = insert.patched("marker")[insert.EXE]
        enc = insert.Encoder("marker")
        for doc in insert.docs():
            if doc["file"] != insert.EXE:
                continue
            table, base = int(doc["table"], 16), int(doc["base"], 16)
            for slot, (i, d) in enumerate(extract._refs_parse(doc["refs"])):
                p = base + 2 * struct.unpack_from("<H", exe, table + 2 * slot)[0] - d
                want = enc.words(doc["entries"][i]) + [extract.TERM_W[doc["entries"][i]["term"]]]
                got = list(struct.unpack_from("<%dH" % len(want), exe, p))
                self.assertEqual(got, want, doc["entries"][i]["id"])


if __name__ == "__main__":
    unittest.main()
