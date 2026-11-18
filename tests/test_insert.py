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


class Layout(unittest.TestCase):
    """Encoder.centre balances the blank in a 12 px-per-code frame; Encoder.slots fills fixed pixel slices."""
    def test_centre_and_slots(self):
        import enfont
        import insert
        enc = insert.Encoder("jp")
        for text in ("　Back at home...　", "　The next day　"):
            w = enc.centre(text, insert.CAPTION_BIAS)
            adv = sum(map(enc.advance, w))
            left = adv - 24 - enfont.width(text.strip("　")) + insert.CAPTION_BIAS
            self.assertLessEqual(abs(left - (12 * len(w) - adv)), 1, text)
            self.assertEqual(enc.en.decode(w), text)
        w = enc.slots("exe.sys.0069", "Enter Name　Hira Kata ABC Del OK")
        self.assertEqual(sum(map(enc.advance, w)), sum(insert.SLOTS["exe.sys.0069"]))
        self.assertEqual(enc.en.decode(w), "Enter NameHiraKataABCDelOK")


@unittest.skipUnless(HAVE, "needs work/disc1/tree and armips")
class English(unittest.TestCase):
    """The full English insert: only allowed bytes change, and every compressed pool reads back as its `en`."""

    @classmethod
    def setUpClass(cls):
        import insert
        cls.insert = insert
        cls.log = []
        cls.out = insert.patched("en", log=cls.log)
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
        for name in (self.insert.EXE, "MSYS.DAT", "MAP.DAT"):
            writes = [(o, a, b, w) for f, o, a, b, w in self.log if f == name]
            self.assertTrue(writes, name)  # MAP.DAT: the title and credits entries
            errs, _ = romdiff.check((extract.TREE / name).read_bytes(), self.out[name], allowed[name], writes)
            self.assertEqual(errs, [], name)

    def test_hook_sites(self):
        """No code branches into the middle of a vwf.asm hook span; the scan sees one planted on purpose."""
        exe = bytearray((extract.TREE / self.insert.EXE).read_bytes())
        self.assertEqual(self.insert.hook_branches(exe), [])
        struct.pack_into("<I", exe, 0x900, 0x08000000 | (0x8006F3AC & 0x3FFFFFF) >> 2)  # j into vwf_std's span
        self.assertEqual(self.insert.hook_branches(exe), [(0x900 + self.insert.RAM, 0x8006F3AC)])
        exe = bytearray((extract.TREE / self.insert.EXE).read_bytes())
        exe[0x8006F3A8 - self.insert.RAM] ^= 1  # another revision: the hook site no longer holds what we patch
        with self.assertRaises(ValueError):
            self.insert.armips(bytes(exe))

    def test_scen_integrity(self):
        """SCEN.DAT is re-laid whole: same leaves in the same order; untouched leaves byte-identical; a text leaf
        keeps every byte before its text section (section 22, the leaf's last), the original had only zero padding
        after that section, and the new one has only zero padding after its own. Header: only the placement table."""
        import dat
        old, new = (extract.TREE / "SCEN.DAT").read_bytes(), self.out["SCEN.DAT"]
        eo, en = dat.entries(old), dat.entries(new)
        self.assertEqual(len(eo), len(en))
        first = min(s for s, n in eo if n)
        table = 4 + 4 * len(eo)
        self.assertEqual(new[:4] + new[table:first * dat.SECTOR], old[:4] + old[table:first * dat.SECTOR])
        text = {d["entry"] for d in self.insert.docs() if d["file"] == "SCEN.DAT"}
        changed = 0
        for i, ((so, no), (sn, nn)) in enumerate(zip(eo, en)):
            a, b = old[so * dat.SECTOR:(so + no) * dat.SECTOR], new[sn * dat.SECTOR:(sn + nn) * dat.SECTOR]
            if a == b:
                continue
            self.assertIn(i, text, f"leaf {i} changed but holds no script text")
            sec = struct.unpack_from("<I", a, 22 * 4)[0]
            self.assertEqual(b[:sec], a[:sec], f"leaf {i}: bytes before the text section")
            end_a = sec + struct.unpack_from("<I", a, sec)[0]
            end_b = sec + struct.unpack_from("<I", b, sec)[0]
            self.assertFalse(a[end_a:].strip(b"\0"), f"leaf {i}: original data after its text section")
            self.assertFalse(b[end_b:].strip(b"\0"), f"leaf {i}: data after the new text section")
            changed += 1
        self.assertGreater(changed, 200)
        self.assertEqual(new[max(s + n for s, n in en) * dat.SECTOR:].strip(b"\0"), b"")  # nothing past the leaves

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
        scen = self.out["SCEN.DAT"]
        ents = dat.entries(scen)
        n = 0
        for doc in self.insert.docs():
            name = doc["entries"][0]["id"].rsplit(".", 1)[0]
            if doc["file"] == "MSYS.DAT":
                continue  # packed: test_msys_getters
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

    def test_vwf_width(self):
        """asm vwf_width (the pre-parser's measure) = the pixel width vwf_draw gives pairs, dictionary codes, glyphs."""
        import enfont
        import vwfemu
        emu, codec = vwfemu.Emu(self.out[self.insert.EXE]), enfont.EnCodec()
        codes = [0x00D1] + codec.encode("Wm.i'q Ag") + [0x4800 + i for i in range(0, self.gen["DICT_N"], 37)]
        for w in codes:
            want = 12 if w < enfont.PAIR else enfont.width(codec.decode(self.expand([w])))
            self.assertEqual(emu.call("vwf_width", w), want, hex(w))

    def test_msys_getters(self):
        """Run the game's six description getters (and asm/vwf.asm msys_get) under unicorn on the built EXE with
        each MSYS subfile in its load buffer: every string unpacks to its `en`; the cache keeps a string's slot."""
        import vwfemu
        exe, msys, ins = self.out[self.insert.EXE], self.out["MSYS.DAT"], self.insert
        emu = vwfemu.Emu(exe)
        enc = ins.Encoder("en")
        docs = {d["entries"][0]["id"].split(".")[1]: d for d in ins.docs() if d["file"] == "MSYS.DAT"}
        # (pool, getter, subfile, first offset-table slot, index limit of the getter)
        getters = [("items", 0x80070F98, 0, 0, 0x168), ("magic", 0x80070EC0, 1, 0, 0x40),
                   ("skills", 0x80070F2C, 1, 0, 0x40), ("skills", 0x8007109C, 1, (0x78 - 4) // 2, 0x20),
                   ("skills", 0x80071108, 1, (0xB8 - 4) // 2, 0x23), ("skills", 0x80071174, 1, (0xFE - 4) // 2, 0x30)]
        slots, seen = set(), set()
        for name, fn, sub, first, limit in getters:
            n = 6 + sub
            start, count = (struct.unpack_from("<H", exe, t + 2 * n)[0] for t in (ins.MSYS_SECTORS, ins.MSYS_COUNTS))
            data = msys[start * 2048:(start + count) * 2048]
            self.assertLessEqual(ins.MSYS_BUF + len(data), self.gen["MSYS_SCRATCH"])
            emu.write(ins.MSYS_BUF, data)
            magic = struct.unpack_from("<I", data)[0]
            emu.write(vwfemu.GP + 0x52E, bytes([sub]))
            emu.write(vwfemu.GP + 0x51A, b"\0")
            emu.write(vwfemu.GP + 0x538, struct.pack("<HH", 0, magic // 2 if sub else 0xFFFF))
            doc = docs[name]
            refs = extract._refs_parse(doc["refs"])
            for k in range(min(limit, len(refs) - first)):
                seen.add((name, first + k))
                e = doc["entries"][refs[first + k][0]]
                want = enc.words(e) + [extract.TERM_W[e["term"]]]
                p = emu.call(fn, k)
                self.assertEqual(emu.call(fn, k), p, "cache")
                got = list(struct.unpack_from("<%dH" % len(want), emu.read(p, 2 * len(want))))
                self.assertEqual(got, want, e["id"])
                slots.add(p)
        self.assertEqual(len(slots), ins.MSYS_NSLOT)
        self.assertEqual(len(seen), sum(len(extract._refs_parse(d["refs"])) for d in docs.values()))


if __name__ == "__main__":
    unittest.main()
