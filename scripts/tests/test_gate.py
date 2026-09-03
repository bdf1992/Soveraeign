"""One positive and one defeating case per `sovkernel.gate` clause.

Every case reuses `base_grant`/`base_request` and the exact patches from
`conformance/fixtures/authority/grant-cases.json` (`soveraeign-authority-grant-cases/v1`).
Corpus case ids D-014 through D-018 are the gate-tier cases: the observation
verdict (`_observation_verdict`) and the required-check precondition
(`_precondition_unmet`) are not an authority decision over the grant's own
attributes - they ask whether the evidence attached to this request satisfies
what a covering grant already requires.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import gate  # noqa: E402

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


class ObservationVerdict(unittest.TestCase):
    def test_positive_confirmed_independent_observation(self):
        materialised = _base()
        self.assertIsNone(gate._observation_verdict(materialised["grant"], materialised["request"]))

    def test_defeating_no_observation_offered(self):
        materialised = _case("D-014-no-independent-observation-offered")
        result = gate._observation_verdict(materialised["grant"], materialised["request"])
        self.assertEqual(result[0], "OBSERVATION_MISSING")

    def test_defeating_observation_did_not_confirm(self):
        materialised = _case("D-015-observation-did-not-confirm")
        result = gate._observation_verdict(materialised["grant"], materialised["request"])
        self.assertEqual(result[0], "OBSERVATION_MISSING")

    def test_defeating_observer_was_inside_the_build(self):
        materialised = _case("D-016-observer-was-inside-the-build")
        result = gate._observation_verdict(materialised["grant"], materialised["request"])
        self.assertEqual(result[0], "OBSERVER_NOT_INDEPENDENT")


class PreconditionUnmet(unittest.TestCase):
    def test_positive_all_required_checks_pass(self):
        materialised = _base()
        self.assertIsNone(gate._precondition_unmet(materialised["grant"], materialised["request"]))

    def test_defeating_required_check_absent(self):
        materialised = _case("D-017-required-check-absent-from-the-evidence")
        self.assertIsNotNone(gate._precondition_unmet(materialised["grant"], materialised["request"]))

    def test_defeating_required_check_failed(self):
        materialised = _case("D-018-required-check-failed")
        self.assertIsNotNone(gate._precondition_unmet(materialised["grant"], materialised["request"]))


if __name__ == "__main__":
    unittest.main()
