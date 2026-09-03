"""Prove the three-module split changes no observable verdict.

This test's golden dict was recorded from `sovkernel.authority.evaluate()`
before `admission.py` and `gate.py` existed, by materialising every case in
`conformance/fixtures/authority/grant-cases.json` the way `sov_grant.py`'s own
`selfcheck` does. It must pass unchanged before and after that split.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import authority  # noqa: E402

CORPUS = ROOT / "conformance" / "fixtures" / "authority" / "grant-cases.json"

GOLDEN = {
    "P-001-witnessed-green-in-scope-landing": {
        "verdict": "PERMITTED",
        "code": None,
        "detail": "covered by grant:corpus-landing",
        "considered": [],
    },
    "P-002-record-local-commit-under-a-heavier-ceiling": {
        "verdict": "PERMITTED",
        "code": None,
        "detail": "covered by grant:corpus-landing",
        "considered": [],
    },
    "D-001-grant-not-yet-ratified": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant is at PROPOSED standing and has not been ratified",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant is at PROPOSED standing and has not been ratified",
            }
        ],
    },
    "D-002-grant-names-another-actor": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant names actor 'some-other-profile'",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant names actor 'some-other-profile'",
            }
        ],
    },
    "D-003-capability-not-carried": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant does not carry the capability 'standing.ratify'",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant does not carry the capability 'standing.ratify'",
            }
        ],
    },
    "D-004-grant-revoked": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant was revoked at 2026-08-30T00:00:00Z",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant was revoked at 2026-08-30T00:00:00Z",
            }
        ],
    },
    "D-005-request-before-valid-from": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant is not valid until 2026-08-25T00:00:00Z",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant is not valid until 2026-08-25T00:00:00Z",
            }
        ],
    },
    "D-006-grant-expired": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: grant expired at 2026-11-23T00:00:00Z",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "grant expired at 2026-11-23T00:00:00Z",
            }
        ],
    },
    "D-007-path-inside-an-excluded-prefix": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: decisions/0061-x.md is inside the excluded prefix decisions/",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "decisions/0061-x.md is inside the excluded prefix decisions/",
            }
        ],
    },
    "D-008a-grant-cannot-widen-itself": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts/standing-grants.json is inside the "
            "excluded prefix contracts/standing-grants.json"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts/standing-grants.json is inside the excluded prefix "
                    "contracts/standing-grants.json"
                ),
            }
        ],
    },
    "D-008b-dot-dot-walks-out-of-an-admitted-prefix": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts/../STATUS.yaml carries `..` segment, so the "
            "string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts/../STATUS.yaml carries `..` segment, so the string it is "
                    "compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008c-dot-dot-reaches-the-grant-registry-itself": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts/../contracts/standing-grants.json carries "
            "`..` segment, so the string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts/../contracts/standing-grants.json carries `..` segment, so "
                    "the string it is compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008d-dot-dot-leaves-the-repository-altogether": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts/../../etc/passwd carries `..` segment, so the "
            "string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts/../../etc/passwd carries `..` segment, so the string it is "
                    "compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008f-a-dot-segment-reaches-the-grant-registry": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts/./standing-grants.json carries `.` segment, "
            "so the string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts/./standing-grants.json carries `.` segment, so the string "
                    "it is compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008g-a-doubled-separator-reaches-the-grant-registry": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts//standing-grants.json carries an empty "
            "segment, so the string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts//standing-grants.json carries an empty segment, so the "
                    "string it is compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008h-a-trailing-separator-does-not-name-a-file": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts/sov_land.py/ carries an empty segment, so the "
            "string it is compared as is not the path it names"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts/sov_land.py/ carries an empty segment, so the string it is "
                    "compared as is not the path it names"
                ),
            }
        ],
    },
    "D-008i-a-wildcard-selects-the-grant-registry-after-the-check": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts/* carries the pattern character `*`, so it "
            "names a set that is chosen after this check has compared it"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts/* carries the pattern character `*`, so it names a set "
                    "that is chosen after this check has compared it"
                ),
            }
        ],
    },
    "D-008j-a-single-character-wildcard-is-the-same-escape": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts/standing-grants.jso? carries the pattern "
            "character `?`, so it names a set that is chosen after this check has "
            "compared it"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts/standing-grants.jso? carries the pattern character `?`, "
                    "so it names a set that is chosen after this check has compared it"
                ),
            }
        ],
    },
    "D-008k-a-character-class-is-the-same-escape-again": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts/[s]tanding-grants.json carries the pattern "
            "character `[`, so it names a set that is chosen after this check has "
            "compared it"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts/[s]tanding-grants.json carries the pattern character `[`, "
                    "so it names a set that is chosen after this check has compared it"
                ),
            }
        ],
    },
    "D-008l-pathspec-magic-rewrites-what-a-string-selects": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: :!contracts/standing-grants.json opens git's "
            "pathspec magic, which changes what the string selects after this check "
            "has read it"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    ":!contracts/standing-grants.json opens git's pathspec magic, which "
                    "changes what the string selects after this check has read it"
                ),
            }
        ],
    },
    "D-008m-a-bare-directory-selects-what-it-contains": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: contracts is a directory containing the excluded "
            "contracts/standing-grants.json"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "contracts is a directory containing the excluded "
                    "contracts/standing-grants.json"
                ),
            }
        ],
    },
    "P-003-a-directory-containing-nothing-excluded-still-lands": {
        "verdict": "PERMITTED",
        "code": None,
        "detail": "covered by grant:corpus-landing",
        "considered": [],
    },
    "D-008e-an-absolute-path-cannot-be-graded-here": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: C:/checkouts/Soveraeign/scripts/sov_land.py is not "
            "repository-relative; a grant's scope is declared in repository-relative "
            "prefixes"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "C:/checkouts/Soveraeign/scripts/sov_land.py is not "
                    "repository-relative; a grant's scope is declared in "
                    "repository-relative prefixes"
                ),
            }
        ],
    },
    "D-008-path-outside-every-included-prefix": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: README.md is outside every path prefix the grant admits",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "README.md is outside every path prefix the grant admits",
            }
        ],
    },
    "D-009-branch-not-admitted": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: branch release/1.0 is not among the branches the "
            "grant admits"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "branch release/1.0 is not among the branches the grant admits",
            }
        ],
    },
    "D-010-budget-exceeded": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: 61 agent_invocations against a ceiling of 60",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "61 agent_invocations against a ceiling of 60",
            }
        ],
    },
    "D-011-effect-class-above-the-ceiling": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: request declares RESOURCE_CONSUMPTION against an "
            "effect ceiling of RECORD_LOCAL"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "request declares RESOURCE_CONSUMPTION against an effect ceiling of "
                    "RECORD_LOCAL"
                ),
            }
        ],
    },
    "D-012-judgement-authority-issued-by-a-non-owner": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": "grant:corpus-landing: JUDGEMENT authority issued by 'sov'; only bdo may issue it",
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": "JUDGEMENT authority issued by 'sov'; only bdo may issue it",
            }
        ],
    },
    "P-004-scoped-external-world-effect-covered": {
        "verdict": "PERMITTED",
        "code": None,
        "detail": "covered by grant:corpus-landing",
        "considered": [],
    },
    "D-013b-external-world-effect-above-grant-ceiling": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: request declares EXTERNAL_WORLD against an effect "
            "ceiling of RESOURCE_CONSUMPTION"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "request declares EXTERNAL_WORLD against an effect ceiling of "
                    "RESOURCE_CONSUMPTION"
                ),
            }
        ],
    },
    "D-014-no-independent-observation-offered": {
        "verdict": "REFUSED",
        "code": "OBSERVATION_MISSING",
        "detail": "the grant requires an independent observation and the request carries none",
        "considered": [],
    },
    "D-015-observation-did-not-confirm": {
        "verdict": "REFUSED",
        "code": "OBSERVATION_MISSING",
        "detail": "the observation reads 'DISSENTED', not CONFIRMED",
        "considered": [],
    },
    "D-016-observer-was-inside-the-build": {
        "verdict": "REFUSED",
        "code": "OBSERVER_NOT_INDEPENDENT",
        "detail": "observer 'sov-worker-03' contributed to the build it is offered as the observation of",
        "considered": [],
    },
    "D-017-required-check-absent-from-the-evidence": {
        "verdict": "REFUSED",
        "code": "MISSING_PRECONDITION",
        "detail": "required check 'verify' is not present in the request's evidence",
        "considered": [],
    },
    "D-018-required-check-failed": {
        "verdict": "REFUSED",
        "code": "MISSING_PRECONDITION",
        "detail": "required check 'lint' reads 'FAIL'",
        "considered": [],
    },
    "D-008c-a-backslash-names-two-different-files": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts\\tests\\x.py carries a backslash, which is a "
            "separator on one host and a filename character on another, so what it "
            "names depends on where this check runs"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts\\tests\\x.py carries a backslash, which is a separator on "
                    "one host and a filename character on another, so what it names "
                    "depends on where this check runs"
                ),
            }
        ],
    },
    "D-008d-a-backslash-inside-an-admitted-prefix-is-still-refused": {
        "verdict": "REFUSED",
        "code": "AUTHORITY_REFUSED",
        "detail": (
            "grant:corpus-landing: scripts/tests\\x.py carries a backslash, which is a "
            "separator on one host and a filename character on another, so what it "
            "names depends on where this check runs"
        ),
        "considered": [
            {
                "grant_id": "grant:corpus-landing",
                "reason": (
                    "scripts/tests\\x.py carries a backslash, which is a separator on "
                    "one host and a filename character on another, so what it names "
                    "depends on where this check runs"
                ),
            }
        ],
    },
}


def _merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


class AuthoritySplitParity(unittest.TestCase):
    def test_every_corpus_case_matches_the_pre_split_golden(self):
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        base_grant = corpus["base_grant"]
        base_request = corpus["base_request"]
        self.assertEqual(set(GOLDEN), {case["case_id"] for case in corpus["cases"]})
        for case in corpus["cases"]:
            grant = _merge(base_grant, case.get("grant_patch") or {})
            request = _merge(base_request, case.get("request_patch") or {})
            result = authority.evaluate([grant], request)
            actual = {
                "verdict": result["verdict"],
                "code": result["code"],
                "detail": result["detail"],
                "considered": result["considered"],
            }
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(actual, GOLDEN[case["case_id"]])


if __name__ == "__main__":
    unittest.main()
