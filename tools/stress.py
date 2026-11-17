"""stress.py: write a --qa stress file of ruler lines for the width gate (build.py --qa F --out work/qa/bN).

    python -X utf8 tools/stress.py OUT.tsv ids scen000.0186:4 scen000.0003:1 ...   rulers into these ids (lines)
    python -X utf8 tools/stress.py OUT.tsv tables [POOL ..]   rulers into every EXE table entry (minus POOLs,
                                                              default sys dict) + the first 3 MSYS descriptions

Ruler: "A234567890B234567890...H234567890", every character 6 px, so character k ends at 6k px; the engine wraps
or the window clips at the budget, read it off a zoomed shot.
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = "".join(c + "234567890" for c in "ABCDEFGH")  # 80 chars = 480 px


def ruler(n=1):
    return "{n}".join([R] * n)


def tables(skip):
    for f in sorted(glob.glob(str(ROOT / "script/exe/*.json"))) + sorted(glob.glob(str(ROOT / "script/msys/*.json"))):
        msys = "msys" in Path(f).parent.name
        if not msys and Path(f).stem in skip:
            continue
        for k, e in enumerate(json.loads(Path(f).read_text(encoding="utf-8"))["entries"]):
            if e["jp"] and (not msys or k < 3):  # MSYS blocks only hold a few multi-line rulers
                yield e["id"], ruler(4 if msys else 1)


def main(a):
    out, mode, rest = a[0], a[1], a[2:]
    if mode == "ids":
        rows = [(i, ruler(int(n or 4))) for i, _, n in (s.partition(":") for s in rest)]
    else:
        rows = list(tables(set(rest) or {"sys", "dict"}))
    Path(out).write_text("".join("%s\t%s\n" % r for r in rows), encoding="utf-8", newline="\n")
    print("%d lines -> %s" % (len(rows), out))


if __name__ == "__main__":
    main(sys.argv[1:])
