"""check.py: the repo's one-command check (pre-commit runs it). Runs every tests/test_*.py with unittest.

Tests that need the disc image skip themselves when rom/ is absent, so a fresh clone still passes. Exit 1 on any failure."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
