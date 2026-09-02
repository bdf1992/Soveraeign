"""Regression test for the phase-state-has-one-producer fix.

Two halves of one problem: a clarity review pinned to `STATUS.yaml` by digest
staled every time the phase changed, even for prose that has nothing to do
with the phase; and nothing stopped a governing document from restating the
phase state itself, which is exactly what let the staleness recur. This module
proves both halves stay fixed - the volatile-basis exclusion in
`scripts/sov_clarity.py`/`scripts/sovclarity`, and the new lint check in
`scripts/lint.py`/`scripts/sovlint` - independently of the shape the rest of
`scripts/tests/test_sov_clarity.py` and `scripts/tests/test_lint.py` already
cover.

Run directly (`python scripts/tests/test_clarity_basis.py`), not only via
`-m unittest`, so it stands as its own acceptance check.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_clarity as sc  # noqa: E402
from sovclarity.scope import volatile_basis  # noqa: E402
from sovlint.phase_producer import defects as phase_defects  # noqa: E402
from sovlint.phase_producer import producer_tokens  # noqa: E402

ROOT = sc.ROOT


class StatusYamlIsNotAClarityBasis(unittest.TestCase):
    def test_status_yaml_is_volatile(self) -> None:
        contract = sc.load(sc.CONTRACT_PATH)
        self.assertEqual({"STATUS.yaml"}, volatile_basis(contract))

    def test_status_yaml_is_no_longer_a_reviewable_candidate(self) -> None:
        contract = sc.load(sc.CONTRACT_PATH)
        self.assertNotIn("STATUS.yaml", sc.eligible(contract))
        self.assertNotIn("STATUS.yaml", sc.clarity_candidates(contract))

    def test_default_basis_never_names_status_yaml(self) -> None:
        contract = sc.load(sc.CONTRACT_PATH)
        for path in sc.eligible(contract):
            self.assertNotIn("STATUS.yaml", sc.default_basis(contract, path), path)

    def test_a_review_not_about_the_phase_survives_a_status_yaml_edit(self) -> None:
        """The actual bug: changing the phase must not stale unrelated reviews.

        Reads the real coverage record rather than a synthetic one, because the
        regression this guards against is specifically "the repository's own
        recorded reviews go stale when STATUS.yaml's `phase` moves" - the branch
        this runs on already carries that exact move (Phase 1.5 opened).
        """
        contract = sc.load(sc.CONTRACT_PATH)
        record = sc.coverage(contract)
        reviews = record.get("reviews", {})
        # AGENTS.md's review predates this fix and previously pinned STATUS.yaml.
        self.assertIn("AGENTS.md", reviews)
        review = reviews["AGENTS.md"]
        self.assertNotIn(
            "STATUS.yaml", [entry["path"] for entry in review.get("basis", [])]
        )
        self.assertEqual("CURRENT", sc.review_state(contract, "AGENTS.md", review))

    def test_the_full_registry_is_well_formed_and_current(self) -> None:
        contract = sc.load(sc.CONTRACT_PATH)
        record = sc.coverage(contract)
        self.assertEqual([], sc.registry_errors(contract, record))
        stale = {
            path: state
            for path, state in sc.state_map(contract, record).items()
            if state in {"TEXT_STALE", "BASIS_STALE"}
        }
        self.assertEqual({}, stale)


class PhaseStateHasOneProducer(unittest.TestCase):
    def test_the_repository_declares_current_phase_tokens(self) -> None:
        tokens = producer_tokens(ROOT)
        self.assertIn("phase_id", tokens)
        self.assertIn("next_gate", tokens)

    def test_a_document_restating_the_current_phase_id_is_refused(self) -> None:
        tokens = producer_tokens(ROOT)
        text = f"seat:root opened `{tokens['phase_id']}` as its successor.\n"
        found = phase_defects("CANON.md", text, tokens)
        self.assertTrue(found, "a literal phase id in a governing document went uncaught")

    def test_a_document_restating_the_current_next_gate_is_refused(self) -> None:
        tokens = producer_tokens(ROOT)
        text = f"The next gate is `{tokens['next_gate']}`.\n"
        found = phase_defects("CANON.md", text, tokens)
        self.assertTrue(found, "a literal next_gate value went uncaught")

    def test_a_conditional_mention_of_a_sentinel_state_is_not_flagged(self) -> None:
        """Evergreen conditionals ('if the state is NONE_ACTIVE, ...') are not a
        claim about today's value and must stay legal - this is what AGENTS.md
        and SOV.md rely on to describe the no-phase-open case without going
        stale the next time a phase opens or closes."""
        tokens = producer_tokens(ROOT)
        text = "If the reconciled state is NONE_ACTIVE, prepared material is context only.\n"
        self.assertEqual([], phase_defects("AGENTS.md", text, tokens))

    def test_archives_and_decisions_are_exempt(self) -> None:
        tokens = producer_tokens(ROOT)
        text = f"seat:root opened `{tokens['phase_id']}` as its successor.\n"
        self.assertEqual([], phase_defects("archives/OLD.md", text, tokens))
        self.assertEqual([], phase_defects("decisions/0100-example.md", text, tokens))

    def test_a_nested_document_is_outside_the_checked_population(self) -> None:
        """Only root-level governing prose is in scope; a service's own scoped
        notes staying silent on phase state is not this check's concern."""
        tokens = producer_tokens(ROOT)
        text = f"seat:root opened `{tokens['phase_id']}` as its successor.\n"
        self.assertEqual([], phase_defects("services/asset/CHARTER.md", text, tokens))

    def test_the_repaired_governing_documents_now_pass(self) -> None:
        tokens = producer_tokens(ROOT)
        for relative in ("CLAUDE.md", "AGENTS.md", "SOV.md", "PRD.md", "SPEC.md",
                          "ROADMAP.md", "CANON.md", "README.md"):
            path = ROOT / relative
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                [], phase_defects(relative, text, tokens),
                f"{relative} still restates phase state as fact"
            )

    def test_lint_passes_over_the_real_tree(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import lint  # noqa: E402 (repository root, not this test's own directory)

        self.assertEqual(0, lint.main())


if __name__ == "__main__":
    unittest.main()
