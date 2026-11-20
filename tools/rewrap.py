"""rewrap.py: re-flow the pages of entries the fit lint fails (e.g. after a fit.py model change).

    python -X utf8 tools/rewrap.py [IDPREFIX ..] [--write]

For each wrapped entry (batches.wrap's scope) with a fit error, every page that has a wait code or fails on its own
is unwrapped ({n} -> space, edge blanks kept) and wrapped again by batches.wrap (fit.lint is the oracle, so the
new layout fits the current model). Prints old / new per entry; --write stores them. Entries still failing are
listed as manual.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402
import fit  # noqa: E402


def errors(e, en):
    font, codec = batches.tools()
    return [m for err, m in fit.lint(en, batches.budget(e, en), font, codec) if err]


def reflow(e):
    pages = []
    for page in e["en"].split("{p}"):
        if errors(e, page):
            lines = page.split("{n}")
            head = []  # leading blank lines ("　{n}") are layout (D13): kept
            while len(lines) > 1 and not lines[0].strip(" 　"):
                head.append(lines.pop(0))
            body = " ".join(x.strip(" ") for x in lines)
            lead = lines[0][:len(lines[0]) - len(lines[0].lstrip(" "))]
            page = "{n}".join(head + [batches.wrap(e, lead + body)])
        pages.append(page)
    return batches.widows(e, "{p}".join(pages))


def main(argv):
    write = "--write" in argv
    prefixes = [a for a in argv if not a.startswith("--")]
    changed = manual = 0
    for path, doc, entries in batches.docs():
        touched = False
        for e in entries:
            if not e.get("en") or e["id"] in batches.KEEP_JP or not e["id"].startswith(batches.WRAPPED):
                continue
            if prefixes and not e["id"].startswith(tuple(prefixes)):
                continue
            if not errors(e, e["en"]):
                continue
            new = reflow(e)
            bad = errors(e, new)
            print(f"{'MANUAL' if bad else 'ok    '} {e['id']}\n  old {e['en']}\n  new {new}" + (f"\n  {bad[0]}" if bad else ""))
            if bad:
                manual += 1
                continue
            if new != e["en"]:
                e["en"], touched = new, True
                changed += 1
        if touched and write:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"rewrap: {changed} re-flowed{'' if write else ' (dry run: --write)'}, {manual} manual")
    return 1 if manual else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
