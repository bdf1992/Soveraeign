from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import history_sources


WHEN = "2026-08-23T00:00:00+00:00"
WHO = "Bdo"

SPEC_SOURCE_FIELDS = (
    "source_id", "source_address", "payload_digest", "payload_size",
    "captured_at", "captured_by",
)


def build(commits=(), pulls=(), issues=(), sessions=()):
    return history_sources.build_lock(
        commits=list(commits), pulls=list(pulls), issues=list(issues),
        sessions=list(sessions), captured_at=WHEN, captured_by=WHO)


class LockShape(unittest.TestCase):
    """Positive fixtures: the lock carries exactly the SPEC Source fields."""

    def test_every_source_carries_spec_source_fields(self):
        lock = build(
            commits=[("a" * 40, "docs: found the boundary")],
            pulls=[{"number": 69, "title": "feat: measure", "state": "OPEN"}],
            issues=[{"number": 57, "title": "seed lineage", "state": "OPEN"}],
            sessions=[("11111111-2222-3333-4444-555555555555", 128,
                       "sha256:" + "0" * 64)])
        self.assertEqual(len(lock["sources"]), 4)
        for entry in lock["sources"]:
            for field in SPEC_SOURCE_FIELDS:
                self.assertNotIn(entry.get(field), (None, ""), field)
            self.assertTrue(entry["payload_digest"].startswith("sha256:"))
            self.assertEqual(entry["captured_at"], WHEN)
            self.assertEqual(entry["captured_by"], WHO)

    def test_lock_renders_as_parseable_json(self):
        rendered = history_sources.render(build(commits=[("b" * 40, "one")]))
        parsed = json.loads(rendered)
        self.assertEqual(parsed["captured_by"], WHO)
        self.assertEqual(parsed["counts"]["git-commit"], 1)

    def test_commit_address_is_the_sha_and_no_author_field_exists(self):
        lock = build(commits=[("c" * 40, "fix: subject only")])
        entry = lock["sources"][0]
        self.assertEqual(entry["source_address"], "c" * 40)
        self.assertEqual(entry["source_id"], "git-commit:" + "c" * 40)
        self.assertNotIn("author", entry)
        self.assertNotIn("email", entry)


class SessionEnumeration(unittest.TestCase):
    def test_records_id_size_digest_and_never_a_path(self):
        with TemporaryDirectory() as tmp:
            payload = b'{"type": "session"}\n'
            session_id = "0f0e0d0c-1111-2222-3333-444444444444"
            (Path(tmp) / (session_id + ".jsonl")).write_bytes(payload)
            (Path(tmp) / "memory").mkdir()  # subdirectories are not sessions
            sessions = history_sources.enumerate_sessions(Path(tmp))
        self.assertEqual(
            sessions,
            [(session_id, len(payload),
              "sha256:" + hashlib.sha256(payload).hexdigest())])
        rendered = history_sources.render(build(sessions=sessions))
        self.assertNotIn(Path(tmp).name, rendered)


class DefeatingFixtures(unittest.TestCase):
    """The lock is refused whenever an email or host path would land in it.

    Forbidden shapes are assembled at runtime so repository lint never sees a
    literal address or absolute path in this file.
    """

    def test_email_in_a_commit_subject_is_refused(self):
        address = "owner" + "@" + "example.com"
        lock = build(commits=[("d" * 40, "fix: mailto " + address)])
        self.assertIsNotNone(history_sources.sensitive(history_sources.render(lock)))

    def test_windows_user_path_is_refused(self):
        bad = "C:" + "\\" + "Users" + "\\" + "someone" + "\\" + "project"
        lock = build(pulls=[{"number": 1, "title": "chore: saw " + bad,
                             "state": "OPEN"}])
        self.assertIsNotNone(history_sources.sensitive(history_sources.render(lock)))

    def test_posix_user_path_is_refused(self):
        bad = "/" + "Users" + "/" + "someone" + "/" + "project"
        lock = build(issues=[{"number": 2, "title": "bug at " + bad,
                              "state": "OPEN"}])
        self.assertIsNotNone(history_sources.sensitive(history_sources.render(lock)))

    def test_clean_lock_passes_the_guard(self):
        lock = build(commits=[("e" * 40, "docs: clean subject")])
        self.assertIsNone(history_sources.sensitive(history_sources.render(lock)))

    def test_write_refuses_rather_than_writes(self):
        address = "owner" + "@" + "example.com"
        lock = build(commits=[("f" * 40, "docs: " + address)])
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "SOURCES.lock"
            refusal = history_sources.write_lock(lock, target)
            self.assertIsNotNone(refusal)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
