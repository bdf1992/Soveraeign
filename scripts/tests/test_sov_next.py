"""Cases for the signpost reconciler and the roadmap lane grader it calls.

Every check has a positive case and a case proving the required refusal, per
`AGENTS.md` Testing and verification. Nothing here reaches the network or the
coordination surface.

The lane cases live here rather than in a module of their own because the
tooling suite partitions by module and a ninetieth module repacks every shard:
measured, it moved two multi-second readers onto the shard already holding a
third and put the suite past its catastrophic ceiling. The grader is reached
through ``sov_next``, so this is also where its cases belong.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

import roadmap_lanes  # noqa: E402
import sov_next  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


ROADMAP = """# Phased Attack Plan

## F2 · Conformance corpus

Text.

## F3 · Minimal local kernel

Text.

## Name crosswalk

| Phase | Epic ticket | Governing debt or objective | Drawn as |
| --- | --- | --- | --- |
| `F3` Minimal local kernel | `#6` Shared Kernel | `ENGINEERING.md` named module debt: split `core.py` | `K` in `diagrams/present.md` |

Trailing prose.
"""


def _issue(number, kind, standing, requires=(), state="OPEN"):
    return {"number": number, "title": f"Issue {number}", "state": state,
            "metadata": {"kind": kind, "standing": standing,
                         "horizon": "NOW", "requires": list(requires)}}


class CrosswalkParsing(unittest.TestCase):
    def test_rows_parse_and_the_separator_is_skipped(self):
        rows = sov_next.crosswalk(ROADMAP)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["phase"], "F3")
        self.assertEqual(rows[0]["ticket"], "6")

    def test_absent_table_yields_no_rows_rather_than_raising(self):
        self.assertEqual(sov_next.crosswalk("# Roadmap\n\nNo table here.\n"), [])

    def test_phases_resolve_from_headings(self):
        self.assertEqual(sov_next.roadmap_phases(ROADMAP),
                         {"F2": "Conformance corpus", "F3": "Minimal local kernel"})


class DeclaredGate(unittest.TestCase):
    def test_gate_parses(self):
        self.assertEqual(sov_next.declared_gate("next_gate: F0_FOUNDING_CLOSURE\n"),
                         "F0_FOUNDING_CLOSURE")

    def test_absent_gate_is_none_not_a_crash(self):
        self.assertIsNone(sov_next.declared_gate("phase: FOUNDING\n"))


class ReachableWork(unittest.TestCase):
    def test_a_bit_with_no_unsatisfied_requirement_is_reachable(self):
        ready = sov_next.epic_ready({"6": _issue("6", "bit", "OPEN")})
        self.assertEqual([row["number"] for row in ready], ["6"])

    def test_a_bit_blocked_by_an_open_requirement_is_not_reachable(self):
        issues = {"6": _issue("6", "bit", "OPEN"),
                  "7": _issue("7", "bit", "OPEN", requires=["#6"])}
        self.assertEqual([row["number"] for row in sov_next.epic_ready(issues)], ["6"])

    def test_a_requirement_that_is_settled_no_longer_blocks(self):
        issues = {"6": _issue("6", "bit", "RATIFIED"),
                  "7": _issue("7", "bit", "OPEN", requires=["#6"])}
        self.assertEqual([row["number"] for row in sov_next.epic_ready(issues)], ["7"])

    def test_containers_are_not_reachable_work(self):
        """An epic or village holds work; it is not work."""
        issues = {"1": _issue("1", "epic-of-epics", "OPEN"),
                  "4": _issue("4", "village", "OPEN")}
        self.assertEqual(sov_next.epic_ready(issues), [])

    def test_a_closed_ticket_is_not_reachable(self):
        self.assertEqual(sov_next.epic_ready({"6": _issue("6", "bit", "OPEN", state="CLOSED")}), [])


class Resolution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "diagrams").mkdir()
        (self.root / "diagrams" / "present.md").write_bytes(b"drawn\n")
        self.addCleanup(self.tmp.cleanup)

    def _resolve(self, roadmap=ROADMAP):
        rows = sov_next.crosswalk(roadmap)
        phases = sov_next.roadmap_phases(roadmap)
        ready = [{"number": "6"}]
        return sov_next.resolve(rows, ready, phases, roadmap, root=self.root)

    def test_a_resolving_crosswalk_reports_no_defect(self):
        self.assertEqual(self._resolve(), [])

    def test_a_row_drawing_to_a_missing_view_is_a_defect(self):
        broken = ROADMAP.replace("diagrams/present.md", "diagrams/absent.md")
        self.assertIn("absent.md", " ".join(self._resolve(broken)))

    def test_a_row_naming_a_phase_absent_from_the_roadmap_is_a_defect(self):
        broken = ROADMAP.replace("## F3 · Minimal local kernel", "## F9 · Renamed")
        self.assertIn("F3", " ".join(self._resolve(broken)))

    def test_a_row_naming_no_ticket_is_a_defect(self):
        broken = ROADMAP.replace("`#6` Shared Kernel", "Shared Kernel")
        self.assertIn("names no epic ticket", " ".join(self._resolve(broken)))

    def test_losing_the_module_debt_reference_is_a_defect(self):
        broken = ROADMAP.replace("split `core.py`", "split the service")
        self.assertIn("module debt", " ".join(self._resolve(broken)))

    def test_an_empty_frontier_is_a_state_not_a_defect(self):
        """Every open ticket being held is legitimate; failing the build on it
        teaches operators to clear the alarm unread."""
        rows = sov_next.crosswalk(ROADMAP)
        defects = sov_next.resolve(rows, [], sov_next.roadmap_phases(ROADMAP),
                                   ROADMAP, root=self.root)
        self.assertEqual(defects, [])


class CrosswalkLiveness(unittest.TestCase):
    """A crosswalk row asserts an identity. It must resolve to live work."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "diagrams").mkdir()
        (self.root / "diagrams" / "present.md").write_bytes(b"drawn\n")
        self.addCleanup(self.tmp.cleanup)

    def _resolve(self, issues):
        return sov_next.resolve(sov_next.crosswalk(ROADMAP), [{"number": "6"}],
                                sov_next.roadmap_phases(ROADMAP), ROADMAP,
                                root=self.root, issues=issues)

    def test_a_row_naming_a_live_ticket_reports_no_defect(self):
        self.assertEqual(self._resolve({"6": _issue("6", "bit", "OPEN")}), [])

    def test_a_row_naming_a_closed_ticket_is_a_defect(self):
        """The ticket can die while the job does not; the row must not lie."""
        defects = self._resolve({"6": _issue("6", "bit", "OPEN", state="CLOSED")})
        self.assertIn("closed", " ".join(defects))

    def test_a_row_naming_an_absent_ticket_is_a_defect(self):
        self.assertIn("absent from the epic projection", " ".join(self._resolve({})))

    def test_without_a_projection_liveness_is_not_asserted(self):
        """No tree available is not evidence the ticket is dead."""
        self.assertEqual(sov_next.resolve(sov_next.crosswalk(ROADMAP), [{"number": "6"}],
                                          sov_next.roadmap_phases(ROADMAP), ROADMAP,
                                          root=self.root), [])


