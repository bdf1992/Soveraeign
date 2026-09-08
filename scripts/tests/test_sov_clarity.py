"""Clarity coverage is a live repository claim, not a decorative percentage."""

from __future__ import annotations

import unittest

from scripts import sov_clarity


class ClarityCoverageTests(unittest.TestCase):
    def test_scope_is_fully_classified(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)

        self.assertEqual([], sov_clarity.scope_errors(contract))
        self.assertEqual([], sov_clarity.campaigns(contract)["_unassigned"])

    def test_current_prose_is_reviewable_or_explicitly_exempt(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)

        candidates = sov_clarity.clarity_candidates(contract)
        eligible = sov_clarity.eligible(contract)
        exemptions = set(sov_clarity.exemption_map(contract))

        self.assertFalse(eligible & exemptions)
        self.assertEqual(candidates, eligible | exemptions)

    def test_recorded_reviews_are_well_formed_and_current(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = sov_clarity.coverage(contract)

        self.assertEqual([], sov_clarity.registry_errors(contract, record))
        stale = {
            path: state
            for path, state in sov_clarity.state_map(contract, record).items()
            if state in {"TEXT_STALE", "BASIS_STALE"}
        }
        self.assertEqual({}, stale)

    def test_reviewed_files_carry_their_declared_basis(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = sov_clarity.coverage(contract)
        reviews = record["reviews"]

        for path, review in reviews.items():
            expected = sov_clarity.default_basis(contract, path)
            if not expected:
                continue
            actual = [item["path"] for item in review.get("basis", [])]
            self.assertEqual(expected, actual, path)


    def test_zero_state_requires_only_the_declared_reader_set(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = sov_clarity.coverage(contract)

        required = sov_clarity.zero_required(contract)
        self.assertTrue(required)
        self.assertEqual(len(required), len(set(required)))
        self.assertTrue(set(required) <= sov_clarity.eligible(contract))
        self.assertEqual(
            [],
            sov_clarity.zero_errors(
                contract,
                sov_clarity.state_map(contract, record),
                sov_clarity.eligible(contract),
                sov_clarity.registry_errors(contract, record),
            ),
        )

        required_only = {
            "schema": "soveraeign-clarity-coverage/v1",
            "skill": contract["skill"],
            "reviews": {path: record["reviews"][path] for path in required},
        }
        states = sov_clarity.state_map(contract, required_only)
        self.assertEqual(
            [],
            sov_clarity.zero_errors(
                contract, states, sov_clarity.eligible(contract),
                sov_clarity.registry_errors(contract, required_only),
            ),
        )
        self.assertTrue(any(
            state == "UNCHECKED" and path not in required
            for path, state in states.items()
        ))

    def test_unchecked_files_do_not_fake_failure_or_coverage(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = {
            "schema": "soveraeign-clarity-coverage/v1",
            "skill": contract["skill"],
            "reviews": {},
        }

        self.assertEqual([], sov_clarity.registry_errors(contract, record))
        states = sov_clarity.state_map(contract, record)
        non_exempt = {state for state in states.values() if state != "EXEMPT"}
        self.assertTrue(non_exempt)
        self.assertEqual({"UNCHECKED"}, non_exempt)



class BasisAddresses(unittest.TestCase):
    def test_a_basis_may_address_a_part_of_a_file(self) -> None:
        whole = sov_clarity.basis_digest(sov_clarity.ROOT, "STATUS.yaml")
        part = sov_clarity.basis_digest(sov_clarity.ROOT, "STATUS.yaml#owner_holds")
        self.assertTrue(whole and part and whole != part)
        self.assertIsNone(sov_clarity.basis_digest(sov_clarity.ROOT, "STATUS.yaml#no_such_key"))
        self.assertIsNone(sov_clarity.basis_digest(sov_clarity.ROOT, "NO-SUCH-FILE.md"))


class AnUnreadableBasisIsStale(unittest.TestCase):
    """The refusal a refactor lost, measured by a witness on identical input.

    `basis_digest` returns None when a basis is gone or its fragment stops
    resolving. `review_state` compared that against `basis.get("digest")`, which
    is also None when a receipt entry records no digest, so None != None was False
    and a basis the grader could not read reported CURRENT. The expression it
    replaced could not collapse, because `not source.is_file()` short-circuited
    first. Base read BASIS_STALE here; the refactor read CURRENT.
    """

    def review(self, basis: list[dict]) -> dict:
        artifact = sov_clarity.ROOT / "AGENTS.md"
        return {"artifact_digest": sov_clarity.digest(artifact), "basis": basis}

    def test_a_basis_that_cannot_be_read_and_records_no_digest_is_stale(self) -> None:
        state = sov_clarity.review_state(
            "AGENTS.md", self.review([{"path": "contracts/does-not-exist.json"}]))
        self.assertEqual("BASIS_STALE", state)

    def test_a_basis_that_cannot_be_read_but_records_a_digest_is_stale(self) -> None:
        state = sov_clarity.review_state(
            "AGENTS.md",
            self.review([{"path": "contracts/does-not-exist.json", "digest": "sha256:x"}]))
        self.assertEqual("BASIS_STALE", state)

    def test_a_readable_basis_whose_digest_matches_is_current(self) -> None:
        """The defeat: staleness must not become the answer to everything."""
        found = sov_clarity.basis_digest(sov_clarity.ROOT, "GROUND.md")
        state = sov_clarity.review_state(
            "AGENTS.md", self.review([{"path": "GROUND.md", "digest": found}]))
        self.assertEqual("CURRENT", state)

    def test_a_readable_basis_whose_digest_moved_is_stale(self) -> None:
        state = sov_clarity.review_state(
            "AGENTS.md", self.review([{"path": "GROUND.md", "digest": "sha256:moved"}]))
        self.assertEqual("BASIS_STALE", state)


if __name__ == "__main__":
    unittest.main()
