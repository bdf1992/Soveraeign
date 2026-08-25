"""Prove the receipt-event check admits what it must and refuses what it must not.

The check exists because a receipt names the operation it is a receipt *for*, and a
name that is not the operation's canonical identifier cannot be joined to the
capability map. Four defeats are declared and each has a case here, alongside the
positive: the checked-in services, judged against the checked-in map.

Passing establishes ``BUILT`` for the checker. It witnesses nothing - it says only
that the names a service's source passes to its journal agree with the names the map
declares, and agreement is not evidence that any operation ran.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import receipt_events  # noqa: E402

CAPABILITY_MAP = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def _manifests() -> dict[str, dict]:
    found = {}
    for path in sorted((ROOT / "services").glob("*/contracts/service.json")):
        manifest = _load(path)
        found[manifest["service_id"]] = manifest
    return found


class HarvestTest(unittest.TestCase):
    """What the harvester reads out of a service's own source."""

    def _harvest(self, source: str) -> dict[str, list[str]]:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "svc").mkdir()
            (root / "svc" / "module.py").write_bytes(source.encode("utf-8"))
            return receipt_events.emitted_events(root / "svc", root)

    def test_a_literal_passed_to_an_emitter_is_found(self):
        found = self._harvest('store.receipt("COMMITTED", "asset.ingest-asset", "asset", a, b, c)\n')
        self.assertIn("asset.ingest-asset", found)
        self.assertTrue(found["asset.ingest-asset"][0].endswith("module.py:1"))

    def test_a_module_constant_passed_to_an_emitter_is_found(self):
        """The Console names its events; a check that saw only literals would read zero."""
        found = self._harvest(
            'POST_OPERATION = "console.post"\n'
            'def go(self):\n'
            '    return self._emit("post", subject, actor, payload, POST_OPERATION)\n'
        )
        self.assertIn("console.post", found)

    def test_a_string_reaching_no_emitter_is_not_an_event(self):
        found = self._harvest('LABEL = "asset.ingest-asset"\nprint(LABEL)\n')
        self.assertEqual(found, {})

    def test_a_file_name_is_not_an_event(self):
        """A payload carrying a module address must not read as an operation."""
        found = self._harvest('store.receipt("REFUSED", "core.py", "asset", a, b, c)\n')
        self.assertEqual(found, {})

    def test_a_single_word_is_not_an_event(self):
        """Subject types and record kinds share the argument list and are not events."""
        found = self._harvest('store.receipt("COMMITTED", "channel", "thread", a, b, c)\n')
        self.assertEqual(found, {})


class DefectTest(unittest.TestCase):
    """Each declared defeat, driven through the judgement."""

    CAPABILITIES = {"asset.ingest-asset", "asset.read-version", "console.post"}

    def test_an_event_that_is_neither_declared_nor_excused_is_refused(self):
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": []},
            {"asset.ingest": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(len(defects), 1)
        self.assertIn("UNMAPPED_EVENT", defects[0])
        self.assertIn("asset.ingest", defects[0])

    def test_an_excused_event_the_service_no_longer_emits_is_refused(self):
        """An excuse that outlives its reason is how a list stops being true."""
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": [{"event": "session.open", "because": "x" * 30}]},
            {"asset.ingest-asset": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(len(defects), 1)
        self.assertIn("STALE_UNDECLARED_EVENT", defects[0])

    def test_excusing_an_event_the_map_declares_is_refused(self):
        """A declared capability may not also be recorded as having no operation."""
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": [{"event": "asset.ingest-asset",
                                             "because": "x" * 30}]},
            {"asset.ingest-asset": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(len(defects), 1)
        self.assertIn("EXCUSED_BUT_DECLARED", defects[0])

    def test_emitting_another_services_capability_is_refused(self):
        """A receipt naming a sibling's operation would attribute the act to the wrong door."""
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": []},
            {"console.post": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(len(defects), 1)
        self.assertIn("FOREIGN_CAPABILITY_EVENT", defects[0])

    def test_a_declared_capability_passes(self):
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": []},
            {"asset.ingest-asset": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(defects, [])

    def test_an_excused_event_passes(self):
        defects = receipt_events.service_defects(
            "asset", {"undeclared_events": [{"event": "session.open", "because": "x" * 30}]},
            {"session.open": ["services/asset/src/x.py:1"]}, self.CAPABILITIES)
        self.assertEqual(defects, [])


class CheckedInServicesTest(unittest.TestCase):
    """The positive case: the services as they stand, against the map as it stands."""

    def test_every_emitted_event_resolves(self):
        defects, _ = receipt_events.run(ROOT, _load(CAPABILITY_MAP), _manifests())
        self.assertEqual(defects, [], "\n".join(defects))

    def test_the_built_services_emit_something(self):
        """A harvester that silently read nothing would pass this check vacuously."""
        _, harvested = receipt_events.run(ROOT, _load(CAPABILITY_MAP), _manifests())
        self.assertGreater(len(harvested["asset"]), 0)
        self.assertGreater(len(harvested["console"]), 0)

    def test_every_undeclared_entry_states_a_reason(self):
        for service_id, manifest in _manifests().items():
            for entry in manifest.get("undeclared_events", []):
                with self.subTest(service=service_id, event=entry["event"]):
                    self.assertGreaterEqual(len(entry["because"]), 20)


if __name__ == "__main__":
    unittest.main()
