from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import sov_env
from sovenv import (
    StateStore,
    instantiate_environment,
    instantiate_trunk,
    load_json,
    new_state,
    propose_crossing,
)
from sovenv.authority import environment_resource

PATTERN = ROOT / "conformance" / "fixtures" / "environment" / "software-delivery.json"


def prepared() -> tuple[dict, dict, dict]:
    pattern = load_json(PATTERN)
    state = new_state(pattern)
    instantiate_environment(state, pattern, "FEAT", "feat:a")
    instantiate_environment(state, pattern, "DEV", "dev")
    instantiate_trunk(state, pattern, "release", "release:main")
    proposal = propose_crossing(
        state,
        pattern,
        trunk_instance="release:main",
        source_instance="feat:a",
        target_instance="dev",
        revision="abc123",
        artifact_digest="sha256:candidate",
        config_digest="sha256:dev-config",
        actor="builder",
        integration_base="base1",
        evidence=["tests"],
    )
    return pattern, state, proposal


def grant(state: dict, proposal: dict) -> dict:
    return {
        "grant_schema": "soveraeign-authority-grant/v1",
        "status": "RATIFIED",
        "grant_id": "grant:environment-dev",
        "issuer_id": "bdo",
        "actor_id": "qa",
        "authority_type": "VERIFICATION",
        "capabilities": ["environment.promote"],
        "scope": {
            "paths": [],
            "excluded_paths": [],
            "environment": environment_resource(state, proposal),
        },
        "budget": {"unit": "none", "ceiling": None},
        "effect_ceiling": "RECORD_LOCAL",
        "preconditions": {},
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2099-01-01T00:00:00Z",
        "revoked_at": None,
    }


def run_admit(state: dict, args: list[str], offered: dict | None = None) -> tuple[int, dict, dict]:
    with tempfile.TemporaryDirectory() as directory:
        state_path = Path(directory) / "state.json"
        grant_path = Path(directory) / "grant.json"
        StateStore(state_path).write(state)
        command = [
            "admit",
            "--pattern",
            str(PATTERN),
            "--state",
            str(state_path),
            "--crossing",
            state["crossing_records"][0]["crossing_id"],
            "--integration-base",
            "base1",
            "--witness",
            "qa",
            *args,
        ]
        if offered is not None:
            grant_path.write_text(json.dumps(offered), encoding="utf-8")
            command.extend(["--grant", str(grant_path)])
        output = StringIO()
        with redirect_stdout(output):
            code = sov_env.main(command)
        return code, json.loads(output.getvalue()), StateStore(state_path).read()


class CliAuthorityBoundaryTests(unittest.TestCase):
    def test_authority_string_cannot_admit_a_crossing(self) -> None:
        _pattern, state, _proposal = prepared()
        code, result, stored = run_admit(state, ["--authority", "VERIFICATION"])
        self.assertEqual(2, code)
        self.assertEqual("REFUSED", result["outcome"])
        self.assertEqual(
            "AUTHORITY_REFUSED:CALLER_AUTHORITY_LABEL_FORBIDDEN", result["reason"]
        )
        self.assertEqual("PROPOSED", stored["crossing_records"][0]["status"])

    def test_exact_environment_grant_admits_and_is_retained(self) -> None:
        _pattern, state, proposal = prepared()
        offered = grant(state, proposal)
        code, result, stored = run_admit(state, [], offered)
        self.assertEqual(0, code)
        self.assertEqual("ADMITTED", result["status"])
        self.assertEqual("VERIFICATION", result["authority"])
        self.assertEqual("grant:environment-dev", result["authority_grant_id"])
        self.assertEqual("ADMITTED", stored["crossing_records"][0]["status"])

    def test_grant_for_another_target_cannot_slide_to_this_crossing(self) -> None:
        _pattern, state, proposal = prepared()
        offered = grant(state, proposal)
        offered["scope"]["environment"]["target_instance"] = "some-other-dev"
        code, result, stored = run_admit(state, [], offered)
        self.assertEqual(2, code)
        self.assertIn("AUTHORITY_REFUSED", result["reason"])
        self.assertIn("target_instance", result["reason"])
        self.assertEqual("PROPOSED", stored["crossing_records"][0]["status"])

    def test_malformed_environment_grant_never_reaches_evaluator(self) -> None:
        _pattern, state, proposal = prepared()
        offered = grant(state, proposal)
        del offered["scope"]["environment"]["artifact_digest"]
        code, result, stored = run_admit(state, [], offered)
        self.assertEqual(2, code)
        self.assertIn("AUTHORITY_GRANT_INVALID", result["reason"])
        self.assertEqual("PROPOSED", stored["crossing_records"][0]["status"])


if __name__ == "__main__":
    unittest.main()
