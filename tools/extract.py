"""extract.py: dump every text pool of the original disc to script/*.json (formats: docs/re/text.md).

    python -X utf8 tools/extract.py            write missing script files (never touches existing ones)
    python -X utf8 tools/extract.py --force    rewrite files that hold no English yet (refuses files with any `en`)
    python -X utf8 tools/extract.py --check    exit 1 unless script/ matches the disc and rebuilds byte-identical

Pools: SCEN.DAT scene text sections (script/scen/sNNN.json, N = entry - 280 = scene id), MSYS.DAT description
sections (script/msys/), EXE string tables (script/exe/). Both discs carry the same files; disc 1 is read.
Entry fields: id, jp (terminator excluded), en, term (end = FFFE message, null = FFFF name/slot), unref (no pointer:
choice lines read on past their question). Pool fields: where it lives, refs ("i" or "i+d" per pointer slot, in
slot order: string index, byte delta), pad (trailing FFFF words).
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dat  # noqa: E402
import gltext  # noqa: E402
import scen  # noqa: E402
import textsec  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc1" / "tree"
SCRIPT = ROOT / "script"
TERM = {0xFFFE: "end", 0xFFFF: "null"}
TERM_W = {v: k for k, v in TERM.items()}
# name, table, base, count, end of the last string (file offsets in SLPS_023.80); getters at 0x80070C04-0x80071094
EXE_TABLES = [
    ("sys", 0xE2138, 0xE22C4, 0xC5, 0xE310E),      # system messages, menus, prompts (getter 0x80070C04)
    ("names", 0xE3110, 0xE3374, 0x132, 0xE3868),   # character names; slots 0, 0x10, 0x131 read RAM buffers instead
    ("units", 0xE3868, 0xE3ACC, 0x132, 0xE4910),   # battle unit names
    ("classes", 0xE4910, 0xE4B0C, 0xFE, 0xE4F80),  # classes / titles
    ("magic", 0xE4F80, 0xE5000, 0x40, 0xE5244),    # spell names
    ("skills", 0xE5244, 0xE52C4, 0x40, 0xE55BA),   # skill names
    ("items", 0xE55BC, 0xE588C, 0x168, 0xE6A0C),   # item names
    ("help", 0xE6A0C, 0xE6A54, 0x24, 0xE70F0),     # menu help lines
    ("places", 0xE70F0, 0xE7118, 0x14, 0xE722A),   # place names
    ("dict", 0xE722C, 0xE742C, 0x100, 0xE85C8),    # F4xx dictionary: {F4xx} = entry xx (verified by decoding)
]
EXE_PADS = [(0xE22C2, 2), (0xE310E, 2), (0xE55BA, 2), (0xE722A, 2)]  # zero words between blocks
EXE_RANGE = (0xE2138, 0xE85C8)  # E2000-E2138 is pointer data, E85C8 starts the font
MSYS_SECTIONS = [("items", 0x42800), ("magic", 0x47800), ("skills", 0x485BC)]  # item / spell / skill + appendix
MSYS_RANGE = (0x42800, 0x49E14)  # 0x477EC-0x47800 and 0x49E14-0x4A000 are zero
SCEN_ENTRIES = range(280, 560)


def _refs_str(refs):
    return " ".join(str(i) if d == 0 else "%d+%d" % (i, d) for i, d in refs)


def _refs_parse(s):
    out = []
    for t in s.split():
        i, _, d = t.partition("+")
        out.append((int(i), int(d or 0)))
    return out


def _entries(prefix, strings, refs, codec, mark_unref):
    used = {i for i, _ in refs}
    out = []
    for k, ws in enumerate(strings):
        e = {"id": "%s.%04d" % (prefix, k), "jp": codec.decode(ws[:-1]), "en": "", "term": TERM[ws[-1]]}
        if mark_unref and k not in used:
            e["unref"] = True
        out.append(e)
    return out


def pools(tree=TREE):
    """Yield (relative path, doc) for every pool, generated from the disc files."""
    c = gltext.Codec()
    data = (tree / "SCEN.DAT").read_bytes()
    for n in SCEN_ENTRIES:
        e = dat.entry(data, n)
        ts = scen.text_section(e) if e else None
        if ts is None:
            continue
        sec = ts[0]
        strings, refs, pad, _ = textsec.read_section(e, sec)
        yield "scen/s%03d.json" % (n - 280), {
            "file": "SCEN.DAT", "form": "section", "entry": n, "at": "0x%X" % sec, "pad": pad,
            "refs": _refs_str(refs), "entries": _entries("scen%03d" % (n - 280), strings, refs, c, True)}
    data = (tree / "MSYS.DAT").read_bytes()
    for name, off in MSYS_SECTIONS:
        strings, refs, pad, _ = textsec.read_section(data, off)
        yield "msys/%s.json" % name, {
            "file": "MSYS.DAT", "form": "section", "at": "0x%X" % off, "pad": pad,
            "refs": _refs_str(refs), "entries": _entries("msys.%s" % name, strings, refs, c, True)}
    data = (tree / "SLPS_023.80").read_bytes()
    for name, table, base, count, end in EXE_TABLES:
        strings, refs = textsec.read_table(data, table, base, count, end)
        yield "exe/%s.json" % name, {
            "file": "SLPS_023.80", "form": "table", "table": "0x%X" % table, "base": "0x%X" % base,
            "end": "0x%X" % end, "refs": _refs_str(refs), "entries": _entries("exe.%s" % name, strings, refs, c, True)}


def pool_bytes(doc, field="jp", codec=None):
    """Rebuild a pool from a script doc: section bytes, or (table bytes, string bytes) for an EXE table."""
    c = codec or gltext.Codec()
    strings = [c.encode(e[field]) + [TERM_W[e["term"]]] for e in doc["entries"]]
    refs = _refs_parse(doc["refs"])
    if doc["form"] == "section":
        return textsec.build_section(strings, refs, doc["pad"])
    return textsec.build_table(strings, refs)


def original_bytes(doc, tree=TREE):
    data = (tree / doc["file"]).read_bytes()
    if doc["file"] == "SCEN.DAT":
        data = dat.entry(data, doc["entry"])
    if doc["form"] == "section":
        at = int(doc["at"], 16)
        return data[at:at + struct.unpack_from("<I", data, at)[0]]
    table, base, end = (int(doc[k], 16) for k in ("table", "base", "end"))
    return data[table:table + 2 * len(doc["refs"].split())], data[base:end]


def dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def _skeleton(doc):
    """Everything the disc decides: pool fields and each entry's id, jp, term, unref (not en, notes...)."""
    return ({k: v for k, v in doc.items() if k != "entries"},
            [tuple(e.get(k) for k in ("id", "jp", "term", "unref")) for e in doc["entries"]])