class ActionableKinds(unittest.TestCase):
    def test_a_story_is_reachable_work(self):
        """Stories are a declared ticket kind; a reconciler blind to them
        reports an empty frontier while real work waits."""
        ready = sov_next.epic_ready({"67": _issue("67", "story", "PROPOSED")})
        self.assertEqual([row["number"] for row in ready], ["67"])

    def test_a_null_requires_list_does_not_crash(self):
        issue = _issue("67", "story", "PROPOSED")
        issue["metadata"]["requires"] = None
        self.assertEqual([row["number"] for row in sov_next.epic_ready({"67": issue})], ["67"])


class ClosedWithoutSettledStanding(unittest.TestCase):
    def test_a_closed_ticket_with_an_open_standing_is_reported(self):
        issues = {"6": _issue("6", "bit", "OPEN", state="CLOSED")}
        self.assertIn("#6", " ".join(sov_next.closed_unsettled(issues)))

    def test_a_closed_ticket_that_is_settled_is_not_reported(self):
        issues = {"6": _issue("6", "bit", "RATIFIED", state="CLOSED")}
        self.assertEqual(sov_next.closed_unsettled(issues), [])

    def test_an_open_ticket_is_never_reported_here(self):
        issues = {"6": _issue("6", "bit", "OPEN")}
        self.assertEqual(sov_next.closed_unsettled(issues), [])


