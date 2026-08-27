"""Prove the witness-layer graders measure artifacts rather than reading declarations.

Every case here builds a scratch tree and grades it, so the corpus does not depend
on `witness/` holding anything. That matters twice: both directories are empty on
`main`, and a check that only ever passes vacuously is the defect this grader was
written to catch, not a demonstration of it.

The defeating cases are the point. A receipt that digests nothing, one that
respells its own probe's address to downgrade its drift, one naming a Windows
device that reads as an empty file forever, and a probe hiding its real reach
behind a decoy constant each have a case proving the grader refuses them. Several
of these were found by an adversarial pass against an earlier version that let
them through.

Passing establishes `BUILT` for the graders. It witnesses nothing, and it says
nothing about whether any receipt's finding was correct.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_witness_layer as layer  # noqa: E402
from sovwitness import probes as probe_grader  # noqa: E402
from sovwitness import records as record_grader  # noqa: E402

LF = chr(10)
# A probe shaped like the real ones: it reads its declared target, and its handler
# can actually be reached. An earlier fixture returned before it could raise, which
# made every handler case in this file exercise dead code.
GOOD_PROBE = '''"""A probe."""
from pathlib import Path
import json
import sys

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "subject" / "thing.txt"


class ProbeError(RuntimeError):
    """Could not reach."""


def reach() -> str:
    if not TARGET.exists():
        raise ProbeError(f"no subject at {TARGET}")
    return TARGET.read_text(encoding="utf-8")


def main() -> int:
    try:
        found = reach()
    except ProbeError as failure:
        json.dump({"checks": {"a": {"held": None, "probe_error": repr(failure)}}}, sys.stdout)
        return 0
    json.dump({"checks": {"a": {"held": bool(found)}}}, sys.stdout)
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
        self.probe_path = write(self.root / "witness" / "probes" / "probe_thing.py", GOOD_PROBE)

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

    def observing(self, *addresses: str, name: str = "obs.json", text: str = "") -> dict:
        """A receipt over the given addresses, digesting `text` for each."""
        self.receipt(name=name, observed={
            "observed_state_addresses": list(addresses),
            "observed_state_digests": [digest(text)] * len(addresses)})
        return self.grade(name)


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
        self.receipt(observed={
            "observed_state_addresses": ["subject/thing.txt",
                                         "witness/probes/probe_thing.py"],
            "observed_state_digests": [digest(self.subject_text), digest(GOOD_PROBE)]})
        (self.root / "subject" / "thing.txt").unlink()
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_SUBJECT)

    def test_moved_probe_reads_stale_probe(self) -> None:
        """The receipt digested its own probe; when that moves the receipt is void."""
        self.receipt(observed={
            "observed_state_addresses": ["subject/thing.txt",
                                         "witness/probes/probe_thing.py"],
            "observed_state_digests": [digest(self.subject_text), digest(GOOD_PROBE)]})
        self.assertEqual(self.grade()["verdict"], record_grader.CURRENT)
        write(self.probe_path, GOOD_PROBE + "# edit" + LF)
        self.assertEqual(self.grade()["verdict"], record_grader.STALE_PROBE)

    def test_probe_drift_survives_a_respelt_address(self) -> None:
        """Classification is on the resolved path, so case cannot downgrade the verdict.

        `Path.glob` and the filesystem are case-insensitive on Windows and not on
        the Linux runner, so a case variant is a real address on one and a missing
        one on the other. Both must read `STALE_PROBE`.
        """
        write(self.probe_path, GOOD_PROBE + "# edit" + LF)
        for spelling in ("witness/probes/probe_thing.py",
                         "Witness/probes/probe_thing.py",
                         "witness/PROBES/probe_thing.py"):
            with self.subTest(spelling=spelling):
                self.assertEqual(self.observing(spelling)["verdict"],
                                 record_grader.STALE_PROBE)

    def test_a_non_canonical_address_cannot_downgrade_probe_drift(self) -> None:
        """The other half: a `.` or `..` respelling is refused rather than reclassified."""
        write(self.probe_path, GOOD_PROBE + "# edit" + LF)
        for spelling in ("./witness/probes/probe_thing.py",
                         "subject/../witness/probes/probe_thing.py",
                         "witness/../witness/probes/probe_thing.py"):
            with self.subTest(spelling=spelling):
                result = self.observing(spelling)
                self.assertEqual(result["verdict"], record_grader.INVALID)
                self.assertIn(result["verdict"], record_grader.FAILING_VERDICTS)

    def test_probe_drift_outranks_subject_drift(self) -> None:
        self.assertEqual(
            self.observing("subject/thing.txt", "witness/probes/probe_thing.py")["verdict"],
            record_grader.STALE_PROBE)

    def test_subject_drift_alone_does_not_fail(self) -> None:
        """The graded line, exercised through grading rather than restated."""
        self.receipt()
        write(self.root / "subject" / "thing.txt", "moved" + LF)
        self.assertNotIn(self.grade()["verdict"], record_grader.FAILING_VERDICTS)
        self.assertIn(record_grader.STALE_PROBE, record_grader.FAILING_VERDICTS)


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

    def test_reserved_device_name_is_invalid(self) -> None:
        """`nul` exists in every directory on Windows and reads as an empty file."""
        for bad in ("nul", "NUL", "subject/nul", "nul.txt", "con", "com1", "lpt1"):
            with self.subTest(bad=bad):
                self.observing(bad)
                self.assert_invalid("reserved device")

    def test_host_normalised_segments_are_invalid(self) -> None:
        """Win32 strips a trailing space or dot, so the file opened is not the address."""
        for bad in ("subject/thing.txt ", "subject/thing.txt.", "subject /thing.txt"):
            with self.subTest(bad=bad):
                self.observing(bad)
                self.assert_invalid("normalised away")

    def test_duplicate_addresses_are_invalid(self) -> None:
        self.observing("subject/thing.txt", "subject/thing.txt")
        self.assert_invalid("named twice")

    def test_receipt_that_recomputes_nothing_is_invalid(self) -> None:
        self.observing("gone/a.txt", "gone/b.txt")
        self.assert_invalid("measures nothing")

    def test_duplicate_json_keys_are_invalid(self) -> None:
        """Python keeps the last block and a reader sees the first."""
        honest = json.dumps({"observed_state_addresses": ["subject/thing.txt"],
                             "observed_state_digests": [digest(self.subject_text)]})
        write(self.root / "witness" / "observations" / "obs.json",
              '{"artifact_revision": "a", "observed": ' + honest
              + ', "observed": ' + honest + "}")
        self.assert_invalid("duplicate JSON key")

    def test_null_byte_in_an_address_is_invalid_not_a_crash(self) -> None:
        self.observing("subject/thing\x00.txt")
        self.assert_invalid("null byte")

    def test_count_mismatch_is_invalid(self) -> None:
        self.receipt(observed={"observed_state_addresses": ["subject/thing.txt", "a"],
                               "observed_state_digests": [digest(self.subject_text)]})
        self.assert_invalid("against")

    def test_missing_revision_is_invalid(self) -> None:
        body = json.loads(self.receipt().read_text(encoding="utf-8"))
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
        for bad in ("../outside.txt", "/etc/passwd", "C:/Windows/x", "subject\\thing.txt", "."):
            with self.subTest(bad=bad):
                self.observing(bad)
                self.assertEqual(self.grade()["verdict"], record_grader.INVALID)

    def test_directory_address_is_invalid(self) -> None:
        self.observing("subject")
        self.assert_invalid("is a directory")

    def test_receipts_are_found_at_any_depth(self) -> None:
        self.receipt(name="obs.json")
        write(self.root / "witness" / "observations" / "deep" / "nested.json", "{not json")
        graded = {item["receipt"] for item in record_grader.grade_all(self.root)}
        self.assertEqual(graded, {"obs.json", "nested.json"})

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

    def test_a_decoy_constant_cannot_hide_the_real_reach(self) -> None:
        """A bare alias of the root must stay visible, or paths through it vanish."""
        result = self.probe(GOOD_PROBE.replace(
            'TARGET = REPO / "subject" / "thing.txt"',
            'BASE = REPO' + LF + 'TARGET = BASE / "gone" / "missing.py"'))
        self.assertEqual(result["verdict"], probe_grader.DEAD, result)
        self.assertIn("gone/missing.py", " ".join(result["defects"]))

    def test_an_unused_reach_constant_is_dead(self) -> None:
        result = self.probe(GOOD_PROBE.replace(
            'TARGET = REPO / "subject" / "thing.txt"',
            'TARGET = REPO / "subject" / "thing.txt"' + LF + 'DECOY = REPO / "subject"'))
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertIn("never used", " ".join(result["defects"]))

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

    def swallow(self, clause: str, body: str) -> dict:
        return self.probe(GOOD_PROBE.replace(
            "    except ProbeError as failure:" + LF
            + '        json.dump({"checks": {"a": {"held": None, '
              '"probe_error": repr(failure)}}}, sys.stdout)' + LF
            + "        return 0",
            f"    {clause}" + LF + f"        {body}"))

    def test_discarding_the_reach_failure_is_dead(self) -> None:
        """The named attack in its blatant form, across every clause that catches."""
        for clause in ("except ProbeError:", "except RuntimeError:", "except Exception:",
                       "except:", "except errors.ProbeError:"):
            for body in ("pass", "..."):
                with self.subTest(clause=clause, body=body):
                    result = self.swallow(clause, body)
                    self.assertEqual(result["verdict"], probe_grader.DEAD, result)
                    self.assertIn("discards it", " ".join(result["defects"]))

    def test_catching_without_re_raising_is_debt(self) -> None:
        """Reported, not failed: whether the reason reaches the report is not static."""
        result = self.swallow("except ProbeError as failure:", "return 0")
        self.assertEqual(result["verdict"], probe_grader.LIVE)
        self.assertIn("does not re-raise", " ".join(result["debts"]))

    def test_no_reach_failure_type_is_debt_not_failure(self) -> None:
        """Not every probe declares one; that is reported, not legislated."""
        result = self.probe(GOOD_PROBE.replace("class ProbeError(RuntimeError):",
                                               "class ProbeError:"))
        self.assertEqual(result["verdict"], probe_grader.LIVE)
        self.assertIn("declares no reach-failure exception", " ".join(result["debts"]))

    def test_probes_are_found_at_any_depth(self) -> None:
        write(self.root / "witness" / "probes" / "deep" / "probe_nested.py", GOOD_PROBE)
        found = {path.name for path in probe_grader.modules(self.root)}
        self.assertEqual(found, {"probe_thing.py", "probe_nested.py"})

    def test_join_defect_when_receipt_names_a_missing_probe(self) -> None:
        self.receipt(telemetry={"probe": "witness/probes/probe_gone.py"})
        defects, _ = probe_grader.joins(self.root)
        self.assertIn("probe_gone.py", " ".join(defects))

    def test_join_refuses_a_probe_address_outside_the_tree(self) -> None:
        self.receipt(telemetry={"probe": "C:/Windows/System32/drivers/etc/hosts"})
        defects, _ = probe_grader.joins(self.root)
        self.assertTrue(defects, "an out-of-tree probe address must be refused")

    def test_join_refuses_a_probe_address_that_is_not_a_probe(self) -> None:
        self.receipt(telemetry={"probe": "subject/thing.txt"})
        defects, _ = probe_grader.joins(self.root)
        self.assertIn("not a probe module", " ".join(defects))

    def test_join_debt_when_probe_has_no_receipt(self) -> None:
        _, debts = probe_grader.joins(self.root)
        self.assertIn("probe_thing.py is named by no receipt", debts)


class ProbeExecution(TreeCase):
    """`run` grades the process and the report, and never the exit code alone."""

    def emit(self, report: str, exit_code: int = 0, stderr: str = "") -> dict:
        path = write(self.root / "witness" / "probes" / "probe_emit.py",
                     "import json, sys" + LF
                     + f"sys.stderr.write({stderr!r})" + LF
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

    def test_exit_zero_does_not_make_a_failed_probe_live(self) -> None:
        """A probe whose every check failed to reach still exits 0 and still reports."""
        result = self.emit('{"checks": {"a": {"held": None, "probe_error": "x"},'
                           ' "b": {"held": None, "probe_error": "y"}}}', exit_code=0)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertEqual(len(result["reach_failures"]), 2)

    def test_nonzero_exit_is_dead(self) -> None:
        """A clean exit is not evidence of reaching; a dirty one is evidence against."""
        result = self.emit('{"checks": {"a": {"held": True}}}', exit_code=3)
        self.assertEqual(result["verdict"], probe_grader.DEAD)
        self.assertIn("exited 3", " ".join(result["defects"]))

    def test_empty_and_scalar_reports_are_dead(self) -> None:
        for report in ("None", "{}", "[]", "0", '"ok"'):
            with self.subTest(report=report):
                self.assertEqual(self.emit(report)["verdict"], probe_grader.DEAD)

    def test_stderr_is_debt(self) -> None:
        result = self.emit('{"checks": {"a": {"held": True}}}', stderr="noise")
        self.assertEqual(result["verdict"], probe_grader.LIVE)
        self.assertTrue(result["debts"])

    def test_unreadable_report_is_dead(self) -> None:
        path = write(self.root / "witness" / "probes" / "probe_quiet.py",
                     "print('not json')" + LF)
        self.assertEqual(probe_grader.run(path, self.root)["verdict"], probe_grader.DEAD)

    def test_the_fixture_probe_reports_reaching_and_not_reaching(self) -> None:
        """The fixture must exercise its own handler, or every case above is dead code."""
        self.assertEqual(probe_grader.run(self.probe_path, self.root)["verdict"],
                         probe_grader.LIVE)
        (self.root / "subject" / "thing.txt").unlink()
        broken = probe_grader.run(self.probe_path, self.root)
        self.assertEqual(broken["verdict"], probe_grader.DEAD)
        self.assertIn("no subject at", " ".join(broken["defects"]))


class CommandExits(TreeCase):
    """The exit codes verify.py will read."""

    def test_records_passes_on_subject_drift_and_fails_on_probe_drift(self) -> None:
        self.receipt()
        write(self.root / "subject" / "thing.txt", "moved" + LF)
        self.assertEqual(layer.records(self.root, False), 0)
        self.observing("witness/probes/probe_thing.py", name="probe.json", text="never")
        self.assertEqual(layer.records(self.root, False), 1)

    def test_records_fails_on_an_ungradeable_receipt(self) -> None:
        write(self.root / "witness" / "observations" / "obs.json", "{")
        self.assertEqual(layer.records(self.root, False), 1)

    def test_probes_fails_on_a_dead_probe(self) -> None:
        self.assertEqual(layer.probes(self.root, False), 0)
        write(self.probe_path, "def main( ->:")
        self.assertEqual(layer.probes(self.root, False), 1)

    def test_probes_fails_on_a_join_defect(self) -> None:
        self.receipt(telemetry={"probe": "witness/probes/probe_gone.py"})
        self.assertEqual(layer.probes(self.root, False), 1)

    def test_empty_layer_passes_and_says_so(self) -> None:
        for name in ("observations", "probes"):
            for path in (self.root / "witness" / name).glob("*"):
                path.unlink()
        self.assertEqual(layer.records(self.root, False), 0)
        self.assertEqual(layer.probes(self.root, False), 0)


class CheckedInLayer(unittest.TestCase):
    """Whatever `witness/` currently holds must at least be gradeable."""

    def test_every_checked_in_receipt_is_gradeable(self) -> None:
        graded = record_grader.grade_all(ROOT)
        if not graded:
            self.skipTest("witness/observations/ holds no receipt on this branch")
        for result in graded:
            self.assertNotEqual(result["verdict"], record_grader.INVALID,
                                f"{result['receipt']}: {result['defects']}")

    def test_every_checked_in_probe_is_live(self) -> None:
        found = probe_grader.modules(ROOT)
        if not found:
            self.skipTest("witness/probes/ holds no probe on this branch")
        for path in found:
            self.assertEqual(probe_grader.inspect(path, ROOT)["verdict"],
                             probe_grader.LIVE, path.name)


if __name__ == "__main__":
    unittest.main()
