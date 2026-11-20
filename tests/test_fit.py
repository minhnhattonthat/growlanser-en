"""Fit lint (tools/fit.py) against the widths measured in-game (docs/windows.md), and the script passes it."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fit  # noqa: E402

RULER = "".join(c + "234567890" for c in "ABCDEFGH")  # 6 px per character


def errors(eid, text, term="end"):
    return [m for err, m in fit.lint(text, fit.budget(eid, {"en": text, "term": term})) if err]


class Fit(unittest.TestCase):
    def test_measured_rulers(self):
        # dialogue wrapped after 48 ruler chars, item list after 16, name tag clipped after 24
        self.assertEqual(errors("scen000.0186", RULER[:48]), [])
        self.assertTrue(errors("scen000.0186", RULER[:49]))
        self.assertEqual(errors("exe.items.0001", RULER[:16]), [])
        self.assertTrue(errors("exe.items.0001", RULER[:17]))
        self.assertEqual(errors("scen000.0003", RULER[:24], "null"), [])
        self.assertTrue(errors("scen000.0003", RULER[:25], "null"))

    def test_lines_per_page(self):
        self.assertEqual(errors("scen000.0186", "a{n}b{n}c{p}d{n}e{n}f"), [])
        self.assertTrue(errors("scen000.0186", "a{n}b{n}c{n}d"))
        self.assertTrue(errors("exe.items.0001", "{F401}"))  # dictionary codes write Japanese

    def test_wait_codes(self):
        # in game (work/qa/waitwrap.tsv, warp dn_glocian f2464) the pen continues across waits and the resumed print
        # wraps on a code's end: "... Such a fra" / "il, sorrowful voice."
        line = ("{v:0001}...Hmm. Yes.{FFF9}{FFFB} {v:0003}It's faint, but I can hear singing...{FFF9}{FFFB} "
                "{v:0004}Such a frail")
        self.assertTrue(errors("scen070.0017", line))
        self.assertEqual(errors("scen070.0017", line[:-6]), [])

    def test_script(self):
        font, codec = fit.enfont.load(), fit.enfont.EnCodec()
        bad = [(e["id"], m) for e in fit.entries([])
               for err, m in fit.lint(e["en"], fit.budget(e["id"], e), font, codec)]
        self.assertEqual(bad, [])  # warnings too: an unmeasured guess must still hold (fit the JP's own bound)

    def test_choice_prompts(self):
        # a prompt shares the 3-row box with its "・" options: an extra EN line scrolls an option out of view
        # shortcut: only prompts followed by "・" entries; built-in Yes/No prompts (scen018 dev menu) are not marked
        import json
        import re
        lines = lambda s: len(re.split(r"\{n\}|\n", s.split("{p}")[-1]))
        bad = []
        for f in sorted((Path(__file__).resolve().parents[1] / "script" / "scen").glob("*.json")):
            es = json.loads(f.read_text(encoding="utf-8"))["entries"]
            for e, nx in zip(es, es[1:]):
                if nx["jp"].startswith("・") and not e["jp"].startswith("・") and e["en"] \
                        and lines(e["en"]) > lines(e["jp"]):
                    bad.append(e["id"])
        self.assertEqual(bad, [])

    def test_description_widows(self):
        # item/spell/skill help text is hand-wrapped: no last line of one word ("attacks.", "ally.", "+5%.")
        import json
        LABELS = ("Attribute:", "Target:", "Recovery:", "Removed by:", "Activation:", "Duration:", " On")
        bad = []
        for t in ("items", "magic", "skills"):
            f = Path(__file__).resolve().parents[1] / "script" / "msys" / f"{t}.json"
            for e in json.loads(f.read_text(encoding="utf-8"))["entries"]:
                ls = (e.get("en") or "").split("{n}")
                if len(ls) > 1 and len(ls[-1].split()) == 1 or any(
                        l.rstrip().endswith(LABELS) for l in ls[:-1]) or any(  # label cut from its value
                        l.rstrip().endswith(" Removed") for l in ls[:-1]):
                    bad.append(e["id"])
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
