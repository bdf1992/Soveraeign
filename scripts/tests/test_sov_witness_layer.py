"""Prove the witness-layer graders measure artifacts rather than reading declarations.

Every case here builds a scratch tree and grades it, so the corpus does not depend
on `witness/` holding anything. That matters twice: the directory is empty on
`main`, and a check that only ever passes vacuously is the defect this grader was
written to catch, not a demonstration of it.

The defeating cases are the point. A receipt that digests nothing, one whose own
probe moved, and a probe that catches its reach failure and reports a result
anyway each have a case proving the grader refuses them.

Passing establishes `BUILT` for the graders. It witnesses nothing, and it says
nothing about whether any receipt's finding was correct.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_witness_layer as layer  # noqa: E402
from sovwitness import probes as probe_grader  # noqa: E402
from sovwitness import records as record_grader  # noqa: E402

LF = chr(10)
GOOD_PROBE = '''"""A probe."""
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "subject" / "thing.txt"


class ProbeError(RuntimeError):
    """Could not reach."""


def main() -> int:
    try:
        return 0
    except ProbeError as failure:
        print(repr(failure))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline=LF)
    return path


def digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


class TreeCase(unittest.TestCase):
    """A scratch repository with one subject file and somewhere to put receipts."""

    def setUp(self) -> None:
        self.hold = tempfile.TemporaryDirectory()
        self.addCleanup(self.hold.cleanup)
        self.root = Path(self.hold.name).resolve()
        self.subject_text = "the subject" + LF
        write(self.root / "subject" / "thing.txt", self.subject_text)
        write(self.root / "witness" / "probes" / "probe_thing.py", GOOD_PROBE)

    def receipt(self, name: str = "obs.json", **override) -> Path:
        body = {
            "artifact_revision": "0" * 40,
            "observed": {
                "observed_state_addresses": ["subject/thing.txt"],
                "observed_state_digests": [digest(self.subject_text)],
            },
            "telemetry": {"probe": "witness/probes/probe_thing.py"},
        }
        body.update(override)
        return write(self.root / "witness" / "observations" / name,
                     json.dumps(body, indent=2) + LF)

    def grade(self, name: str = "obs.json") -> dict:
        return record_grader.grade(self.root / "witness" / "observations" / name, self.root)


class Staleness(TreeCase):
    def test_matching_digest_reads_current(self) -> None:
        self.receipt()
        self.assertEqual(self.grade()["verdict"], record_grader.CURRENT)

    def test_moved_subject_reads_stale_subject(self) -> None:
        self.receipt()
        write(self.root / "subject" / "thing.txt", "changed" + LF)
        result = self.grade()
        self.assertEqual(result["verdict"], record_grader.STALE_SUBJECT)
        self.assertIn("subject/thing.txt", result["moved"][0])

    def test_deleted_subject_reads_stale_subject(self) -> None:
        self.receipt()
        (self.root / "subject" / "thing.txt").unlink()
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_SUBJECT)

    def test_moved_probe_reads_stale_probe(self) -> None:
        """The receipt digested its own probe; when that moves the receipt is void."""
        self.receipt(observed={
            "observed_state_addresses": ["subject/thing.txt",
                                         "witness/probes/probe_thing.py"],
            "observed_state_digests": [digest(self.subject_text), digest(GOOD_PROBE)]})
        self.assertEqual(self.grade()["verdict"], record_grader.CURRENT)
        write(self.root / "witness" / "probes" / "probe_thing.py", GOOD_PROBE + "# edit" + LF)
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_PROBE)

    def test_deleted_probe_reads_stale_probe(self) -> None:
        self.receipt(observed={
            "observed_state_addresses": ["witness/probes/probe_thing.py"],
            "observed_state_digests": [digest(GOOD_PROBE)]})
        (self.root / "witness" / "probes" / "probe_thing.py").unlink()
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_PROBE)

    def test_probe_drift_outranks_subject_drift(self) -> None:
        self.receipt(observed={
            "observed_state_addresses": ["subject/thing.txt",
                                         "witness/probes/probe_thing.py"],
            "observed_state_digests": [digest("wrong"), digest("wrong")]})
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_PROBE)

    def test_only_invalid_and_probe_drift_fail(self) -> None:
        """The graded line: subject drift is reported debt, never a failure."""
        self.assertEqual(record_grader.FAILING_VERDICTS,
                         frozenset({record_grader.INVALID, record_grader.STALE_PROBE}))


class UngradeableReceipts(TreeCase):
    """Every shape that would let a receipt pass while measuring nothing."""

    def assert_invalid(self, contains: str, name: str = "obs.json") -> None:
        result = self.grade(name)
        self.assertEqual(result["verdict"], record_grader.INVALID, result)
        self.assertIn(contains, " ".join(result["defects"]))

    def test_empty_address_list_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": [],
                               "observed_state_digests": []})
        self.assert_invalid("digests nothing")

    def test_count_mismatch_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": ["subject/thing.txt", "a"],
                               "observed_state_digests": [digest(self.subject_text)]})
        self.assert_invalid("against")

    def test_missing_revision_is_invalid(self) -> None:
        body = json.loads((self.receipt()).read_text(encoding="utf-8"))
        del body["artifact_revision"]
        write(self.root / "witness" / "observations" / "obs.json", json.dumps(body))
        self.assert_invalid("artifact_revision")

    def test_missing_observed_is_invalid(self) -> None:
        write(self.root / "witness" / "observations" / "obs.json",
              json.dumps({"artifact_revision": "a"}))
        self.assert_invalid("observed")

    def test_unreadable_json_is_invalid(self) -> None:
        write(self.root / "witness" / "observations" / "obs.json", "{not json")
        self.assert_invalid("unreadable JSON")

    def test_malformed_digests_are_invalid(self) -> None:
        for bad in ("deadbeef", "sha256:zz", "sha256:" + "g" * 64, "sha256:" + "a" * 63, 7):
            with self.subTest(bad=bad):
                self.receipt(observed={"observed_state_addresses": ["subject/thing.txt"],
                                       "observed_state_digests": [bad]})
                self.assert_invalid("not a sha256")

    def test_non_string_address_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": [None],
                               "observed_state_digests": [digest("x")]})
        self.assert_invalid("non-empty string")

    def test_addresses_not_a_list_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": "subject/thing.txt",
                               "observed_state_digests": [digest("x")]})
        self.assert_invalid("must be lists")

    def test_escaping_addresses_are_invalid(self) -> None:
        for bad in ("../outside.txt", "/etc/passwd", "C:/Windows/x", "subject\\thing.txt"):
            with self.subTest(bad=bad):
                self.receipt(observed={"observed_state_addresses": [bad],
                                       "observed_state_digests": [digest("x")]})
                self.assertEqual(self.grade()["verdict"], record_grader.INVALID)

    def test_directory_address_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": ["subject"],
                               "observed_state_digests": [digest("x")]})
        self.assert_invalid("is a directory")

    def test_missing_directory_grades_nothing(self) -> None:
        empty = self.root / "nowhere"
        empty.mkdir()
        self.assertEqual(record_grader.grade_all(empty), [])


class ProbeLiveness(TreeCase):
    def probe(self, text: str, name: str = "probe_thing.py") -> dict:
        path = write(self.root / "witness" / "probes" / name, text)
        return probe_grader.inspect(path, self.root)

    def test_well_formed_probe_is_live(self) -> None:
        result = self.probe(GOOD_PROBE)
        self.assertEqual(result["verdict"], probe_grader.LIVE, result)
        self.assertEqual(result["reaches"], ["subject/thing.txt"])

    def test_transitive_reach_constant_is_read(self) -> None:
        result = self.probe(GOOD_PROBE.replace(
            'TARGET = REPO / "subject" / "thing.txt"',
            'SUB = REPO / "subject"' + LF + 'TARGET = SUB / "thing.txt"'))
        self.assertIn("subject/thing.txt", result["reaches"])

    def test_syntax_error_is_dead(self) -> None:
        result = self.probe("def main( ->:")
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertIn("does not parse", result["defects"][0])

    def test_missing_reach_target_is_dead(self) -> None:
        result = self.probe(GOOD_PROBE.replace('"subject" / "thing.txt"', '"gone" / "x.txt"'))
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertIn("not in the tree", " ".join(result["defects"]))

    def test_no_reach_target_is_dead(self) -> None:
        result = self.probe(GOOD_PROBE.replace(
            'TARGET = REPO / "subject" / "thing.txt"', "TARGET = 1"))
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertIn("declares no reach target", " ".join(result["defects"]))

    def test_missing_entry_points_are_dead(self) -> None:
        self.assertEqual(self.probe(GOOD_PROBE.replace("def main() -> int:",
                                                       "def other() -> int:"))["verdict"],
                         probe_grader.DEAD)
        guardless = GOOD_PROBE.split("if __name__")[0]
        self.assertIn("__main__ guard", " ".join(self.probe(guardless)["defects"]))

    def test_swallowing_the_reach_failure_is_dead(self) -> None:
        """The named attack: catch the reach failure and carry on as if reached."""
        for catch in ("ProbeError", "RuntimeError", "Exception", ""):
            with self.subTest(catch=catch):
                clause = f"except {catch}:" if catch else "except:"
                text = GOOD_PROBE.replace(
                    "    except ProbeError as failure:" + LF
                    + "        print(repr(failure))" + LF + "        return 0",
                    f"    {clause}" + LF + "        pass")
                result = self.probe(text)
                self.assertEqual(result["verdict"], probe_grader.DEAD, result)
                self.assertIn("discards it", " ".join(result["defects"]))

    def test_no_reach_failure_type_is_debt_not_failure(self) -> None:
        """Not every probe declares one; that is reported, not legislated."""
        result = self.probe(GOOD_PROBE.replace("class ProbeError(RuntimeError):", "class Note:"))
        self.assertEqual(result["verdict"], probe_grader.LIVE)
        self.assertIn("declares no reach-failure exception", " ".join(result["debts"]))

    def test_handler_that_drops_the_reason_is_debt(self) -> None:
        result = self.probe(GOOD_PROBE.replace(
            "    except ProbeError as failure:" + LF + "        print(repr(failure))",
            "    except ProbeError:" + LF + "        print('oh well')"))
        self.assertEqual(result["verdict"], probe_grader.LIVE)
        self.assertIn("without carrying the reason", " ".join(result["debts"]))

    def test_join_defect_when_receipt_names_a_missing_probe(self) -> None:
        self.receipt(telemetry={"probe": "witness/probes/probe_gone.py"})
        defects, _ = probe_grader.joins(self.root)
        self.assertIn("probe_gone.py", " ".join(defects))

    def test_join_debt_when_probe_has_no_receipt(self) -> None:
        _, debts = probe_grader.joins(self.root)
        self.assertIn("probe_thing.py is named by no receipt", debts)


class ProbeExecution(TreeCase):
    """`run` reads reaching out of the report, never out of the exit code."""

    def emit(self, report: str, exit_code: int = 0) -> dict:
        path = write(self.root / "witness" / "probes" / "probe_emit.py",
                     "import json, sys" + LF
                     + f"json.dump({report}, sys.stdout)" + LF
                     + f"raise SystemExit({exit_code})" + LF)
        return probe_grader.run(path, self.root)

    def test_clean_report_is_live(self) -> None:
        self.assertEqual(self.emit('{"checks": {"a": {"held": True}}}')["verdict"],
                         probe_grader.LIVE)

    def test_probe_error_in_the_report_is_dead(self) -> None:
        result = self.emit('{"checks": {"a": {"held": None, "probe_error": "boom"}}}')
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertEqual(result["exit_code"], 0)

    def test_null_held_without_a_reason_is_dead(self) -> None:
        self.assertEqual(self.emit('{"checks": {"a": {"held": None}}}')["verdict"],
                         probe_grader.DEAD)

    def test_exit_zero_does_not_make_a_failed_probe_live(self) -> None:
        """A probe whose every check failed to reach still exits 0 and still reports."""
        result = self.emit('{"checks": {"a": {"held": None, "probe_error": "x"},'
                           ' "b": {"held": None, "probe_error": "y"}}}', exit_code=0)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertEqual(len(result["reach_failures"]), 2)

    def test_unreadable_report_is_dead(self) -> None:
        path = write(self.root / "witness" / "probes" / "probe_quiet.py",
                     "print('not json')" + LF)
        self.assertEqual(probe_grader.run(path, self.root)["verdict"], probe_grader.DEAD)


class CommandExits(TreeCase):
    """The exit codes verify.py will read."""

    def test_records_passes_on_subject_drift_and_fails_on_probe_drift(self) -> None:
        self.receipt()
        write(self.root / "subject" / "thing.txt", "moved" + LF)
        self.assertEqual(layer.records(self.root, False), 0)
        self.receipt(name="probe.json", observed={
            "observed_state_addresses": ["witness/probes/probe_thing.py"],
            "observed_state_digests": [digest("never")]})
        self.assertEqual(layer.records(self.root, False), 1)

    def test_records_fails_on_an_ungradeable_receipt(self) -> None:
        write(self.root / "witness" / "observations" / "obs.json", "{")
        self.assertEqual(layer.records(self.root, False), 1)

    def test_probes_fails_on_a_dead_probe(self) -> None:
        self.assertEqual(layer.probes(self.root, False), 0)
        write(self.root / "witness" / "probes" / "probe_thing.py", "def main( ->:")
        self.assertEqual(layer.probes(self.root, False), 1)

    def test_empty_layer_passes_and_says_so(self) -> None:
        for name in ("observations", "probes"):
            for path in (self.root / "witness" / name).glob("*"):
                path.unlink()
        self.assertEqual(layer.records(self.root, False), 0)
        self.assertEqual(layer.probes(self.root, False), 0)


class CheckedInLayer(unittest.TestCase):
    """Whatever `witness/` currently holds must at least be gradeable."""

    def test_every_checked_in_receipt_and_probe_grades(self) -> None:
        for result in record_grader.grade_all(ROOT):
            self.assertNotEqual(result["verdict"], record_grader.INVALID,
                                f"{result['receipt']}: {result['defects']}")
        for path in probe_grader.modules(ROOT):
            self.assertEqual(probe_grader.inspect(path, ROOT)["verdict"],
                             probe_grader.LIVE, path.name)


if __name__ == "__main__":
    unittest.main()
