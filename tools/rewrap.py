"""rewrap.py: re-flow the pages of entries the fit lint fails (e.g. after a fit.py model change).

    python -X utf8 tools/rewrap.py [IDPREFIX ..] [--write]
    python -X utf8 tools/rewrap.py --pages [IDPREFIX ..] [--write]   dialogue {p} that cuts a sentence -> sentence end

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


def mid_sentence(a, b):
    """A {p} between pages a and b that cuts a sentence, which page_flow may move: plain text both sides."""
    a = a.rstrip(" ")
    return bool(a) and not a.endswith("}") and not batches.sentence_end(a.split()[-1]) \
        and not b.startswith(("{", " ", "　")) and "　" not in a + b and not a.startswith(" ")


def hard_break(page, b):
    """A {n} the wrapper didn't make (the next line's first word would fit): a list or legend, laid out by hand."""
    lines = page.split("{n}")
    return any(c.split(" ")[0] and batches.fits(f"{a} {c.split(' ')[0]}", b) for a, c in zip(lines, lines[1:]))


def sentence_pages(e):
    """Merge each run of pages joined by mid-sentence breaks and lay it out again with batches.page_flow."""
    pages = e["en"].split("{p}")
    b = batches.budget(e, e["en"])
    out, run = [], [pages[0]]
    for page in pages[1:] + [None]:
        if page is not None and mid_sentence(run[-1], page):
            run.append(page)
            continue
        if len(run) > 1 and not any(hard_break(p, b) for p in run):
            words = " ".join(p.replace("{n}", " ") for p in run).split()
            out += batches.page_flow(words, b, b[3])
        else:
            out += run
        run = [page]
    return batches.widows(e, "{p}".join(out))


def main(argv):
    write = "--write" in argv
    if "--pages" in argv:
        return pages_main(write, [a for a in argv if not a.startswith("--")])
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


def pages_main(write, prefixes):
    """--pages: page breaks at sentence ends (batches.page_flow) for dialogue whose {p} cuts a sentence."""
    changed = left = 0
    for path, doc, entries in batches.docs():
        touched = False
        for e in entries:
            if not e.get("en") or e["id"] in batches.KEEP_JP or not e["id"].startswith("scen") \
                    or batches.budget(e, e["en"])[0] != "scen" or "{p}" not in e["en"]:
                continue
            if prefixes and not e["id"].startswith(tuple(prefixes)):
                continue
            new = sentence_pages(e)
            if new == e["en"]:
                continue
            if errors(e, new):
                left += 1
                print(f"KEEP   {e['id']} (new layout fails the lint)")
                continue
            print(f"ok     {e['id']}\n  old {e['en']}\n  new {new}")
            e["en"], touched = new, True
            changed += 1
        if touched and write:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"rewrap --pages: {changed} re-paged{'' if write else ' (dry run: --write)'}, {left} kept")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
