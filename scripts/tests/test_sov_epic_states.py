"""The epic walk keeps HELD, UNROUTED, and OWNER_HELD distinct.

Merging any two of them is the defect these cases pin. Before this module,
``sov_epic.py unrouted`` printed "routing them is Bdo's call", which reported
ordinary domain work as owner-held, and the three-way ready/held/unrouted split
hid the fact that eighteen of the unrouted issues were dependency-held as well.

Every rule below has a positive case and a case that proves the refusal fires,
including one on the scanner itself so it cannot pass vacuously.
"""

from __future__ import annotations

from pathlib import Path
import io
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_epic  # noqa: E402
from sovepic import survey, walk  # noqa: E402
from sovepic.projection import Issue  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
VILLAGES = json.loads((REPO_ROOT / ".claude" / "epic" / "villages.json").read_text("utf-8"))

# Phrases that hand a decision to the owner. A line may carry one only when it is
# denied. Trap T3 in CLAUDE.md is the reason this compares position rather than
# mere presence: "not Bdo's call" contains "Bdo's call", and a substring match
# would report the repaired text as the defect it repaired.
ATTRIBUTIONS = (
    "bdo's call",
    "bdo's judgement",
    "bdo makes",
    "question for bdo",
    "judgement item",
    "queue for bdo",
)
DENIALS = ("not ", "never ", "no ", "rather than ", "instead of ", "nor ")
ROUTING_WORDS = ("unrouted", "routing ", "route ", "routes ")
# Every output path that can tell a reader who owns an unrouted issue.
OUTPUT_PATHS = (
    "scripts/sov_epic.py",
    "scripts/sovepic/survey.py",
    "scripts/sovepic/walk.py",
    ".claude/epic/villages.json",
    ".claude/epic/README.md",
    ".claude/README.md",
    ".claude/workflows/sov-epic.js",
)


def attributions_without_denial(text: str) -> list[str]:
    """Sentences that pair routing language with an undenied owner attribution."""
    flat = " ".join(text.split()).lower()
    findings = []
    for sentence in re.split(r"(?<=[.!?])\s+", flat):
        if not any(word in sentence for word in ROUTING_WORDS):
            continue
        for phrase in ATTRIBUTIONS:
            start = sentence.find(phrase)
            while start != -1:
                before = sentence[:start]
                if not any(denial in before for denial in DENIALS):
                    findings.append(f"{phrase!r} in: {sentence[:120]}")
                start = sentence.find(phrase, start + 1)
    return findings


def evidence_paths(evidence: str) -> list[str]:
    """Repository paths named by one route's evidence string."""
    found = []
    for token in re.split(r"[\s,;]+", evidence):
        token = token.strip("'\"()[[]").rstrip(".")
        if "/" in token and not token.startswith("sov://"):
            found.append(token)
    return found


def issue(number, **overrides):
    fields = {
        "number": number,
        "title": f"Issue {number}",
        "state": "OPEN",
        "labels": [],
        "url": "",
        "updated_at": "",
        "metadata": {},
        "parse_error": None,
    }
    fields.update(overrides)
    return Issue(**fields)


def bit(number, standing="OPEN", requires=None):
    block = {
        "kind": "bit",
        "village": "trust-and-control",
        "standing": standing,
        "horizon": "NOW",
        "requires": requires or [],
    }
    return issue(number, metadata=block)


def unblock(number, provision="judgement", requested_from="owner"):
    block = {
        "kind": "unblock",
        "village": "trust-and-control",
        "standing": "OPEN",
        "horizon": "NOW",
        "requested_provision": provision,
        "requested_from": requested_from,
    }
    return issue(number, metadata=block)


def run(document, routing):
    return survey.survey(REPO_ROOT, document, routing)


def document(issues):
    return {
        "source": {"repository": "owner/repo", "root_issue": 1},
        "synced_at": "2026-08-26T00:00:00Z",
        "issues": {str(n): None for n in issues},
    }


