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
        self.assertFalse((self.temp / "never" / "record").exists())


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

    def test_a_citation_of_an_unknown_node_or_wrong_head_or_missing_entry_fails(self) -> None:
        self.report("unknown", journal={"address": "nodes/nowhere/journal/x.json", "head": "x"})
        self.report("head", journal={"address": self.address(), "head": "sha256:wrong"})
        self.report("entry", journal={"address": self.address(), "head": self.exported["head"]},
                    cited_entries=["entry_not_there"])
        defects, _ = self.grade()
        self.assertEqual(len(defects), 3, defects)
        self.assertTrue(any("is no export under nodes/" in item for item in defects))
        self.assertTrue(any("is not an entry in" in item for item in defects))
        self.assertTrue(any("had not recorded at its cited head" in item for item in defects))

    def test_every_entry_or_receipt_id_a_report_mentions_must_resolve(self) -> None:
        self.report("deep", journal={"address": self.address(), "head": self.exported["head"]},
                    live_run={"node": {"own": {"receipt_id": "entry_never_written"}}})
        defects, _ = self.grade()
        self.assertEqual(len(defects), 1, defects)
        self.assertIn("entry_never_written", defects[0])

    def test_a_cited_entry_count_must_match_the_export(self) -> None:
        self.report("count", journal={"address": self.address(), "head": self.exported["head"],
                                      "entries": 999})
        defects, _ = self.grade()
        self.assertTrue(any("cites 999 entries" in item for item in defects), defects)

    def advanced(self) -> dict:
        """Record more on the same node and replace its export, as an active node does."""
        with nodelayer.open_node_at(self.state) as node:
            nodelayer.open_office(node, ISSUER, "principal:fixture-second",
                                  {"read:registry": nodelayer.SCOPE})
        self.exported["path"].unlink()
        return journal.export(self.state, self.temp / "nodes" / "node-local" / "journal")

    def test_a_report_keeps_its_citation_when_the_node_records_more(self) -> None:
        """The state a report read stays an ancestor; only the file naming it moves."""
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("earlier", journal={"address": self.address(), "node": "node:local",
                                        "head": self.exported["head"],
                                        "entries": first["entry_count"]},
                    cited_entries=[first["entries"][0]["entry_id"]])
        later = self.advanced()
        self.assertNotEqual(later["head"], self.exported["head"])
        defects, heads = self.grade()
        self.assertEqual(defects, [], defects)
        self.assertEqual(list(heads.values()), [later["head"]])

    def test_a_report_may_not_cite_an_entry_the_node_recorded_after_its_head(self) -> None:
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        later = self.advanced()
        document = json.loads(Path(later["path"]).read_text(encoding="utf-8"))
        after = document["entries"][first["entry_count"]]["entry_id"]
        self.report("ahead", journal={"address": self.address(), "node": "node:local",
                                      "head": self.exported["head"],
                                      "entries": first["entry_count"]},
                    cited_entries=[after])
        defects, _ = self.grade()
        self.assertTrue(any("had not recorded at its cited head" in item for item in defects),
                        defects)

    def test_an_earlier_citation_must_still_state_its_own_position(self) -> None:
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("miscounted", journal={"address": self.address(), "node": "node:local",
                                           "head": self.exported["head"],
                                           "entries": first["entry_count"] + 1})
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("its head is entry" in item for item in defects), defects)

    def test_a_stale_address_must_name_its_node_or_it_is_a_defect(self) -> None:
        """The address stays measured: a deleted file is not silently resolved away."""
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("orphan", journal={"address": self.address(),
                                       "head": self.exported["head"],
                                       "entries": first["entry_count"]})
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("which is no export under nodes/" in item for item in defects),
                        defects)

    def test_naming_the_node_resolves_a_stale_address(self) -> None:
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("named", journal={"address": self.address(), "node": "node:local",
                                      "head": self.exported["head"],
                                      "entries": first["entry_count"]},
                    cited_entries=[first["entries"][0]["entry_id"]])
        self.advanced()
        defects, _ = self.grade()
        self.assertEqual(defects, [], defects)

    def test_a_named_node_with_no_export_is_a_defect(self) -> None:
        self.report("elsewhere", journal={"address": "nodes/node-gone/journal/x.json",
                                          "node": "node:gone", "head": "x"})
        defects, _ = self.grade()
        self.assertTrue(any("has no export under nodes/" in item for item in defects), defects)

    def test_a_citation_may_not_understate_its_position(self) -> None:
        """Fewer entries than the head's position is as wrong as more."""
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        self.report("under", journal={"address": self.address(), "node": "node:local",
                                      "head": self.exported["head"],
                                      "entries": first["entry_count"] - 1})
        defects, _ = self.grade()
        self.assertTrue(any("its head is entry" in item for item in defects), defects)

    def test_an_export_filename_must_be_the_whole_head_prefix(self) -> None:
        """A shorter filename is a prefix of the head and must not pass as its name."""
        shortened = self.exported["path"].with_name(self.exported["head"][:6] + ".json")
        self.exported["path"].rename(shortened)
        defects, _ = self.grade()
        self.assertTrue(any("filename says" in item for item in defects), defects)

    def grant_id(self) -> str:
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        return next(entry["payload"]["grant_id"] for entry in document["entries"]
                    if isinstance(entry.get("payload"), dict)
                    and entry["payload"].get("grant_id"))

    def test_a_report_may_name_a_grant_the_node_recorded(self) -> None:
        """The positive half: grants are ids the node holds, not only entry ids."""
        self.report("grant", journal={"address": self.address(),
                                      "head": self.exported["head"]},
                    office_act={"grants": [{"grant_id": self.grant_id()}]})
        defects, _ = self.grade()
        self.assertEqual(defects, [], defects)

    def test_a_fabricated_grant_id_is_refused(self) -> None:
        self.report("fake", journal={"address": self.address(),
                                     "head": self.exported["head"]},
                    office_act={"grants": [{"grant_id": "grant_never_recorded_0000"}]})
        defects, _ = self.grade()
        self.assertTrue(any("grant_never_recorded_0000" in item for item in defects), defects)

    def stale(self, **over) -> dict:
        """A citation of the pre-advance state, with fields overridden."""
        first = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        journal = {"address": self.address(), "node": "node:local",
                   "head": self.exported["head"], "entries": first["entry_count"]}
        journal.update(over)
        return journal

    def test_naming_a_node_does_not_excuse_an_address_of_another_node(self) -> None:
        bad = self.address().replace("/node-local/", "/node-elsewhere/")
        self.report("wrongnode", journal=self.stale(address=bad))
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("names /" in item or "names nodes/" in item
                            for item in defects), defects)

    def test_a_declared_node_must_equal_the_nodes_name_and_not_merely_contain_it(self) -> None:
        """`CLAUDE.md` trap T3, in the direction that bites.

        The harmless reading asks whether the real node contains the declared one and
        refuses either way. The reading that lets a citation through is the containment
        run the other way, so the declared name must be a proper prefix of a real node's:
        `node:loc` against this fixture's `node:local`, with an address that is otherwise
        exactly right, so nothing but the node comparison can refuse it.
        """
        self.report("substring", journal=self.stale(node="node:loc"))
        defects, _ = self.grade()
        self.assertTrue(any("names node node:loc, which has no export" in item
                            for item in defects), defects)

    def test_naming_a_node_does_not_excuse_a_missing_address(self) -> None:
        journal = self.stale()
        del journal["address"]
        self.report("noaddress", journal=journal)
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("cites (no address), where node node:local" in item
                            for item in defects), defects)

    def test_an_address_must_be_named_by_the_head_it_declares(self) -> None:
        """A superseded address still names its own head; a fabricated one does not."""
        invented = self.address().rsplit("/", 1)[0] + "/deadbeefdead.json"
        self.report("invented", journal=self.stale(address=invented))
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("where node node:local at head" in item for item in defects),
                        defects)

    def test_an_address_may_not_reach_the_node_directory_from_anywhere(self) -> None:
        """Everything above the node directory is part of the address, not decoration."""
        tail = self.address().rsplit("/", 3)[-3:]
        self.report("traversal", journal=self.stale(
            address=self.address().rsplit("/", 4)[0] + "/elsewhere/" + "/".join(tail)))
        self.advanced()
        defects, _ = self.grade()
        self.assertTrue(any("where node node:local at head" in item for item in defects),
                        defects)

    def test_a_truncated_head_does_not_resolve_by_prefix(self) -> None:
        self.report("prefix", journal=self.stale(head=self.exported["head"][:20]))
        defects, _ = self.grade()
        self.assertTrue(any("is not an entry in" in item for item in defects), defects)

    def test_an_entry_count_that_is_not_a_number_is_a_defect_not_a_traceback(self) -> None:
        self.report("wordy", journal=self.stale(entries="many"))
        defects, _ = self.grade()
        self.assertTrue(any("cites many entries" in item for item in defects), defects)

    def test_a_node_has_one_head(self) -> None:
        second = self.exported["path"].with_name("aaaaaaaaaaaa.json")
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        second.write_text(json.dumps(document), encoding="utf-8")
        defects, _ = self.grade()
        self.assertTrue(any("a node has one head; found 2 exports" in item for item in defects),
                        defects)

    def test_an_edited_entry_is_a_defect_not_a_traceback(self) -> None:
        document = json.loads(self.exported["path"].read_text(encoding="utf-8"))
        document["entries"][2]["payload"]["granted_by"] = "principal:somebody-else"
        self.exported["path"].write_text(json.dumps(document), encoding="utf-8")
        defects, heads = self.grade()
        self.assertEqual(heads, {})
        self.assertTrue(any("digest does not match" in item for item in defects), defects)

    def test_the_directory_must_name_the_node_the_entries_name(self) -> None:
        moved = self.temp / "nodes" / "node-other" / "journal"
        moved.mkdir(parents=True)
        self.exported["path"].rename(moved / self.exported["path"].name)
        (self.temp / "nodes" / "node-local" / "journal").rmdir()
        defects, _ = self.grade()
        self.assertTrue(any("entries name node node:local, the directory names node:other"
                            in item for item in defects), defects)
        self.assertTrue(any("node:other is not in the node registry" in item
                            for item in defects), defects)

    def test_a_report_without_a_journal_field_is_left_alone(self) -> None:
        self.report("plain", observation_schema="something-else", verdict="CONFIRMED")
        self.assertEqual(self.grade()[0], [])


if __name__ == "__main__":
    unittest.main()
