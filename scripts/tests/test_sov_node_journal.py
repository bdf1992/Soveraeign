"""Cases for node journal custody: export, restore, truncation, and the citation gate.

Every case builds its own node under a temporary directory and its own nodes/ and
reports/ trees, so the suite reads nothing from the repository's committed exports.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovfresh import node as nodelayer  # noqa: E402
from sovnode import journal  # noqa: E402

ISSUER = "principal:fixture-root"
OPERATOR = "principal:fixture-operator"


class JournalCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.temp = Path(self._temp.name)
        self.state = self.temp / "node"
        with nodelayer.open_node_at(self.state) as node:
            nodelayer.open_office(node, ISSUER, OPERATOR, {"read:registry": nodelayer.SCOPE})
        self.exported = journal.export(self.state, self.temp / "nodes" / "node-local" / "journal")

    def truncated(self) -> Path:
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        document["entries"] = document["entries"][:-1]
        document["entry_count"] -= 1
        document["head_digest"] = document["entries"][-1]["entry_digest"]
        path = self.temp / "truncated.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path


class ExportAndRestore(JournalCase):
    def test_the_export_is_named_by_its_head_and_replays_to_it(self) -> None:
        self.assertEqual(self.exported["path"].stem, self.exported["head"][:12])
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.assertEqual(journal.custody.verify_export(document), self.exported["head"])

    def test_restore_carries_the_office_into_an_empty_node(self) -> None:
        restored = self.temp / "restored"
        count = journal.restore(self.exported["path"], restored, self.exported["head"])
        self.assertEqual(count, self.exported["entries"])
        with nodelayer.open_node_at(restored) as node:
            entries = node.record.reconstruct()
            self.assertEqual(node.record.head(), self.exported["head"])
            self.assertEqual(nodelayer.console_authority.root_issuer(entries, node.node_id),
                             ISSUER)
            held = nodelayer.console_authority.held(entries, OPERATOR, node.node_id)
            self.assertIn("read:registry", {record["capability"] for record in held})

    def test_restore_refuses_a_node_that_already_holds_a_journal(self) -> None:
        with self.assertRaises(journal.custody.RestoreRefused):
            journal.restore(self.exported["path"], self.state, self.exported["head"])

    def test_a_truncated_export_verifies_alone_and_refuses_against_the_outside_head(self) -> None:
        truncated = self.truncated()
        document = json.loads(truncated.read_text(encoding="utf-8"))
        self.assertNotEqual(journal.custody.verify_export(document), self.exported["head"])
        with self.assertRaises(journal.custody.TruncatedExport):
            journal.restore(truncated, self.temp / "never", self.exported["head"])
        self.assertFalse((self.temp / "never" / "record").exists()
                         and journal.RecordService(self.temp / "never" / "record").head()
                         != journal.GENESIS)


class CitationGate(JournalCase):
    def report(self, name: str, **fields) -> None:
        reports = self.temp / "reports"
        reports.mkdir(exist_ok=True)
        (reports / f"{name}.json").write_text(json.dumps(fields), encoding="utf-8")

    def grade(self) -> tuple[list[str], dict[str, str]]:
        return journal.grade(self.temp / "nodes", self.temp / "reports")

    def address(self) -> str:
        return self.exported["path"].resolve().as_posix()

    def test_a_clean_export_and_a_resolving_citation_pass(self) -> None:
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("ok", journal={"address": self.address(), "head": self.exported["head"]},
                    cited_entries=[document["entries"][0]["entry_id"]])
        defects, heads = self.grade()
        self.assertEqual(defects, [], defects)
        self.assertEqual(list(heads.values()), [self.exported["head"]])

    def test_a_misnamed_export_is_a_defect(self) -> None:
        renamed = self.exported["path"].with_name("000000000000.json")
        self.exported["path"].rename(renamed)
        defects, _ = self.grade()
        self.assertTrue(any("filename says 000000000000" in item for item in defects), defects)

    def test_a_citation_of_an_unknown_export_or_wrong_head_or_missing_entry_fails(self) -> None:
        self.report("unknown", journal={"address": "nodes/nowhere/journal/x.json", "head": "x"})
        self.report("head", journal={"address": self.address(), "head": "sha256:wrong"})
        self.report("entry", journal={"address": self.address(), "head": self.exported["head"]},
                    cited_entries=["entry_not_there"])
        defects, _ = self.grade()
        self.assertEqual(len(defects), 3, defects)
        self.assertTrue(any("not a verified export" in item for item in defects))
        self.assertTrue(any("cites head" in item for item in defects))
        self.assertTrue(any("cites entries absent" in item for item in defects))

    def test_a_report_without_a_journal_field_is_left_alone(self) -> None:
        self.report("plain", observation_schema="something-else", verdict="CONFIRMED")
        self.assertEqual(self.grade()[0], [])


if __name__ == "__main__":
    unittest.main()
