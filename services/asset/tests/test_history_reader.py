"""Consuming tests binding the history reader to the lineage reader corpus.

conformance/fixtures/lineage/reader-cases.json is the binding contract: per
its note, these tests live beside the asset-domain reader and are the only
code that joins its split contaminant parts, in memory only; no joined
contaminant is ever written to a committed file. pii-v1 is configured with
the synthetic identities the corpus carries (username example, the joined
example.com address), never a real identity. These cases establish BUILT
evidence only; they witness and ratify nothing.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "conformance" / "fixtures" / "lineage" / "reader-cases.json"
READER_PATH = ROOT / "services" / "asset" / "scripts" / "history_reader.py"

SPEC = importlib.util.spec_from_file_location("history_reader", READER_PATH)
assert SPEC and SPEC.loader
reader = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reader  # dataclass resolution needs the module registered
SPEC.loader.exec_module(reader)


def load_cases() -> dict[str, dict]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in corpus["cases"]}


def synthetic_pii(cases: dict[str, dict]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Join the corpus's synthetic email in memory; never hardcode a joined one."""
    emails = tuple(
        "".join(contaminant["parts"])
        for case in cases.values()
        for contaminant in case.get("contaminants", [])
        if contaminant["kind"] == "email-address"
    )
    return emails, ("example",)


class ReaderCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases()
        cls.emails, cls.usernames = synthetic_pii(cls.cases)

    def run_case(self, case: dict) -> tuple[bytes, tuple[bytes, dict]]:
        config = reader.ReaderConfig(
            definitions=tuple(case["omission_definitions"]),
            pii_emails=self.emails,
            pii_usernames=self.usernames,
        )
        payload = "".join(case["input_parts"]).encode("utf-8")
        return payload, reader.read_source(payload, case["source_id"], config)

    def test_rc001_clean_source_rereads_byte_identical(self):
        case = self.cases["RC-001-clean-source-rereads-byte-identical"]
        payload, (sanitized, manifest) = self.run_case(case)
        self.assertEqual(sanitized, payload)
        for field in case["expected_recording"]["required_fields"]:
            self.assertIn(field, manifest)
        self.assertEqual(manifest["fidelity"], "EXACT")
        self.assertEqual(manifest["omissions"], [])
        self.assertEqual(manifest["source_digest"], manifest["payload_digest"])

    def test_rc002_planted_contaminants_must_not_survive(self):
        case = self.cases["RC-002-planted-contaminants-must-not-survive"]
        payload, (sanitized, manifest) = self.run_case(case)
        joined_input = payload.decode("utf-8")
        output = sanitized.decode("utf-8")
        contaminants = case["contaminants"]
        for contaminant in contaminants:
            joined = "".join(contaminant["parts"])
            label = contaminant["contaminant_id"]
            # Drift guard: a fixture that no longer plants its contaminant is
            # a fixture defect, not a reader pass.
            self.assertIn(joined, joined_input, f"fixture defect: {label} not planted")
            self.assertNotIn(joined, output, f"contaminant survived: {label}")
        for field in case["expected_recording"]["required_fields"]:
            self.assertIn(field, manifest)
        self.assertEqual(manifest["fidelity"], "LOSSY")
        self.assertEqual(len(manifest["omissions"]), len(contaminants))
        for contaminant in contaminants:
            matching = [
                omission for omission in manifest["omissions"]
                if omission["kind"] == contaminant["kind"]
                and omission["definition"] == contaminant["definition"]
            ]
            self.assertEqual(len(matching), 1, contaminant["contaminant_id"])
        self.assertNotEqual(manifest["source_digest"], manifest["payload_digest"])
        recomputed = "sha256:" + hashlib.sha256(sanitized).hexdigest()
        self.assertEqual(manifest["payload_digest"], recomputed)

    def test_reading_is_deterministic(self):
        case = self.cases["RC-002-planted-contaminants-must-not-survive"]
        _, first = self.run_case(case)
        _, second = self.run_case(case)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[1], second[1])


class ReaderMechanicsTests(unittest.TestCase):
    def test_oversized_tool_result_body_is_omitted(self):
        body = "x" * (reader.OVERSIZED_LIMIT_BYTES + 1)
        line = json.dumps({"type": "tool_result", "content": body})
        payload = (line + "\nplain line\n").encode("utf-8")
        sanitized, manifest = reader.read_source(
            payload, "session:oversized", reader.ReaderConfig(definitions=("sanitize-v1",))
        )
        self.assertNotIn(body.encode("utf-8"), sanitized)
        self.assertIn(b"plain line", sanitized)
        self.assertEqual(manifest["fidelity"], "LOSSY")
        self.assertEqual(
            [omission["kind"] for omission in manifest["omissions"]],
            ["oversized-tool-result"],
        )
        self.assertEqual(manifest["omissions"][0]["definition"], "sanitize-v1")

    def test_small_tool_result_body_survives_byte_identical(self):
        line = json.dumps({"type": "tool_result", "content": "small"})
        payload = (line + "\n").encode("utf-8")
        sanitized, manifest = reader.read_source(
            payload, "session:small", reader.ReaderConfig(definitions=("sanitize-v1",))
        )
        self.assertEqual(sanitized, payload)
        self.assertEqual(manifest["fidelity"], "EXACT")

    def test_unknown_omission_definition_is_refused(self):
        with self.assertRaises(ValueError) as refusal:
            reader.read_source(
                b"x", "session:x", reader.ReaderConfig(definitions=("sanitize-v9",))
            )
        self.assertIn("OMISSION_DEFINITION_UNKNOWN", str(refusal.exception))

    def test_undeclared_sessions_dir_is_refused(self):
        with self.assertRaises(ValueError) as refusal:
            reader.resolve_sessions_dir(None, {})
        self.assertIn("SESSIONS_DIR_UNDECLARED", str(refusal.exception))


if __name__ == "__main__":
    unittest.main()
