"""P15-Q1.3 grading: identity separation and the cross-principal/session refusal."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sov_p15_q13  # noqa: E402

VALID_IDENTITIES = {
    "principal_id": "principal:interface-human",
    "session_id": "session_aaaaaaaaaaaaaaaa",
    "grant_id": "grant_bbbbbbbbbbbbbbbb",
    "interface_binding_id": "urn:soveraeign:binding:node-interface:human-cli-v1",
}


def _document(*, identities: dict | None = VALID_IDENTITIES,
              mismatch: str | None = "REFUSED") -> dict:
    return {
        "identities": identities,
        "cross_principal_session_mismatch": mismatch,
    }


class EvaluateFromConstructedDocuments(unittest.TestCase):
    def test_passes_when_identities_separate_and_mismatch_refuses(self) -> None:
        with mock.patch.object(sov_p15_q13, "run_proof", return_value=_document()):
            self.assertEqual(sov_p15_q13.evaluate(), [])
        with mock.patch.object(sov_p15_q13, "run_proof", return_value=_document()):
            self.assertEqual(sov_p15_q13.main(), 0)

    def test_fails_when_mismatch_committed_instead_of_refused(self) -> None:
        with mock.patch.object(
                sov_p15_q13, "run_proof",
                return_value=_document(mismatch="COMMITTED")):
            defects = sov_p15_q13.evaluate()
        self.assertTrue(defects)
        self.assertIn("cross-principal/session mismatch did not refuse", defects)
        with mock.patch.object(
                sov_p15_q13, "run_proof",
                return_value=_document(mismatch="COMMITTED")):
            self.assertEqual(sov_p15_q13.main(), 1)

    def test_fails_when_identities_collapse_to_the_same_value(self) -> None:
        collapsed = dict(VALID_IDENTITIES)
        collapsed["grant_id"] = collapsed["session_id"]
        with mock.patch.object(
                sov_p15_q13, "run_proof", return_value=_document(identities=collapsed)):
            defects = sov_p15_q13.evaluate()
        self.assertIn(
            "principal, session, grant, and interface binding collapsed", defects)

    def test_fails_when_an_identity_is_missing(self) -> None:
        incomplete = dict(VALID_IDENTITIES)
        del incomplete["grant_id"]
        with mock.patch.object(
                sov_p15_q13, "run_proof", return_value=_document(identities=incomplete)):
            defects = sov_p15_q13.evaluate()
        self.assertIn("identity separation missing grant_id", defects)


if __name__ == "__main__":
    unittest.main()