class StaleViews(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "diagrams").mkdir()
        (self.root / "SPEC.md").write_bytes(b"spec bytes\n")
        self.addCleanup(self.tmp.cleanup)

    def _view(self, digest):
        (self.root / "diagrams" / "view.md").write_bytes(
            f"# View\n\n```text\nsource          SPEC.md\n"
            f"source_digest   {digest}\nreader          test · v1\n```\n".encode("utf-8"))

    def test_a_matching_digest_is_not_stale(self):
        from hashlib import sha256
        self._view(sha256((self.root / "SPEC.md").read_bytes()).hexdigest()[:16])
        self.assertEqual(sov_next.stale_views(self.root), [])

    def test_a_drifted_digest_is_reported_stale(self):
        self._view("0000000000000000")
        self.assertEqual(sov_next.stale_views(self.root), [("view.md", ["SPEC.md"])])

    def test_a_source_that_no_longer_exists_is_reported_missing(self):
        self._view("0000000000000000")
        (self.root / "SPEC.md").unlink()
        self.assertEqual(sov_next.stale_views(self.root), [("view.md", ["SPEC.md (missing)"])])


#: A whole small roadmap: a phase table, one phase, and the roadmap's own lanes.
#: It ends its phase on an italic paragraph, because a lane bounded by the next
#: *bold* paragraph swallowed that follower and let an emptied Never read as full.
ADMISSIBLE = """# Product Roadmap

## Now, next, needed, never

- **Now** - prose about the lane, which is a bullet and opens nothing.

## The phases

| Phase | Product result | Estimate |
| --- | --- | ---: |
| `P0` Ground and govern | A product result | 85% |

### `P0` · Ground and govern

**Result.** A product result.

**Now.** The census sweep.

**Next.** The exit custodies.

**Needed.** A fresh-reader test.

**Never.** New product scope.

*Repository reading.* A reading that follows the lanes.

**Exits when** a fresh reader can determine what the product is.

### The roadmap's own lanes

**Now.** `P0`, which gates the rest.

**Next.** `P1`, chosen here.

**Needed.** Everything above `P1`.

**Never.** Distributed consensus, and standing.

## Deferred until earned

Text.
"""


