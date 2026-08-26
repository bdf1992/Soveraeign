"""The epic walk keeps HELD, UNROUTED, and OWNER_HELD distinct.

Merging any two of them is the defect these cases pin. Before this module,
``sov_epic.py unrouted`` printed "routing them is Bdo's call", which reported
ordinary domain work as owner-held, and the three-way ready/held/unrouted split
hid the fact that eighteen of the unrouted issues were dependency-held as well.

Every rule below has a positive case and a case that proves the refusal fires,
including cases on the output scanner itself so it cannot pass vacuously. The
scanner is a heuristic and says so: an exact-string list pins the four sentences
that actually shipped, and the proximity rule catches the paraphrases it can.
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

# Phrases that hand a decision to the owner. One may appear only when it is
# denied within a few words. Trap T3 in CLAUDE.md is why this compares position
# rather than mere presence: "not Bdo's call" contains "Bdo's call", and a
# substring match would report the repaired text as the defect it repaired.
# Denial has to be adjacent, because "Routing is not automated, so unrouted work
# is Bdo's call" carries a denial that disarms nothing.
ATTRIBUTIONS = (
    "bdo's call",
    "bdo's judgement",
    "bdo's judgment",
    "bdo makes",
    "bdo decides",
    "question for bdo",
    "queue for bdo",
    "escalated to bdo",
    "only bdo can",
    "for bdo to decide",
)
DENIALS = ("not", "never", "no ", "nor ", "rather than", "instead of")
ROUTING_WORDS = ("unrouted", "routing ", "route ", "routes ")
# A denial only disarms the clause it sits in. "Routing is not automated, so
# unrouted work is Bdo's call" carries a denial that belongs to another clause,
# so the search for one stops at the nearest clause boundary.
CLAUSE_BREAK = re.compile(r"[.;:,|?!]|\s[-–—]\s|\b(?:so|and|but|because|yet|then)\b")
CONTEXT_WINDOW = 200

# The four sentences that shipped on main and are the defect itself. An exact
# match needs no heuristic and can never be reintroduced by paraphrase drift.
SHIPPED_DEFECTS = (
    "routing them is Bdo's call",
    "Routing it is Bdo's call, not the loop's.",
    "routing it is a judgement only Bdo makes",
    "Routing an unrouted issue is Bdo's judgement",
)

# Everything under .claude/ that a reader or an agent can be told who owns an
# unrouted issue by, plus the walk's own modules. tree.json is excluded: it is a
# verbatim projection of GitHub issue bodies this repository does not author.
SCANNED_SUFFIXES = (".md", ".js", ".json")
EXCLUDED = (Path(".claude") / "epic" / "tree.json",)


def scanned_paths() -> list[Path]:
    """Every authored output path, discovered rather than listed by hand."""
    found = [
        path
        for path in sorted((REPO_ROOT / ".claude").rglob("*"))
        if path.is_file()
        and path.suffix in SCANNED_SUFFIXES
        and path.relative_to(REPO_ROOT) not in EXCLUDED
    ]
    found.append(REPO_ROOT / "scripts" / "sov_epic.py")
    found.extend(sorted((REPO_ROOT / "scripts" / "sovepic").glob("*.py")))
    return found


def attributions_without_denial(text: str) -> list[str]:
    """Owner attributions that sit near routing language without being denied.

    A heuristic, deliberately: natural language cannot be checked exactly, and
    ``SHIPPED_DEFECTS`` carries the exact strings this cannot be trusted for.
    """
    flat = " ".join(text.replace("’", "'").split()).lower()
    findings = []
    for phrase in ATTRIBUTIONS:
        start = flat.find(phrase)
        while start != -1:
            context = flat[max(0, start - CONTEXT_WINDOW):start]
            breaks = list(CLAUSE_BREAK.finditer(context))
            clause = context[breaks[-1].end():] if breaks else context
            near_routing = any(word in context for word in ROUTING_WORDS)
            denied = any(denial in clause for denial in DENIALS)
            if near_routing and not denied:
                findings.append(f"{phrase!r} in: ...{context[-90:]}{phrase}")
            start = flat.find(phrase, start + 1)
    return findings


def evidence_paths(evidence: str) -> list[str]:
    """Repository paths named by one route's evidence string."""
    found = []
    for token in re.split(r"[\s,;]+", evidence):
        token = token.strip("'\"()[]").rstrip(".")
        if "/" in token and not token.startswith("sov://"):
            found.append(token)
    return found


