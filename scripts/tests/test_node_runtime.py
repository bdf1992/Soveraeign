from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("node_runtime", ROOT / "scripts" / "node_runtime.py")
assert SPEC and SPEC.loader
node_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(node_runtime)


class NodeRuntimeTests(unittest.TestCase):
    def test_health_surface_is_explicit_and_only_three_paths(self):
        self.assertEqual(node_runtime.HEALTH_PATHS, {
            "/health/startup", "/health/ready", "/health/live"
        })

    def test_listener_backlog_is_bounded(self):
        self.assertEqual(node_runtime.BoundedHTTPServer.request_queue_size, 1)

    def test_invalid_port_refuses_before_listener_creation(self):
        self.assertEqual(node_runtime.main(["--port", "0"]), 2)
        self.assertEqual(node_runtime.main(["--port", "65536"]), 2)


if __name__ == "__main__":
    unittest.main()
