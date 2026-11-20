"""Story-pass diff review: the lines of a chapter file whose English changed since an old commit.

    python -X utf8 tools/story_diff.py c01_1 [c01_2 ..] [--since 40db776] [--ctx 2]
        -> work/qa/story/diffs/cNN[_P].txt (per changed id: +-ctx lines of the current text, OLD/NEW English)

For chapters reviewed before a polish merge: a reviewer agent checks only the changed lines in context.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "work/qa/story"
ID = re.compile(r">> (\S+) \| - \| (.*)")


def old_en(rev, scene, cache={}):
    if scene not in cache:
        raw = subprocess.run(["git", "show", f"{rev}:script/scen/{scene}.json"], cwd=ROOT, capture_output=True,
                             check=True).stdout.decode("utf-8")
        cache[scene] = {e["id"]: e["en"] for e in json.loads(raw)["entries"]}
    return cache[scene]


def show(text):
    return re.sub(r"\{v:[0-9A-F]{4}\}", "", text).replace("{n}", " ").replace("{p}", " ¶ ")


def diff(part, rev, ctx):
    lines = (STORY / "chapters" / f"{part}.txt").read_text(encoding="utf-8").splitlines()
    rows = []  # (id, jp, en) in order
    for i, line in enumerate(lines):
        m = ID.match(line)
        if m:
            rows.append((m[1], m[2], lines[i + 1].strip()))
    out, n = [], 0
    for k, (eid, jp, en) in enumerate(rows):
        old = old_en(rev, "s" + eid.split(".")[0][4:]).get(eid)  # scen019.0003 lives in s019.json
        if old is None or show(old).strip() == en:
            continue
        n += 1
        out.append(f"=== {eid}")
        for cid, cjp, cen in rows[max(0, k - ctx):k]:
            out.append(f"  ctx {cid} | {cjp}\n      {cen}")
        out.append(f">> {eid} | {jp}\n   OLD: {show(old).strip()}\n   NEW: {en}")
        for cid, cjp, cen in rows[k + 1:k + 1 + ctx]:
            out.append(f"  ctx {cid} | {cjp}\n      {cen}")
    dest = STORY / "diffs" / f"{part}.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"# {part}: {n} changed lines since {rev}\n" + "\n".join(out) + "\n", encoding="utf-8")
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--since", default="40db776")
    ap.add_argument("--ctx", type=int, default=2)
    a = ap.parse_args()
    for p in a.parts:
        print(p, diff(p, a.since, a.ctx))


if __name__ == "__main__":
    main()
