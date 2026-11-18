"""strings.py: write build/strings.tsv for $SKILL/scripts/textcover.py (phase 8 text coverage).

    python -X utf8 tools/strings.py [--out build/strings.tsv]

One "id<TAB>hex key" per reachable string. Text moves in RAM with every scene load, so the key is not an address but
a hash of the string's words as the printer sees them: h = (h * 31 + word) mod 2^32 over the words before the first
FFFE/FFFF. tools/debug/textlog.lua logs the same hash ("TEXT <hex>") at the printer's entry (0x8006E794, text
pointer = *(*(sp + 0x1C))). Left out: empty entries (nothing to show) and `unref` entries (no pointer reaches them).
MSYS descriptions are unpacked by msys_get to the uncompressed words, so they get the hash without dictionary codes.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import insert  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def key(words):
    h = 0
    for w in words:
        if w in (0xFFFE, 0xFFFF):
            break
        h = (h * 31 + w) % 0x100000000
    return h


def rows():
    enc = insert.Encoder("en")
    for doc in insert.docs():
        msys = doc["file"].upper().startswith("MSYS")
        for e in doc["entries"]:
            if e.get("unref") or not (e["jp"] or e["en"]):
                continue
            w = enc.words(e)
            if msys and e.get("en"):
                w = enc.en.encode(e["en"])  # shortcut: assumes msys_get yields dictionary-free words; textcover shows
            yield e["id"], key(w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "build" / "strings.tsv"))
    a = ap.parse_args()
    assert key([1, 2, 0xFFFE, 9]) == 33 and key([0xFFFF]) == 0
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for i, k in rows():
            f.write(f"{i}\t{k:X}\n")
            n += 1
    print(f"{n} strings -> {out}")


if __name__ == "__main__":
    main()
