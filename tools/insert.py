"""insert.py: patched SCEN.DAT, MSYS.DAT and SLPS_023.80 from script/ (used by build.py).

    python -X utf8 tools/insert.py --check     jp-only insert must rebuild every file byte-identical (a test)

Each entry is encoded from `en` (enfont.EnCodec, pair codes) when it has one, else from `jp`. mode="marker"
replaces every non-empty line with "<short id> " plus filler of the same byte size (marker build, phase 5);
mode="jp" ignores `en` (identity check). Pools: SCEN text sections are rebuilt and the archive re-laid with a new
sector table (entries may grow); MSYS sections and EXE tables are written in place and must fit their original
blocks (an error names the pool otherwise). The EXE then gets asm/vwf.asm (VWF) via armips.
"""
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dat  # noqa: E402
import enfont  # noqa: E402
import extract  # noqa: E402
import gltext  # noqa: E402
import textsec  # noqa: E402

ROOT = extract.ROOT
TREE = extract.TREE
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
EXE = "SLPS_023.80"
# MSYS: section -> end of its block. Items = subfile 6 (sectors 0x85-0x8F), magic + skills = subfile 7 (0x8F-0x94);
# the game finds skills at magic + magic's u32 size (0x8004C13C), so skills follows magic wherever it ends.
MSYS_LIMIT = {"items": 0x47800, "magic": 0x4A000, "skills": 0x4A000}
KEEP_JP = {"exe.sys.%04d" % i for i in range(5)}  # single punctuation, maybe kinsoku data (not drawn as text)
FILLER = "The quick brown fox jumps over the lazy dog. "
TEXT_RUN = re.compile(r"(\{\w+(?::[0-9A-Fa-f]{4})?\}|\[[0-9A-Fa-f]{4}\])")


def short_id(eid):
    pool, _, n = eid.rpartition(".")
    m = re.fullmatch(r"scen(\d+)", pool)
    return "%d.%d" % (int(m.group(1)), int(n)) if m else "%s%d" % (pool.split(".")[-1][:2], int(n))