def unresolved_routes(routes: dict) -> list[str]:
    """Routes whose evidence names no path that exists in this repository."""
    unresolved = []
    for number, route in sorted(routes.items()):
        candidates = evidence_paths(route["evidence"])
        resolved = [
            path for path in candidates if (REPO_ROOT / path).exists() or list(REPO_ROOT.glob(path))
        ]
        if not resolved:
            unresolved.append(f"#{number}: {route['evidence']}")
    return unresolved


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


def capture(argv):
    """Run one sov_epic command and return everything it printed."""
    buffer, original = io.StringIO(), sys.stdout
    sys.stdout = buffer
    try:
        code = sov_epic.main(argv)
    finally:
        sys.stdout = original
    return code, buffer.getvalue()


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
    """Only a judgement is owner-held. Asking the owner for anything else is not."""

    def test_an_unblock_asking_for_a_judgement_is_owner_held(self):
        self.assertTrue(walk.owner_held(unblock(60)))

    def test_asking_the_owner_for_ordinary_work_is_not_owner_held(self):
        """The schema constrains judgement->owner, never owner->judgement.

        An unblock ticket may lawfully ask the owner for a fixture or an
        observation. Reading ``requested_from`` would file that ordinary work on
        Bdo's desk, which is exactly the conflation this module refuses.
        """
        for provision in ("fixture", "contract", "capability", "observation", "grant"):
            with self.subTest(provision=provision):
                self.assertFalse(walk.owner_held(unblock(61, provision=provision)))

    def test_the_provision_decides_and_not_the_addressee(self):
        self.assertTrue(walk.owner_held(unblock(62, requested_from="controller")))
        self.assertFalse(walk.owner_held(unblock(63, provision="fixture", requested_from="owner")))

    def test_an_ordinary_bit_is_never_owner_held(self):
        self.assertFalse(walk.owner_held(bit(11, requires=["#8"])))
        self.assertFalse(walk.owner_held(bit(39)))

    def test_a_non_unblock_kind_carrying_the_key_is_not_owner_held(self):
        block = {"kind": "bit", "requested_provision": "judgement", "requested_from": "owner"}
        self.assertFalse(walk.owner_held(issue(64, metadata=block)))

    def test_an_issue_with_no_metadata_is_never_owner_held(self):
        self.assertFalse(walk.owner_held(issue(99, metadata=None)))