class TwoIndependentReadingsTests(unittest.TestCase):
    """Routing answers who owns the work; readiness answers what it waits on."""

    def test_a_routed_issue_with_every_requires_satisfied_is_reachable(self):
        self.assertEqual(
            walk.reading("trust", []), {"routing": walk.ROUTED, "readiness": walk.REACHABLE}
        )

    def test_a_routed_issue_with_an_unmet_requires_is_held(self):
        self.assertEqual(
            walk.reading("trust", ["#8"]), {"routing": walk.ROUTED, "readiness": walk.HELD}
        )

    def test_an_unrouted_issue_still_reports_its_readiness(self):
        """The defect: a missing domain used to hide an unsatisfied dependency."""
        self.assertEqual(
            walk.reading(None, ["#8"]), {"routing": walk.UNROUTED, "readiness": walk.HELD}
        )

    def test_unrouted_and_reachable_is_a_real_and_distinct_combination(self):
        self.assertEqual(
            walk.reading(None, []), {"routing": walk.UNROUTED, "readiness": walk.REACHABLE}
        )


class OwnerHeldTests(unittest.TestCase):
    """Only a judgement asked of the owner is owner-held."""

    def test_an_unblock_asking_the_owner_for_a_judgement_is_owner_held(self):
        self.assertTrue(walk.owner_held(unblock(60)))

    def test_an_unblock_asking_a_worker_for_a_fixture_is_not_owner_held(self):
        self.assertFalse(walk.owner_held(unblock(61, provision="fixture", requested_from="worker")))

    def test_an_ordinary_bit_is_never_owner_held(self):
        self.assertFalse(walk.owner_held(bit(11, requires=["#8"])))
        self.assertFalse(walk.owner_held(bit(39)))

    def test_an_issue_with_no_metadata_is_never_owner_held(self):
        self.assertFalse(walk.owner_held(issue(99, metadata=None)))


class BucketTests(unittest.TestCase):
    """The four dispatch buckets stay disjoint and never borrow each other's name."""

    def survey_of(self, issues, routes):
        by_number = {i.number: i for i in issues}
        doc = document(by_number)
        routing = {"issue_routes": routes}
        # projection.issues() is bypassed: these Issue records are already parsed.
        original = survey.projection.issues
        survey.projection.issues = lambda _document: by_number
        try:
            return run(doc, routing)
        finally:
            survey.projection.issues = original

    def test_the_four_buckets_partition_the_workable_issues(self):
        issues = [
            bit(8),
            bit(11, requires=["#8"]),
            bit(12),
            bit(39),
            bit(40, requires=["#99"]),
            unblock(60),
        ]
        routes = {
            "11": {"domain": "trust", "evidence": "services/identity/"},
            "12": {"domain": "trust", "evidence": "services/registry/"},
        }
        result = self.survey_of(issues, routes)
        self.assertEqual([e["issue"] for e in result["owner_held"]], [60])
        self.assertEqual([e["issue"] for e in result["unrouted"]], [8, 39, 40])
        self.assertEqual([e["issue"] for e in result["ready"]], [12])
        self.assertEqual([e["issue"] for e in result["held"]], [11])
        self.assertEqual([e["readiness"] for e in result["unrouted"]], ["REACHABLE", "REACHABLE", "HELD"])
        total = sum(result["counts"][name] for name in ("ready", "held", "unrouted", "owner_held"))
        self.assertEqual(total, len(issues))

    def test_an_unrouted_issue_never_lands_in_the_owner_held_bucket(self):
        result = self.survey_of([bit(39)], {})
        self.assertEqual(result["owner_held"], [])
        self.assertEqual(result["unrouted"][0]["readiness"], walk.REACHABLE)

    def test_a_held_issue_never_lands_in_the_owner_held_bucket(self):
        routes = {"11": {"domain": "trust", "evidence": "services/identity/"}}
        result = self.survey_of([bit(8), bit(11, requires=["#8"])], routes)
        self.assertEqual(result["owner_held"], [])
        self.assertEqual(result["held"][0]["blocked_by"], ["#8"])

    def test_counts_carry_the_owner_held_reading(self):
        result = self.survey_of([unblock(60)], {})
        self.assertEqual(result["counts"]["owner_held"], 1)