def marker(e):
    """Same byte size as the jp: each text run becomes 2 letters per Japanese character; a leading ・ stays."""
    out, first = [], True
    for part in TEXT_RUN.split(re.sub(r"\{F4[0-9A-F]{2}\}", "", e["jp"])):  # English writes dictionary words out
        if not part or TEXT_RUN.fullmatch(part):
            out.append(part)
            continue
        lead = "・" if part.startswith("・") else ""
        n = 2 * (len(part) - len(lead))
        txt = (short_id(e["id"]) + " ") if first else ""
        first = False
        txt += (FILLER * (n // len(FILLER) + 1))[:max(0, n - len(txt))]
        out.append(lead + txt)
    return "".join(out)


class Encoder:
    def __init__(self, mode, overrides=None):
        self.mode, self.jp, self.en = mode, gltext.Codec(), enfont.EnCodec()
        self.overrides = overrides or {}

    def words(self, e):
        if e["id"] in self.overrides:
            return self.en.encode(self.overrides[e["id"]])
        if self.mode == "jp" or not e["jp"] and not e.get("en") or e["id"] in KEEP_JP:
            return self.jp.encode(e["jp"])
        if self.mode == "marker":
            return self.en.encode(marker(e))
        return self.en.encode(e["en"]) if e.get("en") else self.jp.encode(e["jp"])

    def pool(self, doc):
        strings = [self.words(e) + [extract.TERM_W[e["term"]]] for e in doc["entries"]]
        refs = extract._refs_parse(doc["refs"])
        if doc["form"] == "section":
            pad = doc["pad"] if self.mode == "jp" else textsec.pad_for(strings, len(refs))
            return textsec.build_section(strings, refs, pad)
        return textsec.build_table(strings, refs)


def docs():
    for path in sorted((ROOT / "script").glob("*/*.json")):
        yield json.loads(path.read_text(encoding="utf-8"))


def scen_dat(data, sections):
    """Rebuild SCEN.DAT with new text sections {entry: bytes}; entries re-laid back to back in index order."""
    ents = dat.entries(data)
    first = min(s for s, n in ents if n)
    out = bytearray(data[:first * dat.SECTOR])
    table = []
    for i, (s, n) in enumerate(ents):
        e = data[s * dat.SECTOR:(s + n) * dat.SECTOR]
        if i in sections:
            sec = struct.unpack_from("<I", e, 22 * 4)[0]
            e = e[:sec] + sections[i]
            e += bytes(-len(e) % dat.SECTOR)
        table.append((len(out) // dat.SECTOR if n else s, len(e) // dat.SECTOR))
        out += e
    for i, (s, n) in enumerate(table):
        struct.pack_into("<HH", out, 4 + 4 * i, s, n)
    return bytes(out)


FONT = 0xE85C8  # game font, 18 bytes per glyph
# kanji cells free once the script is English (0x11C-0x69F; 0x6A0 on holds asm/vwf.asm), minus cells used as
# icons or symbols: 01BE flourish, 028B-028E ペンダント, 0298 / 02A4 key items, 03AD 0571 0643 0644 buttons, 0530 heart
FONT_FREE = [(0x11C, 0x1BE), (0x1BF, 0x28B), (0x28F, 0x298), (0x299, 0x2A4), (0x2A5, 0x3AD), (0x3AE, 0x530),
             (0x531, 0x571), (0x572, 0x643), (0x645, 0x6A0)]


class Heap:
    """String space for the EXE tables: their original string blocks plus FONT_FREE. Each table keeps its u16
    array and base (the getters stay as they are); a string may go anywhere in [base, base + 128 KB)."""

    def __init__(self, docs):
        self.free = sorted([(int(d["base"], 16), int(d["end"], 16)) for d in docs] +
                           [(FONT + 18 * a, FONT + 18 * b) for a, b in FONT_FREE])
        self.ranges = list(self.free)
        self.placed = {}

    def put(self, blob, base):
        a = self.placed.get(blob)
        if a is not None and base <= a < base + 0x20000:
            return a
        for k, (s, e) in enumerate(self.free):
            if s >= base and e - s >= len(blob) and s - base < 0x20000:
                self.free[k] = (s + len(blob), e)
                self.placed[blob] = s
                return s
        raise ValueError("EXE string heap full (%d bytes for base 0x%X)" % (len(blob), base))

    def write(self, data, strings):
        for s, e in self.ranges:
            data[s:e] = bytes(e - s)
        for addr, blob in strings:
            data[addr:addr + len(blob)] = blob


def exe_heap(data, items):
    """items: [(doc, strings as word lists incl. terminator)] for every EXE table."""
    heap, out = Heap([d for d, _ in items]), []
    for doc, strings in items:
        table, base = int(doc["table"], 16), int(doc["base"], 16)
        addr = [heap.put(gltext.pack(s), base) for s in strings]
        out += [(a, gltext.pack(s)) for a, s in zip(addr, strings)]
        vals = [(addr[i] + d - base) // 2 for i, d in extract._refs_parse(doc["refs"])]
        data[table:table + 2 * len(vals)] = struct.pack("<%dH" % len(vals), *vals)
    heap.write(data, out)


def exe_text(data, doc, pool):
    tbl, strs = pool
    table, base, end = (int(doc[k], 16) for k in ("table", "base", "end"))
    if len(strs) > end - base:
        raise ValueError("%s: %d bytes > block %d" % (doc["entries"][0]["id"].rsplit(".", 1)[0], len(strs), end - base))
    data[table:table + len(tbl)] = tbl
    data[base:end] = strs + bytes(end - base - len(strs))


def armips(exe):
    work = ROOT / "work" / "asm"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    glyphs, widths = enfont.tables()
    (work / "en_glyphs.bin").write_bytes(glyphs)
    (work / "en_widths.bin").write_bytes(widths)
    shutil.copy(ROOT / "asm" / "vwf.asm", work / "vwf.asm")
    (work / EXE).write_bytes(exe)
    r = subprocess.run([str(ARMIPS), "vwf.asm", "-sym", "vwf.sym"], cwd=work, capture_output=True, text=True)
    if r.returncode or "rror" in r.stdout:
        raise RuntimeError("armips failed:\n" + r.stdout + r.stderr)
    return (work / EXE).read_bytes()


def symbols():
    """{label: address} from the last armips run (work/asm/vwf.sym)."""
    out = {}
    for line in (ROOT / "work" / "asm" / "vwf.sym").read_text(encoding="utf-8").splitlines():
        a, _, name = line.partition(" ")
        if name and not name.startswith(".") and re.fullmatch(r"[0-9A-Fa-f]{8}", a):
            out[name.strip()] = int(a, 16)
    return out


def read_qa(path):
    """--qa file: id<TAB>text per line (stress lines for the width gate); # comments."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            k, _, v = line.partition("\t")
            out[k.strip()] = v
    return out


def patched(mode="en", tree=TREE, overrides=None):
    """{ISO file name: bytes} for SCEN.DAT, MSYS.DAT, SLPS_023.80. overrides: {id: English text} (--qa)."""
    enc = Encoder(mode, overrides)
    scen = (tree / "SCEN.DAT").read_bytes()
    msys = bytearray((tree / "MSYS.DAT").read_bytes())
    exe = bytearray((tree / EXE).read_bytes())
    sections, tables = {}, []
    for doc in docs():
        if doc["file"] == EXE and mode != "jp":
            tables.append((doc, [enc.words(e) + [extract.TERM_W[e["term"]]] for e in doc["entries"]]))
            continue
        pool = enc.pool(doc)
        if doc["file"] == "SCEN.DAT":
            sections[doc["entry"]] = pool
        elif doc["file"] == "MSYS.DAT":
            name = doc["entries"][0]["id"].split(".")[1]
            at = msys_next if name == "skills" else int(doc["at"], 16)
            msys_next = at + len(pool)
            if at + len(pool) > MSYS_LIMIT[name]:
                raise ValueError("msys.%s: %d bytes > block %d" % (name, len(pool), MSYS_LIMIT[name] - at))
            msys[at:MSYS_LIMIT[name]] = pool + bytes(MSYS_LIMIT[name] - at - len(pool))
        else:
            exe_text(exe, doc, pool)
    if tables:
        exe_heap(exe, tables)
    out ={"SCEN.DAT": scen_dat(scen, sections), "MSYS.DAT": bytes(msys)}
    out[EXE] = bytes(exe) if mode == "jp" else armips(bytes(exe))
    return out


def check():
    bad = []
    for name, data in patched("jp").items():
        if data != (TREE / name).read_bytes():
            bad.append(name)
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = check()
        print("jp insert differs: %s" % bad if bad else "jp insert rebuilds every file byte-identical")
        sys.exit(1 if bad else 0)
    print(__doc__)
