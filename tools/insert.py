"""insert.py: patched SCEN.DAT, MSYS.DAT and SLPS_023.80 from script/ (used by build.py).

    python -X utf8 tools/insert.py --check     jp-only insert must rebuild every file byte-identical (a test)

Each entry is encoded from `en` (enfont.EnCodec, pair codes) when it has one, else from `jp`. mode="marker"
replaces every non-empty line with "<short id> " plus filler of the same byte size (marker build, phase 5);
mode="jp" ignores `en` (identity check). Pools: SCEN text sections are rebuilt and the archive re-laid with a new
sector table (entries may grow); MSYS sections are Huffman-packed outside jp mode (tools/msyspack.py, unpacked by
asm/vwf.asm msys_get) and written in place; EXE tables go to the string heap. The EXE then gets asm/vwf.asm (VWF)
via armips.
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
import dictenc  # noqa: E402
import enfont  # noqa: E402
import statusgfx  # noqa: E402
import title  # noqa: E402
import extract  # noqa: E402
import fit  # noqa: E402
import gltext  # noqa: E402
import msyspack  # noqa: E402
import textsec  # noqa: E402

ROOT = extract.ROOT
TREE = extract.TREE
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
EXE = "SLPS_023.80"
# MSYS text: items = subfile 6 (sectors 0x85-0x8F), magic + skills = subfile 7 (0x8F-0x94); the game finds skills
# at magic + magic's u32 size (0x8004C13C). Both load into the buffer at 0x80141778 (0x8004CED8), which the heap
# follows at HEAP_BASE. A subfile that outgrows its sectors moves to the end of MSYS.DAT (sector + count tables in
# the EXE) and the heap base moves up past it (asm/vwf.asm). docs/re/text.md "MSYS.DAT".
MSYS_SUB = {"items": 6, "magic": 7}
MSYS_SECTORS, MSYS_COUNTS = 0x2F3C, 0x2EBC  # EXE offsets of the u16 tables (RAM 0x8001273C / 0x800126BC)
MSYS_BUF, HEAP_BASE = 0x80141778, 0x80146778
# Heap base +0x3000 still opened the field menu; +0x4800 did not (gear_spell warp never reached the menu), so the
# region above the heap's bump pointer is not free. English MSYS text is Huffman-packed (tools/msyspack.py) instead.
HEAP_MAX = 0x80149778
# Unpacked strings go to MSYS_NSLOT slots at the top of the load buffer, above the (shrunk) subfiles.
MSYS_NSLOT = 16
# fit.BUDGETS rows whose frame is sized by code count (docs/windows.md "Name tag"; place popup: 12 px x codes at
# 0x8006BC94)
TAG_POOLS = ("scen.name", "exe.names", "exe.places")
# The place popup and the field-menu bubbles (same routine 0x8006BA48, the bubble has a tail) are sized to the
# text's pixel width by asm/vwf.asm popup_width: nothing to do in the text.
# Scene captions ("　The next day　"): code-count frame too; text starts 15 px in (blank incl.), and the ink ends 4 px
# before the last advance (work/qa/tour/ev_battle003 f002760).
CAPTION_BIAS = 11


def is_caption(e):
    j = e["jp"]
    return len(j) > 2 and j[0] == j[-1] == "　" and "{" not in j and "{" not in e["en"]


def is_title(e):
    """A scene string shown alone in a popup: place or event name (one line, no codes, no sentence punctuation,
    not a choice); its box is sized to the text in whole columns (Encoder.title_lead)."""
    return bool(e["jp"]) and "{" not in e["jp"] + e.get("en", "") and not e["jp"].startswith("　") \
        and not re.search("[。！？‥、「」…・]", e["jp"]) and not is_caption(e)
KEEP_JP = {"exe.sys.%04d" % i for i in range(5)}  # single punctuation, maybe kinsoku data (not drawn as text)
# Name-entry keyboard grids: one code per key, the key's code is what the name gets (D14)
KEEP_JP |= {"exe.sys.%04d" % i for i in range(70, 100)}
# exe.sys.0069 (name-entry title + labels) is printed as one line and cut into fixed pixel slices: title 60 px,
# blank 12, then 24 px per label. English: "Title　Label Label ..", each field centred in its slice (Encoder.slots).
SLOTS = {"exe.sys.0069": (60, 12, 24, 24, 24, 24, 24)}


def needs_english(entry):
    """Nonempty JP with no English and no exemption: KEEP_JP, or exe.dict (unused: English spells words out)."""
    return (bool(entry.get("jp")) and not entry.get("en") and entry["id"] not in KEEP_JP
            and not entry["id"].startswith("exe.dict"))
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
        self.font = enfont.load()
        self.dict = dictenc.build(docs()) if mode == "en" else None

    def words(self, e):
        if e["id"] in self.overrides:
            return self.en.encode(self.overrides[e["id"]])
        if self.mode == "jp" or not e["jp"] and not e.get("en") or e["id"] in KEEP_JP:
            return self.jp.encode(e["jp"])
        if self.mode == "marker":
            return self.en.encode(marker(e))
        if not e.get("en"):
            if self.mode == "en" and needs_english(e):
                raise ValueError(f"{e['id']}: no English (translate it, or add it to insert.KEEP_JP)")
            return self.jp.encode(e["jp"])
        pool = fit.budget(e["id"], e)[0]
        if pool == "scen" and is_caption(e):
            return self.centre(e["en"], CAPTION_BIAS)
        if e["id"] in SLOTS:
            return self.slots(e["id"], e["en"])
        w = self.en.encode(e["en"])
        if pool in TAG_POOLS:
            return self.tag_pad(w)
        if pool == "scen" and is_title(e):
            w = self.title_lead(w)
        return self.dict.compress(w) if self.dict and dictenc.compressible(e) else w

    def advance(self, w):
        if enfont.PAIR <= w < enfont.PAIR + 0x4000:
            return sum(self.font[self.en.rev[k]][2] for k in (w - enfont.PAIR >> 7, w & 0x7F) if k)
        return 12 if w < 0xE000 else 0

    def tag_pad(self, words):
        """Name tags are as many columns wide as their codes, and the printer draws a code only if its column
        ceil(x / 12) is inside: append zero-width codes (pair 0x0800 draws nothing) up to last column + 1."""
        x, need = 0, len(words)
        for w in words:
            need = max(need, -(-x // 12) + 1)
            x += self.advance(w)
        return words + [enfont.PAIR] * (need - len(words))

    def slots(self, eid, text):
        title, rest = text.split("　")
        fields, widths = [title, ""] + rest.split(" "), SLOTS[eid]
        if len(fields) != len(widths):
            raise ValueError(f"{eid}: {len(fields)} fields, the screen has {len(widths)} slices")

        def blank(n):
            sp = {v: k for k, v in enfont.SPACERS.items()}
            return sp[11] * (n // 11) + (sp[n % 11] if n % 11 else "")
        out = ""
        for f, w in zip(fields, widths):
            free = w - enfont.width(f, self.font)
            if free < 0:
                raise ValueError(f"{eid}: {f!r} is {-free} px wider than its {w} px slice")
            out += blank(free // 2) + f + blank(free - free // 2)
        return self.en.encode(out)

    def centre(self, text, bias):
        """The frame is 12 px x code count and the text starts near its left edge: lead with spacer glyphs (after
        any leading full-width blank) so the blank on the left matches the one on the right; bias = how much more
        blank the left side has than the model's. Never more codes than max(plain, 12)."""
        sp = list(enfont.SPACERS)
        leads = [""] + sp + [sp[-1] + s for s in sp]
        head = text[:len(text) - len(text.lstrip("　"))]
        cap = max(len(self.en.encode(text)), 12)
        best = None
        for lead in leads:
            w = self.en.encode(head + lead + text[len(head):])
            left = sum(enfont.SPACERS[c] for c in lead) + bias
            right = 12 * len(w) - sum(map(self.advance, w))
            key = (abs(left - right), len(w))
            if len(w) <= cap and (best is None or key < best[0]):
                best = key, w
        return best[1]

    def title_lead(self, w):
        """Title popups (place / event names) are sized to whole 12 px columns, ceil(width / 12), with the text at
        the left: lead with a spacer of half the slack so it sits centred (inkbox, bt_bernard place popup)."""
        width = sum(map(self.advance, w))
        lead = (-(-width // 12) * 12 - width) // 2
        return self.en.encode(chr(0xE000 + lead)) + w if lead else w

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


SCENE_SLOT = 0x7000  # 0x80128B98-0x8012FB98; JP's largest pair (scene 2) is 28632 bytes


def scen_dat(data, sections, strict=True):
    """Rebuild SCEN.DAT with new text sections {entry: bytes}; entries re-laid back to back in index order."""
    ents = dat.entries(data)
    first = min(s for s, n in ents if n)
    out = bytearray(data[:first * dat.SECTOR])
    table = []
    for i, (s, n) in enumerate(ents):
        e = data[s * dat.SECTOR:(s + n) * dat.SECTOR]
        if i in sections:
            sec = struct.unpack_from("<I", e, 22 * 4)[0]
            old = sec + struct.unpack_from("<I", e, sec)[0]
            e = e[:sec] + sections[i]
            # entries N-280 and N load back to back into 0x80128B98-0x8012FB98 (fixed data follows)
            s0, n0 = ents[i - 280]
            small = len(data[s0 * dat.SECTOR:(s0 + n0) * dat.SECTOR].rstrip(b"\0")) + 0x20
            if small + len(e) > max(SCENE_SLOT, small + old):
                msg = "scene %d: %d bytes > scene slot 0x%X" % (i - 280, small + len(e), SCENE_SLOT)
                if strict:
                    raise ValueError(msg)
                print("warning: " + msg + " (QA build: that scene may crash)")
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

    def write(self, data, strings, log=None):
        """Clear every heap range and fill it; logged as one construction write per range."""
        new = bytearray(data)
        for s, e in self.ranges:
            new[s:e] = bytes(e - s)
        for addr, blob in strings:
            if not any(s <= addr and addr + len(blob) <= e for s, e in self.ranges):
                raise ValueError("heap string at 0x%X outside the heap ranges" % addr)
            new[addr:addr + len(blob)] = blob
        for s, e in self.ranges:
            log_put(log, EXE, data, s, new[s:e], "heap 0x%X" % s)


RAM = 0x8000F800  # EXE file offset -> RAM address
# asm/vwf.asm fixed sites: RAM address -> the original bytes its .org overwrites (pinned from the rom.sha1 EXE).
# armips() asserts them before assembling and lets armips change bytes only here and in [FREE_START, FREE_END).
HOOKS = {
    0x800C1AA8: "1480023c78674224", 0x800C1AD8: "1480023c78674224", 0x800C2D58: "1480023c78674224",  # heap base
    0x8006F3A8: "78c4010c0100d62659a7010c", 0x8006F49C: "94c5010c", 0x8006F4A4: "59a7010c",  # glyph routines
    0x8006F4AC: "0200d626", 0x80065444: "60000316", 0x800658F0: "56000316",  # s6 step, typewriters
    0x8006496C: "f093010801003126", 0x80064AB4: "f093010802003126",  # pre-parser column step
    0x80070F18: "211062001400bf8f", 0x80070F84: "211062001400bf8f", 0x80070FF0: "211062001400bf8f",  # MSYS getters
    0x800710F4: "211062001400bf8f", 0x80071160: "211062001400bf8f", 0x800711CC: "211062001400bf8f",
    0x8006BBB8: "23108500c21f02002110430043a00200", 0x8006BCA0: "80200200",  # place popup frame width
}
_ASM = (ROOT / "asm" / "vwf.asm").read_text(encoding="utf-8")
FREE_ASM = tuple(int(re.search(r"^%s\s+equ\s+(0x[0-9A-Fa-f]+)" % k, _ASM, re.M).group(1), 16) - RAM
                 for k in ("FREE_START", "FREE_END"))  # file offsets of vwf.asm's code + font tables


def log_put(log, name, data, off, blob, writer):
    """data[off:off + len(blob)] = blob, recorded as a romdiff write (file, offset, old, new, writer) in log."""
    if log is not None:
        old = bytes(data[off:off + len(blob)])
        log.append((name, off, old + b"\xff" * (len(blob) - len(old)), bytes(blob), writer))
    data[off:off + len(blob)] = blob


def hook_branches(exe):
    """[(source, target)]: j/jal/branches in the EXE whose target is inside a HOOKS span but not its first word
    (the hook would cut such code in half). Scans every word from the code start (RAM 0x80010000)."""
    spans = [(a, a + len(bytes.fromhex(h))) for a, h in HOOKS.items()]
    out = []
    for off in range(0x800, len(exe) - 3, 4):
        w, pc = struct.unpack_from("<I", exe, off)[0], off + RAM
        op = w >> 26
        if op in (2, 3):
            dst = (pc & 0xF0000000) | (w & 0x3FFFFFF) << 2
        elif op in (4, 5, 6, 7) or op == 1 and (w >> 16 & 0x1F) in (0, 1, 0x10, 0x11):
            dst = pc + 4 + (((w & 0xFFFF) ^ 0x8000) - 0x8000) * 4
        else:
            continue
        out += [(pc, dst) for a, e in spans if a < dst < e and not a <= pc < e]
    return out
DICT_BASE = 0xE2138  # dictionary entries: u16 offsets from here (string blocks + font cells span < 64 KB)


def exe_heap(data, items, dictionary=None, model=None, log=None):
    """items: [(doc, strings as word lists incl. terminator)] for every EXE table; then the dictionary's entries
    and offset table (dictenc), then the msyspack model. Returns (DICT_TAB, DICT_BASE, DICT_N, MSYS_MODEL) as RAM
    addresses for asm/vwf.asm."""
    heap, out = Heap([d for d, _ in items]), []
    for doc, strings in items:
        table, base = int(doc["table"], 16), int(doc["base"], 16)
        addr = [heap.put(gltext.pack(s), base) for s in strings]
        out += [(a, gltext.pack(s)) for a, s in zip(addr, strings)]
        vals = [(addr[i] + d - base) // 2 for i, d in extract._refs_parse(doc["refs"])]
        log_put(log, EXE, data, table, struct.pack("<%dH" % len(vals), *vals), doc["entries"][0]["id"][:-5] + " table")
    info = (0, 0, 0)
    if dictionary and dictionary.entries:
        blobs = dictionary.blobs()
        tab = heap.put(b"\xff" * 2 * len(blobs), DICT_BASE)
        offs = [heap.put(b, DICT_BASE) - DICT_BASE for b in blobs]
        assert max(offs) < 0x10000
        out += [(tab, struct.pack("<%dH" % len(offs), *offs))] + [(DICT_BASE + o, b) for o, b in zip(offs, blobs)]
        info = (tab + RAM, DICT_BASE + RAM, len(blobs))
    if model:
        blob = model.blob()
        at = heap.put(blob, DICT_BASE)
        assert at % 2 == 0
        out.append((at, blob))
        info += (at + RAM,)
    heap.write(data, out, log)
    return info + (0,) * (4 - len(info))


def exe_text(data, doc, pool):
    tbl, strs = pool
    table, base, end = (int(doc[k], 16) for k in ("table", "base", "end"))
    if len(strs) > end - base:
        raise ValueError("%s: %d bytes > block %d" % (doc["entries"][0]["id"].rsplit(".", 1)[0], len(strs), end - base))
    data[table:table + len(tbl)] = tbl
    data[base:end] = strs + bytes(end - base - len(strs))


GEN_DEFAULT = {"DICT_TAB": 0, "DICT_BASE": 0, "DICT_N": 0, "HEAP_BASE": HEAP_BASE, "MSYS_MODEL": 0, "MSYS_SLOT": 0,
               "MSYS_NSLOT": MSYS_NSLOT, "MSYS_SCRATCH": 0}


def armips(exe, gen=None, log=None):
    """Assemble asm/vwf.asm into exe; gen = values for work/asm/gen.inc (GEN_DEFAULT: no dictionary, heap as is).
    Each HOOKS site must still hold its original bytes; armips may change bytes only there and in FREE_ASM."""
    for a, h in HOOKS.items():
        if exe[a - RAM:a - RAM + len(h) // 2].hex() != h:
            raise ValueError("vwf.asm hook 0x%08X: EXE holds %s, not the original %s" % (a, exe[a - RAM:][:len(h) // 2].hex(), h))
    out = _armips(exe, gen)
    spans = [(a - RAM, a - RAM + len(h) // 2, "vwf.asm hook 0x%08X" % a) for a, h in HOOKS.items()]
    spans.append(FREE_ASM + ("vwf.asm code + font tables",))
    if len(out) != len(exe):
        raise ValueError("armips changed the EXE size")
    left = [i for i in range(len(exe)) if exe[i] != out[i]] if exe != out else []
    buf = bytearray(exe)
    for s, e, name in spans:
        if exe[s:e] != out[s:e]:
            log_put(log, EXE, buf, s, out[s:e], name)
    stray = [i for i in left if not any(s <= i < e for s, e, _ in spans)]
    if stray:
        raise ValueError("armips wrote outside the hook sites and free space: 0x%X.." % (stray[0] + RAM))
    return out


def _armips(exe, gen=None):
    work = ROOT / "work" / "asm"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    glyphs, widths = enfont.tables()
    (work / "en_glyphs.bin").write_bytes(glyphs)
    (work / "en_widths.bin").write_bytes(widths)
    (work / "gen.inc").write_text("".join("%s equ 0x%X\n" % kv for kv in {**GEN_DEFAULT, **(gen or {})}.items()))
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


def patched(mode="en", tree=TREE, overrides=None, log=None):
    """{ISO file name: bytes} for SCEN.DAT, MSYS.DAT, SLPS_023.80 (+ MAP.DAT title, not in jp mode). overrides: {id: English text} (--qa).
    log: a list that gets every EXE / MSYS write as (file, offset, old, new, writer) for romdiff --writes
    (SCEN.DAT is re-laid whole: test_insert English.test_scen_integrity checks it leaf by leaf)."""
    enc = Encoder(mode, overrides)
    scen = (tree / "SCEN.DAT").read_bytes()
    msys = bytearray((tree / "MSYS.DAT").read_bytes())
    exe = bytearray((tree / EXE).read_bytes())
    sections, tables, sub, msys_docs = {}, [], {6: b"", 7: b""}, []
    for doc in docs():
        if doc["file"] == EXE and mode != "jp":
            tables.append((doc, [enc.words(e) + [extract.TERM_W[e["term"]]] for e in doc["entries"]]))
            continue
        if doc["file"] == "MSYS.DAT" and mode != "jp":
            msys_docs.append(doc)
            continue
        pool = enc.pool(doc)
        if doc["file"] == "SCEN.DAT":
            sections[doc["entry"]] = pool
        elif doc["file"] == "MSYS.DAT":
            sub[MSYS_SUB.get(doc["entries"][0]["id"].split(".")[1], 7)] += pool  # skills after magic
        else:
            exe_text(exe, doc, pool)
    gen, limit, model = {}, HEAP_BASE, None
    if msys_docs:
        model, slot, pools = msys_pack(enc, msys_docs)
        for doc, pool in zip(msys_docs, pools):
            sub[MSYS_SUB.get(doc["entries"][0]["id"].split(".")[1], 7)] += pool
        limit = HEAP_BASE - MSYS_NSLOT * slot
        gen.update(MSYS_SLOT=slot, MSYS_NSLOT=MSYS_NSLOT, MSYS_SCRATCH=limit)
    heap = msys_text(msys, exe, sub, limit, log)
    if mode != "jp":
        statusgfx.patch(msys, log)  # G2/G3 status-screen resistance labels and element icons
    dict_info = exe_heap(exe, tables, enc.dict, model, log) if tables else (0, 0, 0, 0)
    out = {"SCEN.DAT": scen_dat(scen, sections, strict=mode == "en" and not overrides), "MSYS.DAT": bytes(msys)}
    gen.update(zip(("DICT_TAB", "DICT_BASE", "DICT_N", "MSYS_MODEL"), dict_info), HEAP_BASE=heap)
    out[EXE] = bytes(exe) if mode == "jp" else armips(bytes(exe), gen, log)
    if mode != "jp":
        map_dat = bytearray((tree / "MAP.DAT").read_bytes())
        title.patch(map_dat, log)  # G1 title graphics
        out["MAP.DAT"] = bytes(map_dat)
    return out


def msys_pack(enc, docs_):
    """Huffman-pack the MSYS pools (tools/msyspack.py). -> (model, slot bytes per unpacked string, [section])."""
    strings = [[enc.words(e) + [extract.TERM_W[e["term"]]] for e in doc["entries"]] for doc in docs_]
    model, packed = msyspack.build([s for ss in strings for s in ss])
    it, pools = iter(packed), []
    for doc, ss in zip(docs_, strings):
        words = [msyspack.section_words(next(it)) for _ in ss]
        refs = extract._refs_parse(doc["refs"])
        pools.append(textsec.build_section(words, refs, textsec.pad_for(words, len(refs))))
    slot = max(2 * len(s) for ss in strings for s in ss) + 8 + 3 & ~3  # + room for msys_unpack's cut-off
    return model, slot, pools


def msys_text(msys, exe, sub, limit=HEAP_BASE, log=None):
    """Write MSYS subfiles 6 / 7 ({index: bytes}) in place (sector count shrunk to fit, so the load leaves the
    unpack slots above `limit` alone), or at the end of msys (bytearray) when grown; return the heap base."""
    top = HEAP_BASE
    for i, blob in sub.items():
        start, count = (struct.unpack_from("<H", exe, t + 2 * i)[0] for t in (MSYS_SECTORS, MSYS_COUNTS))
        n = -(-len(blob) // dat.SECTOR)
        if n > count:  # grown: append (sector-aligned) at the end of the file
            pad = -len(msys) % dat.SECTOR
            start = (len(msys) + pad) // dat.SECTOR
            log_put(log, EXE, exe, MSYS_SECTORS + 2 * i, struct.pack("<H", start), "MSYS sector %d" % i)
            log_put(log, "MSYS.DAT", msys, len(msys), bytes(pad) + blob + bytes(n * dat.SECTOR - len(blob)),
                    "MSYS subfile %d (moved)" % i)
        else:
            log_put(log, "MSYS.DAT", msys, start * dat.SECTOR, blob + bytes(count * dat.SECTOR - len(blob)),
                    "MSYS subfile %d" % i)
        if limit < HEAP_BASE or n > count:
            count = n
            log_put(log, EXE, exe, MSYS_COUNTS + 2 * i, struct.pack("<H", count), "MSYS count %d" % i)
        top = max(top, MSYS_BUF + count * dat.SECTOR)
        if MSYS_BUF + count * dat.SECTOR > limit:
            raise ValueError("MSYS subfile %d: %d sectors pass the unpack slots at 0x%X" % (i, count, limit))
    if top > HEAP_MAX:
        raise ValueError("MSYS text needs the heap base at 0x%X > HEAP_MAX 0x%X" % (top, HEAP_MAX))
    return top


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