def check():
    """Problems: script files missing / differing from the disc, or not rebuilding byte-identical."""
    bad, c = [], gltext.Codec()
    for rel, doc in pools():
        path = SCRIPT / rel
        if not path.exists():
            bad.append("%s missing" % rel)
            continue
        have = json.loads(path.read_text(encoding="utf-8"))
        if _skeleton(have) != _skeleton(doc):
            bad.append("%s differs from the disc" % rel)
            continue
        if pool_bytes(have, codec=c) != original_bytes(have):
            bad.append("%s does not rebuild byte-identical" % rel)
    return bad


def main(argv):
    if "--check" in argv:
        bad = check()
        print("\n".join(bad) or "script/ matches the disc and rebuilds byte-identical")
        return 1 if bad else 0
    force = "--force" in argv
    wrote = kept = 0
    for rel, doc in pools():
        path = SCRIPT / rel
        if path.exists():
            if not force:
                kept += 1
                continue
            old = json.loads(path.read_text(encoding="utf-8"))
            if any(e.get("en") for e in old["entries"]):
                print("refusing to overwrite %s: it holds English" % rel)
                kept += 1
                continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump(doc), encoding="utf-8", newline="\n")
        wrote += 1
    print("wrote %d, kept %d" % (wrote, kept))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
