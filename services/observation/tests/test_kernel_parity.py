"""The observation this service emits is the one the kernel's `settle_run` will accept.

`scripts/sovkernel/transitions.py` refuses settlement without a satisfactory observation and
refuses an observer who produced the report. This proves the service's output crosses that
boundary as declared, and that a self-observation still cannot. It settles nothing: the kernel
decides legality only, and no run is settled here.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

SERVICE = Path(__file__).resolve().parents[1]
ROOT = SERVICE.parents[1]
sys.path.insert(0, str(SERVICE / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(SERVICE / "tests"))

from sovkernel import transitions as kernel  # noqa: E402

from soveraeign_observation_service import ObservationService, RunRecord  # noqa: E402
from test_thin_slice import PREDICATES, RUN, Clock, journal, reader  # noqa: E402

DIGEST = "1c" * 32


def settle_request(observation: dict, settled_by: str) -> dict:
    return {
        "request_schema": "soveraeign-kernel-transition/v1",
        "transition": "settle_run",
        "actor_id": settled_by,
        "actor_kind": "SYSTEM",
        "effect_class": "RECORD_LOCAL",
        "reason": "observation service parity",
        "requested_outcome": "COMMITTED",
        "pre_state_digest": DIGEST,
        "declared": {"run_id": RUN, "input_state_digest": DIGEST,
                     "observation_id": observation["observation_id"]},
        "observation": {
            "observation_id": observation["observation_id"],
            "observer_id": observation["observer_id"],
            "observer_relation": observation["observer_relation"],
            "satisfactory": all(observation["predicate_results"].values()),
        },
    }


class SettleRunAcceptsTheServiceObservation(unittest.TestCase):
    def setUp(self) -> None:
        self.table = kernel.load_table(ROOT)
        self.service = ObservationService(Clock())
        self.record = RunRecord.from_entries(RUN, journal())
        self.current = {"state_digest": DIGEST, "reporter_id": "worker-a"}

    def test_an_independent_observation_permits_settlement(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        observation = self.service.observe_run(self.record, "witness-z", reader)
        decision = kernel.evaluate(settle_request(observation, "kernel"), self.table, self.current)
        self.assertTrue(decision.permitted, decision.render())

    def test_an_observation_the_executor_forged_is_refused_by_the_kernel_too(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        observation = dict(self.service.observe_run(self.record, "witness-z", reader))
        observation["observer_id"] = "worker-a"
        decision = kernel.evaluate(settle_request(observation, "kernel"), self.table, self.current)
        self.assertFalse(decision.permitted)
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", decision.reason_code)

    def test_a_failed_predicate_is_not_a_satisfactory_observation(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, [
            {"predicate_id": "wrong", "kind": "JSON_FIELD_EQUALS", "address": "out/1",
             "field": "standing", "expected": "EFFECTIVE"}])
        observation = self.service.observe_run(self.record, "witness-z", reader)
        decision = kernel.evaluate(settle_request(observation, "kernel"), self.table, self.current)
        self.assertEqual("OBSERVATION_MISSING", decision.reason_code)


if __name__ == "__main__":
    unittest.main()
