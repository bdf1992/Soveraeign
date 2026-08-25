"""Cases for the signpost reconciler.

Every check has a positive case and a case proving the required refusal, per
`AGENTS.md` Testing and verification. Nothing here reaches the network or the
coordination surface.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_next  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
