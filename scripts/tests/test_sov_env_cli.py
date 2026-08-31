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

PATTERN = ROOT / "conformance" / "fixtures" / "environment" / "software-delivery.json"


class CliAuthorityBoundaryTests(unittest.TestCase):
    def test_authority_string_cannot_admit_a_crossing(self) -> None:
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

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            StateStore(path).write(state)
            output = StringIO()
            with redirect_stdout(output):
                code = sov_env.main(
                    [
                        "admit",
                        "--pattern",
                        str(PATTERN),
                        "--state",
                        str(path),
                        "--crossing",
                        proposal["crossing_id"],
                        "--integration-base",
                        "base1",
                        "--witness",
                        "qa",
                        "--authority",
                        "VERIFICATION",
                    ]
                )

            result = json.loads(output.getvalue())
            self.assertEqual(2, code)
            self.assertEqual("REFUSED", result["outcome"])
            self.assertEqual(sov_env.AUTHORITY_APERTURE_REFUSAL, result["reason"])
            stored = StateStore(path).read()
            self.assertEqual("PROPOSED", stored["crossing_records"][0]["status"])


if __name__ == "__main__":
    unittest.main()