class BucketTests(unittest.TestCase):
    """The four dispatch buckets stay disjoint; the readings still overlap them."""

    def survey_of(self, issues, routes):
        by_number = {i.number: i for i in issues}
        document = {
            "source": {"repository": "owner/repo", "root_issue": 1},
            "synced_at": "2026-08-26T00:00:00Z",
            "issues": {},
        }
        original = survey.projection.issues
        survey.projection.issues = lambda _document: by_number
        try:
            return survey.survey(REPO_ROOT, document, {"issue_routes": routes})
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
        total = sum(result["counts"][name] for name in ("ready", "held", "unrouted", "owner_held"))
        self.assertEqual(total, len(issues))

    def test_the_readings_count_the_states_the_buckets_understate(self):
        """#40 is dependency-held and lands in the unrouted bucket, not the held one."""
        issues = [bit(8), bit(11, requires=["#8"]), bit(39), bit(40, requires=["#99"])]
        routes = {"11": {"domain": "trust", "evidence": "services/identity/"}}
        counts = self.survey_of(issues, routes)["counts"]
        self.assertEqual(counts["held"], 1)
        self.assertEqual(counts["dependency_held"], 2)
        self.assertEqual(counts["unrouted"], 3)
        self.assertEqual(counts["no_domain_owner"], 3)

    def test_an_unrouted_issue_never_lands_in_the_owner_held_bucket(self):
        result = self.survey_of([bit(39)], {})
        self.assertEqual(result["owner_held"], [])
        self.assertEqual(result["unrouted"][0]["readiness"], walk.REACHABLE)

    def test_a_held_issue_never_lands_in_the_owner_held_bucket(self):
        routes = {"11": {"domain": "trust", "evidence": "services/identity/"}}
        result = self.survey_of([bit(8), bit(11, requires=["#8"])], routes)
        self.assertEqual(result["owner_held"], [])
        self.assertEqual(result["held"][0]["blocked_by"], ["#8"])

    def test_a_ticket_asking_the_owner_for_a_fixture_stays_dispatchable(self):
        result = self.survey_of([unblock(60, provision="fixture")], {})
        self.assertEqual(result["owner_held"], [])
        self.assertEqual([e["issue"] for e in result["unrouted"]], [60])