class LaneParsing(unittest.TestCase):
    """What opens a graded subject, and where a lane's prose ends."""

    def _subjects(self):
        return roadmap_lanes.graded_subjects(ADMISSIBLE)

    def test_a_phase_and_the_roadmap_are_both_graded_subjects(self):
        """The rule claims to hold at every level, so the outer level is graded too."""
        self.assertEqual(sorted(self._subjects()), ["P0", "the roadmap itself"])

    def test_prose_about_the_lanes_is_not_a_subject(self):
        self.assertNotIn("Now, next, needed, never", self._subjects())

    def test_a_bullet_does_not_open_a_lane(self):
        """`- **Now** - ...` in the definitions must not read as a lane paragraph."""
        self.assertEqual(roadmap_lanes.lanes_in("- **Now** - a bullet.\n"), {})

    def test_a_subject_stops_at_the_next_heading(self):
        self.assertNotIn("Deferred until earned", self._subjects()["the roadmap itself"])

    def test_a_lane_is_its_own_paragraph(self):
        self.assertEqual(self._subjects_lane("P0", "Never"), "New product scope.")

    def test_a_lane_does_not_swallow_an_italic_follower(self):
        """The defect that defeated the first draft: bounding on the next bold opener."""
        self.assertNotIn("Repository reading", self._subjects_lane("P0", "Never"))

    def test_exits_when_is_not_read_as_a_lane(self):
        """`**Exits when**` carries no full stop before the close, so it opens no lane."""
        self.assertNotIn("Exits", roadmap_lanes.lanes_in(self._subjects()["P0"]))

    def test_a_multi_digit_phase_heading_is_matched(self):
        """`[FP]\\d` made a `P10` section invisible to the grader and to the count."""
        self.assertIn("P10", roadmap_lanes.phase_sections("### `P10` · Later\n\ntext\n"))

    def test_the_archived_f_ladder_is_deliberately_not_graded(self):
        """`ROADMAP-F0-F6.md` is pinned as a closed phase's definition and carries no lanes.

        `sov_next` still resolves its crosswalk rows, so the two readers see
        different populations on purpose; anything else would demand lanes
        inside a document `contracts/phases.json` pins byte for byte.
        """
        both = "## F2 · Old ladder\n\ntext\n\n### `P3` · New ladder\n\ntext\n"
        self.assertEqual(sorted(roadmap_lanes.phase_sections(both)), ["P3"])
        self.assertEqual(sorted(sov_next.roadmap_phases(both)), ["F2", "P3"])
        self.assertEqual([d for d in roadmap_lanes.grade(both) if "F2" in d.detail], [])

    def _subjects_lane(self, subject, lane):
        return roadmap_lanes.lanes_in(self._subjects()[subject])[lane][0]


class LaneRefusals(unittest.TestCase):
    """Each declared refusal fires against a controlled mutation, and only then."""

    def _codes(self, text):
        return {defect.code for defect in roadmap_lanes.grade(text)}

    def test_the_admissible_control_is_quiet(self):
        self.assertEqual(roadmap_lanes.grade(ADMISSIBLE), [])

    def test_a_dropped_lane_is_refused(self):
        broken = ADMISSIBLE.replace("**Never.** New product scope.\n", "")
        self.assertIn("ROADMAP_SUBJECT_MISSING_LANE", self._codes(broken))

    def test_the_defect_names_the_subject_that_dropped_it(self):
        broken = ADMISSIBLE.replace("**Never.** New product scope.\n", "")
        self.assertEqual([d.detail for d in roadmap_lanes.grade(broken)
                          if d.code == "ROADMAP_SUBJECT_MISSING_LANE"],
                         ["P0 carries no Never lane"])

    def test_an_empty_never_is_refused_above_an_italic_paragraph(self):
        broken = ADMISSIBLE.replace("**Never.** New product scope.", "**Never.**")
        self.assertIn("ROADMAP_EMPTY_NEVER", self._codes(broken))

    def test_a_lone_full_stop_is_not_a_stated_edge(self):
        for filler in (".", " ", "- -"):
            with self.subTest(filler=filler):
                broken = ADMISSIBLE.replace("**Never.** New product scope.",
                                            f"**Never.** {filler}")
                self.assertIn("ROADMAP_EMPTY_NEVER", self._codes(broken))

    def test_an_empty_now_is_not_refused(self):
        """A subject whose Now is empty is making a reading, so only Never is required."""
        thin = ADMISSIBLE.replace("**Now.** The census sweep.", "**Now.**")
        self.assertNotIn("ROADMAP_EMPTY_NEVER", self._codes(thin))

    def test_a_duplicate_lane_is_refused_rather_than_resolved_last_wins(self):
        """A second Never had masked an emptied first one."""
        broken = ADMISSIBLE.replace(
            "**Never.** New product scope.",
            "**Never.**\n\n**Never.** A second edge entirely.")
        codes = self._codes(broken)
        self.assertIn("ROADMAP_LANE_DECLARED_TWICE", codes)
        self.assertIn("ROADMAP_EMPTY_NEVER", codes)

    def test_an_undeclared_lane_is_refused_and_fires_alone(self):
        broken = ADMISSIBLE.replace("**Now.** The census sweep.",
                                    "**Now.** The census sweep.\n\n**Soon.** Something else.")
        self.assertEqual(self._codes(broken), {"ROADMAP_UNDECLARED_LANE"})

    def test_an_admitted_non_lane_opener_is_not_refused(self):
        """`**Result.**` opens every phase and is declared, so it must stay quiet."""
        self.assertNotIn("ROADMAP_UNDECLARED_LANE", self._codes(ADMISSIBLE))

    def test_a_mistyped_heading_is_named_rather_than_dropping_the_phase(self):
        """Before the table cross-check this was caught only by a magic phase count."""
        broken = ADMISSIBLE.replace("### `P0` · Ground and govern", "### P0 - Ground and govern")
        self.assertEqual(self._codes(broken), {"ROADMAP_PHASE_NOT_GRADED"})

    def test_a_roadmap_with_no_phases_and_no_table_is_quiet(self):
        self.assertEqual(roadmap_lanes.grade("# Product Roadmap\n"), [])

    def test_selfcheck_proves_every_refusal_fires_alone(self):
        self.assertEqual(roadmap_lanes.selfcheck(), [])

    def test_every_declared_refusal_has_a_case_here(self):
        source = Path(__file__).read_bytes().decode("utf-8")
        for code in roadmap_lanes.REFUSALS:
            self.assertIn(code, source, f"{code} is declared and never exercised")


