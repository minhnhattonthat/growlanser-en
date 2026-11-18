"""normalize.py: give every entry whose `jp` matches a rule one canonical English, through batches.merge.

    python -X utf8 tools/normalize.py            dry run: what would change
    python -X utf8 tools/normalize.py --write    merge the changes into script/
    python -X utf8 tools/normalize.py --scan [N] list repeated JP strings (N+ copies) whose English differs
    python -X utf8 tools/normalize.py --majority N [--write]   also give every scene string with N+ translated
                                                 copies its most common English (RULES win)

For strings repeated across scenes (elevator menus etc.) that batches translated differently. Entries without English
yet are left alone (their batch translates them). Stop the tl_run runner first if it may merge into the same scenes.
"""
import sys
from collections import Counter

import batches

# exact JP -> canonical English
RULES = {
    "・１Ｆ　学食": "・1F Cafeteria",
    "・２Ｆ　講義室": "・2F Lecture Rooms",
    "・３Ｆ　講義室": "・3F Lecture Rooms",
    "・４Ｆ　図書室": "・4F Library",
    "・５Ｆ　重要図書閲覧室": "・5F Restricted Reading Room",
    "・６Ｆ　薬剤研究フロア": "・6F Pharmaceutical Research",
    "・７Ｆ　学院長室フロア": "・7F Headmaster's Office",
    "・Ｂ１　特別研究室フロア": "・B1 Special Research Labs",
    "魔法学院・図書室": "Magic Academy - Library",
    "魔法学院・学院長室フロア": "Magic Academy - Headmaster's Office",
    "魔法学院・学食": "Magic Academy - Cafeteria",
    "魔法学院・屋上": "Magic Academy - Rooftop",
    "魔法学院・特別研究室フロア": "Magic Academy - Special Research Labs",
    "魔法学院・薬剤研究フロア": "Magic Academy - Pharmaceutical Research",
    "魔法学院・講義室": "Magic Academy - Lecture Rooms",
    "魔法学院・重要図書閲覧室": "Magic Academy - Restricted Reading Room",
    "バイト店員": "Part-Time Clerk",
    "学食の親父": "Cafeteria Owner",
}


def scan(min_count):
    """Repeated JP strings (min_count+ translated copies) whose English differs, most copies first."""
    groups = {}
    for _, _, entries in batches.docs():
        for e in entries:
            if e.get("en") and e["id"].startswith("scen"):
                groups.setdefault(e["jp"], {}).setdefault(e["en"], []).append(e["id"])
    rows = [(sum(map(len, ens.values())), jp, ens) for jp, ens in groups.items()
            if len(ens) > 1 and sum(map(len, ens.values())) >= min_count and jp not in RULES]
    for n, jp, ens in sorted(rows, key=lambda r: -r[0]):
        print(f"{n:3d} {jp!r}")
        for en, ids in sorted(ens.items(), key=lambda x: -len(x[1])):
            print(f"      {len(ids):3d} {en!r} ({ids[0]})")
    print(f"{len(rows)} repeated strings with differing English")


def majority(min_count):
    """JP -> its most common English, for scene strings with min_count+ translated copies (ties: first seen)."""
    groups = {}
    for _, _, entries in batches.docs():
        for e in entries:
            if e.get("en") and e["id"].startswith("scen"):
                groups.setdefault(e["jp"], Counter())[e["en"]] += 1
    return {jp: c.most_common(1)[0][0] for jp, c in groups.items() if len(c) > 1 and sum(c.values()) >= min_count}


def main(argv):
    if "--scan" in argv:
        return scan(int(argv[argv.index("--scan") + 1]) if len(argv) > argv.index("--scan") + 1 else 3)
    rules = dict(RULES)
    if "--majority" in argv:
        rules = {**majority(int(argv[argv.index("--majority") + 1])), **RULES}
    new = {}
    for _, _, entries in batches.docs():
        for e in entries:
            want = rules.get(e["jp"])
            if want and e.get("en") and e["en"] != want:
                new[batches.entry_key(e)] = want
                print(f"{e['id']}: {e['en']!r} -> {want!r}")
    print(f"{len(new)} entries to change")
    if "--write" in argv and new:
        batches.merge(new, overwrite=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
