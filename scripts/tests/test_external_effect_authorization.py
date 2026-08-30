"""Focused regressions for external-effect authorization at both evaluator boundaries."""

from __future__ import annotations

from pathlib import Path
import unittest

from sovkernel import transitions as kernel
from sovticket import transitions as ticket

ROOT = Path(__file__).resolve().parents[2]


class ExternalEffectAuthorization(unittest.TestCase):
    def setUp(self):
        self.kernel_table = kernel.load_table(ROOT)
        self.ticket_table = ticket.load_table(ROOT)
        self.kernel_request = {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "cross",
            "actor_id": "model/orchestrator",
            "actor_kind": "MODEL",
            "effect_class": "EXTERNAL_WORLD",
            "reason": "focused authorization regression",
            "declared": {
                "source_address": "src-1",
                "reader_declaration": "reader-1",
                "omissions": ["none"],
                "authority_grant_id": "grant-1",
                "destination_address": "dst-1",
            },
        }
        self.ticket_request = {
            "request_schema": "soveraeign-ticket-transition/v1",
            "ticket": "#148",
            "from": "OPEN",
            "to": "PROPOSED",
            "actor_id": "model/orchestrator",
            "actor_kind": "MODEL",
            "effect_class": "EXTERNAL_WORLD",
            "reason": "focused authorization regression",
            "evidence": {
                "obligation": "#148",
                "priors": "contracts/external-effect-authorization.json",
                "closure_contract": "#148#terminal-condition",
            },
        }

    @staticmethod
    def valid_authorization():
        return {
            "scope": "coordination.issue_metadata",
            "verb": "set_body",
            "target": "github.com/bdf1992/Soveraeign/issues/148",
            "receipt": "receipt/coordination/focused-regression",
            "preconditions_discharged": {
                "body_validates": "proof/body-validates",
                "prior_body_recorded": "proof/prior-body",
            },
        }

    def test_contract_preconditions_are_addressable(self):
        scope = self.kernel_table["_authorization"]["scopes"]["coordination.issue_metadata"]
        for precondition in scope["preconditions"]:
            self.assertIsInstance(precondition, dict)
            self.assertTrue(precondition["id"])
            self.assertTrue(precondition["verbs"])
            self.assertTrue(precondition["discharged_by"])

    def test_kernel_malformed_values_refuse_instead_of_raising(self):
        malformed = [
            ["truthy", "non-mapping"],
            {"scope": "coordination.issue_metadata", "verb": ["set_body"],
             "receipt": "receipt/x"},
            {"scope": ["coordination.issue_metadata"], "verb": "set_body",
             "receipt": "receipt/x"},
            {"scope": "coordination.issue_metadata", "verb": "set_body", "receipt": 7},
            {"scope": "coordination.issue_metadata", "verb": "set_body", "receipt": "\u200b"},
            {"scope": "coordination.issue_metadata", "verb": "set_body",
             "receipt": "receipt/x", "preconditions_discharged": ["not", "a", "mapping"]},
            {"scope": "coordination.issue_metadata", "verb": "set_body",
             "receipt": "receipt/x", "preconditions_discharged": {
                 "body_validates": "\u200b", "prior_body_recorded": "proof/prior"}},
        ]
        for authorization in malformed:
            with self.subTest(authorization=authorization):
                request = {**self.kernel_request, "authorization": authorization}
                decision = kernel.evaluate(request, self.kernel_table)
                self.assertFalse(decision.permitted)
                self.assertEqual(decision.reason_code, "EXTERNAL_EFFECT_UNAUTHORIZED")

    def test_ticket_malformed_values_refuse_instead_of_raising(self):
        cases = [
            (["truthy", "non-mapping"], "EXTERNAL_EFFECT_UNAUTHORIZED"),
            ({"scope": "coordination.issue_metadata", "verb": ["set_body"],
              "receipt": "receipt/x"}, "EXTERNAL_EFFECT_OUT_OF_SCOPE"),
            ({"scope": ["coordination.issue_metadata"], "verb": "set_body",
              "receipt": "receipt/x"}, "EXTERNAL_EFFECT_OUT_OF_SCOPE"),
            ({"scope": "coordination.issue_metadata", "verb": "set_body", "receipt": 7},
             "EXTERNAL_EFFECT_WITHOUT_RECEIPT"),
            ({"scope": "coordination.issue_metadata", "verb": "set_body", "receipt": "\u200b"},
             "EXTERNAL_EFFECT_WITHOUT_RECEIPT"),
            ({"scope": "coordination.issue_metadata", "verb": "set_body",
              "receipt": "receipt/x", "preconditions_discharged": ["not", "a", "mapping"]},
             "EXTERNAL_EFFECT_PRECONDITION_UNMET"),
        ]
        for authorization, reason in cases:
            with self.subTest(authorization=authorization):
                request = {**self.ticket_request, "authorization": authorization}
                decision = ticket.evaluate(request, self.ticket_table)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason_code, reason)

    def test_valid_discharge_passes_both_authorization_boundaries(self):
        authorization = self.valid_authorization()
        self.assertTrue(kernel._authorized(
            self.kernel_table, {**self.kernel_request, "authorization": authorization}))

        decision = ticket.evaluate(
            {**self.ticket_request, "authorization": authorization}, self.ticket_table)
        self.assertTrue(decision.allowed, decision.render())


if __name__ == "__main__":
    unittest.main()