class LaneContract(unittest.TestCase):
    """The contract, the document it governs, and the vocabulary it borrows."""

    def test_the_contract_declares_the_four_lanes(self):
        self.assertEqual(roadmap_lanes.contract_lanes(), ["Now", "Next", "Needed", "Never"])

    def test_never_is_the_only_lane_that_may_not_be_empty(self):
        optional = roadmap_lanes.lanes_that_may_be_empty()
        self.assertEqual(set(roadmap_lanes.contract_lanes()) - optional, {"Never"})

    def test_needed_is_the_only_way_out_of_never(self):
        """Bdo's correction: discovery under Now moves it, and only into Needed."""
        transitions = roadmap_lanes.load_contract()["lane_transitions"]
        self.assertIn("NEEDED", transitions["never_to_needed"])
        self.assertIn("only way out of NEVER", transitions["never_to_needed"])

    def test_never_is_not_declared_permanent(self):
        """It holds by default; it is not a claim to be permanent."""
        never = [lane for lane in roadmap_lanes.load_contract()["lanes"]
                 if lane["lane"] == "NEVER"][0]
        self.assertIn("how_it_leaves", never)

    def test_the_horizon_crosswalk_covers_every_ticket_horizon(self):
        """NOW and NEXT already name ticket horizons; the two vocabularies must not fork."""
        schema = json.loads(
            (ROOT / "contracts" / "issue-metadata.schema.json").read_bytes().decode("utf-8"))
        declared = set(schema["properties"]["horizon"]["enum"])
        crosswalk = roadmap_lanes.load_contract()["ticket_horizon_crosswalk"]
        self.assertEqual(declared - set(crosswalk), set())

    def test_the_committed_roadmap_carries_every_lane(self):
        self.assertEqual(roadmap_lanes.grade(self._roadmap()), [])

    def test_every_phase_the_table_names_is_graded(self):
        """Measured against the document's own table, not against a literal count."""
        text = self._roadmap()
        subjects = roadmap_lanes.graded_subjects(text)
        for phase in roadmap_lanes.table_phases(text):
            self.assertIn(phase, subjects)

    def test_every_extra_subject_the_contract_names_resolves(self):
        """A renamed heading would silently stop grading the recursion."""
        subjects = roadmap_lanes.graded_subjects(self._roadmap())
        for extra in roadmap_lanes.load_contract()["graded_subjects"]["extra"]:
            self.assertIn(extra["subject"], subjects)

    def _roadmap(self):
        return (ROOT / "ROADMAP.md").read_bytes().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
