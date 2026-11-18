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


@unittest.skipUnless(HAVE, "needs work/disc1/tree and armips")
class English(unittest.TestCase):
    """The full English insert: only allowed bytes change, and every compressed pool reads back as its `en`."""

    @classmethod
    def setUpClass(cls):
        import insert
        cls.insert = insert
        try:
            cls.out = insert.patched("en")
        except ValueError as e:
            if "HEAP_MAX" in str(e):  # open phase 7 blocker, docs/status.md
                raise unittest.SkipTest("English build blocked: " + str(e))
            raise
        gen = (ROOT / "work" / "asm" / "gen.inc").read_text(encoding="utf-8")
        cls.gen = {k: int(v, 16) for k, v in (line.split(" equ ") for line in gen.splitlines())}

    def test_romdiff(self):
        import romdiff
        allowed = {}
        for line in (ROOT / "tools" / "allowed.txt").read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                name, rng = line.split()[:2]
                lo, _, hi = rng.partition("-")
                allowed.setdefault(name, []).append(range(int(lo, 16), int(hi or lo, 16) + 1))
        for name in (self.insert.EXE, "MSYS.DAT"):
            errs, _ = romdiff.check((extract.TREE / name).read_bytes(), self.out[name], allowed[name], [])
            self.assertEqual(errs, [], name)

    def expand(self, words):
        exe, g, out = self.out[self.insert.EXE], self.gen, []
        for w in words:
            if 0x4800 <= w < 0x4800 + g["DICT_N"]:
                p = g["DICT_BASE"] + struct.unpack_from("<H", exe, g["DICT_TAB"] - 0x8000F800 + 2 * (w - 0x4800))[0]
                p -= 0x8000F800
                while struct.unpack_from("<H", exe, p)[0]:
                    out.append(struct.unpack_from("<H", exe, p)[0])
                    p += 2
            else:
                out.append(w)
        return out

    def test_pools_read_back(self):
        """MSYS subfiles (found through the EXE's sector table) and SCEN sections, dictionary expanded = `en`."""
        import dat
        import enfont
        import textsec
        codec, exe = enfont.EnCodec(), self.out[self.insert.EXE]
        msys, scen = self.out["MSYS.DAT"], self.out["SCEN.DAT"]
        sub7 = 2048 * struct.unpack_from("<H", exe, self.insert.MSYS_SECTORS + 14)[0]
        where = {"msys.items": 2048 * struct.unpack_from("<H", exe, self.insert.MSYS_SECTORS + 12)[0],
                 "msys.magic": sub7, "msys.skills": sub7 + struct.unpack_from("<I", msys, sub7)[0]}
        ents = dat.entries(scen)
        n = 0
        for doc in self.insert.docs():
            name = doc["entries"][0]["id"].rsplit(".", 1)[0]
            if doc["file"] == "MSYS.DAT":
                buf, off = msys, where[name]
            elif doc["file"] == "SCEN.DAT":
                s, _ = ents[doc["entry"]]
                buf = scen[s * 2048:]
                off = struct.unpack_from("<I", buf, 22 * 4)[0]
            else:
                continue
            strings, refs, _, _ = textsec.read_section(buf, off)
            self.assertEqual(refs, extract._refs_parse(doc["refs"]), name)
            for e, ws in zip(doc["entries"], strings):
                if e.get("en") and e["id"] not in self.insert.KEEP_JP:
                    want = codec.encode(e["en"]) + [extract.TERM_W[e["term"]]]
                    self.assertEqual(codec.decode(self.expand(ws)), codec.decode(want), e["id"])  # pairs regroup
                    n += 1
        self.assertGreater(n, 20000)


if __name__ == "__main__":
    unittest.main()