class ScannerTests(unittest.TestCase):
    """The output scanner has to fire on the defect and stay quiet on the repair."""

    def test_it_fires_on_every_sentence_that_actually_shipped(self):
        for defect in SHIPPED_DEFECTS:
            with self.subTest(defect=defect):
                self.assertTrue(attributions_without_denial(defect))

    def test_it_fires_on_the_paraphrases_a_naive_check_would_miss(self):
        cases = (
            "Routing is not automated, so unrouted work is Bdo's call.",
            "- Unrouted work is not a backlog\n- Routing them is Bdo's call",
            "Routing them is Bdo’s call.",
            "There is no evidence yet, so routing them is Bdo's call.",
            "An unrouted issue must be escalated to Bdo for a decision.",
            "These issues are unrouted. Deciding them is Bdo's call.",
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertTrue(attributions_without_denial(case), case)

    def test_it_stays_quiet_on_correct_prose(self):
        cases = (
            "Unrouted work needs a domain, which is not Bdo's call to make.",
            "Route each issue by evidence, and file a judgement item only for an owner seam.",
            "Routing is decided by evidence; a judgement item is something else entirely.",
            "The walk reports unrouted work as needing a domain, never as a question for Bdo.",
            "Whether that drift turns the repository red is Bdo's call.",
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(attributions_without_denial(case), [], case)


class OutputLanguageTests(unittest.TestCase):
    """No shipped output path may report unrouted work as a question for the owner."""

    def test_the_scan_covers_the_files_this_change_added(self):
        covered = {path.relative_to(REPO_ROOT).as_posix() for path in scanned_paths()}
        for required in (
            "scripts/sov_epic.py",
            "scripts/sovepic/walk.py",
            "scripts/sovepic/survey.py",
            ".claude/README.md",
            ".claude/epic/README.md",
            ".claude/epic/NARRATIVE.md",
            ".claude/epic/villages.json",
            ".claude/workflows/sov-epic.js",
            ".claude/workflows/sov-trust.js",
            ".claude/skills/sov-trust/SKILL.md",
        ):
            self.assertIn(required, covered)

    def test_no_shipped_output_path_attributes_routing_to_the_owner(self):
        for path in scanned_paths():
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(attributions_without_denial(text), [])

    def test_no_shipped_output_path_carries_a_sentence_that_shipped_as_the_defect(self):
        for path in scanned_paths():
            text = path.read_text(encoding="utf-8")
            for defect in SHIPPED_DEFECTS:
                with self.subTest(path=path.name, defect=defect):
                    self.assertNotIn(defect, text)

    def test_the_unrouted_command_prints_a_readiness_on_every_issue_line(self):
        code, printed = capture(["unrouted"])
        self.assertEqual(code, 0)
        lines = [line for line in printed.splitlines() if line.startswith("#")]
        self.assertTrue(lines)
        for line in lines:
            self.assertTrue(
                walk.HELD in line or walk.REACHABLE in line, f"no readiness on {line!r}"
            )
        self.assertEqual(attributions_without_denial(printed), [])

    def test_the_owner_held_command_prints_the_tickets_it_is_given(self):
        original = sov_epic._survey
        sov_epic._survey = lambda _root: {
            "owner_held": [
                {
                    "issue": 60,
                    "village": "trust-and-control",
                    "title": "Where principal identity lives",
                    "readiness": walk.REACHABLE,
                }
            ]
        }
        try:
            code, printed = capture(["owner-held"])
        finally:
            sov_epic._survey = original
        self.assertEqual(code, 0)
        self.assertIn("#60", printed)
        self.assertIn("Where principal identity lives", printed)
        self.assertIn("1 open issue(s) owner-held", printed)

    def test_the_owner_held_command_refuses_to_read_as_the_whole_owner_queue(self):
        code, printed = capture(["owner-held"])
        self.assertEqual(code, 0)
        self.assertIn("STATUS.yaml", printed)
        self.assertIn("decisions/", printed)

    def test_status_prints_the_buckets_and_the_readings_separately(self):
        code, printed = capture(["status"])
        self.assertEqual(code, 0)
        self.assertIn("buckets:", printed)
        self.assertIn("dependency-held", printed)
        self.assertIn("no-domain-owner", printed)
        self.assertEqual(attributions_without_denial(printed), [])


class RoutingEvidenceTests(unittest.TestCase):
    """A route claims a domain owner; the artifact behind it has to exist."""

    def test_every_route_names_at_least_one_path_that_exists(self):
        self.assertEqual(unresolved_routes(VILLAGES["issue_routes"]), [])

    def test_an_invented_evidence_path_is_refused(self):
        doctored = dict(VILLAGES["issue_routes"])
        doctored["999"] = {"domain": "trust", "evidence": "services/nonexistent/CHARTER.md"}
        self.assertEqual(
            unresolved_routes(doctored), ["#999: services/nonexistent/CHARTER.md"]
        )

    def test_evidence_naming_no_path_at_all_is_refused(self):
        doctored = {"998": {"domain": "trust", "evidence": "it is obviously ours"}}
        self.assertEqual(unresolved_routes(doctored), ["#998: it is obviously ours"])

    def test_every_routed_domain_has_a_skill_and_a_workflow(self):
        declared = set()
        for village in VILLAGES["villages"].values():
            declared.update(village["domains"])
        for route in VILLAGES["issue_routes"].values():
            self.assertIn(route["domain"], declared)
        for domain in sorted(declared):
            with self.subTest(domain=domain):
                skill = REPO_ROOT / ".claude" / "skills" / f"sov-{domain}" / "SKILL.md"
                workflow = REPO_ROOT / ".claude" / "workflows" / f"sov-{domain}.js"
                self.assertTrue(skill.exists(), f"{domain} has no skill")
                self.assertTrue(workflow.exists(), f"{domain} has no workflow")

    def test_the_trust_domain_routes_only_where_a_service_directory_backs_it(self):
        trust = {n for n, r in VILLAGES["issue_routes"].items() if r["domain"] == "trust"}
        self.assertEqual(trust, {"11", "14"})
        for path in ("services/identity", "services/registry"):
            self.assertTrue((REPO_ROOT / path / "CHARTER.md").exists())
            self.assertTrue((REPO_ROOT / path / "contracts" / "service.json").exists())

    def test_the_unrouted_villages_have_no_domain_to_claim_them(self):
        """Authority, gates, the broker, and #39 stay unrouted on purpose."""
        routes = VILLAGES["issue_routes"]
        for number in ("12", "13", "15", "39"):
            self.assertNotIn(number, routes)


if __name__ == "__main__":
    unittest.main()
