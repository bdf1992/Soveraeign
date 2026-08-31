import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("sov_disposition", ROOT / "scripts" / "sov_disposition.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class DispositionLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "disposition"
        mod.cmd_init(type("Args", (), {"store": str(self.store)})())

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **values):
        return type("Args", (), values)()

    def add_subject(self, subject_id="subject-a", revision="r1", kind="human", config=None):
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

    def observe(self, construct, value, probe="p1", context="default", subject_id="subject-a", revision="r1"):
        return mod.cmd_observe(
            self.args(
                store=str(self.store),
                subject_id=subject_id,
                subject_revision=revision,
                construct=construct,
                probe=probe,
                adapter="test-adapter",
                adapter_revision="1",
                context=context,
                value=value,
                evidence_json=json.dumps({"observed": value, "probe": probe}),
            )
        )

    def test_profile_replay_is_deterministic(self):
        self.add_subject()
        self.observe("exploration", 0.2, probe="a")
        self.observe("exploration", 0.6, probe="b")
        self.observe("exploration", 1.0, probe="c")
        first = mod.build_profile(self.store, "subject-a", "r1")
        second = mod.build_profile(self.store, "subject-a", "r1")
        self.assertEqual(first, second)
        self.assertEqual(first["profile_digest"], second["profile_digest"])
        self.assertEqual(0.6, first["constructs"]["exploration"]["center"])

    def test_profile_exposes_variation_not_only_center(self):
        self.add_subject()
        self.observe("initiative", -1.0, probe="a", context="blocked")
        self.observe("initiative", 0.0, probe="b", context="mixed")
        self.observe("initiative", 1.0, probe="c", context="clear")
        row = mod.build_profile(self.store, "subject-a", "r1")["constructs"]["initiative"]
        self.assertEqual(0.0, row["center"])
        self.assertGreater(row["spread"], 0.0)
        self.assertEqual(["blocked", "clear", "mixed"], row["contexts"])

    def test_too_few_observations_are_insufficient(self):
        self.add_subject()
        self.observe("scope-horizon", 0.8)
        row = mod.build_profile(self.store, "subject-a", "r1")["constructs"]["scope-horizon"]
        self.assertEqual("INSUFFICIENT_EVIDENCE", row["status"])
        self.assertEqual(1, row["n"])

    def test_model_subject_requires_material_configuration(self):
        with self.assertRaisesRegex(ValueError, "requires non-empty"):
            self.add_subject(kind="model")
        self.add_subject(subject_id="model-a", kind="model", config={"model": "example", "temperature": 0})

    def test_unknown_construct_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "unknown construct"):
            self.observe("made-up-trait", 0.5)

    def test_value_outside_scale_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "within"):
            self.observe("exploration", 1.5)

    def test_empty_evidence_refuses(self):
        self.add_subject()
        with self.assertRaisesRegex(ValueError, "identify supplied or observed evidence"):
            mod.cmd_observe(
                self.args(
                    store=str(self.store),
                    subject_id="subject-a",
                    subject_revision="r1",
                    construct="exploration",
                    probe="p",
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
            self.observe("exploration", value, probe=f"e{index}")
            self.observe("abstraction-preference", value, probe=f"a{index}")
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
            self.observe("exploration", value, probe=f"e{index}")
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

    def test_ledger_tampering_is_detected(self):
        self.add_subject()
        self.observe("exploration", 0.2)
        path = mod.ledger_path(self.store, "observations")
        rows = path.read_text(encoding="utf-8").splitlines()
        row = json.loads(rows[0])
        row["payload"]["value"] = 0.9
        path.write_text(mod.canonical(row) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            mod.verify_ledger(path)

    def test_cross_subject_comparison_is_refused_by_profile_contract(self):
        self.add_subject()
        profile = mod.build_profile(self.store, "subject-a", "r1")
        self.assertEqual(
            "NOT_COMPARABLE_ACROSS_ADAPTERS_OR_SUBJECT_KINDS",
            profile["comparison"]["standing"],
        )


if __name__ == "__main__":
    unittest.main()
