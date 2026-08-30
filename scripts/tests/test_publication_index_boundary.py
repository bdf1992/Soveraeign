"""Defeat publication-gate readers that escape the repository index.

The publication grader claims that indexed membership and indexed bytes determine
publication evidence. This module proves that claim from outside the grader:
working-tree edits cannot satisfy route or declaration checks, untracked builders
do not become published merely because a file exists, and the one intentional
working-tree read is confined to refusing import shadows.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock
import ast
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sov_publication.py"
sys.path.insert(0, str(ROOT / "scripts"))

import sov_publication  # noqa: E402


def assigned_aliases(tree: ast.AST) -> list[str]:
    """Names that hide either the process spawn or the single git wrapper."""
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            targets, value = [node.target], node.value
        else:
            continue
        if value is None:
            continue
        spawn = isinstance(value, ast.Attribute) and value.attr == "run"
        wrapper = isinstance(value, ast.Name) and value.id == "_git"
        if spawn or wrapper:
            found.extend(target.id for target in targets if isinstance(target, ast.Name))
    return sorted(found)


def subprocess_sites(tree: ast.AST) -> list[ast.Call]:
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]


def git_vectors(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "_git" and node.args):
            continue
        first = node.args[0]
        found.append(first.value if isinstance(first, ast.Constant) and isinstance(first.value, str)
                     else "<computed>")
    return sorted(found)


def calls_named(tree: ast.AST, names: set[str]) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in names:
            found.append(node.func.id)
        elif isinstance(node.func, ast.Attribute) and node.func.attr in names:
            found.append(node.func.attr)
    return sorted(found)


class ReaderShapeIsClosed(unittest.TestCase):
    """The source shape keeps all publication evidence behind one git reader."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))

    def test_exactly_one_process_spawn_exists(self) -> None:
        self.assertEqual(1, len(subprocess_sites(self.tree)))

    def test_spawn_and_git_wrapper_are_not_rebound(self) -> None:
        self.assertEqual([], assigned_aliases(self.tree))

    def test_alias_mutant_is_detected(self) -> None:
        mutant = ast.parse(
            "import subprocess\n"
            "_spawn = subprocess.run\n"
            "_read = _git\n"
            "_spawn(['git', 'grep', '--no-index', 'x', '.'])\n"
        )
        self.assertEqual(["_read", "_spawn"], assigned_aliases(mutant))

    def test_git_reader_has_only_index_vectors(self) -> None:
        self.assertEqual(["cat-file", "ls-files"], git_vectors(self.tree))

    def test_general_file_readers_are_absent_from_publication_logic(self) -> None:
        banned = {"open", "read_text", "read_bytes", "is_file", "is_dir", "stat"}
        self.assertEqual([], calls_named(self.tree, banned))

    def test_exists_is_confined_to_import_shadow_refusal(self) -> None:
        all_exists = calls_named(self.tree, {"exists"})
        functions = {
            node.name: calls_named(node, {"exists"})
            for node in self.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(["exists"], all_exists)
        self.assertEqual(["exists"], functions.get("shadowing_modules"))


class IndexedEvidenceIgnoresUnstagedBytes(unittest.TestCase):
    """Run the real reader against a throwaway index so the repository stays untouched."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        (self.repo / "contracts").mkdir()
        (self.repo / "scripts").mkdir()
        (self.repo / "README.md").write_text("published text\n", encoding="utf-8")
        (self.repo / "contracts" / "publication-surface.json").write_text(
            json.dumps({"paths": [], "routes": []}) + "\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "add", "README.md", "contracts/publication-surface.json"],
            cwd=self.repo, check=True,
        )
        self.root_patch = mock.patch.object(sov_publication, "ROOT", self.repo)
        self.root_patch.start()
        sov_publication._CONTENT.clear()

    def tearDown(self) -> None:
        sov_publication._CONTENT.clear()
        self.root_patch.stop()
        self.tmp.cleanup()

    def test_content_returns_index_blob_not_unstaged_document(self) -> None:
        marker = "UNSTAGED-MARKER"
        (self.repo / "README.md").write_text(f"published text\n{marker}\n", encoding="utf-8")
        self.assertNotIn(marker, sov_publication.content("README.md") or "")

    def test_contract_load_ignores_unstaged_invalid_json(self) -> None:
        (self.repo / "contracts" / "publication-surface.json").write_text(
            "{ definitely not json", encoding="utf-8"
        )
        contract = sov_publication.load()
        self.assertEqual([], contract["paths"])
        self.assertEqual([], contract["routes"])

    def test_unstaged_route_text_cannot_close_an_indexed_gap(self) -> None:
        contract = {
            "routes": [{
                "audience": "reader",
                "document": "README.md",
                "must_name": ["MISSING.md"],
                "must_not_name": [],
            }]
        }
        (self.repo / "README.md").write_text("published text\nMISSING.md\n", encoding="utf-8")
        sov_publication._CONTENT.clear()
        found = sov_publication.routes(contract)
        self.assertEqual(["ROUTE_GAP"], [item["check"] for item in found])

    def test_untracked_derived_builder_cannot_satisfy_publication(self) -> None:
        ghost = "scripts/__publication_untracked_builder__.py"
        (self.repo / ghost).write_text("# local only\n", encoding="utf-8")
        found = sov_publication.surfaces(
            {"paths": [{"path": "docs/x.html", "surface": "DERIVED",
                        "builder": ghost, "check": ghost}]},
            sov_publication.tracked(),
        )
        self.assertEqual(["DERIVED_UNCHECKED", "DERIVED_UNCHECKED"],
                         [item["check"] for item in found])
        self.assertTrue(all(ghost in item["detail"] for item in found))

    def test_unstaged_import_shadow_is_refused(self) -> None:
        shadow = self.repo / "scripts" / "json.py"
        shadow.write_text("# would replace json for a fresh entrypoint process\n", encoding="utf-8")
        self.assertIn("scripts/json.py", sov_publication.shadowing_modules())


if __name__ == "__main__":
    unittest.main()
