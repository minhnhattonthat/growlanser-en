"""Polish pass over docs/polish.md (skill translation.md §Review): batch the open lines for translator agents, then
merge their fixes and tick the lines.

    python -X utf8 tools/polish.py split [--size 60]   open lines with a string id -> work/tl/pNN.tsv (one row per id)
    python -X utf8 tools/polish.py ids                 open lines with no string id (fix those by hand)
    python -X utf8 tools/polish.py merge pNN ...       batches.py merge pNN --overwrite, then tick its ids' lines

pNN.tsv columns: id, JP, current English ({n} shown as a space), every polish note for that id (" || " between).
The agent writes pNN.out.tsv (id<TAB>English, same ids, same order; unchanged English for a kept line) and
pNN.notes.tsv (id<TAB>"fixed" or "waived: reason"). merge ticks each open line of those ids: "[x] ... -> fixed" or
"[x] ... -> waived: reason". A line naming several ids is ticked when its first id is.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402

POLISH = ROOT / "docs/polish.md"
TL = ROOT / "work/tl"
ID = re.compile(r"\b(?:scen\d{3}|msys\.[a-z]+|exe\.[a-z]+)\.\d{4}\b")


def open_lines():
    return [(i, ln) for i, ln in enumerate(POLISH.read_text(encoding="utf-8").splitlines()) if ln.startswith("- [ ]")]


def split(size):
    entries = batches.index()
    notes = {}
    for _, ln in open_lines():
        m = ID.search(ln)
        if m and m[0] in entries:
            notes.setdefault(m[0], []).append(ln[6:].replace("\t", " "))
    done = {p.name.split(".")[0] for p in TL.glob("p[0-9][0-9].tsv")}
    n = len(done)
    ids = list(notes)
    for k in range(0, len(ids), size):
        n += 1
        name = f"p{n:02d}"
        rows = []
        for eid in ids[k:k + size]:
            e = entries[eid]
            rows.append("\t".join([eid, e["jp"].replace("\t", " "), e["en"].replace("{n}", " "), " || ".join(notes[eid])]))
        (TL / f"{name}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        print(f"{name}.tsv {len(rows)} ids")


def merge(names):
    lines = POLISH.read_text(encoding="utf-8").splitlines()
    for name in names:
        rc = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/batches.py"), "merge", name, "--overwrite"],
                            cwd=ROOT).returncode
        if rc:
            sys.exit(f"{name}: batches.py merge failed; nothing ticked")
        verdict = dict(r[:2] for r in batches.read_tsv(TL / f"{name}.notes.tsv") if len(r) >= 2)
        ticked = 0
        for i, ln in enumerate(lines):
            m = ID.search(ln)
            if ln.startswith("- [ ]") and m and m[0] in verdict:
                lines[i] = "- [x]" + ln[5:] + " -> " + verdict[m[0]]
                ticked += 1
        print(f"{name}: {ticked} lines ticked")
    POLISH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "split":
        return split(int(argv[argv.index("--size") + 1]) if "--size" in argv else 60)
    if argv[0] == "ids":
        entries = batches.index()
        for i, ln in open_lines():
            m = ID.search(ln)
            if not (m and m[0] in entries):
                print(f"{i + 1}: {ln[:160]}")
        return 0
    if argv[0] == "merge":
        return merge(argv[1:])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
