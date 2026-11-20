"""Global system-message pass -> work/tl/p09.tsv + p09.out.tsv (merged with batches.py merge p09 --overwrite)."""
import glob
import json
import re

RULES = [
    (re.compile(r"\b(Obtained|Received|Found) an? (?=')"), r"\1 "),
    (re.compile(r"but (?:you )?(?:can't|cannot) carry"), "but you can't carry"),
    (re.compile(r"\bObtained ((?:\d+|\{[^}]*\})) Elm\b"), r"Received \1 Elm"),
]
ids, out = [], []
for f in sorted(glob.glob("script/scen/*.json")):
    for e in json.load(open(f, encoding="utf-8"))["entries"]:
        m = re.fullmatch(r"((?:\{n\}|[ 　])*)(.*?)((?:\{n\}|[ 　])*)", e["en"], re.S)
        en = m[1] + m[2].replace("{n}", " ") + m[3]  # edge {n}/blanks kept (D13), interior re-wrapped
        new = en
        for pat, rep in RULES:
            new = pat.sub(rep, new)
        new = re.sub(r"  +", " ", new) if new != en else new
        if new != en:  # compare to the stripped form: an unchanged line is not batched
            ids.append(e["id"])
            out.append(f"{e['id']}\t{new}")
open("work/tl/p09.tsv", "w", encoding="utf-8", newline="\n").write("\n".join(ids) + "\n")
open("work/tl/p09.out.tsv", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print(len(ids), "changed")
for line in out[:6]:
    print(line[:140])
