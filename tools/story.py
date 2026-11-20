"""Story-pass chapter files (skill translation.md §Review): every scene line, JP / EN, in chapter order.

    python -X utf8 tools/story.py [--max 90000]   -> work/qa/story/chapters/cNN[_P].txt (old files removed)

Chapters come from docs/synopsis.md's table; a scene listed in several chapters goes to the first one. Scenes no
chapter lists go to c16 (relationships, endings branches: synopsis §3) or c17 (optional, system, debug). A chapter
over --max characters is split by scene into parts. Then:
    python qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters --glob "*.txt"
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work/qa/story/chapters"
VOICE = re.compile(r"\{v:[0-9A-F]{4}\}")
BRANCH = "s013 s020 s093 s101 s147-s154 s237-s261 s033 s041 s047 s203-s204 s195 s248 s011".split()  # synopsis §3


def expand(spec):
    """'s021–s022, s089' -> ['s021', 's022', 's089']."""
    out = []
    for part in re.split(r"[,\s]+", spec.strip()):
        m = re.fullmatch(r"s(\d{3})(?:[–-]s(\d{3}))?", part)
        if m:
            a, b = int(m[1]), int(m[2] or m[1])
            out += ["s%03d" % i for i in range(a, b + 1)]
    return out


def chapters():
    rows = []
    for line in (ROOT / "docs/synopsis.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d+)\. ([^|]+) \| ([^|]+) \|", line)
        if m:
            rows.append((int(m[1]), m[2].strip(), expand(m[3])))
    return rows


def show(text):
    return VOICE.sub("", text).replace("{n}", " ").replace("{p}", " ¶ ")


def scene_text(sid):
    doc = json.loads((ROOT / f"script/scen/{sid}.json").read_text(encoding="utf-8"))
    cast = [e["en"] or e["jp"] for e in doc["entries"] if e.get("term") == "null" and e["jp"]]
    lines = [f"## {sid} (names in scene: {', '.join(cast) or '-'})"]
    for e in doc["entries"]:
        if e["jp"] and e.get("term") != "null":
            lines += [f">> {e['id']} | - | {show(e['jp'])}", f"   {show(e['en'])}"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max", type=int, default=90000)
    a = ap.parse_args()
    every = sorted(p.stem for p in (ROOT / "script/scen").glob("s*.json"))
    seen, plan = set(), []
    for num, title, scenes in chapters():
        own = [s for s in scenes if s in every and s not in seen]
        seen |= set(own)
        plan.append((num, title, own))
    branch = [s for s in expand(" ".join(BRANCH)) if s in every and s not in seen]
    seen |= set(branch)
    plan.append((16, "Relationships, branches and endings (synopsis §3)", branch))
    plan.append((17, "Optional, system and debug scenes (synopsis §3, §5)", [s for s in every if s not in seen]))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.txt"):
        old.unlink()
    for num, title, scenes in plan:
        parts, cur = [], ""
        for s in scenes:
            t = scene_text(s)
            if cur and len(cur) + len(t) > a.max:
                parts.append(cur)
                cur = ""
            cur += t
        parts.append(cur)
        for i, body in enumerate(parts, 1):
            name = f"c{num:02d}" + (f"_{i}" if len(parts) > 1 else "")
            head = f"# Chapter {num}. {title}" + (f" (part {i}/{len(parts)})" if len(parts) > 1 else "")
            head += "\n# '¶' = page break; voice codes removed. Speaker column '-': not stored in the script.\n\n"
            (OUT / f"{name}.txt").write_text(head + body, encoding="utf-8", newline="\n")
            print(f"{name}.txt {len(body)} chars")


if __name__ == "__main__":
    main()
