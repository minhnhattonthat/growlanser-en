"""Translation batch rules (tools/batches.py): the wrapper's layout and the per-line checks; shipped English passes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import batches  # noqa: E402
import fit  # noqa: E402

DLG = {"id": "scen000.0014", "jp": "{v:0019}まだ？{p}{FC00}{v:001A}ティピちゃんです。{n}よろしく。", "term": "end"}
MENU = {"id": "exe.sys.0121", "jp": "ア{n}イ", "term": "end"}


class Batches(unittest.TestCase):
    def test_wrap_fits_and_pages(self):
        en = "{v:0019}Not yet?{p}{FC00}{v:001A}" + "This is Tippi-chan, the cheeky fairy. " * 6
        out = batches.wrap(DLG, en)
        pages = out.split("{p}")
        self.assertGreater(len(pages), 2)  # long page split into 3-line pages
        for page in pages:
            self.assertLessEqual(page.count("{n}"), 2)
        self.assertEqual([m for e, m in fit.lint(out, fit.budget(DLG["id"], {**DLG, "en": out})) if e], [])
        self.assertEqual(batches.wrap(DLG, out), out)  # idempotent on stored English

    def test_problems(self):
        ok = "{v:0019}Not yet?{p}{FC00}{v:001A}I'm Tippi-chan. Nice to meet you."
        names = [(["ティピ"], ["Tippi"], [])]
        self.assertEqual(batches.problems(DLG, ok, names), [])
        self.assertTrue(batches.problems(DLG, ok.replace("{FC00}", ""), []))  # code lost
        self.assertTrue(batches.problems(DLG, ok.replace("-chan", ""), names))  # honorific dropped
        maid = {"id": "msys.items.0106", "jp": "メイドさんの服", "term": "end"}
        self.assertEqual(batches.problems(maid, "A maid's dress.", names), [])  # not after a name
        self.assertTrue(batches.problems(DLG, ok + "★", []))  # no glyph
        self.assertTrue(batches.problems(MENU, "A", []))  # menus keep their {n} rows
        self.assertEqual(batches.problems(MENU, "A{n}B", []), [])

    def test_shipped_english(self):
        self.assertEqual(batches.main(["check"]), 0)


if __name__ == "__main__":
    unittest.main()
