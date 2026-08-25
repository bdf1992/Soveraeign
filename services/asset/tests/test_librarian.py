"""The conformance read over a typed collection, and the CLI that reaches it."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import io
import contextlib
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService
from soveraeign_asset_service.cli import main
from soveraeign_asset_service.librarian import render

PROJECT_SPEC = {
    "required_fields": ["title", "owner", "status"],
    "optional_fields": ["due"],
    "vocabularies": {"status": ["PLANNED", "ACTIVE", "CLOSED"]},
    "admits_roles": ["ORIGINAL", "REVISION"],
}


class LibraryCase(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.service = AssetService(self.state)
        self.org = self.service.organization
        for capability in ("declare:collection-type", "declare:asset-collection",
                           "organize:asset", "retract:record", "ratify:judgement"):
            self.service.grant("Bdo", "Bdo", capability)
        self.org.declare_type("project", "Project", PROJECT_SPEC, "Bdo")
        self.collection_id = self.org.declare_collection(
            "project", "Autumn launch", "Bdo")["collection_id"]

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def asset(self, name: str, body: bytes = b"payload\n") -> str:
        path = self.root / name
        path.write_bytes(body)
        return self.service.ingest(path, name, "Bdo")["asset_id"]

    def member(self, name: str = "brief.txt") -> str:
        asset_id = self.asset(name)
        self.org.add_member(self.collection_id, asset_id, "Bdo")
        return asset_id

    def describe(self, asset_id: str, payload: dict, ratify: bool = True) -> None:
        proposal = self.service.propose(asset_id, "Bdo", payload)
        if ratify:
            self.service.ratify(proposal, "Bdo")

    def verdicts(self, asset_id: str) -> dict[str, str]:
        report = self.service.librarian.conformance(self.collection_id)
        return {finding["field"]: finding["verdict"] for finding in report["findings"]
                if finding["asset_id"] == asset_id}


class ConformanceTests(LibraryCase):
    def test_a_fully_ratified_member_conforms(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        self.assertEqual(self.verdicts(asset_id),
                         {"title": "CONFORMING", "owner": "CONFORMING", "status": "CONFORMING"})

    def test_a_required_field_nobody_recorded_is_missing(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo"})
        self.assertEqual(self.verdicts(asset_id)["status"], "MISSING_FIELD")

    def test_an_unratified_description_is_a_claim_and_never_conformance(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"},
                      ratify=False)
        self.assertEqual(self.verdicts(asset_id),
                         {"title": "CLAIMED_UNRATIFIED", "owner": "CLAIMED_UNRATIFIED",
                          "status": "CLAIMED_UNRATIFIED"})

    def test_ratifying_a_claim_turns_it_into_conformance(self):
        asset_id = self.member()
        proposal = self.service.propose(
            asset_id, "Bdo", {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        self.assertEqual(self.verdicts(asset_id)["title"], "CLAIMED_UNRATIFIED")
        self.service.ratify(proposal, "Bdo")
        self.assertEqual(self.verdicts(asset_id)["title"], "CONFORMING")

    def test_a_value_outside_the_declared_vocabulary_is_refused(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "SHIPPED"})
        self.assertEqual(self.verdicts(asset_id)["status"], "VOCABULARY_REFUSED")

    def test_an_absent_optional_field_produces_no_finding(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        self.assertNotIn("due", self.verdicts(asset_id))

    def test_a_later_description_supersedes_an_earlier_one(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "PLANNED"})
        self.describe(asset_id, {"status": "ACTIVE"})
        findings = self.service.librarian.conformance(self.collection_id)["findings"]
        status = [f for f in findings if f["field"] == "status"][0]
        self.assertEqual(status["value"], "ACTIVE")
        self.assertEqual(status["verdict"], "CONFORMING")

    def test_a_relationship_payload_is_not_read_as_metadata(self):
        asset_id = self.member()
        other = self.asset("other.txt", b"other\n")
        self.describe(asset_id, {"relationship": {"predicate": "derived-from",
                                                  "dst_asset": other}})
        self.assertNotIn("relationship", self.service.librarian.describe(asset_id)["ratified"])

    def test_an_empty_collection_is_a_finding_not_a_clean_bill(self):
        report = self.service.librarian.conformance(self.collection_id)
        self.assertEqual([f["verdict"] for f in report["findings"]], ["EMPTY_COLLECTION"])

    def test_conformance_over_a_collection_that_does_not_exist_raises(self):
        with self.assertRaises(KeyError):
            self.service.librarian.conformance("collection_absent")


class ReportTests(LibraryCase):
    def test_the_report_counts_defects_across_the_whole_library(self):
        good = self.member("good.txt")
        bad = self.member("bad.txt")
        self.asset("stray.txt", b"stray\n")
        self.describe(good, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        self.describe(bad, {"title": "Winter"})
        report = self.service.library_report()
        self.assertEqual(report["counts"]["CONFORMING"], 4)
        self.assertEqual(report["counts"]["MISSING_FIELD"], 2)
        self.assertEqual(report["counts"]["UNFILED"], 1)
        self.assertEqual(report["defects"], 3)

    def test_a_clean_library_reports_no_defects(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        report = self.service.library_report()
        self.assertEqual(report["defects"], 0)
        self.assertEqual(report["unfiled"], [])

    def test_the_rendered_report_names_the_defect_and_not_the_conforming_rows(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "SHIPPED"})
        text = render(self.service.library_report())
        self.assertIn("VOCABULARY_REFUSED", text)
        self.assertIn("SHIPPED", text)
        self.assertNotIn("| title | CONFORMING", text)

    def test_the_report_carries_the_schema_every_verdict_was_judged_against(self):
        text = render(self.service.library_report())
        self.assertIn("## Declared types", text)
        self.assertIn("| project | title, owner, status | due | status: ACTIVE/CLOSED/PLANNED "
                      "| ORIGINAL, REVISION |", text)

    def test_a_library_with_no_declared_type_says_so_rather_than_showing_an_empty_table(self):
        empty = AssetService(self.root / "empty")
        try:
            self.assertIn("Nothing can be filed until one is declared.",
                          render(empty.library_report()))
        finally:
            empty.close()

    def test_the_report_is_derived_and_stores_no_verdict(self):
        asset_id = self.member()
        self.describe(asset_id, {"title": "Autumn", "owner": "Bdo", "status": "ACTIVE"})
        self.service.library_report()
        events = {r["event"] for r in self.service.receipts()}
        self.assertNotIn("asset.read-conformance", events)


class CommandTests(LibraryCase):
    def run_cli(self, *argv: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["--root", str(self.state), *argv])
        return code, buffer.getvalue()

    def test_the_cli_walks_a_library_from_grant_to_report(self):
        self.service.close()
        spec = self.root / "spec.json"
        spec.write_text(json.dumps({"required_fields": ["title"]}), encoding="utf-8")
        payload = self.root / "campaign.txt"
        payload.write_bytes(b"campaign\n")

        code, out = self.run_cli("grant", "--issuer", "Bdo", "--actor", "Ada",
                                 "--capability", "organize:asset")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("declare-type", "campaign", "--label", "Campaign",
                                 "--spec", str(spec), "--actor", "Bdo")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("declare-collection", "--type", "campaign",
                                 "--label", "Winter", "--actor", "Bdo")
        collection_id = json.loads(out)["collection_id"]
        code, out = self.run_cli("ingest", str(payload), "--label", "campaign", "--actor", "Bdo")
        asset_id = json.loads(out)["asset_id"]
        code, out = self.run_cli("add-member", collection_id, asset_id, "--actor", "Ada")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("conformance")
        self.assertEqual(json.loads(out)["counts"]["MISSING_FIELD"], 1)

        self.service = AssetService(self.state)

    def test_a_refused_command_exits_two_and_names_the_refusal(self):
        self.service.close()
        code, out = self.run_cli("declare-collection", "--type", "absent",
                                 "--label", "Nowhere", "--actor", "Bdo")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["refused"], "TYPE_UNDECLARED")
        self.service = AssetService(self.state)

    def test_the_markdown_report_is_offered_for_a_human_reader(self):
        self.service.close()
        code, out = self.run_cli("conformance", "--markdown")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("# Asset library conformance"))
        self.assertIn("EMPTY_COLLECTION", out)
        self.service = AssetService(self.state)


if __name__ == "__main__":
    unittest.main()