class OutputLanguageTests(unittest.TestCase):
    """No output path may report unrouted work as a question for the owner."""

    def test_the_scanner_fires_on_the_exact_defect_it_replaced(self):
        defect = "22 open issue(s) unrouted; routing them is Bdo's call"
        self.assertTrue(attributions_without_denial(defect))

    def test_the_scanner_accepts_a_denied_attribution(self):
        repaired = "Unrouted work needs a domain, which is not Bdo's call to make."
        self.assertEqual(attributions_without_denial(repaired), [])

    def test_no_shipped_output_path_attributes_routing_to_the_owner(self):
        for relative in OUTPUT_PATHS:
            with self.subTest(path=relative):
                text = (REPO_ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(attributions_without_denial(text), [])

    def test_the_unrouted_command_reports_readiness_and_refuses_the_attribution(self):
        captured, original = io.StringIO(), sys.stdout
        sys.stdout = captured
        try:
            sov_epic.main(["unrouted"])
        finally:
            sys.stdout = original
        printed = captured.getvalue()
        self.assertIn(walk.HELD, printed)
        self.assertEqual(attributions_without_denial(printed), [])

    def test_the_owner_held_command_reports_only_genuine_seams(self):
        captured, original = io.StringIO(), sys.stdout
        sys.stdout = captured
        try:
            sov_epic.main(["owner-held"])
        finally:
            sys.stdout = original
        printed = captured.getvalue()
        self.assertIn("owner-held", printed)
        self.assertNotIn(" UNROUTED ", printed)


class RoutingEvidenceTests(unittest.TestCase):
    """A route claims a domain owner; the artifact behind it has to exist."""

    def test_every_route_names_at_least_one_path_that_exists(self):
        for number, route in VILLAGES["issue_routes"].items():
            with self.subTest(issue=number):
                candidates = evidence_paths(route["evidence"])
                self.assertTrue(candidates, f"issue {number} names no repository path")
                resolved = [
                    path
                    for path in candidates
                    if (REPO_ROOT / path).exists() or list(REPO_ROOT.glob(path))
                ]
                self.assertTrue(resolved, f"issue {number} cites {candidates}, none of which exist")

    def test_an_invented_evidence_path_is_refused(self):
        candidates = evidence_paths("services/nonexistent/CHARTER.md")
        self.assertEqual(candidates, ["services/nonexistent/CHARTER.md"])
        self.assertFalse((REPO_ROOT / candidates[0]).exists())

    def test_every_routed_domain_has_a_skill_and_a_workflow(self):
        declared = set()
        for village in VILLAGES["villages"].values():
            declared.update(village["domains"])
        for route in VILLAGES["issue_routes"].values():
            self.assertIn(route["domain"], declared)
        for domain in sorted(declared):
            with self.subTest(domain=domain):
                self.assertTrue((REPO_ROOT / ".claude" / "skills" / f"sov-{domain}").is_dir())
                self.assertTrue(
                    (REPO_ROOT / ".claude" / "skills" / f"sov-{domain}" / "SKILL.md").exists()
                )
                self.assertTrue(
                    (REPO_ROOT / ".claude" / "workflows" / f"sov-{domain}.js").exists()
                )

    def test_the_trust_domain_routes_only_where_a_service_directory_backs_it(self):
        trust = {n for n, r in VILLAGES["issue_routes"].items() if r["domain"] == "trust"}
        self.assertEqual(trust, {"11", "14"})
        for path in ("services/identity", "services/registry"):
            self.assertTrue((REPO_ROOT / path / "CHARTER.md").exists())
            self.assertTrue((REPO_ROOT / path / "contracts" / "service.json").exists())


if __name__ == "__main__":
    unittest.main()
