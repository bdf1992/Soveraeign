from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("repository_lint", ROOT / "scripts" / "lint.py")
assert SPEC and SPEC.loader
repository_lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository_lint)


class LintPopulationTests(unittest.TestCase):
    def test_force_added_ignored_secret_is_scanned(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            synthetic = "TOKEN=" + "sk-" + "abcdefghijklmnopqrstuvwxyz123456" + "\n"
            (root / ".env").write_text(synthetic, encoding="utf-8")
            subprocess.run(["git", "add", "-f", ".env"], cwd=root, check=True)
            previous = repository_lint.ROOT
            repository_lint.ROOT = root
            try:
                files = repository_lint.repository_text_files()
                self.assertIn(root / ".env", files)
                defects = repository_lint.check_text(root / ".env", (root / ".env").read_text(encoding="utf-8"))
                self.assertTrue(any("OpenAI-style token" in defect for defect in defects))
            finally:
                repository_lint.ROOT = previous


if __name__ == "__main__":
    unittest.main()
