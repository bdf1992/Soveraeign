"""One positive and one defeating case per `sovkernel.admission.unavailable` clause.

Every case reuses `base_grant`/`base_request` and the exact patches from
`conformance/fixtures/authority/grant-cases.json` (`soveraeign-authority-grant-cases/v1`),
so a clause here is proved by the same fixture that proves it for the combined
evaluator. Corpus case ids D-001 through D-013b are the admission-tier cases; a
clause with no corpus positive (JUDGEMENT issuer) is proved positive by the
unmodified base grant, whose `authority_type` is `VERIFICATION` and so never
enters that branch at all.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import admission, authority  # noqa: E402

CORPUS = ROOT / "conformance" / "fixtures" / "authority" / "grant-cases.json"


def _merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _case(case_id: str) -> dict:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in corpus["cases"]}
    case = cases[case_id]
    return {
        "grant": _merge(corpus["base_grant"], case.get("grant_patch") or {}),
        "request": _merge(corpus["base_request"], case.get("request_patch") or {}),
    }


def _base() -> dict:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    return {"grant": dict(corpus["base_grant"]), "request": dict(corpus["base_request"])}


def _unavailable(materialised: dict) -> str | None:
    now = authority._instant(materialised["request"]["at"], "at")
    return admission.unavailable(materialised["grant"], materialised["request"], now)


class AdmissionClauses(unittest.TestCase):
    def test_status_positive_ratified(self):
        self.assertIsNone(_unavailable(_base()))

    def test_status_defeating_not_ratified(self):
        self.assertIsNotNone(_unavailable(_case("D-001-grant-not-yet-ratified")))

    def test_actor_positive_matches(self):
        self.assertIsNone(_unavailable(_base()))

    def test_actor_defeating_names_another_actor(self):
        self.assertIsNotNone(_unavailable(_case("D-002-grant-names-another-actor")))

    def test_capability_positive_carried(self):
        self.assertIsNone(_unavailable(_base()))

    def test_capability_defeating_not_carried(self):
        self.assertIsNotNone(_unavailable(_case("D-003-capability-not-carried")))

    def test_judgement_issuer_positive_non_judgement_grant_unaffected(self):
        self.assertIsNone(_unavailable(_base()))

    def test_judgement_issuer_defeating_non_owner_issuer(self):
        self.assertIsNotNone(
            _unavailable(_case("D-012-judgement-authority-issued-by-a-non-owner"))
        )

    def test_revocation_positive_not_revoked(self):
        self.assertIsNone(_unavailable(_base()))

    def test_revocation_defeating_revoked(self):
        self.assertIsNotNone(_unavailable(_case("D-004-grant-revoked")))

    def test_valid_from_positive_within_window(self):
        self.assertIsNone(_unavailable(_base()))

    def test_valid_from_defeating_before_window(self):
        self.assertIsNotNone(_unavailable(_case("D-005-request-before-valid-from")))

    def test_valid_until_positive_within_window(self):
        self.assertIsNone(_unavailable(_base()))

    def test_valid_until_defeating_after_window(self):
        self.assertIsNotNone(_unavailable(_case("D-006-grant-expired")))

    def test_effect_ceiling_positive_at_or_below(self):
        self.assertIsNone(_unavailable(_base()))

    def test_effect_ceiling_defeating_above(self):
        self.assertIsNotNone(_unavailable(_case("D-011-effect-class-above-the-ceiling")))

    def test_branch_positive_admitted(self):
        self.assertIsNone(_unavailable(_base()))

    def test_branch_defeating_not_admitted(self):
        self.assertIsNotNone(_unavailable(_case("D-009-branch-not-admitted")))

    def test_budget_positive_under_ceiling(self):
        self.assertIsNone(_unavailable(_base()))

    def test_budget_defeating_exceeded(self):
        self.assertIsNotNone(_unavailable(_case("D-010-budget-exceeded")))


if __name__ == "__main__":
    unittest.main()
