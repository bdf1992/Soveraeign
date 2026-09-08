from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import sov_disposition as mod


class DispositionLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "disposition"
        mod.cmd_init(type("Args", (), {"store": str(self.store)})())

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **values):
        return type("Args", (), values)()

    def add_subject(
        self,
        subject_id="subject-a",
        revision="r1",
        kind="human",
        config=None,
    ):
        return mod.cmd_subject_add(
            self.args(
                store=str(self.store),
                subject_id=subject_id,
                revision=revision,
                kind=kind,
                adapter=f"{kind}-adapter",
                config_json=json.dumps(config or {}),
            )
        )

    def observe(
        self,
        construct,
        value,
        probe,
        context="default",
        subject_id="subject-a",
        revision="r1",
        trial=None,
    ):
        return mod.cmd_observe(
            self.args(
                store=str(self.store),
                subject_id=subject_id,
                subject_revision=revision,
                construct=construct,
                probe=probe,
                trial=trial or f"{probe}:{context}",
                adapter="test-adapter",
                adapter_revision="1",
                context=context,
                value=value,
                evidence_json=json.dumps({"observed": value, "probe": probe}),
            )
        )

    def test_profile_replay_is_deterministic(self):
        self.add_subject()
        probes = [
            "exploration.reversible-novelty.001",
            "exploration.unknown-solution.002",
            "exploration.reversible-novelty.001",
        ]
        for index, (probe, value) in enumerate(zip(probes, (0.2, 0.6, 1.0)), start=1):
            self.observe("exploration", value, probe, trial=f"trial-{index}")
        first = mod.build_profile(self.store, "subject-a", "r1")
        second = mod.build_profile(self.store, "subject-a", "r1")
        self.assertEqual(first, second)
        self.assertEqual(first["profile_digest"], second["profile_digest"])
        self.assertEqual(0.6, first["constructs"]["exploration"]["center"])

    def test_profile_exposes_variation_not_only_center(self):
        self.add_subject()
        probe = "initiative.sufficient-boundary.001"
        self.observe("initiative", -1.0, probe, context="blocked", trial="i-1")
        self.observe("initiative", 0.0, probe, context="mixed", trial="i-2")
        self.observe("initiative", 1.0, probe, context="clear", trial="i-3")
        row = mod.build_profile(self.store, "subject-a", "r1")["constructs"]["initiative"]
        self.assertEqual(0.0, row["center"])
        self.assertGreater(row["spread"], 0.0)
        self.assertEqual(["blocked", "clear", "mixed"], row["contexts"])

    def test_too_few_observations_are_insufficient(self):
        self.add_subject()
        self.observe(
            "scope-horizon",
            0.8,
            "scope-horizon.local-vs-system.001",
        )
        row = mod.build_profile(self.store, "subject-a", "r1")["constructs"]["scope-horizon"]
        self.assertEqual("INSUFFICIENT_EVIDENCE", row["status"])
        self.assertEqual(1, row["n"])

    def test_model_subject_requires_material_configuration(self):
        with self.assertRaisesRegex(ValueError, "requires non-empty"):
            self.add_subject(kind="model")
        self.add_subject(
            subject_id="model-a",
            kind="model",
            config={"model": "example", "temperature": 0},
        )

    def test_subject_revision_is_immutable(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "already declared"):
            self.add_subject()

    def test_unknown_construct_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "unknown construct"):
            self.observe("made-up-trait", 0.5, "exploration.reversible-novelty.001")

    def test_unknown_probe_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "unknown probe"):
            self.observe("exploration", 0.5, "unknown.probe")

    def test_probe_construct_mismatch_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "measures exploration"):
            self.observe("initiative", 0.5, "exploration.reversible-novelty.001")

    def test_duplicate_trial_refuses(self):
        self.add_subject()
        probe = "exploration.reversible-novelty.001"
        self.observe("exploration", 0.2, probe, trial="same-trial")
        with self.assertRaisesRegex(ValueError, "duplicate trial_id"):
            self.observe("exploration", 0.9, probe, trial="same-trial")

    def test_value_outside_scale_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "within"):
            self.observe("exploration", 1.5, "exploration.reversible-novelty.001")

    def test_empty_evidence_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "identify supplied or observed evidence"):
            mod.cmd_observe(
                self.args(
                    store=str(self.store),
                    subject_id="subject-a",
                    subject_revision="r1",
                    construct="exploration",
                    probe="exploration.reversible-novelty.001",
                    trial="empty-evidence",
                    adapter="test",
                    adapter_revision="1",
                    context="default",
                    value=0.2,
                    evidence_json="{}",
                )
            )

    def test_unvalidated_projection_requires_explicit_opt_in(self):
        self.add_subject()
        for index, value in enumerate((0.2, 0.4, 0.6), start=1):
            self.observe(
                "exploration",
                value,
                "exploration.reversible-novelty.001",
                trial=f"e{index}",
            )
            self.observe(
                "abstraction-preference",
                value,
                "abstraction-preference.pattern-transfer.001",
                trial=f"a{index}",
            )
        args = self.args(
            store=str(self.store),
            subject_id="subject-a",
            revision="r1",
            projection="big-five-like-v0.1",
            allow_unvalidated=False,
        )
        with self.assertRaisesRegex(ValueError, "UNVALIDATED"):
            mod.cmd_report(args)
        args.allow_unvalidated = True
        report = mod.cmd_report(args)["report"]
        self.assertEqual("UNVALIDATED", report["calibration_standing"])
        self.assertEqual("NOT_ADMITTED", report["cohort_comparison"])

    def test_projection_is_rebuildable_from_profile_evidence(self):
        self.add_subject()
        for index, value in enumerate((0.2, 0.4, 0.6), start=1):
            self.observe(
                "exploration",
                value,
                "exploration.reversible-novelty.001",
                trial=f"e{index}",
            )
        args = self.args(
            store=str(self.store),
            subject_id="subject-a",
            revision="r1",
            projection="sov-native-v0.1",
            allow_unvalidated=False,
        )
        first = mod.cmd_report(args)["report"]
        path = self.store / "reports" / "subject-a@r1.sov-native-v0.1.json"
        path.unlink()
        second = mod.cmd_report(args)["report"]
        self.assertEqual(first, second)

    def test_ledger_tampering_is_detected_and_blocks_append(self):
        self.add_subject()
        probe = "exploration.reversible-novelty.001"
        self.observe("exploration", 0.2, probe, trial="first")
        path = mod.ledger_path(self.store, "observations")
        row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        row["payload"]["value"] = 0.9
        path.write_text(mod.canonical(row) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            mod.verify_ledger(path)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.observe("exploration", 0.4, probe, trial="second")

    def test_cross_subject_comparison_is_refused_by_profile_contract(self):
        self.add_subject()
        profile = mod.build_profile(self.store, "subject-a", "r1")
        self.assertEqual(
            "NOT_COMPARABLE_ACROSS_ADAPTERS_OR_SUBJECT_KINDS",
            profile["comparison"]["standing"],
        )


if __name__ == "__main__":
    unittest.main()
