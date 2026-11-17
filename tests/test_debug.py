"""The debug warp scene list parses: unique names, a known kind, scene ids 0-279, route steps warp.lua accepts."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))

STEP = re.compile(r"^\s*(pick\s+\d+|\d+\s+[\w+\-]+(\*\d+)?)\s*$")  # mirrors warp.lua's route parser


class ScenesTxt(unittest.TestCase):
    def test_scene_list(self):
        import warp_all
        names = [s[0] for s in warp_all.scenes()]
        self.assertEqual(len(names), len(set(names)), "duplicate scene names")
        self.assertIn("title", names)
        for line in (ROOT / "tools" / "debug" / "scenes.txt").read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            name, rest = line.split(None, 1)
            body, _, route = rest.partition(" then ")
            self.assertRegex(body, r"^(title|scene\s+\d+)", name)
            m = re.match(r"scene\s+(\d+)", body)
            if m:
                self.assertLess(int(m.group(1)), 280, name)
            for step in filter(None, route.split(";")):
                self.assertRegex(step, STEP, f"{name}: {step}")


if __name__ == "__main__":
    unittest.main()
