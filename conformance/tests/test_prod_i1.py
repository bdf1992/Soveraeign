"""Each PROD-I-1 delivery and authority refusal, reached on its own.

The two oracle controls `CONF-I1-SURFACE-DEF` and `CONF-I1-CLAIM-DEF` each trip several
refusals at once, so removing any one branch still leaves the control failing and the
branch untested. These cases isolate one refusal apiece: every observation below is
otherwise clean, so the asserted defect is the only defect, and deleting the branch that
produces it makes exactly one case here fail.

This grades local mechanics. Whether a named surface exists, and whether a human read it,
are not visible to the oracle and stay unattestable until a participant is bound.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("conformance_requirements", ROOT / "requirements.py")
assert SPEC and SPEC.loader
predicates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(predicates)


def observation(**overrides):
    """A PROD-I-1 observation with no defects, before the case under test spoils one."""
    observed = {
        "proposal": {
            "proposal_id": "p1",
            "actor_id": "model-1",
            "actor_kind": "MODEL",
            "content_address": "sha256:p1",
            "source_addresses": ["sha256:s1"],
            "cost_record": {"unit": "token", "amount": 42},
            "required_authority_type": "JUDGEMENT",
            "scope": "asset:a1",
            "standing": "RECORDED",
        },
        "admitted": True,
        "delivery": {
            "surface_id": "console:thread_02c3d2d8b98140f8",
            "operator_id": "bdo",
            "receipt_id": "rcpt-i1-1",
            "proposal_id": "p1",
            "readable_by_operator": True,
        },
        "authority_claim": {
            "asserted": True,
            "asserted_authority_type": "JUDGEMENT",
            "actor_continuity": "INSTANCE",
            "honored": False,
            "grant_id": None,
        },
    }
    observed.update(overrides)
    return observed


class TheCleanObservation(unittest.TestCase):
    """Everything below is a one-field spoil of this, so it has to be clean first."""

    def test_a_complete_observation_has_no_defects(self):
        self.assertEqual([], predicates.check_i1(observation()))


class Delivery(unittest.TestCase):
    """An admitted proposal has to have reached somewhere a named operator can read."""

    def test_an_admitted_proposal_with_no_delivery_is_refused(self):
        self.assertEqual(["admitted proposal never reached an operator surface"],
                         predicates.i1_delivery(observation(delivery=None)))

    def test_each_delivery_field_is_required_on_its_own(self):
        for field in ("surface_id", "operator_id", "receipt_id", "proposal_id"):
            with self.subTest(field=field):
                observed = observation()
                del observed["delivery"][field]
                self.assertIn(f"delivery missing {field}", predicates.i1_delivery(observed))

    def test_a_receipt_for_another_proposal_does_not_deliver_this_one(self):
        observed = observation()
        observed["delivery"]["proposal_id"] = "p-somebody-else"
        self.assertEqual(["delivery receipt names a different proposal"],
                         predicates.i1_delivery(observed))

    def test_a_surface_the_operator_cannot_read_is_not_delivery(self):
        observed = observation()
        observed["delivery"]["readable_by_operator"] = False
        self.assertEqual(["proposal reached a surface the operator cannot read"],
                         predicates.i1_delivery(observed))

    def test_readability_must_be_stated_not_merely_unstated(self):
        observed = observation()
        del observed["delivery"]["readable_by_operator"]
        self.assertEqual(["proposal reached a surface the operator cannot read"],
                         predicates.i1_delivery(observed))

    def test_delivery_is_not_asked_of_a_proposal_that_was_not_admitted(self):
        self.assertEqual([], predicates.i1_delivery(observation(admitted=False, delivery=None)))


class AuthorityClaim(unittest.TestCase):
    """The session asserts; the record records the assertion and never honors it."""

    def test_an_absent_claim_is_refused_rather_than_read_as_no_claim(self):
        self.assertEqual(["proposal carries no authority claim to grade"],
                         predicates.i1_authority_claim(observation(authority_claim=None)))

    def test_an_object_that_states_nothing_does_not_satisfy_the_claim(self):
        defects = predicates.i1_authority_claim(observation(authority_claim={"x": 1}))
        for field in ("asserted", "asserted_authority_type", "actor_continuity", "honored"):
            self.assertIn(f"authority claim missing {field}", defects)

    def test_each_claim_field_is_required_on_its_own(self):
        for field in ("asserted", "asserted_authority_type", "actor_continuity", "honored"):
            with self.subTest(field=field):
                observed = observation()
                del observed["authority_claim"][field]
                self.assertIn(f"authority claim missing {field}",
                              predicates.i1_authority_claim(observed))

    def test_honoring_the_assertion_is_refused(self):
        observed = observation()
        observed["authority_claim"]["honored"] = True
        self.assertEqual(["an instanced session's asserted authority was honored"],
                         predicates.i1_authority_claim(observed))

    def test_a_session_cannot_escape_by_declaring_itself_continuous(self):
        observed = observation()
        observed["authority_claim"]["actor_continuity"] = "CONTINUOUS"
        self.assertEqual(["a fresh model session declared itself other than an instance"],
                         predicates.i1_authority_claim(observed))

    def test_a_grant_attached_to_an_instance_is_refused(self):
        observed = observation()
        observed["authority_claim"]["grant_id"] = "grant:invented-by-generation"
        self.assertEqual(["a grant was attached to an instanced session"],
                         predicates.i1_authority_claim(observed))

    def test_declaring_continuity_does_not_licence_keeping_the_grant(self):
        """The pair the escape hatch needed: both refusals fire, neither excuses the other."""
        observed = observation()
        observed["authority_claim"]["actor_continuity"] = "CONTINUOUS"
        observed["authority_claim"]["grant_id"] = "grant:invented-by-generation"
        self.assertEqual(["a fresh model session declared itself other than an instance",
                          "a grant was attached to an instanced session"],
                         predicates.i1_authority_claim(observed))


if __name__ == "__main__":
    unittest.main()
