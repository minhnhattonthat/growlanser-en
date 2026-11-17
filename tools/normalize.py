"""normalize.py: give every entry whose `jp` matches a rule one canonical English, through batches.merge.

    python -X utf8 tools/normalize.py            dry run: what would change
    python -X utf8 tools/normalize.py --write    merge the changes into script/

For strings repeated across scenes (elevator menus etc.) that batches translated differently. Entries without English
yet are left alone (their batch translates them). Stop the tl_run runner first if it may merge into the same scenes.
"""
import sys

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


def main(argv):
    new = {}
    for _, _, entries in batches.docs():
        for e in entries:
            want = RULES.get(e["jp"])
            if want and e.get("en") and e["en"] != want:
                new[batches.entry_key(e)] = want
                print(f"{e['id']}: {e['en']!r} -> {want!r}")
    print(f"{len(new)} entries to change")
    if "--write" in argv and new:
        batches.merge(new, overwrite=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
